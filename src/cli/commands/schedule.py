"""CLI schedule command."""
from src.services.scheduler import DownloadScheduler
from rich import print
from rich.table import Table
from rich.console import Console

console = Console()

def add_schedule(url, scheduled_time, output_path=None, repeat="none"):
    scheduler = DownloadScheduler()
    schedule = scheduler.add_schedule(url, scheduled_time, output_path=output_path, repeat=repeat)
    print(f"[bold green]Schedule added: {schedule['id']}[/bold green]")

def list_schedules():
    scheduler = DownloadScheduler()
    schedules = scheduler.list_schedules()
    if not schedules:
        print("[dim]No schedules[/dim]")
        return
    table = Table(title="Download Schedules")
    table.add_column("ID", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Time", style="yellow")
    table.add_column("Repeat", style="magenta")
    table.add_column("Status", style="blue")
    for s in schedules:
        table.add_row(s["id"][:8], s["url"][:40], s["scheduled_time"], s["repeat"], s["status"])
    console.print(table)

def remove_schedule(schedule_id):
    scheduler = DownloadScheduler()
    scheduler.remove_schedule(schedule_id)
    print(f"[bold green]Schedule {schedule_id} removed[/bold green]")
