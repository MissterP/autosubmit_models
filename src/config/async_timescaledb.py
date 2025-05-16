"""
Configuration for async TimescaleDB connection.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from src.logging.logger import ContextualLogger

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "timescaledb")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

_async_engine = None
_async_session_maker = None


def get_async_connection_string() -> str:
    """
    Get the async database connection string from environment variables.

    Returns:
        str: The async database connection string.
    """
    return f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_async_engine():
    """
    Get or create the async SQLAlchemy engine with proper configuration.

    Returns:
        AsyncEngine: The SQLAlchemy async engine instance.
    """
    global _async_engine

    if _async_engine is None:
        connection_string = get_async_connection_string()

        ContextualLogger.info(f"Creating async database engine")

        _async_engine = create_async_engine(
            connection_string,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_timeout=DB_POOL_TIMEOUT,
            pool_pre_ping=True,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        )

    return _async_engine


def get_async_session_maker():
    """
    Create an async sessionmaker for database sessions.

    Returns:
        async_sessionmaker: A configured async sessionmaker instance.
    """
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_async_engine()
        _async_session_maker = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )

    return _async_session_maker


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Yields:
        AsyncSession: An async database session.

    Raises:
        Exception: Any exception that occurs during session usage.
    """
    session_maker = get_async_session_maker()
    session = session_maker()

    try:
        ContextualLogger.debug("Opening new async database session")
        yield session
        await session.commit()
        ContextualLogger.debug("Async session committed")
    except Exception as e:
        ContextualLogger.error(f"Async session rollback due to error: {str(e)}")
        await session.rollback()
        raise
    finally:
        ContextualLogger.debug("Closing async database session")
        await session.close()
