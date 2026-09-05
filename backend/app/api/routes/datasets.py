from uuid import uuid4
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from app.api.dependencies import get_db
from app.core.config import settings
from app.crud.processing_job import (
    create_processing_job,
    get_processing_job,
    get_processing_jobs,
    mark_processing_job_failed,
)
from app.crud.dataset import (
    create_dataset,
    create_uploaded_dataset,
    get_dataset,
    get_datasets,
)
from app.crud.dataset_analysis import (
    create_dataset_analysis,
    get_dataset_analyses,
    get_dataset_analysis,
)
from app.crud.dataset_insight import (
    create_dataset_insight,
    get_dataset_insight,
    get_dataset_insights,
    get_newest_dataset_analysis,
)
from app.crud.cleaned_dataset import (
    create_cleaned_dataset,
    get_cleaned_dataset,
    get_cleaned_datasets,
)
from app.schemas.dataset import DatasetCreate, DatasetRead
from app.schemas.cleaned_dataset import CleaningRequest, CleanedDatasetRead
from app.schemas.dataset_analysis import DatasetAnalysisRead
from app.schemas.dataset_insight import (
    DatasetInsightRead,
    InsightGenerationRequest,
)
from app.schemas.profile import DatasetProfile
from app.services.dataset_analysis import (
    DatasetFileNotFoundError,
    DatasetNotFoundError,
    DatasetProfilingError,
    DatasetWithoutUploadedFileError,
    build_dataset_profile,
    get_dataset_file_path,
)
from app.services.file_storage import (
    FileTooLargeError,
    InvalidFileError,
    delete_stored_file,
    save_csv_file,
)
from app.services.data_cleaning import (
    DatasetCleaningError,
    clean_dataset_file,
    delete_cleaned_file,
)
from app.schemas.processing_job import ProcessingJobRead
from app.tasks.dataset_analysis import process_dataset_analysis
from app.services.insight_generation import (
    InsightGenerationError,
    InsightProviderNotConfiguredError,
    generate_insight,
)

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
    "/{dataset_id}/cleanings",
    response_model=CleanedDatasetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cleaning(
    dataset_id: int,
    cleaning_request: CleaningRequest,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        dataset, source_path = get_dataset_file_path(db, dataset_id=dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DatasetWithoutUploadedFileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DatasetFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        output_filename, stored_filename, summary = clean_dataset_file(
            source_path,
            dataset.original_filename,
            cleaning_request,
        )
    except DatasetCleaningError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return create_cleaned_dataset(
            db,
            dataset_id=dataset_id,
            original_filename=output_filename,
            stored_filename=stored_filename,
            cleaning_config=cleaning_request.model_dump(),
            summary=summary,
            original_row_count=summary["original_row_count"],
            cleaned_row_count=summary["cleaned_row_count"],
        )
    except Exception:
        db.rollback()
        delete_cleaned_file(stored_filename)
        raise


@router.get(
    "/{dataset_id}/cleanings",
    response_model=list[CleanedDatasetRead],
)
def list_cleanings(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if get_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return get_cleaned_datasets(db, dataset_id=dataset_id, limit=limit, offset=offset)


@router.get(
    "/{dataset_id}/cleanings/{cleaning_id}",
    response_model=CleanedDatasetRead,
)
def read_cleaning(
    dataset_id: int,
    cleaning_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    if get_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    cleaning = get_cleaned_dataset(db, dataset_id=dataset_id, cleaning_id=cleaning_id)
    if cleaning is None:
        raise HTTPException(status_code=404, detail="Cleaning not found")
    return cleaning


@router.get("/{dataset_id}/cleanings/{cleaning_id}/download")
def download_cleaning(
    dataset_id: int,
    cleaning_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    if get_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    cleaning = get_cleaned_dataset(db, dataset_id=dataset_id, cleaning_id=cleaning_id)
    if cleaning is None:
        raise HTTPException(status_code=404, detail="Cleaning not found")
    file_path = settings.cleaned_dir / Path(cleaning.stored_filename).name
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Cleaned file not found")
    return FileResponse(file_path, media_type="text/csv", filename=cleaning.original_filename)

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

def _build_dataset_profile(
    dataset_id: int,
    db: Session,
) -> DatasetProfile:
    try:
        return build_dataset_profile(
            db,
            dataset_id=dataset_id,
        )
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DatasetWithoutUploadedFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DatasetFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DatasetProfilingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
def get_dataset_profile(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    return _build_dataset_profile(dataset_id, db)
@router.post(
    "/{dataset_id}/analyses",
    response_model=DatasetAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_analysis_endpoint(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    profile = _build_dataset_profile(dataset_id, db)
    return create_dataset_analysis(db, profile)
@router.post(
    "/{dataset_id}/analysis-jobs",
    response_model=ProcessingJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_analysis_job(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        get_dataset_file_path(
            db,
            dataset_id=dataset_id,
        )
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DatasetWithoutUploadedFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except DatasetFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    task_id = str(uuid4())

    job = create_processing_job(
        db,
        dataset_id=dataset_id,
        task_id=task_id,
    )

    try:
        process_dataset_analysis.apply_async(
            kwargs={
                "job_id": job.id,
                "dataset_id": dataset_id,
            },
            task_id=task_id,
        )
    except Exception as exc:
        mark_processing_job_failed(
            db,
            job,
            error_message="Analysis queue unavailable",
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis queue unavailable",
        ) from exc

    return job

@router.get(
    "/{dataset_id}/analysis-jobs",
    response_model=list[ProcessingJobRead],
)
def list_analysis_jobs(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    dataset = get_dataset(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return get_processing_jobs(
        db,
        dataset_id=dataset_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{dataset_id}/analysis-jobs/{job_id}",
    response_model=ProcessingJobRead,
)
def read_analysis_job(
    dataset_id: int,
    job_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    dataset = get_dataset(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    job = get_processing_job(
        db,
        dataset_id=dataset_id,
        job_id=job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found",
        )

    return job

@router.get(
    "/{dataset_id}/analyses",
    response_model=list[DatasetAnalysisRead],
)
def list_dataset_analyses_endpoint(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    dataset = get_dataset(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return get_dataset_analyses(
        db,
        dataset_id=dataset_id,
        limit=limit,
        offset=offset,
    )



@router.get(
    "/{dataset_id}/analyses/{analysis_id}",
    response_model=DatasetAnalysisRead,
)
def read_dataset_analysis(
    dataset_id: int,
    analysis_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    dataset = get_dataset(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    analysis = get_dataset_analysis(
        db,
        dataset_id=dataset_id,
        analysis_id=analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset analysis not found",
        )

    return analysis


@router.post(
    "/{dataset_id}/insights",
    response_model=DatasetInsightRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_insight_endpoint(
    dataset_id: int,
    request: InsightGenerationRequest,
    db: Annotated[Session, Depends(get_db)],
):
    if get_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if request.analysis_id is None:
        analysis = get_newest_dataset_analysis(db, dataset_id=dataset_id)
        if analysis is None:
            raise HTTPException(
                status_code=409, detail="Dataset has no persisted analysis"
            )
    else:
        analysis = get_dataset_analysis(
            db, dataset_id=dataset_id, analysis_id=request.analysis_id
        )
        if analysis is None:
            raise HTTPException(
                status_code=404, detail="Dataset analysis not found"
            )

    try:
        payload, model = generate_insight(
            analysis.report, provider=request.provider
        )
    except InsightProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=503,
            detail="OpenAI insight provider is not configured",
        ) from exc
    except InsightGenerationError as exc:
        raise HTTPException(
            status_code=502, detail="Insight generation failed"
        ) from exc

    try:
        return create_dataset_insight(
            db,
            dataset_id=dataset_id,
            analysis_id=analysis.id,
            provider=request.provider,
            model=model,
            payload=payload,
        )
    except Exception:
        db.rollback()
        raise


@router.get(
    "/{dataset_id}/insights",
    response_model=list[DatasetInsightRead],
)
def list_dataset_insights_endpoint(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if get_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return get_dataset_insights(
        db, dataset_id=dataset_id, limit=limit, offset=offset
    )


@router.get(
    "/{dataset_id}/insights/{insight_id}",
    response_model=DatasetInsightRead,
)
def read_dataset_insight(
    dataset_id: int,
    insight_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    if get_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    insight = get_dataset_insight(
        db, dataset_id=dataset_id, insight_id=insight_id
    )
    if insight is None:
        raise HTTPException(status_code=404, detail="Dataset insight not found")
    return insight



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
