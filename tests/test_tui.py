"""Tests for TUI."""


class TestTUI:
    def test_run_tui_imports(self):
        from src.ui.tui import run_tui, KyroApp
        assert callable(run_tui)
        assert KyroApp is not None

    def test_tui_bindings(self):
        from src.ui.tui import KyroApp
        bindings = KyroApp.BINDINGS
        binding_keys = [b.key for b in bindings]
        assert "q" in binding_keys
        assert "d" in binding_keys
        assert "p" in binding_keys
        assert "r" in binding_keys
        assert "c" in binding_keys

    def test_tui_has_required_methods(self):
        from src.ui.tui import KyroApp
        assert hasattr(KyroApp, "action_download")
        assert hasattr(KyroApp, "action_pause_queue")
        assert hasattr(KyroApp, "action_resume_queue")
        assert hasattr(KyroApp, "action_clear_queue")
        assert hasattr(KyroApp, "_fetch_info")
        assert hasattr(KyroApp, "_queue_current")
