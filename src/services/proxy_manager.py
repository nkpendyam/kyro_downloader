"""Proxy rotation manager."""

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ProxyManager:
    def __init__(self, proxies: list[str] | None = None) -> None:
        self._proxies = proxies or []
        self._current_index = 0
        self._working: list[str] = []

    def add_proxy(self, proxy_url: str) -> None:
        self._proxies.append(proxy_url)

    def add_proxies_from_file(self, filepath: str) -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and not proxy.startswith("#"):
                        self._proxies.append(proxy)
        except OSError as e:
            logger.warning(f"Failed to load proxies from {filepath}: {e}")

    def get_next_proxy(self) -> str | None:
        if not self._working:
            self._test_proxies()
        if not self._working:
            return None
        proxy = self._working[self._current_index % len(self._working)]
        self._current_index += 1
        return proxy

    def _test_proxies(self, timeout: int = 5) -> None:
        self._working = []
        for proxy in self._proxies:
            try:
                proxies = {"http": proxy, "https": proxy}
                response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=timeout)
                if response.status_code == 200:
                    self._working.append(proxy)
                    logger.info(f"Working proxy: {proxy}")
            except Exception:
                logger.debug(f"Failed proxy: {proxy}")

    def get_working_count(self) -> int:
        return len(self._working)

    def get_total_count(self) -> int:
        return len(self._proxies)
