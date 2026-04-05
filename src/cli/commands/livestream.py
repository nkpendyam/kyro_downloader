"""CLI livestream command."""
from src.services.livestream import download_livestream, record_livestream_ffmpeg
from rich import print

def livestream_download(url, output_path, from_start=False):
    print(f"[bold blue]Downloading livestream: {url}[/bold blue]")
    result = download_livestream(url, output_path, from_start)
    if result:
        print(f"[bold green]Livestream download complete: {result}[/bold green]")
    else:
        print("[bold red]Livestream download failed[/bold red]")

def livestream_record(url, output_path, timeout=3600):
    print(f"[bold blue]Recording livestream: {url}[/bold blue]")
    result = record_livestream_ffmpeg(url, output_path, timeout)
    if result:
        print(f"[bold green]Livestream recording complete: {result}[/bold green]")
    else:
        print("[bold red]Livestream recording failed[/bold red]")
