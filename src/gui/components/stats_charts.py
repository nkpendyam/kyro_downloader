"""Statistics charts component for Desktop GUI using simple text-based visualization."""


class StatsCharts:
    def __init__(self):
        self._data = []

    def add_data_point(self, date_str, downloads=0, bytes_downloaded=0, failed=0):
        """Record a daily data point for trend visualization."""
        self._data.append(
            {
                "date": date_str,
                "downloads": downloads,
                "bytes": bytes_downloaded,
                "failed": failed,
            }
        )

    def get_data_points(self):
        """Return all recorded data points."""
        return list(self._data)

    def get_daily_summary(self, stats_dict):
        lines = []
        lines.append("=== Daily Download Summary ===")
        total = stats_dict.get("total_downloads", 0)
        failed = stats_dict.get("failed_downloads", 0)
        success_rate = stats_dict.get("success_rate", 0)
        total_bytes = stats_dict.get("total_bytes", 0)
        avg_speed = stats_dict.get("avg_speed_mbps", 0)
        lines.append(f"Total Downloads: {total}")
        lines.append(f"Failed: {failed}")
        lines.append(f"Success Rate: {success_rate:.1f}%")
        lines.append(f"Total Data: {total_bytes / (1024 * 1024 * 1024):.2f} GB")
        lines.append(f"Avg Speed: {avg_speed:.2f} Mbps")
        return "\n".join(lines)

    def get_platform_breakdown(self, stats_dict):
        lines = []
        lines.append("=== Platform Breakdown ===")
        platforms = stats_dict.get("platforms", {})
        if not platforms:
            lines.append("No platform data available")
            return "\n".join(lines)
        for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
            bar = "#" * min(count, 50)
            lines.append(f"{platform:15s} | {bar} ({count})")
        return "\n".join(lines)

    def get_weekly_trend(self, stats_dict):
        lines = []
        lines.append("=== Weekly Trend ===")
        daily = stats_dict.get("daily_downloads", {})
        if not daily:
            lines.append("No daily data available")
            return "\n".join(lines)
        max_val = max(daily.values()) if daily else 1
        for date_str in sorted(daily.keys())[-7:]:
            count = daily[date_str]
            bar_len = int((count / max_val) * 30) if max_val > 0 else 0
            bar = "█" * bar_len
            lines.append(f"{date_str} | {bar} {count}")
        return "\n".join(lines)

    def get_format_distribution(self, stats_dict):
        lines = []
        lines.append("=== Format Distribution ===")
        formats = stats_dict.get("formats", {})
        if not formats:
            lines.append("No format data available")
            return "\n".join(lines)
        total = sum(formats.values())
        for fmt, count in sorted(formats.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            bar = "▓" * int(pct / 2)
            lines.append(f"{fmt:10s} | {bar} {pct:.0f}% ({count})")
        return "\n".join(lines)

    def get_speed_history(self, stats_dict):
        lines = []
        lines.append("=== Speed History ===")
        speeds = stats_dict.get("speed_history", [])
        if not speeds:
            lines.append("No speed data available")
            return "\n".join(lines)
        for entry in speeds[-10:]:
            ts = entry.get("timestamp", "")
            speed = entry.get("speed_mbps", 0)
            bar_len = int(speed * 2)
            bar = "▂▃▄▅▆▇█"[min(bar_len, 6)] * min(bar_len, 20)
            lines.append(f"{ts} | {bar} {speed:.1f} Mbps")
        return "\n".join(lines)

    def generate_full_report(self, stats_dict):
        sections = [
            self.get_daily_summary(stats_dict),
            "",
            self.get_platform_breakdown(stats_dict),
            "",
            self.get_weekly_trend(stats_dict),
            "",
            self.get_format_distribution(stats_dict),
            "",
            self.get_speed_history(stats_dict),
        ]
        return "\n".join(sections)
