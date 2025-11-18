"""
Project and Repository models for GitHub integration.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Database Models (Pydantic for API)
# ============================================================================

class ProjectBase(BaseModel):
    """Base project model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    repo_url: str = Field(..., description="GitHub repository URL")
    repo_full_name: str = Field(..., description="owner/repo format")
    branch: str = Field(default="main", description="Git branch to track")
    target: str = Field(default="esp32", description="ESP32 target chip")
    build_system: str = Field(default="cmake", description="Build system")


class ProjectCreate(ProjectBase):
    """Project creation model."""
    webhook_secret: Optional[str] = Field(None, description="Secret for webhook validation")


class ProjectUpdate(BaseModel):
    """Project update model."""
    description: Optional[str] = None
    branch: Optional[str] = None
    target: Optional[str] = None
    status: Optional[str] = None
    webhook_secret: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Project response model."""
    id: str
    clone_path: str
    last_commit_sha: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    status: str  # pending, active, error, archived
    created_at: datetime
    updated_at: datetime
    
    # Additional computed fields
    builds_count: Optional[int] = 0
    last_build_status: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProjectWithDetails(ProjectResponse):
    """Project with full details including dependencies and metrics."""
    dependencies: List["DependencyResponse"] = []
    recent_builds: List["BuildResponse"] = []
    metrics: Optional[dict] = None


# ============================================================================
# Dependency Models
# ============================================================================

class DependencyBase(BaseModel):
    """Base dependency model."""
    component_name: str
    version: str
    source: str  # registry, git, local
    git_url: Optional[str] = None
    git_ref: Optional[str] = None


class DependencyCreate(DependencyBase):
    """Dependency creation model."""
    project_id: str


class DependencyResponse(DependencyBase):
    """Dependency response model."""
    id: int
    project_id: str
    installed: bool
    installed_at: Optional[datetime] = None
    install_error: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Build Models
# ============================================================================

class BuildBase(BaseModel):
    """Base build model."""
    commit_sha: str
    commit_message: Optional[str] = None
    commit_author: Optional[str] = None
    branch: str


class BuildCreate(BuildBase):
    """Build creation model."""
    project_id: str
    triggered_by: str  # webhook, manual, scheduled
    github_event_type: Optional[str] = None


class BuildUpdate(BaseModel):
    """Build update model."""
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    build_output: Optional[str] = None
    test_results: Optional[str] = None
    artifacts_path: Optional[str] = None


class BuildResponse(BuildBase):
    """Build response model."""
    id: int
    project_id: str
    status: str  # pending, running, success, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    triggered_by: str
    github_event_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class BuildWithDetails(BuildResponse):
    """Build with full output and test results."""
    build_output: Optional[str] = None
    test_results: Optional[dict] = None
    artifacts_path: Optional[str] = None


# ============================================================================
# Webhook Models
# ============================================================================

class WebhookEventBase(BaseModel):
    """Base webhook event model."""
    event_type: str
    event_id: str
    payload: dict


class WebhookEventCreate(WebhookEventBase):
    """Webhook event creation model."""
    project_id: Optional[str] = None
    signature_valid: bool = False


class WebhookEventUpdate(BaseModel):
    """Webhook event update model."""
    status: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WebhookEventResponse(WebhookEventBase):
    """Webhook event response model."""
    id: int
    project_id: Optional[str] = None
    status: str  # pending, processing, success, failed
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    signature_valid: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Request/Response Models
# ============================================================================

class SyncProjectResponse(BaseModel):
    """Response from project sync operation."""
    status: str
    previous_commit: Optional[str] = None
    current_commit: str
    changes: dict = Field(default_factory=dict)


class TriggerBuildRequest(BaseModel):
    """Request to trigger a manual build."""
    trigger: str = Field(default="manual", description="Build trigger source")
    commit_sha: Optional[str] = Field(None, description="Specific commit to build")


class TriggerBuildResponse(BaseModel):
    """Response from build trigger."""
    build_id: int
    status: str
    project_id: str
    commit_sha: str


class WebhookReceivedResponse(BaseModel):
    """Response from webhook endpoint."""
    status: str = "received"
    event_id: str
    event_type: str
    queued: bool = True


class ProjectMetrics(BaseModel):
    """Project metrics summary."""
    total_builds: int = 0
    success_rate: float = 0.0
    avg_build_time: float = 0.0
    last_7_days_builds: int = 0


class ProjectListResponse(BaseModel):
    """Response for project list."""
    projects: List[ProjectResponse]
    total: int


class BuildListResponse(BaseModel):
    """Response for build list."""
    builds: List[BuildResponse]
    total: int
