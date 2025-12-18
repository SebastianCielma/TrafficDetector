from unittest.mock import MagicMock, mock_open, patch

import pytest

from backend.app.services.yolo import YoloService


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for YoloService testing."""
    with (
        patch("backend.app.services.yolo.cv2") as cv2,
        patch("backend.app.services.yolo.sv") as sv,
        patch("backend.app.services.yolo.YOLO") as yolo,
        patch("backend.app.services.yolo.subprocess.run") as subprocess,
        patch("backend.app.services.yolo.shutil.which", return_value="/usr/bin/ffmpeg"),
    ):
        yield cv2, sv, yolo, subprocess


def test_yolo_init(mock_dependencies):
    _, _, mock_yolo_class, _ = mock_dependencies
    with patch("backend.app.core.config.settings.MODEL_PATH", "dummy.pt"):
        service = YoloService()
        mock_yolo_class.assert_called_once_with("dummy.pt")
        assert service.model is not None


def test_process_video_flow_with_analytics(mock_dependencies):
    mock_cv2, mock_sv, mock_yolo_class, mock_subprocess = mock_dependencies

    # Create mock Path objects
    mock_input_path = MagicMock()
    mock_input_path.exists.return_value = True
    mock_input_path.name = "input.mp4"  # Required by _build_report

    mock_output_path = MagicMock()
    mock_output_path.stem = "output"
    mock_output_path.suffix = ".mp4"
    mock_temp_path = MagicMock()
    mock_temp_path.__str__ = MagicMock(return_value="output_temp.mp4")
    mock_output_path.with_name.return_value = mock_temp_path
    mock_json_path = MagicMock()
    mock_json_path.__str__ = MagicMock(return_value="output.json")
    mock_output_path.with_suffix.return_value = mock_json_path

    with (
        patch("backend.app.services.yolo.Path") as mock_path_cls,
        patch("backend.app.core.config.settings.MODEL_PATH", "dummy.pt"),
        patch("builtins.open", mock_open()) as mock_file,
    ):
        # Configure Path to return appropriate mocks
        def path_side_effect(p):
            if p == "input.mp4":
                return mock_input_path
            return mock_output_path

        mock_path_cls.side_effect = path_side_effect
        mock_temp_path.exists.return_value = True
        mock_info = mock_sv.VideoInfo.from_video_path.return_value
        mock_info.fps = 30.0
        mock_info.resolution_wh = (1920, 1080)
        mock_info.total_frames = 10

        mock_frame = MagicMock()
        mock_sv.get_video_frames_generator.return_value = [mock_frame]

        mock_model_instance = mock_yolo_class.return_value
        mock_yolo_result = MagicMock()
        mock_model_instance.return_value = [mock_yolo_result]

        mock_detections = MagicMock()
        mock_detections.class_id = [0, 2]
        mock_sv.Detections.from_ultralytics.return_value = mock_detections

        mock_model_instance.model.names = {0: "car", 1: "truck", 2: "person"}

        service = YoloService()
        json_path = service.process_video("input.mp4", "output.mp4")

        assert json_path == "output.json"

        handle = mock_file()
        handle.write.assert_called_once()

        written_content = handle.write.call_args[0][0]

        assert '"total_detections": 2' in written_content
        assert '"car": 1' in written_content
        assert '"person": 1' in written_content

        mock_subprocess.assert_called_once()
