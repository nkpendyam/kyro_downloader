"""Export/import settings service."""
import json
from pathlib import Path
from datetime import datetime
from src.utils.logger import get_logger
logger = get_logger(__name__)

class ExportImport:
    def __init__(self, config):
        self.config = config

    def export_settings(self, filepath=None):
        if not filepath:
            filepath = f"kyro_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.config.model_dump(), f, indent=2, ensure_ascii=False)
            logger.info(f"Settings exported to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None

    def import_settings(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            from src.config.schema import AppConfig
            config = AppConfig(**data)
            logger.info(f"Settings imported from: {filepath}")
            return config
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return None

    def backup_settings(self, backup_dir=None):
        if not backup_dir:
            backup_dir = Path.home() / ".config" / "kyro" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        filepath = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return self.export_settings(str(filepath))

    def restore_latest_backup(self, backup_dir=None):
        if not backup_dir:
            backup_dir = Path.home() / ".config" / "kyro" / "backups"
        if not backup_dir.exists(): return None
        backups = sorted(backup_dir.glob("backup_*.json"), reverse=True)
        if not backups: return None
        return self.import_settings(str(backups[0]))
