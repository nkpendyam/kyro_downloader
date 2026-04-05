"""Keyboard shortcuts handler."""
from src.utils.logger import get_logger
logger = get_logger(__name__)

SHORTCUTS = {
    "Ctrl+N": "new_download",
    "Ctrl+O": "open_batch_file",
    "Ctrl+S": "save_settings",
    "Ctrl+P": "pause_download",
    "Ctrl+R": "resume_download",
    "Ctrl+D": "delete_download",
    "Ctrl+F": "search_downloads",
    "Ctrl+T": "toggle_theme",
    "Ctrl+W": "close_window",
    "F5": "refresh",
    "F1": "help",
    "Escape": "cancel",
    "Delete": "delete_selected",
    "Enter": "start_download",
}

class KeyboardShortcuts:
    def __init__(self, handlers=None):
        self.handlers = handlers or {}

    def register(self, shortcut, handler):
        SHORTCUTS[shortcut] = handler.__name__
        self.handlers[shortcut] = handler

    def handle(self, shortcut):
        if shortcut in self.handlers:
            self.handlers[shortcut]()
            return True
        return False

    def get_shortcuts(self):
        return SHORTCUTS
