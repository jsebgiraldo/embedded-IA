"""
Build Orchestration Service

Integrates GitHub projects with the AgentOrchestrator to execute
complete build/test/QA workflows.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from database.db import Project, Build
from agent.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class BuildOrchestrationService:
    """
    Service to orchestrate builds using the AgentOrchestrator.
    
    This service connects the GitHub project management system with
    the existing agent-based workflow for building, testing, and validating
    ESP32 projects.
    """
    
    def __init__(self, orchestrator: AgentOrchestrator):
        """
        Initialize build orchestration service.
        
        Args:
            orchestrator: Initialized AgentOrchestrator instance
        """
        self.orchestrator = orchestrator
        logger.info("🚀 BuildOrchestrationService initialized")
    
    async def execute_build(
        self,
        db: Session,
        build_id: int,
        project: Project,
        flash_device: bool = False,
        run_qemu: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a complete build workflow for a project.
        
        This orchestrates the full pipeline:
        1. Set target chip
        2. Build firmware
        3. Run tests (QEMU and/or hardware)
        4. QA validation
        5. Generate artifacts
        
        Args:
            db: Database session
            build_id: Build ID to track
            project: Project instance
            flash_device: Whether to flash to physical hardware
            run_qemu: Whether to run QEMU simulation
            
        Returns:
            Dictionary with build results
        """
        build = db.query(Build).filter(Build.id == build_id).first()
        
        if not build:
            raise ValueError(f"Build {build_id} not found")
        
        logger.info(f"🔨 Starting build #{build_id} for project {project.name}")
        
        # Update build status
        build.status = "running"
        build.started_at = datetime.utcnow()
        db.commit()
        
        try:
            # Execute workflow using orchestrator
            result = await self.orchestrator.execute_workflow(
                project_path=project.clone_path,
                target=project.target,
                flash_device=flash_device,
                run_qemu=run_qemu,
                job_id=build_id
            )
            
            # Update build with results
            build.completed_at = datetime.utcnow()
            
            # Calculate duration
            if build.started_at:
                duration = (build.completed_at - build.started_at).total_seconds()
                build.duration = duration
            
            # Determine final status from workflow result
            if result.get("success", False):
                build.status = "success"
                logger.info(f"✅ Build #{build_id} completed successfully")
            else:
                build.status = "failed"
                logger.error(f"❌ Build #{build_id} failed")
            
            # Store artifacts and outputs
            if "artifacts" in result:
                build.artifacts_path = str(result["artifacts"])
            
            if "build_output" in result:
                build.build_output = result["build_output"]
            
            if "test_results" in result:
                build.test_results = str(result["test_results"])
            
            db.commit()
            
            return {
                "build_id": build_id,
                "status": build.status,
                "duration": build.duration,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing build #{build_id}: {e}")
            
            # Update build status to failed
            build.status = "failed"
            build.completed_at = datetime.utcnow()
            
            if build.started_at:
                duration = (build.completed_at - build.started_at).total_seconds()
                build.duration = duration
            
            build.build_output = f"Error: {str(e)}"
            db.commit()
            
            return {
                "build_id": build_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def execute_build_background(
        self,
        db: Session,
        build_id: int,
        project_id: str,
        flash_device: bool = False,
        run_qemu: bool = True
    ):
        """
        Execute build in background without blocking the API response.
        
        This is called by FastAPI BackgroundTasks to run builds asynchronously.
        
        Args:
            db: Database session
            build_id: Build ID
            project_id: Project UUID
            flash_device: Whether to flash hardware
            run_qemu: Whether to run QEMU
        """
        try:
            # Get fresh project instance
            project = db.query(Project).filter(Project.id == project_id).first()
            
            if not project:
                logger.error(f"Project {project_id} not found")
                return
            
            # Execute build
            await self.execute_build(
                db=db,
                build_id=build_id,
                project=project,
                flash_device=flash_device,
                run_qemu=run_qemu
            )
            
        except Exception as e:
            logger.error(f"Background build execution error: {e}")
    
    def validate_project_for_build(self, project: Project) -> tuple[bool, Optional[str]]:
        """
        Validate that a project is ready to be built.
        
        Args:
            project: Project instance
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if project.status != "active":
            return False, f"Project status is '{project.status}', must be 'active'"
        
        if not project.clone_path:
            return False, "Project has no clone path"
        
        if not os.path.exists(project.clone_path):
            return False, f"Clone path does not exist: {project.clone_path}"
        
        # Check for CMakeLists.txt (required for ESP-IDF projects)
        cmake_path = os.path.join(project.clone_path, "CMakeLists.txt")
        if not os.path.exists(cmake_path):
            return False, "Project missing CMakeLists.txt (not a valid ESP-IDF project)"
        
        return True, None
    
    async def retry_failed_build(
        self,
        db: Session,
        build_id: int,
        flash_device: bool = False,
        run_qemu: bool = True
    ) -> Dict[str, Any]:
        """
        Retry a failed build.
        
        Args:
            db: Database session
            build_id: Build ID to retry
            flash_device: Whether to flash hardware
            run_qemu: Whether to run QEMU
            
        Returns:
            Build results
        """
        build = db.query(Build).filter(Build.id == build_id).first()
        
        if not build:
            raise ValueError(f"Build {build_id} not found")
        
        if build.status != "failed":
            raise ValueError(f"Build {build_id} is not in failed state, cannot retry")
        
        project = db.query(Project).filter(Project.id == build.project_id).first()
        
        if not project:
            raise ValueError(f"Project {build.project_id} not found")
        
        logger.info(f"🔄 Retrying failed build #{build_id}")
        
        # Reset build state
        build.status = "pending"
        build.started_at = None
        build.completed_at = None
        build.duration = None
        build.build_output = None
        build.test_results = None
        db.commit()
        
        # Execute build
        return await self.execute_build(
            db=db,
            build_id=build_id,
            project=project,
            flash_device=flash_device,
            run_qemu=run_qemu
        )
    
    def get_build_stats(self, db: Session, project_id: str) -> Dict[str, Any]:
        """
        Get build statistics for a project.
        
        Args:
            db: Database session
            project_id: Project UUID
            
        Returns:
            Dictionary with build stats
        """
        builds = db.query(Build).filter(Build.project_id == project_id).all()
        
        total = len(builds)
        successful = len([b for b in builds if b.status == "success"])
        failed = len([b for b in builds if b.status == "failed"])
        pending = len([b for b in builds if b.status == "pending"])
        running = len([b for b in builds if b.status == "running"])
        
        # Calculate average duration for completed builds
        completed_builds = [b for b in builds if b.duration is not None]
        avg_duration = None
        if completed_builds:
            avg_duration = sum(b.duration for b in completed_builds) / len(completed_builds)
        
        return {
            "project_id": project_id,
            "total_builds": total,
            "successful": successful,
            "failed": failed,
            "pending": pending,
            "running": running,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_duration": avg_duration
        }


def create_build_orchestration_service(orchestrator: AgentOrchestrator) -> BuildOrchestrationService:
    """
    Factory function to create BuildOrchestrationService.
    
    Args:
        orchestrator: Initialized AgentOrchestrator
        
    Returns:
        BuildOrchestrationService instance
    """
    return BuildOrchestrationService(orchestrator)
