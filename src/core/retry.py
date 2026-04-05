"""Retry logic with exponential backoff."""
import time
import functools
from src.utils.logger import get_logger
logger = get_logger(__name__)

class RetryExhaustedError(Exception):
    def __init__(self, message, last_error=None):
        super().__init__(message)
        self.last_error = last_error

def calculate_delay(attempt, base_delay, strategy="exponential", max_delay=60.0):
    if strategy == "exponential": delay = base_delay * (2 ** attempt)
    elif strategy == "linear": delay = base_delay * (attempt + 1)
    else: delay = base_delay
    return min(delay, max_delay)

def retry(max_attempts=3, base_delay=2.0, backoff="exponential", max_delay=60.0, retryable_exceptions=(ConnectionError, TimeoutError, OSError), on_retry=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        delay = calculate_delay(attempt, base_delay, backoff, max_delay)
                        logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {delay:.1f}s...")
                        if on_retry: on_retry(attempt, e, delay)
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            raise RetryExhaustedError(f"Function {func.__name__} failed after {max_attempts} attempts", last_error=last_error)
        return wrapper
    return decorator

def retry_download(func, *args, **kwargs):
    """Apply retry decorator and immediately call the function.

    Returns the result of func(*args, **kwargs), not a decorated function.
    """
    retry_kwargs = kwargs.pop("_retry", {})
    decorated = retry(
        max_attempts=retry_kwargs.get("max_attempts", 3),
        base_delay=retry_kwargs.get("base_delay", 2.0),
        backoff=retry_kwargs.get("backoff", "exponential"),
        max_delay=retry_kwargs.get("max_delay", 60.0),
        retryable_exceptions=retry_kwargs.get("retryable_exceptions", (ConnectionError, TimeoutError, OSError)),
    )(func)
    return decorated(*args, **kwargs)

