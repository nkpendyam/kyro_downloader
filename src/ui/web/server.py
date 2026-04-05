"""FastAPI web server for Kyro Downloader."""
import os

def create_app():
    try:
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import HTMLResponse
    except ImportError:
        raise ImportError("Web UI dependencies not installed. Run: pip install fastapi uvicorn")

    from src.config.manager import load_config
    from src.ui.web.routes import router as api_router
    from src.ui.web.websocket import router as ws_router
    from src.ui.web.routes_files import router as files_router

    config = load_config()
    web_config = config.web
    app = FastAPI(title="Kyro Downloader API", description="REST API and WebSocket interface for Kyro Downloader by nkpendyam", version="2.0.0")
    cors_origins = web_config.cors_origins
    allow_creds = "*" not in cors_origins
    app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=allow_creds, allow_methods=["*"], allow_headers=["*"])
    app.include_router(api_router, prefix="/api")
    app.include_router(ws_router, prefix="/ws")
    app.include_router(files_router, prefix="/api/files")
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
    return app

def run_web(host="127.0.0.1", port=8000, debug=False):
    import uvicorn
    app = create_app()
    uvicorn.run(app, host=host, port=port, reload=debug, log_level="debug" if debug else "info")

if __name__ == "__main__":
    from src.config.manager import load_config
    config = load_config()
    run_web(host=config.web.host, port=config.web.port, debug=config.web.debug)
