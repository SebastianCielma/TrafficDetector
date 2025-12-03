from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.db import get_session
from backend.app.services.file import FileService
from backend.app.services.task import TaskService


async def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(session)


def get_file_service() -> FileService:
    return FileService()
