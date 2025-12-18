"""Tests for file service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.services.file import FileService

MOCK_CONFIG = {
    "s3_endpoint": "http://fake-s3",
    "access_key": "fake",
    "secret_key": "fake",
    "bucket_name": "test-bucket",
    "upload_dir": "/tmp/up",
    "results_dir": "/tmp/res",
}


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client for testing."""
    with patch("backend.app.services.file.aioboto3.Session") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        mock_client = AsyncMock()

        mock_session.client.return_value.__aenter__.return_value = mock_client
        mock_session.client.return_value.__aexit__.return_value = None

        yield mock_client


@pytest.mark.asyncio
async def test_save_upload_locally():
    """Test saving uploaded file locally."""
    mock_upload = MagicMock()
    mock_upload.read = AsyncMock(side_effect=[b"chunk1", b"chunk2", b""])

    mock_file_handle = AsyncMock()
    mock_file_handle.write = AsyncMock()

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_file_handle
    mock_context.__aexit__.return_value = None

    with patch("aiofiles.open", return_value=mock_context) as mock_open_func:
        service = FileService(**MOCK_CONFIG)
        path = await service.save_upload_locally(mock_upload, "video.mp4")

        assert path == "/tmp/up/video.mp4"
        mock_open_func.assert_called_once()
        assert mock_file_handle.write.call_count == 2


@pytest.mark.asyncio
async def test_upload_file_to_s3(mock_s3_client):
    """Test uploading file to S3."""
    service = FileService(**MOCK_CONFIG)

    # Mock aiofiles.open for the async file read
    mock_file_handle = AsyncMock()
    mock_file_handle.read = AsyncMock(return_value=b"video_data")

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_file_handle
    mock_context.__aexit__.return_value = None

    with patch("aiofiles.open", return_value=mock_context):
        key = await service.upload_file_to_s3("/tmp/local.mp4", "results/video.mp4")

    assert key == "results/video.mp4"

    mock_s3_client.put_object.assert_awaited_once()
    args = mock_s3_client.put_object.call_args
    assert args.kwargs["Bucket"] == "test-bucket"
    assert args.kwargs["Key"] == "results/video.mp4"
    assert args.kwargs["Body"] == b"video_data"


@pytest.mark.asyncio
async def test_generate_presigned_url(mock_s3_client):
    """Test generating presigned URL for S3 object."""
    mock_s3_client.generate_presigned_url.return_value = (
        "https://cdn.fake/video.mp4?token=123"
    )

    service = FileService(**MOCK_CONFIG)
    url = await service.generate_presigned_url("results/video.mp4")

    assert url == "https://cdn.fake/video.mp4?token=123"
    mock_s3_client.generate_presigned_url.assert_awaited_once()
