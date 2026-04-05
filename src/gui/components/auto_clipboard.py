"""Auto-clipboard monitoring service."""
import time
import threading
from src.utils.validation import validate_url
from src.utils.logger import get_logger
logger = get_logger(__name__)

class AutoClipboard:
    def __init__(self, on_url_detected=None, check_interval=2.0):
        self.on_url_detected = on_url_detected
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        self._last_content = ""

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Auto-clipboard monitoring started")

    def stop(self):
        self._running = False

    def _monitor_loop(self):
        while self._running:
            try:
                import pyperclip
                content = pyperclip.paste()
                if content != self._last_content:
                    self._last_content = content
                    if validate_url(content):
                        logger.info(f"URL detected in clipboard: {content}")
                        if self.on_url_detected:
                            self.on_url_detected(content)
            except ImportError:
                logger.warning("pyperclip not installed, auto-clipboard disabled")
                self._running = False
            except Exception as e:
                logger.warning(f"Clipboard check failed: {e}")
            time.sleep(self.check_interval)
