"""
Materialized views for optimizing frequently used queries.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import text

from src.config.timescaledb import get_db_session
from src.exceptions.exceptions import DatabaseException
from src.logging import ContextualLogger


def create_popular_models_materialized_view():
    """
    Create a materialized view for aggregated models popularity data.

    This view aggregates data across all time periods and creates one row per model
    with the sum of all counts and the most recent extraction time.
    The primary key is model.

    Returns:
        bool: True if the view was created successfully.

    Raises:
        DatabaseException: If there's an error during creation.
        Exception: For any unexpected errors.
    """
    try:
        ContextualLogger.info(
            "Creating materialized view for aggregated models popularity data"
        )

        with get_db_session() as session:
            check_table_result = session.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'metric_models_popularity'
                );
            """
                )
            ).scalar()

            if not check_table_result:
                ContextualLogger.error(
                    "Table 'metric_models_popularity' doesn't exist yet. Skipping materialized view creation."
                )
                raise DatabaseException(
                    "Table 'metric_models_popularity' doesn't exist so materialized view creation is cannot be performed",
                )

        with get_db_session() as session:
            try:
                session.execute(
                    text(
                        """
                    DROP MATERIALIZED VIEW IF EXISTS mv_latest_popular_models CASCADE;
                    """
                    )
                )
                ContextualLogger.info("Dropped existing materialized view")
            except SQLAlchemyError as e:
                if "is not a materialized view" in str(e):
                    ContextualLogger.warning(
                        "Found a table named 'mv_latest_popular_models' instead of a materialized view. Dropping the table..."
                    )
                    session.execute(
                        text("DROP TABLE IF EXISTS mv_latest_popular_models CASCADE;")
                    )
                else:
                    raise

        with get_db_session() as session:
            session.execute(
                text(
                    """
                CREATE MATERIALIZED VIEW mv_latest_popular_models AS
                WITH latest_updates AS (
                    SELECT 
                        model,
                        MAX(time) as latest_time
                    FROM metric_models_popularity
                    GROUP BY model
                ),
                latest_records AS (
                    SELECT 
                        mp.model,
                        mp.time,
                        mp.total_count,
                        mp.extracted_time,
                        ROW_NUMBER() OVER(PARTITION BY mp.model ORDER BY mp.extracted_time DESC) as rn
                    FROM metric_models_popularity mp
                    JOIN latest_updates lu ON mp.model = lu.model AND mp.time = lu.latest_time
                )
                SELECT 
                    mp.model,
                    SUM(mp.count) as count,
                    (
                        SELECT lr.total_count
                        FROM latest_records lr
                        WHERE lr.model = mp.model AND lr.rn = 1
                    ) as total_count,
                    MAX(mp.extracted_time) as last_updated
                FROM metric_models_popularity mp
                GROUP BY mp.model
                WITH NO DATA;
                """
                )
            )

            ContextualLogger.info("Created materialized view structure")

            session.execute(
                text(
                    """
                CREATE INDEX idx_mv_latest_models_count ON mv_latest_popular_models (count DESC);
                """
                )
            )

            session.execute(
                text(
                    """
                CREATE INDEX idx_mv_latest_models_name ON mv_latest_popular_models (model);
                """
                )
            )

            # Create or ensure index exists on original table for faster materialized view generation
            session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_model_time_extracted_time 
                ON metric_models_popularity (model, time DESC, extracted_time DESC);
                """
                )
            )

            ContextualLogger.info(
                "Created indexes on materialized view and metric_models_popularity table"
            )

        ContextualLogger.info("Materialized view for aggregated models data created")
        return True

    except SQLAlchemyError as e:
        raise DatabaseException("Failed to create materialized view", {"error": str(e)})
    except Exception as e:
        raise DatabaseException(
            "Failed to create materialized view due to unexpected error",
            {"error": str(e)},
        )


def refresh_materialized_views():
    """
    Refresh all materialized views to ensure they contain the latest data.

    This function should be called after data updates to ensure views reflect current data.

    Returns:
        bool: True if refresh was successful

    Raises:
        DatabaseException: If there's an error during refresh
    """
    try:
        ContextualLogger.info("Refreshing materialized views")

        with get_db_session() as session:
            check_query = text(
                """
                SELECT COUNT(*) 
                FROM pg_catalog.pg_matviews 
                WHERE matviewname = 'mv_latest_popular_models'
            """
            )

            result = session.execute(check_query)
            view_exists = result.scalar() > 0

            if not view_exists:
                ContextualLogger.info(
                    "Materialized view 'mv_latest_popular_models' does not exist, creating it now"
                )
                create_popular_models_materialized_view()

            session.execute(text("REFRESH MATERIALIZED VIEW mv_latest_popular_models;"))

        ContextualLogger.info("Materialized views refreshed successfully")

    except SQLAlchemyError as e:
        ContextualLogger.error(
            f"Failed to refresh materialized views.", extra={"error": str(e)}
        )
        raise DatabaseException(
            "Failed to refresh materialized views", {"error": str(e)}
        )
    except Exception as e:
        ContextualLogger.error(
            f"Failed to refresh materialized views due to unexpected error.",
            extra={"error": str(e)},
        )
        raise
