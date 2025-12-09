import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.api.deps import get_file_service, get_task_service
from backend.app.core.security import verify_api_key
from backend.app.models.task import Task, TaskStatus
from backend.app.worker import celery_process_video


@pytest.fixture
def mock_file_service():
    mock = MagicMock()
    mock.save_upload_locally = AsyncMock(return_value="/tmp/uploads/test.mp4")
    mock.get_result_path_local = MagicMock(return_value="/tmp/results/test.mp4")
    mock.generate_presigned_url = AsyncMock(return_value="https://cdn.fake/video.mp4")
    return mock


@pytest.mark.asyncio
async def test_debug_routes_listing(client):
    from backend.app.main import app

    found = False
    for route in app.routes:
        path = getattr(route, "path", str(route))
        if "status" in path:
            found = True
    assert found is True


@pytest.mark.asyncio
async def test_detect_endpoint(client, mock_file_service):
    local_mock_task_service = AsyncMock()
    local_mock_task_service.create_task.return_value = Task(
        id=uuid.uuid4(), status=TaskStatus.QUEUED, input_filename="test.mp4"
    )

    async def override_task_service():
        return local_mock_task_service

    def override_file_service():
        return mock_file_service

    async def override_security():
        return "bypass-key"

    from backend.app.main import app

    app.dependency_overrides[get_task_service] = override_task_service
    app.dependency_overrides[get_file_service] = override_file_service
    app.dependency_overrides[verify_api_key] = override_security

    with patch.object(celery_process_video, "delay") as mock_delay:
        files = {"file": ("video.mp4", b"fake content", "video/mp4")}

        response = await client.post("/api/v1/detect", files=files)

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"

        mock_delay.assert_called_once()

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_status_endpoint(client, mock_file_service):
    target_uuid = uuid.uuid4()
    task_obj = Task(
        id=target_uuid,
        status=TaskStatus.COMPLETED,
        input_filename="test.mp4",
        result_url="s3_key/video.mp4",
    )

    local_task_service = AsyncMock()
    local_task_service.get_task.return_value = task_obj

    async def override_task():
        return local_task_service

    async def override_security():
        return "bypass-key"

    from backend.app.main import app

    app.dependency_overrides[get_task_service] = override_task
    app.dependency_overrides[get_file_service] = lambda: mock_file_service
    app.dependency_overrides[verify_api_key] = override_security

    url = f"/api/v1/status/{str(target_uuid)}"

    response = await client.get(url, follow_redirects=True)

    assert response.status_code == 200
    data = response.json()
    assert data["result_url"] == "https://cdn.fake/video.mp4"

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_security_rejection(client):
    from backend.app.main import app

    app.dependency_overrides.pop(verify_api_key, None)

    files = {"file": ("video.mp4", b"fake", "video/mp4")}
    response = await client.post("/api/v1/detect", files=files)

    assert response.status_code == 403
