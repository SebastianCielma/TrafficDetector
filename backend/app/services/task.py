import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models.task import Task, TaskStatus


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, filename: str) -> Task:
        task = Task(input_filename=filename)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: uuid.UUID) -> Task | None:
        return await self.session.get(Task, task_id)

    async def mark_processing(self, task: Task) -> None:
        task.status = TaskStatus.PROCESSING
        self.session.add(task)
        await self.session.commit()

    async def mark_completed(self, task: Task, result_url: str) -> None:
        task.status = TaskStatus.COMPLETED
        task.result_url = result_url
        self.session.add(task)
        await self.session.commit()

    async def mark_failed(self, task: Task, error: str) -> None:
        task.status = TaskStatus.FAILED
        task.error_message = error
        self.session.add(task)
        await self.session.commit()
