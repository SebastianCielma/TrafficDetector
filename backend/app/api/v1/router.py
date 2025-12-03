from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from backend.app.api.deps import get_file_service, get_task_service
from backend.app.services.file import FileService
from backend.app.services.task import TaskService
from backend.app.services.workflow import process_video_workflow

router = APIRouter()


@router.post("/detect", response_model=dict[str, str], status_code=202)
async def detect(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    task_service: TaskService = Depends(get_task_service),
    file_service: FileService = Depends(get_file_service),
) -> dict[str, str]:
    original_filename = file.filename or "unknown.mp4"

    task = await task_service.create_task(original_filename)

    file_ext = Path(original_filename).suffix.lower()
    if not file_ext:
        file_ext = ".mp4"

    input_filename = f"{task.id}{file_ext}"

    output_filename = f"{task.id}.mp4"

    input_path = await file_service.save_upload(file, input_filename)

    output_path = file_service.get_result_path(output_filename)

    background_tasks.add_task(process_video_workflow, task.id, input_path, output_path)

    return {"task_id": str(task.id), "status": task.status}
