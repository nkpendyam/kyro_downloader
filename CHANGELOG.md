# Changelog

All notable changes to Kyro Downloader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-04-06

### Added
- Stress and E2E test coverage for queue concurrency, executor stability, and real yt-dlp integration paths
- GUI state component persistence tests for accessibility settings, tags, and history behavior

### Changed
- Hardened persistence with UTF-8 + atomic write patterns across config/services/gui state files
- Bounded in-memory growth for progress/task and queue history tracking while preserving aggregate counters
- Improved typing consistency across config, core, and utility modules with explicit return and parameter annotations

### Fixed
- Download manager compatibility regressions (`queue_batch`, `execute`, `download_now`) and playlist outcome notifications
- Web auth and API safeguards, including restricted config key handling and unauthenticated health response minimization
- CLI/web argument forwarding and lazy banner import behavior

## [1.0.0] - 2026-04-05

### Added
- Competitor-grade CLI presets: `voice-optimized`, `music-lossless`, `podcast-fast`
- Preset-driven subtitle defaults and output naming template support in downloader config
- Web API contract test suite to detect documentation/route drift in CI
- Desktop GUI (CustomTkinter) with tags, presets, history viewer, stats charts
- Multi-language support (25 languages)
- Accessibility settings (font size, high contrast, color blind modes)
- Browser extensions (Chrome & Firefox)
- Media server integration (Plex & Jellyfin)
- Circuit breaker pattern for resilient service calls
- Auto-updater using GitHub Releases API
- Version bump script
- Automated release pipeline (EXE, AppImage, DMG)
- Queue persistence and crash recovery
- Bandwidth scheduler
- Error recovery with history tracking

### Fixed
- CLI strict typing issues in `tests/test_cli_main.py` (private symbol usage, unknown parameter/member types)
- Documentation alignment for CLI preset flags and Web API endpoint contract
- Core downloader outtmpl wiring to honor configured output templates
- date_filter.py: corrected datebefore logic (returned True instead of False)
- sponsorblock.py: fixed API URL (added /api path)
- livestream.py: use yt-dlp piping for FFmpeg, fix wait_for_video format
- external_dl.py: extract direct URL via yt-dlp before passing to aria2c
- routes_files.py: mount file router in web server
- concurrent.py: daemon=True for clean process exit
- auto_organize.py: use os.replace for Windows compatibility
- auto_compress.py: safe dict access with .get()
- media_server.py: absolute path for state file, Jellyfin auth headers
- geo_restriction.py: removed placeholder example.com proxies
- linux service: fixed env var names and removed unsupported CLI args
- RPM spec: wrapper script instead of broken symlink
- Removed empty directories (dialogs, pages, widgets, scripts, systemd)

## [0.9.0] - 2026-04-03

### Added
- Complete modular architecture (6 packages, 50+ modules)
- 20+ social media platforms
- 8K/4K HDR video with Dolby Atmos audio
- 3 UI modes: CLI, TUI, Web UI
- Download archive tracking
- Format conversion pipeline
- Video compression
- Download scheduling
- Platform search
- Channel download
- Chapter extraction
- Live stream support
- External downloader support (aria2c)
- SponsorBlock integration
- Subtitle download and embedding
- Cloud upload (S3, GDrive)
- Download statistics
- All features FREE - no paid tiers
