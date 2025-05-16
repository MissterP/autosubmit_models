"""
Service for syncing Autosubmit data with TimescaleDB.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import not_, select

from src.config.autosubmit_sqlite import get_autosubmit_db_session
from src.config.timescaledb import get_db_session
from src.data.models.sqlite.autosubmit_models import ExperimentDetailDB
from src.data.models.timescaledb.experiment_time_db import ExperimentTimeDB
from src.data.models.timescaledb.model_popularity_time_db import \
    ModelPopularityTimeDB

logger = logging.getLogger(__name__)


class AutosubmitSyncService:
    """
    Service for synchronizing data between Autosubmit SQLite and TimescaleDB.

    This service provides methods for extracting data from Autosubmit,
    processing it, and updating TimescaleDB records.
    """

    def __init__(self):
        """Initialize the AutosubmitSyncService."""
        self.invalid_model_values = ["NA", "Blabla", "blabla"]

    def sync_data(self):
        """
        Synchronize data from Autosubmit SQLite to TimescaleDB.

        This method orchestrates the full synchronization process.
        """
        logger.info("Starting data synchronization process")

        # Get current timestamp for this sync
        current_time = datetime.now()

        # Extract and process data
        experiments = self.extract_autosubmit_experiments()

        if not experiments:
            logger.info("No valid experiments to synchronize")
            return

        models_data = self.process_experiments(experiments)

        # Update TimescaleDB
        self.update_timescaledb_data(models_data, current_time)

        logger.info(
            f"Data synchronization completed: {len(experiments)} experiments, {len(models_data)} models"
        )

    def extract_autosubmit_experiments(self) -> List[ExperimentDetailDB]:
        """
        Extract experiment data from Autosubmit SQLite database.

        Returns:
            List[ExperimentDetailDB]: List of valid experiment details.
        """
        logger.debug("Extracting experiments from Autosubmit database")

        with get_autosubmit_db_session() as session:
            # Query experiments filtering out invalid model values and clean models directly in SQL
            stmt = select(
                ExperimentDetailDB.exp_id,
                ExperimentDetailDB.user,
                ExperimentDetailDB.name,
                # Apply SQL transformations to clean model names
                # Remove trailing slash and single quotes
                (
                    select("TRIM(REPLACE(REPLACE(model, '/', ''), \"'\", ''))")
                    .where(ExperimentDetailDB.model == ExperimentDetailDB.model)
                    .scalar_subquery()
                    .label("model")
                ),
                ExperimentDetailDB.credated,
                ExperimentDetailDB.branch,
                ExperimentDetailDB.hpc,
            ).where(not_(ExperimentDetailDB.model.in_(self.invalid_model_values)))
            result = session.execute(stmt)
            experiments = []

            for row in result:
                # Create ExperimentDetailDB objects from the query results
                detail = ExperimentDetailDB(
                    exp_id=row.exp_id,
                    user=row.user,
                    name=row.name,
                    model=row.model,  # Already cleaned by SQL
                    credated=row.credated,
                    branch=row.branch,
                    hpc=row.hpc,
                )
                experiments.append(detail)

            logger.info(f"Extracted {len(experiments)} valid experiments")
            return experiments

    def process_experiments(
        self, experiments: List[ExperimentDetailDB]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Process experiment data and organize it by model.

        Args:
            experiments: List of experiment details from Autosubmit.

        Returns:
            Dict[str, Dict[str, Any]]: Processed data organized by model.
        """
        logger.debug("Processing experiment data by model")

        models_data = {}

        for exp in experiments:
            model_name = exp.model

            if model_name not in models_data:
                models_data[model_name] = {
                    "model": model_name,
                    "count": 0,
                    "experiments": [],
                }

            # Add experiment to model data
            models_data[model_name]["experiments"].append(
                {"id": exp.exp_id, "name": exp.name, "created_time": exp.credated}
            )

            # Increment count
            models_data[model_name]["count"] += 1

        return models_data

    def update_timescaledb_data(
        self, models_data: Dict[str, Dict[str, Any]], current_time: datetime
    ):
        """
        Update TimescaleDB with processed data.

        Args:
            models_data: Processed data organized by model.
            current_time: Current timestamp for this sync operation.
        """
        logger.debug("Updating TimescaleDB with processed data")

        with get_db_session() as session:
            for model_name, model_info in models_data.items():
                # Create/update model popularity record
                model_popularity = ModelPopularityTimeDB(
                    time=current_time,
                    model=model_name,
                    count=model_info["count"],
                    extracted_time=current_time,
                )

                session.add(model_popularity)

                # Process experiments for this model
                for exp_data in model_info["experiments"]:
                    # Check if experiment already exists
                    existing_exp = session.exec(
                        select(ExperimentTimeDB).where(
                            ExperimentTimeDB.id == exp_data["id"]
                        )
                    ).first()

                    if not existing_exp:
                        # Create new experiment record
                        experiment = ExperimentTimeDB(
                            id=exp_data["id"],
                            name=exp_data["name"],
                            model=model_name,
                            created_time=exp_data["created_time"],
                        )
                        session.add(experiment)

            # Commit all changes
            session.commit()
