import os
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app

os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ["S3_ENDPOINT"] = "http://test-s3"
os.environ["S3_ACCESS_KEY"] = "test-key"
os.environ["S3_SECRET_KEY"] = "test-secret"
os.environ["CELERY_BROKER_URL"] = "redis://test"
os.environ["CELERY_RESULT_BACKEND"] = "redis://test"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
