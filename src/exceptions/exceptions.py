"""
Domain-specific exceptions for the Autosubmit Models API.
"""

from typing import Any, Dict, Optional


class DomainException(Exception):
    """Base exception for all domain-specific exceptions."""

    http_status_code = 500

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        already_logged: bool = False,
    ):
        self.message = message
        self.context = context or {}
        self.already_logged = already_logged
        super().__init__(message)


class ValidationException(DomainException):
    """Exception raised for validation errors."""

    http_status_code = 400


class ResourceNotFoundException(DomainException):
    """Exception raised when a requested resource is not found."""

    http_status_code = 404


class ServiceUnavailableException(DomainException):
    """Exception raised when a required service is unavailable."""

    http_status_code = 503


class DatabaseException(DomainException):
    """Exception raised when there is an error with database operations."""

    http_status_code = 500
