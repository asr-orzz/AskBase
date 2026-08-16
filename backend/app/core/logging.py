import logging
import sys

import structlog

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()

    log_level = logging.DEBUG if settings.debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if not settings.is_production
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    for noisy_logger in ["uvicorn.access", "sqlalchemy.engine"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
