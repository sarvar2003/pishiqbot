from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# libpq-style query params some managed Postgres providers (e.g. `fly postgres
# attach`) append to DATABASE_URL. asyncpg's connect() doesn't accept them as
# keyword arguments, so they must be translated (sslmode) or dropped, never
# just left in the URL's query string.
_SSLMODE_TO_ASYNCPG_SSL = {
    "disable": False,
    "allow": None,
    "prefer": None,
    "require": True,
    "verify-ca": True,
    "verify-full": True,
}
_UNSUPPORTED_QUERY_PARAMS = {"sslmode", "channel_binding", "gssencmode"}


def split_connect_args(url: str) -> tuple[str, dict]:
    """Strips libpq-only query params from a DSN and translates the ones that
    matter into asyncpg connect_args, so create_async_engine gets a clean URL.
    """
    parts = urlsplit(url)
    connect_args: dict = {}
    kept = []
    for key, value in parse_qsl(parts.query):
        if key == "sslmode":
            ssl_value = _SSLMODE_TO_ASYNCPG_SSL.get(value)
            if ssl_value is not None:
                connect_args["ssl"] = ssl_value
        elif key in _UNSUPPORTED_QUERY_PARAMS:
            continue
        else:
            kept.append((key, value))

    clean_url = urlunsplit(parts._replace(query=urlencode(kept)))
    return clean_url, connect_args
