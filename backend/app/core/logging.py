"""Centralised logging via loguru.

``configure_logging(settings)`` is called once at startup. It removes loguru's
default handler, installs a console sink at the configured level (JSON in prod),
and redirects stdlib + uvicorn logging into loguru.
"""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.core.config import Settings

__all__ = ["logger", "configure_logging"]


class _InterceptHandler(logging.Handler):
    """Route stdlib logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D102
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging(settings: "Settings") -> None:
    """Configure loguru sinks and intercept stdlib/uvicorn loggers."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        serialize=settings.log_json,
        backtrace=settings.debug,
        diagnose=settings.debug,
        enqueue=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    intercept = _InterceptHandler()
    logging.basicConfig(handlers=[intercept], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "httpx"):
        std = logging.getLogger(name)
        std.handlers = [intercept]
        std.propagate = False
    # httpx logs the full request URL at INFO; for the Google AI provider that URL
    # carries ?key=<API_KEY>. Raise its level so the secret never reaches a sink.
    logging.getLogger("httpx").setLevel(logging.WARNING)
