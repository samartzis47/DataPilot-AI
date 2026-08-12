from typing import Annotated
from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session

from app.api.dependencies import get_db 
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.dataset import DatasetRead
from app.crud.dataset import get_datasets

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
)

@router.get("", response_model=list[DatasetRead])
def list_datasets(
    db: Annotated[Session, Depends(get_db)],
):
    return get_datasets(db)