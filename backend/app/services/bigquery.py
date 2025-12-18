import json
from datetime import datetime, timezone

import structlog
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery

from backend.app.schemas.analytics import AnalyticsReport

logger = structlog.get_logger(__name__)


class BigQueryService:
    """Service for inserting analytics reports into BigQuery."""

    def __init__(self, dataset_id: str, client: bigquery.Client | None = None) -> None:
        self.client = client
        self.dataset_id = dataset_id
        self.table_id: str | None = None

        if self.client:
            try:
                self.table_id = f"{self.client.project}.{self.dataset_id}.daily_reports"
            except Exception as e:
                logger.warning("bq_project_id_error", error=str(e))

    def insert_report(self, task_id: str, report: AnalyticsReport) -> None:
        """Insert an analytics report into BigQuery."""
        if not self.client or not self.table_id:
            logger.warning("bq_skip", message="Client not initialized")
            return

        class_dist_json = json.dumps(report.summary.class_distribution)

        row = {
            "task_id": task_id,
            "filename": report.meta.source_filename,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": report.meta.duration_seconds,
            "total_vehicles": report.summary.total_detections,
            "dominant_class": report.summary.dominant_class or "none",
            "class_distribution_json": class_dist_json,
        }

        try:
            errors = self.client.insert_rows_json(self.table_id, [row])
            if errors:
                logger.error("bq_insert_errors", errors=errors)
            else:
                logger.info("bq_upload_success", task_id=task_id)

        except GoogleAPIError as e:
            logger.error("bq_api_error", error=str(e))
