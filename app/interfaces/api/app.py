from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config.settings import get_settings
from app.infrastructure.persistence.db import Base, engine, ensure_ticket_columns
from app.interfaces.api.routes.admin import router as admin_router
from app.interfaces.api.routes.system import router as system_router
from app.interfaces.api.routes.tickets import router as tickets_router


def create_app() -> FastAPI:
    settings = get_settings()

    Base.metadata.create_all(bind=engine)
    ensure_ticket_columns()

    application = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
    )

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
