import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.models.task import Task
from backend.app.services.file import FileService
from backend.app.services.task import TaskService
from backend.app.services.workflow import process_video_workflow
from backend.app.services.yolo import YoloService


@pytest.mark.asyncio
async def test_workflow_success_analytics_upload(mock_db_session_factory):
    mock_factory, mock_session = mock_db_session_factory
    task_id = uuid.uuid4()

    # Mocki
    mock_task_service = AsyncMock(spec=TaskService)
    mock_task_service.get_task.return_value = Task(input_filename="test.mp4")

    mock_yolo_service = MagicMock(spec=YoloService)

    mock_file_service = MagicMock(spec=FileService)
    mock_file_service.upload_file_to_s3 = AsyncMock()
    mock_file_service.cleanup_local_file = AsyncMock()

    with (
        patch("backend.app.services.workflow.async_session_factory", mock_factory),
        patch(
            "backend.app.services.workflow.TaskService", return_value=mock_task_service
        ),
        patch(
            "backend.app.services.workflow.YoloService", return_value=mock_yolo_service
        ),
        patch(
            "backend.app.services.workflow.FileService", return_value=mock_file_service
        ),
        patch(
            "backend.app.services.workflow.run_in_threadpool", new_callable=AsyncMock
        ) as mock_thread,
        patch("backend.app.services.workflow.os.path.exists", return_value=True),
    ):
        mock_thread.return_value = "/tmp/analytics.json"

        await process_video_workflow(task_id, "/tmp/in.mp4", "/tmp/out.mp4")

        mock_file_service.upload_file_to_s3.assert_any_await(
            "/tmp/out.mp4", "results/out.mp4"
        )

        mock_file_service.upload_file_to_s3.assert_any_await(
            "/tmp/analytics.json", f"analytics/{task_id}.json"
        )

        mock_file_service.cleanup_local_file.assert_any_await("/tmp/analytics.json")
