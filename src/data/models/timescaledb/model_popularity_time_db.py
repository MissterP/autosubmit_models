"""
Model popularity time-series database model.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import foreign
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.data.models.timescaledb.experiment_time_db import ExperimentTimeDB


class ModelPopularityTimeDB(SQLModel, table=True):
    """
    TimescaleDB model for storing model popularity metrics over time.

    This model tracks the usage and popularity of climate models across different
    autosubmit versions over time.
    """

    __tablename__ = "metric_models_popularity"

    time: datetime = Field(
        primary_key=True,
        default_factory=datetime.now,
        description="Time of the data point where a group of experiment were created with the same model and autosubmit version",
    )
    model: str = Field(primary_key=True, description="Name of the climate model")
    count: int = Field(description="Number of times the model was used in experiments")
    total_count: int = Field(
        default=0, description="Historical total count of experiments for this model"
    )

    extracted_time: datetime = Field(
        ...,
        default_factory=datetime.now,
        description="When this data point was extracted from source",
    )

    experiments: List["ExperimentTimeDB"] = Relationship(
        back_populates="model_popularity",
        sa_relationship_kwargs={
            "primaryjoin": "ModelPopularityTimeDB.model == foreign(ExperimentTimeDB.model)",
            "lazy": "selectin",
            "viewonly": True,
        },
    )
