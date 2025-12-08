import logging
import sys
from typing import List

import structlog
from asgi_correlation_id import correlation_id
from logging_loki import LokiHandler

from backend.app.core.config import settings


def setup_logging():
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    def add_correlation(logger, method_name, event_dict):
        if request_id := correlation_id.get():
            event_dict["request_id"] = request_id
        return event_dict

    shared_processors.append(add_correlation)

    if settings.ENVIRONMENT == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    handlers: List[logging.Handler] = [stream_handler]

    if settings.LOKI_URL and settings.LOKI_USERNAME and settings.LOKI_PASSWORD:
        loki_handler = LokiHandler(
            url=settings.LOKI_URL,
            tags={"app": "traffic-detector", "env": settings.ENVIRONMENT},
            auth=(settings.LOKI_USERNAME, settings.LOKI_PASSWORD),
            version="1",
        )
        loki_handler.setFormatter(formatter)
        handlers.append(loki_handler)

    logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=handlers)

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True


def get_logger(name: str):
    return structlog.get_logger(name)
