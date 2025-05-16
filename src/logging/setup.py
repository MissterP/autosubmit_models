"""
Setup and configuration for application logging.
"""

import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from src.logging.formatters import ContextualLogFormatter


class DuplicateFilter(logging.Filter):
    """
    Filter for removing duplicate log records.
    Keeps track of logged messages and filters out duplicates within a short time window.
    """

    def __init__(self):
        super().__init__()
        self.last_log = {}
        self.duplicate_window = 0.5  # in seconds

    def filter(self, record):
        # Create a key from the message and log level
        current_time = record.created
        log_key = (record.levelno, record.getMessage())

        # Check if this is a repeat message within the window
        if log_key in self.last_log:
            last_time = self.last_log[log_key]
            if current_time - last_time < self.duplicate_window:
                return 0  # Filter out duplicate

        # Update last time this message was seen
        self.last_log[log_key] = current_time
        return 1  # Keep the log


def configure_logging():
    """
    Configure the application logging system.

    Sets up formatters, handlers and log levels.
    Suppresses uvicorn logs and reduces duplicate logs.
    """
    # First, set up the root logger to control all Python logs
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Set root logger to WARNING to reduce noise

    # Configure the application logger
    logger = logging.getLogger("autosubmit_models_api")

    # Clear existing handlers if any
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    formatter = ContextualLogFormatter(
        " %(levelname)s | %(asctime)s | %(name)s - %(message)s",
    )

    # Add duplicate filter to console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    console_handler.addFilter(DuplicateFilter())

    logger.setLevel(log_level)
    logger.addHandler(console_handler)

    # Configuración para logs en archivos con nombres por fecha
    log_dir = os.getenv("LOG_DIR", "logs")

    if log_dir:
        # Asegurar que el directorio de logs existe
        os.makedirs(log_dir, exist_ok=True)

        # Crear nombre de archivo basado en la fecha actual
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"autosubmit_models_{current_date}.log"

        # Ruta completa al archivo de logs
        log_path = os.path.join(log_dir, log_filename)

        # Usar FileHandler para crear un nuevo archivo cada día
        # (el nombre del archivo ya incluye la fecha)
        file_handler = logging.FileHandler(
            log_path,
            mode="a",  # Append mode
        )

        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        file_handler.addFilter(
            DuplicateFilter()
        )  # Also add duplicate filter to file handler
        logger.addHandler(file_handler)

    # Disable propagation to prevent double-logging
    logger.propagate = False

    # Suppress uvicorn logs unless explicitly enabled
    if not os.getenv("ENABLE_UVICORN_LOGS", "").lower() in ("1", "true", "yes"):
        for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
            uvicorn_logger = logging.getLogger(logger_name)
            uvicorn_logger.handlers = []
            uvicorn_logger.propagate = False

    # Also suppress other common noisy loggers
    for logger_name in ["asyncio", "urllib3", "httpx"]:
        noise_logger = logging.getLogger(logger_name)
        noise_logger.setLevel(logging.WARNING)

    logger.debug(f"Logging initialized at {log_level_name} level")
