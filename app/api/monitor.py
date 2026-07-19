from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.job import Job
from app.schemas.monitor import SystemMetrics, QueueMetrics, DatabaseMetrics
from app.core.redis import redis_client

router = APIRouter(prefix="/monitor", tags=["Monitor"])

@router.get("/", response_model=SystemMetrics)
def get_system_metrics(db: Session = Depends(get_db)):
    # 1. Gather Redis Queue Lengths (Instantaneous pressure)
    high_len = redis_client.llen("queue:high") or 0
    medium_len = redis_client.llen("queue:medium") or 0
    low_len = redis_client.llen("queue:low") or 0
    
    # 2. Gather Postgres Historical Statuses (The Truth)
    # SQLAlchemy GROUP BY query: SELECT status, count(id) FROM jobs GROUP BY status
    status_aggregation = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    
    status_counts = {}
    total_db_jobs = 0
    for status_enum, count in status_aggregation:
        status_name = status_enum.value
        status_counts[status_name] = count
        total_db_jobs += count

    # Make sure all statuses have at least a 0 count if missing, for frontend simplicity
    for s in ["queued", "running", "completed", "failed", "retrying", "dead_letter"]:
        if s not in status_counts:
            status_counts[s] = 0

    return SystemMetrics(
        redis_queues=QueueMetrics(
            high_priority=high_len,
            medium_priority=medium_len,
            low_priority=low_len,
            total_waiting=high_len + medium_len + low_len
        ),
        postgres_jobs=DatabaseMetrics(
            status_counts=status_counts,
            total_tracked=total_db_jobs
        )
    )
