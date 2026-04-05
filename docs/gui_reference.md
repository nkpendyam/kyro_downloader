# GUI Reference

## Overview

The Kyro Downloader GUI is built with CustomTkinter and features 7 tabs for complete download management.

## Tabs

### 1. Download Tab
- **URL Input** - Paste any supported URL
- **Fetch Info** - Retrieves video metadata and available formats
- **Smart Quality Selector** - Auto-detected options like "8K HDR + Dolby", "4K", "1080p"
- **Format Toggle** - Switch between Video and Audio mode
- **Smart Audio Selector** - Dynamically detects source audio streams and combines them with transcode presets
- **Audio Format** - mp3, flac, aac, opus, wav, alac, ogg
- **Subtitle Controls** - Toggle subtitle download, embedding, and languages (comma-separated)
- **Download/Queue/Batch** buttons
- **Progress bar** with real-time speed display
- **Cancel** button for active downloads

### 2. Queue Tab
- Start Queue, Refresh, Clear Completed buttons
- Shows all queued downloads with status and format info

### 3. History Tab
- Shows all past downloads with status, date, and file size
- Refresh and Clear All buttons

### 4. Search Tab
- Search YouTube or SoundCloud directly
- Platform selector dropdown
- Results show title, URL, duration, and views

### 5. Statistics Tab
- Download statistics dashboard
- Total downloads, success rate, total data, total time

### 6. Schedule Tab
- Add scheduled downloads
- Shows all scheduled downloads with time and repeat settings

### 7. Settings Tab
- **General**: Download path
- **Download**: Max retries, workers, rate limit
- **Features**: Notifications, auto-update, duplicate check
- **Plugins**: Enable/disable plugins with version info
- Save Settings button

## Keyboard Shortcuts
- `Ctrl+V` - Focus URL input
- `Enter` - Fetch info / Start download
- `Ctrl+S` - Save settings
- `Ctrl+Q` - Quit application

## Theme
- Click "Toggle Theme" in header to switch between Dark and Light modes
