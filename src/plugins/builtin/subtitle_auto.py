"""Auto-subtitle plugin - automatically downloads subtitles for videos."""
from pathlib import Path
from src.plugins.api import PluginBase

class AutoSubtitlePlugin(PluginBase):
    name = "Auto Subtitles"
    version = "1.0.0"
    description = "Automatically downloads subtitles for videos"
    enabled = True

    def on_download_complete(self, url, output_path):
        from src.services.subtitles import download_subtitles_separately
        output_dir = str(Path(output_path).parent)
        download_subtitles_separately({}, output_dir, languages=["en"])
        return output_path
