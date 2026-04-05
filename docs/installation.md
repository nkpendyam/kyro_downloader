# Installation Guide

## Quick Start

### Windows (Recommended)
Download the latest `.exe` from [Releases](https://github.com/nkpendyam/kyro_downloader/releases) and run it directly. No installation required.

### Linux
```bash
# Using install script
curl -sSL https://raw.githubusercontent.com/nkpendyam/kyro_downloader/main/install.sh | bash

# Or install via pip
pip install kyro-downloader
```

### macOS
Download the latest `.dmg` from [Releases](https://github.com/nkpendyam/kyro_downloader/releases).

### From Source
```bash
git clone https://github.com/nkpendyam/kyro_downloader.git
cd kyro_downloader
pip install -r requirements.txt
pip install customtkinter  # for GUI
python -m src --help
```

## Requirements
- **Python**: 3.10+ (3.11-3.12 recommended for building)
- **FFmpeg**: Required for audio extraction and format conversion
- **aria2c**: Optional, for external downloads

## Building from Source
```bash
# Install build dependencies
pip install pyinstaller customtkinter

# Build Windows EXE
pyinstaller kyro.spec

# Build Linux AppImage
# (see .github/workflows/release.yml for details)
```

> **Note**: Python 3.14+ is not yet supported by PyInstaller. Use Python 3.11-3.12 for building.

## Configuration
Config file location: `~/.config/kyro/config.yaml`

See [Configuration Reference](config.md) for all options.
