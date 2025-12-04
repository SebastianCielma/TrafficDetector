import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.models.task import Task
from backend.app.services.workflow import process_video_workflow


@pytest.mark.asyncio
async def test_workflow_success_s3_upload():
    task_id = uuid.uuid4()

    mock_task_service = AsyncMock()
    mock_task_service.get_task.return_value = Task(input_filename="test.mp4")

    mock_yolo_service = MagicMock()

    mock_file_service_instance = MagicMock()

    mock_file_service_instance.upload_file_to_s3 = AsyncMock(
        return_value="ignored_return_value"
    )
    mock_file_service_instance.cleanup_local_file = MagicMock()

    with (
        patch(
            "backend.app.services.workflow.async_session_factory"
        ) as mock_session_fac,
        patch(
            "backend.app.services.workflow.TaskService", return_value=mock_task_service
        ),
        patch(
            "backend.app.services.workflow.YoloService", return_value=mock_yolo_service
        ),
        patch(
            "backend.app.services.workflow.FileService",
            return_value=mock_file_service_instance,
        ),
        patch(
            "backend.app.services.workflow.run_in_threadpool", new_callable=AsyncMock
        ) as mock_threadpool,
    ):
        mock_session = AsyncMock()
        mock_session_fac.return_value.__aenter__.return_value = mock_session

        await process_video_workflow(task_id, "/tmp/in.mp4", "/tmp/out.mp4")

        mock_threadpool.assert_awaited_once()

        mock_file_service_instance.upload_file_to_s3.assert_awaited_once_with(
            "/tmp/out.mp4", "results/out.mp4"
        )

        mock_task_service.mark_completed.assert_awaited_once()
        args = mock_task_service.mark_completed.call_args[0]
        assert args[1] == "results/out.mp4"

        assert mock_file_service_instance.cleanup_local_file.call_count == 2


@pytest.mark.asyncio
async def test_workflow_failure():
    task_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session_fac = MagicMock()
    mock_session_fac.return_value.__aenter__.return_value = mock_session

    mock_task_service = AsyncMock()
    mock_task_service.get_task.return_value = Task(input_filename="test.mp4")

    mock_run_in_threadpool = AsyncMock(side_effect=Exception("GPU Boom"))

    with (
        patch("backend.app.services.workflow.async_session_factory", mock_session_fac),
        patch(
            "backend.app.services.workflow.TaskService", return_value=mock_task_service
        ),
        patch("backend.app.services.workflow.YoloService"),
        patch("backend.app.services.workflow.FileService"),
        patch(
            "backend.app.services.workflow.run_in_threadpool", mock_run_in_threadpool
        ),
    ):
        await process_video_workflow(task_id, "in.mp4", "out.mp4")

        mock_task_service.mark_failed.assert_awaited_once()
        args = mock_task_service.mark_failed.call_args[0]
        assert "GPU Boom" in args[1]
