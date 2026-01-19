"""
Common Utilities and Helper Functions

This module contains shared utility functions used across multiple
modules to prevent code duplication.
"""
from typing import Set
from fastapi import Request


# ============== Path Utilities ==============

PUBLIC_PATHS: Set[str] = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json"
}


def is_public_path(path: str) -> bool:
    """
    Check if a path should be public (no authentication required).

    This is a centralized function used by multiple middleware components
    to determine if authentication/authorization should be skipped.

    Args:
        path: URL path to check

    Returns:
        True if path is public, False otherwise

    Example:
        >>> is_public_path("/health")
        True
        >>> is_public_path("/api/v1/datasets")
        False
    """
    return path in PUBLIC_PATHS or path.startswith("/static")


# ============== Error Response Utilities ==============

def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: dict = None
) -> dict:
    """
    Create standardized error response.

    This provides a consistent error response format across all endpoints,
    making error handling predictable and easier to parse.

    Args:
        error_code: Unique error code for programmatic handling
        message: Human-readable error message
        status_code: HTTP status code (for reference)
        details: Additional error details (optional)

    Returns:
        Standardized error response dictionary

    Example:
        >>> create_error_response(
        ...     "NOT_FOUND",
        ...     "Resource not found",
        ...     404,
        ...     {"resource_id": "123"}
        ... )
        {
            "status": "error",
            "error_code": "NOT_FOUND",
            "message": "Resource not found",
            "details": {"resource_id": "123"}
        }
    """
    response = {
        "status": "error",
        "error_code": error_code,
        "message": message
    }

    if details:
        response["details"] = details

    return response


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error message for client responses.

    Removes potentially sensitive information from error messages
    before sending to clients. Detailed errors are logged server-side.

    Args:
        error: Exception object

    Returns:
        Sanitized error message safe for clients

    Example:
        >>> sanitize_error_message(Exception("Connection failed: password=xyz"))
        "An error occurred"
    """
    error_str = str(error)

    # List of patterns that might contain sensitive info
    sensitive_patterns = [
        "password",
        "token",
        "key",
        "secret",
        "credential",
        "auth",
        "connection string",
        "://",
    ]

    error_lower = error_str.lower()

    # If error contains potentially sensitive info, return generic message
    if any(pattern in error_lower for pattern in sensitive_patterns):
        return "An error occurred. Please try again later."

    # Otherwise return original message (but still sanitized)
    return error_str[:200]  # Limit length


# ============== HTTP Response Utilities ==============

def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for logging/rate limiting.

    Prefers API key over IP address for more accurate tracking.

    Args:
        request: FastAPI Request object

    Returns:
        Client identifier (API key or IP address)

    Example:
        >>> # Request with API key
        >>> get_client_identifier(request)
        "api_key_abc123"

        >>> # Request without API key
        >>> get_client_identifier(request)
        "192.168.1.1"
    """
    # Try to get API key first
    api_key = request.headers.get("X-API-Key") or request.cookies.get("api_key")
    if api_key:
        return f"api_key:{api_key[:16]}..."  # Truncate for security

    # Fall back to IP address
    return f"ip:{request.client.host}"


# ============== Validation Utilities ==============

def validate_pagination_params(
    page: int = 1,
    page_size: int = 50,
    max_page_size: int = 100
) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (validated_page, validated_page_size)

    Raises:
        ValueError: If parameters are invalid

    Example:
        >>> validate_pagination_params(1, 50, 100)
        (1, 50)

        >>> validate_pagination_params(0, 200, 100)
        (1, 100)
    """
    # Validate page number
    if page < 1:
        page = 1

    # Validate page size
    if page_size < 1:
        page_size = 50  # Default
    elif page_size > max_page_size:
        page_size = max_page_size

    return page, page_size


def calculate_offset(page: int, page_size: int) -> int:
    """
    Calculate database offset for pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        Offset value

    Example:
        >>> calculate_offset(1, 50)
        0

        >>> calculate_offset(3, 50)
        100
    """
    return (page - 1) * page_size


def create_pagination_response(
    data: list,
    page: int,
    page_size: int,
    total: int,
    base_url: str = ""
) -> dict:
    """
    Create paginated response with metadata.

    Args:
        data: List of items for current page
        page: Current page number
        page_size: Items per page
        total: Total number of items
        base_url: Base URL for pagination links

    Returns:
        Paginated response dictionary

    Example:
        >>> create_pagination_response(
        ...     data=[{"id": 1}],
        ...     page=1,
        ...     page_size=50,
        ...     total=150
        ... )
        {
            "data": [{"id": 1}],
            "pagination": {
                "page": 1,
                "page_size": 50,
                "total": 150,
                "total_pages": 3,
                "has_next": True,
                "has_prev": False
            }
        }
    """
    total_pages = (total + page_size - 1) // page_size

    return {
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


def paginate_list(
    items: list,
    page: int = 1,
    page_size: int = 50
) -> dict:
    """
    Paginate a list of items.

    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        Dictionary with paginated data and metadata

    Example:
        >>> items = [{"id": i} for i in range(100)]
        >>> result = paginate_list(items, page=2, page_size=10)
        >>> result["pagination"]["page"]
        2
        >>> len(result["data"])
        10
        >>> result["data"][0]["id"]
        10
    """
    # Validate parameters
    page, page_size = validate_pagination_params(page, page_size, max_page_size=1000)

    # Calculate total items
    total = len(items)

    # Calculate pagination bounds
    start_idx = calculate_offset(page, page_size)
    end_idx = start_idx + page_size

    # Slice the list
    paginated_items = items[start_idx:end_idx]

    # Create response
    return create_pagination_response(
        data=paginated_items,
        page=page,
        page_size=page_size,
        total=total
    )


# ============== String Utilities ==============

def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string

    Example:
        >>> truncate_string("This is a very long string", 10)
        "This is..."
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def sanitize_log_message(message: str) -> str:
    """
    Sanitize message for logging (remove sensitive data).

    Args:
        message: Message to sanitize

    Returns:
        Sanitized message

    Example:
        >>> sanitize_log_message("User password=secret123 logged in")
        "User PASSWORD=*** logged in"
    """
    import re

    # Replace common sensitive patterns
    message = re.sub(r'password=[^\s]+', 'PASSWORD=***', message, flags=re.IGNORECASE)
    message = re.sub(r'token=[^\s]+', 'TOKEN=***', message, flags=re.IGNORECASE)
    message = re.sub(r'key=[^\s]+', 'KEY=***', message, flags=re.IGNORECASE)
    message = re.sub(r'secret=[^\s]+', 'SECRET=***', message, flags=re.IGNORECASE)

    return message


# ============== Time Utilities ==============

def format_duration_ms(duration_ms: int) -> str:
    """
    Format duration in milliseconds to human-readable string.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Formatted duration string

    Example:
        >>> format_duration_ms(1500)
        "1.50s"

        >>> format_duration_ms(250)
        "250ms"
    """
    if duration_ms >= 1000:
        return f"{duration_ms / 1000:.2f}s"
    return f"{duration_ms}ms"


def format_bytes(bytes_count: int) -> str:
    """
    Format byte count to human-readable string.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted byte string

    Example:
        >>> format_bytes(1536)
        "1.50 KB"

        >>> format_bytes(1048576)
        "1.00 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"
