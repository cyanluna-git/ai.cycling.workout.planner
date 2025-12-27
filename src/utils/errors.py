"""Error Handling Utilities.

Provides decorators and utilities for consistent error handling
across the application.
"""

import logging
import functools
from typing import Callable, TypeVar, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar("T")


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details


class APIError(AppError):
    """Error from external API calls."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        super().__init__(message, code="API_ERROR", details=details)
        self.status_code = status_code


class ValidationError(AppError):
    """Data validation error."""

    def __init__(self, message: str, field: str = None):
        super().__init__(message, code="VALIDATION_ERROR", details={"field": field})
        self.field = field


class ConfigError(AppError):
    """Configuration error."""

    def __init__(self, message: str, missing_key: str = None):
        super().__init__(
            message, code="CONFIG_ERROR", details={"missing_key": missing_key}
        )


def handle_errors(
    log_level: int = logging.ERROR,
    reraise: bool = True,
    default_return: Any = None,
):
    """Decorator for consistent error handling.

    Args:
        log_level: Logging level for errors.
        reraise: Whether to reraise the exception after logging.
        default_return: Value to return if not reraising.

    Example:
        @handle_errors(log_level=logging.WARNING)
        async def my_function():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Don't wrap FastAPI HTTP exceptions
                raise
            except AppError as e:
                logger.log(log_level, f"{func.__name__}: {e.code} - {e.message}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                logger.log(log_level, f"{func.__name__} failed: {e}", exc_info=True)
                if reraise:
                    raise
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except AppError as e:
                logger.log(log_level, f"{func.__name__}: {e.code} - {e.message}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                logger.log(log_level, f"{func.__name__} failed: {e}", exc_info=True)
                if reraise:
                    raise
                return default_return

        # Check if function is async
        if hasattr(func, "__wrapped__"):
            # Handle already-wrapped functions
            return (
                async_wrapper
                if asyncio.iscoroutinefunction(func.__wrapped__)
                else sync_wrapper
            )
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def to_http_exception(error: AppError, status_code: int = 500) -> HTTPException:
    """Convert AppError to FastAPI HTTPException.

    Args:
        error: The application error.
        status_code: HTTP status code to use.

    Returns:
        FastAPI HTTPException.
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error.code,
            "message": error.message,
            "details": error.details,
        },
    )


def safe_get(data: dict, *keys, default: Any = None) -> Any:
    """Safely get nested dictionary values.

    Args:
        data: Dictionary to get value from.
        *keys: Keys to traverse.
        default: Default value if key not found.

    Returns:
        Value at the nested key path or default.

    Example:
        >>> data = {"a": {"b": {"c": 1}}}
        >>> safe_get(data, "a", "b", "c")
        1
        >>> safe_get(data, "a", "x", default=0)
        0
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


# Import asyncio for the decorator
import asyncio
