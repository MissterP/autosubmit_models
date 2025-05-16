"""
Experiment domain class.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.domain.models.model import Model


class Experiment(BaseModel):
    """
    Domain model representing a climate model experiment.

    This class encapsulates the business logic for climate experiments.
    """

    id: str = Field(
        ..., primary_key=True, description="Unique identifier for the experiment"
    )

    name: str = Field(..., unique=True, description="Name of the experiment")
    model: Optional["Model"] = Field(
        default=None, description="Reference to the associated model domain instance"
    )
    created_time: datetime = Field(..., description="When the experiment was created")

    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> "Experiment":
        """
        Create a domain model from database model.

        Args:
            data: Dict with basic experiment information

        Returns:
            Experiment: Domain model instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            model=data["model"],
            created_time=data["created_time"],
            model_instance=data["model_instance"],
        )

    def get_name(self) -> str:
        """
        Get the name of the experiment.

        Returns:
            str: Name of the experiment
        """
        return self.name


from src.domain.models.model import Model

Experiment.model_rebuild()
