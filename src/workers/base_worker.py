"""
Base worker class that defines the common interface and functionality for all workers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """Base worker class that all workers should extend."""

    def __init__(self, interval_seconds: int):
        """
        Initialize the worker with the specified interval.

        Args:
            interval_seconds: Time in seconds between worker executions
        """
        self.interval_seconds = interval_seconds
        self.is_running = False
        self.shared_timestamp = None

    def set_timestamp(self, timestamp: datetime):
        """Set a shared timestamp for this worker."""
        self.shared_timestamp = timestamp

    @abstractmethod
    async def execute_task(self):
        """
        Execute the worker task. This method should be implemented by all workers.

        Raises:
            Exception: If the task execution fails
        """
        pass

    async def start(self):
        """Start the worker process."""
        self.is_running = True
        logger.info(
            f"Starting {self.__class__.__name__} with {self.interval_seconds}s interval"
        )

        while self.is_running:
            try:
                logger.info(f"Executing {self.__class__.__name__} task")
                await self.execute_task()
                logger.info(f"{self.__class__.__name__} task completed successfully")
            except Exception as e:
                logger.error(
                    f"Error executing {self.__class__.__name__} task: {str(e)}",
                    exc_info=True,
                )

            await asyncio.sleep(self.interval_seconds)

    async def stop(self):
        """Stop the worker process."""
        logger.info(f"Stopping {self.__class__.__name__}")
        self.is_running = False
