"""
Main application entry point that handles startup and shutdown of the API and workers.
"""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI

from src.api.api_router import setup_routes
from src.cache import Cache
from src.config.project import get_project_metadata
from src.data.db_init import initialize_database
from src.logging import ContextualLogger, configure_logging
from src.middleware import global_exception_handler, request_context_middleware
from src.workers.worker_manager import worker_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Configure resources on startup and cleanup on shutdown.
    """

    metadata = get_project_metadata()
    version = metadata["version"]

    configure_logging()
    cache = Cache(default_ttl=int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", 3600)))

    app.state.start_time = datetime.now()
    app.state.version = version
    app.state.cache = cache

    ContextualLogger.info(
        f"Starting {metadata['name']} version {version} at {app.state.start_time.isoformat()}"
    )

    initialize_database()

    worker_manager.register_default_workers()
    app.state.worker_manager = worker_manager
    await worker_manager.start_workers()
    ContextualLogger.info("Workers started successfully")

    yield

    ContextualLogger.info("Stopping workers...")
    if hasattr(app.state, "worker_manager"):
        await app.state.worker_manager.stop_workers()
        ContextualLogger.info("All workers stopped successfully")

    uptime = datetime.now() - app.state.start_time
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    if hasattr(app.state, "cache"):
        cache_stats = app.state.cache.get_stats()
        app.state.cache.clear()
        ContextualLogger.info(
            f"Cache cleared, had {cache_stats['total_entries']} entries"
        )

    ContextualLogger.info(
        f"Shutting down {metadata['name']} after {uptime_str}",
        extra={
            "uptime_seconds": uptime.total_seconds(),
        },
    )


def configure_app(app: FastAPI):
    """
    Configure middleware and exception handlers.
    """

    app.middleware("http")(request_context_middleware)

    app.exception_handler(Exception)(global_exception_handler)


def create__app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """

    metadata = get_project_metadata()

    app = FastAPI(
        title=metadata["name"],
        description=metadata["description"],
        version=metadata["version"],
        lifespan=lifespan,
        license_info=metadata["license"],
        contact=metadata["contact"],
    )

    configure_app(app)

    setup_routes(app)

    return app


def run_api_server():
    """
    Run the API server using uvicorn.
    """
    try:
        uvicorn.run(
            "src.main:create__app",
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", 8003)),
            factory=True,
            log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
            timeout_keep_alive=int(os.getenv("UVICORN_KEEP_ALIVE", "60")),
            reload=os.getenv("UVICORN_RELOAD", "false").lower() == "true",
            access_log=(os.getenv("ENABLE_UVICORN_LOGS", "False").lower() == "true"),
            timeout_graceful_shutdown=int(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "10")),
        )
    except KeyboardInterrupt:
        ContextualLogger.info(
            "Received KeyboardInterrupt (Ctrl+C). Shutting down gracefully."
        )
    except Exception as e:
        ContextualLogger.error(f"Error running API server: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    """
    Entry point for running the API server.
    """
    import signal
    import threading

    shutdown_in_progress = threading.Event()

    def signal_handler(sig, frame):
        sig_name = signal.Signals(sig).name

        if shutdown_in_progress.is_set():
            ContextualLogger.warning(
                f"Second {sig_name} received. Forcing immediate shutdown..."
            )
            sys.exit(1)

        shutdown_in_progress.set()
        ContextualLogger.info(
            f"Received signal {sig_name}. Initiating graceful shutdown..."
        )

        # Set a fallback timeout for forced exit if graceful shutdown takes too long
        def force_exit():
            if shutdown_in_progress.is_set():
                ContextualLogger.warning("Graceful shutdown timed out. Forcing exit...")
                sys.exit(1)

        # Wait up to 15 seconds for graceful shutdown before forcing exit
        threading.Timer(15.0, force_exit).start()

    # Register signal handlers for common termination signals
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination request

    try:
        run_api_server()
    except KeyboardInterrupt:
        # This is a fallback in case the signal handler doesn't catch it
        ContextualLogger.info("KeyboardInterrupt received. Shutting down...")
    except Exception as e:
        ContextualLogger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
