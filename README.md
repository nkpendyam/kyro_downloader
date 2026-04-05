# Kyro Downloader

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-orange)]()
[![Tests](https://img.shields.io/badge/Tests-passing-brightgreen)]()
[![CI](https://github.com/nkpendyam/kyro_downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/nkpendyam/kyro_downloader/actions)

Production-grade media downloader by **nkpendyam** - download videos, audio, stories, posts, and playlists from 1000+ social media platforms in up to 8K HDR with Dolby Atmos audio.

## Features

### Core
- 8K/4K/1080p/720p video downloads with HDR support
- Audio extraction (MP3, FLAC, AAC, OGG, WAV, Opus)
- Dolby Atmos audio download
- Full playlist downloading with concurrency control
- Batch download from URL files
- Retry with exponential/linear/fixed backoff
- Resume interrupted downloads
- Concurrent parallel downloads (configurable workers)
- Rate limiting and proxy support

### Platform Support
YouTube, Instagram, TikTok, Facebook, X/Twitter, Vimeo, SoundCloud, Reddit, Twitch, Threads, Pinterest, Snapchat, LinkedIn, Bandcamp, Dailymotion, Bilibili, Tumblr, PeerTube, and **1000+ more** via yt-dlp.

Supports: Videos, Audio, Stories, Posts, Reels/Shorts, Live Streams, HDR, Dolby Atmos.

### Intelligence
- Duplicate detection (by name and content hash)
- SponsorBlock integration (skip sponsors, intros, outros)
- Subtitle download and embedding (auto-generated + manual)
- Metadata embedding (title, artist, thumbnail)
- Auto yt-dlp update checker
- Video trimming, compression, and format conversion
- Download scheduling
- Channel and livestream support
- Download statistics and analytics dashboard

### Interfaces
- **CLI** - 20+ commands with rich formatting, interactive mode, plugin management
- **GUI** - Modern desktop app with CustomTkinter (7 tabs: Download, Queue, History, Search, Stats, Schedule, Settings)
- **TUI** - Interactive terminal UI with Textual (`kyro tui`)
- **Web UI** - FastAPI with REST API + WebSocket progress (`kyro web`)

### Smart Features
- **Auto Format Detection** - Automatically detects available qualities, HDR, Dolby, audio codecs
- **Smart Quality Labels** - Shows "8K HDR + Dolby", "4K HDR", "1080p" based on what's actually available
- **Full Audio Spectrum** - 11 presets from 64kbps (Voice) to Lossless (FLAC/ALAC/WAV)
- **Plugin System** - Auto-discover and manage plugins (Auto Compress, Auto Convert, Auto Organize, Auto Subtitles)
- **Download Scheduling** - Schedule downloads for specific times with repeat options
- **Channel Subscriptions** - Subscribe to channels for automatic new video detection

## Quick Start

### Windows (Recommended)
Download the latest `.exe` from [Releases](https://github.com/nkpendyam/kyro_downloader/releases) and run it directly.

### pip install
```bash
pip install kyro-downloader  # CLI only
pip install kyro-downloader[web]  # CLI + Web UI
pip install customtkinter  # For GUI
```

### From Source
```bash
git clone https://github.com/nkpendyam/kyro_downloader.git
cd kyro_downloader
pip install -e .
kyro --help              # CLI
kyro tui                 # Terminal UI
kyro web                 # Web UI
python -m src.gui.gui_main  # Desktop GUI
```

### Docker
```bash
docker build -f docker/Dockerfile -t kyro-downloader .
docker run kyro-downloader --help
```

### Linux/macOS Install Script
```bash
curl -sSL https://raw.githubusercontent.com/nkpendyam/kyro_downloader/main/install.sh | bash
```

## CLI Quick Reference

```bash
kyro download URL              # Download video
kyro download URL -q 1080p     # Specific quality
kyro download URL --hdr        # HDR version
kyro download URL --dolby      # Dolby Atmos
kyro mp3 URL                   # Audio extraction
kyro mp3 URL --format flac     # FLAC audio
kyro playlist URL -w 5         # Playlist with 5 workers
kyro batch urls.txt            # Batch download
kyro info URL --subs           # Video info + subtitles
kyro search "query"            # Search platforms
kyro stats                     # Download statistics
kyro platforms                 # List supported platforms
kyro config show               # Show configuration
kyro plugins list              # List all plugins
kyro plugins enable <name>     # Enable a plugin
kyro tui                       # Launch Terminal UI
kyro web --port 8000           # Launch Web UI
kyro --update                  # Update yt-dlp
kyro                           # Interactive mode
```

See [CLI Reference](docs/cli_reference.md) for all commands and flags.

## Documentation

| Document | Description |
|----------|-------------|
| [Installation](docs/installation.md) | Install on Windows, Linux, macOS, Docker, pip |
| [Usage Guide](docs/usage.md) | CLI, GUI, TUI, and Web UI usage examples |
| [Configuration](docs/config.md) | All config options, env variables, plugins |
| [CLI Reference](docs/cli_reference.md) | Complete command reference with all flags |
| [GUI Reference](docs/gui_reference.md) | All 7 tabs, quality selector, plugins |
| [TUI Reference](docs/tui_reference.md) | Terminal UI screens and shortcuts |
| [Web API](docs/web_api.md) | REST API endpoints and WebSocket |
| [Plugin Development](docs/plugins.md) | How to write and install plugins |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [Development](docs/development.md) | Build, test, and contribute |

## Requirements
- **Python**: 3.10+ (3.11-3.12 recommended for building)
- **FFmpeg**: Required for audio extraction and format conversion
- **aria2c**: Optional, for external downloads

## Testing

```bash
python -m pytest tests/ -v          # Run all tests
python -m pytest tests/ --cov=src   # With coverage
python -m ruff check src/ tests/    # Lint check
```

## Building

```bash
# Windows EXE
pip install pyinstaller customtkinter
pyinstaller kyro.spec

# Linux AppImage / macOS DMG
# See .github/workflows/release.yml
```

> **Note**: Python 3.14+ is not yet supported by PyInstaller. Use Python 3.11-3.12 for building.

## Architecture

```
src/
├── core/           # Download engine (downloader, queue, progress, retry, concurrent)
├── services/       # 36 feature modules (SponsorBlock, subtitles, search, plugins, etc.)
├── utils/          # Shared utilities (validation, logging, notifications, etc.)
├── config/         # Pydantic config models + YAML management
├── cli/            # 20+ CLI commands with rich formatting, interactive mode
├── gui/            # CustomTkinter desktop app (7 tabs, smart quality selector)
├── ui/             # TUI (Textual) and Web (FastAPI + WebSocket)
└── plugins/        # Plugin system (loader, API, 4 builtin plugins)
```

## License
MIT License - see [LICENSE](LICENSE)

**Developed by [nkpendyam](https://github.com/nkpendyam)**

Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) | UI by [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) + [Rich](https://github.com/Textualize/rich) + [Textual](https://github.com/Textualize/textual)
