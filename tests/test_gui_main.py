"""Tests for GUI entrypoint wiring."""

from unittest.mock import patch


def test_gui_main_exported() -> None:
    """GUI module should expose callable main for console-script entrypoint."""
    from src.gui import gui_main

    assert hasattr(gui_main, "main")
    assert callable(gui_main.main)


def test_gui_main_version_flag_prints_version(monkeypatch, capsys) -> None:
    """GUI entrypoint should support --version fast path."""
    from src.gui import gui_main

    monkeypatch.setattr("sys.argv", ["kyro-gui", "--version"])
    gui_main.main()
    captured = capsys.readouterr()
    assert "Kyro Downloader v" in captured.out


def test_gui_main_handles_exception_with_exit(monkeypatch) -> None:
    """GUI entrypoint should exit 1 when initialization fails."""
    from src.gui import gui_main

    monkeypatch.setattr("sys.argv", ["kyro-gui"])
    fake_root = type("_Root", (), {"withdraw": lambda self: None, "destroy": lambda self: None})()
    monkeypatch.setattr(gui_main.tk, "Tk", lambda: fake_root)
    monkeypatch.setattr(gui_main.messagebox, "showerror", lambda *args, **kwargs: None)
    with patch("src.config.manager.load_config", side_effect=RuntimeError("boom")):
        try:
            gui_main.main()
        except SystemExit as exc:
            assert exc.code == 1
        else:
            raise AssertionError("Expected SystemExit(1)")
