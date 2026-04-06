"""File browser routes for web UI."""

import os
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from src.utils.logger import get_logger
from src.ui.web.routes import require_api_auth, _check_rate_limit

router = APIRouter(tags=["files"])
logger = get_logger(__name__)

DOWNLOAD_DIR = Path(os.environ.get("KYRO_DOWNLOAD_DIR", "downloads")).resolve()


def _safe_path(user_path: str) -> Path:
    """Resolve user path and ensure it stays within DOWNLOAD_DIR."""
    if not user_path:
        return DOWNLOAD_DIR
    target = (DOWNLOAD_DIR / user_path).resolve()
    try:
        target.relative_to(DOWNLOAD_DIR)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path traversal detected")
    return target


@router.get("/")
async def list_files(path: str = ""):
    target = _safe_path(path)
    if not target.exists() or not target.is_dir():
        return JSONResponse(status_code=404, content={"error": "Path not found"})
    items = []
    for entry in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        stat = entry.stat()
        items.append(
            {
                "name": entry.name,
                "path": str(entry.relative_to(DOWNLOAD_DIR)),
                "is_dir": entry.is_dir(),
                "size": stat.st_size if entry.is_file() else None,
                "modified": stat.st_mtime,
            }
        )
    return {"path": str(target), "items": items}


@router.get("/download/{filename:path}")
async def download_file(filename: str):
    filepath = _safe_path(filename)
    if not filepath.exists() or not filepath.is_file():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    from fastapi.responses import FileResponse

    return FileResponse(filepath, filename=filepath.name)


@router.delete("/{filename:path}", dependencies=[Depends(require_api_auth)])
async def delete_file(filename: str, confirm: bool = False, dry_run: bool = False, user: str = "authenticated"):
    _check_rate_limit("api_files_delete", limit=10)
    filepath = _safe_path(filename)
    if not filepath.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    if dry_run:
        if filepath.is_dir():
            would_delete = [str(path.relative_to(DOWNLOAD_DIR)) for path in sorted(filepath.rglob("*"))]
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

        logger.warning(
            f"Directory deletion: timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')} path={filepath} user={user} confirm={confirm}"
        )
        shutil.rmtree(filepath)
    else:
        filepath.unlink()
    return {"status": "deleted", "path": filename}
