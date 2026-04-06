"""Configuration loading, merging, and saving."""

import copy
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from src.config.defaults import DEFAULT_CONFIG
from src.config.schema import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)

CONFIG_DIRS = [Path.home() / ".config" / "kyro", Path.home() / ".kyro", Path.cwd() / "config"]


class ConfigValidationError(ValueError):
    """Raised when application configuration fails validation."""


class ConfigSaveError(OSError):
    """Raised when configuration cannot be persisted to disk."""


def validate_config(config_dict):
    """Validate raw config mapping and return parsed app config."""
    try:
        return AppConfig(**config_dict)
    except Exception as e:
        raise ConfigValidationError(str(e)) from e


def deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def find_config_file():
    for config_dir in CONFIG_DIRS:
        for ext in ("yaml", "yml"):
            candidate = config_dir / f"config.{ext}"
            if candidate.exists():
                return candidate
    return None


def load_config_file(filepath):
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_env_config():
    load_dotenv()
    config = {}
    prefix = "KYRO_"
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("__")
        current = config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = _parse_env_value(value)
    return config


def _parse_env_value(value):
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    if value.lower() == "none":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def load_config(config_path=None):
    config = copy.deepcopy(DEFAULT_CONFIG)
    if config_path:
        file_config = load_config_file(config_path)
        config = deep_merge(config, file_config)
        logger.info(f"Loaded config from: {config_path}")
    else:
        found = find_config_file()
        if found:
            file_config = load_config_file(found)
            config = deep_merge(config, file_config)
            logger.info(f"Loaded config from: {found}")
    env_config = load_env_config()
    if env_config:
        config = deep_merge(config, env_config)
        logger.debug("Applied environment variable overrides")
    try:
        return validate_config(config)
    except ConfigValidationError as e:
        logger.error(f"Config validation failed: {e}")
        raise


def save_config(config, filepath=None):
    if not filepath:
        filepath = Path.home() / ".config" / "kyro" / "config.yaml"
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    config_dict = config.model_dump()
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    except OSError as e:
        logger.error(f"Failed to save configuration to {path}: {e}")
        raise ConfigSaveError(f"Failed to save configuration to {path}: {e}") from e
    logger.info(f"Configuration saved to: {path}")
    return path


def get_default_config_path():
    return Path.home() / ".config" / "kyro" / "config.yaml"
