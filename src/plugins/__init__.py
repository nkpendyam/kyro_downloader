"""Plugin system for Kyro Downloader."""
import os
import importlib
import importlib.util
from src.utils.logger import get_logger
logger = get_logger(__name__)

class PluginManager:
    def __init__(self, plugin_dirs=None):
        self.plugin_dirs = plugin_dirs or [os.path.join(os.path.dirname(__file__), "builtin")]
        self.plugins = {}

    def discover_plugins(self):
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir): continue
            for filename in os.listdir(plugin_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    plugin_name = filename[:-3]
                    plugin_path = os.path.join(plugin_dir, filename)
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "register"):
                        plugin_info = module.register()
                        self.plugins[plugin_name] = {"module": module, "info": plugin_info}
                        logger.info(f"Plugin loaded: {plugin_name}")
        return self.plugins

    def get_plugin(self, name):
        return self.plugins.get(name)

    def list_plugins(self):
        return {name: info["info"] for name, info in self.plugins.items()}
