"""Plugin API - base class for all plugins."""

PLUGIN_API_VERSION = "1.0.0"


class PluginBase:
    """Base class for all plugins."""

    name = ""
    version = ""
    description = ""
    enabled = True
    expected_api_version: str = PLUGIN_API_VERSION

    def on_download_start(self, url: str, config: dict) -> None:
        """Called before download starts."""
        pass

    def on_download_progress(self, url: str, progress: float, speed: float) -> None:
        """Called during download."""
        pass

    def on_download_complete(self, url: str, output_path: str) -> None:
        """Called after download completes."""
        pass

    def on_download_error(self, url: str, error: str) -> None:
        """Called on download failure."""
        pass
