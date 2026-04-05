"""Match filter service for advanced video filtering."""
import re
from src.utils.logger import get_logger
logger = get_logger(__name__)

def apply_match_filters(info, filters=None):
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
            except: pass
        elif "<=" in f:
            field, value = f.split("<=", 1)
            try:
                if (info.get(field.strip()) or 0) > float(value.strip()): return False
            except: pass
        elif ">" in f:
            field, value = f.split(">", 1)
            try:
                if (info.get(field.strip()) or 0) <= float(value.strip()): return False
            except: pass
        elif "<" in f:
            field, value = f.split("<", 1)
            try:
                if (info.get(field.strip()) or 0) >= float(value.strip()): return False
            except: pass
        elif "~=" in f:
            field, pattern = f.split("~=", 1)
            try:
                if not re.search(pattern.strip(), str(info.get(field.strip(), ""))):
                    return False
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}' in match filter: {e}")
                return False
    return True

def build_filter_opts(match_filters=None, break_filters=None):
    opts = {}
    if match_filters: opts["match_filter"] = match_filters
    if break_filters: opts["break_on_filter"] = break_filters
    return opts
