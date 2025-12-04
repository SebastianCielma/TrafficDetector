from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.services.file import FileService


@pytest.mark.asyncio
async def test_file_service_save_upload():
    mock_upload_file = MagicMock()

    mock_upload_file.read = AsyncMock(side_effect=[b"chunk1", b"chunk2", b""])

    mock_file_handle = AsyncMock()
    mock_file_handle.write = AsyncMock()

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_file_handle
    mock_context.__aexit__.return_value = None

    with patch("aiofiles.open", return_value=mock_context) as mock_open:
        service = FileService()
        path = await service.save_upload(mock_upload_file, "test.mp4")

        assert "test.mp4" in path

        mock_open.assert_called_once()

        assert mock_file_handle.write.call_count == 2
