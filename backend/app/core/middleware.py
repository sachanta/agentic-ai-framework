"""
Custom middleware for the application.
"""
import time
import logging
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling uncaught exceptions."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(f"Unhandled exception: {e}")
            raise


def setup_middleware(app: FastAPI):
    """Setup all middleware for the application."""
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
