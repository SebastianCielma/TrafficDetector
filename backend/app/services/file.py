import os
from pathlib import Path

import aioboto3
import aiofiles
import aiofiles.os
import structlog
from botocore.config import Config
from fastapi import UploadFile

logger = structlog.get_logger(__name__)


class FileServiceError(Exception):
    """Base exception for FileService errors."""


class FileUploadError(FileServiceError):
    """Raised when file upload fails."""


class S3UploadError(FileServiceError):
    """Raised when S3 upload fails."""


class FileService:
    """Service for handling file operations including local storage and S3."""

    def __init__(
        self,
        s3_endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        upload_dir: str,
        results_dir: str,
    ) -> None:
        self.bucket_name = bucket_name
        self.upload_dir = upload_dir
        self.results_dir = results_dir

        self.session = aioboto3.Session()

        self.s3_config: dict[str, object] = {
            "endpoint_url": s3_endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": Config(signature_version="s3v4", region_name="us-east-1"),
        }

    async def save_upload_locally(self, file: UploadFile, filename: str) -> str:
        """Save an uploaded file to local storage.

        Args:
            file: The uploaded file from FastAPI.
            filename: The target filename.

        Returns:
            The path to the saved file.

        Raises:
            FileUploadError: If the file cannot be saved.
        """
        file_path = os.path.join(self.upload_dir, filename)
        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                while content := await file.read(1024 * 1024):
                    await buffer.write(content)

            logger.info("file_saved_locally", filename=filename, path=file_path)
            return file_path
        except Exception as e:
            logger.error("file_save_failed", filename=filename, error=str(e))
            raise FileUploadError(f"Failed to save file locally: {e}") from e

    async def upload_file_to_s3(self, local_path: str, s3_key: str) -> str:
        """Upload a file to S3 storage.

        Args:
            local_path: Path to the local file.
            s3_key: The S3 key (path) for the uploaded file.

        Returns:
            The S3 key of the uploaded file.

        Raises:
            S3UploadError: If the upload fails.
        """
        try:
            async with self.session.client("s3", **self.s3_config) as s3:  # type: ignore[arg-type]
                async with aiofiles.open(local_path, "rb") as f:
                    content = await f.read()
                    await s3.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=content,
                    )

            logger.info("file_uploaded_to_s3", s3_key=s3_key)
            return s3_key
        except Exception as e:
            logger.critical("s3_upload_failed", s3_key=s3_key, error=str(e))
            raise S3UploadError(f"S3 upload failed: {e}") from e

    async def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for accessing an S3 object.

        Args:
            s3_key: The S3 key of the object.
            expiration: URL expiration time in seconds.

        Returns:
            The presigned URL, or empty string on failure.
        """
        try:
            async with self.session.client("s3", **self.s3_config) as s3:  # type: ignore[arg-type]
                url: str = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
                return url
        except Exception as e:
            logger.error("presigned_url_failed", s3_key=s3_key, error=str(e))
            return ""

    async def cleanup_local_file(self, path: str) -> None:
        """Remove a local file if it exists.

        Args:
            path: Path to the file to remove.
        """
        try:
            if await aiofiles.os.path.exists(path):
                await aiofiles.os.remove(path)
                logger.debug("file_cleaned_up", path=path)
        except OSError as e:
            logger.warning("file_cleanup_failed", path=path, error=str(e))

    def get_result_path_local(self, filename: str) -> str:
        """Get the local path for a result file.

        Args:
            filename: The result filename.

        Returns:
            The full path to the result file.
        """
        return str(Path(self.results_dir) / filename)
