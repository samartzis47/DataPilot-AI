import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.db.base import Base 
from app.main import app
from app.core.config import settings
from app.models.dataset import Dataset


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_test_environment(tmp_path):
    original_upload_dir = settings.upload_dir
    settings.upload_dir = tmp_path / "uploads"

    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)
    settings.upload_dir = original_upload_dir

def test_list_datasets_returns_empty_list():
    response = client.get("/datasets")

    assert response.status_code == 200
    assert response.json() == []

def test_create_dataset():
    payload = {
        "original_filename": "customers.csv",
        "content_type": "text/csv",
        "size_bytes": 180000,
    }

    response = client.post("/datasets", json=payload)

    assert response.status_code == 201

    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["original_filename"] == "customers.csv"
    assert response_data["content_type"] == "text/csv"
    assert response_data["size_bytes"] == 180000

def test_get_existing_dataset():
    create_response = client.post(
        "/datasets",
        json={
            "original_filename": "sales.csv",
            "content_type": "text/csv",
            "size_bytes": 245000,
        },
    )
    dataset_id = create_response.json()["id"]

    response = client.get(f"/datasets/{dataset_id}")

    assert response.status_code == 200
    assert response.json()["id"] == dataset_id
    assert response.json()["original_filename"] == "sales.csv"


def test_get_missing_dataset_returns_404():
    response = client.get("/datasets/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Dataset not found"}

def test_upload_csv_creates_dataset_and_file():
    csv_content = (
        b"customer_id,name,revenue\n"
        b"1,Alice,120.50\n"
        b"2,Bob,89.99\n"
    )

    response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "customers.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 201

    response_data = response.json()
    assert response_data["original_filename"] == "customers.csv"
    assert response_data["content_type"] == "text/csv"
    assert response_data["size_bytes"] == len(csv_content)

    with TestingSessionLocal() as db:
        dataset = db.get(Dataset, response_data["id"])

        assert dataset is not None
        assert dataset.stored_filename is not None

        stored_file = settings.upload_dir / dataset.stored_filename
        assert stored_file.exists()
        assert stored_file.read_bytes() == csv_content

def test_upload_rejects_non_csv_file():
    response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "notes.txt",
                b"This is not a CSV file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only CSV files are allowed"
    }
    assert client.get("/datasets").json() == []


def test_upload_rejects_empty_csv():
    response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "empty.csv",
                b"",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "CSV file is empty"
    }
    assert client.get("/datasets").json() == []

    assert (
        not settings.upload_dir.exists()
        or list(settings.upload_dir.iterdir()) == []
    )

def test_upload_rejects_file_over_size_limit(monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size_bytes", 10)

    response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "large.csv",
                b"12345678901",
                "text/csv",
            )
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "File exceeds the maximum allowed size"
    }
    assert client.get("/datasets").json() == []

    assert (
        not settings.upload_dir.exists()
        or list(settings.upload_dir.iterdir()) == []
    )

def test_profile_uploaded_dataset():
    upload_response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "sales.csv",
                b"name,revenue\nAlice,120.50\nBob,89.99\n",
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    dataset_id = upload_response.json()["id"]

    response = client.get(f"/datasets/{dataset_id}/profile")

    assert response.status_code == 200

    profile = response.json()
    assert profile["dataset_id"] == dataset_id
    assert profile["original_filename"] == "sales.csv"
    assert profile["row_count"] == 2
    assert profile["column_count"] == 2
    assert profile["duplicate_row_count"] == 0
    assert len(profile["columns"]) == 2

    columns_by_name = {
        column["name"]: column
        for column in profile["columns"]
    }

    assert columns_by_name["name"]["numeric_statistics"] is None

    revenue_statistics = columns_by_name["revenue"]["numeric_statistics"]
    assert revenue_statistics["minimum"] == 89.99
    assert revenue_statistics["maximum"] == 120.5
    assert revenue_statistics["mean"] == 105.25
    assert len(profile["preview"]) == 2

    quality = profile["quality"]

    assert quality["score"] == 100.0
    assert quality["missing_cell_count"] == 0
    assert quality["completeness_percentage"] == 100.0
    assert quality["duplicate_percentage"] == 0.0
    assert quality["issues"] == []

def test_profile_missing_dataset():
    response = client.get("/datasets/999/profile")

    assert response.status_code == 404
    assert response.json() == {"detail": "Dataset not found"}


def test_profile_dataset_without_uploaded_file():
    create_response = client.post(
        "/datasets",
        json={
            "original_filename": "metadata.csv",
            "content_type": "text/csv",
            "size_bytes": 100,
        },
    )

    assert create_response.status_code == 201
    dataset_id = create_response.json()["id"]

    response = client.get(f"/datasets/{dataset_id}/profile")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Dataset has no uploaded file"
    }


def test_read_missing_analysis_returns_404():
    create_response = client.post(
        "/datasets",
        json={
            "original_filename": "sales.csv",
            "content_type": "text/csv",
            "size_bytes": 100,
        },
    )

    assert create_response.status_code == 201
    dataset_id = create_response.json()["id"]

    response = client.get(
        f"/datasets/{dataset_id}/analyses/999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Dataset analysis not found"
    }

def test_create_and_read_analysis_without_source_file():
    upload_response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "sales.csv",
                b"name,revenue\nAlice,120.50\nBob,89.99\n",
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    dataset_id = upload_response.json()["id"]

    profile_response = client.get(
        f"/datasets/{dataset_id}/profile"
    )
    assert profile_response.status_code == 200

    create_response = client.post(
        f"/datasets/{dataset_id}/analyses"
    )

    assert create_response.status_code == 201
    analysis = create_response.json()
    assert analysis["id"] > 0
    assert analysis["dataset_id"] == dataset_id
    assert analysis["created_at"] is not None
    assert analysis["report"] == profile_response.json()

    with TestingSessionLocal() as db:
        dataset = db.get(Dataset, dataset_id)
        assert dataset is not None
        assert dataset.stored_filename is not None
        stored_file = settings.upload_dir / dataset.stored_filename

    stored_file.unlink()

    read_response = client.get(
        f"/datasets/{dataset_id}/analyses/{analysis['id']}"
    )

    assert read_response.status_code == 200
    assert read_response.json() == analysis

def test_repeated_analyses_create_separate_snapshots():
    upload_response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "sales.csv",
                b"name,revenue\nAlice,120.50\nBob,89.99\n",
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    dataset_id = upload_response.json()["id"]

    first_response = client.post(
        f"/datasets/{dataset_id}/analyses"
    )
    assert first_response.status_code == 201
    first_analysis = first_response.json()

    with TestingSessionLocal() as db:
        dataset = db.get(Dataset, dataset_id)
        assert dataset is not None
        assert dataset.stored_filename is not None
        stored_file = settings.upload_dir / dataset.stored_filename

    stored_file.write_bytes(
        b"name,revenue\n"
        b"Alice,120.50\n"
        b"Bob,89.99\n"
        b"Charlie,150.00\n"
    )

    second_response = client.post(
        f"/datasets/{dataset_id}/analyses"
    )
    assert second_response.status_code == 201
    second_analysis = second_response.json()

    assert first_analysis["id"] != second_analysis["id"]
    assert first_analysis["report"]["row_count"] == 2
    assert second_analysis["report"]["row_count"] == 3

    first_read_response = client.get(
        f"/datasets/{dataset_id}/analyses/{first_analysis['id']}"
    )
    second_read_response = client.get(
        f"/datasets/{dataset_id}/analyses/{second_analysis['id']}"
    )

    assert first_read_response.status_code == 200
    assert second_read_response.status_code == 200
    assert first_read_response.json() == first_analysis
    assert second_read_response.json() == second_analysis

def test_create_analysis_for_missing_dataset_returns_404():
    response = client.post("/datasets/999/analyses")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Dataset not found"
    }


def test_create_analysis_without_uploaded_file_returns_409():
    create_response = client.post(
        "/datasets",
        json={
            "original_filename": "metadata.csv",
            "content_type": "text/csv",
            "size_bytes": 100,
        },
    )

    assert create_response.status_code == 201
    dataset_id = create_response.json()["id"]

    response = client.post(
        f"/datasets/{dataset_id}/analyses"
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Dataset has no uploaded file"
    }