"""
Database initialization module.
This module orchestrates the initialization of all database components.
"""

from src.config.timescaledb import get_engine
from src.data.db_init.experiment_init import initialize_experiment_table
from src.data.db_init.materialized_views import \
    create_popular_models_materialized_view
from src.data.db_init.model_popularity_init import \
    initialize_model_popularity_table
from src.logging import ContextualLogger


def initialize_database():
    """
    Initialize all database components.

    This function orchestrates the initialization of all database tables
    and materialized views in the correct order.

    Returns:
        bool: True if initialization was successful

    Raises:
        Exception: If any initialization step fails
    """

    ContextualLogger.info("Starting database initialization")

    # Initialize the model popularity table first since experiment table has a foreign key to it
    initialize_model_popularity_table()
    initialize_experiment_table()

    create_popular_models_materialized_view()

    ContextualLogger.info("Database initialization completed successfully")
