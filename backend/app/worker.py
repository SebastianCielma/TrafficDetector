import asyncio
import uuid

from backend.app.core.celery_app import celery_app
from backend.app.core.logger import get_logger
from backend.app.services.workflow import process_video_workflow

logger = get_logger("worker")


@celery_app.task(acks_late=True, name="process_video_task")
def celery_process_video(task_id_str: str, input_path: str, output_path: str) -> str:
    """Celery task for processing video with YOLO detection.

    Args:
        task_id_str: String representation of the task UUID.
        input_path: Path to the input video file.
        output_path: Path for the output video file.

    Returns:
        "OK" on success, "FAILED" on UUID parsing error.

    Raises:
        Exception: Re-raises any exception from the video processing workflow.
    """
    logger.info("worker_task_started", task_id=task_id_str)

    try:
        task_id = uuid.UUID(task_id_str)
    except ValueError:
        logger.error("worker_invalid_uuid", task_id=task_id_str)
        return "FAILED"

    try:
        asyncio.run(process_video_workflow(task_id, input_path, output_path))
        logger.info("worker_task_completed", task_id=task_id_str)
        return "OK"

    except Exception as e:
        logger.exception("worker_task_failed", task_id=task_id_str, error=str(e))
        raise
