"""HTTP middleware: request-id, structured access log, optional API key."""

from __future__ import annotations

import logging
import os
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.infrastructure.logging.request_context import reset_request_id, set_request_id

logger = logging.getLogger("app.http")

REQUEST_ID_HEADER = "X-Request-ID"
API_KEY_HEADER = "X-API-Key"

# Paths that must stay reachable without authentication, even when an API key
# is configured. Probes, docs and the OpenAPI schema are expected to be public.
_PUBLIC_PATHS = {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a request id and emit one structured access-log line per request."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = set_request_id(incoming)
        start = time.perf_counter()

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            reset_request_id()
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        reset_request_id()
        return response


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Optional shared-secret check.

    If ``API_KEY`` is set in the environment, every non-public request must
    carry a matching ``X-API-Key`` header. When the env var is unset the
    middleware is a no-op — this keeps local dev / E2E tests frictionless.
    """

    async def dispatch(self, request: Request, call_next):
        expected = os.getenv("API_KEY")
        if not expected:
            return await call_next(request)

        if request.method == "OPTIONS" or request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        provided = request.headers.get(API_KEY_HEADER)
        if provided != expected:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key."},
            )

        return await call_next(request)
