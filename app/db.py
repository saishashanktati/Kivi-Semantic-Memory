"""Database access. One connection pool, opened once, used everywhere."""
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

from app.config import DATABASE_URL

_pool: ConnectionPool | None = None


def _configure(conn: psycopg.Connection) -> None:
    """Runs on every new connection so vector types work."""
    register_vector(conn)


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            configure=_configure,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


@contextmanager
def conn():
    """Use as:  with conn() as c: c.execute(...)"""
    with pool().connection() as c:
        yield c


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT, get a list of dicts back."""
    with conn() as c:
        cur = c.execute(sql, params)
        return cur.fetchall()


def execute(sql: str, params: tuple = ()) -> None:
    """Run an INSERT/UPDATE/DELETE."""
    with conn() as c:
        c.execute(sql, params)


def log_decision(
    user_id: str,
    stage: str,
    verdict: str,
    reason: str,
    detail: dict | None = None,
    episode_id: str | None = None,
    query_id: str | None = None,
    model: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    latency_ms: int | None = None,
) -> None:
    """Every meaningful decision gets a row. This is the inspectability layer (§7.13)."""
    import json

    execute(
        """
        insert into decisions
          (user_id, episode_id, query_id, stage, verdict, reason, detail,
           model, tokens_in, tokens_out, latency_ms)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            user_id, episode_id, query_id, stage, verdict, reason,
            json.dumps(detail or {}), model, tokens_in, tokens_out, latency_ms,
        ),
    )
