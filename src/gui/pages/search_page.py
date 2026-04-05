"""Legacy Flet search page prototype.

This module is intentionally not wired into the active desktop GUI runtime,
which uses CustomTkinter.
"""
import flet as ft


class SearchPage:
    def __init__(self):
        self.build()

    def build(self):
        self.search_input = ft.TextField(label="Search", prefix_icon=ft.Icons.SEARCH, expand=True, on_submit=self.do_search)
        self.search_btn = ft.ElevatedButton("Search", icon=ft.Icons.SEARCH, on_click=self.do_search)
        self.search_platform = ft.Dropdown(
            label="Platform",
            options=[ft.DropdownOption("youtube"), ft.DropdownOption("soundcloud")],
            value="youtube",
            width=150,
        )
        self.search_results = ft.ListView(expand=True, spacing=5)
        self.content = ft.Column([
            ft.Row([self.search_input, self.search_btn, self.search_platform]),
            self.search_results,
        ], spacing=10)

    def set_page(self, page):
        self.page = page

    def _raise_legacy_runtime_error(self, action: str) -> None:
        """Raise a clear error for unsupported legacy Flet actions."""
        raise NotImplementedError(
            f"Legacy Flet SearchPage action '{action}' is not supported. "
            "Use the active CustomTkinter GUI in src/gui/app.py."
        )

    def do_search(self, e=None):
        self._raise_legacy_runtime_error("do_search")

    def _download_search_result(self, url):
        self._raise_legacy_runtime_error("download_search_result")
