"""CLI search command."""

import sys
from typing import Any

from src.services.search import search_platform
from rich import print
from rich.table import Table
from rich.console import Console

console = Console()


def _safe_console_text(value: Any) -> str:
    """Return text that is safe for the current stdout encoding."""
    text = str(value)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except Exception:
        return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def search(query: str, platform: str = "youtube", max_results: int = 10) -> None:
    safe_platform = _safe_console_text(platform)
    safe_query = _safe_console_text(query)
    print(f"[bold blue]Searching {safe_platform} for: {safe_query}[/bold blue]")
    try:
        results = search_platform(query, platform, max_results)
    except Exception as exc:
        print(f"[bold red]Search failed:[/bold red] {_safe_console_text(exc)}")
        return
    if not results:
        print("[dim]No results found[/dim]")
        return
    table = Table(title=f"Search Results ({platform})")
    table.add_column("#", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Uploader", style="yellow")
    table.add_column("Duration", style="magenta")
    table.add_column("Views", style="blue")
    for i, r in enumerate(results, 1):
        duration_min = r.get("duration", 0) // 60
        views = r.get("view_count", 0)
        views_str = (
            f"{views / 1_000_000:.1f}M"
            if views > 1_000_000
            else f"{views / 1_000:.1f}K"
            if views > 1_000
            else str(views)
        )
        title = _safe_console_text(r.get("title", "Unknown"))[:50]
        uploader = _safe_console_text(r.get("uploader", "?"))
        table.add_row(str(i), title, uploader, f"{duration_min}m", views_str)
    console.print(table)
