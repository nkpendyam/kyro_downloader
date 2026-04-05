# Development Guide

## Setup

```bash
git clone https://github.com/nkpendyam/kyro_downloader.git
cd kyro_downloader
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install customtkinter  # for GUI development
```

## Project Structure

```
src/
├── core/           # Download engine (downloader, queue, progress, retry)
├── services/       # Feature modules
├── utils/          # Shared utilities (validation, logging, etc.)
├── config/         # Configuration (Pydantic models, YAML)
├── cli/            # Command-line interface
├── gui/            # Desktop GUI (CustomTkinter 5.2)
│   ├── app.py      # Active 7-tab GUI runtime
│   └── components/ # Reusable GUI components
├── ui/             # TUI (Textual) and Web (FastAPI + WebSocket)
└── plugins/        # Plugin system
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_downloader.py -v
```

## Linting

```bash
python -m ruff check src/ tests/
python -m ruff check src/ tests/ --fix  # auto-fix
```

## Building

### Windows EXE
```bash
pyinstaller kyro.spec
# Output: dist/KyroDownloader.exe
```

### Linux AppImage
```bash
# See .github/workflows/release.yml for full build process
```

### Docker
```bash
docker build -f docker/Dockerfile -t kyro-downloader .
```

## Adding New Features

1. **New service**: Add to `src/services/`, export in `src/services/__init__.py`
2. **New CLI command**: Add to `src/cli/commands/`, register in `src/cli/__main__.py`
3. **New GUI feature**: Add to `src/gui/app.py` and related `src/gui/components/`
4. **New config option**: Add to `src/config/schema.py` and `src/config/defaults.py`

## Release Process

1. Update version in `src/__init__.py` and `src/utils/app_updater.py`
2. Run `python scripts/bump_version.py <new_version>`
3. Update `CHANGELOG.md`
4. Create git tag: `git tag v1.0.4 && git push origin v1.0.4`
5. CI will automatically build and create GitHub Release

## Python Version Support

- **Runtime**: Python 3.10+
- **Build**: Python 3.11-3.12 (PyInstaller compatible)
- **Not supported**: Python 3.14+ (PyInstaller incompatibility)
