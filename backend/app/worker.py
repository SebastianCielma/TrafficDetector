import asyncio
import uuid

from backend.app.core.celery_app import celery_app
from backend.app.services.workflow import process_video_workflow


@celery_app.task(acks_late=True, name="process_video_task")
def celery_process_video(task_id_str: str, input_path: str, output_path: str) -> str:
    print(f"Celery Worker picked up task: {task_id_str}")

    try:
        task_id = uuid.UUID(task_id_str)
    except ValueError:
        print(f"Critical Error: Invalid UUID format: {task_id_str}")
        return "FAILED"

    try:
        asyncio.run(process_video_workflow(task_id, input_path, output_path))
        return "OK"

    except Exception as e:
        print(f"Worker Critical Failure for {task_id}: {e}")
        raise e from e
