"""CLI external downloader command."""
from src.services.external_dl import download_with_aria2c, get_external_downloader
from rich import print

def external_download(url, output_path, max_connections=16, rate_limit=None):
    downloader = get_external_downloader()
    if not downloader:
        print("[bold red]No external downloader available. Install aria2c.[/bold red]")
        return
    print(f"[bold blue]Downloading with {downloader}: {url}[/bold blue]")
    result = download_with_aria2c(url, output_path, max_connections, rate_limit)
    if result:
        print(f"[bold green]Download complete with {downloader}[/bold green]")
    else:
        print(f"[bold red]{downloader} download failed[/bold red]")
