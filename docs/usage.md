# Usage Guide

## CLI Usage

### Basic Download
```bash
kyro download https://www.youtube.com/watch?v=dQw4w9WgXcQ
kyro dl https://vimeo.com/123456  # alias
```

### Audio Only (MP3)
```bash
kyro mp3 https://www.youtube.com/watch?v=dQw4w9WgXcQ
kyro audio https://soundcloud.com/artist/track --format flac
```

### Playlist Download
```bash
kyro playlist https://www.youtube.com/playlist?list=PLxxx
kyro pl https://youtube.com/playlist?list=xxx --workers 5 --max 10
kyro playlist URL --mp3 --audio-format flac  # audio-only playlist
```

### Batch Download
```bash
kyro batch urls.txt --workers 3
kyro b urls.txt --mp3  # audio-only batch
```

### Video Info
```bash
kyro info https://youtube.com/watch?v=xxx --subs --sponsorblock
```

### Search
```bash
kyro search "python tutorial" --platform youtube --max-results 20
```

### Advanced Commands
```bash
kyro convert input.mp4 mp3 --remove-original
kyro compress input.mp4 --quality high
kyro schedule add --url "https://..." --time "2024-01-01T10:00:00"
kyro schedule list
kyro archive --clear
kyro stats
kyro platforms
kyro config show
kyro config reset
```

### Interactive Mode
```bash
kyro  # launches interactive prompt with menu
```

### Flags
| Flag | Description |
|------|-------------|
| `--output`, `-o` | Output directory |
| `--format`, `-f` | Format ID |
| `--quality`, `-q` | Quality preset (best, 1080p, 720p, 480p) |
| `--hdr` | Download HDR version |
| `--dolby` | Download with Dolby audio |
| `--proxy` | Proxy URL |
| `--cookies` | Cookies file path |
| `--rate-limit` | Rate limit (e.g. 1M) |
| `--sponsorblock` | Enable SponsorBlock |
| `--verbose`, `-v` | Enable verbose logging |
| `--dry-run` | Show what would be downloaded |
| `--no-banner` | Hide startup banner |
| `--update` | Update yt-dlp |
| `--config` | Path to config file |

## GUI Usage

Launch the GUI:
```bash
python -m src.gui.gui_main
# or
kyro-gui  # after install.sh
```

### Tabs
1. **Download** - Paste URL, fetch info, select quality/format, download
2. **Queue** - View, pause, resume, cancel downloads
3. **History** - Search and filter download history
4. **Search** - Search YouTube/SoundCloud directly
5. **Statistics** - View download statistics dashboard
6. **Settings** - Configure output path, workers, notifications, language, accessibility

### Keyboard Shortcuts
- `Ctrl+V` - Paste URL from clipboard
- `Enter` - Fetch info / Start download
- `Ctrl+S` - Save settings
- `Ctrl+R` - Refresh queue

## Supported Platforms
YouTube, Instagram, TikTok, Facebook, X/Twitter, Vimeo, SoundCloud, Reddit, Twitch, Threads, Pinterest, Snapchat, LinkedIn, Bandcamp, Dailymotion, Bilibili, Tumblr, PeerTube, and 1000+ more via yt-dlp.

Supports: Videos, Audio, Stories, Posts, Reels/Shorts, Live Streams, HDR, Dolby Atmos.
