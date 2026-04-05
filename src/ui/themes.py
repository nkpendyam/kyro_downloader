"""UI theme definitions for TUI."""
from dataclasses import dataclass

@dataclass
class Theme:
    name: str
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    error: str
    background: str
    surface: str
    text: str
    text_muted: str
    border: str
    progress_bar: str

THEMES = {
    "dark": Theme(name="Dark", primary="cyan", secondary="magenta", accent="blue", success="green", warning="yellow", error="red", background="black", surface="grey15", text="white", text_muted="grey50", border="cyan", progress_bar="green"),
    "light": Theme(name="Light", primary="blue", secondary="magenta", accent="cyan", success="green", warning="dark_yellow", error="red", background="white", surface="grey93", text="black", text_muted="grey50", border="blue", progress_bar="green"),
    "dracula": Theme(name="Dracula", primary="bright_magenta", secondary="bright_cyan", accent="bright_green", success="bright_green", warning="bright_yellow", error="bright_red", background="#282a36", surface="#44475a", text="#f8f8f2", text_muted="#6272a4", border="#bd93f9", progress_bar="#50fa7b"),
    "nord": Theme(name="Nord", primary="#88c0d0", secondary="#b48ead", accent="#a3be8c", success="#a3be8c", warning="#ebcb8b", error="#bf616a", background="#2e3440", surface="#3b4252", text="#eceff4", text_muted="#4c566a", border="#88c0d0", progress_bar="#a3be8c"),
    "monokai": Theme(name="Monokai", primary="#a6e22e", secondary="#f92672", accent="#66d9ef", success="#a6e22e", warning="#e6db74", error="#f92672", background="#272822", surface="#3e3d32", text="#f8f8f2", text_muted="#75715e", border="#a6e22e", progress_bar="#a6e22e"),
}

def get_theme(name="dark"):
    return THEMES.get(name, THEMES["dark"])

def list_themes():
    return list(THEMES.keys())
