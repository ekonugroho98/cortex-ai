"""
Authentication Middleware for API Security
"""
from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader, APIKeyCookie
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from loguru import logger
from typing import Optional
import secrets

from app.utils.common import is_public_path


class APIKeyAuth:
    """
    API Key Authentication using X-API-Key header or cookie
    """

    def __init__(self, api_keys: list[str]) -> None:
        """
        Initialize API Key authentication

        Args:
            api_keys: List of valid API keys
        """
        self.api_keys = set(api_keys)
        self.header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
        self.cookie_scheme = APIKeyCookie(name="api_key", auto_error=False)

    async def __call__(self, request: Request) -> Optional[str]:
        """
        Validate API key from header or cookie

        Args:
            request: FastAPI request object

        Returns:
            API key if valid, None otherwise

        Raises:
            HTTPException: If API key is invalid or missing
        """
        # Skip authentication for health checks and docs
        if self._is_public_path(request.url.path):
            return None

        # Try header first, then cookie
        api_key = await self.header_scheme.__call__(request)
        if not api_key:
            api_key = await self.cookie_scheme.__call__(request)

        if not api_key:
            logger.warning(f"Missing API key for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "MISSING_API_KEY",
                    "message": "API key is required. Provide it via X-API-Key header or api_key cookie."
                }
            )

        if api_key not in self.api_keys:
            logger.warning(f"Invalid API key attempted for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INVALID_API_KEY",
                    "message": "Invalid API key"
                }
            )

        logger.debug(f"Authenticated request to {request.url.path}")
        return api_key

    def _is_public_path(self, path: str) -> bool:
        """
        Check if path should be public (no auth required)

        Args:
            path: URL path

        Returns:
            True if path is public, False otherwise
        """
        return is_public_path(path)


def generate_api_key() -> str:
    """
    Generate a secure random API key

    Returns:
        Secure random API key (64 characters hex)
    """
    return secrets.token_hex(32)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication Middleware for all requests
    """

    def __init__(self, app, api_keys: list[str]) -> None:
        """
        Initialize authentication middleware

        Args:
            app: FastAPI application
            api_keys: List of valid API keys
        """
        super().__init__(app)
        self.api_keys = set(api_keys)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and validate authentication

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response or JSONResponse with error
        """
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Check for API key in header or cookie
        api_key = request.headers.get("X-API-Key") or request.cookies.get("api_key")

        if not api_key:
            logger.warning(f"Missing API key for {request.url.path} from {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "error_code": "MISSING_API_KEY",
                    "message": "API key is required. Provide it via X-API-Key header or api_key cookie."
                }
            )

        if api_key not in self.api_keys:
            logger.warning(f"Invalid API key attempted for {request.url.path} from {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": "error",
                    "error_code": "INVALID_API_KEY",
                    "message": "Invalid API key"
                }
            )

        # Log successful authentication
        logger.debug(f"Authenticated request: {request.method} {request.url.path}")

        # Continue with request
        response = await call_next(request)
        return response

    def _is_public_path(self, path: str) -> bool:
        """
        Check if path should be public (no auth required)

        Args:
            path: URL path

        Returns:
            True if path is public, False otherwise
        """
        return is_public_path(path)
