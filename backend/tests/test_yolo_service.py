from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.yolo import YoloService


@pytest.fixture
def mock_env_settings(monkeypatch):
    monkeypatch.setattr("backend.app.core.config.settings.MODEL_PATH", "dummy_model.pt")


@patch("backend.app.services.yolo.YOLO")
def test_yolo_init(mock_yolo_class, mock_env_settings):
    service = YoloService()
    mock_yolo_class.assert_called_once_with("dummy_model.pt")
    assert service.model is not None


@patch("backend.app.services.yolo.os.path.exists")
@patch("backend.app.services.yolo.YOLO")
def test_process_video_file_not_found(mock_yolo, mock_exists, mock_env_settings):
    mock_exists.return_value = False
    service = YoloService()

    with pytest.raises(FileNotFoundError):
        service.process_video("ghost.mp4", "out.mp4")


@patch("backend.app.services.yolo.sv.Detections.from_ultralytics")
@patch("backend.app.services.yolo.subprocess.run")
@patch("backend.app.services.yolo.cv2.VideoWriter")
@patch("backend.app.services.yolo.sv.BoxAnnotator")
@patch("backend.app.services.yolo.sv.get_video_frames_generator")
@patch("backend.app.services.yolo.sv.VideoInfo")
@patch("backend.app.services.yolo.os.path.exists")
@patch("backend.app.services.yolo.os.remove")
@patch("backend.app.services.yolo.YOLO")
def test_process_video_flow(
    mock_yolo_class,
    mock_remove,
    mock_exists,
    mock_video_info,
    mock_frame_gen,
    mock_box_annotator,
    mock_writer,
    mock_subprocess,
    mock_from_ultralytics,
    mock_env_settings,
):
    mock_exists.return_value = True
    mock_frame_gen.return_value = [MagicMock(), MagicMock()]

    mock_info = mock_video_info.from_video_path.return_value
    mock_info.fps = 30.0
    mock_info.resolution_wh = (1920, 1080)
    mock_info.total_frames = 2

    mock_model_instance = mock_yolo_class.return_value
    mock_model_instance.return_value = ["dummy_result"]

    mock_detections = MagicMock()
    mock_from_ultralytics.return_value = mock_detections
    mock_detections.class_id = []

    service = YoloService()
    service.process_video("in.mp4", "out.mp4")

    assert mock_model_instance.call_count == 2
    mock_subprocess.assert_called_once()
    mock_remove.assert_called()
