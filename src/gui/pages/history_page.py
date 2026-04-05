"""History tab page for Kyro Downloader GUI."""
import flet as ft


class HistoryPage:
    def __init__(self, stats, history_viewer):
        self.stats = stats
        self.history_viewer = history_viewer
        self.build()

    def build(self):
        self.history_list = ft.ListView(expand=True, spacing=5)
        self.refresh_history_btn = ft.ElevatedButton("Refresh", icon=ft.Icons.REFRESH, on_click=self.refresh_history)
        self.history_search = ft.TextField(label="Search history", prefix_icon=ft.Icons.SEARCH, width=200, on_submit=self.search_history_tab)
        self.history_status_filter = ft.Dropdown(
            label="Status",
            options=[ft.DropdownOption("all"), ft.DropdownOption("completed"), ft.DropdownOption("failed")],
            value="all",
            width=120,
            on_select=self.filter_history_by_status,
        )
        self.clear_history_btn = ft.ElevatedButton("Clear All", icon=ft.Icons.DELETE_FOREVER, on_click=self.clear_all_history)
        self.content = ft.Column([
            ft.Row([ft.Text("Download History", size=20, weight=ft.FontWeight.BOLD), ft.Container(expand=True), self.history_search, self.history_status_filter, self.refresh_history_btn, self.clear_history_btn]),
            self.history_list,
        ], spacing=10)

    def set_page(self, page):
        self.page = page

    def refresh_history(self, e=None):
        items = self.stats.get_stats()
        self.history_list.controls.clear()
        self.history_list.controls.append(ft.Text(f"Total downloads: {items.total_downloads}", size=14))
        self.history_list.controls.append(ft.Text(f"Success rate: {items.success_rate:.1f}%", size=14))
        self.history_list.controls.append(ft.Text(f"Total data: {items.total_gb:.2f} GB", size=14))
        self.page.update()

    def search_history_tab(self, e=None):
        query = self.history_search.value
        if not query:
            self.refresh_history()
            return
        results = self.history_viewer.search_history(query)
        self.history_list.controls.clear()
        for entry in results:
            self.history_list.controls.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.GREY_400),
                title=ft.Text(entry.get("title", "Unknown"), size=12),
                subtitle=ft.Text(f"{entry.get('status', '')} | {entry.get('timestamp', '')[:19]}", size=10),
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, tid=entry.get("task_id"): self.delete_history_entry(tid)),
            ))
        self.page.update()

    def filter_history_by_status(self, e=None):
        status = self.history_status_filter.value
        if status == "all":
            self.refresh_history()
            return
        results = self.history_viewer.filter_by_status(status)
        self.history_list.controls.clear()
        for entry in results:
            self.history_list.controls.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.GREY_400),
                title=ft.Text(entry.get("title", "Unknown"), size=12),
                subtitle=ft.Text(f"{entry.get('status', '')} | {entry.get('timestamp', '')[:19]}", size=10),
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, tid=entry.get("task_id"): self.delete_history_entry(tid)),
            ))
        self.page.update()

    def clear_all_history(self, e=None):
        self.history_viewer.clear_history()
        self.refresh_history()

    def delete_history_entry(self, task_id):
        self.history_viewer.delete_entry(task_id)
        self.refresh_history()
