from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging.setup import configure_logging
from app.infrastructure.persistence.db import Base, engine, ensure_ticket_columns
from app.interfaces.api.middleware import ApiKeyMiddleware, RequestContextMiddleware
from app.interfaces.api.routes.admin import router as admin_router
from app.interfaces.api.routes.system import router as system_router
from app.interfaces.api.routes.tickets import router as tickets_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    Base.metadata.create_all(bind=engine)
    ensure_ticket_columns()

    application = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description=(
            "REST API for AI-assisted ticket triage. "
            "Exposes use cases, analytics and admin operations behind a clean "
            "domain-driven architecture. Full OpenAPI schema at /openapi.json."
        ),
    )

    # NOTE: middleware ordering in Starlette is LIFO — the middleware added
    # *last* is the outermost one. We want request-id to be outermost so the
    # id is available inside every inner middleware and handler, and the
    # optional API-key check to sit just below it.
    application.add_middleware(ApiKeyMiddleware)
    application.add_middleware(RequestContextMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(system_router)
    application.include_router(tickets_router)
    application.include_router(admin_router)

    return application


app = create_app()
