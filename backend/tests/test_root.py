from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "DataPilot-AI",
        "message": "DataPilot -AI API is running",
        "version": "0.1.0",
        "documentation": "/docs",
    }