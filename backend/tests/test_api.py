import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.api.deps import get_file_service, get_task_service
from backend.app.models.task import Task, TaskStatus


@pytest.fixture
def mock_file_service():
    mock = MagicMock()
    mock.save_upload_locally = AsyncMock(return_value="/tmp/uploads/test.mp4")
    mock.get_result_path_local = MagicMock(return_value="/tmp/results/test.mp4")
    mock.generate_presigned_url = AsyncMock(return_value="https://cdn.fake/video.mp4")
    return mock


@pytest.mark.asyncio
async def test_detect_endpoint_sends_to_celery(client, mock_file_service):
    local_mock_task_service = AsyncMock()
    fixed_uuid = uuid.uuid4()

    local_mock_task_service.create_task.return_value = Task(
        id=fixed_uuid, status=TaskStatus.QUEUED, input_filename="test.mp4"
    )

    async def override_task():
        return local_mock_task_service

    def override_file():
        return mock_file_service

    from backend.app.main import app

    app.dependency_overrides[get_task_service] = override_task
    app.dependency_overrides[get_file_service] = override_file

    with patch("backend.app.api.v1.router.celery_process_video") as mock_celery_task:
        files = {"file": ("video.mp4", b"fake", "video/mp4")}

        response = await client.post("/api/v1/detect", files=files)

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"

        mock_celery_task.delay.assert_called_once_with(
            str(fixed_uuid), "/tmp/uploads/test.mp4", "/tmp/results/test.mp4"
        )

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_status_endpoint(client, mock_file_service):
    target_id = uuid.uuid4()
    task_obj = Task(
        id=target_id,
        status=TaskStatus.COMPLETED,
        input_filename="test.mp4",
        result_url="s3_key/video.mp4",
    )

    local_task_service = AsyncMock()
    local_task_service.get_task.return_value = task_obj

    async def override_task():
        return local_task_service

    def override_file():
        return mock_file_service

    from backend.app.main import app

    app.dependency_overrides[get_task_service] = override_task
    app.dependency_overrides[get_file_service] = override_file

    response = await client.get(f"/api/v1/status/{target_id}")

    assert response.status_code == 200
    assert response.json()["result_url"] == "https://cdn.fake/video.mp4"

    app.dependency_overrides = {}
