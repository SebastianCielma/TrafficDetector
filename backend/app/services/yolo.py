import cv2
import supervision as sv
from ultralytics import YOLO
from backend.app.core.config import settings
import os


class YoloService:
    def __init__(self):
        print(f"Loading YOLO model from {settings.MODEL_PATH}...")
        self.model = YOLO(settings.MODEL_PATH)

    def process_video(self, input_path: str, output_path: str, conf: float = 0.25):
        try:
            video_info = sv.VideoInfo.from_video_path(input_path)
            frame_generator = sv.get_video_frames_generator(input_path)

            box_annotator = sv.BoxAnnotator(thickness=2)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, video_info.fps, video_info.resolution_wh)

            for frame in frame_generator:
                result = self.model(frame, conf=conf, verbose=False)[0]
                detections = sv.Detections.from_ultralytics(result)

                annotated_frame = box_annotator.annotate(scene=frame, detections=detections)
                writer.write(annotated_frame)

            writer.release()
            return True
        except Exception as e:
            print(f"❌ YoloService Error: {e}")
            raise e