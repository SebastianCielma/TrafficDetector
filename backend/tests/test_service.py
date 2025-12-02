from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.yolo import YoloService


@pytest.fixture
def mock_env_settings(monkeypatch):
    monkeypatch.setattr("backend.app.core.config.settings.MODEL_PATH", "dummy_model.pt")


@patch("backend.app.services.yolo.YOLO")
def test_yolo_service_init(mock_yolo_class, mock_env_settings):
    service = YoloService()

    mock_yolo_class.assert_called_once_with("dummy_model.pt")
    assert service.model is not None


@patch("backend.app.services.yolo.os.path.exists")
@patch("backend.app.services.yolo.YOLO")
def test_process_video_file_not_found(mock_yolo, mock_exists, mock_env_settings):
    mock_exists.return_value = False

    service = YoloService()

    with pytest.raises(FileNotFoundError) as excinfo:
        service.process_video("ghost.mp4", "out.mp4")

    assert "Input video not found" in str(excinfo.value)


@patch("backend.app.services.yolo.sv.Detections.from_ultralytics")
@patch("backend.app.services.yolo.subprocess.run")
@patch("backend.app.services.yolo.cv2.VideoWriter")
@patch("backend.app.services.yolo.sv.BoxAnnotator")
@patch("backend.app.services.yolo.sv.get_video_frames_generator")
@patch("backend.app.services.yolo.sv.VideoInfo")
@patch("backend.app.services.yolo.os.path.exists")
@patch("backend.app.services.yolo.os.remove")
@patch("backend.app.services.yolo.YOLO")
def test_process_video_happy_path(
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

    mock_info_instance = mock_video_info.from_video_path.return_value
    mock_info_instance.fps = 30.0
    mock_info_instance.resolution_wh = (1920, 1080)
    mock_info_instance.total_frames = 2

    mock_model_instance = mock_yolo_class.return_value
    mock_model_instance.return_value = ["dummy_result"]

    mock_detections = MagicMock()
    mock_from_ultralytics.return_value = mock_detections
    mock_detections.class_id = []

    mock_annotator_instance = mock_box_annotator.return_value
    mock_annotator_instance.annotate.return_value = "annotated_frame"

    service = YoloService()
    result = service.process_video("input.mp4", "final_output.mp4")

    assert result is True
    assert mock_model_instance.call_count == 2

    mock_from_ultralytics.assert_called_with("dummy_result")

    mock_writer.return_value.write.assert_called_with("annotated_frame")

    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args
    command_list = call_args[0][0]
    assert "ffmpeg" in command_list


@patch("backend.app.services.yolo.sv.get_video_frames_generator")
@patch("backend.app.services.yolo.sv.VideoInfo")
@patch("backend.app.services.yolo.os.path.exists")
@patch("backend.app.services.yolo.YOLO")
def test_process_video_runtime_error_no_frames(
    mock_yolo, mock_exists, mock_video_info, mock_frame_gen, mock_env_settings
):
    mock_exists.return_value = True
    mock_frame_gen.return_value = []

    mock_info_instance = mock_video_info.from_video_path.return_value
    mock_info_instance.fps = 30.0
    mock_info_instance.resolution_wh = (100, 100)

    service = YoloService()

    with pytest.raises(RuntimeError, match="No frames were processed"):
        service.process_video("empty.mp4", "out.mp4")
