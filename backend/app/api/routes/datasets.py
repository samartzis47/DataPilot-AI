from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db 
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.dataset import DatasetRead, DatasetCreate
from app.crud.dataset import get_datasets, get_dataset, create_dataset

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
)

@router.get("", response_model=list[DatasetRead])
def list_datasets(
    db: Annotated[Session, Depends(get_db)],
):
    return get_datasets(db)

@router.get("/{dataset_id}", response_model=DatasetRead)
def read_dataset(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    dataset = get_dataset(db, dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")    
    return dataset

@router.post(
    "",
    response_model=DatasetRead,
    status_code=status.HTTP_201_CREATED,    
)
def create_dataset_endpoint(
    dataset_in: DatasetCreate,
    db: Annotated[Session, Depends(get_db)],
):
    return create_dataset(db, dataset_in)