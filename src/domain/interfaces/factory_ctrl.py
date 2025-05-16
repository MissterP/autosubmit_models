from typing import Any, Optional

from src.data.controllers.popular_models_ctrl_db import PopularModelsCtrlDB


class FactoryCtrl:
    """Singleton factory for controllers."""

    _instance: Optional["FactoryCtrl"] = None

    @classmethod
    def get_instance(cls) -> "FactoryCtrl":
        """
        Get or create the singleton instance of FactoryCtrl.

        This method implements the lazy initialization pattern, creating the
        instance only when first requested.

        Returns:
            FactoryCtrl: The singleton instance of the factory.
        """
        if cls._instance is None:
            cls._instance = FactoryCtrl()
        return cls._instance

    def get_popular_models_controller(self) -> Any:
        """
        Get controller for popular models operations.

        This controller handles data access and manipulation for model popularity
        metrics, including retrieving ranked models and filtering by various criteria.

        Returns:
            Controller instance with methods for accessing and manipulating
            popular models data.
        """
        return PopularModelsCtrlDB()
