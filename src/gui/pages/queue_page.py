"""Queue tab page for Kyro Downloader GUI."""
import flet as ft


class QueuePage:
    def __init__(self, manager, tags_manager):
        self.manager = manager
        self.tags_manager = tags_manager
        self.build()

    def build(self):
        self.queue_list = ft.ListView(expand=True, spacing=5)
        self.refresh_queue_btn = ft.ElevatedButton("Refresh", icon=ft.Icons.REFRESH, on_click=self.refresh_queue)
        self.clear_queue_btn = ft.ElevatedButton("Clear Completed", icon=ft.Icons.DELETE_SWEEP, on_click=self.clear_completed)
        self.pause_all_btn = ft.ElevatedButton("Pause All", icon=ft.Icons.PAUSE, on_click=self.pause_all_queue)
        self.resume_all_btn = ft.ElevatedButton("Resume All", icon=ft.Icons.PLAY_ARROW, on_click=self.resume_all_queue)
        self.queue_search = ft.TextField(label="Filter queue", prefix_icon=ft.Icons.SEARCH, width=200, on_submit=self.filter_queue)
        self.queue_tag_filter = ft.Dropdown(label="Filter by tag", width=150, on_select=self.filter_queue_by_tag)
        self._populate_queue_tag_filter()
        self.content = ft.Column([
            ft.Row([ft.Text("Download Queue", size=20, weight=ft.FontWeight.BOLD), ft.Container(expand=True), self.queue_search, self.queue_tag_filter, self.pause_all_btn, self.resume_all_btn, self.refresh_queue_btn, self.clear_queue_btn]),
            self.queue_list,
        ], spacing=10)

    def set_page(self, page):
        self.page = page

    def refresh_queue(self, e=None):
        items = self.manager.queue.get_all_items()
        self.queue_list.controls.clear()
        for item in items:
            self.queue_list.controls.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.BLUE_400),
                title=ft.Text(item.url[:80] + "..." if len(item.url) > 80 else item.url, size=12),
                subtitle=ft.Text(f"Status: {item.status.value} | Priority: {item.priority.name}", size=10),
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, i=item: self._cancel_download(i)),
            ))
        self.page.update()

    def _cancel_download(self, item):
        self.manager.queue.cancel(item.task_id)
        self.refresh_queue()

    def clear_completed(self, e=None):
        self.manager.queue.clear_completed()
        self.refresh_queue()

    def pause_all_queue(self, e=None):
        for item in self.manager.queue.get_all_items():
            if item.status.value in ("pending", "downloading"):
                self.manager.queue.pause(item.task_id)
        self.refresh_queue()

    def resume_all_queue(self, e=None):
        for item in self.manager.queue.get_all_items():
            if item.status.value == "paused":
                self.manager.queue.resume(item.task_id)
        self.refresh_queue()

    def filter_queue(self, e=None):
        query = self.queue_search.value.lower()
        items = self.manager.queue.get_all_items()
        self.queue_list.controls.clear()
        for item in items:
            if query and query not in item.url.lower():
                continue
            self.queue_list.controls.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.BLUE_400),
                title=ft.Text(item.url[:80] + "..." if len(item.url) > 80 else item.url, size=12),
                subtitle=ft.Text(f"Status: {item.status.value} | Priority: {item.priority.name}", size=10),
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, i=item: self._cancel_download(i)),
            ))
        self.page.update()

    def filter_queue_by_tag(self, e=None):
        tag = self.queue_tag_filter.value
        if tag == "all":
            self.refresh_queue()
            return
        task_ids = self.tags_manager.get_tasks_by_tag(tag)
        items = self.manager.queue.get_all_items()
        self.queue_list.controls.clear()
        for item in items:
            if item.task_id in task_ids:
                self.queue_list.controls.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.BLUE_400),
                    title=ft.Text(item.url[:80] + "..." if len(item.url) > 80 else item.url, size=12),
                    subtitle=ft.Text(f"Status: {item.status.value} | Priority: {item.priority.name}", size=10),
                    trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, i=item: self._cancel_download(i)),
                ))
        self.page.update()

    def _populate_queue_tag_filter(self):
        tags = self.tags_manager.get_all_tags()
        self.queue_tag_filter.options = [ft.DropdownOption("all")] + [ft.DropdownOption(t) for t in tags]
        self.queue_tag_filter.value = "all"
