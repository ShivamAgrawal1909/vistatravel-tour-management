"""
Ensure the configured MySQL/MariaDB database exists before SQLAlchemy creates tables.

Fixes OperationalError 1049 (Unknown database). Older MySQL (< 5.5.3) does not support
utf8mb4; bootstrap connects with charset=utf8 and falls back CREATE DATABASE to utf8
if the server returns 1115 Unknown character set 'utf8mb4'.
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

_DB_NAME_RE = re.compile(r"^[a-zA-Z0-9_]{1,64}$")

_MYSQL_FAMILY = frozenset(
    {
        "mysql+pymysql",
        "mysql+mysqldb",
        "mysql+cymysql",
        "mariadb+pymysql",
        "mariadb+mysqldb",
    }
)

_DDL_UTF8MB4 = (
    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)
_DDL_UTF8 = (
    "CHARACTER SET utf8 COLLATE utf8_general_ci"
)


def ensure_mysql_database(uri: str | None) -> None:
    if not uri:
        return

    from sqlalchemy import create_engine, text
    from sqlalchemy.engine.url import make_url, URL
    from sqlalchemy.exc import OperationalError

    try:
        url = make_url(uri)
    except Exception as e:
        logger.warning("Could not parse DATABASE_URL: %s", e)
        return

    if url.drivername not in _MYSQL_FAMILY:
        return

    db_name = url.database
    if not db_name:
        return

    if not _DB_NAME_RE.match(db_name):
        logger.warning(
            "Skipping auto-create: database name must be 1–64 chars [a-zA-Z0-9_], got %r",
            db_name,
        )
        return

    # Always use utf8 for this short admin connection — avoids 1115 on MySQL without utf8mb4.
    admin_query = dict(url.query)
    admin_query["charset"] = "utf8"

    admin = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host if url.host else "127.0.0.1",
        port=url.port if url.port is not None else 3306,
        database="mysql",
        query=admin_query,
    )

    ddl_mb4 = f"CREATE DATABASE IF NOT EXISTS `{db_name}` {_DDL_UTF8MB4}"
    ddl_utf8 = f"CREATE DATABASE IF NOT EXISTS `{db_name}` {_DDL_UTF8}"

    engine = create_engine(admin, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            try:
                conn.execute(text(ddl_mb4))
            except OperationalError as e:
                orig = getattr(e, "orig", None)
                errno = getattr(orig, "args", [None])[0]
                if errno == 1115:
                    logger.info(
                        "Server has no utf8mb4; creating database %r with utf8 instead",
                        db_name,
                    )
                    conn.execute(text(ddl_utf8))
                else:
                    raise
    finally:
        engine.dispose()
