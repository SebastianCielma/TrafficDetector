import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.models.task import Task
from backend.app.services.file import FileService
from backend.app.services.task import TaskService
from backend.app.services.workflow import process_video_workflow
from backend.app.services.yolo import YoloService


@pytest.fixture
def mock_db_session():
    session = AsyncMock()

    context_manager = MagicMock()
    context_manager.__aenter__.return_value = session
    context_manager.__aexit__.return_value = None

    with patch(
        "backend.app.services.workflow.async_session_factory", new_callable=MagicMock
    ) as factory:
        factory.return_value = context_manager
        yield session


@pytest.fixture
def mock_task_service():
    service = AsyncMock(spec=TaskService)
    service.get_task.return_value = Task(input_filename="test.mp4")

    with patch("backend.app.services.workflow.TaskService", return_value=service):
        yield service


@pytest.fixture
def mock_yolo_service():
    service = MagicMock(spec=YoloService)
    with patch("backend.app.services.workflow.YoloService", return_value=service):
        yield service


@pytest.fixture
def mock_file_service():
    service = MagicMock(spec=FileService)
    service.upload_file_to_s3 = AsyncMock(return_value="s3_key_ignored")
    service.cleanup_local_file = MagicMock()

    with patch("backend.app.services.workflow.FileService", return_value=service):
        yield service


@pytest.fixture
def mock_threadpool():
    with patch(
        "backend.app.services.workflow.run_in_threadpool", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.mark.asyncio
async def test_workflow_success_s3_upload(
    mock_db_session,
    mock_task_service,
    mock_yolo_service,
    mock_file_service,
    mock_threadpool,
):
    task_id = uuid.uuid4()
    input_path = "/tmp/in.mp4"
    output_path = "/tmp/out.mp4"

    await process_video_workflow(task_id, input_path, output_path)

    mock_threadpool.assert_awaited_once()

    mock_file_service.upload_file_to_s3.assert_awaited_once_with(
        output_path, "results/out.mp4"
    )

    mock_task_service.mark_completed.assert_awaited_once()
    args = mock_task_service.mark_completed.call_args[0]
    assert args[1] == "results/out.mp4"

    assert mock_file_service.cleanup_local_file.call_count == 2


@pytest.mark.asyncio
async def test_workflow_failure(
    mock_db_session,
    mock_task_service,
    mock_yolo_service,
    mock_file_service,
    mock_threadpool,
):
    task_id = uuid.uuid4()
    mock_threadpool.side_effect = Exception("GPU Boom")

    await process_video_workflow(task_id, "in.mp4", "out.mp4")

    mock_task_service.mark_failed.assert_awaited_once()
    args = mock_task_service.mark_failed.call_args[0]
    assert "GPU Boom" in args[1]

    assert mock_file_service.cleanup_local_file.call_count == 2
