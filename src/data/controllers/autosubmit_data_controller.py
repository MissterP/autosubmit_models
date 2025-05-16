"""
Controller for accessing and manipulating Autosubmit data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import not_, select

from src.config.autosubmit_sqlite import get_autosubmit_db_session
from src.data.models.sqlite.autosubmit_models import (ExperimentDB,
                                                      ExperimentDetailDB)

logger = logging.getLogger(__name__)


class AutosubmitDataController:
    """
    Controller for interacting with Autosubmit data.

    Provides methods for querying and manipulating data in the Autosubmit SQLite database.
    """

    def __init__(self):
        """Initialize the Autosubmit data controller."""
        self.invalid_model_values = ["NA", "Blabla", "blabla"]

    def _clean_model_name(self, model_name: str) -> str:
        """
        Clean the model name by removing trailing slashes and surrounding quotes.

        Args:
            model_name: The raw model name from the database.

        Returns:
            str: Cleaned model name.
        """
        # Remove trailing slashes if present
        model_name = model_name.rstrip("/")

        # Remove surrounding single quotes if present
        if model_name.startswith("'") and model_name.endswith("'"):
            model_name = model_name[1:-1]

        return model_name

    def get_all_experiments(self) -> List[ExperimentDetailDB]:
        """
        Get all valid experiments from Autosubmit database.

        Filters out experiments with invalid model values.

        Returns:
            List[ExperimentDetailDB]: List of valid experiment details.
        """
        with get_autosubmit_db_session() as session:
            stmt = select(ExperimentDetailDB).where(
                not_(ExperimentDetailDB.model.in_(self.invalid_model_values))
            )
            result = session.execute(stmt)
            experiments = result.scalars().all()

            # Clean model names
            for exp in experiments:
                exp.model = self._clean_model_name(exp.model)

            return experiments

    def get_experiment_by_id(self, experiment_id: str) -> Optional[ExperimentDetailDB]:
        """
        Get experiment by ID.

        Args:
            experiment_id: ID of the experiment to retrieve.

        Returns:
            Optional[ExperimentDetailDB]: The experiment if found, None otherwise.
        """
        with get_autosubmit_db_session() as session:
            return session.get(ExperimentDetailDB, experiment_id)

    def get_experiments_by_model(self, model_name: str) -> List[ExperimentDetailDB]:
        """
        Get all experiments for a specific model.

        Args:
            model_name: Name of the model to filter by.

        Returns:
            List[ExperimentDetailDB]: List of experiments using the specified model.
        """
        # Clean the input model name for consistency in the query
        clean_model_name = self._clean_model_name(model_name)

        with get_autosubmit_db_session() as session:
            stmt = select(ExperimentDetailDB).where(
                ExperimentDetailDB.model == clean_model_name
            )
            result = session.execute(stmt)
            experiments = result.scalars().all()

            # Clean model names for returned experiments
            for exp in experiments:
                exp.model = self._clean_model_name(exp.model)

            return experiments

    def get_experiment_runs(self, experiment_id: str) -> List[ExperimentDB]:
        """
        Get all runs for a specific experiment.

        Args:
            experiment_id: ID of the experiment.

        Returns:
            List[ExperimentDB]: List of experiment runs.
        """
        with get_autosubmit_db_session() as session:
            stmt = select(ExperimentDB).where(
                ExperimentDB.experiment_id == experiment_id
            )
            result = session.execute(stmt)
            return result.scalars().all()

    def get_model_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all models.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of model statistics.
        """
        experiments = self.get_all_experiments()
        model_stats = {}

        for exp in experiments:
            model_name = exp.model

            if model_name not in model_stats:
                model_stats[model_name] = {"count": 0, "latest_experiment_date": None}

            # Increment count
            model_stats[model_name]["count"] += 1

            # Update latest experiment date if needed
            latest_date = model_stats[model_name]["latest_experiment_date"]
            if latest_date is None or exp.created_time > latest_date:
                model_stats[model_name]["latest_experiment_date"] = exp.created_time

        return model_stats
