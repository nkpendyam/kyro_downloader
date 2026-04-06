"""Tests for retry mechanism."""

from src.core.retry import retry, retry_network_timeout, retry_on_network_timeout


class TestRetry:
    def test_successful_call_no_retry(self):
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = success_func()
        assert result == "ok"
        assert call_count == 1

    def test_retry_on_failure_then_success(self):
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01, retryable_exceptions=(ValueError,))
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        call_count = 0

        @retry(max_attempts=2, base_delay=0.01, retryable_exceptions=(RuntimeError,))
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("permanent error")

        from src.core.retry import RetryExhaustedError

        try:
            always_fail()
            assert False, "Should have raised RetryExhaustedError"
        except RetryExhaustedError:
            pass

        assert call_count == 2

    def test_retry_with_exponential_backoff(self):
        sleep_times = []

        def mock_sleep(delay):
            sleep_times.append(delay)

        import unittest.mock

        with unittest.mock.patch("time.sleep", mock_sleep):

            @retry(max_attempts=3, base_delay=0.1, backoff="exponential", retryable_exceptions=(ValueError,))
            def slow_fail():
                raise ValueError("fail")

            from src.core.retry import RetryExhaustedError

            try:
                slow_fail()
            except RetryExhaustedError:
                pass

        # Exponential: delays should be 0.1, 0.2 (base_delay * 2^attempt)
        assert len(sleep_times) == 2
        assert sleep_times[0] == 0.1
        assert sleep_times[1] == 0.2

    def test_retry_with_linear_backoff(self):
        sleep_times = []

        def mock_sleep(delay):
            sleep_times.append(delay)

        import unittest.mock

        with unittest.mock.patch("time.sleep", mock_sleep):

            @retry(max_attempts=3, base_delay=0.1, backoff="linear", retryable_exceptions=(ValueError,))
            def slow_fail():
                raise ValueError("fail")

            from src.core.retry import RetryExhaustedError

            try:
                slow_fail()
            except RetryExhaustedError:
                pass

        # Linear: delays should be 0.1, 0.2 (base_delay * (attempt + 1))
        assert len(sleep_times) == 2
        assert sleep_times[0] == 0.1
        assert sleep_times[1] == 0.2

    def test_retry_with_fixed_backoff(self):
        sleep_times = []

        def mock_sleep(delay):
            sleep_times.append(delay)

        import unittest.mock

        with unittest.mock.patch("time.sleep", mock_sleep):

            @retry(max_attempts=3, base_delay=0.1, backoff="fixed", retryable_exceptions=(ValueError,))
            def slow_fail():
                raise ValueError("fail")

            from src.core.retry import RetryExhaustedError

            try:
                slow_fail()
            except RetryExhaustedError:
                pass

        # Fixed: delays should be 0.1, 0.1
        assert len(sleep_times) == 2
        assert sleep_times[0] == 0.1
        assert sleep_times[1] == 0.1

    def test_retry_network_timeout_uses_configured_max_attempts(self):
        call_count = 0

        @retry_network_timeout(max_attempts=4, base_delay=0.01)
        def timeout_func():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("network timeout")

        from src.core.retry import RetryExhaustedError

        try:
            timeout_func()
            assert False, "Should have raised RetryExhaustedError"
        except RetryExhaustedError:
            pass

        assert call_count == 4

    def test_retry_on_network_timeout_wrapper(self):
        call_count = 0

        def flaky_timeout():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("network timeout")
            return "ok"

        result = retry_on_network_timeout(
            flaky_timeout,
            _timeout_retry={"max_attempts": 3, "base_delay": 0.01},
        )

        assert result == "ok"
        assert call_count == 3

    def test_file_not_found_is_not_retried(self):
        call_count = 0

        @retry(max_attempts=4, base_delay=0.01)
        def missing_file_func():
            nonlocal call_count
            call_count += 1
            raise FileNotFoundError("missing")

        with raises_error(FileNotFoundError):
            missing_file_func()

        assert call_count == 1

    def test_connection_error_is_retried(self):
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01, retryable_exceptions=(ConnectionError,))
        def flaky_connection():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("temporary")

        from src.core.retry import RetryExhaustedError

        with raises_error(RetryExhaustedError):
            flaky_connection()

        assert call_count == 3

    def test_download_error_is_retried(self):
        call_count = 0

        import yt_dlp.utils

        @retry(max_attempts=3, base_delay=0.01)
        def flaky_download():
            nonlocal call_count
            call_count += 1
            raise yt_dlp.utils.DownloadError("video unavailable")

        from src.core.retry import RetryExhaustedError

        with raises_error(RetryExhaustedError):
            flaky_download()

        assert call_count == 3


class raises_error:
    def __init__(self, exc_type):
        self.exc_type = exc_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return exc_type is not None and (
            exc_val.__class__ is self.exc_type or issubclass(exc_val.__class__, self.exc_type)
        )
