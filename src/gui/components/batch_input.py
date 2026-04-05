"""Batch URL input component."""
from src.utils.validation import validate_url
from src.utils.logger import get_logger
logger = get_logger(__name__)

class BatchInput:
    def __init__(self):
        self.urls = []

    def parse_input(self, text):
        self.urls = []
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and validate_url(line):
                self.urls.append(line)
        return self.urls

    def load_from_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return self.parse_input(f.read())
        except Exception as e:
            logger.error(f"Failed to load batch file: {e}")
            return []

    def get_urls(self):
        return self.urls

    def clear(self):
        self.urls = []
