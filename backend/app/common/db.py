"""
Database connection and session management using SQLAlchemy.
"""
from __future__ import annotations
import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .config import get_settings
from .models import Base

settings = get_settings()



_pool: Optional[SimpleConnectionPool] = None


IS_PRODUCTION = os.getenv('K_SERVICE') is not None

def get_conn() -> SimpleConnectionPool:
    """Creates a new connection pool for either local or prod."""
    global _pool
    if _pool is not None:
        return _pool.getconn()

    try:
        if IS_PRODUCTION:
            _pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=f"/cloudsql/{settings.CLOUD_SQL_CONNECTION_NAME}",
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )
        else:
            _pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=settings.DB_HOST,
                port=5432, 
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )
            
    except Exception as e:
        raise e

    return _pool.getconn()


def put_conn(conn) -> None:
    """Legacy function - kept for backward compatibility during migration"""
    if _pool is not None:
        _pool.putconn(conn)


# ============================================================================
# SQLAlchemy Engine and Session Management
# ============================================================================

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    Use with Depends(get_db) in route handlers.

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(CatalogItem).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for manual session management.
    Use this in agent tools for database operations.

    Example:
        with get_db_session() as db:
            product = db.query(CatalogItem).filter(CatalogItem.id == product_id).first()
            # Automatic commit on success, rollback on exception
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables from models"""
    Base.metadata.create_all(bind=engine)


def health_check() -> bool:
    """Health check for database connectivity (now using SQLAlchemy)"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False
