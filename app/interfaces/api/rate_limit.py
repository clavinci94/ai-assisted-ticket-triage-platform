"""Per-IP rate limiting for the LLM-bound endpoints.

The /tickets/triage/llm and /tickets/triage/llm/preview routes can each
trigger an outbound LiteLLM call — i.e. real money per request. Without
throttling, a single laptop can drain the LLM budget in seconds. We
default to a conservative limit and let operators tune it via the env
var ``LLM_RATE_LIMIT`` (any slowapi spec, e.g. ``"30/minute"`` or
``"500/hour"``).

The limiter exempts the public probes and the docs so platform-level
liveness checks aren't throttled.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

DEFAULT_LLM_RATE_LIMIT = "30/minute"


def _llm_rate_limit() -> str:
    return os.getenv("LLM_RATE_LIMIT", DEFAULT_LLM_RATE_LIMIT)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # opt-in per-endpoint, not global
    # ``headers_enabled`` requires a Response param on every limited route;
    # we keep routes Pydantic-typed and surface limits via the 429 body
    # (including the Retry-After header in _rate_limit_handler) instead.
    headers_enabled=False,
)


def install_rate_limiter(application: FastAPI) -> None:
    """Wire the slowapi limiter into a FastAPI app."""

    application.state.limiter = limiter
    application.add_middleware(SlowAPIMiddleware)
    application.add_exception_handler(RateLimitExceeded, _rate_limit_handler)


def llm_rate_limit():
    """Decorator factory for LLM-bound routes.

    Usage:

        @router.post("/triage/llm")
        @llm_rate_limit()
        def triage_llm(request: Request, ...): ...

    The ``request`` parameter must appear in the route signature for
    slowapi to read the client IP. We pass ``_llm_rate_limit`` (callable,
    not its return value) so slowapi re-reads the env var per request —
    tests can override LLM_RATE_LIMIT without re-importing the route.
    """

    return limiter.limit(_llm_rate_limit)


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning(
        "rate limit exceeded",
        extra={"path": request.url.path, "client": get_remote_address(request)},
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Too many requests to the AI endpoint. "
                f"Limit is {_llm_rate_limit()} per client. Retry after a moment."
            ),
        },
        headers={"Retry-After": "30"},
    )
