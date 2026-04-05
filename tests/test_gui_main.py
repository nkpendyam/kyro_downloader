"""Tests for GUI entrypoint wiring."""


def test_gui_main_exported() -> None:
    """GUI module should expose callable main for console-script entrypoint."""
    from src.gui import gui_main

    assert hasattr(gui_main, "main")
    assert callable(gui_main.main)
