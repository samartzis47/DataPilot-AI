import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud.dataset_analysis import (
    create_dataset_analysis,
    get_dataset_analysis,
)
from app.db.base import Base
from app.models.dataset import Dataset
from app.schemas.dataset_analysis import DatasetAnalysisRead
from app.schemas.profile import DatasetProfile
from app.services.data_profiler import profile_dataframe


@pytest.fixture
def analysis_session_factory():
    engine = create_engine("sqlite://")

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(bind=engine)
        yield sessionmaker(bind=engine, expire_on_commit=False)
    finally:
        engine.dispose()


def test_analysis_is_persisted_and_scoped_to_dataset(
    analysis_session_factory,
):
    with analysis_session_factory() as db:
        dataset = Dataset(
            original_filename="sales.csv",
            content_type="text/csv",
            size_bytes=100,
        )
        db.add(dataset)
        db.commit()
        dataset_id = dataset.id

        dataframe = pd.DataFrame(
            {"value": [10, 11, 12, 13, 1000, None]}
        )
        profile = DatasetProfile(
            dataset_id=dataset_id,
            original_filename=dataset.original_filename,
            **profile_dataframe(dataframe),
        )
        expected_report = profile.model_dump(mode="json")

        analysis = create_dataset_analysis(db, profile)
        analysis_id = analysis.id

    with analysis_session_factory() as db:
        stored = get_dataset_analysis(
            db,
            dataset_id=dataset_id,
            analysis_id=analysis_id,
        )

        assert stored is not None
        assert stored.dataset_id == dataset_id
        assert stored.report == expected_report

        response = DatasetAnalysisRead.model_validate(stored)
        assert response.id == analysis_id
        assert response.created_at is not None
        assert response.report == profile

        wrong_dataset_result = get_dataset_analysis(
            db,
            dataset_id=dataset_id + 1,
            analysis_id=analysis_id,
        )
        assert wrong_dataset_result is None