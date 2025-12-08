import os
import time
import uuid

import structlog
from fastapi.concurrency import run_in_threadpool

from backend.app.core.config import settings
from backend.app.core.db import async_session_factory
from backend.app.core.logger import get_logger
from backend.app.services.file import FileService
from backend.app.services.task import TaskService
from backend.app.services.yolo import YoloService

logger = get_logger("workflow")


async def process_video_workflow(
    task_id: uuid.UUID, input_path: str, output_path: str
) -> None:
    structlog.contextvars.bind_contextvars(task_id=str(task_id))

    start_time = time.time()

    async with async_session_factory() as session:
        task_service = TaskService(session)
        yolo_service = YoloService()

        file_service = FileService(
            s3_endpoint=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket_name=settings.S3_BUCKET_NAME,
            upload_dir=settings.UPLOAD_DIR,
            results_dir=settings.RESULTS_DIR,
        )

        task = await task_service.get_task(task_id)
        if not task:
            logger.warning("task_not_found_db")
            return

        await task_service.mark_processing(task)

        try:
            logger.info("processing_started", input=input_path)

            await run_in_threadpool(yolo_service.process_video, input_path, output_path)

            s3_key = f"results/{os.path.basename(output_path)}"
            await file_service.upload_file_to_s3(output_path, s3_key)

            await task_service.mark_completed(task, s3_key)

            duration = time.time() - start_time
            logger.info(
                "processing_finished",
                status="success",
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            logger.exception("processing_failed", error=str(e))
            await task_service.mark_failed(task, str(e))

        finally:
            await file_service.cleanup_local_file(input_path)
            await file_service.cleanup_local_file(output_path)
            structlog.contextvars.clear_contextvars()
