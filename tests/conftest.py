"""Pytest fixtures for Kyro Downloader tests."""
import pytest
import tempfile


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
