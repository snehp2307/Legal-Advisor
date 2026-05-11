import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    dbname="legal_ai",
    user="postgres",
    password="admin",
    host="postgres",
    port="5432"
)

cursor = conn.cursor(cursor_factory=RealDictCursor)