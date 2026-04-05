"""CLI convert command."""
from src.services.converter import convert_file, batch_convert
from rich import print

def convert_single(input_path, output_format, quality=None, remove_original=False):
    print(f"[bold blue]Converting {input_path} to {output_format}...[/bold blue]")
    result = convert_file(input_path, output_format, quality, remove_original)
    if result:
        print(f"[bold green]Converted: {result}[/bold green]")
    else:
        print("[bold red]Conversion failed[/bold red]")

def convert_batch(file_list, output_format, quality=None, remove_original=False):
    print(f"[bold blue]Converting {len(file_list)} files to {output_format}...[/bold blue]")
    results = batch_convert(file_list, output_format, quality, remove_original)
    success = sum(1 for r in results if r["success"])
    print(f"[bold green]{success}/{len(results)} files converted[/bold green]")
