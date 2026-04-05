"""CLI search command."""
from src.services.search import search_platform
from rich import print
from rich.table import Table
from rich.console import Console

console = Console()

def search(query, platform="youtube", max_results=10):
    print(f"[bold blue]Searching {platform} for: {query}[/bold blue]")
    results = search_platform(query, platform, max_results)
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
        views_str = f"{views/1_000_000:.1f}M" if views > 1_000_000 else f"{views/1_000:.1f}K" if views > 1_000 else str(views)
        table.add_row(str(i), r["title"][:50], r.get("uploader", "?"), f"{duration_min}m", views_str)
    console.print(table)
