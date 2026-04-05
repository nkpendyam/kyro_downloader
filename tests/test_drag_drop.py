"""Tests for GUI drag-and-drop URL parsing."""

from pathlib import Path

from src.gui.components.drag_drop import DragDropHandler


def test_handle_text_drop_extracts_http_urls() -> None:
    handler = DragDropHandler()
    text = "https://example.com/a\nnot-a-url\nhttp://example.org/b"

    urls = handler.handle_text_drop(text)

    assert urls == ["https://example.com/a", "http://example.org/b"]


def test_handle_drop_reads_url_file_and_url_equals_lines(tmp_path: Path) -> None:
    handler = DragDropHandler()
    drop_file = tmp_path / "links.txt"
    drop_file.write_text("https://example.com/one\nURL=https://example.com/two\n", encoding="utf-8")

    urls = handler.handle_drop(str(drop_file))

    assert urls == ["https://example.com/one", "https://example.com/two"]
