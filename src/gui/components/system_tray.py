"""System tray integration."""
from src.utils.logger import get_logger
logger = get_logger(__name__)

class SystemTray:
    def __init__(self, on_show=None, on_quit=None, on_download=None):
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_download = on_download

    def create_tray(self):
        try:
            logger.info("System tray available")
            return True
        except ImportError:
            logger.warning("plyer not installed, system tray unavailable")
            return False

    def show_notification(self, title, message):
        try:
            from plyer import notification
            notification.notify(title=title, message=message, app_name="Kyro Downloader", timeout=10)
        except Exception as e:
            logger.warning(f"System tray notification failed: {e}")

    def minimize_to_tray(self):
        logger.info("Minimized to system tray")

    def restore_from_tray(self):
        logger.info("Restored from system tray")
        if self.on_show: self.on_show()
