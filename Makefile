# Kyro Downloader - Development Makefile
# Usage: make [target]

PYTHON := python3
PIP := pip3
VENV := venv
ACTIVATE := . $(VENV)/bin/activate

.PHONY: help install install-gui dev test lint format clean run-cli run-tui run-web run-gui docker-build docker-run installer-deb installer-rpm installer-macos installer-windows browser-extension

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PYTHON) -m venv $(VENV)
	. $(ACTIVATE) && $(PIP) install --upgrade pip
	. $(ACTIVATE) && $(PIP) install -r requirements.txt
	. $(ACTIVATE) && $(PIP) install -r requirements-dev.txt

install-gui: install ## Install with GUI support
	. $(ACTIVATE) && $(PIP) install -r requirements-web.txt
	. $(ACTIVATE) && $(PIP) install flet

dev: install ## Install all dependencies including dev
	. $(ACTIVATE) && $(PIP) install -r requirements-dev.txt

test: ## Run tests
	. $(ACTIVATE) && pytest tests/ -v --cov=src --cov-report=term-missing

test-cov: ## Run tests with HTML coverage report
	. $(ACTIVATE) && pytest tests/ -v --cov=src --cov-report=html

lint: ## Run linter
	. $(ACTIVATE) && ruff check src/ tests/

typecheck: ## Run type checker
	. $(ACTIVATE) && mypy src/ --ignore-missing-imports

format: ## Format code
	. $(ACTIVATE) && ruff format src/ tests/

check: lint typecheck ## Run all checks

clean: ## Clean build artifacts
	rm -rf $(VENV) __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache/
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

run-cli: ## Run CLI
	. $(ACTIVATE) && $(PYTHON) -m src.cli

run-tui: ## Run TUI
	. $(ACTIVATE) && $(PYTHON) -m src.ui.tui

run-web: ## Run Web UI
	. $(ACTIVATE) && $(PYTHON) -m src.ui.web.server

run-gui: ## Run Desktop GUI
	. $(ACTIVATE) && $(PYTHON) -m src.gui.gui_main

docker-build: ## Build Docker image
	docker build -f docker/Dockerfile -t kyro-downloader:latest .

docker-run: ## Run Docker container
	docker-compose -f docker/docker-compose.yml up -d

docker-stop: ## Stop Docker container
	docker-compose -f docker/docker-compose.yml down

docker-logs: ## View Docker logs
	docker-compose -f docker/docker-compose.yml logs -f

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
	. $(ACTIVATE) && $(PYTHON) -m PyInstaller --onefile --name kyro src/main.py

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
