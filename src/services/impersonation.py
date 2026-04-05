"""Browser impersonation service."""
from src.utils.logger import get_logger
logger = get_logger(__name__)

BROWSER_TARGETS = {
    "chrome": {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    "firefox": {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"},
    "safari": {"user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"},
    "edge": {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"},
}

def get_impersonation_headers(browser="chrome"):
    config = BROWSER_TARGETS.get(browser, BROWSER_TARGETS["chrome"])
    return {"User-Agent": config["user_agent"]}

def build_impersonation_opts(browser=None):
    opts = {}
    if browser:
        config = BROWSER_TARGETS.get(browser, BROWSER_TARGETS["chrome"])
        opts["user_agent"] = config["user_agent"]
    return opts
