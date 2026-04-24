"""Request-ID propagation via contextvars.

Provides a stable correlation id per HTTP request so logs can be grouped even
when the app serves many requests in parallel. The middleware reads an
incoming ``X-Request-ID`` header if present (useful behind a load balancer /
reverse proxy), otherwise generates a new UUID.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _REQUEST_ID.get()


def set_request_id(value: str | None = None) -> str:
    resolved = value or uuid.uuid4().hex
    _REQUEST_ID.set(resolved)
    return resolved


def reset_request_id() -> None:
    _REQUEST_ID.set("-")
