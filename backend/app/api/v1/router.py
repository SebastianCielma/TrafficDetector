from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from backend.app.services.yolo import YoloService
from backend.app.api.deps import get_yolo_service
from backend.app.core.config import settings
import shutil
import uuid
import os

router = APIRouter()

TASKS = {}

def run_detection_bg(task_id: str, input_path: str, output_path: str, service: YoloService):
    TASKS[task_id] = "processing"
    try:
        service.process_video(input_path, output_path)
        TASKS[task_id] = "completed"
    except:
        TASKS[task_id] = "failed"

@router.post("/detect")
async def detect(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: YoloService = Depends(get_yolo_service)
):
    task_id = str(uuid.uuid4())
    input_path = os.path.join(settings.UPLOAD_DIR, f"{task_id}.mp4")
    output_path = os.path.join(settings.RESULTS_DIR, f"{task_id}.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(run_detection_bg, task_id, input_path, output_path, service)
    TASKS[task_id] = "queued"

    return {"task_id": task_id, "status": "queued"}

@router.get("/status/{task_id}")
def status(task_id: str):
    return {"status": TASKS.get(task_id, "not_found")}