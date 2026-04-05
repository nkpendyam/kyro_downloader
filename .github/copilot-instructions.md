# Kyro Downloader — Copilot Instructions

## Project summary
Kyro is a production-grade Python media downloader wrapping yt-dlp.
It exposes four interfaces: CLI (rich/pyfiglet), GUI (CustomTkinter), TUI (Textual), Web (FastAPI + WebSocket).
It supports 1000+ platforms, 8K/HDR/Dolby Atmos, 298 automated tests, a plugin system, and cross-platform packaging.

## Python version
3.10+ required. Use 3.11–3.12 for PyInstaller builds. Never use 3.14+.

## Stack
- Core engine:    yt-dlp, loguru, pydantic, pyyaml, requests, packaging
- CLI:            rich, pyfiglet, pyperclip
- GUI:            customtkinter, pillow
- TUI:            textual
- Web:            fastapi, uvicorn, jinja2, python-multipart
- Utils:          plyer (notifications), loguru (logging)
- Test:           pytest, ruff (lint)
- Build:          pyinstaller (kyro.spec)

## Architecture — always follow this
src/
  core/       → Download engine only (downloader.py, queue.py, progress.py, retry.py, concurrent.py, download_manager.py)
  services/   → Feature modules — one responsibility per file (36 services)
  config/     → Pydantic models + YAML (schema.py, manager.py, defaults.py)
  cli/commands/ → One file per CLI command (20+ commands)
  gui/components/ → One component per file (CustomTkinter widgets)
  gui/pages/  → One page per file (7 tabs)
  ui/web/     → FastAPI routes, WebSocket, static, templates
  plugins/    → Plugin loader + API + builtin plugins
  utils/      → Shared helpers (logger, validation, ffmpeg, platform, etc.)
tests/        → Mirror of src/ structure, one test file per module

## Coding rules — always follow these
- Type hints on every function signature (Python 3.10+ style: use `X | Y` not `Union[X, Y]`)
- Pydantic models for ALL config and input validation (see src/config/schema.py)
- loguru for ALL logging — never use print() for debug output
- Never hardcode paths — use pathlib.Path and platform.py helpers
- Async where the interface is async (FastAPI routes, WebSocket handlers)
- Sync for core downloader logic (yt-dlp is sync)
- One class or logical group per file — never dump multiple unrelated classes in one file
- All new CLI commands go in src/cli/commands/ as a new file
- All new services go in src/services/ as a new file
- All new GUI components go in src/gui/components/

## Error handling
- Use loguru: `from loguru import logger` → `logger.error(...)`, `logger.warning(...)`
- Raise specific exceptions, never bare `except:`
- yt-dlp errors: catch `yt_dlp.utils.DownloadError` explicitly
- FastAPI routes: use HTTPException with appropriate status codes

## Testing
- Every new module in src/ must have a corresponding test_ file in tests/
- Use pytest fixtures from tests/conftest.py
- Run: `python -m pytest tests/ -v`
- Lint: `python -m ruff check src/ tests/`
- Coverage: `python -m pytest tests/ --cov=src`

## Config
- All user settings go through src/config/schema.py (Pydantic) + config/default.yaml
- Environment variables: load via python-dotenv from .env (never os.environ.get directly — use config manager)
- Never hardcode API keys, tokens, or credentials anywhere

## Entry points
- CLI:  `kyro` → src/main.py or src/cli/__main__.py
- GUI:  `python -m src.gui.gui_main`
- TUI:  `kyro tui` → src/ui/tui.py
- Web:  `kyro web` → src/ui/web/server.py

## Plugin system
- Plugins live in src/plugins/builtin/ or user plugin dirs
- All plugins must implement the API defined in src/plugins/api.py
- Use src/plugins/loader.py for discovery — never import plugins directly

## Build
- Windows EXE: `pyinstaller kyro.spec` (Python 3.11–3.12 only)
- Do NOT change kyro.spec without testing the full build
- Docker: docker/Dockerfile + docker/docker-compose.yml

## What NOT to do
- Never add logic to main.py — it is an entry point only
- Never import GUI modules from core/ or services/ (no circular deps)
- Never use os.system() — use subprocess.run() with explicit args list
- Never store credentials in code or config files committed to git
- Never install a new dependency without adding it to the correct requirements file
