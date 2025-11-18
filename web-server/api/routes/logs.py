"""Log management endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from database.db import get_db, Log as DBLog
from models.log import LogResponse, LogCreate

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=List[LogResponse])
async def list_logs(
    limit: int = 100,
    offset: int = 0,
    level: Optional[str] = None,
    agent_id: Optional[str] = None,
    job_id: Optional[int] = None,
    since_minutes: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List logs with optional filtering."""
    query = db.query(DBLog).order_by(desc(DBLog.timestamp))
    
    if level:
        query = query.filter(DBLog.level == level)
    if agent_id:
        query = query.filter(DBLog.agent_id == agent_id)
    if job_id:
        query = query.filter(DBLog.job_id == job_id)
    if since_minutes:
        since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
        query = query.filter(DBLog.timestamp >= since_time)
    
    logs = query.offset(offset).limit(limit).all()
    return logs


@router.post("", response_model=LogResponse)
async def create_log(log: LogCreate, db: Session = Depends(get_db)):
    """Create a new log entry."""
    db_log = DBLog(
        level=log.level.value,
        message=log.message,
        agent_id=log.agent_id,
        job_id=log.job_id,
        meta_data=log.meta_data
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.delete("")
async def clear_logs(
    older_than_hours: Optional[int] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Clear logs with optional filtering."""
    query = db.query(DBLog)
    
    if older_than_hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        query = query.filter(DBLog.timestamp < cutoff_time)
    if agent_id:
        query = query.filter(DBLog.agent_id == agent_id)
    
    count = query.delete()
    db.commit()
    
    return {"status": "success", "message": f"Deleted {count} log entries"}
