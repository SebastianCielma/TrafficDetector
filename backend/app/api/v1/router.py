import os
import shutil
import uuid
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from backend.app.api.deps import get_yolo_service
from backend.app.core.config import settings
from backend.app.services.yolo import YoloService

router = APIRouter()

TASKS: Dict[str, Dict[str, Any]] = {}


def run_detection_bg(
    task_id: str, input_path: str, output_path: str, service: YoloService
):
    TASKS[task_id] = {"status": "processing"}

    try:
        service.process_video(input_path, output_path)
        TASKS[task_id] = {
            "status": "completed",
            "result_url": f"/results/{os.path.basename(output_path)}",
        }
    except Exception as e:
        print(f"Error processing task {task_id}: {e}")
        TASKS[task_id] = {"status": "failed", "error": str(e)}


@router.post("/detect")
async def detect(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: YoloService = Depends(get_yolo_service),
):
    task_id = str(uuid.uuid4())
    input_path = os.path.join(settings.UPLOAD_DIR, f"{task_id}.mp4")
    output_path = os.path.join(settings.RESULTS_DIR, f"{task_id}.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(
        run_detection_bg, task_id, input_path, output_path, service
    )
    TASKS[task_id] = {"status": "queued"}

    return {"task_id": task_id, "status": "queued"}


@router.get("/status/{task_id}")
def status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        return {"status": "not_found"}
    return task
