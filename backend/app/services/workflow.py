import json
import uuid
from pathlib import Path

import structlog
from fastapi.concurrency import run_in_threadpool

from backend.app.api.deps import get_bigquery_service
from backend.app.core.config import settings
from backend.app.core.db import async_session_factory
from backend.app.core.logger import get_logger
from backend.app.schemas.analytics import AnalyticsReport
from backend.app.services.file import FileService
from backend.app.services.task import TaskService
from backend.app.services.yolo import YoloService

logger = get_logger("workflow")


async def process_video_workflow(
    task_id: uuid.UUID,
    input_path: str,
    output_path: str,
) -> None:
    """Process a video through the complete detection workflow.

    This function orchestrates the entire video processing pipeline:
    1. Updates task status to PROCESSING
    2. Runs YOLO detection on the video
    3. Uploads results to S3
    4. Sends analytics to BigQuery
    5. Updates task status to COMPLETED or FAILED
    6. Cleans up local files

    Args:
        task_id: UUID of the task being processed.
        input_path: Path to the input video file.
        output_path: Path for the output annotated video.
    """
    structlog.contextvars.bind_contextvars(task_id=str(task_id))

    async with async_session_factory() as session:
        task_service = TaskService(session)
        yolo_service = YoloService()
        bq_service = get_bigquery_service()

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
            logger.warning("task_not_found_in_db", task_id=str(task_id))
            return

        await task_service.mark_processing(task)
        json_path: str | None = None

        try:
            logger.info("workflow_started", input_path=input_path)

            json_path = await run_in_threadpool(
                yolo_service.process_video,
                input_path,
                output_path,
            )

            video_s3_key = f"results/{Path(output_path).name}"
            await file_service.upload_file_to_s3(output_path, video_s3_key)

            if json_path and Path(json_path).exists():
                json_s3_key = f"analytics/{task_id}.json"
                await file_service.upload_file_to_s3(json_path, json_s3_key)
                logger.info("analytics_s3_uploaded", key=json_s3_key)

                try:
                    with open(json_path) as f:
                        data_dict = json.load(f)
                        report = AnalyticsReport(**data_dict)

                    await run_in_threadpool(
                        bq_service.insert_report, str(task_id), report
                    )

                except Exception as bq_e:
                    logger.error("bq_integration_failed", error=str(bq_e))

            await task_service.mark_completed(task, video_s3_key)

            logger.info("workflow_finished", status="success")

        except Exception as e:
            logger.exception("workflow_failed", error=str(e))
            await task_service.mark_failed(task, str(e))

        finally:
            await file_service.cleanup_local_file(input_path)
            await file_service.cleanup_local_file(output_path)
            if json_path:
                await file_service.cleanup_local_file(json_path)

            structlog.contextvars.clear_contextvars()
