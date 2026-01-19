"""
Structured Logging Utilities

This module provides structured logging helpers with context tracking.
All logs include request_id, user_id, and other contextual information.
"""
from loguru import logger
from typing import Dict, Any, Optional
from contextvars import ContextVar
import uuid
import time
from functools import wraps

# Context variables for async-safe request tracking
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")
api_key_ctx: ContextVar[str] = ContextVar("api_key", default="")


def generate_request_id() -> str:
    """
    Generate a unique request ID

    Returns:
        Unique request ID (UUID v4)
    """
    return str(uuid.uuid4())


def get_request_id() -> str:
    """
    Get current request ID from context

    Returns:
        Current request ID or empty string if not set
    """
    return request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """
    Set request ID in context

    Args:
        request_id: Request ID to set
    """
    request_id_ctx.set(request_id)


def set_user_context(user_id: str = "", api_key: str = "") -> None:
    """
    Set user context in current request

    Args:
        user_id: User identifier
        api_key: API key (truncated)
    """
    if user_id:
        user_id_ctx.set(user_id)
    if api_key:
        # Truncate API key for security
        api_key_ctx.set(api_key[:16] + "..." if len(api_key) > 16 else api_key)


def get_log_context() -> Dict[str, str]:
    """
    Get current logging context

    Returns:
        Dictionary with request_id, user_id, api_key
    """
    return {
        "request_id": get_request_id(),
        "user_id": user_id_ctx.get(),
        "api_key": api_key_ctx.get()
    }


def log_with_context(
    message: str,
    level: str = "info",
    **extra_context
) -> None:
    """
    Log a message with current context

    Args:
        message: Log message
        level: Log level (debug, info, warning, error, critical)
        **extra_context: Additional context fields

    Example:
        log_with_context("User logged in", user_id="123", ip="192.168.1.1")
        # Logs: {"request_id": "...", "user_id": "123", "ip": "192.168.1.1", "message": "User logged in"}
    """
    context = get_log_context()
    context.update(extra_context)

    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, **context)


def log_api_request(
    method: str,
    path: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    **extra_context
) -> None:
    """
    Log API request with structured context

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code (optional)
        duration_ms: Request duration in milliseconds (optional)
        **extra_context: Additional context fields

    Example:
        log_api_request("GET", "/datasets", status_code=200, duration_ms=123)
    """
    context = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms
    }
    context.update(extra_context)

    message = f"{method} {path}"
    if status_code:
        message += f" - {status_code}"
    if duration_ms:
        message += f" ({duration_ms}ms)"

    log_with_context(message, **context)


def log_bigquery_operation(
    operation: str,
    dataset_id: Optional[str] = None,
    table_id: Optional[str] = None,
    success: bool = True,
    duration_ms: Optional[int] = None,
    **extra_context
) -> None:
    """
    Log BigQuery operation with context

    Args:
        operation: Operation type (list_datasets, execute_query, etc.)
        dataset_id: Dataset ID (optional)
        table_id: Table ID (optional)
        success: Whether operation succeeded
        duration_ms: Operation duration in milliseconds (optional)
        **extra_context: Additional context fields

    Example:
        log_bigquery_operation("execute_query", duration_ms=1234, rows_returned=100)
    """
    context = {
        "operation": operation,
        "dataset_id": dataset_id,
        "table_id": table_id,
        "success": success,
        "duration_ms": duration_ms
    }
    context.update(extra_context)

    message = f"BigQuery: {operation}"
    if dataset_id:
        message += f" on {dataset_id}"
        if table_id:
            message += f".{table_id}"

    level = "info" if success else "error"
    log_with_context(message, level=level, **context)


def log_error(
    error: Exception,
    message: str,
    **extra_context
) -> None:
    """
    Log error with context

    Args:
        error: Exception object
        message: Error message
        **extra_context: Additional context fields

    Example:
        try:
            ...
        except Exception as e:
            log_error(e, "Failed to process request", dataset_id="analytics")
    """
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        **extra_context
    }

    log_with_context(message, level="error", **context)


def log_function_call(
    func_name: str,
    args: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
    **extra_context
) -> None:
    """
    Log function call with parameters and duration

    Args:
        func_name: Function name
        args: Function arguments (optional, dict)
        duration_ms: Function duration in milliseconds (optional)
        **extra_context: Additional context fields

    Example:
        @log_function_calls
        def my_function(x, y):
            return x + y
    """
    context = {
        "function": func_name,
        "args": args or {},
        "duration_ms": duration_ms,
        **extra_context
    }

    message = f"Function: {func_name}"
    if duration_ms:
        message += f" ({duration_ms}ms)"

    log_with_context(message, level="debug", **context)


# ============== Decorators ==============

def log_execution_time(func):
    """
    Decorator to log function execution time

    Example:
        @log_execution_time
        def slow_function():
            time.sleep(1)
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)
            log_function_call(
                func.__name__,
                duration_ms=duration_ms,
                success=True
            )
            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_error(
                e,
                f"Function {func.__name__} failed",
                duration_ms=duration_ms
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)
            log_function_call(
                func.__name__,
                duration_ms=duration_ms,
                success=True
            )
            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log_error(
                e,
                f"Function {func.__name__} failed",
                duration_ms=duration_ms
            )
            raise

    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_errors(func):
    """
    Decorator to log function errors

    Example:
        @log_errors
        def risky_function():
            raise ValueError("Something went wrong")
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log_error(e, f"Error in {func.__name__}")
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(e, f"Error in {func.__name__}")
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# ============== Middleware Helpers ==============

async def log_request_middleware(request, call_next):
    """
    FastAPI middleware to log all requests

    Args:
        request: FastAPI Request object
        call_next: Next middleware/route handler

    Returns:
        Response object
    """
    # Generate request ID
    request_id = generate_request_id()
    set_request_id(request_id)

    # Extract API key for context
    api_key = request.headers.get("X-API-Key") or request.cookies.get("api_key", "")
    if api_key:
        set_user_context(api_key=api_key)

    # Log request start
    log_with_context(
        f"Request started: {request.method} {request.url.path}",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params)
    )

    # Process request
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # Log successful request
        log_api_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        # Log failed request
        log_error(
            e,
            f"Request failed: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms
        )
        raise
