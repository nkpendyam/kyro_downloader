"""Retry logic with exponential backoff."""

from __future__ import annotations

import functools
import socket
import time
from collections.abc import Callable
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RetryExhaustedError(Exception):
    """Raised when a retry policy reaches max attempts."""

    def __init__(self, message: str, last_error: Exception | None = None) -> None:
        super().__init__(message)
        self.last_error = last_error


NON_RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    FileNotFoundError,
    PermissionError,
    IsADirectoryError,
    NotADirectoryError,
)


def calculate_delay(attempt: int, base_delay: float, strategy: str = "exponential", max_delay: float = 60.0) -> float:
    """Calculate retry delay using configured strategy."""
    if strategy == "exponential":
        delay = base_delay * (2**attempt)
    elif strategy == "linear":
        delay = base_delay * (attempt + 1)
    else:
        delay = base_delay
    return min(delay, max_delay)


def _default_retryable_exceptions() -> tuple[type[Exception], ...]:
    """Return default recoverable network/system transient exceptions."""
    exceptions: list[type[Exception]] = [ConnectionError, TimeoutError, socket.timeout]
    try:
        import requests

        exceptions.append(requests.exceptions.ConnectionError)
        exceptions.append(requests.exceptions.Timeout)
    except Exception:
        pass
    try:
        import yt_dlp.utils

        exceptions.append(yt_dlp.utils.DownloadError)
    except Exception:
        pass
    unique: list[type[Exception]] = []
    for exc in exceptions:
        if exc not in unique:
            unique.append(exc)
    return tuple(unique)


def retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    backoff: str = "exponential",
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
    non_retryable_exceptions: tuple[type[Exception], ...] = NON_RETRYABLE_EXCEPTIONS,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Retry decorator with customizable retryable/non-retryable exceptions."""
    effective_retryable = retryable_exceptions or _default_retryable_exceptions()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except non_retryable_exceptions:
                    raise
                except effective_retryable as exc:
                    last_error = exc
                    if attempt < max_attempts - 1:
                        delay = calculate_delay(attempt, base_delay, backoff, max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {exc}. Retrying in {delay:.1f}s..."
                        )
                        if on_retry:
                            on_retry(attempt, exc, delay)
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {exc}")
            raise RetryExhaustedError(
                f"Function {func.__name__} failed after {max_attempts} attempts",
                last_error=last_error,
            )

        return wrapper

    return decorator


def _timeout_exceptions() -> tuple[type[Exception], ...]:
    """Build timeout exception tuple, including optional requests timeout."""
    exceptions: list[type[Exception]] = [TimeoutError, socket.timeout]
    try:
        import requests

        exceptions.append(requests.exceptions.Timeout)
    except Exception:
        pass
    unique: list[type[Exception]] = []
    for exc in exceptions:
        if exc not in unique:
            unique.append(exc)
    return tuple(unique)


def retry_network_timeout(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    backoff: str = "exponential",
    max_delay: float = 60.0,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Retry decorator specialized for network timeout exceptions."""
    return retry(
        max_attempts=max_attempts,
        base_delay=base_delay,
        backoff=backoff,
        max_delay=max_delay,
        retryable_exceptions=_timeout_exceptions(),
        on_retry=on_retry,
    )


def retry_download(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Apply retry decorator and immediately call the function."""
    retry_kwargs = kwargs.pop("_retry", {})
    decorated = retry(
        max_attempts=retry_kwargs.get("max_attempts", 3),
        base_delay=retry_kwargs.get("base_delay", 2.0),
        backoff=retry_kwargs.get("backoff", "exponential"),
        max_delay=retry_kwargs.get("max_delay", 60.0),
        retryable_exceptions=retry_kwargs.get("retryable_exceptions", _default_retryable_exceptions()),
    )(func)
    return decorated(*args, **kwargs)


def retry_on_network_timeout(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Apply timeout-only retry decorator and immediately call function."""
    retry_kwargs = kwargs.pop("_timeout_retry", {})
    decorated = retry_network_timeout(
        max_attempts=retry_kwargs.get("max_attempts", 3),
        base_delay=retry_kwargs.get("base_delay", 2.0),
        backoff=retry_kwargs.get("backoff", "exponential"),
        max_delay=retry_kwargs.get("max_delay", 60.0),
    )(func)
    return decorated(*args, **kwargs)
