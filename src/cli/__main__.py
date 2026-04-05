"""CLI entry point with rich formatting."""
import argparse
import importlib
import importlib.util
import pathlib

from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from src import __version__
from src.ui.banner import show_banner
from src.config.manager import load_config, save_config
from src.config.schema import AppConfig
from src.core.download_manager import DownloadManager
from src.core.downloader import get_video_info, list_video_formats
from src.utils.validation import validate_url, validate_output_path, validate_integer, validate_batch_file
from src.utils.platform import normalize_url, get_platform_info, get_supported_platforms
from src.utils.ytdlp_updater import update_ytdlp
from src.services.thumbnails import show_thumbnail_inline
from src.services.sponsorblock import extract_video_id, get_segments, format_segments_for_display
from src.services.subtitles import get_available_subtitles


def _load_cmd(name):
    path = pathlib.Path(__file__).parent / "commands" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"cmd_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_cmd_stats = _load_cmd("stats")
_cmd_archive = _load_cmd("archive")
_cmd_convert = _load_cmd("convert")
_cmd_compress = _load_cmd("compress")
_cmd_schedule = _load_cmd("schedule")
_cmd_search = _load_cmd("search")
_cmd_channels = _load_cmd("channels")
_cmd_livestream = _load_cmd("livestream")
_cmd_chapters = _load_cmd("chapters")
_cmd_external = _load_cmd("external")

console = Console()

def create_parser():
    parser = argparse.ArgumentParser(prog="kyro", description="Kyro Downloader - Production-grade media downloader by nkpendyam", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"Kyro Downloader v{__version__}")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--no-banner", action="store_true", help="Hide banner")
    parser.add_argument("--update", action="store_true", help="Update yt-dlp")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without downloading")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    dl = subparsers.add_parser("download", aliases=["dl", "d"], help="Download a video")
    dl.add_argument("url", nargs="?", help="Video URL")
    dl.add_argument("-o", "--output", type=str, help="Output directory")
    dl.add_argument("-f", "--format", type=str, help="Format ID")
    dl.add_argument("-q", "--quality", type=str, help="Quality preset (best, 1080p, 720p, 480p)")
    dl.add_argument("--hdr", action="store_true", help="Download HDR version")
    dl.add_argument("--dolby", action="store_true", help="Download with Dolby audio")
    dl.add_argument("--proxy", type=str, help="Proxy URL")
    dl.add_argument("--cookies", type=str, help="Cookies file path")
    dl.add_argument("--rate-limit", type=str, help="Rate limit (e.g. 1M)")
    dl.add_argument("--no-notify", action="store_true", help="Disable notifications")
    dl.add_argument("--sponsorblock", action="store_true", help="Enable SponsorBlock")
    mp3 = subparsers.add_parser("mp3", aliases=["audio", "a"], help="Download audio only")
    mp3.add_argument("url", nargs="?", help="Video URL")
    mp3.add_argument("-o", "--output", type=str, help="Output directory")
    mp3.add_argument("--format", type=str, default="mp3", help="Audio format (mp3, flac, aac, ogg, wav)")
    mp3.add_argument("--quality", type=str, default="192", help="Audio bitrate")
    pl = subparsers.add_parser("playlist", aliases=["pl", "p"], help="Download playlist")
    pl.add_argument("url", nargs="?", help="Playlist URL")
    pl.add_argument("-o", "--output", type=str, help="Output directory")
    pl.add_argument("-w", "--workers", type=int, default=3, help="Concurrent workers")
    pl.add_argument("-f", "--format", type=str, help="Format ID")
    pl.add_argument("--mp3", action="store_true", help="Audio-only mode")
    pl.add_argument("--audio-format", type=str, default="mp3", help="Audio format")
    pl.add_argument("--audio-quality", type=str, default="192", help="Audio bitrate")
    pl.add_argument("--max", type=int, help="Max videos to download")
    pl.add_argument("--reverse", action="store_true", help="Reverse playlist order")
    pl.add_argument("--random", action="store_true", help="Shuffle playlist")
    pl.add_argument("--sleep", type=float, default=0, help="Sleep between downloads")
    batch = subparsers.add_parser("batch", aliases=["b"], help="Download from URL file")
    batch.add_argument("file", help="File containing URLs (one per line)")
    batch.add_argument("-o", "--output", type=str, help="Output directory")
    batch.add_argument("-w", "--workers", type=int, default=3, help="Concurrent workers")
    batch.add_argument("--mp3", action="store_true", help="Audio-only mode")
    info_p = subparsers.add_parser("info", aliases=["i"], help="Show video info")
    info_p.add_argument("url", nargs="?", help="Video URL")
    info_p.add_argument("--subs", action="store_true", help="Show available subtitles")
    info_p.add_argument("--sponsorblock", action="store_true", help="Show SponsorBlock segments")
    subparsers.add_parser("platforms", help="List supported platforms")
    cfg = subparsers.add_parser("config", help="Manage configuration")
    cfg.add_argument("action", choices=["show", "save", "reset"], help="Config action")
    cfg.add_argument("--path", type=str, help="Config file path")

    # Advanced commands
    _ = subparsers.add_parser("stats", help="Show download statistics")
    archive_p = subparsers.add_parser("archive", help="Show download archive")
    archive_p.add_argument("--clear", action="store_true", help="Clear archive")
    convert_p = subparsers.add_parser("convert", help="Convert media format")
    convert_p.add_argument("input", help="Input file")
    convert_p.add_argument("format", help="Output format (mp3, mp4, flac, etc.)")
    convert_p.add_argument("--batch", nargs="*", help="Multiple files to convert")
    convert_p.add_argument("--remove-original", action="store_true", help="Delete original after conversion")
    compress_p = subparsers.add_parser("compress", help="Compress video files")
    compress_p.add_argument("input", help="Input file")
    compress_p.add_argument("--quality", choices=["low", "medium", "high", "best"], default="medium")
    compress_p.add_argument("--batch", nargs="*", help="Multiple files to compress")
    compress_p.add_argument("--remove-original", action="store_true", help="Delete original after compression")
    schedule_p = subparsers.add_parser("schedule", help="Manage download schedules")
    schedule_p.add_argument("action", choices=["add", "list", "remove"], help="Schedule action")
    schedule_p.add_argument("--url", type=str, help="URL to schedule")
    schedule_p.add_argument("--time", type=str, help="Scheduled time (ISO format)")
    schedule_p.add_argument("--id", type=str, help="Schedule ID to remove")
    schedule_p.add_argument("--repeat", choices=["none", "daily", "weekly", "monthly"], default="none")
    search_p = subparsers.add_parser("search", help="Search platforms")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--platform", default="youtube", help="Platform to search")
    search_p.add_argument("--max-results", type=int, default=20)
    channel_p = subparsers.add_parser("channel", help="Show channel info")
    channel_p.add_argument("url", help="Channel URL")
    channel_p.add_argument("-o", "--output", type=str, help="Output directory")
    livestream_p = subparsers.add_parser("livestream", help="Download/record livestream")
    livestream_p.add_argument("url", help="Livestream URL")
    livestream_p.add_argument("-o", "--output", type=str, help="Output directory")
    livestream_p.add_argument("--record", action="store_true", help="Record with FFmpeg")
    livestream_p.add_argument("--timeout", type=int, default=3600, help="Max recording time (seconds)")
    chapters_p = subparsers.add_parser("chapters", help="Show or split video chapters")
    chapters_p.add_argument("input", help="Video file")
    chapters_p.add_argument("-o", "--output", type=str, help="Output directory for split chapters")
    chapters_p.add_argument("--split", type=str, help="Output directory to split chapters")
    external_p = subparsers.add_parser("external", help="Download with external tool (aria2c)")
    external_p.add_argument("url", help="URL to download")
    external_p.add_argument("--connections", type=int, default=16, help="Max connections")
    external_p.add_argument("--rate-limit", type=str, help="Rate limit (e.g. 1M)")
    plugins_p = subparsers.add_parser("plugins", help="Manage plugins")
    plugins_p.add_argument("action", nargs="?", default="list", choices=["list", "enable", "disable", "info"], help="Plugin action")
    plugins_p.add_argument("name", nargs="?", help="Plugin name")
    subparsers.add_parser("tui", help="Launch Textual TUI")
    web_p = subparsers.add_parser("web", help="Launch Web UI")
    web_p.add_argument("--port", type=int, default=8000, help="Web UI port")
    return parser

def cmd_download(args, config):
    url = args.url or Prompt.ask("Enter YouTube URL")
    url = normalize_url(url)
    if not validate_url(url):
        print(f"[bold red]Invalid URL: {url}[/bold red]")
        return
    output = validate_output_path(args.output or config.general.output_path)
    manager = DownloadManager(config.model_dump())
    print("\n[bold green]Fetching video info...[/bold green]")
    info, unique_name = manager.prepare_download(url, str(output))
    print(f"\n[bold]Title:[/bold] {info.title}")
    print(f"[bold]Duration:[/bold] {info.duration_str}")
    print(f"[bold]Uploader:[/bold] {info.uploader}")
    print(f"[bold]Views:[/bold] {info.view_count_str}")
    if hasattr(config, 'ui') and getattr(config.ui, 'show_thumbnail', False) and info.thumbnail:
        print("\n[bold blue]Thumbnail:[/bold blue]")
        show_thumbnail_inline(info.thumbnail)
    formats = list_video_formats(info.formats)
    if not formats:
        print("[bold red]No video-only formats available for this video[/bold red]")
        return
    if args.quality:
        target = args.quality.lower()
        if target == "best": choice = 0
        else:
            height_map = {"1080p": 1080, "720p": 720, "480p": 480, "2160p": 2160, "4k": 2160, "8k": 4320}
            target_h = height_map.get(target)
            choice = 0
            if target_h:
                best_match = 0
                for i, fmt in enumerate(formats):
                    fmt_h = fmt.get("height") or 0
                    if fmt_h <= target_h and fmt_h > (formats[best_match].get("height") or 0):
                        best_match = i
                choice = best_match
    elif args.format:
        choice = -1
        for i, fmt in enumerate(formats):
            if fmt["format_id"] == args.format:
                choice = i
                break
        if choice == -1:
            print(f"[bold red]Format {args.format} not found[/bold red]")
            return
    else:
        _display_formats(formats)
        choice_input = Prompt.ask("Select quality index")
        choice = validate_integer(choice_input, 0, len(formats) - 1)
        if choice is None:
            print("[bold red]Invalid selection[/bold red]")
            return
    format_id = formats[choice]["format_id"]
    print(f"\n[bold blue]Downloading (format: {format_id})...[/bold blue]")
    cfg = config.model_dump()
    if args.proxy: cfg["proxy"] = args.proxy
    if args.cookies: cfg["cookies_file"] = args.cookies
    if args.rate_limit: cfg["rate_limit"] = args.rate_limit
    if args.sponsorblock: cfg["sponsorblock"] = {"enabled": True}
    if args.hdr:
        cfg["hdr"] = True
    if args.dolby:
        cfg["dolby"] = True
    manager.config.update(cfg)
    manager.download_now(url, str(output), format_id)
    print("[bold green]Download complete![/bold green]")

def cmd_mp3(args, config):
    url = args.url or Prompt.ask("Enter YouTube URL")
    url = normalize_url(url)
    if not validate_url(url):
        print(f"[bold red]Invalid URL: {url}[/bold red]")
        return
    output = validate_output_path(args.output or config.general.output_path)
    manager = DownloadManager(config.model_dump())
    cfg = config.model_dump()
    cfg["audio_format"] = args.format
    cfg["audio_quality"] = args.quality
    manager.config.update(cfg)
    print(f"\n[bold green]Downloading audio ({args.format} @ {args.quality}k)...[/bold green]")
    manager.download_now(url, str(output), only_audio=True)
    print("[bold green]Audio download complete![/bold green]")

def cmd_playlist(args, config):
    url = args.url or Prompt.ask("Enter Playlist URL")
    url = normalize_url(url)
    if not validate_url(url):
        print(f"[bold red]Invalid URL: {url}[/bold red]")
        return
    output = validate_output_path(args.output or config.general.output_path)
    manager = DownloadManager(config.model_dump())
    cfg = config.model_dump()
    pl_cfg = {"concurrent_downloads": args.workers, "sleep_interval": args.sleep, "max_downloads": args.max, "playlist_reverse": args.reverse, "playlist_random": args.random}
    if args.mp3:
        cfg["audio_format"] = getattr(args, "audio_format", "mp3")
        cfg["audio_quality"] = getattr(args, "audio_quality", "192")
        pl_cfg["only_audio"] = True
    if args.format:
        pl_cfg["format_id"] = args.format
    cfg["playlist"] = pl_cfg
    manager.config.update(cfg)
    print("\n[bold green]Downloading playlist...[/bold green]")
    manager.download_playlist(url, str(output))
    print("[bold green]Playlist download complete![/bold green]")

def cmd_batch(args, config):
    try:
        urls = validate_batch_file(args.file)
    except (FileNotFoundError, PermissionError) as e:
        print(f"[bold red]{e}[/bold red]")
        return
    if not urls:
        print("[bold red]No valid URLs found in file[/bold red]")
        return
    print(f"[bold green]Found {len(urls)} URLs in {args.file}[/bold green]")
    output = validate_output_path(args.output or config.general.output_path)
    manager = DownloadManager(config.model_dump())
    manager.config["concurrent_workers"] = args.workers
    for item in manager.queue_batch(urls, output_path=str(output), only_audio=args.mp3):
        print(f"  Queued: {item.url} [{item.task_id[:8]}]")
    print(f"\n[bold blue]Starting {len(urls)} downloads with {args.workers} workers...[/bold blue]")
    manager.execute()
    print("[bold green]Batch download complete![/bold green]")

def cmd_info(args, config):
    url = args.url or Prompt.ask("Enter URL")
    url = normalize_url(url)
    if not validate_url(url):
        print(f"[bold red]Invalid URL: {url}[/bold red]")
        return
    info = get_video_info(url)
    print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    print(f"[bold]Title:[/bold] {info.title}")
    print(f"[bold]Duration:[/bold] {info.duration_str}")
    print(f"[bold]Uploader:[/bold] {info.uploader}")
    print(f"[bold]Upload Date:[/bold] {info.upload_date}")
    print(f"[bold]Views:[/bold] {info.view_count_str}")
    print(f"[bold]Type:[/bold] {'Playlist' if info.is_playlist else 'Video'}")
    if info.entries: print(f"[bold]Playlist Items:[/bold] {len(info.entries)}")
    platform = get_platform_info(url)
    if platform: print(f"[bold]Platform:[/bold] {platform['icon']} {platform['name']}")
    if hasattr(config, 'ui') and getattr(config.ui, 'show_thumbnail', False): show_thumbnail_inline(info.thumbnail)
    if args.subs:
        subs = get_available_subtitles(info.raw)
        if subs:
            print(f"\n[bold yellow]Available Subtitles ({len(subs)}):[/bold yellow]")
            for sub in subs:
                auto_tag = " [auto]" if sub["auto_generated"] else ""
                print(f"  {sub['language']} ({sub['ext']}){auto_tag}")
        else: print("\n[dim]No subtitles available[/dim]")
    if args.sponsorblock:
        video_id = extract_video_id(url)
        if video_id:
            segments = get_segments(video_id)
            print(format_segments_for_display(segments))
    print(f"[bold cyan]{'='*60}[/bold cyan]")

def cmd_platforms(args, config):
    platforms = get_supported_platforms()
    table = Table(title="Supported Platforms")
    table.add_column("Platform", style="cyan")
    table.add_column("Icon", style="magenta")
    table.add_column("Video", style="green")
    table.add_column("Audio", style="yellow")
    table.add_column("Live", style="cyan")
    table.add_column("HDR", style="green")
    table.add_column("Dolby", style="yellow")
    table.add_column("Max Quality", style="blue")
    for p in platforms:
        table.add_row(p["name"], p.get("icon",""), "Yes" if p.get("supports_video") else "No", "Yes" if p.get("supports_audio") else "No", "Yes" if p.get("supports_live") else "No", "Yes" if p.get("supports_hdr") else "No", "Yes" if p.get("supports_dolby") else "No", p.get("max_resolution","?"))
    console.print(table)

def cmd_search(args, config):
    from src.services.search import search_platform
    results = search_platform(args.query, args.platform, args.max_results)
    table = Table(title=f"Search Results for '{args.query}'")
    table.add_column("#", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("URL", style="yellow")
    for i, r in enumerate(results, 1):
        table.add_row(str(i), r.get("title", "?")[:50], r.get("url", "")[:60])
    console.print(table)

def cmd_stats(args, config):
    from src.services.statistics import StatsTracker
    stats = StatsTracker()
    summary = stats.get_summary()
    table = Table(title="Download Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for key, value in summary.items():
        table.add_row(key.replace("_", " ").title(), str(value))
    console.print(table)

def cmd_config(args, config):
    if args.action == "show":
        config_dict = config.model_dump()
        table = Table(title="Configuration")
        table.add_column("Section", style="cyan")
        table.add_column("Key", style="magenta")
        table.add_column("Value", style="green")
        for section, values in config_dict.items():
            for key, value in values.items():
                table.add_row(section, key, str(value))
        console.print(table)
    elif args.action == "save":
        path = save_config(config, args.path)
        print(f"[bold green]Config saved to: {path}[/bold green]")
    elif args.action == "reset":
        from src.config.defaults import DEFAULT_CONFIG
        config = AppConfig(**DEFAULT_CONFIG)
        path = save_config(config, args.path)
        print(f"[bold green]Config reset and saved to: {path}[/bold green]")
        return config

def cmd_plugins(args, config):
    """Handle plugin management commands."""
    from src.plugins.loader import PluginLoader
    loader = PluginLoader()
    if args.action == "list":
        table = Table(title="Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Description", style="yellow")
        for plugin in loader.list_plugins():
            table.add_row(plugin["name"], plugin["version"], "Enabled" if plugin["enabled"] else "Disabled", plugin.get("description", ""))
        console.print(table)
    elif args.action == "enable":
        if not args.name:
            print("[bold red]Plugin name required[/bold red]")
            return
        if loader.enable_plugin(args.name):
            print(f"[bold green]Enabled plugin: {args.name}[/bold green]")
        else:
            print(f"[bold red]Plugin not found: {args.name}[/bold red]")
    elif args.action == "disable":
        if not args.name:
            print("[bold red]Plugin name required[/bold red]")
            return
        if loader.disable_plugin(args.name):
            print(f"[bold green]Disabled plugin: {args.name}[/bold green]")
        else:
            print(f"[bold red]Plugin not found: {args.name}[/bold red]")
    elif args.action == "info":
        if not args.name:
            print("[bold red]Plugin name required[/bold red]")
            return
        plugin = loader.get_plugin(args.name)
        if plugin:
            print(f"[bold cyan]Name:[/bold cyan] {plugin.name}")
            print(f"[bold cyan]Version:[/bold cyan] {plugin.version}")
            print(f"[bold cyan]Description:[/bold cyan] {plugin.description}")
            print(f"[bold cyan]Enabled:[/bold cyan] {plugin.enabled}")
        else:
            print(f"[bold red]Plugin not found: {args.name}[/bold red]")

def _launch_tui():
    """Launch the Textual TUI."""
    try:
        from src.ui.tui import run_tui
        run_tui()
    except ImportError:
        print("[bold red]TUI dependencies not installed. Run: pip install textual[/bold red]")

def _launch_web(port=8000):
    """Launch the Web UI."""
    try:
        from src.ui.web.server import run_web
        run_web(port=port)
    except ImportError:
        print("[bold red]Web UI dependencies not installed. Run: pip install fastapi uvicorn[/bold red]")

def _display_formats(formats):
    table = Table(title="Available Formats")
    table.add_column("Index", style="cyan")
    table.add_column("Format ID", style="magenta")
    table.add_column("Resolution", style="green")
    table.add_column("Ext", style="yellow")
    table.add_column("Size", style="blue")
    for i, fmt in enumerate(formats):
        table.add_row(
            str(i),
            fmt.get("format_id", "?"),
            f"{fmt.get('height', '?')}p" if fmt.get("height") else "audio",
            fmt.get("ext", "?"),
            f"{fmt.get('filesize_approx', 0) / 1024 / 1024:.0f}MB" if fmt.get("filesize_approx") else "?",
        )
    console.print(table)

def interactive_mode(config):
    print("[bold cyan]Interactive Mode[/bold cyan]")
    print("1. Download video")
    print("2. Download audio (MP3)")
    print("3. Download playlist")
    print("4. Batch download")
    print("5. Search")
    print("6. Stats")
    print("7. Platforms")
    print("8. Config")
    print("q. Quit")
    while True:
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "q"])
        if choice == "q":
            break
        elif choice == "1":
            url = Prompt.ask("Enter URL")
            output = Prompt.ask("Output path", default=config.general.output_path)
            cmd_download(argparse.Namespace(url=url, output=output, format=None, quality=None, hdr=False, dolby=False, proxy=None, cookies=None, rate_limit=None, no_notify=False, sponsorblock=False), config)
        elif choice == "2":
            url = Prompt.ask("Enter URL")
            output = Prompt.ask("Output path", default=config.general.output_path)
            cmd_mp3(argparse.Namespace(url=url, output=output, format="mp3", quality="192"), config)
        elif choice == "3":
            url = Prompt.ask("Enter playlist URL")
            output = Prompt.ask("Output path", default=config.general.output_path)
            cmd_playlist(argparse.Namespace(url=url, output=output, workers=3, max=None, reverse=False, random=False, sleep=0, format=None, mp3=False, audio_format="mp3", audio_quality="192"), config)
        elif choice == "4":
            filepath = Prompt.ask("Enter batch file path")
            cmd_batch(argparse.Namespace(file=filepath, output="", workers=3, mp3=False), config)
        elif choice == "5":
            query = Prompt.ask("Search query")
            cmd_search(argparse.Namespace(query=query, platform="youtube", max_results=20), config)
        elif choice == "6":
            cmd_stats(argparse.Namespace(), config)
        elif choice == "7":
            cmd_platforms(argparse.Namespace(), config)
        elif choice == "8":
            action = Prompt.ask("Action", choices=["show", "save", "reset"])
            cmd_config(argparse.Namespace(action=action, path=None), config)



def main():
    parser = create_parser()
    args = parser.parse_args()
    try: config = load_config(args.config if hasattr(args, "config") else None)
    except Exception as e:
        print(f"[bold red]Config error: {e}[/bold red]")
        config = AppConfig()
    if args.update:
        if update_ytdlp(): print("[bold green]yt-dlp updated![/bold green]")
        else: print("[bold red]Update failed[/bold red]")
        return
    if not args.command:
        if not args.no_banner: show_banner()
        interactive_mode(config)
        return
    if not args.no_banner: show_banner()
    command_map = {
        "download": cmd_download, "dl": cmd_download, "d": cmd_download,
        "mp3": cmd_mp3, "audio": cmd_mp3, "a": cmd_mp3,
        "playlist": cmd_playlist, "pl": cmd_playlist, "p": cmd_playlist,
        "batch": cmd_batch, "b": cmd_batch,
        "info": cmd_info, "i": cmd_info,
        "platforms": cmd_platforms,
        "config": cmd_config,
        "stats": lambda a, c: _cmd_stats.show_stats(),
        "archive": lambda a, c: _cmd_archive.clear_archive() if getattr(a, 'clear', False) else _cmd_archive.show_archive(),
        "convert": lambda a, c: _cmd_convert.convert_batch(a.batch, a.format, remove_original=a.remove_original) if a.batch else _cmd_convert.convert_single(a.input, a.format, remove_original=a.remove_original),
        "compress": lambda a, c: _cmd_compress.compress_batch(a.batch, a.quality, remove_original=a.remove_original) if a.batch else _cmd_compress.compress_single(a.input, a.quality, remove_original=a.remove_original),
        "schedule": lambda a, c: _cmd_schedule.add_schedule(a.url, a.time, repeat=a.repeat) if a.action == "add" else (_cmd_schedule.remove_schedule(a.id) if a.action == "remove" else _cmd_schedule.list_schedules()),
        "search": lambda a, c: _cmd_search.search(a.query, a.platform, a.max_results),
        "channel": lambda a, c: _cmd_channels.channel_info(a.url),
        "livestream": lambda a, c: _cmd_livestream.livestream_record(a.url, getattr(a, 'output', None) or c.general.output_path, a.timeout) if a.record else _cmd_livestream.livestream_download(a.url, getattr(a, 'output', None) or c.general.output_path),
        "chapters": lambda a, c: _cmd_chapters.split_chapters(a.input, getattr(a, 'split', None) or getattr(a, 'output', None) or c.general.output_path) if getattr(a, 'split', None) else _cmd_chapters.show_chapters(a.input),
        "external": lambda a, c: _cmd_external.external_download(a.url, c.general.output_path, a.connections, getattr(a, 'rate_limit', None)),
        "plugins": lambda a, c: cmd_plugins(a, c),
        "tui": lambda a, c: _launch_tui(),
        "web": lambda a, c: _launch_web(getattr(a, 'port', 8000)),
    }
    handler = command_map.get(args.command)
    if handler:
        try:
            handler(args, config)
        except KeyboardInterrupt:
            print("\n[bold yellow]Interrupted by user[/bold yellow]")
        except Exception as e:
            print(f"[bold red]Error: {e}[/bold red]")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
