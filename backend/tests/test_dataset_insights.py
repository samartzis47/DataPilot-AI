import json
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.models.dataset import Dataset
from app.models.dataset_analysis import DatasetAnalysis
from app.models.dataset_insight import DatasetInsight
from app.schemas.dataset_insight import GeneratedInsightPayload
from app.services.insight_generation import (
    InsightGenerationError,
    OpenAIInsightProvider,
    RulesInsightProvider,
)


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def database():
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


def report(score=72.5, *, marker="first"):
    return {
        "dataset_id": 1,
        "original_filename": "sales.csv",
        "row_count": 10,
        "column_count": 2,
        "duplicate_row_count": 2,
        "preview": [{"customer": marker}],
        "quality": {
            "score": score,
            "missing_cell_count": 3,
            "completeness_percentage": 85,
            "duplicate_percentage": 20,
            "issues": [
                {"code": "missing_values", "severity": "medium", "message": "3 missing cells"},
                {"code": "duplicate_rows", "severity": "high", "message": "2 duplicate rows"},
                {"code": "numeric_outliers", "severity": "high", "message": "Outliers found", "column": "revenue"},
            ],
        },
        "columns": [
            {"name": "revenue", "data_type": "float64", "missing_count": 2, "missing_percentage": 20,
             "unique_count": 8, "numeric_statistics": {"outlier_count": 3, "outlier_percentage": 30}},
            {"name": "constant", "data_type": "string", "missing_count": 0, "missing_percentage": 0,
             "unique_count": 1, "numeric_statistics": None},
        ],
    }


def add_dataset_with_analyses(count=1):
    with SessionLocal() as db:
        dataset = Dataset(original_filename="sales.csv", content_type="text/csv", size_bytes=10)
        db.add(dataset)
        db.flush()
        for index in range(count):
            db.add(DatasetAnalysis(dataset_id=dataset.id, report=report(marker=str(index))))
        db.commit()
        return dataset.id


def test_rules_provider_is_deterministic_and_structured():
    provider = RulesInsightProvider()
    first = provider.generate(report())
    second = provider.generate(report())

    assert first == second
    assert first.summary == "sales.csv contains 10 rows and 2 columns. Its persisted data-quality score is 72.50/100."
    categories = {item.category for item in first.insights}
    assert {"quality", "missing_values", "duplicates", "outliers", "columns"} <= categories
    assert any(item.priority == "high" for item in first.recommendations)


def test_create_insight_selects_newest_analysis_and_preserves_source():
    dataset_id = add_dataset_with_analyses(2)
    with SessionLocal() as db:
        analyses = list(db.scalars(select(DatasetAnalysis).order_by(DatasetAnalysis.id)).all())
        source_reports = [analysis.report.copy() for analysis in analyses]

    response = client.post(f"/datasets/{dataset_id}/insights", json={})

    assert response.status_code == 201
    body = response.json()
    assert body["analysis_id"] == analyses[-1].id
    assert body["provider"] == "rules"
    with SessionLocal() as db:
        assert [analysis.report for analysis in db.scalars(select(DatasetAnalysis).order_by(DatasetAnalysis.id)).all()] == source_reports


def test_explicit_analysis_selection_and_history_pagination():
    dataset_id = add_dataset_with_analyses(2)
    with SessionLocal() as db:
        analysis_ids = [analysis.id for analysis in db.scalars(select(DatasetAnalysis).order_by(DatasetAnalysis.id)).all()]

    for analysis_id in analysis_ids:
        assert client.post(f"/datasets/{dataset_id}/insights", json={"analysis_id": analysis_id}).status_code == 201
    assert client.post(f"/datasets/{dataset_id}/insights", json={"analysis_id": analysis_ids[0]}).status_code == 201

    response = client.get(f"/datasets/{dataset_id}/insights?limit=2&offset=1")
    assert response.status_code == 200
    assert [item["analysis_id"] for item in response.json()] == [analysis_ids[1], analysis_ids[0]]

    insight_id = response.json()[0]["id"]
    assert client.get(f"/datasets/{dataset_id}/insights/{insight_id}").json()["id"] == insight_id
    assert client.get(f"/datasets/{dataset_id + 1}/insights/{insight_id}").status_code == 404


def test_missing_insight_is_scoped_to_existing_dataset():
    dataset_id = add_dataset_with_analyses()

    response = client.get(f"/datasets/{dataset_id}/insights/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Dataset insight not found"}


@pytest.mark.parametrize(
    ("path", "payload", "status", "detail"),
    [
        ("/datasets/999/insights", {}, 404, "Dataset not found"),
        ("/datasets/1/insights", {}, 409, "Dataset has no persisted analysis"),
        ("/datasets/1/insights", {"analysis_id": 999}, 404, "Dataset analysis not found"),
        ("/datasets/1/insights/999", None, 404, "Dataset not found"),
    ],
)
def test_insight_error_responses(path, payload, status, detail):
    if path == "/datasets/1/insights":
        add_dataset_with_analyses(0 if status == 409 else 1)
    response = client.post(path, json=payload) if payload is not None else client.get(path)
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_invalid_provider_and_unconfigured_openai():
    dataset_id = add_dataset_with_analyses()
    invalid = client.post(f"/datasets/{dataset_id}/insights", json={"provider": "other"})
    assert invalid.status_code == 422

    old_key = settings.openai_api_key
    settings.openai_api_key = None
    try:
        response = client.post(f"/datasets/{dataset_id}/insights", json={"provider": "openai"})
    finally:
        settings.openai_api_key = old_key
    assert response.status_code == 503
    assert response.json() == {"detail": "OpenAI insight provider is not configured"}


def test_provider_failure_returns_502_and_persists_nothing(monkeypatch):
    dataset_id = add_dataset_with_analyses()
    monkeypatch.setattr(
        "app.api.routes.datasets.generate_insight",
        lambda report, provider: (_ for _ in ()).throw(InsightGenerationError()),
    )
    response = client.post(f"/datasets/{dataset_id}/insights", json={})
    assert response.status_code == 502
    assert response.json() == {"detail": "Insight generation failed"}
    with SessionLocal() as db:
        assert db.scalars(select(DatasetInsight)).first() is None


def test_mocked_openai_structured_output_excludes_preview(monkeypatch):
    captured = {}

    class FakeResponses:
        def parse(self, **kwargs):
            captured["input"] = kwargs["input"]
            return SimpleNamespace(output_parsed=GeneratedInsightPayload(
                summary="structured", insights=[], recommendations=[]
            ))

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    old_key = settings.openai_api_key
    settings.openai_api_key = "test-key"
    try:
        payload = OpenAIInsightProvider().generate(report())
    finally:
        settings.openai_api_key = old_key

    assert payload.summary == "structured"
    request_text = captured["input"][1]["content"]
    assert "preview" not in json.loads(request_text)
    assert "customer" not in request_text
