from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.api.deps import get_yolo_service
from backend.app.main import app
from backend.app.services.yolo import YoloService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_yolo_service():
    mock_service = MagicMock(spec=YoloService)

    mock_service.process_video.return_value = {"status": "success"}

    return mock_service


def test_detect_endpoint_happy_path(client, mock_yolo_service):
    app.dependency_overrides[get_yolo_service] = lambda: mock_yolo_service

    files = {"file": ("test_video.mp4", b"fake video content", "video/mp4")}
    response = client.post("/api/v1/detect", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"

    app.dependency_overrides = {}


def test_status_endpoint_not_found(client):
    response = client.get("/api/v1/status/fake-uuid-12345")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_found"


def test_detect_endpoint_validation_error(client):
    response = client.post("/api/v1/detect")

    assert response.status_code == 422
