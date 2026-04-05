"""CLI archive command."""
from src.services.archive import DownloadArchive
from rich import print
from rich.table import Table
from rich.console import Console

console = Console()

def show_archive():
    archive = DownloadArchive()
    items = archive.list_all(limit=50)
    if not items:
        print("[dim]Archive is empty[/dim]")
        return
    table = Table(title="Download Archive")
    table.add_column("Title", style="cyan")
    table.add_column("Platform", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Duration", style="magenta")
    table.add_column("Downloaded", style="blue")
    for video_id, entry in items:
        size_mb = entry.get("size", 0) / (1024*1024)
        duration_min = entry.get("duration", 0) / 60
        table.add_row(entry["title"], entry.get("platform", "?"), f"{size_mb:.1f} MB", f"{duration_min:.1f} min", entry.get("downloaded_at", "?")[:10])
    console.print(table)

def clear_archive():
    archive = DownloadArchive()
    archive.clear()
    print("[bold green]Archive cleared[/bold green]")
