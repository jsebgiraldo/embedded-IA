"""
Projects API routes.
Handles CRUD operations for GitHub-imported projects.
"""
import uuid
import os
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database.db import get_db, Project, Build, Dependency
from models.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithDetails,
    ProjectListResponse,
    ProjectMetrics,
    SyncProjectResponse,
    TriggerBuildRequest,
    TriggerBuildResponse
)
from services.repository_manager import RepositoryManager
from services.dependency_resolver import DependencyResolver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Initialize services
PROJECTS_BASE_DIR = os.getenv("PROJECTS_BASE_DIR", "/app/projects")
repo_manager = RepositoryManager(base_dir=PROJECTS_BASE_DIR)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new project from GitHub repository.
    
    Steps:
    1. Validate project name is unique
    2. Generate UUID and clone path
    3. Create project record
    4. Clone repository (async)
    5. Update project with commit info
    """
    logger.info(f"Creating project: {project.name}")
    
    # Check if project with same name exists
    existing = db.query(Project).filter(Project.name == project.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Project with name '{project.name}' already exists"
        )
    
    # Generate UUID and clone path
    project_id = str(uuid.uuid4())
    clone_path = os.path.join(PROJECTS_BASE_DIR, project.name)
    
    # Create project record
    db_project = Project(
        id=project_id,
        name=project.name,
        description=project.description,
        repo_url=project.repo_url,
        repo_full_name=project.repo_full_name,
        branch=project.branch,
        clone_path=clone_path,
        target=project.target,
        build_system=project.build_system,
        webhook_secret=project.webhook_secret,
        status="pending"
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Clone repository in background
    try:
        clone_result = await repo_manager.clone_repository(
            repo_url=project.repo_url,
            clone_path=clone_path,
            branch=project.branch
        )
        
        if clone_result["success"]:
            # Update project with commit info
            db_project.last_commit_sha = clone_result["commit_sha"]
            db_project.last_synced_at = datetime.utcnow()
            db_project.status = "active"
            
            logger.info(f"✅ Project {project.name} created and cloned successfully")
            
            # Automatically scan for dependencies
            try:
                resolver = DependencyResolver(db)
                total_found, newly_added = resolver.scan_project_dependencies(
                    project_id=project_id,
                    project_path=clone_path
                )
                logger.info(f"✅ Auto-scanned dependencies: {total_found} found, {newly_added} stored")
            except Exception as e:
                logger.warning(f"⚠️ Failed to auto-scan dependencies: {e}")
        else:
            db_project.status = "error"
            logger.error(f"❌ Failed to clone repository: {clone_result.get('error')}")
        
        db.commit()
        db.refresh(db_project)
        
    except Exception as e:
        logger.error(f"❌ Error cloning repository: {e}")
        db_project.status = "error"
        db.commit()
    
    return db_project


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all projects with optional filtering.
    """
    query = db.query(Project)
    
    # Apply filters
    if status:
        query = query.filter(Project.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    projects = query.order_by(desc(Project.created_at)).offset(offset).limit(limit).all()
    
    # Enrich with build info
    result_projects = []
    for project in projects:
        project_dict = ProjectResponse.from_orm(project).dict()
        
        # Get builds count
        builds_count = db.query(func.count(Build.id)).filter(
            Build.project_id == project.id
        ).scalar()
        
        # Get last build status
        last_build = db.query(Build).filter(
            Build.project_id == project.id
        ).order_by(desc(Build.created_at)).first()
        
        project_dict["builds_count"] = builds_count
        project_dict["last_build_status"] = last_build.status if last_build else None
        
        result_projects.append(ProjectResponse(**project_dict))
    
    return ProjectListResponse(projects=result_projects, total=total)


# ============================================================================
# Build Status Endpoints (must come before /{project_id} endpoints)
# ============================================================================

@router.get("/builds/{build_id}")
async def get_build_status(
    build_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed status of a specific build.
    
    Returns:
        Build information including status, duration, outputs, and artifacts
    """
    build = db.query(Build).filter(Build.id == build_id).first()
    
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    # Get project info
    project = db.query(Project).filter(Project.id == build.project_id).first()
    
    return {
        "id": build.id,
        "project_id": build.project_id,
        "project_name": project.name if project else None,
        "commit_sha": build.commit_sha,
        "commit_message": build.commit_message,
        "commit_author": build.commit_author,
        "branch": build.branch,
        "triggered_by": build.triggered_by,
        "status": build.status,
        "started_at": build.started_at,
        "completed_at": build.completed_at,
        "duration": build.duration,
        "build_output": build.build_output,
        "test_results": build.test_results,
        "artifacts_path": build.artifacts_path,
        "created_at": build.created_at
    }


@router.post("/builds/{build_id}/retry")
async def retry_build(
    build_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Retry a failed build.
    
    Only builds with status='failed' can be retried.
    """
    build = db.query(Build).filter(Build.id == build_id).first()
    
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    if build.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry build with status '{build.status}'. Only failed builds can be retried."
        )
    
    project = db.query(Project).filter(Project.id == build.project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Initialize orchestration service
    import sys
    from pathlib import Path
    mcp_path = Path(__file__).parent.parent.parent / "mcp-server" / "src"
    if str(mcp_path) not in sys.path:
        sys.path.insert(0, str(mcp_path))
    
    from services.build_orchestration import BuildOrchestrationService
    from agent.orchestrator import AgentOrchestrator
    from mcp_idf.client import MCPClient
    
    mcp_client = MCPClient()
    tools = mcp_client.get_langchain_tools()
    orchestrator = AgentOrchestrator(langchain_tools=tools)
    build_service = BuildOrchestrationService(orchestrator)
    
    # Reset build status
    build.status = "pending"
    build.started_at = None
    build.completed_at = None
    build.duration = None
    build.build_output = None
    build.test_results = None
    db.commit()
    
    logger.info(f"🔄 Retrying failed build #{build_id}")
    
    # Execute build in background
    background_tasks.add_task(
        build_service.execute_build_background,
        db=db,
        build_id=build_id,
        project_id=build.project_id,
        flash_device=False,
        run_qemu=True
    )
    
    return {
        "build_id": build_id,
        "status": "pending",
        "message": "Build retry scheduled"
    }


@router.get("/builds")
async def list_all_builds(
    status: Optional[str] = Query(None, description="Filter by status"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all builds across all projects with optional filtering.
    """
    query = db.query(Build)
    
    # Apply filters
    if status:
        query = query.filter(Build.status == status)
    
    if project_id:
        query = query.filter(Build.project_id == project_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    builds = query.order_by(desc(Build.created_at)).offset(offset).limit(limit).all()
    
    # Enrich with project names
    result = []
    for build in builds:
        project = db.query(Project).filter(Project.id == build.project_id).first()
        result.append({
            "id": build.id,
            "project_id": build.project_id,
            "project_name": project.name if project else None,
            "commit_sha": build.commit_sha[:7] if build.commit_sha else None,
            "commit_message": build.commit_message,
            "branch": build.branch,
            "status": build.status,
            "duration": build.duration,
            "created_at": build.created_at
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "builds": result
    }


@router.get("/{project_id}", response_model=ProjectWithDetails)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get project details including dependencies and recent builds.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get dependencies
    dependencies = db.query(Dependency).filter(
        Dependency.project_id == project_id
    ).all()
    
    # Get recent builds (last 10)
    recent_builds = db.query(Build).filter(
        Build.project_id == project_id
    ).order_by(desc(Build.created_at)).limit(10).all()
    
    # Calculate metrics
    total_builds = db.query(func.count(Build.id)).filter(
        Build.project_id == project_id
    ).scalar()
    
    successful_builds = db.query(func.count(Build.id)).filter(
        Build.project_id == project_id,
        Build.status == "success"
    ).scalar()
    
    success_rate = (successful_builds / total_builds * 100) if total_builds > 0 else 0
    
    avg_duration = db.query(func.avg(Build.duration)).filter(
        Build.project_id == project_id,
        Build.status == "success",
        Build.duration.isnot(None)
    ).scalar()
    
    metrics = ProjectMetrics(
        total_builds=total_builds,
        success_rate=success_rate,
        avg_build_time=float(avg_duration) if avg_duration else 0.0
    )
    
    # Build response
    return ProjectWithDetails(
        **ProjectResponse.from_orm(project).dict(),
        dependencies=dependencies,
        recent_builds=recent_builds,
        metrics=metrics.dict()
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update project configuration.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    update_data = project_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    
    project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    logger.info(f"✅ Updated project {project_id}")
    
    return project


@router.put("/{project_id}/sync", response_model=SyncProjectResponse)
async def sync_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Synchronize project by pulling latest changes from GitHub.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot sync project with status: {project.status}"
        )
    
    logger.info(f"Syncing project: {project.name}")
    
    # Update repository
    result = await repo_manager.update_repository(
        clone_path=project.clone_path,
        branch=project.branch
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync repository: {result.get('error')}"
        )
    
    # Update project record
    previous_commit = project.last_commit_sha
    project.last_commit_sha = result["current_commit"]
    project.last_synced_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"✅ Synced project {project.name}: {result['commits_pulled']} new commits")
    
    # Re-scan dependencies after sync
    try:
        resolver = DependencyResolver(db)
        total_found, newly_added = resolver.scan_project_dependencies(
            project_id=project_id,
            project_path=project.clone_path
        )
        logger.info(f"✅ Re-scanned dependencies after sync: {total_found} found, {newly_added} updated")
    except Exception as e:
        logger.warning(f"⚠️ Failed to re-scan dependencies after sync: {e}")
    
    return SyncProjectResponse(
        status="synced",
        previous_commit=previous_commit,
        current_commit=result["current_commit"],
        changes={
            "files_changed": result["files_changed"],
            "insertions": result["insertions"],
            "deletions": result["deletions"],
            "commits_pulled": result["commits_pulled"]
        }
    )


@router.post("/{project_id}/build", response_model=TriggerBuildResponse, status_code=201)
async def trigger_build(
    project_id: str,
    request: TriggerBuildRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger a manual build for the project.
    
    This executes a complete workflow using the AgentOrchestrator:
    - Build firmware
    - Run tests (QEMU/hardware)
    - QA validation
    - Generate artifacts
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Add mcp_idf to path if not already there
    import sys
    from pathlib import Path
    mcp_path = Path(__file__).parent.parent.parent / "mcp-server" / "src"
    if str(mcp_path) not in sys.path:
        sys.path.insert(0, str(mcp_path))
    
    # Validate project is ready for build
    from services.build_orchestration import BuildOrchestrationService
    from agent.orchestrator import AgentOrchestrator
    from mcp_idf.client import MCPClient
    
    # Get MCP tools and create orchestrator
    mcp_client = MCPClient()
    tools = mcp_client.get_langchain_tools()
    orchestrator = AgentOrchestrator(langchain_tools=tools)
    build_service = BuildOrchestrationService(orchestrator)
    
    is_valid, error_msg = build_service.validate_project_for_build(project)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Get commit info
    if request.commit_sha:
        # Checkout specific commit
        checkout_result = await repo_manager.checkout_commit(
            clone_path=project.clone_path,
            commit_sha=request.commit_sha
        )
        
        if not checkout_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to checkout commit: {checkout_result.get('error')}"
            )
        
        commit_sha = request.commit_sha
        commit_message = checkout_result.get("commit_message")
        commit_author = checkout_result.get("commit_author")
    else:
        # Use latest commit
        commit_info = await repo_manager.get_latest_commit(project.clone_path)
        commit_sha = commit_info["commit_sha"]
        commit_message = commit_info.get("commit_message")
        commit_author = commit_info.get("commit_author")
    
    # Create build record
    build = Build(
        project_id=project_id,
        commit_sha=commit_sha,
        commit_message=commit_message,
        commit_author=commit_author,
        branch=project.branch,
        triggered_by=request.trigger,
        status="pending"
    )
    
    db.add(build)
    db.commit()
    db.refresh(build)
    
    logger.info(f"🚀 Build #{build.id} triggered for project {project.name}")
    
    # Execute build in background using orchestrator
    background_tasks.add_task(
        build_service.execute_build_background,
        db=db,
        build_id=build.id,
        project_id=project_id,
        flash_device=False,
        run_qemu=True
    )
    
    return TriggerBuildResponse(
        build_id=build.id,
        status=build.status,
        project_id=project_id,
        commit_sha=commit_sha
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete project (metadata only, repository files remain).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete project (cascades to dependencies and builds)
    db.delete(project)
    db.commit()
    
    logger.info(f"✅ Deleted project {project.name}")
    
    return {"deleted": True, "id": project_id}


@router.post("/{project_id}/scan-dependencies")
async def scan_project_dependencies(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Scan project for ESP-IDF component dependencies.
    
    Finds and parses idf_component.yml files in the project,
    extracts dependencies, and stores them in the database.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.clone_path or not os.path.exists(project.clone_path):
        raise HTTPException(
            status_code=400,
            detail="Project repository not cloned yet"
        )
    
    try:
        # Initialize dependency resolver
        resolver = DependencyResolver(db)
        
        # Scan for dependencies
        total_found, newly_added = resolver.scan_project_dependencies(
            project_id=project_id,
            project_path=project.clone_path
        )
        
        logger.info(f"✅ Scanned dependencies for project {project.name}: {total_found} found, {newly_added} stored")
        
        # Get updated dependency list
        dependencies = resolver.get_project_dependencies(project_id)
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "total_found": total_found,
            "newly_added": newly_added,
            "dependencies": [
                {
                    "id": str(dep.id),
                    "component_name": dep.component_name,
                    "version": dep.version,
                    "source": dep.source,
                    "installed": dep.installed
                }
                for dep in dependencies
            ]
        }
        
    except Exception as e:
        logger.error(f"Error scanning dependencies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan dependencies: {str(e)}"
        )


@router.get("/{project_id}/dependencies")
async def get_project_dependencies(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all dependencies for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    resolver = DependencyResolver(db)
    dependencies = resolver.get_project_dependencies(project_id)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_dependencies": len(dependencies),
        "dependencies": [
            {
                "id": str(dep.id),
                "component_name": dep.component_name,
                "version": dep.version,
                "source": dep.source,
                "installed": dep.installed,
                "created_at": dep.created_at.isoformat() if dep.created_at else None
            }
            for dep in dependencies
        ]
    }


@router.post("/{project_id}/install-dependencies")
async def install_project_dependencies(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Install all dependencies for a project.
    
    Note: This is a placeholder. Actual installation logic is not yet implemented.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.clone_path or not os.path.exists(project.clone_path):
        raise HTTPException(
            status_code=400,
            detail="Project repository not cloned yet"
        )
    
    try:
        resolver = DependencyResolver(db)
        successful, failed, errors = resolver.install_dependencies(
            project_id=project_id,
            project_path=project.clone_path
        )
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "successful_installs": successful,
            "failed_installs": failed,
            "errors": errors,
            "message": "Dependency installation feature is not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to install dependencies: {str(e)}"
        )


@router.get("/{project_id}/dependency-tree")
async def get_dependency_tree(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get dependency tree for a project showing all dependencies.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    resolver = DependencyResolver(db)
    tree = resolver.get_dependency_tree(project_id)
    
    tree['project_name'] = project.name
    
    return tree
