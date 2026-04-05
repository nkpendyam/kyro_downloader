"""Tests for circuit breaker utilities."""
import time
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState, CircuitBreakerRegistry

class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    def test_successful_call(self):
        cb = CircuitBreaker("test")
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(3):
            try:
                cb.call(lambda: 1/0)
            except ZeroDivisionError:
                pass
        assert cb.state == CircuitState.OPEN

    def test_raises_when_open(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        assert cb.state == CircuitState.OPEN
        try:
            cb.call(lambda: "ok")
        except CircuitBreakerError:
            pass

    def test_recovers_after_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        assert cb.state == CircuitState.OPEN
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    def test_reset(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        try:
            cb.call(lambda: 1/0)
        except ZeroDivisionError:
            pass
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_get_status(self):
        cb = CircuitBreaker("test", failure_threshold=5)
        status = cb.get_status()
        assert status["name"] == "test"
        assert status["threshold"] == 5


class TestCircuitBreakerRegistry:
    def test_singleton(self):
        r1 = CircuitBreakerRegistry()
        r2 = CircuitBreakerRegistry()
        assert r1 is r2

    def test_get_creates_new(self):
        registry = CircuitBreakerRegistry()
        registry._breakers = {}
        cb = registry.get("test", failure_threshold=3)
        assert isinstance(cb, CircuitBreaker)
        assert cb.failure_threshold == 3

    def test_get_returns_existing(self):
        registry = CircuitBreakerRegistry()
        registry._breakers = {}
        cb1 = registry.get("test")
        cb2 = registry.get("test")
        assert cb1 is cb2

    def test_get_all_status(self):
        registry = CircuitBreakerRegistry()
        registry._breakers = {}
        registry.get("test1")
        registry.get("test2")
        status = registry.get_all_status()
        assert "test1" in status
        assert "test2" in status
