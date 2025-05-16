"""
Functions to initialize the Autosubmit SQLite database schema.
"""

from sqlmodel import SQLModel

from src.config.autosubmit_sqlite import get_autosubmit_engine
from src.data.models.sqlite.autosubmit_models import (ExperimentDB,
                                                      ExperimentDetailDB)
from src.logging.logger import ContextualLogger


def init_autosubmit_db():
    """
    Initialize the Autosubmit SQLite database schema.

    Creates all tables if they do not exist.
    """
    ContextualLogger.info("Initializing Autosubmit SQLite database schema")

    engine = get_autosubmit_engine()
    SQLModel.metadata.create_all(engine)

    ContextualLogger.info("Autosubmit SQLite database schema initialized successfully")
