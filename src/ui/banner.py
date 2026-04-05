"""ASCII banner and branding."""
import pyfiglet
from rich import print

BANNER_TEXT = "Kyro Downloader"
VERSION = "1.0.0"
AUTHOR = "nkpendyam"
GITHUB = "github.com/nkpendyam"

def show_banner():
    banner = pyfiglet.figlet_format(BANNER_TEXT)
    print(f"[bold cyan]{banner}[/bold cyan]")
    print(f"[bold magenta]v{VERSION}[/bold magenta]  [dim]by {AUTHOR}[/dim]")
    print(f"[bold blue]{GITHUB}[/bold blue]\n")

def show_mini_banner():
    print(f"[bold cyan]Kyro[/bold cyan] [dim]Downloader v{VERSION}[/dim]")

def get_banner_text():
    return pyfiglet.figlet_format(BANNER_TEXT)
