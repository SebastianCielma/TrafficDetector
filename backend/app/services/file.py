import os

import aiofiles
from fastapi import UploadFile

from backend.app.core.config import settings


class FileService:
    async def save_upload(self, file: UploadFile, filename: str) -> str:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                while content := await file.read(1024 * 1024):  # 1MB chunks
                    await buffer.write(content)
            return file_path
        except Exception as e:
            raise IOError(f"Failed to save file asynchronously: {e}") from e

    def get_result_path(self, filename: str) -> str:
        return os.path.join(settings.RESULTS_DIR, filename)
