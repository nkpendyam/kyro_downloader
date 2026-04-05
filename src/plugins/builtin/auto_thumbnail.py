"""Auto-thumbnail plugin - downloads thumbnail for completed media."""
from pathlib import Path

from src.plugins.api import PluginBase
from src.core.downloader import get_video_info
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AutoThumbnailPlugin(PluginBase):
    """Save a media thumbnail next to downloaded files."""

    name = "Auto Thumbnail"
    version = "1.0.0"
    description = "Automatically downloads media thumbnails after completion"
    enabled = True

    def on_download_complete(self, url, output_path):
        from src.services.thumbnails import download_thumbnail

        target = Path(output_path)
        output_dir = target if target.is_dir() else target.parent
        filename = target.stem if target.is_file() else "thumbnail"

        try:
            info = get_video_info(url)
            thumbnail_url = getattr(info, "thumbnail", None)
            if not thumbnail_url:
                return output_path
            download_thumbnail(thumbnail_url, str(output_dir), filename=filename)
        except Exception as exc:
            logger.warning(f"Auto thumbnail failed for {url}: {exc}")
        return output_path
