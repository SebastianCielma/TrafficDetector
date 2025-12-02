import os

from backend.app.core.config import Settings, settings


def test_pydantic_settings_loaded():
    assert settings.PROJECT_NAME is not None
    assert settings.API_URL is not None
    assert settings.API_URL.startswith("http")
    assert "yolo" in settings.MODEL_PATH


def test_directories_created():
    assert os.path.exists(settings.UPLOAD_DIR)
    assert os.path.isdir(settings.UPLOAD_DIR)
    assert os.path.exists(settings.RESULTS_DIR)


def test_env_override(monkeypatch):
    monkeypatch.setenv("PROJECT_NAME", "Testowy Projekt AI")

    new_settings = Settings()

    assert new_settings.PROJECT_NAME == "Testowy Projekt AI"
