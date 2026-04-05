"""Plugin loader - auto-discovers and manages plugins."""
import importlib
import importlib.util
from pathlib import Path
from src.plugins.api import PluginBase
from src.utils.logger import get_logger
logger = get_logger(__name__)

# Only these builtin plugins are allowed by default
ALLOWED_BUILTIN_PLUGINS = {"auto_compress", "auto_convert", "auto_organize", "subtitle_auto"}

class PluginLoader:
    def __init__(self, allow_user_plugins=False):
        self._plugins = {}
        self._allow_user_plugins = allow_user_plugins
        self._discover_builtin()
        if self._allow_user_plugins:
            self._discover_user()

    def _discover_builtin(self):
        """Auto-discover plugins from src/plugins/builtin/"""
        builtin_dir = Path(__file__).parent / "builtin"
        if not builtin_dir.exists():
            return
        for f in builtin_dir.glob("*.py"):
            if f.stem != "__init__" and f.stem in ALLOWED_BUILTIN_PLUGINS:
                self._load_plugin(f, f"builtin.{f.stem}")

    def _discover_user(self):
        """Discover user plugins from ~/.config/kyro/plugins/ (disabled by default)"""
        user_dir = Path.home() / ".config" / "kyro" / "plugins"
        if not user_dir.exists():
            return
        for f in user_dir.glob("*.py"):
            if f.stem != "__init__":
                self._load_plugin(f, f"user.{f.stem}")

    def _load_plugin(self, filepath, module_name):
        """Load a plugin module and register it."""
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and issubclass(attr, PluginBase)
                        and attr is not PluginBase):
                    plugin = attr()
                    self._plugins[plugin.name or attr_name] = plugin
                    logger.info(f"Loaded plugin: {plugin.name or attr_name} v{plugin.version}")
        except Exception as e:
            logger.warning(f"Failed to load plugin {module_name}: {e}")

    def fire_hook(self, hook_name, **kwargs):
        """Fire a plugin hook across all enabled plugins."""
        for name, plugin in self._plugins.items():
            if plugin.enabled and hasattr(plugin, hook_name):
                try:
                    getattr(plugin, hook_name)(**kwargs)
                except Exception as e:
                    logger.error(f"Plugin {name} hook {hook_name} failed: {e}")

    def list_plugins(self):
        """Return list of all plugins with their status."""
        result = []
        for name, plugin in self._plugins.items():
            result.append({
                "name": name,
                "version": plugin.version,
                "description": plugin.description,
                "enabled": plugin.enabled,
            })
        return result

    def enable_plugin(self, name):
        """Enable a plugin by name."""
        if name in self._plugins:
            self._plugins[name].enabled = True
            logger.info(f"Enabled plugin: {name}")
            return True
        return False

    def disable_plugin(self, name):
        """Disable a plugin by name."""
        if name in self._plugins:
            self._plugins[name].enabled = False
            logger.info(f"Disabled plugin: {name}")
            return True
        return False

    def get_plugin(self, name):
        """Get a plugin by name."""
        return self._plugins.get(name)
