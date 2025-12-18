from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.config import settings


def _build_database_url() -> str:
    """Build the database URL, stripping sslmode query params if present."""
    db_url = settings.DATABASE_URL
    if "sslmode=" in db_url:
        db_url = db_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    return db_url


def _get_connect_args() -> dict[str, object]:
    """Get connection arguments based on SSL configuration."""
    if settings.DATABASE_SSL_REQUIRED:
        return {"ssl": "require"}
    return {}


async_engine: AsyncEngine = create_async_engine(
    _build_database_url(),
    echo=False,
    future=True,
    connect_args=_get_connect_args(),
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize the database by creating all tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for dependency injection."""
    async with async_session_factory() as session:
        yield session
