import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Traffic AI"
    API_URL: str = "http://localhost:8000"
    MODEL_PATH: str = "yolov8n.pt"

    DATABASE_URL: str = (
        "postgresql+asyncpg://traffic_user:traffic_password@localhost:5432/traffic_db"
    )

    UPLOAD_DIR: str = os.path.join("data", "uploads")
    RESULTS_DIR: str = os.path.join("data", "results")
    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=True
    )


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
