from fastapi import Request

from src.api.routes.internal.router import internal_router


@internal_router.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


@internal_router.get("/ready", tags=["health"])
async def readiness_check(request: Request):
    """
    Readiness check endpoint to verify if the service is ready to accept traffic.

    Checks if all dependencies are healthy and the service is ready to handle requests.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        dict: A dictionary containing the readiness status and dependency statuses.
    """

    is_ready = True
    deps_status = {}

    app = request.app

    if hasattr(app.state, "cache"):
        try:
            app.state.cache.get("health_check")
            deps_status["cache"] = "ok"
        except Exception as e:
            is_ready = False
            deps_status["cache"] = f"error: {e}"

    return {
        "status": "ready" if is_ready else "not ready",
        "dependencies": deps_status,
    }
