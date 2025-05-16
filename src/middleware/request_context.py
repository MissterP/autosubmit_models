"""
Middleware for request context tracking and logging.
"""

import time
import uuid

from fastapi import Request

from src.logging import ContextualLogger, reset_request_id, set_request_id


async def request_context_middleware(request: Request, call_next):
    """
    Middleware that sets up request tracking and logging context.

    Args:
        request (Request): The FastAPI request object.
        call_next: The next middleware or next endpoint handler.

    Returns:
        Response: The HTTP response.
    """

    request_id = str(uuid.uuid4())
    token = set_request_id(request_id)

    request.state.request_id = request_id
    request.state.start_time = time.time()

    ContextualLogger.info(
        f"Request ({request_id}) started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "client_pot": request.client.port if request.client else None,
        },
    )

    try:
        response = await call_next(request)

        process_time = time.time() - request.state.start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # Only log successful completions at INFO level
        if response.status_code < 400:
            ContextualLogger.info(
                f"Request ({request_id}) completed",
                extra={
                    "status_code": response.status_code,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                },
            )

        return response

    except Exception as e:
        process_time = time.time() - request.state.start_time

        # Log the exception only if it's not already being handled elsewhere
        # by checking if it's a known exception type
        from src.exceptions.exceptions import DomainException

        if not isinstance(e, DomainException):
            ContextualLogger.error(
                f"Request ({request_id}) failed: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "error_type": e.__class__.__name__,
                },
                exc_info=True,
            )
        raise
    finally:
        try:
            if token:
                reset_request_id(token)
        except Exception as reset_error:
            ContextualLogger.error(
                f"Error resetting request_id context: {reset_error}",
                extra={"request_id": request_id},
                exc_info=True,
            )
