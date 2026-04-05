"""Download card widget for Kyro Downloader GUI."""
import flet as ft


class DownloadCard(ft.Container):
    def __init__(self, url, status, progress=0, on_cancel=None):
        self.url = url
        self.status = status
        self.progress = progress
        self.on_cancel = on_cancel
        self._build()
        super().__init__(content=self._content, padding=10, border_radius=8, border=ft.border.all(1, ft.Colors.GREY_800))

    def _build(self):
        self.progress_bar = ft.ProgressBar(value=self.progress, color=ft.Colors.BLUE_400)
        self.status_text = ft.Text(self.status, size=12, color=ft.Colors.GREY_400)
        self._content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.BLUE_400),
                ft.Text(self.url[:80] + "..." if len(self.url) > 80 else self.url, size=12, expand=True),
                ft.IconButton(ft.Icons.DELETE, on_click=self._handle_cancel),
            ]),
            self.progress_bar,
            self.status_text,
        ], spacing=5)

    def _handle_cancel(self, e):
        if self.on_cancel:
            self.on_cancel(self)

    def update_progress(self, value, status_text):
        self.progress_bar.value = value
        self.status_text.value = status_text
