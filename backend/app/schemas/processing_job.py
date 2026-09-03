from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


JobStatus = Literal[
    "queued",
    "running",
    "retrying",
    "succeeded",
    "failed",
]


class ProcessingJobRead(BaseModel):
    id: int
    dataset_id: int
    analysis_id: int | None
    job_type: Literal["dataset_profile"]
    status: JobStatus
    task_id: str | None
    attempt_count: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)