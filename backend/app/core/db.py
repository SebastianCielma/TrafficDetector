from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.config import settings

async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL, echo=False, future=True
)

async_session_factory = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
