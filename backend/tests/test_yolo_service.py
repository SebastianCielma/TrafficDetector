from unittest.mock import MagicMock, mock_open, patch

import pytest

from backend.app.services.yolo import YoloService


@pytest.fixture
def mock_dependencies():
    with (
        patch("backend.app.services.yolo.cv2") as cv2,
        patch("backend.app.services.yolo.sv") as sv,
        patch("backend.app.services.yolo.YOLO") as yolo,
        patch("backend.app.services.yolo.subprocess.run") as subprocess,
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

    with (
        patch("backend.app.services.yolo.os.path.exists", return_value=True),
        patch("backend.app.services.yolo.os.remove") as mock_remove,
        patch("backend.app.core.config.settings.MODEL_PATH", "dummy.pt"),
        patch("builtins.open", mock_open()) as mock_file,
    ):
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
        mock_remove.assert_called_with("output_temp.mp4")
