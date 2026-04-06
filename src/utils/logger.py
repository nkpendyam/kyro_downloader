"""Structured logging setup with loguru."""

import sys
import threading

from loguru import logger

LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

_setup_done = False
_setup_lock = threading.Lock()


def setup_logger(log_level: str = "INFO", log_file: str | None = None):
    global _setup_done
    if _setup_done:
        return logger
    with _setup_lock:
        if _setup_done:
            return logger
        logger.remove()
        logger.add(sys.stderr, format=LOG_FORMAT, level=log_level, colorize=True)
        if log_file:
            logger.add(log_file, level=log_level, rotation="10 MB", retention="30 days", enqueue=True)
        _setup_done = True
    return logger


def get_logger(name: str | None = None):
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")
    return logger.bind(name=name)
