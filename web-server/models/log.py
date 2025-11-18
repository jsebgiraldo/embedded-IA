"""Log Pydantic models."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class LogLevel(str, Enum):
    """Log level enum."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class LogBase(BaseModel):
    """Base log model."""
    level: LogLevel
    message: str
    agent_id: Optional[str] = None
    job_id: Optional[int] = None
    meta_data: Optional[str] = None


class LogCreate(LogBase):
    """Log creation model."""
    pass


class LogResponse(LogBase):
    """Log response model."""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True
