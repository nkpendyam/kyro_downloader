"""Plugin API - base class for all plugins."""

class PluginBase:
    """Base class for all plugins."""
    name = ""
    version = ""
    description = ""
    enabled = True

    def on_download_start(self, url, config):
        """Called before download starts."""
        pass

    def on_download_progress(self, url, progress, speed):
        """Called during download."""
        pass

    def on_download_complete(self, url, output_path):
        """Called after download completes."""
        pass

    def on_download_error(self, url, error):
        """Called on download failure."""
        pass
