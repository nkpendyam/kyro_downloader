"""Desktop notifications."""
import platform
import subprocess
from src.utils.logger import get_logger
logger = get_logger(__name__)

def send_notification(title, message, urgency="normal"):
    system = platform.system()
    try:
        if system == "Windows":
            from plyer import notification
            notification.notify(title=title, message=message, app_name="Kyro Downloader", timeout=10)
        elif system == "Darwin":
            # Use stdin to prevent command injection via title/message
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, timeout=5, check=True,
                input=message.encode()
            )
        else:
            subprocess.run(
                ["notify-send", "-u", urgency, "-a", "Kyro Downloader", title, message],
                capture_output=True, timeout=5, check=True
            )
        return True
    except Exception as e:
        logger.warning(f"Notification failed: {e}")
        try:
            from rich import print as rich_print
            rich_print(f"[bold blue][NOTIFICATION] {title}:[/bold blue] {message}")
        except Exception:
            print(f"[NOTIFICATION] {title}: {message}")
        return False

def notify_download_complete(video_title, output_path):
    return send_notification("Download Complete", f"{video_title}\nSaved to: {output_path}")

def notify_download_failed(video_title, error):
    return send_notification("Download Failed", f"{video_title}\nError: {error}", urgency="critical")

def notify_playlist_complete(playlist_title, count):
    return send_notification("Playlist Complete", f"{playlist_title}\n{count} videos downloaded")
