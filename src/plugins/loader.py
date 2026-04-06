"""Plugin loader - auto-discovers and manages plugins."""

import importlib
import importlib.util
from pathlib import Path
from typing import Any
from src.plugins.api import PluginBase, PLUGIN_API_VERSION
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Only these builtin plugins are allowed by default
ALLOWED_BUILTIN_PLUGINS = {"auto_compress", "auto_convert", "auto_organize", "auto_thumbnail", "subtitle_auto"}


def _is_api_compatible(plugin_api_version: str) -> bool:
    """Check if a plugin's API version is compatible with the host API version."""
    try:
        plugin_major = int(plugin_api_version.split(".")[0])
        host_major = int(PLUGIN_API_VERSION.split(".")[0])
        if plugin_major != host_major:
            return False
        return True
    except (ValueError, IndexError):
        return False


class PluginLoader:
    def __init__(self, allow_user_plugins: bool = False) -> None:
        self._plugins: dict[str, PluginBase] = {}
        self._allow_user_plugins = allow_user_plugins
        self._discover_builtin()
        if self._allow_user_plugins:
            self._discover_user()

    def _discover_builtin(self) -> None:
        """Auto-discover plugins from src/plugins/builtin/"""
        builtin_dir = Path(__file__).parent / "builtin"
        if not builtin_dir.exists():
            return
        for f in builtin_dir.glob("*.py"):
            if f.stem != "__init__" and f.stem in ALLOWED_BUILTIN_PLUGINS:
                self._load_plugin(f, f"builtin.{f.stem}")

    def _discover_user(self) -> None:
        """Discover user plugins from ~/.config/kyro/plugins/ (disabled by default)"""
        user_dir = Path.home() / ".config" / "kyro" / "plugins"
        if not user_dir.exists():
            return
        for f in user_dir.glob("*.py"):
            if f.stem != "__init__":
                self._load_plugin(f, f"user.{f.stem}")

    def _load_plugin(self, filepath: Path, module_name: str) -> None:
        """Load a plugin module and register it."""
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                return
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
                    plugin = attr()
                    plugin_api_version = getattr(plugin, "expected_api_version", None)
                    if plugin_api_version and not _is_api_compatible(plugin_api_version):
                        logger.warning(
                            f"Skipping plugin {plugin.name or attr_name}: "
                            f"API version {plugin_api_version} incompatible with host {PLUGIN_API_VERSION}"
                        )
                        continue
                    self._plugins[plugin.name or attr_name] = plugin
                    logger.info(f"Loaded plugin: {plugin.name or attr_name} v{plugin.version}")
        except Exception as e:
            logger.warning(f"Failed to load plugin {module_name}: {e}")

    def fire_hook(self, hook_name: str, **kwargs: Any) -> None:
        """Fire a plugin hook across all enabled plugins."""
        for name, plugin in self._plugins.items():
            if plugin.enabled and hasattr(plugin, hook_name):
                try:
                    getattr(plugin, hook_name)(**kwargs)
                except Exception as e:
                    logger.error(f"Plugin {name} hook {hook_name} failed: {e}")

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return list of all plugins with their status."""
        result = []
        for name, plugin in self._plugins.items():
            result.append(
                {
                    "name": name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "enabled": plugin.enabled,
                }
            )
        return result

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin by name."""
        if name in self._plugins:
            self._plugins[name].enabled = True
            logger.info(f"Enabled plugin: {name}")
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin by name."""
        if name in self._plugins:
            self._plugins[name].enabled = False
            logger.info(f"Disabled plugin: {name}")
            return True
        return False

    def get_plugin(self, name: str) -> PluginBase | None:
        """Get a plugin by name."""
        return self._plugins.get(name)
