"""CLI stats command."""
from src.services.statistics import StatsTracker
from rich import print
from rich.table import Table
from rich.console import Console

console = Console()

def show_stats():
    tracker = StatsTracker()
    summary = tracker.get_summary()
    table = Table(title="Kyro Downloader Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for key, value in summary.items():
        table.add_row(key.replace("_", " ").title(), str(value))
    console.print(table)

def reset_stats():
    tracker = StatsTracker()
    tracker.reset()
    print("[bold green]Statistics reset[/bold green]")
