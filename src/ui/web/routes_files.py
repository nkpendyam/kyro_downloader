"""File browser routes for web UI."""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(tags=["files"])

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
        items.append({
            "name": entry.name,
            "path": str(entry.relative_to(DOWNLOAD_DIR)),
            "is_dir": entry.is_dir(),
            "size": stat.st_size if entry.is_file() else None,
            "modified": stat.st_mtime,
        })
    return {"path": str(target), "items": items}


@router.get("/download/{filename:path}")
async def download_file(filename: str):
    filepath = _safe_path(filename)
    if not filepath.exists() or not filepath.is_file():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    from fastapi.responses import FileResponse
    return FileResponse(filepath, filename=filepath.name)


@router.delete("/{filename:path}")
async def delete_file(filename: str):
    filepath = _safe_path(filename)
    if not filepath.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    if filepath.is_dir():
        import shutil
        shutil.rmtree(filepath)
    else:
        filepath.unlink()
    return {"status": "deleted", "path": filename}
