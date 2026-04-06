"""Duplicate download detection."""

import hashlib
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_file_hash(filepath: str, algorithm: str = "sha256", chunk_size: int = 8192) -> str | None:
    hasher = hashlib.new(algorithm)
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        logger.warning(f"Cannot hash file {filepath}: {e}")
        return None
    return hasher.hexdigest()


def check_duplicate(output_path: str, title: str, ext: str = "mp4") -> tuple[Path, str | None] | None:
    candidate = Path(output_path) / f"{title}.{ext}"
    if candidate.exists():
        logger.warning(f"Duplicate file found: {candidate}")
        candidate_hash = get_file_hash(str(candidate))
        return candidate, candidate_hash
    return None


def generate_unique_filename(output_path: str, title: str, ext: str = "mp4") -> str:
    base = f"{title}.{ext}"
    candidate = Path(output_path) / base
    if not candidate.exists():
        return base
    counter = 1
    while True:
        candidate = Path(output_path) / f"{title} ({counter}).{ext}"
        if not candidate.exists():
            return f"{title} ({counter}).{ext}"
        counter += 1
