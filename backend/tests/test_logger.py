import logging
from unittest.mock import patch

import pytest

from backend.app.core.logger import setup_logging


@pytest.fixture
def mock_loki_handler():
    with patch("backend.app.core.logger.LokiHandler") as mock:
        yield mock


@pytest.fixture
def mock_structlog_configure():
    with patch("backend.app.core.logger.structlog.configure") as mock:
        yield mock


@pytest.fixture
def mock_logging_basic_config():
    with patch("backend.app.core.logger.logging.basicConfig") as mock:
        yield mock


@pytest.fixture
def mock_processor_formatter():
    with patch("backend.app.core.logger.structlog.stdlib.ProcessorFormatter") as mock:
        yield mock


@pytest.fixture
def mock_renderers():
    with (
        patch("backend.app.core.logger.structlog.processors.JSONRenderer") as json_mock,
        patch("backend.app.core.logger.structlog.dev.ConsoleRenderer") as console_mock,
    ):
        yield json_mock, console_mock


@pytest.mark.parametrize(
    "environment, loki_url, expect_json, expect_loki",
    [
        ("development", None, False, False),
        ("production", "http://loki", True, True),
    ],
)
def test_setup_logging_configuration(
    environment,
    loki_url,
    expect_json,
    expect_loki,
    mock_loki_handler,
    mock_structlog_configure,
    mock_logging_basic_config,
    mock_processor_formatter,
    mock_renderers,
):
    mock_json_cls, mock_console_cls = mock_renderers

    with patch("backend.app.core.logger.settings") as mock_settings:
        mock_settings.ENVIRONMENT = environment
        mock_settings.LOKI_URL = loki_url
        mock_settings.LOKI_USERNAME = "user" if loki_url else None
        mock_settings.LOKI_PASSWORD = "pass" if loki_url else None

        setup_logging()

        assert mock_structlog_configure.called

        assert mock_processor_formatter.called
        formatter_call_kwargs = mock_processor_formatter.call_args[1]
        used_renderer = formatter_call_kwargs.get("processor")

        if expect_json:
            assert used_renderer == mock_json_cls.return_value
        else:
            assert used_renderer == mock_console_cls.return_value

        basic_config_kwargs = mock_logging_basic_config.call_args[1]
        handlers = basic_config_kwargs["handlers"]

        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

        if expect_loki:
            mock_loki_handler.assert_called_once()
            loki_instance = mock_loki_handler.return_value
            loki_instance.setFormatter.assert_called_with(
                mock_processor_formatter.return_value
            )

            assert loki_instance in handlers
        else:
            mock_loki_handler.assert_not_called()
