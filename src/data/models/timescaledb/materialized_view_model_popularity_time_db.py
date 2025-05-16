"""
Model for the materialized view of popular models.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class PopularModelMaterializedViewTimeDB(SQLModel, table=True):
    """
    SQLModel representation of the mv_latest_popular_models materialized view.

    This model provides access to the aggregated data about popular models
    across different autosubmit versions.
    """

    __tablename__ = "mv_latest_popular_models"

    model: str = Field(primary_key=True, description="Name of the climate model")
    count: int = Field(description="Count of experiments for this model and version")
    last_updated: datetime = Field(
        description="When this model was last updated with a new experiment"
    )

    model_config = {
        "protected_namespaces": (),
        "from_attributes": True,  # Replaces deprecated orm_mode=True
    }
