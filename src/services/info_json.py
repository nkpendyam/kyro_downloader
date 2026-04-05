"""Write video info as JSON service."""
from typing import Any

import json
import os
from src.utils.logger import get_logger
logger = get_logger(__name__)

def write_info_json(info: dict[str, Any], output_dir: str) -> str | None:
    title = info.get("title", "unknown").replace("/", "_").replace("\\", "_")
    video_id = info.get("id", "unknown")
    filename = f"{title} [{video_id}].info.json"
    filepath = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Info JSON written: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to write info JSON: {e}")
        return None

def write_description(info: dict[str, Any], output_dir: str) -> str | None:
    title = info.get("title", "unknown").replace("/", "_").replace("\\", "_")
    video_id = info.get("id", "unknown")
    description = info.get("description", "")
    if not description: return None
    filename = f"{title} [{video_id}].description.txt"
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(description)
        logger.info(f"Description written: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to write description: {e}")
        return None

def write_annotations(info: dict[str, Any], output_dir: str) -> str | None:
    annotations = info.get("annotations", "")
    if not annotations: return None
    title = info.get("title", "unknown").replace("/", "_").replace("\\", "_")
    video_id = info.get("id", "unknown")
    filename = f"{title} [{video_id}].annotations.xml"
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(annotations))
        return filepath
    except Exception as e:
        logger.warning(f"Failed to write annotations: {e}")
        return None
