"""Textual TUI application."""

import os
import argparse
import threading
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Button, DataTable, Static, Select
from textual.binding import Binding

from src import __version__
from src.config.manager import load_config
from src.core.download_manager import DownloadManager, DownloadOptions
from src.core.downloader import get_video_info
from src.services.presets import PresetsManager
from src.utils.validation import validate_url, validate_output_path
from src.utils.platform import normalize_url
from src.ui.themes import get_theme
from src.utils.ytdlp_updater import auto_update_on_startup


class KyroApp(App):
    CSS = """
    Screen { background: $surface; }
    #main-container { layout: vertical; margin: 1 2; }
    #header-panel { height: 3; background: $primary; color: $text; content-align: center middle; }
    #url-input { width: 100%; margin: 1 0; }
    #mode-select { width: 100%; margin: 1 0; }
    #output-input { width: 100%; margin: 1 0; }
    #action-buttons { height: 3; align: center middle; }
    #action-buttons Button { margin: 0 1; min-width: 15; }
    #info-panel { height: 10; border: solid $border; margin: 1 0; padding: 0 1; }
    #progress-panel { height: 5; border: solid $border; margin: 1 0; padding: 0 1; }
    #queue-panel { height: 15; border: solid $border; margin: 1 0; }
    #status-bar { height: 3; background: $surface; dock: bottom; content-align: center middle; }
    DataTable { height: 100%; }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "download", "Download", show=True),
        Binding("p", "pause_queue", "Pause", show=True),
        Binding("r", "resume_queue", "Resume", show=True),
        Binding("c", "clear_queue", "Clear", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.manager = DownloadManager(self.config.model_dump())
        self.ui_theme = get_theme(self.config.ui.theme)
        self.presets_manager = PresetsManager()
        self.current_info = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static(f"[bold cyan]Kyro Downloader v{__version__}[/bold cyan]", id="header-panel"),
            Input(placeholder="Enter URL...", id="url-input"),
            Select(
                [("Video", "video"), ("MP3", "mp3"), ("Playlist", "playlist"), ("Batch", "batch")],
                value="video",
                id="mode-select",
                prompt="Select mode",
            ),
            Select(
                [("None", "None")] + [(name, name) for name in self.presets_manager.get_all_presets().keys()],
                value="None",
                id="preset-select",
                prompt="Select preset",
            ),
            Input(placeholder=f"Output: {self.config.general.output_path}", id="output-input"),
            Horizontal(
                Button("Download", id="btn-download", variant="primary"),
                Button("Queue", id="btn-queue", variant="success"),
                Button("Info", id="btn-info", variant="default"),
                Button("Clear", id="btn-clear", variant="error"),
                id="action-buttons",
            ),
            ScrollableContainer(
                Static("Video info will appear here...", id="info-panel"),
                Static("Progress: Waiting...", id="progress-panel"),
                DataTable(id="queue-table"),
            ),
            Static("[dim]Press Q to quit | D to download | P to pause | R to resume[/dim]", id="status-bar"),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"Kyro Downloader v{__version__}"
        self.sub_title = "Production-grade media downloader by nkpendyam"
        table = self.query_one("#queue-table", DataTable)
        table.add_columns("ID", "URL", "Status", "Priority")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-download":
            self.action_download()
        elif button_id == "btn-queue":
            self._queue_current()
        elif button_id == "btn-info":
            self._fetch_info()
        elif button_id == "btn-clear":
            self.action_clear_queue()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "url-input":
            self._fetch_info()

    def action_download(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            self.notify("Please enter a URL", severity="error")
            return
        url = normalize_url(url)
        if not validate_url(url):
            self.notify(f"Invalid URL: {url}", severity="error")
            return
        mode = self.query_one("#mode-select", Select).value
        preset_name = self.query_one("#preset-select", Select).value
        preset = self.presets_manager.get_preset(preset_name) if preset_name and preset_name != "None" else None
        output = self.query_one("#output-input", Input).value.strip()
        if not output:
            output = self.config.general.output_path
        output = validate_output_path(output)
        self.notify(f"Starting download: {url}", severity="information")

        def _download_task():
            try:
                cfg = self.config.model_dump()
                if preset:
                    cfg["output_template"] = preset.get("output_template")
                    cfg["subtitles"] = preset.get("subtitles", cfg.get("subtitles"))
                if mode == "mp3":
                    cfg["only_audio"] = True
                    if preset and preset.get("audio_format"):
                        cfg["audio_format"] = preset["audio_format"]
                    else:
                        cfg["audio_format"] = "mp3"
                    if preset and preset.get("audio_quality"):
                        cfg["audio_quality"] = preset["audio_quality"]
                    self.manager.config.update(cfg)
                    self.manager.download_now(DownloadOptions(url=url, output_path=str(output), only_audio=True))
                elif mode == "playlist":
                    self.manager.config.update(cfg)
                    self.manager.download_playlist(DownloadOptions(url=url, output_path=str(output)))
                else:
                    self.manager.config.update(cfg)
                    self.manager.download_now(DownloadOptions(url=url, output_path=str(output)))
                self.call_from_thread(self.notify, "Download complete!", severity="success")
            except Exception as e:
                self.call_from_thread(self.notify, f"Download failed: {e}", severity="error")

        threading.Thread(target=_download_task, daemon=True, name="kyro-tui-download").start()

    def action_pause_queue(self) -> None:
        paused = 0
        for item in self.manager.queue.get_all_items():
            if item.status.value in ("pending", "downloading"):
                self.manager.queue.pause(item.task_id)
                paused += 1
        if paused > 0:
            self.notify(f"Paused {paused} download(s)", severity="warning")
        else:
            self.notify("Nothing to pause", severity="information")

    def action_resume_queue(self) -> None:
        resumed = 0
        for item in self.manager.queue.get_all_items():
            if item.status.value == "paused":
                self.manager.queue.resume(item.task_id)
                resumed += 1
        if resumed > 0:
            self.notify(f"Resumed {resumed} download(s)", severity="information")
        else:
            self.notify("Nothing to resume", severity="information")

    def action_clear_queue(self) -> None:
        self.manager.queue.clear_all()
        table = self.query_one("#queue-table", DataTable)
        table.clear()
        self.notify("Queue cleared", severity="information")

    def _fetch_info(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            return
        url = normalize_url(url)
        if not validate_url(url):
            self.notify(f"Invalid URL: {url}", severity="error")
            return
        try:
            info = get_video_info(url)
            self.current_info = info
            info_panel = self.query_one("#info-panel", Static)
            info_panel.update(
                f"[bold]Title:[/bold] {info.title}\n[bold]Duration:[/bold] {info.duration_str}\n[bold]Uploader:[/bold] {info.uploader}\n[bold]Views:[/bold] {info.view_count_str}"
            )
            self.notify(f"Loaded: {info.title}", severity="success")
        except Exception as e:
            self.notify(f"Failed to fetch info: {e}", severity="error")

    def _queue_current(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            self.notify("Please enter a URL first", severity="error")
            return
        try:
            preset_name = self.query_one("#preset-select", Select).value
            preset = self.presets_manager.get_preset(preset_name) if preset_name and preset_name != "None" else None
            cfg = self.config.model_dump()
            if preset:
                cfg["output_template"] = preset.get("output_template")
                cfg["subtitles"] = preset.get("subtitles", cfg.get("subtitles"))
                if preset.get("only_audio"):
                    cfg["only_audio"] = True
                if preset.get("audio_format"):
                    cfg["audio_format"] = preset["audio_format"]
                if preset.get("audio_quality"):
                    cfg["audio_quality"] = preset["audio_quality"]
            self.manager.config.update(cfg)
            item = self.manager.queue_download(DownloadOptions(url=url, only_audio=bool(cfg.get("only_audio", False))))
            table = self.query_one("#queue-table", DataTable)
            table.add_row(
                item.task_id[:8], url[:50] + "..." if len(url) > 50 else url, item.status.value, item.priority.name
            )
            self.notify(f"Queued: {item.task_id[:8]}", severity="success")
        except Exception as e:
            self.notify(f"Queue error: {e}", severity="error")


def run_tui():
    config = load_config()
    if getattr(config.general, "auto_update", False) and not os.environ.get("PYTEST_CURRENT_TEST"):
        auto_update_on_startup(check_only=False)
    app = KyroApp()
    app.run()


def create_parser() -> argparse.ArgumentParser:
    """Create TUI CLI parser."""
    parser = argparse.ArgumentParser(description="Run Kyro Downloader Textual TUI")
    parser.add_argument("-v", "--version", action="store_true", help="Show version and exit")
    parser.add_argument("--no-auto-update", action="store_true", help="Skip startup auto-update check")
    return parser


def main() -> None:
    """CLI entrypoint for TUI module."""
    args = create_parser().parse_args()
    if args.version:
        print(f"Kyro Downloader v{__version__}")
        return

    if args.no_auto_update:
        os.environ["KYRO_SKIP_AUTO_UPDATE"] = "1"

    config = load_config()
    should_auto_update = (
        not args.no_auto_update
        and not os.environ.get("KYRO_SKIP_AUTO_UPDATE")
        and getattr(config.general, "auto_update", False)
        and not os.environ.get("PYTEST_CURRENT_TEST")
    )
    if should_auto_update:
        auto_update_on_startup(check_only=False)

    app = KyroApp()
    app.run()


if __name__ == "__main__":
    main()
