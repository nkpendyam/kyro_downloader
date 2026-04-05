# Plugin Development Guide

## Overview

Kyro Downloader supports a plugin system that allows extending functionality through hooks in the download lifecycle.

## Plugin Structure

```python
from src.plugins.api import PluginBase

class MyPlugin(PluginBase):
    name = "My Plugin"
    version = "1.0.0"
    description = "Does something useful"
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
```

## Hook Lifecycle

1. `on_download_start` - Before yt-dlp begins downloading
2. `on_download_progress` - During download (called multiple times)
3. `on_download_complete` - After successful download
4. `on_download_error` - If download fails

## Builtin Plugins

| Plugin | Description |
|--------|-------------|
| Auto Compress | Compresses videos over 500MB |
| Auto Convert | Converts downloads to target format |
| Auto Organize | Organizes by platform and date |
| Auto Thumbnail | Downloads media thumbnails automatically |
| Auto Subtitles | Downloads subtitles automatically |

## Installing User Plugins

Place `.py` files in `~/.config/kyro/plugins/` and they will be auto-discovered.

## Managing Plugins

```bash
kyro plugins list           # List all plugins
kyro plugins enable <name>  # Enable a plugin
kyro plugins disable <name> # Disable a plugin
kyro plugins info <name>    # Show plugin details
```

Plugins can also be managed from the GUI Settings tab.
