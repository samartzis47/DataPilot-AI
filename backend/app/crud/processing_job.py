from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.processing_job import ProcessingJob


def create_processing_job(
    db: Session,
    *,
    dataset_id: int,
    task_id: str,
) -> ProcessingJob:
    job = ProcessingJob(
        dataset_id=dataset_id,
        task_id=task_id,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_processing_job(
    db: Session,
    *,
    dataset_id: int,
    job_id: int,
) -> ProcessingJob | None:
    statement = select(ProcessingJob).where(
        ProcessingJob.id == job_id,
        ProcessingJob.dataset_id == dataset_id,
    )

    return db.scalar(statement)


def get_processing_jobs(
    db: Session,
    *,
    dataset_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[ProcessingJob]:
    statement = (
        select(ProcessingJob)
        .where(ProcessingJob.dataset_id == dataset_id)
        .order_by(ProcessingJob.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def mark_processing_job_running(
    db: Session,
    job: ProcessingJob,
) -> ProcessingJob:
    job.status = "running"
    job.attempt_count += 1
    job.started_at = datetime.now(timezone.utc)
    job.finished_at = None
    job.error_message = None

    db.commit()
    db.refresh(job)

    return job


def mark_processing_job_retrying(
    db: Session,
    job: ProcessingJob,
    *,
    error_message: str,
) -> ProcessingJob:
    job.status = "retrying"
    job.error_message = error_message

    db.commit()
    db.refresh(job)

    return job


def mark_processing_job_succeeded(
    db: Session,
    job: ProcessingJob,
    *,
    analysis_id: int,
) -> ProcessingJob:
    job.status = "succeeded"
    job.analysis_id = analysis_id
    job.error_message = None
    job.finished_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    return job


def mark_processing_job_failed(
    db: Session,
    job: ProcessingJob,
    *,
    error_message: str,
) -> ProcessingJob:
    job.status = "failed"
    job.error_message = error_message
    job.finished_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    return job