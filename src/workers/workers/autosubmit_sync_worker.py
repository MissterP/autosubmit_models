"""
Worker to synchronize data between Autosubmit SQLite database and TimescaleDB.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple

from sqlalchemy import func
from sqlmodel import not_, select

from src.config.autosubmit_sqlite import (AUTOSUBMIT_SYNC_INTERVAL,
                                          get_autosubmit_db_session)
from src.config.timescaledb import get_db_session
from src.data.db_init.materialized_views import refresh_materialized_views
from src.data.models.sqlite.autosubmit_models import ExperimentDetailDB
from src.data.models.timescaledb.experiment_time_db import ExperimentTimeDB
from src.data.models.timescaledb.model_popularity_time_db import \
    ModelPopularityTimeDB
from src.logging.logger import ContextualLogger
from src.workers.base_worker import BaseWorker


class AutosubmitSyncWorker(BaseWorker):
    """
    Worker that synchronizes data from Autosubmit SQLite database to TimescaleDB.

    This worker extracts experiment and model data from Autosubmit SQLite database
    and updates the corresponding records in TimescaleDB at specified intervals.
    """

    def __init__(self, current_time: datetime = None):
        """
        Initialize the Autosubmit synchronization worker with the interval from environment variable.
        """
        interval_seconds = AUTOSUBMIT_SYNC_INTERVAL
        super().__init__(interval_seconds)
        self.invalid_model_values = ["NA", "Blabla", "blabla"]
        self._experiment_names = {}
        if current_time is None:
            self.current_time = datetime.now()
        else:
            self.current_time = current_time

    def _clean_model_name(self, model_name: str) -> str:
        """
        Clean the model name by removing trailing slashes and surrounding quotes.

        Args:
            model_name: The raw model name from the database.

        Returns:
            str: Cleaned model name.
        """
        if not model_name:
            return model_name

        # Remove trailing slashes if present
        model_name = model_name.rstrip("/")

        # Remove surrounding single quotes if present
        if model_name.startswith("'") and model_name.endswith("'"):
            model_name = model_name[1:-1]

        return model_name

    async def execute_task(self):
        """
        Execute the synchronization task between Autosubmit SQLite and TimescaleDB.

        This method retrieves data from the Autosubmit SQLite database and
        updates corresponding records in TimescaleDB.
        """
        ContextualLogger.info(
            "Starting synchronization of Autosubmit data to TimescaleDB"
        )

        current_time = self.current_time

        try:
            # Extraer y procesar experimentos
            experiments = self._extract_autosubmit_experiments()

            if not experiments:
                ContextualLogger.info(
                    "No valid experiments found in Autosubmit database"
                )
                return

            models_data = self._process_experiments(experiments)

            # Actualizar datos en TimescaleDB con manejo de fallos
            try:
                self._update_timescaledb(models_data, current_time)
            except Exception as db_err:
                ContextualLogger.error(f"Error during database update: {str(db_err)}")
                # Incluso si falla la actualización, permitir que la API siga funcionando
                # No re-lanzar la excepción para evitar que el worker se detenga completamente

            refresh_materialized_views()

            ContextualLogger.info(
                f"Successfully synchronized {len(experiments)} experiments and {len(models_data)} model-date combinations"
            )

        except Exception as e:
            ContextualLogger.error(
                f"Error during Autosubmit data synchronization: {str(e)}", exc_info=True
            )
            raise

    def _extract_autosubmit_experiments(self) -> List[dict]:
        """
        Extract experiment data from Autosubmit SQLite database.

        Returns:
            List[dict]: List of experiment data dictionaries instead of model objects
            to avoid modifying read-only database records.
        """
        ContextualLogger.debug("Extracting experiment data from Autosubmit database")

        with get_autosubmit_db_session() as session:
            from sqlmodel import join, select

            from src.data.models.sqlite.autosubmit_models import ExperimentDB

            query = (
                select(ExperimentDetailDB, ExperimentDB.name)
                .join(ExperimentDB, ExperimentDetailDB.exp_id == ExperimentDB.id)
                .where(not_(ExperimentDetailDB.model.in_(self.invalid_model_values)))
            )

            result = session.execute(query)
            experiments = []
            self._experiment_names = {}

            for row in result:
                detail = row[0]
                exp_name = row[1]

                clean_model = self._clean_model_name(detail.model)

                exp_data = {
                    "exp_id": detail.exp_id,
                    "user": detail.user,
                    "model": clean_model,
                    "branch": detail.branch,
                    "hpc": detail.hpc,
                    "credated": detail.credated,
                    "name": exp_name,
                }

                experiments.append(exp_data)

            ContextualLogger.info(
                f"Extracted {len(experiments)} valid experiments from Autosubmit database"
            )
            return experiments

    def _process_experiments(
        self, experiments: List[dict]
    ) -> Dict[tuple, Dict[str, Any]]:
        """
        Process and organize experiment data by model and creation date (year, month, day).

        Args:
            experiments: List of experiment data dictionaries.

        Returns:
            Dict[tuple, Dict[str, Any]]: Processed data organized by date and model.
        """
        ContextualLogger.debug("Processing experiment data")

        models_data = {}

        for exp in experiments:
            model_name = exp["model"]
            creation_date = exp["credated"].replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            key = (creation_date, model_name)

            if key not in models_data:
                models_data[key] = {
                    "model": model_name,
                    "time": creation_date,
                    "count": 0,
                    "experiments": [],
                }

            models_data[key]["experiments"].append(
                {
                    "id": exp["exp_id"],
                    "name": exp["name"],
                    "created_time": exp["credated"],
                }
            )

            models_data[key]["count"] += 1

        return models_data

    def _update_timescaledb(
        self,
        models_data: Dict[Tuple[datetime, str], Dict[str, Any]],
        current_time: datetime,
    ):
        """
        Update TimescaleDB with processed experiment and model data.

        Args:
            models_data: Processed data organized by date and model.
            current_time: Current timestamp for this synchronization.
        """
        ContextualLogger.debug("Updating TimescaleDB with processed data")

        with get_db_session() as session:
            existing_experiments_query = select(ExperimentTimeDB.id)
            existing_experiment_ids = {
                row[0] for row in session.execute(existing_experiments_query)
            }

            # Consulta para obtener entradas existentes de popularidad de modelos por fecha
            existing_popularity_query = select(
                ModelPopularityTimeDB.time, ModelPopularityTimeDB.model
            )
            existing_popularity_entries = {
                (row[0], row[1]) for row in session.execute(existing_popularity_query)
            }

            models_historical_count = {}
            new_model_popularity_entries = []

            for (date_key, model_name), model_info in models_data.items():

                new_experiments = [
                    exp
                    for exp in model_info["experiments"]
                    if exp["id"] not in existing_experiment_ids
                ]

                new_exp_count = len(new_experiments)
                if new_exp_count == 0:
                    ContextualLogger.debug(
                        f"All experiments for {model_name} on {date_key} already exist in TimescaleDB"
                    )
                    continue

                if model_name not in models_historical_count:
                    latest_record_query = (
                        select(ModelPopularityTimeDB)
                        .where(ModelPopularityTimeDB.model == model_name)
                        .order_by(ModelPopularityTimeDB.extracted_time.desc())
                    )

                    latest_record_result = session.execute(latest_record_query).first()

                    if latest_record_result:
                        latest_record = latest_record_result[0]
                        models_historical_count[model_name] = latest_record.total_count
                    else:
                        historical_sum_query = (
                            select(
                                ModelPopularityTimeDB.model,
                                func.sum(ModelPopularityTimeDB.count).label("total"),
                            )
                            .where(ModelPopularityTimeDB.model == model_name)
                            .group_by(ModelPopularityTimeDB.model)
                        )

                        result = session.execute(historical_sum_query).first()
                        models_historical_count[model_name] = result[1] if result else 0

                total_count = models_historical_count[model_name] + new_exp_count
                models_historical_count[model_name] = total_count

                model_popularity_key = (date_key, model_name)
                if model_popularity_key not in existing_popularity_entries:
                    new_model_popularity_entries.append(
                        {
                            "time": date_key,
                            "model": model_name,
                            "count": new_exp_count,
                            "total_count": total_count,
                            "extracted_time": current_time,
                        }
                    )

                if new_experiments:
                    ContextualLogger.debug(
                        f"Adding {len(new_experiments)} new experiments for model {model_name}"
                    )
                    batch_size = 100
                    for i in range(0, len(new_experiments), batch_size):
                        batch = new_experiments[i : i + batch_size]
                        from sqlalchemy.dialects.postgresql import insert

                        # Crear valores para inserción masiva
                        values = [
                            {
                                "id": exp_data["id"],
                                "name": exp_data["name"],
                                "model": model_name,
                                "created_time": exp_data["created_time"],
                            }
                            for exp_data in batch
                        ]

                        # Usar insert con on_conflict_do_nothing para evitar duplicados
                        insert_stmt = insert(ExperimentTimeDB).values(values)
                        insert_stmt = insert_stmt.on_conflict_do_nothing(
                            index_elements=["id"]
                        )

                        # Ejecutar la inserción masiva
                        session.execute(insert_stmt)

                        # Actualizar el conjunto de IDs existentes
                        for exp_data in batch:
                            existing_experiment_ids.add(exp_data["id"])

            # Insertar entradas de popularidad de modelos en lotes
            if new_model_popularity_entries:
                ContextualLogger.debug(
                    f"Adding {len(new_model_popularity_entries)} new model popularity entries"
                )
                # Procesar entradas de popularidad de modelos en lotes
                batch_size = 100
                from sqlalchemy.dialects.postgresql import insert

                for i in range(0, len(new_model_popularity_entries), batch_size):
                    batch = new_model_popularity_entries[i : i + batch_size]

                    # Usar insert con on_conflict_do_nothing para evitar actualizar entradas históricas
                    insert_stmt = insert(ModelPopularityTimeDB).values(batch)
                    insert_stmt = insert_stmt.on_conflict_do_nothing(
                        index_elements=["time", "model"]
                    )

                    # Ejecutar la inserción masiva
                    session.execute(insert_stmt)

            try:
                # Usar flush primero para detectar errores antes de commit
                session.flush()

                # Si flush exitoso, hacer commit
                session.commit()

                # Refrescar vistas materializadas después de una actualización exitosa
                try:
                    refresh_materialized_views()
                    ContextualLogger.info("Successfully refreshed materialized views")
                except Exception as view_err:
                    # No fallar el proceso completo si solo falla la actualización de vistas
                    ContextualLogger.warning(
                        f"Failed to refresh materialized views: {str(view_err)}"
                    )

                ContextualLogger.info(
                    f"Successfully updated {len(models_data)} model-date combinations in TimescaleDB"
                )
            except Exception as e:
                ContextualLogger.error(
                    f"Error committing changes to database: {str(e)}"
                )
                session.rollback()
                raise
