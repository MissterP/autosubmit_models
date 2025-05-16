"""
Global exception handlers for the application.
"""

import traceback

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.exceptions.exceptions import DomainException
from src.logging import ContextualLogger, get_current_request_id


async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.

    Provides consistent error handling, logging, and HTTP responses
    for different types of exceptions throughout the application.

    Args:
        request: FastAPI request object
        exc: The exception that was raised

    Returns:
        JSONResponse: A properly formatted error response with appropriate status code
    """

    request_id = get_current_request_id()

    request_info = {
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
        "client_port": request.client.port if request.client else None,
    }

    response_headers = None

    if isinstance(exc, DomainException):
        status_code = exc.http_status_code
        error_type = exc.__class__.__name__
        error_message = exc.message

        context_info = exc.context if hasattr(exc, "context") else {}

        log_method = (
            ContextualLogger.error if status_code >= 500 else ContextualLogger.warning
        )

        log_method(
            f"{error_type}: {error_message}",
            extra={
                "error_type": error_type,
                "status_code": status_code,
                **request_info,
                **context_info,
            },
        )

        response_content = {
            "detail": error_message,
            "type": error_type,
            "reference": request_id,
        }

    elif isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_type = "HTTPException"
        error_message = str(exc.detail)

        log_method = (
            ContextualLogger.error if status_code >= 500 else ContextualLogger.warning
        )

        log_method(
            f"HTTP Exception {status_code}: {error_message}",
            extra={
                "error_type": error_type,
                "status_code": status_code,
                **request_info,
            },
        )
        response_content = {
            "detail": error_message,
            "type": error_type,
            "reference": request_id,
        }

    else:
        status_code = 500
        error_type = exc.__class__.__name__
        error_message = str(exc)

        ContextualLogger.error(
            f"Unhandled exception: {error_type}: {error_message}",
            extra={
                "error_type": error_type,
                "status_code": status_code,
                "traceback": traceback.format_exc(),
                **request_info,
            },
        )

        response_content = {
            "detail": "An unexpected error occurred",
            "reference": request_id,
        }

    response_kwargs = {"status_code": status_code, "content": response_content}

    if response_headers:
        response_kwargs["headers"] = response_headers

    return JSONResponse(**response_kwargs)
