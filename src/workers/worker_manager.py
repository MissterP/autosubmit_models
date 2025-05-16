"""
Worker manager that coordinates all API workers.
"""

import asyncio
from datetime import datetime
from typing import Dict, List

from src.logging.logger import ContextualLogger
from src.workers.base_worker import BaseWorker
from src.workers.workers.autosubmit_sync_worker import AutosubmitSyncWorker


class WorkerManager:
    """
    Manages the lifecycle of all API workers.
    Handles starting and stopping worker tasks.
    """

    def __init__(self):
        """Initialize the worker manager."""
        self.workers: Dict[str, BaseWorker] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.current_timestamp = None

    def register_worker(self, name: str, worker: BaseWorker):
        """
        Register a new worker.

        Args:
            name: Unique name for the worker
            worker: Worker instance
        """
        if name in self.workers:
            ContextualLogger.warning(f"Worker {name} already registered, replacing")
        self.workers[name] = worker
        ContextualLogger.info(f"Registered worker: {name}")

    def register_default_workers(self):
        """Register all default workers."""
        self.register_worker("autosubmit_sync", AutosubmitSyncWorker())

    async def _generate_shared_timestamp(self):
        """Generate a shared timestamp for all workers to use."""
        self.current_timestamp = datetime.now()
        return self.current_timestamp

    async def start_workers(self):
        """Start all registered workers with a shared timestamp."""
        ContextualLogger.info("Starting all workers")

        shared_timestamp = await self._generate_shared_timestamp()
        ContextualLogger.info(
            f"Generated shared timestamp for all workers: {shared_timestamp}"
        )

        for name, worker in self.workers.items():
            if name not in self.tasks or self.tasks[name].done():
                worker.set_timestamp(shared_timestamp)
                self.tasks[name] = asyncio.create_task(worker.start())
                ContextualLogger.info(f"Started worker: {name}")

    async def stop_workers(self):
        """Stop all running workers."""
        ContextualLogger.info("Stopping all workers")
        for name, worker in self.workers.items():
            if name in self.tasks and not self.tasks[name].done():
                await worker.stop()
                ContextualLogger.info(f"Stopped worker: {name}")

        # Wait for all tasks to complete
        pending_tasks = [task for task in self.tasks.values() if not task.done()]
        if pending_tasks:
            await asyncio.gather(*pending_tasks, return_exceptions=True)

    def get_worker_names(self) -> List[str]:
        """
        Get a list of all registered worker names.

        Returns:
            List[str]: List of worker names
        """
        return list(self.workers.keys())

    def get_worker(self, name: str) -> BaseWorker:
        """
        Get a specific worker by name.

        Args:
            name: Worker name

        Returns:
            BaseWorker: The worker instance

        Raises:
            KeyError: If the worker is not found
        """
        if name not in self.workers:
            raise KeyError(f"Worker {name} not found")
        return self.workers[name]


worker_manager = WorkerManager()
