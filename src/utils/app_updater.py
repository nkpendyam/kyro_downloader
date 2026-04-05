"""Auto-updater for Kyro Downloader using GitHub Releases."""
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from packaging import version
from src.utils.logger import get_logger

logger = get_logger(__name__)

GITHUB_API = "https://api.github.com/repos/nkpendyam/kyro_downloader"
CURRENT_VERSION = "2.0.0"


def get_current_version():
    try:
        from src import __version__
        return __version__
    except ImportError:
        return CURRENT_VERSION


def get_latest_release():
    import requests
    try:
        resp = requests.get(f"{GITHUB_API}/releases/latest", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "tag_name": data["tag_name"].lstrip("v"),
                "name": data["name"],
                "body": data["body"],
                "html_url": data["html_url"],
                "assets": [
                    {"name": a["name"], "url": a["browser_download_url"], "size": a["size"]}
                    for a in data.get("assets", [])
                ],
            }
    except Exception as e:
        logger.warning(f"Failed to check for updates: {e}")
    return None


def check_for_update():
    current = get_current_version()
    latest = get_latest_release()
    if not latest:
        return {"update_available": False, "current": current, "latest": "unknown"}
    latest_ver = latest["tag_name"]
    try:
        has_update = version.parse(latest_ver) > version.parse(current)
    except Exception:
        has_update = latest_ver != current
    return {
        "update_available": has_update,
        "current": current,
        "latest": latest_ver,
        "release_name": latest["name"],
        "release_notes": latest["body"],
        "download_url": latest["html_url"],
        "assets": latest["assets"],
    }


def get_platform_asset(assets):
    """Find the right download asset for the current platform."""
    platform = sys.platform
    if platform == "win32":
        for a in assets:
            if a["name"].endswith(".exe"):
                return a
    elif platform == "darwin":
        for a in assets:
            if a["name"].endswith(".dmg"):
                return a
    elif platform == "linux":
        for a in assets:
            if a["name"].endswith(".AppImage"):
                return a
    return None


def download_and_update(asset_url):
    """Download the latest release and launch the installer."""
    import requests
    try:
        resp = requests.get(asset_url, stream=True, timeout=300)
        resp.raise_for_status()
        filename = asset_url.split("/")[-1]
        tmp_path = Path(tempfile.gettempdir()) / filename
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded update to {tmp_path}")
        return str(tmp_path)
    except Exception as e:
        logger.error(f"Failed to download update: {e}")
        return None


def launch_installer(installer_path):
    """Launch the downloaded installer."""
    platform = sys.platform
    try:
        if platform == "win32":
            os.startfile(installer_path)
        elif platform == "darwin":
            subprocess.run(["open", installer_path])
        elif platform == "linux":
            os.chmod(installer_path, 0o755)
            subprocess.Popen([installer_path])
        return True
    except Exception as e:
        logger.error(f"Failed to launch installer: {e}")
        return False


def auto_update():
    """Full auto-update flow: check, download, install."""
    status = check_for_update()
    if not status["update_available"]:
        logger.info("Kyro Downloader is up to date")
        return False
    logger.info(f"Update available: {status['latest']}")
    asset = get_platform_asset(status.get("assets", []))
    if not asset:
        logger.warning("No suitable update asset found for this platform")
        return False
    installer_path = download_and_update(asset["url"])
    if not installer_path:
        return False
    return launch_installer(installer_path)


if __name__ == "__main__":
    status = check_for_update()
    if status["update_available"]:
        print(f"Update available: {status['latest']}")
        print(f"Release: {status.get('release_name', '')}")
        print(f"Notes: {status.get('release_notes', '')}")
        print(f"Download: {status['download_url']}")
    else:
        print(f"Up to date (v{status['current']})")
