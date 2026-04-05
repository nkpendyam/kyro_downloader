"""Accessibility settings component for Desktop GUI."""
import json
from pathlib import Path


class AccessibilitySettings:
    def __init__(self, state_dir=".kyro_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.settings_file = self.state_dir / "accessibility.json"
        self._settings = {
            "font_size": 14,
            "high_contrast": False,
            "screen_reader": False,
            "large_buttons": False,
            "keyboard_navigation": True,
            "focus_indicators": True,
            "reduced_motion": False,
            "color_blind_mode": "none",
            "minimum_touch_target": 44,
            "text_spacing": 1.0,
        }
        self._load_settings()

    def _load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                self._settings.update(data)
        except Exception:
            pass

    def _save_settings(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        if key in self._settings:
            self._settings[key] = value
            self._save_settings()

    def get_all(self):
        return self._settings.copy()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._settings:
                self._settings[key] = value
        self._save_settings()

    def reset_to_defaults(self):
        self._settings = {
            "font_size": 14,
            "high_contrast": False,
            "screen_reader": False,
            "large_buttons": False,
            "keyboard_navigation": True,
            "focus_indicators": True,
            "reduced_motion": False,
            "color_blind_mode": "none",
            "minimum_touch_target": 44,
            "text_spacing": 1.0,
        }
        self._save_settings()

    def get_font_size(self):
        return self._settings.get("font_size", 14)

    def is_high_contrast(self):
        return self._settings.get("high_contrast", False)

    def is_screen_reader_enabled(self):
        return self._settings.get("screen_reader", False)

    def has_large_buttons(self):
        return self._settings.get("large_buttons", False)

    def get_color_blind_mode(self):
        return self._settings.get("color_blind_mode", "none")

    def get_text_spacing(self):
        return self._settings.get("text_spacing", 1.0)

    def get_contrast_colors(self):
        if self._settings.get("high_contrast", False):
            return {
                "background": "#000000",
                "text": "#FFFFFF",
                "primary": "#00FFFF",
                "secondary": "#FFFF00",
                "success": "#00FF00",
                "error": "#FF0000",
                "warning": "#FFA500",
                "border": "#FFFFFF",
            }
        return {
            "background": "#1e1e2e",
            "text": "#cdd6f4",
            "primary": "#89b4fa",
            "secondary": "#a6e3a1",
            "success": "#a6e3a1",
            "error": "#f38ba8",
            "warning": "#f9e2af",
            "border": "#45475a",
        }

    def get_color_blind_palette(self):
        mode = self._settings.get("color_blind_mode", "none")
        palettes = {
            "none": {},
            "protanopia": {
                "red": "#006699",
                "green": "#CC79A7",
                "blue": "#0072B2",
                "yellow": "#F0E442",
            },
            "deuteranopia": {
                "red": "#D55E00",
                "green": "#009E73",
                "blue": "#0072B2",
                "yellow": "#F0E442",
            },
            "tritanopia": {
                "red": "#E69F00",
                "green": "#56B4E9",
                "blue": "#0072B2",
                "yellow": "#F0E442",
            },
        }
        return palettes.get(mode, {})

    def apply_to_gui_runtime(self, app):
        font_size = self.get_font_size()
        colors = self.get_contrast_colors()
        if self.is_high_contrast():
            try:
                app.theme_mode = "dark"
            except Exception:
                pass
        if self.has_large_buttons():
            pass
        return {
            "font_size": font_size,
            "colors": colors,
            "high_contrast": self.is_high_contrast(),
            "large_buttons": self.has_large_buttons(),
        }
