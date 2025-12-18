from unittest.mock import MagicMock

import pytest

from backend.app.schemas.analytics import AnalysisSummary, AnalyticsReport, VideoMeta
from backend.app.services.bigquery import BigQueryService


@pytest.fixture
def mock_analytics_report():
    return AnalyticsReport(
        meta=VideoMeta(
            source_filename="test.mp4",
            fps=30.0,
            total_frames=100,
            resolution=(1920, 1080),
            duration_seconds=3.33,
        ),
        summary=AnalysisSummary(
            total_detections=10,
            unique_classes=["car"],
            dominant_class="car",
            class_distribution={"car": 10},
        ),
        time_series=[],
    )


def test_insert_report_success(mock_analytics_report):
    mock_client = MagicMock()
    mock_client.project = "test-project"

    mock_client.insert_rows_json.return_value = []

    service = BigQueryService(dataset_id="test_dataset", client=mock_client)

    service.insert_report("task-123", mock_analytics_report)

    mock_client.insert_rows_json.assert_called_once()

    call_args = mock_client.insert_rows_json.call_args
    table_id = call_args[0][0]
    rows = call_args[0][1]

    assert table_id == "test-project.test_dataset.daily_reports"
    assert rows[0]["task_id"] == "task-123"
    assert rows[0]["total_vehicles"] == 10
    assert rows[0]["class_distribution_json"] == '{"car": 10}'


def test_insert_report_no_client_graceful_exit(mock_analytics_report):
    service = BigQueryService(dataset_id="test_dataset", client=None)

    service.insert_report("task-123", mock_analytics_report)
