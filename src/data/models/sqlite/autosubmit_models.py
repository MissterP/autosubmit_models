"""
SQLModel models for Autosubmit SQLite database.
"""

from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class ExperimentDetailDB(SQLModel, table=True):
    """
    Model representing experiment details from Autosubmit database.
    """

    __tablename__ = "details"

    # Configuración para desactivar el espacio de nombres protegido y resolver el warning
    model_config = {
        "protected_namespaces": (),  # Deshabilita espacios de nombres protegidos
        "from_attributes": True,  # Reemplaza orm_mode=True que está deprecado
    }

    exp_id: int = Field(
        primary_key=True,
        foreign_key="experiment.id",
        description="Experiment ID, also primary key",
    )
    user: str = Field(description="User who created the experiment")
    created: str = Field(description="Creation time as text")
    model: str = Field(index=True, description="Model used")
    branch: str = Field(description="Branch of the model used")
    hpc: str = Field(description="HPC used")

    # Property to access creation date as datetime (since stored as text in DB)
    @property
    def credated(self) -> datetime:
        """Get creation date as datetime object."""
        if not self.created:
            return None
        try:
            # Handle ISO format with timezone
            import re
            from datetime import datetime, timezone

            # Parse ISO 8601 format with timezone offset
            # Example: 2022-02-28T17:02:59+02:00
            iso_pattern = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})([+-])(\d{2}):(\d{2})"
            match = re.match(iso_pattern, self.created)

            if match:
                dt_str, sign, hours, minutes = match.groups()
                dt = datetime.fromisoformat(dt_str)

                # Convert timezone offset to seconds
                offset_seconds = int(hours) * 3600 + int(minutes) * 60
                if sign == "-":
                    offset_seconds = -offset_seconds

                # Return datetime with timezone info removed (just the UTC time)
                return dt.replace(tzinfo=None)
            else:
                # Fallback to basic parsing without timezone
                return datetime.fromisoformat(self.created)
        except ValueError as e:
            # Provide fallback behavior if parsing fails
            print(f"Error parsing date '{self.created}': {e}")
            # Return current time as fallback
            return datetime.now()

    # La columna name no existe en la tabla details, está en la tabla experiment
    # Este atributo se rellenará en el worker después de hacer join con experiment

    # Relationship with experiment
    experiment: Optional["ExperimentDB"] = Relationship(
        back_populates="details", sa_relationship_kwargs={"uselist": False}
    )


class ExperimentDB(SQLModel, table=True):
    """
    Model representing experiments from Autosubmit database.
    """

    __tablename__ = "experiment"

    # Configuración para desactivar el espacio de nombres protegido y resolver el warning
    model_config = {
        "protected_namespaces": (),  # Deshabilita espacios de nombres protegidos
        "from_attributes": True,  # Reemplaza orm_mode=True que está deprecado
    }

    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    name: str = Field(index=True)
    type: str = Field(default=None)
    autosubmit_version: str = Field(default=None)
    description: str = Field(default="")
    model_branch: str = Field(default=None)
    template_name: str = Field(default=None)
    template_branch: str = Field(default=None)
    ocean_diagnostics_branch: str = Field(default=None)

    # Relationship with details
    details: Optional["ExperimentDetailDB"] = Relationship(back_populates="experiment")
