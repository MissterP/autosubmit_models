"""
Enhanced logger with context capabilities.
"""

import logging

from src.logging.context import get_current_request_id

logger = logging.getLogger("autosubmit_models_api")


class ContextualLogger:
    """
    Logger that automatically adds context to log messages.
    """

    @staticmethod
    def get_context():
        """
        Get current logging context."

        Returns:
            dict: A dictionary containing the current logging context.
        """
        context = {}
        request_id = get_current_request_id()
        if request_id:
            context["request_id"] = request_id
        return context

    @staticmethod
    def _log(level_method, message, *args, **kwargs):
        """
        Helper method to handle common logging logic.

        Args:
            level_method (function): The logging method to call (e.g., debug, info).
            message (str): The log message.
            *args: Additional arguments to pass to the logging method.
            **kwargs: Additional keyword arguments to pass to the logging method.
        """
        # Extract extra parameters and ensure they're properly processed
        extra = kwargs.pop("extra", {})

        # Add request context
        context = ContextualLogger.get_context()

        # Create a LogRecord-compatible extra dict
        record_dict = {}

        # Add context first (lower priority)
        for key, value in context.items():
            record_dict[key] = value

        # Then add explicit extra fields (higher priority)
        for key, value in extra.items():
            record_dict[key] = value

        # Put back in kwargs
        kwargs["extra"] = record_dict

        # Add exception info for error and critical logs if not explicitly disabled
        if level_method in (logger.error, logger.critical) and "exc_info" not in kwargs:
            kwargs["exc_info"] = True

        level_method(message, *args, **kwargs)

    @staticmethod
    def debug(message, *args, **kwargs):
        """
        Log a debug message with context.
        """
        ContextualLogger._log(logger.debug, message, *args, **kwargs)

    @staticmethod
    def info(message, *args, **kwargs):
        """
        Log an info message with context.
        """
        ContextualLogger._log(logger.info, message, *args, **kwargs)

    @staticmethod
    def warning(message, *args, **kwargs):
        """
        Log a warning message with context.
        """
        ContextualLogger._log(logger.warning, message, *args, **kwargs)

    @staticmethod
    def error(message, *args, **kwargs):
        """
        Log an error message with context.
        """
        ContextualLogger._log(logger.error, message, *args, **kwargs)

    @staticmethod
    def critical(message, *args, **kwargs):
        """
        Log a critical message with context.
        """
        ContextualLogger._log(logger.critical, message, *args, **kwargs)
