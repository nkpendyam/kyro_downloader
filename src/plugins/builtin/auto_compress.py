"""Auto-compress plugin - automatically compresses large video files."""
from src.plugins.api import PluginBase

class AutoCompressPlugin(PluginBase):
    name = "Auto Compress"
    version = "1.0.0"
    description = "Automatically compresses videos over size threshold"
    enabled = True

    def on_download_complete(self, url, output_path):
        import os
        threshold = 500 * 1024 * 1024  # 500MB
        if not os.path.exists(output_path):
            return
        if os.path.getsize(output_path) < threshold:
            return
        from src.services.compressor import compress_video
        result = compress_video(output_path, quality="medium")
        if result and result.get("output"):
            return result["output"]
