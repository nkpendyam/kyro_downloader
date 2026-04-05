"""Theme customization component."""
from src.ui.themes import THEMES, get_theme
from src.utils.logger import get_logger
logger = get_logger(__name__)

class ThemeCustomizer:
    def __init__(self):
        self.custom_themes = {}

    def list_themes(self):
        return list(THEMES.keys()) + list(self.custom_themes.keys())

    def get_theme(self, name):
        if name in self.custom_themes:
            return self.custom_themes[name]
        return get_theme(name)

    def create_custom_theme(self, name, primary, secondary, accent, success, warning, error, background, surface, text):
        from dataclasses import dataclass
        @dataclass
        class CustomTheme:
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
            text_muted: str = "#888888"
            border: str = None
            progress_bar: str = None
        theme = CustomTheme(name=name, primary=primary, secondary=secondary, accent=accent, success=success, warning=warning, error=error, background=background, surface=surface, text=text)
        theme.border = primary
        theme.progress_bar = success
        self.custom_themes[name] = theme
        return theme

    def delete_custom_theme(self, name):
        if name in self.custom_themes:
            del self.custom_themes[name]
            return True
        return False
