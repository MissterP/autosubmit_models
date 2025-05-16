"""
Project metadata configuration.
"""

import os
from typing import Any, Dict

PROJECT_NAME = "Autosubmit Models API"
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "1.0.0")
PROJECT_DESCRIPTION = "API for analyzing Autosubmit models and experiments"
PROJECT_LICENSE = {
    "name": "GNU GENERAL PUBLIC LICENSE",
    "url": "https://www.gnu.org/licenses/gpl-3.0.html",
}

COPYRIGHT_YEAR = "2025"
COPYRIGHT_OWNER = "BSC - Barcelona Supercomputing Center"

CONTACT_NAME = "Pablo Aparici"
CONTACT_EMAIL = "pablo.aparici@bsc.es"


def get_project_metadata() -> Dict[str, Any]:
    """
    Get project metadata as a dictionary.
    """

    return {
        "name": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "description": PROJECT_DESCRIPTION,
        "license": PROJECT_LICENSE,
        "copyright": f"{COPYRIGHT_YEAR} {COPYRIGHT_OWNER}",
        "contact": {"name": CONTACT_NAME, "email": CONTACT_EMAIL},
    }
