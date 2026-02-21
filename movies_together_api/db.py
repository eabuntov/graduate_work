import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/movies",
)


# -----------------------------------------------------------------------------
# Engine
# -----------------------------------------------------------------------------

engine: Engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,      # Detect stale connections
    pool_recycle=1800,       # Avoid idle disconnects
    future=True,
)


# -----------------------------------------------------------------------------
# Session Factory
# -----------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# -----------------------------------------------------------------------------
# Base Class
# -----------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------------------------
# Dependency
# -----------------------------------------------------------------------------

def get_db() -> Generator:
    """
    FastAPI dependency that provides a SQLAlchemy session.

    - Opens session
    - Commits if no exception
    - Rolls back on failure
    - Always closes
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