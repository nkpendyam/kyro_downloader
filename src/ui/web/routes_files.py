"""File browser routes for web UI."""

import hashlib
import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config.manager import load_config
from src.utils.logger import get_logger
from src.ui.web.routes import require_api_auth, _check_rate_limit

router = APIRouter(tags=["files"])
logger = get_logger(__name__)


def get_download_dir() -> Path:
    """Resolve effective download directory from config/env at request time."""
    try:
        config = load_config()
        return Path(config.general.output_path).resolve()
    except Exception:
        return Path(os.environ.get("KYRO_DOWNLOAD_DIR", "downloads")).resolve()


def _safe_path(user_path: str) -> Path:
    """Resolve user path and ensure it stays within DOWNLOAD_DIR."""
    download_dir = get_download_dir()
    if not user_path:
        return download_dir
    target = (download_dir / user_path).resolve()
    try:
        target.relative_to(download_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path traversal detected")
    return target


def _derive_user_identity(request: Request) -> str:
    """Derive user identity from the authenticated request context without leaking token data."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        bearer_token = auth_header[7:].strip()
        token_hash = hashlib.sha256(bearer_token.encode()).hexdigest()[:12]
        return f"token:sha256:{token_hash}"
    api_token = request.headers.get("x-api-token", "")
    if api_token:
        token_hash = hashlib.sha256(api_token.encode()).hexdigest()[:12]
        return f"api_token:sha256:{token_hash}"
    return "authenticated"


@router.get("/", dependencies=[Depends(require_api_auth)])
async def list_files(path: str = ""):
    """List files and folders in the download directory."""
    target = _safe_path(path)
    download_dir = get_download_dir()
    if not target.exists() or not target.is_dir():
        return JSONResponse(status_code=404, content={"error": "Path not found"})
    items = []
    for entry in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        stat = entry.stat()
        items.append(
            {
                "name": entry.name,
                "path": str(entry.relative_to(download_dir)),
                "is_dir": entry.is_dir(),
                "size": stat.st_size if entry.is_file() else None,
                "modified": stat.st_mtime,
            }
        )
    return {"path": str(target), "items": items}


@router.get("/download/{filename:path}", dependencies=[Depends(require_api_auth)])
async def download_file(filename: str):
    """Download a file from the download directory."""
    filepath = _safe_path(filename)
    if not filepath.exists() or not filepath.is_file():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    from fastapi.responses import FileResponse

    return FileResponse(filepath, filename=filepath.name)


@router.delete("/{filename:path}", dependencies=[Depends(require_api_auth)])
async def delete_file(filename: str, request: Request, confirm: bool = False, dry_run: bool = False):
    """Delete a file or folder from the download directory."""
    app_state = getattr(request.app, "state", None)
    state = getattr(app_state, "web_state", None) if app_state else None
    if state is not None:
        _check_rate_limit("api_files_delete", limit=10, state=state)
    filepath = _safe_path(filename)
    download_dir = get_download_dir()
    if not filepath.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    user_identity = _derive_user_identity(request)
    if dry_run:
        if filepath.is_dir():
            would_delete = [str(path.relative_to(download_dir)) for path in sorted(filepath.rglob("*"))]
            return {
                "status": "dry_run",
                "path": filename,
                "is_dir": True,
                "count": len(would_delete),
                "items": would_delete,
            }
        return {"status": "dry_run", "path": filename, "is_dir": False, "count": 1, "items": [filename]}
    if filepath.is_dir():
        if not confirm:
            raise HTTPException(status_code=400, detail="Directory deletion requires confirm=true")
        import shutil

        try:
            shutil.rmtree(filepath)
            logger.warning(
                "Delete audit: "
                f"timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')} "
                f"user={user_identity} "
                f"path={filepath} type=directory result=success"
            )
        except Exception:
            logger.warning(
                "Delete audit: "
                f"timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')} "
                f"user={user_identity} "
                f"path={filepath} type=directory result=failure"
            )
            raise
    else:
        file_size = filepath.stat().st_size
        try:
            filepath.unlink()
            logger.warning(
                "Delete audit: "
                f"timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')} "
                f"user={user_identity} "
                f"path={filepath} type=file size={file_size} result=success"
            )
        except Exception:
            logger.warning(
                "Delete audit: "
                f"timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')} "
                f"user={user_identity} "
                f"path={filepath} type=file size={file_size} result=failure"
            )
            raise
    return {"status": "deleted", "path": filename}
