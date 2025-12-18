import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models.task import Task, TaskStatus


class TaskService:
    """Service for managing video processing tasks."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the task service.

        Args:
            session: Async database session.
        """
        self.session = session

    async def create_task(self, filename: str) -> Task:
        """Create a new processing task.

        Args:
            filename: Original filename of the uploaded video.

        Returns:
            The created task.
        """
        task = Task(input_filename=filename)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: uuid.UUID) -> Task | None:
        """Retrieve a task by its ID.

        Args:
            task_id: UUID of the task.

        Returns:
            The task if found, None otherwise.
        """
        return await self.session.get(Task, task_id)

    async def mark_processing(self, task: Task) -> None:
        """Mark a task as currently processing.

        Args:
            task: The task to update.
        """
        task.status = TaskStatus.PROCESSING
        self.session.add(task)
        await self.session.commit()

    async def mark_completed(self, task: Task, result_url: str) -> None:
        """Mark a task as completed with its result URL.

        Args:
            task: The task to update.
            result_url: S3 key or URL of the result video.
        """
        task.status = TaskStatus.COMPLETED
        task.result_url = result_url
        self.session.add(task)
        await self.session.commit()

    async def mark_failed(self, task: Task, error: str) -> None:
        """Mark a task as failed with an error message.

        Args:
            task: The task to update.
            error: Description of the error.
        """
        task.status = TaskStatus.FAILED
        task.error_message = error
        self.session.add(task)
        await self.session.commit()
