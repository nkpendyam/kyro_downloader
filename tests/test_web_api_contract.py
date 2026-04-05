"""Contract tests to keep Web API docs and routes in sync."""

import re
from typing import Any, cast

import pytest

pytest.importorskip("fastapi", reason="Web UI optional dependency")

from src.ui.web.server import create_app


def _normalize_path(path: str) -> str:
    """Strip query string and normalize trailing slash for contract checks."""
    base = path.split("?", 1)[0]
    if base != "/" and base.endswith("/"):
        return base[:-1]
    return base


def _parse_doc_http_endpoints(markdown: str) -> set[tuple[str, str]]:
    pattern = re.compile(r"\|\s*(GET|POST|PUT|DELETE)\s*\|\s*`([^`]+)`")
    endpoints: set[tuple[str, str]] = set()
    for method, path in pattern.findall(markdown):
        endpoints.add((method, _normalize_path(path)))
    return endpoints


def _parse_doc_ws_endpoints(markdown: str) -> set[str]:
    pattern = re.compile(r"- `GET\s+(/ws/[^`]+)`")
    return {_normalize_path(path) for path in pattern.findall(markdown)}


def test_web_api_docs_match_runtime_contract() -> None:
    """docs/web_api.md should describe the actual runtime API and websocket routes."""
    app = cast(Any, create_app())

    with open("docs/web_api.md", "r", encoding="utf-8") as handle:
        markdown = handle.read()

    documented_http = _parse_doc_http_endpoints(markdown)
    documented_ws = _parse_doc_ws_endpoints(markdown)

    runtime_http: set[tuple[str, str]] = set()
    runtime_ws: set[str] = set()

    routes = cast(list[Any], getattr(app, "routes", []))
    for route in routes:
        path = _normalize_path(getattr(route, "path", ""))
        if not path:
            continue
        methods = getattr(route, "methods", None)
        if methods and path.startswith("/api"):
            for method in methods:
                if method in {"GET", "POST", "PUT", "DELETE"}:
                    runtime_http.add((method, path))
            continue
        if path.startswith("/ws"):
            runtime_ws.add(path)

    assert documented_http == runtime_http
    assert documented_ws == runtime_ws
