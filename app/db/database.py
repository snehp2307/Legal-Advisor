import redis
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from app.utils.config import (
    POSTGRES_DB, POSTGRES_USER, POSTGRES_PASS,
    POSTGRES_HOST, POSTGRES_PORT,
    REDIS_HOST, REDIS_PORT
)

pg_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASS,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
)

def get_pg_conn():
    """Borrow a connection from the pool."""
    return pg_pool.getconn()

def release_pg_conn(conn):
    """Return a connection to the pool."""
    pg_pool.putconn(conn)


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,  
)