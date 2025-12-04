import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.api.deps import get_file_service, get_task_service
from backend.app.models.task import Task, TaskStatus


@pytest.fixture
def mock_file_service():
    mock = MagicMock()
    mock.save_upload = AsyncMock(return_value="/tmp/uploads/test.mp4")
    mock.get_result_path.return_value = "/tmp/results/test.mp4"
    return mock


@pytest.mark.asyncio
async def test_debug_routes_listing(client):
    from backend.app.main import app

    found = False
    for route in app.routes:
        path = getattr(route, "path", str(route))
        print(f"   ➡️ {path}")
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

    from backend.app.main import app

    app.dependency_overrides[get_task_service] = override_task_service
    app.dependency_overrides[get_file_service] = override_file_service

    with patch("backend.app.api.v1.router.process_video_workflow") as mock_workflow:
        files = {"file": ("video.mp4", b"fake content", "video/mp4")}

        response = await client.post("/api/v1/detect", files=files)

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"

        assert mock_workflow.called

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_status_endpoint(client):
    target_uuid = uuid.uuid4()
    task_obj = Task(
        id=target_uuid,
        status=TaskStatus.COMPLETED,
        input_filename="test.mp4",
        result_url="/results/test.mp4",
    )

    local_mock_service = AsyncMock()
    local_mock_service.get_task.return_value = task_obj

    async def override_get_task_service():
        return local_mock_service

    from backend.app.main import app

    app.dependency_overrides[get_task_service] = override_get_task_service

    url = f"/api/v1/status/{str(target_uuid)}"
    print(f"DEBUG: Calling {url}")

    response = await client.get(url)

    if response.status_code != 200:
        print(f"DEBUG FAIL RESPONSE: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["id"] == str(target_uuid)

    local_mock_service.get_task.assert_awaited_once_with(target_uuid)

    app.dependency_overrides = {}
