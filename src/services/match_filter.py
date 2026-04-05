"""Match filter service for advanced video filtering."""
from typing import Any

import re
from src.utils.logger import get_logger
logger = get_logger(__name__)

def apply_match_filters(info: dict[str, Any], filters: list[str] | None = None) -> bool:
    if not filters: return True
    for f in filters:
        f = f.strip()
        if not f: continue
        if f.startswith("!"):
            field = f[1:]
            if info.get(field): return False
        elif "==" in f:
            field, value = f.split("==", 1)
            if str(info.get(field.strip())) != value.strip(): return False
        elif "!=" in f:
            field, value = f.split("!=", 1)
            if str(info.get(field.strip())) == value.strip(): return False
        elif ">=" in f:
            field, value = f.split(">=", 1)
            try:
                if (info.get(field.strip()) or 0) < float(value.strip()): return False
            except (TypeError, ValueError):
                pass
        elif "<=" in f:
            field, value = f.split("<=", 1)
            try:
                if (info.get(field.strip()) or 0) > float(value.strip()): return False
            except (TypeError, ValueError):
                pass
        elif ">" in f:
            field, value = f.split(">", 1)
            try:
                if (info.get(field.strip()) or 0) <= float(value.strip()): return False
            except (TypeError, ValueError):
                pass
        elif "<" in f:
            field, value = f.split("<", 1)
            try:
                if (info.get(field.strip()) or 0) >= float(value.strip()): return False
            except (TypeError, ValueError):
                pass
        elif "~=" in f:
            field, pattern = f.split("~=", 1)
            try:
                if not re.search(pattern.strip(), str(info.get(field.strip(), ""))):
                    return False
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}' in match filter: {e}")
                return False
    return True

def build_filter_opts(match_filters: list[str] | None = None, break_filters: list[str] | None = None) -> dict[str, list[str]]:
    opts: dict[str, list[str]] = {}
    if match_filters: opts["match_filter"] = match_filters
    if break_filters: opts["break_on_filter"] = break_filters
    return opts
