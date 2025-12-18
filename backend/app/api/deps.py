from fastapi import Depends
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.config import settings
from backend.app.core.db import get_session
from backend.app.core.logger import get_logger
from backend.app.services.bigquery import BigQueryService
from backend.app.services.file import FileService
from backend.app.services.task import TaskService

logger = get_logger("deps")


async def get_task_service(
    session: AsyncSession = Depends(get_session),
) -> TaskService:
    """Dependency that provides a TaskService instance."""
    return TaskService(session)


def get_file_service() -> FileService:
    """Dependency that provides a FileService instance."""
    return FileService(
        s3_endpoint=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
        upload_dir=settings.UPLOAD_DIR,
        results_dir=settings.RESULTS_DIR,
    )


def get_bigquery_service() -> BigQueryService:
    """Dependency that provides a BigQueryService instance."""
    client: bigquery.Client | None = None
    try:
        client = bigquery.Client()
    except DefaultCredentialsError as e:
        logger.warning(
            "bigquery_credentials_missing",
            error=str(e),
            message="BigQuery client not initialized - credentials not found",
        )
    except Exception as e:
        logger.warning(
            "bigquery_client_init_failed",
            error=str(e),
            message="BigQuery client initialization failed",
        )

    return BigQueryService(dataset_id=settings.BIGQUERY_DATASET, client=client)
