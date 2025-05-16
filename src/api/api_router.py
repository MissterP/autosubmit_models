from fastapi import FastAPI

from src.api.routes.internal.router import internal_router
from src.api.routes.v1.metrics.metrics_router import router as metrics_router
from src.logging import ContextualLogger


def setup_routes(app: FastAPI):
    """
    Configure all API routes for the application.

    Args:
        app: FastAPI application instance
    """
    app.include_router(metrics_router, tags=["metrics"])

    app.include_router(internal_router, tags=["internal"])

    ContextualLogger.info("API routes configured successfully")
