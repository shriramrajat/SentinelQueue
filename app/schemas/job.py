from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.job import JobStatus, JobPriority

class JobCreate(BaseModel):
    task_name: str
    payload: Dict[str, Any] = {}
    priority: JobPriority = JobPriority.MEDIUM
    execute_at: Optional[datetime] = None

class JobResponse(BaseModel):
    id: UUID
    task_name: str
    status: JobStatus
    priority: JobPriority
    execute_at: Optional[datetime] = None
    created_at: datetime
    
    # We allow returning ORM models directly
    model_config = ConfigDict(from_attributes=True)
