from abc import ABC, abstractmethod
from typing import List

from src.domain.models.model import Model


class PopularModelsCtrl(ABC):
    """
    Interface for popular models controller.

    This interface defines the contract that any popular models
    controller implementation must fulfill.
    """

    @abstractmethod
    async def get_aggregated_popular_models(self) -> List[Model]:
        """
        Get popular models based on the specified criteria.

        Args:
            autosubmit_versions: Optional list of autosubmit versions to filter by
            limit: Optional maximum number of models to return

        Returns:
            List[Model]: List of popular models matching the criteria.
        """
        raise NotImplementedError(
            "The method get_popular_models from PopularModelsCtrl is not implemented."
        )
