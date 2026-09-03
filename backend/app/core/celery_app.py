from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "datapilot",
    broker=settings.redis_url,
)

celery_app.conf.update(
        imports=(
        "app.tasks.dataset_analysis",
    ),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_ignore_result=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
    enable_utc=True,
)