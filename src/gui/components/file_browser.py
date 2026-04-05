"""File browser component for downloaded files."""
import os
from pathlib import Path
from datetime import datetime
from src.utils.logger import get_logger
logger = get_logger(__name__)

class FileBrowser:
    def __init__(self, root_path="./downloads"):
        self.root_path = Path(root_path)

    def list_files(self, directory=None, sort_by="date", reverse=True):
        dir_path = Path(directory) if directory else self.root_path
        if not dir_path.exists(): return []
        files = []
        for f in dir_path.iterdir():
            if f.is_file():
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": f.suffix,
                })
            elif f.is_dir():
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size": 0,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "extension": "",
                    "is_dir": True,
                })
        if sort_by == "date":
            files.sort(key=lambda x: x["modified"], reverse=reverse)
        elif sort_by == "size":
            files.sort(key=lambda x: x["size"], reverse=reverse)
        elif sort_by == "name":
            files.sort(key=lambda x: x["name"].lower(), reverse=reverse)
        return files

    def get_directory_size(self, directory):
        dir_path = Path(directory)
        return sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file())

    def delete_file(self, filepath):
        try:
            Path(filepath).unlink()
            return True
        except OSError:
            return False

    def open_file(self, filepath):
        import subprocess
        import platform
        if platform.system() == "Windows": os.startfile(filepath)
        elif platform.system() == "Darwin": subprocess.run(["open", filepath])
        else: subprocess.run(["xdg-open", filepath])
