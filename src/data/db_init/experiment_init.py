"""
Initialization of the experiment table.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, text

from src.config.timescaledb import get_db_session, get_engine
from src.data.models.timescaledb.experiment_time_db import ExperimentTimeDB
from src.exceptions.exceptions import DatabaseException
from src.logging import ContextualLogger


def initialize_experiment_table():
    """
    Initialize the experiment table with proper indexes.

    This function:
    1. Creates the experiment table if it doesn't exist.
    2. Creates necessary indexes for common query patterns.

    Returns:
        bool: True if initialization was successful.

    Raises:
        DatabaseException: If there's an error during initialization.
        Exception: For any unexpected errors.
    """
    try:
        ContextualLogger.info("Initializing experiment table...")

        engine = get_engine()
        SQLModel.metadata.create_all(engine, tables=[ExperimentTimeDB.__table__])

        with get_db_session() as session:
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_exp_created_time
                ON experiments (created_time DESC);
                """
                )
            )

            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_exp_model_created_time
                ON experiments (model, created_time DESC);
                """
                )
            )

        ContextualLogger.info("ExperimentTimeDB table initialized successfully")
        return True

    except SQLAlchemyError as e:
        ContextualLogger.error(
            f"Failed to initialize experiment table.", extra={"error": str(e)}
        )
        raise DatabaseException(
            "Failed to initialize experiment table", {"error": str(e)}
        )
    except Exception as e:
        ContextualLogger.error(
            f"Failed to initialize experiment table due to unexpected error.",
            extra={"error": str(e)},
        )
        raise
