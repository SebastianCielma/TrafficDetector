import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Traffic AI"
    API_URL: str = "http://localhost:8000"
    MODEL_PATH: str = "yolov8n.pt"
    UPLOAD_DIR: str = os.path.join("data", "uploads")
    RESULTS_DIR: str = os.path.join("data", "results")
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()


os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
