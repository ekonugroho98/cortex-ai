"""
Security Middleware for Rate Limiting and Security Headers
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from typing import Dict, Optional
from datetime import datetime, timedelta
import time

from app.utils.common import is_public_path


class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, use Redis or similar
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list[datetime]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed

        Args:
            identifier: Unique identifier (IP address or API key)

        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.now()

        # Clean old requests
        if identifier in self.requests:
            # Remove requests older than 1 minute
            minute_ago = now - timedelta(minutes=1)
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > minute_ago
            ]

        # Check if limit exceeded
        if identifier not in self.requests:
            self.requests[identifier] = []

        if len(self.requests[identifier]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limiting Middleware
    """

    def __init__(self, app, requests_per_minute: int = 60) -> None:
        """
        Initialize rate limiting middleware

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and check rate limits

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response or JSONResponse with error
        """
        # Skip rate limiting for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Get client identifier (IP address or API key)
        api_key = request.headers.get("X-API-Key")
        identifier = api_key or request.client.host

        # Check rate limit
        if not self.rate_limiter.is_allowed(identifier):
            logger.warning(f"Rate limit exceeded for {identifier} at {request.url.path}")
            return Response(
                content='{"status":"error","error_code":"RATE_LIMIT_EXCEEDED","message":"Too many requests. Please try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )

        # Get current count
        remaining = self.rate_limiter.requests_per_minute - len(
            self.rate_limiter.requests.get(identifier, [])
        )

        # Continue with request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _is_public_path(self, path: str) -> bool:
        """
        Check if path should be public (no rate limit)

        Args:
            path: URL path

        Returns:
            True if path is public, False otherwise
        """
        return is_public_path(path)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security Headers Middleware
    Adds security headers to all responses
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add security headers to response

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
