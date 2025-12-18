"""Analytics schemas for video processing reports."""

from pydantic import BaseModel, ConfigDict


class FrameDetection(BaseModel):
    """Detection data for a single video frame."""

    frame_id: int
    timestamp: float
    objects: dict[str, int]


class VideoMeta(BaseModel):
    """Metadata about the processed video."""

    source_filename: str
    fps: float
    total_frames: int
    resolution: tuple[int, int]
    duration_seconds: float


class AnalysisSummary(BaseModel):
    """Summary statistics from video analysis."""

    total_detections: int
    unique_classes: list[str]
    dominant_class: str | None
    class_distribution: dict[str, int]


class AnalyticsReport(BaseModel):
    """Complete analytics report for a processed video."""

    meta: VideoMeta
    summary: AnalysisSummary
    time_series: list[FrameDetection]

    model_config = ConfigDict(from_attributes=True)
