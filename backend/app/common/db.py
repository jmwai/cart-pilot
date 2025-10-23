import psycopg2
from psycopg2.pool import SimpleConnectionPool
from typing import Optional


from .config import get_settings

_pool: Optional[SimpleConnectionPool] = None

def get_conn() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = SimpleConnectionPool(
            minconn=1, 
            maxconn=10, 
            host=settings.DB_HOST, 
            port=settings.DB_PORT, 
            dbname=settings.DB_NAME, 
            user=settings.DB_USER, 
            password=settings.DB_PASSWORD)
    return _pool.getconn()

def put_conn(conn) -> None:
    if _pool is not None:
        _pool.putconn(conn)


def health_check() -> bool:
    conn = get_conn()
    try:
        conn.cursor().execute("SELECT 1")
        return True
    except Exception as e:
        return False