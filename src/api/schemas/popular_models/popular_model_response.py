from typing import List

from pydantic import BaseModel, Field

from src.domain.models.model import Model


class PopularModelResponse(BaseModel):
    """Schema for model response returned by the API."""

    name: str = Field(description="Name of the climate model")

    total_count: int = Field(description="Total number of experiments", ge=0)

    experiments: List[str] = Field(
        description="List of experiments names using this model"
    )

    @classmethod
    def from_domain(cls, domain_model: Model) -> "PopularModelResponse":
        """Create API response model from domain model."""

        return cls(
            name=domain_model.get_name(),
            total_count=domain_model.get_count(),
            experiments=[
                experiment.get_name() for experiment in domain_model.get_experiments()
            ],
        )
