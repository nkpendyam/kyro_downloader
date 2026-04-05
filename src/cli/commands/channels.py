"""CLI channels command."""
from src.services.channels import get_channel_info
from rich import print
from rich.console import Console

console = Console()

def channel_info(channel_url):
    info = get_channel_info(channel_url)
    if not info:
        print("[bold red]Failed to get channel info[/bold red]")
        return
    print(f"[bold]Channel:[/bold] {info['title']}")
    print(f"[bold]Uploader:[/bold] {info['uploader']}")
    print(f"[bold]Videos:[/bold] {info['entry_count']}")
