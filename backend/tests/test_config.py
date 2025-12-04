import os

from backend.app.core.config import Settings, settings


def test_directories_created():
    assert os.path.exists(settings.UPLOAD_DIR)
    assert os.path.exists(settings.RESULTS_DIR)


def test_pydantic_settings_env_precedence(monkeypatch):
    monkeypatch.setenv("PROJECT_NAME", "Test Unit Project")

    test_settings = Settings(_env_file=None)

    assert test_settings.PROJECT_NAME == "Test Unit Project"
