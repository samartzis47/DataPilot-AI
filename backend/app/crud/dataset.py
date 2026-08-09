from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate
from sqlalchemy import select

def create_dataset(db: Session, dataset_in: DatasetCreate) -> Dataset:
    dataset = Dataset(
        original_filename=dataset_in.original_filename,
        content_type=dataset_in.content_type,
        size_bytes=dataset_in.size_bytes,
        )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset

def get_dataset(db: Session, dataset_id: int) -> Dataset | None:
        return db.get(Dataset, dataset_id)

def get_datasets(db: Session) -> list[Dataset]:
    statement = select(Dataset)
    return list(db.scalars(statement).all())