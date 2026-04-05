"""Legacy Flet download page prototype.

This module is intentionally not wired into the active desktop GUI runtime,
which uses CustomTkinter.
"""
import flet as ft
from src.utils.validation import validate_url
from src.utils.platform import normalize_url, get_platform_info
from src.core.downloader import get_video_info


class DownloadPage:
    def __init__(self, config, manager, presets_manager, tags_manager):
        self.config = config
        self.manager = manager
        self.presets_manager = presets_manager
        self.tags_manager = tags_manager
        self._current_url = None
        self._current_info = None
        self.build()

    def build(self):
        self.url_input = ft.TextField(
            label="Paste URL or search query",
            prefix_icon=ft.Icons.LINK,
            expand=True,
            on_submit=self.fetch_info,
        )
        self.fetch_btn = ft.ElevatedButton("Fetch Info", icon=ft.Icons.INFO, on_click=self.fetch_info)
        self.download_btn = ft.ElevatedButton("Download", icon=ft.Icons.DOWNLOAD, on_click=self.start_download, disabled=True)
        self.batch_btn = ft.ElevatedButton("Batch Download", icon=ft.Icons.PLAYLIST_ADD, on_click=self.batch_download)
        self.status_text = ft.Text("", size=12, color=ft.Colors.GREY_400)
        self.video_info_card = ft.Container(visible=False, padding=10)
        self.progress_bar = ft.ProgressBar(value=0, color=ft.Colors.BLUE_400, visible=False)
        self.progress_text = ft.Text("", size=12, color=ft.Colors.GREY_400)
        self.eta_text = ft.Text("", size=12, color=ft.Colors.GREY_400)

        self.quality_dropdown = ft.Dropdown(
            label="Quality",
            options=[ft.DropdownOption("best"), ft.DropdownOption("8k"), ft.DropdownOption("4k"), ft.DropdownOption("1080p"), ft.DropdownOption("720p"), ft.DropdownOption("480p")],
            value="best",
            width=150,
        )
        self.format_dropdown = ft.Dropdown(
            label="Format",
            options=[ft.DropdownOption("video"), ft.DropdownOption("audio")],
            value="video",
            width=120,
        )
        self.audio_format_dropdown = ft.Dropdown(
            label="Audio",
            options=[ft.DropdownOption("mp3"), ft.DropdownOption("flac"), ft.DropdownOption("aac"), ft.DropdownOption("ogg"), ft.DropdownOption("wav")],
            value="mp3",
            width=120,
            visible=False,
        )
        self.format_dropdown.on_select = lambda e: self._toggle_audio_format(e.data == "audio")

        self.preset_dropdown = ft.Dropdown(
            label="Presets",
            options=[ft.DropdownOption(name) for name in self.presets_manager.get_all_presets().keys()],
            width=200,
            on_select=self._on_preset_selected,
        )
        self.tags_input = ft.TextField(
            label="Tags (comma-separated)",
            prefix_icon=ft.Icons.LABEL,
            width=250,
            on_submit=self._on_tags_submitted,
        )

        self.content = ft.Column([
            ft.Row([self.url_input, self.fetch_btn]),
            ft.Row([self.preset_dropdown, self.tags_input]),
            ft.Row([self.quality_dropdown, self.format_dropdown, self.audio_format_dropdown, self.download_btn, self.batch_btn]),
            self.status_text,
            self.video_info_card,
            self.progress_bar,
            ft.Row([self.progress_text, self.eta_text]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def _toggle_audio_format(self, visible):
        self.audio_format_dropdown.visible = visible
        self.page.update()

    def set_page(self, page):
        self.page = page

    def fetch_info(self, e=None):
        url = normalize_url(self.url_input.value.strip())
        if not validate_url(url):
            self.status_text.value = "Invalid URL"
            self.status_text.color = ft.Colors.RED_400
            self.page.update()
            return
        self.status_text.value = "Fetching video info..."
        self.status_text.color = ft.Colors.BLUE_400
        self.page.update()
        try:
            info = get_video_info(url)
            platform = get_platform_info(url)
            platform_icon = platform.get("icon", "") if platform else ""
            self.video_info_card.content = ft.Column([
                ft.Row([ft.Text(f"{platform_icon} {info.title}", size=16, weight=ft.FontWeight.BOLD), ft.Container(expand=True)]),
                ft.Row([
                    ft.Text(f"Duration: {info.duration_str}", size=12),
                    ft.Text(f"Uploader: {info.uploader}", size=12),
                    ft.Text(f"Views: {info.view_count_str}", size=12),
                ]),
                ft.Text(f"Type: {'Playlist' if info.is_playlist else 'Video'}", size=12),
            ])
            self.video_info_card.visible = True
            self.download_btn.disabled = False
            self.status_text.value = f"Ready to download: {info.title}"
            self.status_text.color = ft.Colors.GREEN_400
            self._current_info = info
            self._current_url = url
            self.page.update()
        except Exception as ex:
            self.status_text.value = f"Error: {str(ex)}"
            self.status_text.color = ft.Colors.RED_400
            self.page.update()

    def _raise_legacy_runtime_error(self, action: str) -> None:
        """Raise a clear error for unsupported legacy Flet actions."""
        raise NotImplementedError(
            f"Legacy Flet DownloadPage action '{action}' is not supported. "
            "Use the active CustomTkinter GUI in src/gui/app.py."
        )

    def start_download(self, e=None):
        self._raise_legacy_runtime_error("start_download")

    def batch_download(self, e=None):
        self._raise_legacy_runtime_error("batch_download")

    def _on_preset_selected(self, e):
        self._raise_legacy_runtime_error("preset_select")

    def _on_tags_submitted(self, e):
        self._raise_legacy_runtime_error("tags_submit")
