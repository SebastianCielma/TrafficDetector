import shutil
import subprocess
from collections import Counter
from pathlib import Path

import cv2
import supervision as sv
from ultralytics import YOLO

from backend.app.core.config import settings
from backend.app.core.logger import get_logger
from backend.app.schemas.analytics import (
    AnalysisSummary,
    AnalyticsReport,
    FrameDetection,
    VideoMeta,
)

logger = get_logger(__name__)


class YoloServiceError(Exception):
    """Base exception for YoloService errors."""


class FfmpegNotFoundError(YoloServiceError):
    """Raised when ffmpeg is not found in the system."""


class VideoProcessingError(YoloServiceError):
    """Raised when video processing fails."""


class YoloService:
    """Service for video processing using YOLO object detection."""

    def __init__(self) -> None:
        """Initialize the YOLO service and verify dependencies."""
        self._verify_ffmpeg()
        logger.info("yolo_model_loading", model_path=settings.MODEL_PATH)
        self.model = YOLO(settings.MODEL_PATH)
        logger.info("yolo_model_loaded")

    def _verify_ffmpeg(self) -> None:
        """Verify that ffmpeg is available in the system.

        Raises:
            FfmpegNotFoundError: If ffmpeg is not found.
        """
        if shutil.which("ffmpeg") is None:
            raise FfmpegNotFoundError(
                "ffmpeg is not installed or not in PATH. "
                "Please install ffmpeg to enable video conversion."
            )

    def process_video(
        self, input_path: str, output_path: str, conf: float = 0.25
    ) -> str:
        """Process a video file with YOLO object detection.

        Args:
            input_path: Path to the input video file.
            output_path: Path for the output annotated video.
            conf: Confidence threshold for detections.

        Returns:
            Path to the generated analytics JSON file.

        Raises:
            FileNotFoundError: If input video doesn't exist.
            VideoProcessingError: If video processing fails.
        """
        if not Path(input_path).exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")

        in_p = Path(input_path)
        out_p = Path(output_path)

        temp_video_path = out_p.with_name(f"{out_p.stem}_temp{out_p.suffix}")
        json_output_path = out_p.with_suffix(".json")

        logger.info("processing_started", input=str(in_p))

        video_info = sv.VideoInfo.from_video_path(str(in_p))
        frame_generator = sv.get_video_frames_generator(str(in_p))
        box_annotator = sv.BoxAnnotator(thickness=2)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
        writer = cv2.VideoWriter(
            str(temp_video_path), fourcc, video_info.fps, video_info.resolution_wh
        )

        total_counts: Counter[str] = Counter()
        time_series_data: list[FrameDetection] = []
        processed_frames = 0

        try:
            for i, frame in enumerate(frame_generator):
                result = self.model(frame, conf=conf, verbose=False)[0]
                detections = sv.Detections.from_ultralytics(result)

                annotated_frame = box_annotator.annotate(
                    scene=frame, detections=detections
                )
                writer.write(annotated_frame)

                if detections.class_id is not None:
                    class_names = [
                        self.model.model.names[cid]  # type: ignore[union-attr]
                        for cid in detections.class_id
                    ]

                    frame_counts = Counter(class_names)
                    total_counts.update(class_names)

                    if frame_counts:
                        time_series_data.append(
                            FrameDetection(
                                frame_id=i,
                                timestamp=round(i / video_info.fps, 2),
                                objects=dict(frame_counts),
                            )
                        )

                processed_frames += 1

            writer.release()

            if processed_frames == 0:
                raise VideoProcessingError("No frames were processed from the video.")

            report = self._build_report(
                video_info, in_p.name, total_counts, time_series_data
            )

            with open(json_output_path, "w") as f:
                f.write(report.model_dump_json(indent=2))

            logger.info("analytics_generated", json_path=str(json_output_path))
            self._convert_to_h264(str(temp_video_path), str(out_p))

        except Exception as e:
            logger.error("processing_failed", error=str(e))
            raise VideoProcessingError(f"Video processing failed: {e}") from e
        finally:
            self._cleanup(str(temp_video_path), writer)

        return str(json_output_path)

    def _build_report(
        self,
        info: sv.VideoInfo,
        filename: str,
        counts: Counter[str],
        series: list[FrameDetection],
    ) -> AnalyticsReport:
        """Build an analytics report from processed video data.

        Args:
            info: Video information from supervision.
            filename: Original filename.
            counts: Total detection counts per class.
            series: Time series of frame detections.

        Returns:
            Complete analytics report.
        """
        most_common = counts.most_common(1)

        total_frames = info.total_frames or 0
        duration = 0.0
        if info.fps > 0:
            duration = round(total_frames / info.fps, 2)

        return AnalyticsReport(
            meta=VideoMeta(
                source_filename=filename,
                fps=info.fps,
                total_frames=total_frames,
                resolution=info.resolution_wh,
                duration_seconds=duration,
            ),
            summary=AnalysisSummary(
                total_detections=sum(counts.values()),
                unique_classes=list(counts.keys()),
                dominant_class=most_common[0][0] if most_common else None,
                class_distribution=dict(counts),
            ),
            time_series=series,
        )

    def _convert_to_h264(self, source: str, target: str) -> None:
        """Convert video to H.264 codec using ffmpeg.

        Args:
            source: Source video path.
            target: Target video path.

        Raises:
            VideoProcessingError: If conversion fails.
        """
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    source,
                    "-vcodec",
                    "libx264",
                    "-acodec",
                    "aac",
                    "-strict",
                    "experimental",
                    target,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(f"ffmpeg conversion failed: {e}") from e

    def _cleanup(self, temp_path: str, writer: cv2.VideoWriter) -> None:
        """Clean up temporary resources.

        Args:
            temp_path: Path to temporary video file.
            writer: OpenCV video writer to release.
        """
        try:
            writer.release()
        except Exception:
            pass

        temp_file = Path(temp_path)
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError as e:
                logger.warning("temp_file_cleanup_failed", path=temp_path, error=str(e))
