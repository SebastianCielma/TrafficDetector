from pydantic import BaseModel

class DetectionResponse(BaseModel):
    task_id: str
    status: str