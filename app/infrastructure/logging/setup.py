"""Structured JSON logging setup.

Configured once at application startup. Every log record is emitted as a JSON
line with a stable schema, making it straightforward to pipe logs into
platforms like CloudWatch, Loki, or Render's own log explorer.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

from app.infrastructure.logging.request_context import get_request_id

_CONFIGURED = False

_SENSITIVE_ATTRIBUTES = {
    "args",
    "msg",
    "message",
    "exc_info",
    "exc_text",
    "stack_info",
    "pathname",
    "filename",
    "module",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "name",
    "levelname",
    "levelno",
}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Copy through any extra=... attributes that callers attached.
        for key, value in record.__dict__.items():
            if key in _SENSITIVE_ATTRIBUTES or key.startswith("_"):
                continue
            if key in payload:
                continue
            try:
                json.dumps(value, default=str)
            except (TypeError, ValueError):
                continue
            payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: str | None = None) -> None:
    """Install the JSON formatter on the root logger.

    Idempotent — safe to call multiple times (e.g. from tests).
    """

    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    root = logging.getLogger()
    root.setLevel(resolved_level)

    # Remove any handlers that were installed before us (uvicorn default, etc.)
    # so log lines are not duplicated in JSON + plain-text form.
    for existing in list(root.handlers):
        root.removeHandler(existing)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers without hiding our own.
    logging.getLogger("uvicorn.error").setLevel(resolved_level)
    logging.getLogger("uvicorn.access").setLevel("WARNING")

    _CONFIGURED = True
