from fastapi import Request

from src.api.routes.internal.router import internal_router


@internal_router.get("/clean_cache", tags=["cache"])
async def clean_cache(request: Request):
    """
    Clean cache endpoint.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        dict: A dictionary containing the status of the cache cleaning operation.
    """

    app = request.app

    if hasattr(request.app.state, "cache"):
        app.state.cache.clear()
        return {"detail": "Cache cleared"}

    return {"detail": "Cache not ready for cleaning"}
