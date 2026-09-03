from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.dataset import get_dataset
from app.models.dataset import Dataset
from app.schemas.profile import DatasetProfile
from app.services.data_profiler import InvalidCSVError, profile_csv


class DatasetNotFoundError(Exception):
    pass


class DatasetWithoutUploadedFileError(Exception):
    pass


class DatasetFileNotFoundError(Exception):
    pass


class DatasetProfilingError(Exception):
    pass


def get_dataset_file_path(
    db: Session,
    *,
    dataset_id:int,
) -> tuple[Dataset, Path]:
    dataset = get_dataset(db, dataset_id)

    if dataset is None:
        raise DatasetNotFoundError("Dataset not found")

    if dataset.stored_filename is None:
        raise DatasetWithoutUploadedFileError(
            "Dataset has no uploaded file"
        )

    file_path = settings.upload_dir / Path(
        dataset.stored_filename
    ).name

    if not file_path.is_file():
        raise DatasetFileNotFoundError(
            "Dataset file not found"
        )

    return dataset, file_path


def build_dataset_profile(
    db: Session,
    *,
    dataset_id: int,
) -> DatasetProfile:
    dataset, file_path = get_dataset_file_path(
        db,
        dataset_id=dataset_id,
    )

    try:
        profile = profile_csv(file_path)
    except InvalidCSVError as exc:
        raise DatasetProfilingError(str(exc)) from exc

    return DatasetProfile(
        dataset_id=dataset.id,
        original_filename=dataset.original_filename,
        **profile,
    )