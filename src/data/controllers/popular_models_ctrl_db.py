"""
Implementation of the popular models controller for database operations.
"""

from datetime import date
from typing import List

from sqlmodel import desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.async_timescaledb import get_async_db_session
from src.data.models.timescaledb.experiment_time_db import ExperimentTimeDB
from src.data.models.timescaledb.materialized_view_model_popularity_time_db import \
    PopularModelMaterializedViewTimeDB
from src.domain.interfaces.popular_models_ctrl import PopularModelsCtrl
from src.domain.models.experiment import Experiment
from src.domain.models.model import Model


class PopularModelsCtrlDB(PopularModelsCtrl):
    """
    Implementation of PopularModelsCtrl interface for database operations.

    This class provides concrete implementations for fetching popular models data
    from the database and transforming it into domain models.
    """

    async def get_aggregated_popular_models(self) -> List[Model]:
        """
        Get popular models aggregated across versions based on the specified criteria.

        Returns:
            List[Model]: List of popular models matching the criteria.
        """
        async with get_async_db_session() as session:
            extraction_date_query = select(
                func.max(PopularModelMaterializedViewTimeDB.last_updated)
            )
            result = None
            try:
                result = await session.execute(extraction_date_query)
            except Exception:
                raise
            last_updated_date = result.scalar_one_or_none()

            last_updated = (
                last_updated_date.date() if last_updated_date else date.today()
            )

            models_data = await self._get_all_models(session)

            domain_models = []
            for model_name, total_count in models_data:
                experiments = await self._get_experiments(
                    session,
                    model_name,
                )

                domain_model = Model(
                    name=model_name,
                    count=total_count,
                    experiments=experiments,
                    last_extracted=last_updated,
                )

                domain_models.append(domain_model)

            return domain_models

    async def _get_all_models(
        self,
        session: AsyncSession,
    ) -> List[tuple]:
        """
        Get all models aggregated across all versions.

        Args:
            session: Database session
            limit: Optional maximum number of results

        Returns:
            List[tuple]: List of (model_name, total_count) tuples
        """
        query = (
            select(
                PopularModelMaterializedViewTimeDB.model,
                func.sum(PopularModelMaterializedViewTimeDB.count).label("total_count"),
            )
            .group_by(PopularModelMaterializedViewTimeDB.model)
            .order_by(desc("total_count"))
        )

        result = None
        try:
            result = await session.execute(query)
        except Exception:
            raise
        return result.all()

    async def _get_experiments(
        self,
        session: AsyncSession,
        model_name: str,
    ) -> List[Experiment]:
        """
        Get all experiments for a model.

        Args:
            session: Database session
            model_name: Name of the model to get experiments for

        Returns:
            List[Experiment]: List of experiments
        """
        base_query = select(ExperimentTimeDB).where(
            ExperimentTimeDB.model == model_name
        )

        db_experiments = []

        try:
            result = await session.execute(base_query)
            db_experiments = result.scalars().all()
        except Exception:
            raise

        experiments = []
        for db_exp in db_experiments:

            domain_exp = Experiment(
                id=db_exp.id, name=db_exp.name, created_time=db_exp.created_time
            )

            experiments.append(domain_exp)

        return experiments
