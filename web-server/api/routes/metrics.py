"""Metrics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database.db import get_db, Metric as DBMetric, Job as DBJob, Agent as DBAgent
from models.metric import MetricResponse, MetricCreate

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("", response_model=List[MetricResponse])
async def list_metrics(
    limit: int = 100,
    offset: int = 0,
    metric_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    since_hours: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List metrics with optional filtering."""
    query = db.query(DBMetric).order_by(desc(DBMetric.timestamp))
    
    if metric_type:
        query = query.filter(DBMetric.metric_type == metric_type)
    if agent_id:
        query = query.filter(DBMetric.agent_id == agent_id)
    if since_hours:
        since_time = datetime.utcnow() - timedelta(hours=since_hours)
        query = query.filter(DBMetric.timestamp >= since_time)
    
    metrics = query.offset(offset).limit(limit).all()
    return metrics


@router.post("", response_model=MetricResponse)
async def create_metric(metric: MetricCreate, db: Session = Depends(get_db)):
    """Create a new metric entry."""
    db_metric = DBMetric(
        metric_type=metric.metric_type,
        value=metric.value,
        agent_id=metric.agent_id,
        meta_data=metric.meta_data
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


@router.get("/summary", response_model=Dict[str, Any])
async def get_metrics_summary(
    since_hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get aggregated metrics summary."""
    since_time = datetime.utcnow() - timedelta(hours=since_hours)
    
    # Job statistics
    total_jobs = db.query(func.count(DBJob.id)).filter(
        DBJob.created_at >= since_time
    ).scalar()
    
    successful_jobs = db.query(func.count(DBJob.id)).filter(
        DBJob.created_at >= since_time,
        DBJob.status == "success"
    ).scalar()
    
    failed_jobs = db.query(func.count(DBJob.id)).filter(
        DBJob.created_at >= since_time,
        DBJob.status == "failed"
    ).scalar()
    
    # Average duration
    avg_duration = db.query(func.avg(DBJob.duration)).filter(
        DBJob.created_at >= since_time,
        DBJob.duration.isnot(None)
    ).scalar()
    
    # Success rate
    success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    # Active agents
    active_agents = db.query(func.count(DBAgent.id)).filter(
        DBAgent.status == "active"
    ).scalar()
    
    total_agents = db.query(func.count(DBAgent.id)).scalar()
    
    # Model usage (from jobs)
    model_usage = db.query(
        DBJob.model_used,
        func.count(DBJob.id)
    ).filter(
        DBJob.created_at >= since_time,
        DBJob.model_used.isnot(None)
    ).group_by(DBJob.model_used).all()
    
    model_usage_dict = {model: count for model, count in model_usage}
    
    return {
        "time_period_hours": since_hours,
        "jobs": {
            "total": total_jobs,
            "successful": successful_jobs,
            "failed": failed_jobs,
            "success_rate": round(success_rate, 1)
        },
        "performance": {
            "avg_duration_seconds": round(avg_duration, 1) if avg_duration else 0
        },
        "agents": {
            "active": active_agents,
            "total": total_agents
        },
        "model_usage": model_usage_dict
    }
