"""Agent Pydantic models."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AgentStatus(str, Enum):
    """Agent status enum."""
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"


class AgentBase(BaseModel):
    """Base agent model."""
    name: str
    type: str  # developer, test, build
    status: AgentStatus = AgentStatus.IDLE


class AgentCreate(AgentBase):
    """Agent creation model."""
    id: str


class AgentResponse(AgentBase):
    """Agent response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None
    
    class Config:
        from_attributes = True
