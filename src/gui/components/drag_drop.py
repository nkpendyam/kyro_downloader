"""Drag and drop URL support for GUI."""
import os
from pathlib import Path

from src.utils.logger import get_logger
logger = get_logger(__name__)

class DragDropHandler:
    def __init__(self, on_url_dropped=None) -> None:
        self.on_url_dropped = on_url_dropped
        self.supported_extensions = [".url", ".txt", ".m3u8"]

    def handle_drop(self, file_path: str) -> list[str]:
        if not file_path or not os.path.exists(file_path):
            return []
        urls: list[str] = []
        try:
            with Path(file_path).open("r", encoding="utf-8") as f:
                content = f.read()
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("http"):
                    urls.append(line)
                elif line.startswith("URL="):
                    urls.append(line[4:])
        except (OSError, UnicodeDecodeError):
            if file_path.startswith("http"):
                urls.append(file_path)
        if self.on_url_dropped and urls:
            self.on_url_dropped(urls)
        return urls

    def handle_text_drop(self, text: str) -> list[str]:
        urls: list[str] = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("http"):
                urls.append(line)
        if self.on_url_dropped and urls:
            self.on_url_dropped(urls)
        return urls
