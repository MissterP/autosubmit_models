"""
Configuration for Autosubmit SQLite connection.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from src.logging.logger import ContextualLogger

AUTOSUBMIT_DB_PATH = os.getenv("AUTOSUBMIT_MAIN_DB_PATH")
AUTOSUBMIT_SYNC_INTERVAL = int(os.getenv("AUTOSUBMIT_SYNC_INTERVAL", "3600"))

_autosubmit_engine = None


def get_autosubmit_connection_string() -> str:
    """
    Get the Autosubmit database connection string from environment variables.

    Returns:
        str: The database connection string.
    """
    return AUTOSUBMIT_DB_PATH


def get_autosubmit_engine():
    """
    Get or create the SQLAlchemy engine for Autosubmit SQLite database.

    Returns:
        Engine: The SQLAlchemy engine instance.
    """
    global _autosubmit_engine

    if _autosubmit_engine is None:
        connection_string = get_autosubmit_connection_string()

        ContextualLogger.info(f"Creating Autosubmit SQLite database engine")

        _autosubmit_engine = create_engine(
            connection_string,
            connect_args={"check_same_thread": False},
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        )

    return _autosubmit_engine


def get_autosubmit_session_maker():
    """
    Create a session factory for Autosubmit database sessions.

    Returns:
        function: A function that creates new Session instances.
    """
    engine = get_autosubmit_engine()
    return lambda: Session(engine, autocommit=False, autoflush=False)


@contextmanager
def get_autosubmit_db_session() -> Generator:
    """
    Context manager for Autosubmit database sessions.

    Yields:
        Session: A database session in read-only mode.

    Raises:
        Exception: Any exception that occurs during session usage.
    """
    session_maker = get_autosubmit_session_maker()
    session = session_maker()

    # Configure session as read-only since we're connecting to a read-only database
    # This prevents SQLAlchemy from trying to flush changes to the database
    session.autoflush = False

    try:
        ContextualLogger.debug("Opening new Autosubmit database session (read-only)")
        yield session
        # No commit in read-only mode
    except Exception as e:
        ContextualLogger.error(f"Autosubmit session error: {str(e)}")
        # No rollback needed since we're in read-only mode
        raise
    finally:
        ContextualLogger.debug("Closing Autosubmit database session")
        session.close()
