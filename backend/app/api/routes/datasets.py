from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db 
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.dataset import DatasetRead, DatasetCreate
from app.crud.dataset import get_datasets, get_dataset, create_dataset, create_uploaded_dataset
from app.services.file_storage import (
    FileTooLargeError,
    InvalidFileError,
    delete_stored_file,
    save_csv_file,
)

from app.core.config import settings
from app.schemas.profile import DatasetProfile
from app.services.data_profiler import InvalidCSVError, profile_csv

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
)

@router.get("", response_model=list[DatasetRead])
def list_datasets(
    db: Annotated[Session, Depends(get_db)],
):
    return get_datasets(db)

@router.post(
    "/upload",
    response_model=DatasetRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
):
    original_filename = Path(file.filename or "").name
    content_type = file.content_type or "application/octet-stream"

    try:
        stored_filename, size_bytes = await save_csv_file(file)
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except InvalidFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return create_uploaded_dataset(
            db,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=size_bytes,
        )
    except Exception:
        delete_stored_file(stored_filename)
        raise

@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
def get_dataset_profile(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    dataset = get_dataset(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    if dataset.stored_filename is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset has no uploaded file",
        )

    file_path = settings.upload_dir / Path(dataset.stored_filename).name

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found",
        )

    try:
        profile = profile_csv(file_path)
    except InvalidCSVError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "dataset_id": dataset.id,
        "original_filename": dataset.original_filename,
        **profile,
    }

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
