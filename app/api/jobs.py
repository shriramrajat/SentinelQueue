from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse
from app.core.redis import redis_client

router = APIRouter(prefix="/jobs", tags=["Jobs"])

from datetime import datetime, timezone
from app.models.job import JobStatus

@router.post("/", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    is_future = job_in.execute_at and job_in.execute_at > datetime.now(timezone.utc)
    
    # 1. Write to Postgres
    new_job = Job(
        task_name=job_in.task_name,
        payload=job_in.payload,
        priority=job_in.priority,
        execute_at=job_in.execute_at,
        status=JobStatus.SCHEDULED if is_future else JobStatus.QUEUED
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # 2. Push to Redis only if it's not a future job
    if not is_future:
        queue_name = f"queue:{new_job.priority.value}"
        redis_client.lpush(queue_name, str(new_job.id))
        
    # 3. Return instantly
    return new_job

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
