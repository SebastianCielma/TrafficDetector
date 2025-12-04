import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.models.task import Task
from backend.app.services.workflow import process_video_workflow


@pytest.mark.asyncio
async def test_workflow_success():
    task_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    mock_task_service = AsyncMock()
    mock_task_service.get_task.return_value = Task(input_filename="test.mp4")

    mock_yolo_service = MagicMock()

    with (
        patch(
            "backend.app.services.workflow.async_session_factory", mock_session_factory
        ),
        patch(
            "backend.app.services.workflow.TaskService", return_value=mock_task_service
        ),
        patch(
            "backend.app.services.workflow.YoloService", return_value=mock_yolo_service
        ),
    ):
        await process_video_workflow(task_id, "in.mp4", "out.mp4")

        mock_task_service.get_task.assert_awaited_once_with(task_id)

        mock_task_service.mark_processing.assert_awaited_once()

        mock_yolo_service.process_video.assert_called_once_with("in.mp4", "out.mp4")

        mock_task_service.mark_completed.assert_awaited_once()


@pytest.mark.asyncio
async def test_workflow_failure():
    task_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    mock_task_service = AsyncMock()
    mock_task_service.get_task.return_value = Task(input_filename="test.mp4")

    mock_yolo_service = MagicMock()
    mock_yolo_service.process_video.side_effect = Exception("GPU Boom")

    with (
        patch(
            "backend.app.services.workflow.async_session_factory", mock_session_factory
        ),
        patch(
            "backend.app.services.workflow.TaskService", return_value=mock_task_service
        ),
        patch(
            "backend.app.services.workflow.YoloService", return_value=mock_yolo_service
        ),
    ):
        await process_video_workflow(task_id, "in.mp4", "out.mp4")

        mock_task_service.mark_failed.assert_awaited_once()
        args = mock_task_service.mark_failed.call_args[0]
        assert "GPU Boom" in args[1]
