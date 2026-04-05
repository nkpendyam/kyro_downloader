"""Progress row widget for Kyro Downloader GUI."""
import flet as ft


class ProgressRow(ft.Row):
    def __init__(self, value=0, text=""):
        self.progress_bar = ft.ProgressBar(value=value, color=ft.Colors.BLUE_400)
        self.progress_text = ft.Text(text, size=12, color=ft.Colors.GREY_400)
        super().__init__([self.progress_bar], spacing=10)

    def update(self, value, text):
        self.progress_bar.value = value
        self.progress_text.value = text
