"""Test fixtures and configuration for the TrafficDetector backend tests."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

# Set environment variables BEFORE importing the app
# This is required because pydantic-settings loads config at import time
os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ["S3_ENDPOINT"] = "http://test-s3"
os.environ["S3_ACCESS_KEY"] = "test-key"
os.environ["S3_SECRET_KEY"] = "test-secret"
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "db+sqlite:///results.db"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test"
os.environ["GCS_BUCKET_NAME"] = "test-gcs-bucket"
os.environ["API_KEY"] = "test-secret-key"
os.environ["UI_USERNAME"] = "admin"
os.environ["UI_PASSWORD"] = "password"

# Now we can safely import the app
from backend.app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure pytest-asyncio to use asyncio backend."""
    return "asyncio"


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_db_session_factory() -> tuple[MagicMock, AsyncMock]:
    """Create mock database session factory for testing."""
    mock_session = AsyncMock()
    mock_db_manager = MagicMock()
    mock_db_manager.__aenter__.return_value = mock_session
    mock_db_manager.__aexit__.return_value = None

    mock_factory = MagicMock()
    mock_factory.return_value = mock_db_manager

    return mock_factory, mock_session
