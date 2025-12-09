from unittest.mock import MagicMock, mock_open, patch

import pytest

from frontend.app import predict


@pytest.fixture
def mock_env_vars():
    with (
        patch("frontend.app.API_URL", "http://test-api.com"),
        patch("frontend.app.API_KEY", "secret-test-key"),
    ):
        yield


@patch("frontend.app.requests.post")
@patch("frontend.app.requests.get")
@patch("frontend.app.shutil.copyfileobj")
@patch("frontend.app.open", new_callable=mock_open, read_data=b"video_data")
@patch("frontend.app.time.sleep")
def test_predict_happy_path(
    mock_sleep, mock_file_open, mock_shutil, mock_get, mock_post, mock_env_vars
):
    mock_post_response = MagicMock()
    mock_post_response.status_code = 202
    mock_post_response.json.return_value = {"task_id": "123-abc"}
    mock_post.return_value = mock_post_response

    resp_processing = MagicMock()
    resp_processing.json.return_value = {"status": "processing"}
    resp_processing.status_code = 200

    resp_completed = MagicMock()
    resp_completed.json.return_value = {
        "status": "completed",
        "result_url": "https://s3/vid.mp4",
    }
    resp_completed.status_code = 200

    resp_download = MagicMock()
    resp_download.status_code = 200
    resp_download.raise_for_status = MagicMock()
    resp_download.raw = MagicMock()

    mock_get.side_effect = [resp_processing, resp_completed, resp_download]

    result = predict("test_video.mp4")

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://test-api.com/api/v1/detect"
    assert kwargs["headers"] == {"X-API-KEY": "secret-test-key"}

    args_get, kwargs_get = mock_get.call_args_list[0]
    assert kwargs_get["headers"] == {"X-API-KEY": "secret-test-key"}

    args_download, _ = mock_get.call_args_list[2]
    assert args_download[0] == "https://s3/vid.mp4"

    assert result == "result_123-abc.mp4"


@patch("frontend.app.requests.post")
def test_predict_upload_failed_auth(mock_post, mock_env_vars):
    mock_post.return_value.status_code = 403
    mock_post.return_value.text = "Forbidden"

    with patch("builtins.open", mock_open(read_data=b"data")):
        result = predict("video.mp4")

    assert result is None
