from app.db.database import get_pg_conn, release_pg_conn

def create_tables():
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id         SERIAL PRIMARY KEY,
                    user_id    TEXT,
                    query      TEXT,
                    response   TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
    finally:
        release_pg_conn(conn)