import uuid
from unittest.mock import patch

from backend.app.worker import celery_process_video


def test_celery_worker_bridge():
    task_id_str = str(uuid.uuid4())
    input_path = "/in.mp4"
    output_path = "/out.mp4"

    with (
        patch("backend.app.worker.asyncio.run") as mock_run,
        patch("backend.app.worker.process_video_workflow") as mock_workflow,
    ):
        result = celery_process_video(task_id_str, input_path, output_path)

        assert result == "OK"

        mock_run.assert_called_once()

        mock_workflow.assert_called_once()

        args = mock_workflow.call_args
        assert isinstance(args[0][0], uuid.UUID)
        assert str(args[0][0]) == task_id_str
