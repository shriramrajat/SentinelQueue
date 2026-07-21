from app.workers.main import process_job
from app.models.job import Job, JobStatus, JobPriority

def test_process_job_success(db_session):
    # 1. Insert a job directly into the DB
    job = Job(
        task_name="generate_pdf",
        payload={"user_id": 99},
        status=JobStatus.QUEUED
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    # 2. Process it
    process_job(str(job.id))
    
    # 3. Verify it completed
    db_session.refresh(job)
    assert job.status == JobStatus.COMPLETED
    assert job.error_message is None
    assert job.retry_count == 0

def test_process_job_dead_letter(db_session, mock_redis):
    # 1. Insert a failing job
    job = Job(
        task_name="generate_pdf",
        payload={"force_fail": True},
        status=JobStatus.QUEUED
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    job_id = str(job.id)
    
    # Attempt 1
    process_job(job_id)
    db_session.refresh(job)
    assert job.status == JobStatus.RETRYING
    assert job.retry_count == 1
    mock_redis.lpush.assert_called_once_with("queue:medium", job_id)
    
    # Reset mock for next call
    mock_redis.reset_mock()
    
    # Attempt 2
    process_job(job_id)
    db_session.refresh(job)
    assert job.status == JobStatus.RETRYING
    assert job.retry_count == 2
    mock_redis.lpush.assert_called_once_with("queue:medium", job_id)
    
    mock_redis.reset_mock()
    
    # Attempt 3 (Should max out retries and go to DLQ)
    process_job(job_id)
    db_session.refresh(job)
    assert job.status == JobStatus.DEAD_LETTER
    assert job.retry_count == 3
    # Should NOT be pushed back to Redis
    mock_redis.lpush.assert_not_called()
