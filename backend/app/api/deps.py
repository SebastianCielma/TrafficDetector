from functools import lru_cache
from backend.app.services.yolo import YoloService

@lru_cache()
def get_yolo_service() -> YoloService:
    return YoloService()