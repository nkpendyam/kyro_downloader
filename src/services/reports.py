"""Download reports - generate HTML reports of download history."""

import html
from pathlib import Path
from datetime import datetime
from src.services.statistics import StatsTracker
from src.services.archive import DownloadArchive
from src.utils.logger import get_logger

logger = get_logger(__name__)

REPORTS_DIR = Path.home() / ".config" / "kyro" / "reports"


def generate_html_report(output_path: str | None = None, days: int = 30) -> str:
    """Generate an HTML report of download history."""
    archive = DownloadArchive()
    stats = StatsTracker()
    entries = archive.list_all()

    cutoff = datetime.now().timestamp() - (days * 86400)
    recent = [
        e
        for e in entries
        if e.get("downloaded_at", e.get("timestamp", ""))[:10] >= datetime.fromtimestamp(cutoff).strftime("%Y-%m-%d")
    ]

    stats_data = stats.get_summary()

    report_html = f"""<!DOCTYPE html>
<html><head><title>Kyro Download Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }}
h1 {{ color: #3B8ED0; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ border: 1px solid #444; padding: 8px; text-align: left; }}
th {{ background: #16213e; }}
.stat {{ display: inline-block; margin: 10px; padding: 15px; background: #16213e; border-radius: 8px; min-width: 150px; }}
.stat h3 {{ margin: 0; color: #3B8ED0; }}
.stat p {{ margin: 5px 0 0; font-size: 24px; }}
</style></head><body>
<h1>Kyro Downloader Report</h1>
<p>Generated: {html.escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}</p>
<p>Period: Last {days} days</p>
<div>
"""
    for key, value in stats_data.items():
        report_html += f'<div class="stat"><h3>{html.escape(key.replace("_", " ").title())}</h3><p>{html.escape(str(value))}</p></div>\n'

    report_html += (
        "</div><h2>Recent Downloads</h2><table><tr><th>Status</th><th>Title</th><th>Date</th><th>Size</th></tr>\n"
    )
    for entry in recent[:100]:
        status = entry.get("status", "completed")
        title = entry.get("title", "Unknown")
        ts = entry.get("downloaded_at", entry.get("timestamp", ""))[:19]
        size_raw = entry.get("size", 0)
        size_str = f"{size_raw / (1024 * 1024):.1f}MB" if isinstance(size_raw, (int, float)) and size_raw > 0 else "?"
        report_html += f"<tr><td>{html.escape(str(status))}</td><td>{html.escape(str(title))}</td><td>{html.escape(ts)}</td><td>{html.escape(size_str)}</td></tr>\n"
    report_html += "</table></body></html>"

    if not output_path:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(REPORTS_DIR / f"download_report_{datetime.now().strftime('%Y%m%d')}.html")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_html)
        logger.info(f"Report generated: {output_path}")
        return output_path
    except OSError as e:
        logger.error(f"Failed to write report {output_path}: {e}")
        return ""
