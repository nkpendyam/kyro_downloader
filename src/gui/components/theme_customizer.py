"""Theme customization component."""
from src.ui.themes import THEMES, Theme, get_theme

class ThemeCustomizer:
    def __init__(self) -> None:
        self.custom_themes: dict[str, Theme] = {}

    def list_themes(self) -> list[str]:
        return list(THEMES.keys()) + list(self.custom_themes.keys())

    def get_theme(self, name: str) -> Theme:
        if name in self.custom_themes:
            return self.custom_themes[name]
        return get_theme(name)

    def create_custom_theme(
        self,
        name: str,
        primary: str,
        secondary: str,
        accent: str,
        success: str,
        warning: str,
        error: str,
        background: str,
        surface: str,
        text: str,
    ) -> Theme:
        theme = Theme(
            name=name,
            primary=primary,
            secondary=secondary,
            accent=accent,
            success=success,
            warning=warning,
            error=error,
            background=background,
            surface=surface,
            text=text,
            text_muted="#888888",
            border=primary,
            progress_bar=success,
        )
        self.custom_themes[name] = theme
        return theme

    def delete_custom_theme(self, name: str) -> bool:
        if name in self.custom_themes:
            del self.custom_themes[name]
            return True
        return False
