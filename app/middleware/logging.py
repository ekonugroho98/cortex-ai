"""
Structured Logging Middleware

This middleware adds structured logging to all HTTP requests.
It tracks request ID, user context, and execution time.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time

from app.utils.logging import (
    generate_request_id,
    set_request_id,
    set_user_context,
    log_with_context,
    log_api_request,
    log_error
)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging of all HTTP requests

    Features:
    - Generates unique request IDs
    - Tracks user context (API key)
    - Logs request start/end
    - Measures execution time
    - Adds request ID to response headers
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add structured logging

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with X-Request-ID header
        """
        # Generate and set request ID
        request_id = generate_request_id()
        set_request_id(request_id)

        # Extract user context
        api_key = request.headers.get("X-API-Key") or request.cookies.get("api_key", "")
        client_ip = self._get_client_ip(request)
        if api_key:
            set_user_context(api_key=api_key)

        # Log request start
        log_with_context(
            f"{request.method} {request.url.path} - Started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=client_ip
        )

        # Process request with timing
        start_time = time.time()
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful request
            log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Log failed request
            log_error(
                e,
                f"{request.method} {request.url.path} - Failed",
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                duration_ms=duration_ms
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
