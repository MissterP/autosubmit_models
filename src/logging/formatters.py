"""
Custom log formatters for enhanced logging.
"""

import logging


class ContextualLogFormatter(logging.Formatter):
    """
    Custom log formatter that includes contextual information like request_id.
    """

    def format(self, record):
        log_record = super().format(record)

        # Extract extra fields from the record
        extra_info = []

        # First add the request_id if it exists
        if hasattr(record, "request_id"):
            extra_info.append(f"request_id={record.request_id}")

        # Standard fields we always want to show if present
        standard_fields = [
            "path",
            "method",
            "client_ip",
            "error_type",
            "status_code",
            "process_time",
        ]
        for field in standard_fields:
            if hasattr(record, field) and getattr(record, field) is not None:
                extra_info.append(f"{field}={getattr(record, field)}")

        # Now add any other extra fields that might be present
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                # Skip standard attributes and those we've already processed
                if key not in standard_fields and key not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "lineno",
                    "funcName",
                    "created",
                    "asctime",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "request_id",
                    "message",
                ]:
                    if value is not None:
                        extra_info.append(f"{key}={value}")

        # Append the extra information if we have any
        if extra_info:
            log_record = f"{log_record} [{' | '.join(extra_info)}]"

        return log_record
