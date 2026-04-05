"""Tests for top-level src.main entrypoint."""

import sys
from unittest.mock import patch

from src.main import main


def test_cli_passthrough_places_global_flags_before_subcommand(monkeypatch) -> None:
    """--no-banner should be passed before subcommand args for argparse compatibility."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kyro",
            "--ui",
            "cli",
            "--no-banner",
            "info",
            "https://www.youtube.com/watch?v=BaW_jenozKc",
        ],
    )

    with patch("src.cli.main") as mock_cli_main:
        main()

    assert sys.argv[0] == "kyro"
    assert sys.argv[1] == "--no-banner"
    assert sys.argv[2] == "info"
    assert "https://www.youtube.com/watch?v=BaW_jenozKc" in sys.argv
    mock_cli_main.assert_called_once()


def test_main_web_mode_invokes_run_web(monkeypatch) -> None:
    """--ui web should call run_web with supplied host/port."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["kyro", "--ui", "web", "--host", "0.0.0.0", "--port", "9001"],
    )

    with patch("src.ui.web.server.run_web") as mock_run_web:
        main()

    mock_run_web.assert_called_once_with(host="0.0.0.0", port=9001)


def test_main_tui_mode_invokes_run_tui(monkeypatch) -> None:
    """--ui tui should call run_tui."""
    monkeypatch.setattr(sys, "argv", ["kyro", "--ui", "tui"])

    with patch("src.ui.tui.run_tui") as mock_run_tui:
        main()

    mock_run_tui.assert_called_once()
