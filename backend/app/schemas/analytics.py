from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class FrameDetection(BaseModel):
    frame_id: int
    timestamp: float
    objects: Dict[str, int]


class VideoMeta(BaseModel):
    source_filename: str
    fps: float
    total_frames: int
    resolution: tuple[int, int]
    duration_seconds: float


class AnalysisSummary(BaseModel):
    total_detections: int
    unique_classes: List[str]
    dominant_class: Optional[str]
    class_distribution: Dict[str, int]


class AnalyticsReport(BaseModel):
    meta: VideoMeta
    summary: AnalysisSummary
    time_series: List[FrameDetection]

    model_config = ConfigDict(from_attributes=True)
