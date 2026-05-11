from app.db.database import conn, cursor

def save_chat(user_id, query, response):
    cursor.execute("""
        INSERT INTO chat_sessions (user_id, query, response)
        VALUES (%s, %s, %s)
    """, (user_id, query, response))

    conn.commit()