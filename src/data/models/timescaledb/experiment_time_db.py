"""
Experiment time-series database model.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String
from sqlalchemy.orm import foreign
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.data.models.timescaledb.model_popularity_time_db import \
        ModelPopularityTimeDB


class ExperimentTimeDB(SQLModel, table=True):
    """
    Database model for tracking experiments over time.

    This model stores information about climate model experiments,
    including when they were created and what model they use.
    """

    __tablename__ = "experiments"

    id: str = Field(
        primary_key=True, description="Unique identifier for the experiment"
    )

    name: str = Field(unique=True, description="Name of the experiment")
    model: str = Field(description="Name of the climate model used in this experiment")
    created_time: datetime = Field(
        default_factory=datetime.now, description="When this experiment was created"
    )

    model_popularity: Optional["ModelPopularityTimeDB"] = Relationship(
        back_populates="experiments",
        sa_relationship_kwargs={
            "primaryjoin": "foreign(ExperimentTimeDB.model) == ModelPopularityTimeDB.model",
            "viewonly": True,
        },
    )
