import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Traffic AI"
    MODEL_PATH: str = "yolo8n.pt"
    UPLOAD_DIR: str = os.path.join("data","uploads")
    RESULTS_DIR: str = os.path.join("data","results")
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"

settings = Settings()


os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
