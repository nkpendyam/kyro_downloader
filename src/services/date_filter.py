"""Date filtering service."""

from datetime import datetime, timedelta
from src.utils.logger import get_logger
logger = get_logger(__name__)

def parse_date(date_str: str | None) -> str | None:
    if not date_str: return None
    if date_str == "today": return datetime.now().strftime("%Y%m%d")
    if date_str == "yesterday": return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    if date_str.startswith("now-"):
        parts = date_str[4:].split("day")[0]
        try:
            days = int(parts)
            return (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        except ValueError:
            pass
    if len(date_str) == 8 and date_str.isdigit(): return date_str
    return None

def is_date_in_range(upload_date: str | None, dateafter: str | None = None, datebefore: str | None = None) -> bool:
    if not upload_date: return True
    if dateafter and upload_date < dateafter: return False
    if datebefore and upload_date > datebefore: return False
    return True

def build_date_opts(date: str | None = None, dateafter: str | None = None, datebefore: str | None = None) -> dict[str, str]:
    opts: dict[str, str] = {}
    if date: opts["date"] = parse_date(date)
    if dateafter: opts["dateafter"] = parse_date(dateafter)
    if datebefore: opts["datebefore"] = parse_date(datebefore)
    return opts
