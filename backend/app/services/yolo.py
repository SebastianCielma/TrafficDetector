import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import List

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


class YoloService:
    def __init__(self) -> None:
        logger.info(f"Loading YOLO model from {settings.MODEL_PATH}...")
        # type: ignore
        self.model = YOLO(settings.MODEL_PATH)

    def process_video(
        self, input_path: str, output_path: str, conf: float = 0.25
    ) -> str:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        in_p = Path(input_path)
        out_p = Path(output_path)

        temp_video_path = out_p.with_name(f"{out_p.stem}_temp{out_p.suffix}")
        json_output_path = out_p.with_suffix(".json")

        logger.info("processing_started", input=str(in_p))

        video_info = sv.VideoInfo.from_video_path(str(in_p))
        frame_generator = sv.get_video_frames_generator(str(in_p))
        box_annotator = sv.BoxAnnotator(thickness=2)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
        writer = cv2.VideoWriter(
            str(temp_video_path), fourcc, video_info.fps, video_info.resolution_wh
        )

        total_counts: Counter[str] = Counter()
        time_series_data: List[FrameDetection] = []
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
                        self.model.model.names[cid]  # type: ignore
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
                raise RuntimeError("No frames processed.")

            report = self._build_report(
                video_info, in_p.name, total_counts, time_series_data
            )

            with open(json_output_path, "w") as f:
                f.write(report.model_dump_json(indent=2))

            logger.info("analytics_generated", json_path=str(json_output_path))
            self._convert_to_h264(str(temp_video_path), str(out_p))

        except Exception as e:
            logger.error("processing_failed", error=str(e))
            raise e
        finally:
            self._cleanup(str(temp_video_path), writer)

        return str(json_output_path)

    def _build_report(
        self,
        info: sv.VideoInfo,
        filename: str,
        counts: Counter[str],
        series: List[FrameDetection],
    ) -> AnalyticsReport:
        most_common = counts.most_common(1)

        tf = info.total_frames or 0
        duration = 0.0
        if info.fps > 0:
            duration = round(tf / info.fps, 2)

        return AnalyticsReport(
            meta=VideoMeta(
                source_filename=filename,
                fps=info.fps,
                total_frames=tf,
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

    def _cleanup(self, temp_path: str, writer: cv2.VideoWriter) -> None:
        try:
            writer.release()
        except Exception:
            pass
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as e:
                logger.warning(f"Could not remove temp file: {e}")
