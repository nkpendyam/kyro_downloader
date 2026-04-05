"""Statistics tab page for Kyro Downloader GUI."""
import flet as ft


class StatisticsPage:
    def __init__(self, stats):
        self.stats = stats
        self.build()

    def build(self):
        self.stats_content = ft.Column([ft.Text("Loading...", size=14)], spacing=10, scroll=ft.ScrollMode.AUTO)
        self.refresh_stats_btn = ft.ElevatedButton("Refresh", icon=ft.Icons.REFRESH, on_click=self.refresh_stats)
        self.content = ft.Column([
            ft.Row([ft.Text("Statistics Dashboard", size=20, weight=ft.FontWeight.BOLD), ft.Container(expand=True), self.refresh_stats_btn]),
            self.stats_content,
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

    def set_page(self, page):
        self.page = page

    def refresh_stats(self, e=None):
        stats = self.stats.get_summary()
        self.stats_content.controls.clear()
        for key, value in stats.items():
            self.stats_content.controls.append(ft.Row([
                ft.Text(f"{key.replace('_', ' ').title()}:", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(str(value), size=14),
            ]))
        self.page.update()
