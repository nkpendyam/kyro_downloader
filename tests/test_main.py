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
