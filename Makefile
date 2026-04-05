# Kyro Downloader - Development Makefile
# Usage: make [target]

PYTHON := python
VENV := venv
COMPOSE ?= docker compose

ifeq ($(OS),Windows_NT)
VENV_PYTHON := $(VENV)/Scripts/python.exe
else
VENV_PYTHON := $(VENV)/bin/python
endif

.PHONY: help install install-gui install-web install-tui dev test lint format clean run-cli run-tui run-web run-gui docker-build docker-run installer-deb installer-rpm installer-macos installer-windows browser-extension

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

install-gui: install ## Install with GUI support
	$(VENV_PYTHON) -m pip install -r requirements-gui.txt

install-web: install ## Install with Web UI support
	$(VENV_PYTHON) -m pip install -r requirements-web.txt

install-tui: install ## Install with TUI support
	$(VENV_PYTHON) -m pip install textual

dev: install ## Install all dependencies including dev
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

test: ## Run tests
	$(VENV_PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

test-cov: ## Run tests with HTML coverage report
	$(VENV_PYTHON) -m pytest tests/ -v --cov=src --cov-report=html

lint: ## Run linter
	$(VENV_PYTHON) -m ruff check src/ tests/

typecheck: ## Run type checker
	$(VENV_PYTHON) -m mypy src/ --ignore-missing-imports

format: ## Format code
	$(VENV_PYTHON) -m ruff format src/ tests/

check: lint typecheck ## Run all checks

clean: ## Clean build artifacts
	$(PYTHON) -c "import pathlib, shutil; paths=['$(VENV)','__pycache__','src/__pycache__','tests/__pycache__','.pytest_cache','.coverage','htmlcov','.mypy_cache','build','dist']; [shutil.rmtree(p, ignore_errors=True) if pathlib.Path(p).is_dir() else (pathlib.Path(p).unlink() if pathlib.Path(p).exists() else None) for p in paths]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"

run-cli: ## Run CLI
	$(VENV_PYTHON) -m src.cli

run-tui: ## Run TUI
	$(VENV_PYTHON) -m src.ui.tui

run-web: ## Run Web UI
	$(VENV_PYTHON) -m src.ui.web.server

run-gui: ## Run Desktop GUI
	$(VENV_PYTHON) -m src.gui.gui_main

docker-build: ## Build Docker image
	docker build -f docker/Dockerfile -t kyro-downloader:latest .

docker-run: ## Run Docker container
	$(COMPOSE) -f docker/docker-compose.yml up -d

docker-stop: ## Stop Docker container
	$(COMPOSE) -f docker/docker-compose.yml down

docker-logs: ## View Docker logs
	$(COMPOSE) -f docker/docker-compose.yml logs -f

linux-install: ## Install on Linux (system-wide)
	sudo cp linux/kyro-downloader.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable kyro-downloader
	sudo systemctl start kyro-downloader

linux-desktop: ## Install desktop entry on Linux
	cp linux/kyro-downloader.desktop ~/.local/share/applications/
	update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

macos-app: ## Create macOS app bundle
	bash scripts/create-macos-app.sh

release: clean ## Create release build
	$(VENV_PYTHON) -m PyInstaller --onefile --name kyro src/main.py

installer-deb: ## Build DEB package (Debian/Ubuntu)
	bash installer/debian/build-deb.sh

installer-rpm: ## Build RPM package (Fedora/RHEL)
	bash installer/rpm/build-rpm.sh

installer-macos: ## Build macOS DMG installer
	bash installer/macos/build-dmg.sh

installer-windows: ## Build Windows installer (requires Inno Setup)
	@echo "Install Inno Setup from https://jrsoftware.org/isinfo.php"
	@echo "Then run: ISCC.exe installer/windows/kyro_downloader.iss"

browser-extension: ## Package browser extensions
	@echo "Chrome extension: browser-extension/chrome/"
	@echo "  Load unpacked in chrome://extensions/"
	@echo "Firefox extension: browser-extension/firefox/"
	@echo "  Load temporary addon in about:debugging"
