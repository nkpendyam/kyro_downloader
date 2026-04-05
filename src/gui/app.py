"""Kyro Downloader Desktop GUI Application built with CustomTkinter."""

import os
import subprocess
import platform
import threading
import time
from tkinter import filedialog

import customtkinter as ctk

from src import __version__
from src.config.manager import load_config, save_config
from src.core.download_manager import DownloadManager
from src.core.downloader import get_video_info, build_quality_labels, build_smart_audio_options
from src.utils.validation import validate_url, validate_output_path
from src.utils.platform import normalize_url, get_platform_info
from src.services.statistics import StatsTracker
from src.services.archive import DownloadArchive
from src.gui.components import PresetsManager, DragDropHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KyroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"Kyro Downloader v{__version__}")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Config and managers
        self.config = load_config()
        self.manager = DownloadManager(self.config.model_dump())
        self.stats = StatsTracker()
        self.archive = DownloadArchive()
        self.presets_manager = PresetsManager()
        self.drag_drop_handler = DragDropHandler(on_url_dropped=self._handle_dropped_urls)

        # State
        self._current_url = None
        self._current_info = None
        self._download_thread = None
        self._download_cancelled = False
        self._download_start_time = None
        self._queue_refresh_timer = None
        self._audio_options = {}

        # Build UI
        self._build_ui()
        self._bind_keyboard_shortcuts()
        logger.info("GUI initialized")

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.ctk.ctk.CTkLabel(
            header, text="Kyro Downloader", font=ctk.ctk.ctk.CTkFont(size=24, weight="bold"), text_color="#3B8ED0"
        ).pack(side="left")
        ctk.ctk.ctk.CTkLabel(header, text=f"v{__version__}", font=ctk.ctk.ctk.CTkFont(size=12), text_color="gray").pack(
            side="left", padx=(10, 0)
        )

        ctk.CTkFrame(header, width=1, height=30, fg_color="gray").pack(side="left", padx=20)

        ctk.ctk.ctk.CTkButton(header, text="Settings", width=80, command=self._show_settings_dialog).pack(
            side="right", padx=5
        )
        ctk.ctk.ctk.CTkButton(header, text="Open Folder", width=90, command=self._open_download_folder).pack(
            side="right", padx=5
        )
        ctk.ctk.ctk.CTkButton(header, text="Toggle Theme", width=100, command=self._toggle_theme).pack(
            side="right", padx=5
        )

        # Tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs
        self.tab_download = self.tabview.add("Download")
        self.tab_queue = self.tabview.add("Queue")
        self.tab_history = self.tabview.add("History")
        self.tab_search = self.tabview.add("Search")
        self.tab_stats = self.tabview.add("Statistics")
        self.tab_schedule = self.tabview.add("Schedule")
        self.tab_settings = self.tabview.add("Settings")

        # Build each tab
        self._build_download_tab()
        self._build_queue_tab()
        self._build_history_tab()
        self._build_search_tab()
        self._build_stats_tab()
        self._build_schedule_tab()
        self._build_settings_tab()

    # ==================== DOWNLOAD TAB ====================

    def _build_download_tab(self):
        tab = self.tab_download
        scroll = ctk.ctk.ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True)

        # URL input
        url_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        url_frame.pack(fill="x", padx=20, pady=(10, 5))
        self.url_entry = ctk.ctk.CTkEntry(
            url_frame, placeholder_text="Paste URL or search query...", height=40, font=ctk.ctk.CTkFont(size=14)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self._fetch_info())
        self._setup_url_drop_target()
        self.fetch_btn = ctk.ctk.CTkButton(url_frame, text="Fetch Info", width=100, command=self._fetch_info)
        self.fetch_btn.pack(side="right")

        # Options row
        opts_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        opts_frame.pack(fill="x", padx=20, pady=5)
        ctk.ctk.CTkLabel(opts_frame, text="Quality:").pack(side="left", padx=(0, 5))
        self.quality_combo = ctk.ctk.CTkComboBox(opts_frame, values=["Best Available"], width=180)
        self.quality_combo.set("Best Available")
        self.quality_combo.pack(side="left", padx=(0, 10))
        ctk.ctk.CTkLabel(opts_frame, text="Format:").pack(side="left", padx=(0, 5))
        self.format_combo = ctk.ctk.CTkComboBox(
            opts_frame, values=["video", "audio"], width=100, command=self._toggle_audio_format
        )
        self.format_combo.set("video")
        self.format_combo.pack(side="left", padx=(0, 10))
        ctk.ctk.CTkLabel(opts_frame, text="Preset:").pack(side="left", padx=(0, 5))
        preset_names = ["None"] + list(self.presets_manager.get_all_presets().keys())
        self.preset_combo = ctk.ctk.CTkComboBox(opts_frame, values=preset_names, width=180)
        self.preset_combo.set("None")
        self.preset_combo.pack(side="left", padx=(0, 10))

        # Audio quality row (hidden by default)
        self.audio_quality_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.audio_quality_frame.pack(fill="x", padx=20, pady=5)
        self.audio_quality_frame.pack_forget()
        ctk.ctk.CTkLabel(self.audio_quality_frame, text="Audio Quality:").pack(side="left", padx=(0, 5))
        self.audio_quality_combo = ctk.ctk.CTkComboBox(
            self.audio_quality_frame, values=["Smart Best Available (Auto)"], width=200
        )
        self.audio_quality_combo.set("Smart Best Available (Auto)")
        self.audio_quality_combo.pack(side="left", padx=(0, 10))
        ctk.ctk.CTkLabel(self.audio_quality_frame, text="Format:").pack(side="left", padx=(0, 5))
        self.audio_format_combo = ctk.ctk.CTkComboBox(
            self.audio_quality_frame, values=["mp3", "flac", "aac", "opus", "wav", "alac", "ogg"], width=100
        )
        self.audio_format_combo.set("mp3")
        self.audio_format_combo.pack(side="left", padx=(0, 10))
        self._update_audio_options({})

        # Subtitle row
        self.subtitle_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.subtitle_frame.pack(fill="x", padx=20, pady=5)
        self.subtitle_enabled_var = ctk.BooleanVar(value=bool(self.config.subtitles.enabled))
        self.subtitle_enabled_switch = ctk.ctk.CTkSwitch(
            self.subtitle_frame,
            text="Download Subtitles",
            variable=self.subtitle_enabled_var,
        )
        self.subtitle_enabled_switch.pack(side="left", padx=(0, 10))
        self.subtitle_embed_var = ctk.BooleanVar(value=bool(self.config.subtitles.embed))
        self.subtitle_embed_switch = ctk.ctk.CTkSwitch(
            self.subtitle_frame,
            text="Embed Subtitles",
            variable=self.subtitle_embed_var,
        )
        self.subtitle_embed_switch.pack(side="left", padx=(0, 10))
        ctk.ctk.CTkLabel(self.subtitle_frame, text="Lang:").pack(side="left", padx=(0, 5))
        subtitle_lang_default = ",".join(self.config.subtitles.languages or ["en"])
        self.subtitle_lang_entry = ctk.ctk.CTkEntry(self.subtitle_frame, width=120)
        self.subtitle_lang_entry.insert(0, subtitle_lang_default)
        self.subtitle_lang_entry.pack(side="left", padx=(0, 10))

        # Available formats label
        self.available_label = ctk.ctk.CTkLabel(scroll, text="", text_color="gray", font=ctk.ctk.CTkFont(size=11))
        self.available_label.pack(fill="x", padx=20, pady=5)
        self.available_label.pack_forget()

        # Action buttons
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        self.download_btn = ctk.ctk.CTkButton(
            btn_frame, text="Download", width=120, command=self._start_download, state="disabled"
        )
        self.download_btn.pack(side="left", padx=(0, 10))
        ctk.ctk.CTkButton(btn_frame, text="Batch Download", width=120, command=self._batch_download).pack(
            side="left", padx=(0, 10)
        )
        ctk.ctk.CTkButton(btn_frame, text="Queue Download", width=120, command=self._queue_download).pack(
            side="left", padx=(0, 10)
        )

        # Status
        self.status_label = ctk.ctk.CTkLabel(scroll, text="", text_color="gray", font=ctk.ctk.CTkFont(size=12))
        self.status_label.pack(fill="x", padx=20, pady=5)

        # Video info card
        self.info_frame = ctk.CTkFrame(scroll)
        self.info_frame.pack(fill="x", padx=20, pady=5)
        self.info_frame.pack_forget()
        self.info_title = ctk.ctk.CTkLabel(
            self.info_frame, text="", font=ctk.ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        self.info_title.pack(fill="x", padx=10, pady=(10, 5))
        self.info_details = ctk.ctk.CTkLabel(self.info_frame, text="", anchor="w", justify="left")
        self.info_details.pack(fill="x", padx=10, pady=(0, 10))

        # Progress
        self.progress = ctk.ctk.CTkProgressBar(scroll, width=500)
        self.progress.pack(padx=20, pady=5)
        self.progress.set(0)
        self.progress.pack_forget()
        self.progress_label = ctk.ctk.CTkLabel(scroll, text="", text_color="gray", font=ctk.ctk.CTkFont(size=12))
        self.progress_label.pack(pady=5)
        self.progress_label.pack_forget()
        self.speed_label = ctk.ctk.CTkLabel(scroll, text="", text_color="gray", font=ctk.ctk.CTkFont(size=12))
        self.speed_label.pack(pady=5)
        self.speed_label.pack_forget()
        self.cancel_btn = ctk.ctk.CTkButton(
            scroll, text="Cancel Download", width=120, fg_color="#E74C3C", command=self._cancel_download
        )
        self.cancel_btn.pack(pady=5)
        self.cancel_btn.pack_forget()

    def _toggle_audio_format(self, value=None):
        if self.format_combo.get() == "audio":
            self.audio_quality_frame.pack(fill="x", padx=20, pady=5)
        else:
            self.audio_quality_frame.pack_forget()

    def _fetch_info(self):
        url = normalize_url(self.url_entry.get().strip())
        if not validate_url(url):
            self.status_label.configure(text="Invalid URL", text_color="#E74C3C")
            return
        self.status_label.configure(text="Fetching video info...", text_color="#3B8ED0")
        self.fetch_btn.configure(state="disabled")

        def _fetch():
            try:
                info = get_video_info(url)
                platform_info = get_platform_info(url)
                platform_icon = platform_info.get("icon", "") if platform_info else ""
                self.after(0, lambda i=info, u=url, p=platform_icon: self._show_info(i, u, p))
            except Exception as exc:
                err_msg = str(exc)
                self.after(
                    0, lambda msg=err_msg: self.status_label.configure(text=f"Error: {msg}", text_color="#E74C3C")
                )
            finally:
                self.after(0, lambda: self.fetch_btn.configure(state="normal"))

        threading.Thread(target=_fetch, daemon=True).start()

    def _setup_url_drop_target(self):
        """Enable best-effort drag-and-drop for URL entry when tkdnd is available."""
        try:
            from tkinterdnd2 import DND_FILES, DND_TEXT  # type: ignore[import-not-found]

            if hasattr(self.url_entry, "drop_target_register") and hasattr(self.url_entry, "dnd_bind"):
                self.url_entry.drop_target_register(DND_FILES, DND_TEXT)
                self.url_entry.dnd_bind("<<Drop>>", self._on_url_drop)
                logger.info("URL drag-and-drop enabled")
        except Exception:
            # Drag-and-drop is optional; keep GUI functional without tkdnd.
            logger.debug("URL drag-and-drop not available in this environment")

    def _on_url_drop(self, event):
        """Handle OS drop events for URL text or URL list files."""
        raw_data = str(getattr(event, "data", "") or "").strip()
        if not raw_data:
            return "break"

        cleaned = raw_data.replace("{", "").replace("}", "")
        urls = []
        for token in cleaned.split():
            if os.path.exists(token):
                urls.extend(self.drag_drop_handler.handle_drop(token))

        if not urls:
            urls = self.drag_drop_handler.handle_text_drop(cleaned)

        if not urls and cleaned.startswith("http"):
            urls = [cleaned]

        if urls:
            self._handle_dropped_urls(urls)

        return "break"

    def _handle_dropped_urls(self, urls):
        """Apply dropped URL data to the main URL field and prefetch info."""
        if not urls:
            return

        first = normalize_url(urls[0])
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, first)
        self._fetch_info()

        if len(urls) > 1:
            self.status_label.configure(text=f"Loaded {len(urls)} URLs from drop (showing first)", text_color="#3B8ED0")

    def _show_info(self, info, url, platform_icon):
        self._current_url = url
        self._current_info = info
        quality_labels = build_quality_labels(info.available)
        self.quality_combo.configure(values=quality_labels)
        self.quality_combo.set(quality_labels[0])
        self._update_audio_options(info.available)
        avail = info.available
        avail_text = "Available: " + ", ".join(quality_labels)
        if avail["audio_bitrates"]:
            max_abr = max(avail["audio_bitrates"])
            avail_text += f" | Audio up to {max_abr}kbps"
        if avail["audio_codecs"]:
            avail_text += f" ({', '.join(avail['audio_codecs'])})"
        self.available_label.configure(text=avail_text)
        self.available_label.pack(fill="x", padx=20, pady=5)
        self.info_title.configure(text=f"{platform_icon} {info.title}")
        self.info_details.configure(
            text=f"Duration: {info.duration_str}\n"
            f"Uploader: {info.uploader}\n"
            f"Views: {info.view_count_str}\n"
            f"Type: {'Playlist' if info.is_playlist else 'Video'}"
        )
        self.info_frame.pack(fill="x", padx=20, pady=5)
        self.download_btn.configure(state="normal")
        self.status_label.configure(text=f"Ready to download: {info.title}", text_color="#2ECC71")

    def _update_audio_options(self, analysis):
        """Refresh audio options from detected source formats and presets."""
        options = build_smart_audio_options(analysis)
        self._audio_options = {opt["label"]: opt for opt in options}

        labels = [opt["label"] for opt in options]
        self.audio_quality_combo.configure(values=labels)
        self.audio_quality_combo.set(labels[0])

        formats = []
        for opt in options:
            audio_format = opt.get("audio_format")
            if audio_format and audio_format not in formats:
                formats.append(audio_format)
        if formats:
            self.audio_format_combo.configure(values=formats)
            self.audio_format_combo.set(formats[0])

    def _apply_gui_preset(self, cfg, only_audio):
        """Apply the selected GUI preset into the outgoing config."""
        preset_name = self.preset_combo.get() if hasattr(self, "preset_combo") else "None"
        if not preset_name or preset_name == "None":
            return None
        preset = self.presets_manager.get_preset(preset_name)
        if not preset:
            return None
        if preset.get("format"):
            cfg["format"] = preset["format"]
        if preset.get("only_audio"):
            cfg["only_audio"] = True
            only_audio = True
        if preset.get("audio_format"):
            cfg["audio_format"] = preset["audio_format"]
        if preset.get("audio_quality"):
            cfg["audio_quality"] = preset["audio_quality"]
        if preset.get("subtitles"):
            cfg["subtitles"] = preset["subtitles"]
        if preset.get("output_template"):
            cfg["output_template"] = preset["output_template"]
        if preset.get("quality"):
            cfg["quality"] = preset["quality"]
        if preset.get("prefer_codec"):
            cfg["audio_selector_preference"] = preset["prefer_codec"]
        return only_audio

    def _selected_gui_preset(self):
        """Return the active GUI preset config, if any."""
        preset_name = self.preset_combo.get() if hasattr(self, "preset_combo") else "None"
        if not preset_name or preset_name == "None":
            return None
        return self.presets_manager.get_preset(preset_name)

    def _start_download(self):
        if not self._current_url:
            return
        url = self._current_url
        output = validate_output_path(self.config.general.output_path)
        only_audio = self.format_combo.get() == "audio"
        preset_cfg = self._selected_gui_preset()
        if preset_cfg and preset_cfg.get("only_audio"):
            only_audio = True
        quality_label = self.quality_combo.get()
        hdr = "HDR" in quality_label
        dolby = "Dolby" in quality_label
        quality = "best"
        for q in ["8k", "4k", "1080p", "720p", "480p"]:
            if q in quality_label.lower():
                quality = q
                break
        audio_format = "mp3"
        audio_quality = "192"
        audio_selector = None
        subtitles_cfg = None
        if only_audio:
            selected = self._audio_options.get(self.audio_quality_combo.get(), {})
            audio_format = selected.get("audio_format", self.audio_format_combo.get())
            audio_quality = selected.get("audio_quality", "192")
            audio_selector = selected.get("selector")
        if self.subtitle_enabled_var.get():
            languages = [lang.strip() for lang in self.subtitle_lang_entry.get().split(",") if lang.strip()]
            subtitles_cfg = {
                "enabled": True,
                "languages": languages or ["en"],
                "embed": self.subtitle_embed_var.get() and not only_audio,
                "auto_generated": True,
                "format": "srt",
            }
        self._download_cancelled = False
        self._download_start_time = time.time()
        self.progress.pack(fill="x", padx=20, pady=5)
        self.progress.set(0)
        self.progress_label.pack(pady=5)
        self.progress_label.configure(text="Starting...")
        self.speed_label.pack(pady=5)
        self.speed_label.configure(text="")
        self.cancel_btn.pack(pady=5)
        self.download_btn.configure(state="disabled")
        self._start_queue_refresh()

        def _download():
            download_only_audio = only_audio
            try:

                def progress_hook(d):
                    if self._download_cancelled:
                        raise Exception("Download cancelled")
                    if d.get("status") == "downloading":
                        pct = d.get("_percent_str", "0%").strip()
                        speed = d.get("_speed_str", "?").strip()
                        try:
                            pct_val = float(pct.replace("%", "")) / 100
                        except Exception:
                            pct_val = 0
                        self.after(0, lambda v=pct_val, t=f"{pct} - {speed}", s=speed: self._update_progress(v, t, s))

                cfg = self.config.model_dump()
                cfg["hdr"] = hdr
                cfg["dolby"] = dolby
                cfg["audio_format"] = audio_format
                cfg["audio_quality"] = audio_quality
                cfg["audio_selector"] = audio_selector
                if subtitles_cfg:
                    cfg["subtitles"] = subtitles_cfg
                if preset_cfg:
                    selected_only_audio = self._apply_gui_preset(cfg, download_only_audio)
                    if selected_only_audio is not None:
                        download_only_audio = selected_only_audio
                cfg["format_id"] = None
                if download_only_audio:
                    cfg["only_audio"] = True
                if quality != "best" and not hdr and not dolby:
                    height_map = {"8k": 4320, "4k": 2160, "1080p": 1080, "720p": 720, "480p": 480}
                    target_h = height_map.get(quality)
                    if target_h:
                        cfg["format"] = f"bestvideo[height<={target_h}]+bestaudio/best[ext=m4a]/best"
                self.manager.config.update(cfg)
                self.manager.download_now(
                    url,
                    str(output),
                    only_audio=download_only_audio,
                    quality=quality,
                    hdr=hdr,
                    dolby=dolby,
                    audio_format=audio_format,
                    audio_quality=audio_quality,
                    audio_selector=audio_selector,
                    progress_hook=progress_hook,
                )
                self.after(0, lambda: self._add_archive_entry(url, "completed"))
                self.after(0, lambda: self._download_complete(True, "Download complete!"))
            except Exception as exc:
                err_msg = str(exc)
                self.after(0, lambda: self._add_archive_entry(url, "failed"))
                self.after(0, lambda msg=err_msg: self._download_complete(False, f"Error: {msg}"))

        self._download_thread = threading.Thread(target=_download, daemon=True)
        self._download_thread.start()

    def _update_progress(self, value, text, speed):
        self.progress.set(value)
        self.progress_label.configure(text=text)
        self.speed_label.configure(text=f"Speed: {speed}")

    def _download_complete(self, success, message):
        self.progress.pack_forget()
        self.progress_label.pack_forget()
        self.speed_label.pack_forget()
        self.cancel_btn.pack_forget()
        self.download_btn.configure(state="normal")
        self.status_label.configure(text=message, text_color="#2ECC71" if success else "#E74C3C")
        # Stop queue refresh timer
        self._stop_queue_refresh()
        # Refresh all tabs
        self._refresh_history()
        self._refresh_stats()
        self._refresh_queue()

    def _cancel_download(self):
        self._download_cancelled = True
        self.status_label.configure(text="Cancelling...", text_color="#F39C12")
        # Stop queue refresh timer
        self._stop_queue_refresh()
        self.progress.pack_forget()
        self.progress_label.pack_forget()
        self.speed_label.pack_forget()
        self.cancel_btn.pack_forget()
        self.download_btn.configure(state="normal")

    def _add_archive_entry(self, url, status):
        """Add entry to download archive."""
        try:
            title = self._current_info.title if self._current_info else url
            entry = {
                "task_id": f"gui_{int(time.time())}",
                "url": url,
                "title": title,
                "status": status,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "size": "unknown",
            }
            self.archive.add(entry)
        except Exception as e:
            logger.error(f"Failed to add archive entry: {e}")

    def _queue_download(self):
        if not self._current_url:
            self.status_label.configure(text="Fetch info first", text_color="#E74C3C")
            return
        url = self._current_url
        output = validate_output_path(self.config.general.output_path)
        only_audio = self.format_combo.get() == "audio"
        quality_label = self.quality_combo.get()
        hdr = "HDR" in quality_label
        dolby = "Dolby" in quality_label
        quality = "best"
        for q in ["8k", "4k", "1080p", "720p", "480p"]:
            if q in quality_label.lower():
                quality = q
                break
        audio_format = "mp3"
        audio_quality = "192"
        audio_selector = None
        subtitles_cfg = None
        preset_cfg = self._selected_gui_preset()
        if preset_cfg and preset_cfg.get("only_audio"):
            only_audio = True
        if only_audio:
            selected = self._audio_options.get(self.audio_quality_combo.get(), {})
            audio_format = selected.get("audio_format", self.audio_format_combo.get())
            audio_quality = selected.get("audio_quality", "192")
            audio_selector = selected.get("selector")
        if self.subtitle_enabled_var.get():
            languages = [lang.strip() for lang in self.subtitle_lang_entry.get().split(",") if lang.strip()]
            subtitles_cfg = {
                "enabled": True,
                "languages": languages or ["en"],
                "embed": self.subtitle_embed_var.get() and not only_audio,
                "auto_generated": True,
                "format": "srt",
            }
            self.manager.config["subtitles"] = subtitles_cfg
        cfg = self.config.model_dump()
        self._apply_gui_preset(cfg, only_audio)
        self.manager.config.update(cfg)
        item = self.manager.queue_download(
            url,
            output_path=str(output),
            only_audio=only_audio,
            quality=quality,
            hdr=hdr,
            dolby=dolby,
            audio_format=audio_format,
            audio_quality=audio_quality,
            audio_selector=audio_selector,
            subtitles=subtitles_cfg,
            output_template=cfg.get("output_template"),
        )
        self.status_label.configure(text=f"Queued: {url[:50]}... (ID: {item.task_id[:8]})", text_color="#2ECC71")
        self._refresh_queue()

    def _batch_download(self):
        filepath = filedialog.askopenfilename(
            title="Select URL file", filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return
        try:
            from src.utils.validation import validate_batch_file

            urls = validate_batch_file(filepath)
            output = validate_output_path(self.config.general.output_path)
            quality_label = self.quality_combo.get()
            hdr = "HDR" in quality_label
            dolby = "Dolby" in quality_label
            quality = "best"
            for q in ["8k", "4k", "1080p", "720p", "480p"]:
                if q in quality_label.lower():
                    quality = q
                    break
            only_audio = self.format_combo.get() == "audio"
            preset_cfg = self._selected_gui_preset()
            if preset_cfg and preset_cfg.get("only_audio"):
                only_audio = True
            audio_format = "mp3"
            audio_quality = "192"
            audio_selector = None
            subtitles_cfg = None
            if only_audio:
                selected = self._audio_options.get(self.audio_quality_combo.get(), {})
                audio_format = selected.get("audio_format", self.audio_format_combo.get())
                audio_quality = selected.get("audio_quality", "192")
                audio_selector = selected.get("selector")
            if self.subtitle_enabled_var.get():
                languages = [lang.strip() for lang in self.subtitle_lang_entry.get().split(",") if lang.strip()]
                subtitles_cfg = {
                    "enabled": True,
                    "languages": languages or ["en"],
                    "embed": self.subtitle_embed_var.get() and not only_audio,
                    "auto_generated": True,
                    "format": "srt",
                }
            cfg = self.config.model_dump()
            cfg["hdr"] = hdr
            cfg["dolby"] = dolby
            cfg["audio_format"] = audio_format
            cfg["audio_quality"] = audio_quality
            cfg["audio_selector"] = audio_selector
            if subtitles_cfg:
                cfg["subtitles"] = subtitles_cfg
            if preset_cfg:
                self._apply_gui_preset(cfg, only_audio)
            self.manager.config.update(cfg)
            for url in urls:
                self.manager.queue_download(
                    url,
                    output_path=str(output),
                    only_audio=only_audio,
                    quality=quality,
                    hdr=hdr,
                    dolby=dolby,
                    audio_format=audio_format,
                    audio_quality=audio_quality,
                    audio_selector=audio_selector,
                    subtitles=subtitles_cfg,
                    output_template=cfg.get("output_template"),
                )
            self.manager.execute_async()
            self.status_label.configure(text=f"Started {len(urls)} downloads", text_color="#2ECC71")
            self._start_queue_refresh()
            self._refresh_queue()
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="#E74C3C")

    def _start_queue_refresh(self):
        """Start periodic queue refresh during downloads."""

        def _refresh():
            if not self._download_cancelled:
                self.after(0, self._refresh_queue)
                self._queue_refresh_timer = self.after(2000, _refresh)

        self._queue_refresh_timer = self.after(2000, _refresh)

    def _stop_queue_refresh(self):
        """Stop periodic queue refresh."""
        if self._queue_refresh_timer:
            self.after_cancel(self._queue_refresh_timer)
            self._queue_refresh_timer = None

    def _refresh_plugins(self):
        plugin_frame = getattr(self, "plugin_frame", None)
        if plugin_frame is None:
            logger.debug("Plugin frame not initialized; skipping plugin refresh")
            return

        for widget in plugin_frame.winfo_children():
            widget.destroy()
        plugins = self.manager.plugin_loader.list_plugins()
        if not plugins:
            ctk.ctk.CTkLabel(plugin_frame, text="No plugins found").pack(pady=10)
            return
        for plugin in plugins:
            row = ctk.CTkFrame(plugin_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            var = ctk.BooleanVar(value=plugin["enabled"])
            switch = ctk.ctk.CTkSwitch(
                row,
                text=f"{plugin['name']} v{plugin['version']}",
                variable=var,
                command=lambda n=plugin["name"], v=var: self._toggle_plugin(n, v),
            )
            switch.pack(side="left")
            ctk.ctk.CTkLabel(
                row, text=plugin.get("description", ""), text_color="gray", font=ctk.ctk.CTkFont(size=10)
            ).pack(side="left", padx=10)

    def _toggle_plugin(self, name, var):
        if var.get():
            self.manager.plugin_loader.enable_plugin(name)
        else:
            self.manager.plugin_loader.disable_plugin(name)

    def _build_queue_tab(self):
        tab = self.tab_queue
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.ctk.CTkButton(btn_frame, text="Start Queue", width=100, fg_color="#2ECC71", command=self._start_queue).pack(
            side="right", padx=5
        )
        ctk.ctk.CTkButton(btn_frame, text="Refresh", width=80, command=self._refresh_queue).pack(side="right", padx=5)
        ctk.ctk.CTkButton(btn_frame, text="Clear Completed", width=120, command=self._clear_completed).pack(
            side="right", padx=5
        )
        self.queue_text = ctk.ctk.CTkTextbox(tab, font=ctk.ctk.CTkFont(size=12))
        self.queue_text.pack(fill="both", expand=True, padx=20, pady=5)
        self._refresh_queue()

    def _start_queue(self):
        if self.manager.queue.is_empty:
            self.status_label.configure(text="Queue is empty", text_color="#F39C12")
            return
        output = validate_output_path(self.config.general.output_path)
        for item in self.manager.queue.get_all_items():
            if item.status.value == "pending":
                item.metadata["output_path"] = str(output)
        self.manager.config.update(self.config.model_dump())
        self.manager.execute_async()
        self.status_label.configure(text="Queue started!", text_color="#2ECC71")
        self._start_queue_refresh()

    def _refresh_queue(self):
        self.queue_text.delete("1.0", "end")
        items = self.manager.queue.get_all_items()
        if not items:
            self.queue_text.insert("1.0", "Queue is empty")
            return
        for item in items:
            url_short = item.url[:70] + "..." if len(item.url) > 70 else item.url
            self.queue_text.insert("end", f"[{item.status.value.upper()}] {url_short}\n")
            if item.format_id:
                self.queue_text.insert("end", f"  Format: {item.format_id}\n")
            if item.only_audio:
                self.queue_text.insert("end", "  Audio-only mode\n")
            # Show quality if available
            if item.metadata.get("quality"):
                self.queue_text.insert("end", f"  Quality: {item.metadata['quality']}\n")
            self.queue_text.insert("end", "\n")

    def _clear_completed(self):
        self.manager.queue.clear_completed()
        self._refresh_queue()

    def _build_history_tab(self):
        tab = self.tab_history
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.ctk.CTkButton(btn_frame, text="Refresh", width=80, command=self._refresh_history).pack(side="right", padx=5)
        ctk.ctk.CTkButton(btn_frame, text="Clear All", width=80, command=self._clear_history).pack(side="right", padx=5)
        self.history_text = ctk.ctk.CTkTextbox(tab, font=ctk.ctk.CTkFont(size=12))
        self.history_text.pack(fill="both", expand=True, padx=20, pady=5)
        self._refresh_history()

    def _refresh_history(self):
        self.history_text.delete("1.0", "end")
        entries = self.archive.list_all()
        if not entries:
            self.history_text.insert("1.0", "No download history")
            return
        for entry in entries:
            self.history_text.insert("end", f"[{entry.get('status', '?')}] {entry.get('title', 'Unknown')}\n")
            self.history_text.insert(
                "end", f"  Date: {entry.get('timestamp', '')[:19]} | Size: {entry.get('size', '?')}\n\n"
            )

    def _clear_history(self):
        self.archive.clear()
        self._refresh_history()

    def _build_search_tab(self):
        tab = self.tab_search
        search_frame = ctk.CTkFrame(tab, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        self.search_entry = ctk.ctk.CTkEntry(
            search_frame, placeholder_text="Search query...", height=40, font=ctk.ctk.CTkFont(size=14)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._do_search())
        self.search_platform = ctk.ctk.CTkComboBox(search_frame, values=["youtube", "soundcloud"], width=120)
        self.search_platform.set("youtube")
        self.search_platform.pack(side="right", padx=(0, 10))
        ctk.ctk.CTkButton(search_frame, text="Search", width=80, command=self._do_search).pack(side="right")
        self.search_text = ctk.ctk.CTkTextbox(tab, font=ctk.ctk.CTkFont(size=12))
        self.search_text.pack(fill="both", expand=True, padx=20, pady=5)
        self.search_text.insert("1.0", "Enter a search query and press Search")

    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        platform = self.search_platform.get()
        self.search_text.delete("1.0", "end")
        self.search_text.insert("1.0", f"Searching {platform} for: {query}...\n")
        try:
            from src.services.search import search_platform

            results = search_platform(query, platform, max_results=20)
            self.search_text.delete("1.0", "end")
            if not results:
                self.search_text.insert("1.0", "No results found")
                return
            for i, r in enumerate(results, 1):
                self.search_text.insert("end", f"{i}. {r.get('title', 'Unknown')}\n")
                self.search_text.insert("end", f"   URL: {r.get('url', '')}\n")
                self.search_text.insert(
                    "end", f"   Duration: {r.get('duration', '?')}s | Views: {r.get('view_count', '?')}\n\n"
                )
        except Exception as e:
            self.search_text.insert("end", f"\nError: {str(e)}")

    def _build_stats_tab(self):
        tab = self.tab_stats
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.ctk.CTkButton(btn_frame, text="Refresh", width=80, command=self._refresh_stats).pack(side="right", padx=5)
        self.stats_text = ctk.ctk.CTkTextbox(tab, font=ctk.ctk.CTkFont(size=14))
        self.stats_text.pack(fill="both", expand=True, padx=20, pady=5)
        self._refresh_stats()

    def _refresh_stats(self):
        self.stats_text.delete("1.0", "end")
        summary = self.stats.get_summary()
        for key, value in summary.items():
            self.stats_text.insert("end", f"{key.replace('_', ' ').title()}: {value}\n")

    def _build_schedule_tab(self):
        tab = self.tab_schedule
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.ctk.CTkButton(btn_frame, text="Add Schedule", width=120, command=self._add_schedule).pack(
            side="right", padx=5
        )
        ctk.ctk.CTkButton(btn_frame, text="Refresh", width=80, command=self._refresh_schedule).pack(
            side="right", padx=5
        )
        self.schedule_text = ctk.ctk.CTkTextbox(tab, font=ctk.ctk.CTkFont(size=12))
        self.schedule_text.pack(fill="both", expand=True, padx=20, pady=5)
        self._refresh_schedule()

    def _add_schedule(self):
        url = self.url_entry.get().strip()
        if not url or not validate_url(url):
            self.status_label.configure(text="Enter a valid URL first", text_color="#E74C3C")
            return
        from src.services.scheduler import DownloadScheduler

        scheduler = DownloadScheduler()
        import datetime

        scheduled_time = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
        scheduler.add_schedule(url, scheduled_time, output_path=self.config.general.output_path)
        self.status_label.configure(text="Schedule added!", text_color="#2ECC71")
        self._refresh_schedule()

    def _refresh_schedule(self):
        self.schedule_text.delete("1.0", "end")
        from src.services.scheduler import DownloadScheduler

        scheduler = DownloadScheduler()
        schedules = scheduler.list_schedules()
        if not schedules:
            self.schedule_text.insert("1.0", "No scheduled downloads")
            return
        for s in schedules:
            self.schedule_text.insert("end", f"[{s.get('status', '?')}] {s.get('url', '')[:60]}...\n")
            self.schedule_text.insert(
                "end", f"  Time: {s.get('scheduled_time', '')} | Repeat: {s.get('repeat', 'none')}\n\n"
            )

    def _build_settings_tab(self):
        tab = self.tab_settings
        self._settings_scroll = ctk.CTkScrollableFrame(tab)
        self._settings_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.ctk.CTkLabel(self._settings_scroll, text="General", font=ctk.ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(10, 5)
        )
        ctk.ctk.CTkLabel(self._settings_scroll, text="Download Path:").pack(anchor="w", pady=(5, 0))
        self.settings_output = ctk.ctk.CTkEntry(self._settings_scroll, width=500)
        self.settings_output.insert(0, self.config.general.output_path)
        self.settings_output.pack(anchor="w", pady=(0, 10))

        ctk.ctk.CTkLabel(
            self._settings_scroll, text="Download Settings", font=ctk.ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        settings_grid = ctk.CTkFrame(self._settings_scroll, fg_color="transparent")
        settings_grid.pack(anchor="w", fill="x", pady=5)
        ctk.ctk.CTkLabel(settings_grid, text="Max Retries:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.settings_retries = ctk.ctk.CTkEntry(settings_grid, width=80)
        self.settings_retries.insert(0, str(self.config.download.max_retries))
        self.settings_retries.grid(row=0, column=1, padx=(0, 20))
        ctk.ctk.CTkLabel(settings_grid, text="Workers:").grid(row=0, column=2, sticky="w", padx=(0, 10))
        self.settings_workers = ctk.ctk.CTkEntry(settings_grid, width=80)
        self.settings_workers.insert(0, str(self.config.download.concurrent_workers))
        self.settings_workers.grid(row=0, column=3, padx=(0, 20))
        ctk.ctk.CTkLabel(settings_grid, text="Rate Limit:").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0)
        )
        self.settings_rate = ctk.ctk.CTkEntry(settings_grid, width=120)
        self.settings_rate.insert(0, str(self.config.download.rate_limit or ""))
        self.settings_rate.grid(row=1, column=1, padx=(0, 20), pady=(10, 0))

        ctk.ctk.CTkLabel(self._settings_scroll, text="Features", font=ctk.ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(15, 5)
        )
        self.settings_notify_var = ctk.BooleanVar(value=self.config.general.notifications)
        self.settings_notify = ctk.ctk.CTkSwitch(
            self._settings_scroll, text="Desktop Notifications", variable=self.settings_notify_var
        )
        self.settings_notify.pack(anchor="w", pady=5)
        self.settings_autoupdate_var = ctk.BooleanVar(value=self.config.general.auto_update)
        self.settings_autoupdate = ctk.ctk.CTkSwitch(
            self._settings_scroll, text="Auto-update yt-dlp", variable=self.settings_autoupdate_var
        )
        self.settings_autoupdate.pack(anchor="w", pady=5)
        self.settings_dedup_var = ctk.BooleanVar(value=self.config.general.check_duplicates)
        self.settings_dedup = ctk.ctk.CTkSwitch(
            self._settings_scroll, text="Check Duplicates", variable=self.settings_dedup_var
        )
        self.settings_dedup.pack(anchor="w", pady=5)

        ctk.ctk.CTkButton(self._settings_scroll, text="Save Settings", width=150, command=self._save_settings).pack(
            anchor="w", pady=(15, 10)
        )

        ctk.ctk.CTkLabel(self._settings_scroll, text="Plugins", font=ctk.ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", pady=(15, 5)
        )
        self.plugin_frame = ctk.CTkFrame(self._settings_scroll)
        self.plugin_frame.pack(fill="x", padx=10, pady=5)
        self._refresh_plugins()

    def _save_settings(self):
        self.config.general.output_path = self.settings_output.get()
        try:
            self.config.download.max_retries = int(self.settings_retries.get())
        except ValueError:
            pass
        try:
            self.config.download.concurrent_workers = int(self.settings_workers.get())
        except ValueError:
            pass
        self.config.download.rate_limit = self.settings_rate.get() or None
        self.config.general.notifications = self.settings_notify_var.get()
        self.config.general.auto_update = self.settings_autoupdate_var.get()
        self.config.general.check_duplicates = self.settings_dedup_var.get()

        save_config(self.config)
        self.manager.config = self.config.model_dump()
        self.status_label.configure(text="Settings saved!", text_color="#2ECC71")

    # ==================== UTILITY METHODS ====================

    def _bind_keyboard_shortcuts(self):
        self.bind("<Control-v>", self._paste_url_from_clipboard)
        self.bind("<Control-s>", lambda e: self._save_settings())
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<Return>", lambda e: self._fetch_info())

    def _paste_url_from_clipboard(self, _event=None):
        """Handle Ctrl+V in URL field and parse multiple pasted URLs."""
        if self.focus_get() is not self.url_entry:
            return None

        try:
            clip_text = str(self.clipboard_get()).strip()
        except Exception:
            return None

        if not clip_text:
            return "break"

        urls = self.drag_drop_handler.handle_text_drop(clip_text)
        if urls:
            self._handle_dropped_urls(urls)
            return "break"

        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, clip_text)
        return "break"

    def _show_settings_dialog(self):
        self.tabview.set("Settings")

    def _open_download_folder(self):
        try:
            path = str(validate_output_path(self.config.general.output_path))
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as exc:
            self.status_label.configure(text=f"Unable to open folder: {exc}", text_color="#E74C3C")

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = KyroApp()
    app.mainloop()


if __name__ == "__main__":
    main()
