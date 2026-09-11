"""Database connection module for Supabase Postgres via Supavisor."""

from contextlib import contextmanager
from typing import Generator, Any, Optional

import psycopg

from app.config import settings


def get_connection() -> psycopg.Connection:
    """Create a new database connection.
    
    Uses SUPABASE_DB_URL from environment. This should point to
    Supavisor session mode (port 5432) for Lambda compatibility.
    """
    if not settings.supabase_db_url:
        raise RuntimeError("SUPABASE_DB_URL not configured")

    # Pin the session to UTC so CURRENT_DATE / timestamptz casts line up with
    # the UTC datetimes the app writes (review due-dates, streaks, timestamps).
    return psycopg.connect(settings.supabase_db_url, options="-c timezone=UTC")


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    """Context manager for database connections.
    
    Usage:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM decks WHERE user_id = %s", [user_id])
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


async def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception:
        return False
