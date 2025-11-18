"""Metric Pydantic models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MetricBase(BaseModel):
    """Base metric model."""
    metric_type: str  # success_rate, avg_time, model_usage
    value: float
    agent_id: Optional[str] = None
    meta_data: Optional[str] = None


class MetricCreate(MetricBase):
    """Metric creation model."""
    pass


class MetricResponse(MetricBase):
    """Metric response model."""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True
