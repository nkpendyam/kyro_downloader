"""Input validation utilities."""

import os
import ipaddress
from pathlib import Path
from urllib.parse import urlparse


def _supported_platforms() -> list[str]:
    from src.utils.platform import PLATFORM_CONFIG

    return list(PLATFORM_CONFIG.keys())


def validate_url(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.hostname
    if not host:
        return False
    allow_private = os.environ.get("KYRO_ALLOW_PRIVATE_IPS", "").lower() in ("1", "true", "yes")
    if allow_private:
        return True
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
        return True
    except ValueError:
        pass
    if "." not in host:
        return False
    return True


def validate_platform(url: str | None) -> str | None:
    if not validate_url(url):
        return None
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        for p in _supported_platforms():
            if domain == p or domain.endswith(f".{p}"):
                return p
    except Exception:
        pass
    return None


def validate_output_path(path: str | None) -> Path:
    if not path or not path.strip():
        path = os.path.join(os.getcwd(), "downloads")
    output_path = Path(path).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def validate_integer(value: str | None, min_val: int | None = None, max_val: int | None = None) -> int | None:
    try:
        num = int(value)
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
        return num
    except (ValueError, TypeError):
        return None


def sanitize_filename(filename: str, output_dir: str | Path | None = None) -> str:
    invalid = '<>:"/\\|?*'
    sanitized = "".join("_" if ch in invalid or ord(ch) < 32 else ch for ch in filename).strip()
    if not sanitized:
        return "untitled"
    max_len = 200
    if output_dir is not None:
        dir_len = len(str(output_dir))
        max_path = 260
        max_len = min(200, max(10, max_path - dir_len - 10))
    return sanitized[:max_len]


def validate_batch_file(filepath: str) -> list[str]:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Batch file not found: {filepath}")
    urls = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and validate_url(line):
                    urls.append(line)
    except PermissionError as e:
        raise PermissionError(f"Cannot read batch file: {filepath}") from e
    return urls
