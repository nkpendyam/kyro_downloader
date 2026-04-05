"""Tests for logger module."""
from src.utils.logger import setup_logger, get_logger


class TestLogger:
    def test_setup_logger(self):
        logger = setup_logger(log_level="DEBUG")
        assert logger is not None

    def test_setup_logger_with_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logger(log_level="INFO", log_file=str(log_file))
        assert logger is not None

    def test_setup_logger_idempotent(self):
        logger1 = setup_logger(log_level="DEBUG")
        logger2 = setup_logger(log_level="WARNING")
        assert logger1 is logger2

    def test_get_logger(self):
        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_default_name(self):
        logger = get_logger()
        assert logger is not None
