import hashlib
from app.db.database import get_pg_conn, release_pg_conn, redis_client
from app.utils.config import REDIS_CACHE_TTL



def save_chat(user_id: str, query: str, response: str):
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_sessions (user_id, query, response)
                VALUES (%s, %s, %s)
                """,
                (user_id, query, response),
            )
        conn.commit()
    finally:
        release_pg_conn(conn)


def get_chat_history(user_id: str, limit: int = 20) -> list:
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=__import__("psycopg2.extras", fromlist=["RealDictCursor"]).RealDictCursor) as cur:
            cur.execute(
                """
                SELECT query, response, created_at
                FROM chat_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return cur.fetchall()
    finally:
        release_pg_conn(conn)



def _cache_key(query: str) -> str:
    """Stable cache key from query text."""
    return "lexai:query:" + hashlib.sha256(query.strip().lower().encode()).hexdigest()


def get_cached_response(query: str) -> str | None:
    """Return cached LLM response or None if cache miss."""
    return redis_client.get(_cache_key(query))


def set_cached_response(query: str, response: str):
    """Cache LLM response with TTL."""
    redis_client.setex(_cache_key(query), REDIS_CACHE_TTL, response)