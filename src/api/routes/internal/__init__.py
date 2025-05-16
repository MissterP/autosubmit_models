"""
Internal API routes for the application.
"""

from src.api.routes.internal import cache, health, status
from src.api.routes.internal.router import internal_router

__all__ = ["internal_router, health, status, cache"]
