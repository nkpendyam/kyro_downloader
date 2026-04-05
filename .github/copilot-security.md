# Copilot Security Rules — Kyro Downloader
# Reference this in copilot-instructions.md
# These rules apply to ALL generated code

## Secrets and credentials
- NEVER hardcode API keys, tokens, passwords, or secrets in any file
- ALL credentials must come from environment variables via src/config/manager.py
- NEVER log credentials, URLs with auth tokens, or cookies at any log level
- .env is gitignored — never generate code that writes secrets to any committed file
- If generating example config or test data, use placeholder values like "your-key-here"

## Input validation
- ALL URLs passed to yt-dlp must go through src/utils/validation.py first
- ALL user input from CLI, Web API, or GUI must be validated before use
- Web API: use FastAPI's Pydantic request models for every endpoint body
- Never pass raw user input to subprocess, os.system, or eval()

## Subprocess and shell
- NEVER use os.system() — always use subprocess.run() with a list of args, not a string
- NEVER use shell=True in subprocess calls
- NEVER use eval() or exec() anywhere

## File system
- NEVER use hardcoded absolute paths — use pathlib.Path and src/utils/platform.py
- Validate and sanitize all filenames from external sources before writing to disk
- Download directories must stay within user-configured KYRO_DOWNLOAD_DIR

## Dependencies
- Flag any new package not already in requirements*.txt before installing
- Do not install packages with names that resemble but differ from known libraries
- After any dependency change: run `pip-audit` to check for known CVEs

## Web UI (FastAPI)
- Every endpoint that modifies state (POST/DELETE/PATCH) must verify the request is intentional
- Add KYRO_WEB_SECRET_KEY validation before the app starts in server.py
- WebSocket connections must validate origin before accepting

## yt-dlp specific
- Catch yt_dlp.utils.DownloadError explicitly — never swallow it silently
- Never pass user-controlled format strings directly to yt-dlp options
- Cookie files must be read-only and never logged

## Code review trigger
After generating any of these, ask Copilot:
"Act as a security engineer. Review the code you just wrote for:
1. Hardcoded secrets or credentials
2. Unsanitized user input reaching subprocess or file paths
3. Missing error handling on yt-dlp calls
4. Any new dependency not in requirements.txt"
