"""CLI chapters command."""
from src.services.chapters import extract_chapters, split_by_chapters
from rich import print
from rich.table import Table
from rich.console import Console

console = Console()

def show_chapters(video_path):
    chapters = extract_chapters(video_path)
    if not chapters:
        print("[dim]No chapters found[/dim]")
        return
    table = Table(title="Chapters")
    table.add_column("#", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Start", style="yellow")
    table.add_column("End", style="magenta")
    for i, ch in enumerate(chapters, 1):
        start_min = int(ch["start"]) // 60
        start_sec = int(ch["start"]) % 60
        end_min = int(ch["end"]) // 60
        end_sec = int(ch["end"]) % 60
        table.add_row(str(i), ch["title"], f"{start_min}:{start_sec:02d}", f"{end_min}:{end_sec:02d}")
    console.print(table)

def split_chapters(video_path, output_dir):
    chapters = split_by_chapters(video_path, output_dir)
    print(f"[bold green]Split into {len(chapters)} chapters[/bold green]")
