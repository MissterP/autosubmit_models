from datetime import date

from pydantic import BaseModel, Field

from src.api.schemas.popular_models.popular_model_response import \
    PopularModelResponse
from src.domain.models.model import Model


class AggregatedPopularModelsResponse(BaseModel):
    """Schema for aggregated popular models response.

    This class represents a collection of climate models with their aggregated
    historical data summed, providing a comprehensive
    view of accumulated climate patterns across all models.
    """

    last_extracted: date = Field(..., description="Timestamp of the last extraction")

    models: list[PopularModelResponse] = Field(
        ..., description="List of the aggregated popular models"
    )

    @classmethod
    def initialize(cls, models: list[Model]) -> "AggregatedPopularModelsResponse":
        """Initialize the response with the last extraction date and models."""
        return cls(
            last_extracted=models[0].get_last_extracted(),
            models=[
                PopularModelResponse.from_domain(domain_model)
                for domain_model in models
            ],
        )
