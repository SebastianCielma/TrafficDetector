"""Detection endpoint response schemas."""

from pydantic import BaseModel


class DetectionResponse(BaseModel):
    """Response model for the detection endpoint."""

    task_id: str
    status: str
