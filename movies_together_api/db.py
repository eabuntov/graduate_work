import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DATABASE_URL = f"postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@172.24.0.3:5432/{os.getenv("DB_NAME")}"


# -----------------------------------------------------------------------------
# Engine
# -----------------------------------------------------------------------------

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False
)


# -----------------------------------------------------------------------------
# Session Factory
# -----------------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
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

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async SQLAlchemy session.

    - Opens session
    - Commits if no exception
    - Rolls back on failure
    - Always closes
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise