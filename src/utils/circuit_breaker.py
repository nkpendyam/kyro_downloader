"""Circuit breaker pattern for resilient service calls."""
import time
import threading
from enum import Enum
from typing import Callable, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        state = self.state
        if state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit '{self.name}' is OPEN. Service unavailable."
            )

        if state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError(
                        f"Circuit '{self.name}' is HALF_OPEN with max calls reached."
                    )
                self._half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit '{self.name}' CLOSED after successful recovery")
            else:
                self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(
                    f"Circuit '{self.name}' OPEN after failure in HALF_OPEN state"
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit '{self.name}' OPEN after {self._failure_count} failures"
                )

    def reset(self):
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = 0.0
            self._half_open_calls = 0
            logger.info(f"Circuit '{self.name}' manually reset to CLOSED")

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


class CircuitBreakerRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers = {}
        return cls._instance

    def get(self, name: str, **kwargs) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, **kwargs)
        return self._breakers[name]

    def get_all_status(self) -> dict:
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}

    def reset_all(self):
        for breaker in self._breakers.values():
            breaker.reset()
