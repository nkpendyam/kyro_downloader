# Kyro Downloader - Installers

This directory contains build scripts for creating native installers on each platform.

## Quick Start

### Windows (EXE via PyInstaller)
The Windows build is automated via GitHub Actions. On push of a version tag (`v*`), the release workflow builds a standalone `.exe` using PyInstaller.

Manual build:
```bash
pip install pyinstaller customtkinter>=0.25.0
pyinstaller kyro.spec
```
Output: `dist/KyroDownloader.exe`

### Linux (AppImage)
The Linux build is automated via GitHub Actions. It creates a portable `.AppImage` that runs on any Linux distribution.

Manual build:
```bash
pip install pyinstaller customtkinter>=0.25.0
pyinstaller --name KyroDownloader --onedir --add-data "config:config" --add-data "src:src" --hidden-import=src --hidden-import=src.core --hidden-import=src.services --hidden-import=src.utils --hidden-import=src.config --hidden-import=src.gui src/gui/gui_main.py
```

### macOS (DMG)
The macOS build is automated via GitHub Actions. It creates a `.dmg` disk image.

Manual build:
```bash
pip install pyinstaller customtkinter>=0.25.0
pyinstaller --name KyroDownloader --windowed --onedir --add-data "config:config" --add-data "src:src" --hidden-import=src --hidden-import=src.core --hidden-import=src.services --hidden-import=src.utils --hidden-import=src.config --hidden-import=src.gui src/gui/gui_main.py
hdiutil create -volname "Kyro Downloader" -srcfolder dist/KyroDownloader -ov -format UDZO kyro-downloader.dmg
```

## Legacy Package Scripts (Not Recommended)

These scripts exist for reference but are superseded by the GitHub Actions release pipeline:

- `debian/` - DEB package for Debian/Ubuntu (use AppImage instead)
- `rpm/` - RPM package for Fedora/RHEL (use AppImage instead)
- `windows/kyro_downloader.iss` - Inno Setup script (use PyInstaller EXE instead)
- `macos/build-dmg.sh` - Legacy DMG script (use GitHub Actions instead)

## Release Process

1. Update version: `python scripts/bump_version.py patch`
2. Update `CHANGELOG.md`
3. Commit: `git add -A && git commit -m "Release vX.Y.Z"`
4. Tag: `git tag vX.Y.Z`
5. Push: `git push origin main --tags`
6. GitHub Actions builds EXE, AppImage, DMG and creates GitHub Release automatically
