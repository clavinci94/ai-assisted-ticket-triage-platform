"""Global exception handlers that hide internals from clients.

Without this, any unhandled exception (and many handled ones) reach the
client as ``{"detail": "<full Python str of the exception>"}`` — which
leaks stack-trace fragments, DB connection strings, file paths, and
sometimes secrets. Production-grade APIs return a generic message plus
a correlation id; the operator finds the real detail in the structured
log line tagged with the same request id.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.infrastructure.logging.request_context import get_request_id

logger = logging.getLogger(__name__)


def _problem_response(
    *,
    status_code: int,
    detail: str,
    request: Request,
    extra_headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = get_request_id()
    body: dict[str, object] = {"detail": detail}
    if request_id:
        body["request_id"] = request_id

    headers: dict[str, str] = {}
    if extra_headers:
        headers.update(extra_headers)
    if request_id:
        headers["X-Request-ID"] = request_id

    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """FastAPI/Starlette HTTPException — keep the developer-authored detail."""

    extra_headers = getattr(exc, "headers", None)
    return _problem_response(
        status_code=exc.status_code,
        detail=str(exc.detail) if exc.detail is not None else "Unexpected error.",
        request=request,
        extra_headers=extra_headers,
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic validation — surface the parsed errors, not a generic 500."""

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed.",
            "errors": exc.errors(),
            **({"request_id": get_request_id()} if get_request_id() else {}),
        },
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Anything we didn't anticipate — log full stack, return generic message."""

    logger.exception(
        "unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )
    return _problem_response(
        status_code=500,
        detail=("An internal error occurred. Reference the request_id when reporting this to the operator."),
        request=request,
    )


def register_error_handlers(application: FastAPI) -> None:
    """Attach the three handlers to a FastAPI instance."""

    application.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    application.add_exception_handler(HTTPException, _http_exception_handler)
    application.add_exception_handler(RequestValidationError, _validation_exception_handler)
    application.add_exception_handler(Exception, _unhandled_exception_handler)
