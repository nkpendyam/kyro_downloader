"""Automatic yt-dlp update checker."""
import sys
import subprocess
import importlib.metadata
from packaging import version
from src.utils.logger import get_logger
logger = get_logger(__name__)

def get_current_version():
    try:
        return importlib.metadata.version("yt-dlp")
    except Exception:
        return None

def get_latest_version():
    try:
        import requests
        r = requests.get("https://pypi.org/pypi/yt-dlp/json", timeout=10)
        r.raise_for_status()
        return r.json()["info"]["version"]
    except Exception as e:
        logger.warning(f"Failed to check yt-dlp version: {e}")
        return None

def check_for_update():
    current, latest = get_current_version(), get_latest_version()
    if not current or not latest:
        return {"update_available": False, "current": current, "latest": latest}
    return {"update_available": version.parse(latest) > version.parse(current), "current": current, "latest": latest}

def update_ytdlp():
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning(f"yt-dlp update failed: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp update timed out after 120s")
        return False
    except Exception as e:
        logger.error(f"yt-dlp update failed: {e}")
        return False

def auto_update_on_startup(check_only=True):
    from rich import print as rich_print
    status = check_for_update()
    if status.get("update_available"):
        if check_only:
            rich_print(f"[bold yellow]yt-dlp update available: {status['current']} -> {status['latest']}[/bold yellow]")
            rich_print("[dim]Run kyro --update to update[/dim]")
        else:
            rich_print(f"[bold blue]Auto-updating yt-dlp: {status['current']} -> {status['latest']}[/bold blue]")
            if update_ytdlp():
                rich_print("[bold green]yt-dlp updated![/bold green]")
            else:
                rich_print("[bold red]Update failed[/bold red]")
