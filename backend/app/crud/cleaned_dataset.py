from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cleaned_dataset import CleanedDataset


def create_cleaned_dataset(
    db: Session,
    *,
    dataset_id: int,
    original_filename: str,
    stored_filename: str,
    cleaning_config: dict[str, object],
    summary: dict[str, int],
    original_row_count: int,
    cleaned_row_count: int,
) -> CleanedDataset:
    cleaned_dataset = CleanedDataset(
        dataset_id=dataset_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        cleaning_config=cleaning_config,
        summary=summary,
        original_row_count=original_row_count,
        cleaned_row_count=cleaned_row_count,
    )
    db.add(cleaned_dataset)
    db.commit()
    db.refresh(cleaned_dataset)
    return cleaned_dataset


def get_cleaned_dataset(
    db: Session,
    *,
    dataset_id: int,
    cleaning_id: int,
) -> CleanedDataset | None:
    statement = select(CleanedDataset).where(
        CleanedDataset.id == cleaning_id,
        CleanedDataset.dataset_id == dataset_id,
    )
    return db.scalar(statement)


def get_cleaned_datasets(
    db: Session,
    *,
    dataset_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[CleanedDataset]:
    statement = (
        select(CleanedDataset)
        .where(CleanedDataset.dataset_id == dataset_id)
        .order_by(CleanedDataset.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())