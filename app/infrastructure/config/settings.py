import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
)


@dataclass(frozen=True)
class ApiSettings:
    app_title: str
    app_version: str
    cors_origins: tuple[str, ...]


def _parse_origins(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return DEFAULT_CORS_ORIGINS

    origins = tuple(origin.strip() for origin in raw_value.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings(
        app_title=os.getenv("APP_TITLE", "AI-assisted Requirements & Ticket Triage Platform"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        cors_origins=_parse_origins(os.getenv("CORS_ALLOW_ORIGINS")),
    )
