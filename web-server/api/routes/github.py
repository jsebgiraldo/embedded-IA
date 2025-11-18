"""
GitHub Webhook routes.
Handles incoming webhooks from GitHub.
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, Header, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from database.db import get_db, Project, WebhookEvent, Build
from models.project import WebhookReceivedResponse
from services.webhook_service import WebhookService
from services.repository_manager import RepositoryManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github", tags=["github"])

# Initialize services
webhook_service = WebhookService()
repo_manager = RepositoryManager()


@router.post("/webhook", response_model=WebhookReceivedResponse)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db)
):
    """
    Receive webhook from GitHub.
    
    Headers:
    - X-GitHub-Event: Type of event (push, pull_request, ping)
    - X-GitHub-Delivery: Unique delivery ID
    - X-Hub-Signature-256: HMAC signature for validation
    
    Returns webhook received confirmation immediately,
    processes event in background.
    """
    logger.info(f"📨 Received webhook: {x_github_event} (delivery: {x_github_delivery})")
    
    # Read raw body for signature validation
    body = await request.body()
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Extract project identifier from payload
    repo_full_name = webhook_service.extract_project_identifier(payload)
    
    if not repo_full_name:
        raise HTTPException(status_code=400, detail="Could not extract repository info")
    
    # Find project by repo_full_name
    project = db.query(Project).filter(
        Project.repo_full_name == repo_full_name
    ).first()
    
    # Validate signature if project exists and has secret
    signature_valid = False
    if project and project.webhook_secret:
        signature_valid = webhook_service.validate_signature(
            payload=body,
            signature=x_hub_signature_256 or "",
            secret=project.webhook_secret
        )
        
        if not signature_valid:
            logger.error(f"❌ Invalid webhook signature for project {project.name}")
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        # No project or no secret configured, accept anyway
        signature_valid = True
        if not project:
            logger.warning(f"⚠️ No project found for repository: {repo_full_name}")
    
    # Create webhook event record
    webhook_event = WebhookEvent(
        project_id=project.id if project else None,
        event_type=x_github_event,
        event_id=x_github_delivery,
        payload=json.dumps(payload),
        signature_valid=signature_valid,
        status="pending"
    )
    
    db.add(webhook_event)
    db.commit()
    db.refresh(webhook_event)
    
    # Process event in background
    background_tasks.add_task(
        process_webhook_event,
        webhook_event_id=webhook_event.id,
        event_type=x_github_event,
        payload=payload,
        project_id=project.id if project else None
    )
    
    logger.info(f"✅ Webhook queued for processing: {webhook_event.id}")
    
    return WebhookReceivedResponse(
        status="received",
        event_id=x_github_delivery,
        event_type=x_github_event,
        queued=True
    )


async def process_webhook_event(
    webhook_event_id: int,
    event_type: str,
    payload: dict,
    project_id: Optional[str]
):
    """
    Process webhook event in background.
    
    Steps:
    1. Parse event payload
    2. Determine if build should be triggered
    3. Sync repository
    4. Create build record
    5. Trigger workflow
    6. Update webhook event status
    """
    logger.info(f"🔄 Processing webhook event {webhook_event_id}")
    
    # Get database session
    from database.db import SessionLocal
    db = SessionLocal()
    
    try:
        webhook_event = db.query(WebhookEvent).filter(
            WebhookEvent.id == webhook_event_id
        ).first()
        
        if not webhook_event:
            logger.error(f"❌ Webhook event {webhook_event_id} not found")
            return
        
        webhook_event.status = "processing"
        db.commit()
        
        # Get project
        if not project_id:
            webhook_event.status = "failed"
            webhook_event.error_message = "No project associated with this webhook"
            db.commit()
            logger.warning("⚠️ No project for webhook, skipping")
            return
        
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            webhook_event.status = "failed"
            webhook_event.error_message = f"Project {project_id} not found"
            db.commit()
            logger.error(f"❌ Project {project_id} not found")
            return
        
        # Parse event
        if event_type == "push":
            event_data = webhook_service.parse_push_event(payload)
        elif event_type == "pull_request":
            event_data = webhook_service.parse_pull_request_event(payload)
        elif event_type == "ping":
            # Ping events are just health checks
            webhook_event.status = "success"
            webhook_event.processed_at = db.func.now()
            db.commit()
            logger.info("✅ Ping event processed")
            return
        else:
            webhook_event.status = "failed"
            webhook_event.error_message = f"Unsupported event type: {event_type}"
            db.commit()
            logger.warning(f"⚠️ Unsupported event: {event_type}")
            return
        
        # Check if build should be triggered
        if not webhook_service.should_trigger_build(event_type, event_data):
            webhook_event.status = "success"
            webhook_event.processed_at = db.func.now()
            db.commit()
            logger.info(f"ℹ️ Event does not trigger build: {event_type}")
            return
        
        # Sync repository
        logger.info(f"📥 Syncing repository for project {project.name}")
        sync_result = await repo_manager.update_repository(
            clone_path=project.clone_path,
            branch=event_data.get("branch") or project.branch
        )
        
        if not sync_result["success"]:
            webhook_event.status = "failed"
            webhook_event.error_message = f"Failed to sync repository: {sync_result.get('error')}"
            db.commit()
            logger.error(f"❌ Failed to sync repository: {sync_result.get('error')}")
            return
        
        # Update project
        project.last_commit_sha = sync_result["current_commit"]
        project.last_synced_at = db.func.now()
        db.commit()
        
        # Create build record
        build = Build(
            project_id=project_id,
            commit_sha=event_data.get("commit_sha"),
            commit_message=event_data.get("commit_message"),
            commit_author=event_data.get("commit_author"),
            branch=event_data.get("branch") or project.branch,
            triggered_by="webhook",
            github_event_type=event_type,
            status="pending"
        )
        
        db.add(build)
        db.commit()
        db.refresh(build)
        
        logger.info(f"✅ Build #{build.id} created for project {project.name}")
        
        # TODO: Trigger workflow orchestrator
        # await workflow_dispatcher.trigger_build(project, build)
        
        # Mark webhook as successfully processed
        webhook_event.status = "success"
        webhook_event.processed_at = db.func.now()
        db.commit()
        
        logger.info(f"✅ Webhook event {webhook_event_id} processed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook {webhook_event_id}: {e}")
        
        webhook_event.status = "failed"
        webhook_event.error_message = str(e)
        db.commit()
        
    finally:
        db.close()


@router.get("/webhook/test")
async def test_webhook():
    """Test endpoint to verify webhook receiver is working."""
    return {
        "status": "ok",
        "message": "Webhook receiver is active",
        "endpoint": "/api/github/webhook"
    }
