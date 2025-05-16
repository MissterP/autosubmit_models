"""Transaction class for popular models."""

from typing import List, Optional

from src.domain.controllers.transaction import Transaction
from src.domain.interfaces.factory_ctrl import FactoryCtrl
from src.domain.models.model import Model
from src.exceptions.exceptions import DatabaseException
from src.logging import ContextualLogger


class TrPopularModelsAggregated(Transaction[List[Model]]):
    """Transaction class to get the aggegated popular models."""

    async def execute(self) -> List[Model]:
        """Execute the transaction.

        Returns:
            List[Model]: List of the aggregated popular models.

        Raises:
            DatabaseException: If there is an error while fetching the data from the database.
        """
        factory_ctrl = FactoryCtrl.get_instance()

        popular_models_ctrl = factory_ctrl.get_popular_models_controller()

        try:
            self.result = await popular_models_ctrl.get_aggregated_popular_models()
        except Exception as e:
            # Log the error before raising the exception
            error_message = (
                "Error while fetching aggregated popular models from the database"
            )
            context = {"error": str(e)}

            ContextualLogger.error(f"DatabaseException: {error_message}", extra=context)

            # Mark the exception as already logged to avoid duplicate logs
            raise DatabaseException(error_message, context=context, already_logged=True)
        return self.result
