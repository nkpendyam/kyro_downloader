"""Cookie extraction from browsers service."""
import os
import sys
from src.utils.logger import get_logger
logger = get_logger(__name__)

SUPPORTED_BROWSERS = ["chrome", "firefox", "edge", "brave", "opera", "safari"]

def get_browser_cookies_path(browser):
    browser = browser.lower()
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        roaming = os.environ.get("APPDATA", "")
        paths = {
            "chrome": os.path.join(local, "Google", "Chrome", "User Data", "Default", "Network", "Cookies"),
            "edge": os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Network", "Cookies"),
            "firefox": os.path.join(roaming, "Mozilla", "Firefox", "Profiles"),
        }
        return paths.get(browser)
    elif sys.platform == "darwin":
        paths = {
            "chrome": os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),
            "firefox": os.path.expanduser("~/Library/Application Support/Firefox/Profiles"),
            "safari": os.path.expanduser("~/Library/Cookies"),
        }
        return paths.get(browser)
    else:
        paths = {
            "chrome": os.path.expanduser("~/.config/google-chrome/Default/Cookies"),
            "firefox": os.path.expanduser("~/.mozilla/firefox"),
        }
        return paths.get(browser)

def extract_cookies_to_netscape(browser, output_file=None):
    cookies_path = get_browser_cookies_path(browser)
    if not cookies_path or not os.path.exists(cookies_path):
        logger.error(f"Cookies not found for {browser}")
        return None
    if not output_file:
        output_file = f"{browser}_cookies.txt"
    logger.info(f"Extracting cookies from {browser} to {output_file}")
    logger.warning("Cookies extraction from SQLite DB requires browser to be closed")
    logger.warning(f"Use yt-dlp's --cookies-from-browser option instead: yt-dlp --cookies-from-browser {browser}")
    return output_file

def get_cookies_from_browser_cmd(browser):
    return f"--cookies-from-browser {browser}"
