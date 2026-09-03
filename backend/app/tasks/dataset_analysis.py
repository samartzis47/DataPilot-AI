from celery import Task

from app.core.celery_app import celery_app
from app.crud.dataset_analysis import create_dataset_analysis
from app.crud.processing_job import (
    get_processing_job,
    mark_processing_job_failed,
    mark_processing_job_retrying,
    mark_processing_job_running,
    mark_processing_job_succeeded,
)
from app.db.session import SessionLocal
from app.services.dataset_analysis import build_dataset_profile


@celery_app.task(
    bind=True,
    name="app.tasks.dataset_analysis.process_dataset_analysis",
    max_retries=3,
)
def process_dataset_analysis(
    self: Task,
    job_id: int,
    dataset_id: int,
) -> int | None:
    db = SessionLocal()
    job = None

    try:
        job = get_processing_job(
            db,
            dataset_id=dataset_id,
            job_id=job_id,
        )

        if job is None:
            raise ValueError("Processing job not found")

        if job.status == "succeeded":
            return job.analysis_id

        mark_processing_job_running(db, job)

        profile = build_dataset_profile(
            db,
            dataset_id=dataset_id,
        )

        analysis = create_dataset_analysis(
            db,
            profile,
            commit=False,
        )

        mark_processing_job_succeeded(
            db,
            job,
            analysis_id=analysis.id,
        )

        return analysis.id

    except Exception as exc:
        db.rollback()

        if self.request.retries >= self.max_retries:
            if job is not None:
                mark_processing_job_failed(
                    db,
                    job,
                    error_message=str(exc),
                )

            raise

        if job is not None:
            mark_processing_job_retrying(
                db,
                job,
                error_message=str(exc),
            )

        countdown_seconds = min(
            2 ** self.request.retries,
            60,
        )

        raise self.retry(
            exc=exc,
            countdown=countdown_seconds,
        )

    finally:
        db.close()