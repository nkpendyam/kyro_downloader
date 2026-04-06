"""FastAPI web server for Kyro Downloader."""

import asyncio
import os
import argparse
from contextlib import asynccontextmanager

from src import __version__


def create_app(enable_auto_update=False):
    try:
        from fastapi import FastAPI
        from fastapi import Depends
        from fastapi import Request
        from fastapi.staticfiles import StaticFiles
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import HTMLResponse, JSONResponse
    except ImportError:
        raise ImportError("Web UI dependencies not installed. Run: pip install fastapi uvicorn")

    from src.config.manager import load_config
    from src.ui.web.routes import router as api_router, require_api_auth
    from src.ui.web.websocket import router as ws_router
    from src.ui.web.routes_files import router as files_router
    from src.ui.web.routes import shutdown_executor, init_web_state

    try:
        config = load_config()
    except Exception as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e
    if (
        enable_auto_update
        and getattr(config.general, "auto_update", False)
        and not os.environ.get("PYTEST_CURRENT_TEST")
    ):
        from src.utils.ytdlp_updater import auto_update_on_startup

        auto_update_on_startup(check_only=False)
    web_config = config.web

    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        yield
        state = getattr(_app.state, "web_state", None)
        if state and state.get("manager_instance"):
            manager = state["manager_instance"]
            try:
                manager.stop()
            except Exception:
                pass
            try:
                manager._save_queue_state()
            except Exception:
                pass
            stats = getattr(manager, "stats", None)
            if stats:
                try:
                    stats.force_save()
                except Exception:
                    pass
            archive = getattr(manager, "archive", None)
            if archive:
                try:
                    archive.force_save()
                except Exception:
                    pass
        from src.ui.web.websocket import get_connected_clients, remove_client

        for client_id in list(get_connected_clients().keys()):
            remove_client(client_id)
        shutdown_executor(state)

    app = FastAPI(
        title="Kyro Downloader API",
        description="REST API and WebSocket interface for Kyro Downloader by nkpendyam",
        version="1.0.0",
        lifespan=_lifespan,
    )
    app.state.web_state = init_web_state()
    cors_origins = web_config.cors_origins
    allow_creds = "*" not in cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_creds,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def csrf_origin_middleware(request: Request, call_next):
        is_mutating = request.method in {"POST", "PUT", "PATCH", "DELETE"}
        path = request.url.path
        is_api_path = path == "/api" or path.startswith("/api/") or path == "/api/v1" or path.startswith("/api/v1/")
        if is_mutating and is_api_path:
            origin = request.headers.get("origin")
            if origin and "*" not in cors_origins and origin not in cors_origins:
                return JSONResponse(status_code=403, content={"detail": "Forbidden origin"})
            if "*" in cors_origins:
                authorization = request.headers.get("authorization", "")
                x_api_token = request.headers.get("x-api-token", "")
                if not authorization.startswith("Bearer ") and not x_api_token:
                    app_state = getattr(request.app, "state", None)
                    if app_state:
                        state = getattr(app_state, "web_state", None)
                        if state and state.get("config_instance"):
                            web_cfg = getattr(state["config_instance"], "web", None)
                            if web_cfg and getattr(web_cfg, "api_token", None):
                                return JSONResponse(
                                    status_code=403, content={"detail": "CSRF token required with wildcard CORS"}
                                )
        return await call_next(request)

    @app.middleware("http")
    async def request_timeout_middleware(request: Request, call_next):
        path = request.url.path
        skip_timeout_prefixes = (
            "/api/download",
            "/api/v1/download",
            "/api/progress",
            "/api/v1/progress",
            "/ws",
        )
        if path.startswith(skip_timeout_prefixes):
            return await call_next(request)
        request_task = asyncio.create_task(call_next(request))
        try:
            return await asyncio.wait_for(request_task, timeout=300)
        except TimeoutError:
            request_task.cancel()
            await asyncio.gather(request_task, return_exceptions=True)
            return JSONResponse(status_code=504, content={"detail": "Request timeout"})

    @app.middleware("http")
    async def legacy_api_deprecation_middleware(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path == "/api" or path.startswith("/api/"):
            if not (path == "/api/v1" or path.startswith("/api/v1/")):
                response.headers["Deprecation"] = "true"
                response.headers["Link"] = '</api/v1>; rel="successor-version"'
        return response

    app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(require_api_auth)])
    app.include_router(files_router, prefix="/api/v1/files", dependencies=[Depends(require_api_auth)])
    # Legacy compatibility routes (deprecated)
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
    async def health(request: Request):
        state = getattr(app.state, "web_state", None)
        configured_token = None
        if state:
            from src.ui.web.routes import _get_configured_api_token

            configured_token = _get_configured_api_token(state)

        is_authenticated = False
        if configured_token:
            authorization = request.headers.get("authorization", "")
            provided_token = ""
            if authorization.lower().startswith("bearer "):
                provided_token = authorization[7:].strip()
            else:
                provided_token = request.headers.get("x-api-token", "").strip()
            is_authenticated = provided_token == configured_token
        else:
            is_authenticated = True

        if not is_authenticated:
            return {"status": "ok", "version": __version__}

        from src.utils.ffmpeg import check_ffmpeg
        from src.ui.web.websocket import get_active_connection_count

        queue_status = {"pending": 0, "active": 0, "completed": 0, "failed": 0}
        executor_running = False
        scheduler_health = False
        if state and state.get("manager_instance"):
            manager = state["manager_instance"]
            mgr_status = manager.get_status()
            queue_status = {
                "pending": mgr_status.get("pending", 0),
                "active": mgr_status.get("active", 0),
                "completed": mgr_status.get("completed", 0),
                "failed": mgr_status.get("failed", 0),
            }
            executor_running = mgr_status.get("executor_running", False)
            scheduler = getattr(manager, "scheduler", None)
            if scheduler:
                scheduler_health = scheduler.is_healthy()
        download_dir = None
        disk_available = None
        try:
            if state and state.get("config_instance"):
                download_dir = state["config_instance"].general.output_path
            if download_dir:
                import shutil

                usage = shutil.disk_usage(download_dir)
                disk_available = usage.free
        except Exception:
            pass
        ffmpeg_found = False
        ffmpeg_version = None
        try:
            ffmpeg_found = check_ffmpeg()
            if ffmpeg_found:
                import subprocess

                result = subprocess.run(
                    ["ffmpeg", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                ffmpeg_version = result.stdout.splitlines()[0] if result.stdout else None
        except Exception:
            pass
        try:
            import yt_dlp

            ytdlp_version = yt_dlp.version.__version__
        except Exception:
            ytdlp_version = None
        return {
            "status": "ok",
            "version": __version__,
            "queue": queue_status,
            "executor_running": executor_running,
            "scheduler_health": scheduler_health,
            "active_websocket_connections": get_active_connection_count(),
            "disk_available_bytes": disk_available,
            "download_dir": download_dir,
            "ffmpeg": {"found": ffmpeg_found, "version": ffmpeg_version},
            "yt_dlp_version": ytdlp_version,
        }

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

    try:
        config = load_config()
    except Exception as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e
    host = args.host or config.web.host
    port = args.port or config.web.port
    debug = bool(args.debug or config.web.debug)
    run_web(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
