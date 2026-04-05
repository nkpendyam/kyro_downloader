"""Auto-subtitle plugin - automatically downloads subtitles for videos."""
from pathlib import Path

from src.plugins.api import PluginBase
from src.core.downloader import get_video_info
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AutoSubtitlePlugin(PluginBase):
    name = "Auto Subtitles"
    version = "1.0.0"
    description = "Automatically downloads subtitles for videos"
    enabled = True

    def on_download_complete(self, url, output_path):
        from src.services.subtitles import download_subtitles_separately

        target = Path(output_path)
        output_dir = str(target if target.is_dir() else target.parent)
        try:
            info = get_video_info(url)
            download_subtitles_separately(info.raw, output_dir, languages=["en"])
        except Exception as exc:
            logger.warning(f"Auto subtitle fetch failed for {url}: {exc}")
        return output_path
