"""Auto-organize plugin - organizes downloads by platform and date."""
import os
from pathlib import Path
from datetime import datetime
from src.plugins.api import PluginBase

class AutoOrganizePlugin(PluginBase):
    name = "Auto Organize"
    version = "1.0.0"
    description = "Organizes downloads by platform and date"
    enabled = True

    def on_download_complete(self, url, output_path):
        source_path = Path(output_path)
        if not source_path.exists() or source_path.is_dir():
            return
        platform = "other"
        if "youtube" in url or "youtu.be" in url:
            platform = "youtube"
        elif "twitch" in url:
            platform = "twitch"
        elif "vimeo" in url:
            platform = "vimeo"
        elif "soundcloud" in url:
            platform = "soundcloud"
        date_str = datetime.now().strftime("%Y-%m-%d")
        target_dir = source_path.parent / platform / date_str
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = source_path.name
        target_path = target_dir / filename
        os.replace(str(source_path), str(target_path))
        return str(target_path)
