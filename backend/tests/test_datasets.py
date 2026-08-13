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