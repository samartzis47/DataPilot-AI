from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        index=True,
        nullable=False,
    )

    analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("dataset_analyses.id"),
        nullable=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        default="dataset_profile",
        server_default="dataset_profile",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="queued",
        server_default="queued",
        index=True,
        nullable=False,
    )

    task_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )