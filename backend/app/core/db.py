from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.config import settings

db_url = settings.DATABASE_URL
connect_args = {}

if "sslmode=" in db_url:
    db_url = db_url.replace("?sslmode=require", "").replace("&sslmode=require", "")


if "neon.tech" in db_url:
    connect_args = {"ssl": "require"}

async_engine: AsyncEngine = create_async_engine(
    db_url, echo=False, future=True, connect_args=connect_args
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
