"""
Configuration for TimescaleDB connection.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from src.logging.logger import ContextualLogger

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "timescaledb")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

_engine = None


def get_connection_string() -> str:
    """
    Get the database connection string from environment variables.

    Returns:
        str: The database connection string.
    """
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    """
    Get or create the SQLAlchemy engine with proper configuration.

    Returns:
        Engine: The SQLAlchemy engine instance.
    """
    global _engine

    if _engine is None:
        connection_string = get_connection_string()

        ContextualLogger.info(f"Creating database engine with connection string")

        _engine = create_engine(
            connection_string,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_timeout=DB_POOL_TIMEOUT,
            pool_pre_ping=True,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        )

    return _engine


def get_session_maker():
    """
    Create a session factory for database sessions.

    Returns:
        function: A function that creates new Session instances.
    """
    engine = get_engine()
    # SQLModel usa Session directamente en lugar de sessionmaker
    return lambda: Session(engine, autocommit=False, autoflush=False)


@contextmanager
def get_db_session() -> Generator:
    """
    Context manager for database sessions.

    Yields:
        Session: A database session.

    Raises:
        Exception: Any exception that occurs during session usage.
    """
    session_maker = get_session_maker()
    session = session_maker()

    try:
        ContextualLogger.debug("Opening new database session")
        yield session
        session.commit()
        ContextualLogger.debug("Session committed")
    except Exception as e:
        ContextualLogger.error(f"Session rollback due to error: {str(e)}")
        session.rollback()
        raise
    finally:
        ContextualLogger.debug("Closing database session")
        session.close()
