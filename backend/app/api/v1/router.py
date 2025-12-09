import uuid
from pathlib import Path
from typing import Dict

#
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.app.api.deps import get_file_service, get_task_service
from backend.app.core.security import verify_api_key
from backend.app.models.task import Task, TaskStatus
from backend.app.services.file import FileService
from backend.app.services.task import TaskService
from backend.app.worker import celery_process_video

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/detect", response_model=Dict[str, str], status_code=202)
async def detect(
    file: UploadFile = File(...),
    task_service: TaskService = Depends(get_task_service),
    file_service: FileService = Depends(get_file_service),
) -> Dict[str, str]:
    original_filename = file.filename or "unknown.mp4"
    task = await task_service.create_task(original_filename)

    file_ext = Path(original_filename).suffix.lower()
    if not file_ext:
        file_ext = ".mp4"

    input_filename = f"{task.id}{file_ext}"
    output_filename = f"{task.id}.mp4"

    input_path = await file_service.save_upload_locally(file, input_filename)
    output_path = file_service.get_result_path_local(output_filename)

    celery_process_video.delay(str(task.id), input_path, output_path)

    return {"task_id": str(task.id), "status": task.status}


@router.get("/status/{task_id}", response_model=Task)
async def status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    file_service: FileService = Depends(get_file_service),
) -> Task:
    try:
        uuid_obj = uuid.UUID(task_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid UUID format") from err

    task = await task_service.get_task(uuid_obj)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == TaskStatus.COMPLETED and task.result_url:
        presigned_url = await file_service.generate_presigned_url(task.result_url)
        task.result_url = presigned_url

    return task
