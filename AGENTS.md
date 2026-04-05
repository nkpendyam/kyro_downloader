# AGENTS.md — How to work on Kyro Downloader

## Before starting any task
1. Read `.github/copilot-instructions.md` — project rules and architecture
2. Check `TASKS.md` for the current work item
3. Identify which layer the task belongs to: core / service / cli / gui / tui / web / plugin / utils
4. Open only the files relevant to that layer

## How to implement a new feature
1. If it is a new capability (e.g. new site-specific logic, new post-processing) → add a file in `src/services/`
2. If it is a new CLI command → add a file in `src/cli/commands/` and register it in `src/cli/__init__.py`
3. If it is a new GUI page or component → add to `src/gui/pages/` or `src/gui/components/`
4. If it is a new Web API route → add to `src/ui/web/routes.py` or a new routes file
5. Always write the corresponding test in `tests/test_<module>.py`

## How to fix a bug
1. Reproduce it first — identify exactly which file and function is wrong
2. Fix only that function — do not refactor unrelated code in the same PR
3. Add or update the test that covers the broken behaviour
4. Run `python -m pytest tests/test_<relevant>.py -v` before considering it done

## Definition of done (every task)
- [ ] Feature/fix works when running the relevant interface (CLI / GUI / TUI / Web)
- [ ] `python -m pytest tests/ -v` passes with no new failures
- [ ] `python -m ruff check src/ tests/` shows no errors
- [ ] No secrets, API keys, or hardcoded paths in the diff
- [ ] New public functions have type hints and a one-line docstring

## Running the project locally
```bash
# Install all deps
pip install -e .
pip install -r requirements-dev.txt

# CLI
kyro --help

# GUI
python -m src.gui.gui_main

# TUI
kyro tui

# Web UI
kyro web --port 8000

# Tests
python -m pytest tests/ -v
python -m ruff check src/ tests/
```

## Key files to know
| File | Purpose |
|------|---------|
| src/core/downloader.py | Main yt-dlp wrapper — all download logic starts here |
| src/core/download_manager.py | Queue orchestration and worker management |
| src/config/schema.py | Pydantic models — all config validation here |
| src/config/manager.py | Load/save config.yaml and .env |
| src/plugins/api.py | Plugin interface — all plugins must implement this |
| src/ui/web/server.py | FastAPI app startup |
| src/ui/web/websocket.py | Real-time progress via WebSocket |
| tests/conftest.py | Shared pytest fixtures |

## Layer dependency rules (never violate these)
```
cli / gui / tui / web  →  core / services  →  utils / config
plugins                →  core / services  →  utils / config
                       NO reverse imports
```

## When Copilot gets confused or loops
Start a fresh chat. Paste the relevant section of this file + the specific file you are working on.
Describe the problem in 2–3 sentences. Do not carry a broken context forward.
