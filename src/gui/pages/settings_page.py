"""Settings tab page for Kyro Downloader GUI."""
import flet as ft
from src.config.manager import load_config, save_config


class SettingsPage:
    def __init__(self, config, language_selector, accessibility, presets_manager):
        self.config = config
        self.language_selector = language_selector
        self.accessibility = accessibility
        self.presets_manager = presets_manager
        self.build()

    def build(self):
        self.output_path_input = ft.TextField(label="Download Path", value=self.config.general.output_path, prefix_icon=ft.Icons.FOLDER)
        self.max_retries_input = ft.TextField(label="Max Retries", value=str(self.config.download.max_retries), width=100, keyboard_type=ft.KeyboardType.NUMBER)
        self.concurrent_workers_input = ft.TextField(label="Concurrent Workers", value=str(self.config.download.concurrent_workers), width=100, keyboard_type=ft.KeyboardType.NUMBER)
        self.rate_limit_input = ft.TextField(label="Rate Limit (e.g. 1M)", value=str(self.config.download.rate_limit or ""), width=150)
        self.proxy_input = ft.TextField(label="Proxy URL", value=str(self.config.download.proxy or ""), expand=True)
        self.notifications_switch = ft.Switch(label="Desktop Notifications", value=self.config.general.notifications)
        self.auto_update_switch = ft.Switch(label="Auto-update yt-dlp", value=self.config.general.auto_update)
        self.check_duplicates_switch = ft.Switch(label="Check Duplicates", value=self.config.general.check_duplicates)
        self.save_settings_btn = ft.ElevatedButton("Save Settings", icon=ft.Icons.SAVE, on_click=self.save_settings)
        self.reset_settings_btn = ft.OutlinedButton("Reset to Defaults", icon=ft.Icons.RESTORE, on_click=self.reset_settings)

        self.language_dropdown = ft.Dropdown(
            label="Language",
            options=[ft.DropdownOption(code, text=f"{lang['native']} ({lang['name']})") for code, lang in self.language_selector.get_all_languages().items()],
            value=self.language_selector.current,
            width=250,
            on_select=self._on_language_changed,
        )

        self.high_contrast_switch = ft.Switch(label="High Contrast", value=self.accessibility.is_high_contrast(), on_change=self._on_accessibility_changed)
        self.large_buttons_switch = ft.Switch(label="Large Buttons", value=self.accessibility.has_large_buttons(), on_change=self._on_accessibility_changed)
        self.font_size_slider = ft.Slider(min=10, max=24, value=self.accessibility.get_font_size(), divisions=14, label="{value}", on_change=self._on_font_size_changed)

        self.preset_list = ft.ListView(expand=False, spacing=5, height=200)
        self._populate_preset_list()
        self.reset_presets_btn = ft.OutlinedButton("Reset Presets", icon=ft.Icons.RESTORE, on_click=self._reset_presets)
        self.export_presets_btn = ft.OutlinedButton("Export Presets", icon=ft.Icons.SHARE, on_click=self._export_presets)
        self.import_presets_btn = ft.OutlinedButton("Import Presets", icon=ft.Icons.IMPORT_EXPORT, on_click=self._import_presets)

        self.content = ft.ListView([
            ft.Text("General Settings", size=20, weight=ft.FontWeight.BOLD),
            self.language_dropdown,
            self.output_path_input,
            ft.Divider(),
            ft.Text("Download Settings", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([self.max_retries_input, self.concurrent_workers_input, self.rate_limit_input]),
            ft.Row([self.proxy_input]),
            ft.Divider(),
            ft.Text("Features", size=16, weight=ft.FontWeight.BOLD),
            self.notifications_switch,
            self.auto_update_switch,
            self.check_duplicates_switch,
            ft.Divider(),
            ft.Text("Accessibility", size=16, weight=ft.FontWeight.BOLD),
            self.high_contrast_switch,
            self.large_buttons_switch,
            ft.Row([ft.Text("Font Size"), self.font_size_slider]),
            ft.Divider(),
            ft.Text("Presets", size=16, weight=ft.FontWeight.BOLD),
            self.preset_list,
            ft.Row([self.reset_presets_btn, self.export_presets_btn, self.import_presets_btn]),
            ft.Divider(),
            ft.Row([self.save_settings_btn, self.reset_settings_btn]),
        ], spacing=10, padding=20)

    def set_page(self, page):
        self.page = page

    def save_settings(self, e=None):
        self.config.general.output_path = self.output_path_input.value
        self.config.download.max_retries = int(self.max_retries_input.value)
        self.config.download.concurrent_workers = int(self.concurrent_workers_input.value)
        self.config.download.rate_limit = self.rate_limit_input.value or None
        self.config.download.proxy = self.proxy_input.value or None
        self.config.general.notifications = self.notifications_switch.value
        self.config.general.auto_update = self.auto_update_switch.value
        self.config.general.check_duplicates = self.check_duplicates_switch.value
        save_config(self.config)
        self.page.show_snack_bar(ft.SnackBar(ft.Text("Settings saved!"), open=True))

    def reset_settings(self, e=None):
        self.config = load_config()
        self.output_path_input.value = self.config.general.output_path
        self.max_retries_input.value = str(self.config.download.max_retries)
        self.concurrent_workers_input.value = str(self.config.download.concurrent_workers)
        self.rate_limit_input.value = str(self.config.download.rate_limit or "")
        self.proxy_input.value = str(self.config.download.proxy or "")
        self.notifications_switch.value = self.config.general.notifications
        self.auto_update_switch.value = self.config.general.auto_update
        self.check_duplicates_switch.value = self.config.general.check_duplicates
        self.page.update()

    def _on_language_changed(self, e):
        self.language_selector.set_language(self.language_dropdown.value)
        self.page.show_snack_bar(ft.SnackBar(ft.Text(f"Language: {self.language_selector.get_language_name()}"), open=True))

    def _on_accessibility_changed(self, e):
        self.accessibility.set("high_contrast", self.high_contrast_switch.value)
        self.accessibility.set("large_buttons", self.large_buttons_switch.value)
        self.page.update()

    def _on_font_size_changed(self, e):
        self.accessibility.set("font_size", int(self.font_size_slider.value))
        self.page.fonts = {"Roboto": "Roboto"}
        self.page.update()

    def _populate_preset_list(self):
        self.preset_list.controls.clear()
        for name, preset in self.presets_manager.get_all_presets().items():
            self.preset_list.controls.append(ft.ListTile(
                leading=ft.Text(preset.get("icon", "📦"), size=20),
                title=ft.Text(name, size=13),
                subtitle=ft.Text(preset.get("format") or preset.get("mode", ""), size=10),
            ))

    def _reset_presets(self, e=None):
        self.presets_manager.reset_to_defaults()
        self._populate_preset_list()
        self.page.show_snack_bar(ft.SnackBar(ft.Text("Presets reset to defaults"), open=True))

    def _export_presets(self, e=None):
        def pick_result(e: ft.FilePickerResultEvent):
            if e.files:
                success = self.presets_manager.export_presets(e.files[0].path)
                if success:
                    self.page.show_snack_bar(ft.SnackBar(ft.Text("Presets exported!"), open=True))
        picker = ft.FilePicker(on_result=pick_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.save_file(file_name="kyro_presets.json")

    def _import_presets(self, e=None):
        def pick_result(e: ft.FilePickerResultEvent):
            if e.files:
                count = self.presets_manager.import_presets(e.files[0].path)
                self._populate_preset_list()
                self.page.show_snack_bar(ft.SnackBar(ft.Text(f"Imported {count} presets"), open=True))
        picker = ft.FilePicker(on_result=pick_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.pick_files(file_type="any")
