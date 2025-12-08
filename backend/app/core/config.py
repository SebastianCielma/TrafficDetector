import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Traffic AI"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"

    DATABASE_URL: str

    MODEL_PATH: str = "yolov8n.pt"

    S3_BUCKET_NAME: str
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str | None = None

    LOKI_URL: str | None = None
    LOKI_USERNAME: str | None = None
    LOKI_PASSWORD: str | None = None

    UPLOAD_DIR: str = os.path.join("data", "uploads")
    RESULTS_DIR: str = os.path.join("data", "results")

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )


settings = Settings()  # type: ignore

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
