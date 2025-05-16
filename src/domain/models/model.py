"""
Model domain class.
"""

from datetime import date
from typing import TYPE_CHECKING, Dict, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.domain.models.experiment import Experiment


class Model(BaseModel):
    """
    Domain model representing a climate model and its popularity metrics.

    This class encapsulates the business logic for climate models and their usage patterns.
    """

    name: str = Field(..., primary_key=True, description="Name of the climate model")
    count: int = Field(
        ..., description="Total number of experiments using this model", ge=0
    )
    experiments: List["Experiment"] = Field(
        ..., description="List of Experiment domain instances using this model"
    )
    last_extracted: date = Field(
        ..., description="Date when this model data was last extracted"
    )

    @classmethod
    def from_db(cls, name, experiments, last_extracted) -> "Model":
        """
        Create a domain model from database model.

        Args:
            db_model: Database model with basic model information
            experiments: List of Experiment domain instances using this model
            last_extracted: Date of last data extraction

        Returns:
            Model: Domain model instance
        """
        return cls(
            name=name,
            count=sum(len(experiments) for experiments in experiments.values()),
            experiments=experiments,
            last_extracted=last_extracted,
        )

    def get_name(self) -> str:
        """
        Get the name of the model.

        Returns:
            str: Name of the model
        """
        return self.name

    def get_count(self) -> int:
        """
        Get the total count of experiments using this model.

        Returns:
            int: Total count of experiments
        """
        return self.count

    def get_experiments(self) -> Dict[str, List[str]]:
        """
        Get tthe list of experiments using this model.

        Returns:

        """
        return self.experiments

    def get_last_extracted(self) -> date:
        """
        Get the date when this model data was last extracted.

        Returns:
            date: Date of last extraction
        """
        return self.last_extracted
