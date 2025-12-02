from unittest.mock import MagicMock, mock_open, patch

import pytest

from frontend.app import predict


@pytest.fixture
def mock_api_url():
    with patch("frontend.app.API_URL", "http://test-api.com") as mock_url:
        yield mock_url


@patch("frontend.app.requests.post")
@patch("frontend.app.requests.get")
@patch("frontend.app.shutil.copyfileobj")
@patch("frontend.app.open", new_callable=mock_open, read_data=b"video_data")
@patch("frontend.app.time.sleep")
def test_predict_happy_path(
    mock_sleep, mock_file_open, mock_shutil, mock_get, mock_post, mock_api_url
):
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {"task_id": "123-abc"}
    mock_post.return_value = mock_post_response

    resp_processing = MagicMock()
    resp_processing.json.return_value = {"status": "processing"}

    resp_completed = MagicMock()
    resp_completed.json.return_value = {"status": "completed"}

    resp_download = MagicMock()
    resp_download.status_code = 200
    resp_download.raise_for_status = MagicMock()
    resp_download.raw = MagicMock()

    mock_get.side_effect = [resp_processing, resp_completed, resp_download]

    result = predict("test_video.mp4")

    mock_post.assert_called_once()
    assert "http://test-api.com/api/v1/detect" in mock_post.call_args[0][0]

    mock_shutil.assert_called_once()

    assert result == "temp_result_123-abc.mp4"


@patch("frontend.app.requests.post")
def test_predict_upload_failed(mock_post, mock_api_url):
    mock_post.side_effect = Exception("Connection refused")

    with patch("builtins.open", mock_open(read_data=b"data")):
        result = predict("video.mp4")

    assert result is None


@patch("frontend.app.requests.post")
@patch("frontend.app.requests.get")
@patch("frontend.app.time.sleep")
def test_predict_processing_failed(mock_sleep, mock_get, mock_post, mock_api_url):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"task_id": "fail-task"}

    mock_get.return_value.json.return_value = {"status": "failed"}

    with patch("builtins.open", mock_open(read_data=b"data")):
        result = predict("video.mp4")

    assert result is None
