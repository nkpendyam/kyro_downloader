"""CLI compress command."""
from src.services.compressor import compress_video, batch_compress
from rich import print

def compress_single(input_path, quality="medium", remove_original=False):
    print(f"[bold blue]Compressing {input_path}...[/bold blue]")
    result = compress_video(input_path, quality=quality, remove_original=remove_original)
    if result:
        print(f"[bold green]Compressed: {result['reduction_percent']:.1f}% smaller[/bold green]")
    else:
        print("[bold red]Compression failed[/bold red]")

def compress_batch(file_list, quality="medium", remove_original=False):
    print(f"[bold blue]Compressing {len(file_list)} files...[/bold blue]")
    results = batch_compress(file_list, quality=quality, remove_original=remove_original)
    success = sum(1 for r in results if r["success"])
    print(f"[bold green]{success}/{len(results)} files compressed[/bold green]")
