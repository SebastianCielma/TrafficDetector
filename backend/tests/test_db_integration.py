import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models.task import TaskStatus
from backend.app.services.task import TaskService


@pytest.fixture(name="session")
async def session_fixture():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_task_service_crud_lifecycle(session: AsyncSession):
    service = TaskService(session)

    task = await service.create_task("wakacje.mp4")

    assert task.id is not None
    assert task.status == TaskStatus.QUEUED
    assert task.input_filename == "wakacje.mp4"
    assert task in session
    fetched_task = await service.get_task(task.id)
    assert fetched_task is not None
    assert fetched_task.id == task.id

    await service.mark_processing(fetched_task)

    await session.refresh(fetched_task)
    assert fetched_task.status == TaskStatus.PROCESSING

    result_link = "/results/wakacje.mp4"
    await service.mark_completed(fetched_task, result_link)

    await session.refresh(fetched_task)
    assert fetched_task.status == TaskStatus.COMPLETED
    assert fetched_task.result_url == result_link


@pytest.mark.asyncio
async def test_task_service_get_non_existent(session: AsyncSession):
    service = TaskService(session)
    fake_id = uuid.uuid4()

    task = await service.get_task(fake_id)

    assert task is None
