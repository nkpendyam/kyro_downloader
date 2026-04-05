"""FastAPI web server for Kyro Downloader."""
import os
import argparse

from src import __version__

def create_app(enable_auto_update=False):
    try:
        from fastapi import FastAPI
        from fastapi import Depends
        from fastapi.staticfiles import StaticFiles
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import HTMLResponse
    except ImportError:
        raise ImportError("Web UI dependencies not installed. Run: pip install fastapi uvicorn")

    from src.config.manager import load_config
    from src.ui.web.routes import router as api_router, require_api_auth
    from src.ui.web.websocket import router as ws_router
    from src.ui.web.routes_files import router as files_router

    config = load_config()
    if enable_auto_update and getattr(config.general, "auto_update", False) and not os.environ.get("PYTEST_CURRENT_TEST"):
        from src.utils.ytdlp_updater import auto_update_on_startup
        auto_update_on_startup(check_only=False)
    web_config = config.web
    app = FastAPI(title="Kyro Downloader API", description="REST API and WebSocket interface for Kyro Downloader by nkpendyam", version="1.0.0")
    cors_origins = web_config.cors_origins
    allow_creds = "*" not in cors_origins
    app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=allow_creds, allow_methods=["*"], allow_headers=["*"])
    app.include_router(api_router, prefix="/api", dependencies=[Depends(require_api_auth)])
    app.include_router(ws_router, prefix="/ws")
    app.include_router(files_router, prefix="/api/files", dependencies=[Depends(require_api_auth)])
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    _index_html = ""
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            _index_html = f.read()
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return _index_html if _index_html else "<h1>Kyro Downloader</h1><p>Web UI templates not found</p>"

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app

def run_web(host="127.0.0.1", port=8000, debug=False):
    import uvicorn
    app = create_app(enable_auto_update=True)
    uvicorn.run(app, host=host, port=port, reload=debug, log_level="debug" if debug else "info")


def create_parser() -> argparse.ArgumentParser:
    """Create web server CLI parser."""
    parser = argparse.ArgumentParser(description="Run Kyro Downloader Web UI")
    parser.add_argument("--host", type=str, help="Host to bind (default from config)")
    parser.add_argument("--port", type=int, help="Port to bind (default from config)")
    parser.add_argument("--debug", action="store_true", help="Enable debug/reload mode")
    parser.add_argument("-v", "--version", action="store_true", help="Show version and exit")
    return parser


def main() -> None:
    """CLI entrypoint for web server module."""
    args = create_parser().parse_args()
    if args.version:
        print(f"Kyro Downloader v{__version__}")
        return

    from src.config.manager import load_config

    config = load_config()
    host = args.host or config.web.host
    port = args.port or config.web.port
    debug = bool(args.debug or config.web.debug)
    run_web(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
