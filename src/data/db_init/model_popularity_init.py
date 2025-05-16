"""
Initialization of the model popularity metrics table.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, text

from src.config.timescaledb import get_db_session, get_engine
from src.data.models.timescaledb.model_popularity_time_db import \
    ModelPopularityTimeDB
from src.exceptions.exceptions import DatabaseException
from src.logging import ContextualLogger


def initialize_model_popularity_table():
    """
    Initialize the model popularity metrics table with TimescaleDB features.

    This function:
    1. Creates the table if it doesn't exist
    2. Converts it to a TimescaleDB hypertable
    3. Sets up compression policies
    4. Creates necessary indexes

    Returns:
        bool: True if initialization was successful.

    Raises:
        DatabaseException: If there's an error during initialization.
        Exception: For any unexpected errors.
    """
    try:
        ContextualLogger.info("Initializing model popularity metrics table")

        engine = get_engine()
        SQLModel.metadata.create_all(engine, tables=[ModelPopularityTimeDB.__table__])

        with get_db_session() as session:
            try:
                session.execute(
                    text(
                        """
                    SELECT create_hypertable('metric_models_popularity', 'time',
                                            if_not_exists => TRUE,
                                            create_default_indexes => FALSE,
                                            chunk_time_interval => INTERVAL '7 days');
                    """
                    )
                )

                ContextualLogger.info("Created hypertable for model popularity metrics")

            except Exception as hyper_err:
                ContextualLogger.error(f"Could not create hypertable")
                raise DatabaseException(
                    "Failed to create hypertable for model popularity metrics",
                    {"error": str(hyper_err)},
                )

            try:
                session.execute(
                    text(
                        """
                    ALTER TABLE metric_models_popularity SET (
                        timescaledb.compress,
                        timescaledb.compress_orderby = 'time DESC, extracted_time DESC'
                    );
                    """
                    )
                )

                ContextualLogger.info(
                    "Configured compression for model popularity metrics"
                )
            except Exception as comp_err:
                ContextualLogger.error(f"Could not configure compression")
                raise DatabaseException(
                    "Failed to configure compression for model popularity metrics",
                    {"error": str(comp_err)},
                )

            try:
                session.execute(
                    text(
                        """
                    SELECT add_compression_policy('metric_models_popularity', 
                                                INTERVAL '7 days', 
                                                if_not_exists => TRUE);
                    """
                    )
                )

                ContextualLogger.info(
                    "Added compression policy for model popularity metrics"
                )
            except Exception as policy_err:
                ContextualLogger.error(f"Could not add compression policy")
                raise DatabaseException(
                    "Failed to add compression policy for model popularity metrics",
                    {"error": str(policy_err)},
                )

            _create_additional_indexes(session)

        ContextualLogger.info("Model popularity metrics table initialized successfully")
        return True

    except SQLAlchemyError as e:
        ContextualLogger.error(
            f"SQLAlchemy error initializing model popularity table: {str(e)}"
        )
        raise DatabaseException(
            "Failed to initialize model popularity table", {"error": str(e)}
        )
    except Exception as e:
        ContextualLogger.error(
            f"Unexpected error initializing model popularity table: {str(e)}"
        )
        raise DatabaseException(
            "Failed to initialize model popularity table due to unexpected error",
            {"error": str(e)},
        )


def _create_additional_indexes(session):
    """
    Create additional indexes for the model popularity table.

    Args:
        session: SQLAlchemy session
    """
    try:
        session.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_models_popularity_time
            ON metric_models_popularity (time DESC);
            """
            )
        )

        session.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_models_popularity_extracted_time
            ON metric_models_popularity (extracted_time DESC);
            """
            )
        )

        session.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_models_popularity_time_brin
            ON metric_models_popularity USING BRIN (time);
            """
            )
        )

        ContextualLogger.info(
            "Created all additional indexes for model popularity metrics"
        )
    except SQLAlchemyError as e:
        ContextualLogger.error(f"Error creating additional indexes: {str(e)}")
        raise DatabaseException(
            "Failed to create additional indexes for model popularity table",
            {"error": str(e)},
        )
    except Exception as e:
        ContextualLogger.error(
            f"Unexpected error creating additional indexes: {str(e)}"
        )
        raise DatabaseException(
            "Failed to create additional indexes for model popularity table due to unexpected error",
            {"error": str(e)},
        )
