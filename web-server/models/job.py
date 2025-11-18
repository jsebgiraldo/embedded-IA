"""Job Pydantic models."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class JobStatus(str, Enum):
    """Job status enum."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobBase(BaseModel):
    """Base job model."""
    job_type: str  # fix_build, test_suite, analysis
    agent_id: Optional[str] = None
    model_used: Optional[str] = None


class JobCreate(JobBase):
    """Job creation model."""
    pass


class JobResponse(JobBase):
    """Job response model."""
    id: int
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
