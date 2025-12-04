from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.config import settings
from backend.app.core.db import get_session
from backend.app.services.file import FileService
from backend.app.services.task import TaskService


async def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(session)


def get_file_service() -> FileService:
    return FileService(
        s3_endpoint=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
        upload_dir=settings.UPLOAD_DIR,
        results_dir=settings.RESULTS_DIR,
    )
