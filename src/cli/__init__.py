"""CLI package exports."""

def main() -> None:
    """Invoke CLI entrypoint lazily to avoid import-time side effects."""
    from src.cli.__main__ import main as _main

    _main()

__all__ = ["main"]
