import os
import subprocess

import cv2
import supervision as sv
from ultralytics import YOLO

from backend.app.core.config import settings


class YoloService:
    def __init__(self):
        print(f"Loading YOLO model from {settings.MODEL_PATH}...")
        self.model = YOLO(settings.MODEL_PATH)

    def process_video(self, input_path: str, output_path: str, conf: float = 0.25):
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        print(f"🎬 Processing video: {input_path}")

        video_info = sv.VideoInfo.from_video_path(input_path)

        temp_output_path = output_path.replace(".mp4", "_temp.mp4")

        frame_generator = sv.get_video_frames_generator(input_path)
        box_annotator = sv.BoxAnnotator(thickness=2)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            temp_output_path, fourcc, video_info.fps, video_info.resolution_wh
        )

        processed_frames = 0
        try:
            for frame in frame_generator:
                result = self.model(frame, conf=conf, verbose=False)[0]
                detections = sv.Detections.from_ultralytics(result)

                annotated_frame = box_annotator.annotate(
                    scene=frame, detections=detections
                )
                writer.write(annotated_frame)
                processed_frames += 1

            writer.release()

            if processed_frames == 0:
                raise RuntimeError("No frames were processed!")

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_output_path,
                    "-vcodec",
                    "libx264",
                    "-acodec",
                    "aac",
                    "-strict",
                    "experimental",
                    output_path,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        except Exception as e:
            print(f"Error processing video: {e}")
            raise e
        finally:
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            try:
                writer.release()
            except Exception:
                pass

        return True
