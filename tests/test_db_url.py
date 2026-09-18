from __future__ import annotations

from app.utils.db_url import split_connect_args


def test_sslmode_disable_becomes_asyncpg_ssl_false() -> None:
    clean_url, connect_args = split_connect_args(
        "postgresql+asyncpg://user:pass@host:5432/db?sslmode=disable"
    )

    assert clean_url == "postgresql+asyncpg://user:pass@host:5432/db"
    assert connect_args == {"ssl": False}


def test_sslmode_require_becomes_asyncpg_ssl_true() -> None:
    _, connect_args = split_connect_args("postgresql+asyncpg://user:pass@host:5432/db?sslmode=require")

    assert connect_args == {"ssl": True}


def test_unsupported_params_are_dropped_without_translation() -> None:
    clean_url, connect_args = split_connect_args(
        "postgresql+asyncpg://user:pass@host:5432/db?channel_binding=require&gssencmode=disable"
    )

    assert clean_url == "postgresql+asyncpg://user:pass@host:5432/db"
    assert connect_args == {}


def test_url_without_query_params_is_untouched() -> None:
    url = "postgresql+asyncpg://user:pass@host:5432/db"
    clean_url, connect_args = split_connect_args(url)

    assert clean_url == url
    assert connect_args == {}


def test_sqlite_triple_slash_url_is_not_mangled() -> None:
    # Regression: urlsplit/urlunsplit drops a slash on netloc-less URLs
    # (sqlite:///path) unless the no-query-params path is short-circuited.
    url = "sqlite+aiosqlite:///./pishiqbot.db"
    clean_url, connect_args = split_connect_args(url)

    assert clean_url == url
    assert connect_args == {}


def test_unrelated_query_params_are_kept() -> None:
    clean_url, connect_args = split_connect_args(
        "postgresql+asyncpg://user:pass@host:5432/db?application_name=pishiqbot"
    )

    assert clean_url == "postgresql+asyncpg://user:pass@host:5432/db?application_name=pishiqbot"
    assert connect_args == {}
