"""History entry widget for Kyro Downloader GUI."""
import flet as ft


class HistoryEntry(ft.ListTile):
    def __init__(self, entry, on_delete=None):
        self.entry = entry
        self.on_delete = on_delete
        super().__init__(
            leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.GREY_400),
            title=ft.Text(entry.get("title", "Unknown"), size=12),
            subtitle=ft.Text(f"{entry.get('status', '')} | {entry.get('timestamp', '')[:19]}", size=10),
            trailing=ft.IconButton(ft.Icons.DELETE, on_click=self._handle_delete),
        )

    def _handle_delete(self, e):
        if self.on_delete:
            self.on_delete(self.entry.get("task_id"))
