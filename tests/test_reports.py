"""Tests for reports service."""

from unittest.mock import patch
from src.services.reports import generate_html_report


class TestReports:
    def test_generate_html_report_returns_path(self, tmp_path):
        output = tmp_path / "report.html"
        with (
            patch("src.services.reports.DownloadArchive") as mock_archive,
            patch("src.services.reports.StatsTracker") as mock_stats,
        ):
            mock_archive.return_value.list_all.return_value = []
            mock_stats.return_value.get_summary.return_value = {"total_downloads": 0}
            result = generate_html_report(str(output))
        assert result == str(output)
        assert output.exists()

    def test_report_contains_stats(self, tmp_path):
        output = tmp_path / "report.html"
        with (
            patch("src.services.reports.DownloadArchive") as mock_archive,
            patch("src.services.reports.StatsTracker") as mock_stats,
        ):
            mock_archive.return_value.list_all.return_value = []
            mock_stats.return_value.get_summary.return_value = {"total_downloads": 42}
            generate_html_report(str(output))
        content = output.read_text(encoding="utf-8")
        assert "42" in content

    def test_empty_report(self, tmp_path):
        output = tmp_path / "report.html"
        with (
            patch("src.services.reports.DownloadArchive") as mock_archive,
            patch("src.services.reports.StatsTracker") as mock_stats,
        ):
            mock_archive.return_value.list_all.return_value = []
            mock_stats.return_value.get_summary.return_value = {}
            result = generate_html_report(str(output))
        assert result == str(output)
        assert output.exists()
