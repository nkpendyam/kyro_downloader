"""Queue item widget for Kyro Downloader GUI."""
import flet as ft


class QueueItem(ft.ListTile):
    def __init__(self, item, on_cancel=None):
        self.item = item
        self.on_cancel = on_cancel
        super().__init__(
            leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.BLUE_400),
            title=ft.Text(item.url[:80] + "..." if len(item.url) > 80 else item.url, size=12),
            subtitle=ft.Text(f"Status: {item.status.value} | Priority: {item.priority.name}", size=10),
            trailing=ft.IconButton(ft.Icons.DELETE, on_click=self._handle_cancel),
        )

    def _handle_cancel(self, e):
        if self.on_cancel:
            self.on_cancel(self.item)
