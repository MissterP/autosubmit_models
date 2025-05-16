from datetime import datetime

from fastapi import Request

from src.api.routes.internal.router import internal_router
from src.config.project import get_project_metadata


@internal_router.get("/status", tags=["status"])
async def get_status(request: Request):
    """
    Get the status of the API.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        dict: A dictionary containing the status of the API, including version and uptime.
    """
    app = request.app
    start_time = getattr(app, "start_time", None)

    status_info = {
        "status": "healthy",
        "version": getattr(app, "version", "unknown"),
    }

    if start_time:
        uptime = datetime.now() - start_time
        status_info.update(
            {
                "start_time": start_time.isoformat(),
                "uptime_seconds": uptime.total_seconds(),
            }
        )

    if hasattr(app.state, "cache"):
        status_info["cache"] = app.state.cache.get_stats()

    return status_info


@internal_router.get("/info", tags=["info"])
async def get_info(request: Request):
    """
    Get the info of the API.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        dict: A dictionary containing the info of the API, including name, version, and license.
    """
    metadata = get_project_metadata()

    return {
        "name": metadata["name"],
        "version": metadata["version"],
        "description": metadata["description"],
        "license": metadata["license"]["name"],
        "license_url": metadata["license"]["url"],
        "copyright": metadata["copyright"],
        "contact": metadata["contact"],
        "documentation": "/docs",
    }
