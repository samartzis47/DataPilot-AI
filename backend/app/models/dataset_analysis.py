from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DatasetAnalysis(Base):
    __tablename__ = "dataset_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    report: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
    )