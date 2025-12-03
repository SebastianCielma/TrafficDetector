import os
import uuid

from backend.app.core.db import async_session_factory
from backend.app.services.task import TaskService
from backend.app.services.yolo import YoloService


async def process_video_workflow(
    task_id: uuid.UUID, input_path: str, output_path: str
) -> None:
    async with async_session_factory() as session:
        task_service = TaskService(session)
        yolo_service = YoloService()

        task = await task_service.get_task(task_id)
        if not task:
            return

        await task_service.mark_processing(task)

        try:
            yolo_service.process_video(input_path, output_path)

            result_url = f"/results/{os.path.basename(output_path)}"
            await task_service.mark_completed(task, result_url)

        except Exception as e:
            print(f"CRITICAL WORKFLOW ERROR: {e}")
            await task_service.mark_failed(task, str(e))
