# TASKS.md — Kyro Downloader Work Items

## How to use this file
- Pick the top item from "In Progress" or "Up Next"
- When starting: move it to "In Progress"
- When done (tests pass, lint clean): move it to "Done"
- Add new tasks at the bottom of "Up Next" with a brief description

---

## 🔄 In Progress
<!-- Move tasks here when you start them -->


---

## 📋 Up Next
- [ ] Review all existing services for missing type hints and add them
- [ ] Add --cookies-from-browser flag to all relevant CLI commands that don't have it yet
- [ ] GUI: add drag-and-drop URL support to download_page.py
- [ ] Web UI: add authentication (basic token) to protect the REST API endpoints
- [ ] Add retry logic for network timeouts in src/core/retry.py with configurable max attempts
- [ ] Plugin: create a new auto_thumbnail.py builtin plugin for thumbnail download on all formats
- [ ] Write missing tests for src/services/cloud_upload.py and src/services/media_server.py
- [ ] Docker: add health check endpoint to docker-compose.yml

---

## ✅ Done
<!-- Move completed tasks here with date -->

---

## Notes
- Always run `python -m pytest tests/ -v` before marking a task Done
- Always run `python -m ruff check src/ tests/` before marking a task Done
- Keep tasks small — one file changed = one task ideally
