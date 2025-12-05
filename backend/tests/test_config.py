from backend.app.core.config import Settings


def test_pydantic_settings_env_precedence(monkeypatch):
    env_vars = {
        "PROJECT_NAME": "Test Unit Project",
        "DATABASE_URL": "postgresql://user:pass@localhost/db",
        "S3_BUCKET_NAME": "test-bucket",
        "S3_ENDPOINT": "https://fake-endpoint",
        "S3_ACCESS_KEY": "fake-key",
        "S3_SECRET_KEY": "fake-secret",
        "TRAFFIC_BUCKET_NAME": "test-bucket",
        "TRAFFIC_ENDPOINT": "https://fake-endpoint",
        "TRAFFIC_ACCESS_KEY": "fake-key",
        "TRAFFIC_SECRET_KEY": "fake-secret",
        "CELERY_BROKER_URL": "redis://fake-redis:6379/0",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    test_settings = Settings(_env_file=None)

    assert test_settings.PROJECT_NAME == "Test Unit Project"
