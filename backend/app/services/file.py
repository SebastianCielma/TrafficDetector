import os
from typing import Any, Dict

import aioboto3
import aiofiles
from botocore.config import Config  # <--- NOWY IMPORT
from fastapi import UploadFile


class FileService:
    def __init__(
        self,
        s3_endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        upload_dir: str,
        results_dir: str,
    ):
        self.bucket_name = bucket_name
        self.upload_dir = upload_dir
        self.results_dir = results_dir

        self.session = aioboto3.Session()

        self.s3_config: Dict[str, Any] = {
            "endpoint_url": s3_endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": Config(signature_version="s3v4", region_name="auto"),
        }

    async def save_upload_locally(self, file: UploadFile, filename: str) -> str:
        file_path = os.path.join(self.upload_dir, filename)
        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                while content := await file.read(1024 * 1024):
                    await buffer.write(content)
            return file_path
        except Exception as e:
            raise IOError(f"Failed to save file locally: {e}") from e

    async def upload_file_to_s3(self, local_path: str, s3_key: str) -> str:
        try:
            async with self.session.client("s3", **self.s3_config) as s3:  # type: ignore
                with open(local_path, "rb") as f:
                    await s3.upload_fileobj(f, self.bucket_name, s3_key)

            print(f"Uploaded to Storage: {s3_key}")
            return s3_key
        except Exception as e:
            print(f"S3 Upload Error: {e}")
            raise e

    async def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        try:
            async with self.session.client("s3", **self.s3_config) as s3:  # type: ignore
                url: str = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
                return url
        except Exception as e:
            print(f"Presigned URL Error: {e}")
            return ""

    def cleanup_local_file(self, path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as e:
            print(f"Cleanup warning for {path}: {e}")

    def get_result_path_local(self, filename: str) -> str:
        return os.path.join(self.results_dir, filename)
