from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset_analysis import DatasetAnalysis
from app.models.dataset_insight import DatasetInsight
from app.schemas.dataset_insight import GeneratedInsightPayload


def create_dataset_insight(
    db: Session,
    *,
    dataset_id: int,
    analysis_id: int,
    provider: str,
    model: str | None,
    payload: GeneratedInsightPayload,
) -> DatasetInsight:
    insight = DatasetInsight(
        dataset_id=dataset_id,
        analysis_id=analysis_id,
        provider=provider,
        model=model,
        summary=payload.summary,
        insights=[item.model_dump(mode="json") for item in payload.insights],
        recommendations=[
            item.model_dump(mode="json") for item in payload.recommendations
        ],
    )
    db.add(insight)
    try:
        db.commit()
        db.refresh(insight)
    except Exception:
        db.rollback()
        raise
    return insight


def get_dataset_insight(
    db: Session, *, dataset_id: int, insight_id: int
) -> DatasetInsight | None:
    return db.scalar(
        select(DatasetInsight).where(
            DatasetInsight.id == insight_id,
            DatasetInsight.dataset_id == dataset_id,
        )
    )


def get_dataset_insights(
    db: Session, *, dataset_id: int, limit: int = 20, offset: int = 0
) -> list[DatasetInsight]:
    statement = (
        select(DatasetInsight)
        .where(DatasetInsight.dataset_id == dataset_id)
        .order_by(DatasetInsight.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_newest_dataset_analysis(
    db: Session, *, dataset_id: int
) -> DatasetAnalysis | None:
    return db.scalar(
        select(DatasetAnalysis)
        .where(DatasetAnalysis.dataset_id == dataset_id)
        .order_by(DatasetAnalysis.id.desc())
        .limit(1)
    )