"""Job management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from database.db import get_db, Job as DBJob
from models.job import JobResponse, JobCreate, JobStatus

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering."""
    query = db.query(DBJob).order_by(desc(DBJob.created_at))
    
    if status:
        query = query.filter(DBJob.status == status)
    if agent_id:
        query = query.filter(DBJob.agent_id == agent_id)
    
    jobs = query.offset(offset).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job by ID."""
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", response_model=JobResponse)
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new job."""
    db_job = DBJob(
        job_type=job.job_type,
        agent_id=job.agent_id,
        model_used=job.model_used,
        status=JobStatus.PENDING.value
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.post("/{job_id}/start")
async def start_job(job_id: int, db: Session = Depends(get_db)):
    """Start a job."""
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = JobStatus.RUNNING.value
    job.started_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "message": f"Job {job_id} started"}


@router.post("/{job_id}/complete")
async def complete_job(
    job_id: int,
    success: bool = True,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Complete a job."""
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = JobStatus.SUCCESS.value if success else JobStatus.FAILED.value
    job.completed_at = datetime.utcnow()
    if job.started_at:
        job.duration = (job.completed_at - job.started_at).total_seconds()
    if error_message:
        job.error_message = error_message
    db.commit()
    
    return {"status": "success", "message": f"Job {job_id} completed"}


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """Cancel a job."""
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.utcnow()
    if job.started_at:
        job.duration = (job.completed_at - job.started_at).total_seconds()
    db.commit()
    
    return {"status": "success", "message": f"Job {job_id} cancelled"}


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job."""
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    
    return {"status": "success", "message": f"Job {job_id} deleted"}
