"""Auto-convert plugin - automatically converts downloads to preferred format."""
from pathlib import Path

from src.plugins.api import PluginBase

class AutoConvertPlugin(PluginBase):
    name = "Auto Convert"
    version = "1.0.0"
    description = "Automatically converts downloads to preferred format"
    enabled = True

    def on_download_complete(self, url, output_path):
        target_format = "mp4"
        target = Path(output_path)
        if not target.exists() or target.is_dir():
            return
        ext = target.suffix.lstrip(".").lower()
        if ext == target_format:
            return
        from src.services.converter import convert_file

        converted = convert_file(str(target), target_format)
        if converted:
            return converted
