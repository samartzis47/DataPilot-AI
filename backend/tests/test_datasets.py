import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.db.base import Base 
from app.main import app


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
def reset_test_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)

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