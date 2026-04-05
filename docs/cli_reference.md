# CLI Reference

## Commands

### Download Commands
| Command | Aliases | Description |
|---------|---------|-------------|
| `kyro download URL` | `dl`, `d` | Download a video |
| `kyro mp3 URL` | `audio`, `a` | Download audio only |
| `kyro playlist URL` | `pl`, `p` | Download playlist |
| `kyro batch file.txt` | `b` | Batch download from file |

### Info Commands
| Command | Aliases | Description |
|---------|---------|-------------|
| `kyro info URL` | `i` | Show video info |
| `kyro platforms` | - | List supported platforms |
| `kyro stats` | - | Show download statistics |
| `kyro archive` | - | Show download archive |

### Utility Commands
| Command | Aliases | Description |
|---------|---------|-------------|
| `kyro convert INPUT FORMAT` | - | Convert media format |
| `kyro compress INPUT` | - | Compress video file |
| `kyro schedule add URL TIME` | - | Schedule a download |
| `kyro schedule list` | - | List scheduled downloads |
| `kyro schedule remove --id ID` | - | Remove a schedule |
| `kyro channel URL` | - | Show channel info |
| `kyro livestream URL` | - | Download/record livestream |
| `kyro chapters VIDEO` | - | Show video chapters |
| `kyro external URL` | - | Download with aria2c |
| `kyro search QUERY` | - | Search platforms |

### Config Commands
| Command | Description |
|---------|-------------|
| `kyro config show` | Display current configuration |
| `kyro config save` | Save current config to file |
| `kyro config reset` | Reset to defaults and save |

### Global Flags
| Flag | Description |
|------|-------------|
| `--config PATH` | Config file path |
| `--no-banner` | Hide startup banner |
| `--verbose`, `-v` | Enable verbose logging |
| `--dry-run` | Simulate download without downloading |
| `--update` | Update yt-dlp |
| `--version` | Show version |
| `--help` | Show help |

### Download Flags
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
| `--no-notify` | Disable notifications |

### Playlist Flags
| Flag | Description |
|------|-------------|
| `--workers`, `-w` | Concurrent workers (default: 3) |
| `--max` | Max videos to download |
| `--reverse` | Reverse playlist order |
| `--random` | Shuffle playlist |
| `--sleep` | Sleep between downloads (seconds) |
| `--mp3` | Audio-only mode |
| `--audio-format` | Audio format (mp3, flac, aac, ogg, wav) |
| `--audio-quality` | Audio bitrate (default: 192) |
