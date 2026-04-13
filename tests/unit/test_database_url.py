from app.infrastructure.persistence.db import _normalize_database_url


def test_normalize_database_url_supports_render_postgresql_urls():
    raw_url = "postgresql://user:password@host:5432/database"

    normalized = _normalize_database_url(raw_url)

    assert normalized == "postgresql+psycopg://user:password@host:5432/database"


def test_normalize_database_url_supports_legacy_postgres_urls():
    raw_url = "postgres://user:password@host:5432/database"

    normalized = _normalize_database_url(raw_url)

    assert normalized == "postgresql+psycopg://user:password@host:5432/database"


def test_normalize_database_url_keeps_psycopg_urls_unchanged():
    raw_url = "postgresql+psycopg://user:password@host:5432/database"

    normalized = _normalize_database_url(raw_url)

    assert normalized == raw_url
