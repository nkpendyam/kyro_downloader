"""Plugin system for Kyro Downloader.

The active plugin system is in src/plugins/loader.py (PluginLoader).
This module is kept for backward compatibility but delegates to PluginLoader.
"""

from src.plugins.loader import PluginLoader as PluginLoader
