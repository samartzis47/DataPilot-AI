from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset_analysis import DatasetAnalysis
from app.schemas.profile import DatasetProfile


def create_dataset_analysis(
    db: Session,
    profile: DatasetProfile,
) -> DatasetAnalysis:
    analysis = DatasetAnalysis(
        dataset_id=profile.dataset_id,
        report=profile.model_dump(mode="json"),
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


def get_dataset_analysis(
    db: Session,
    *,
    dataset_id: int,
    analysis_id: int,
) -> DatasetAnalysis | None:
    statement = select(DatasetAnalysis).where(
        DatasetAnalysis.id == analysis_id,
        DatasetAnalysis.dataset_id == dataset_id,
    )

    return db.scalar(statement)