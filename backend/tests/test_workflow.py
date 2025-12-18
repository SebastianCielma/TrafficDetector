"""Tests for the video processing workflow."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from backend.app.models.task import Task
from backend.app.services.bigquery import BigQueryService
from backend.app.services.file import FileService
from backend.app.services.task import TaskService
from backend.app.services.workflow import process_video_workflow
from backend.app.services.yolo import YoloService


@pytest.mark.asyncio
async def test_workflow_success_analytics_and_bq(mock_db_session_factory):
    """Full integration test: YOLO -> S3 (Video/JSON) -> BigQuery."""
    # Unpack fixture from conftest.py
    mock_factory, mock_session = mock_db_session_factory
    task_id = uuid.uuid4()

    # --- MOCKS ---
    mock_task_service = AsyncMock(spec=TaskService)
    mock_task_service.get_task.return_value = Task(input_filename="test.mp4")

    mock_yolo_service = MagicMock(spec=YoloService)
    # YOLO returns path to JSON file
    mock_yolo_service.process_video.return_value = "/tmp/analytics.json"

    mock_file_service = MagicMock(spec=FileService)
    mock_file_service.upload_file_to_s3 = AsyncMock()
    mock_file_service.cleanup_local_file = AsyncMock()

    # Mock for BigQuery
    mock_bq_service = MagicMock(spec=BigQueryService)

    # Simulated JSON file data (for BigQuery)
    fake_analytics_data = json.dumps(
        {
            "meta": {
                "source_filename": "test.mp4",
                "fps": 30,
                "total_frames": 100,
                "resolution": [1920, 1080],
                "duration_seconds": 3.3,
            },
            "summary": {
                "total_detections": 10,
                "unique_classes": ["car"],
                "dominant_class": "car",
                "class_distribution": {"car": 10},
            },
            "time_series": [],
        }
    )

    # Create a mock Path object that returns True for exists()
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.name = "out.mp4"

    wf = "backend.app.services.workflow"

    # --- PATCHING ---
    with (
        patch(f"{wf}.async_session_factory", mock_factory),
        patch(f"{wf}.TaskService", return_value=mock_task_service),
        patch(f"{wf}.YoloService", return_value=mock_yolo_service),
        patch(f"{wf}.FileService", return_value=mock_file_service),
        patch(f"{wf}.get_bigquery_service", return_value=mock_bq_service),
        patch(f"{wf}.run_in_threadpool", new_callable=AsyncMock) as mock_thread,
        patch(f"{wf}.Path") as mock_path_cls,
        patch("builtins.open", mock_open(read_data=fake_analytics_data)),
    ):
        # Configure Path mock
        mock_path_cls.return_value = mock_path

        # Configure side_effect for threadpool
        # 1. Call: YOLO (returns path)
        # 2. Call: BigQuery Insert (returns None)
        mock_thread.side_effect = ["/tmp/analytics.json", None]

        # ACTION
        await process_video_workflow(task_id, "/tmp/in.mp4", "/tmp/out.mp4")

        # ASSERTIONS

        # 1. Check if data was sent to BigQuery
        # Look for insert_report call in threadpool call list
        # call_args_list[1] is the second call (first is YOLO)
        bq_call = mock_thread.call_args_list[1]

        # Arguments for run_in_threadpool: (function, *args)
        assert bq_call[0][0] == mock_bq_service.insert_report
        assert bq_call[0][1] == str(task_id)

        # Verify report object
        report_arg = bq_call[0][2]
        assert report_arg.summary.total_detections == 10

        # 2. Check S3 uploads (Video + JSON)
        assert mock_file_service.upload_file_to_s3.await_count == 2
