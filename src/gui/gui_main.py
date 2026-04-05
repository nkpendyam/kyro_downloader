"""Kyro Downloader Desktop GUI entry point."""
import os
import sys
import tkinter as tk
from tkinter import messagebox


def main() -> None:
    """Launch the CustomTkinter desktop application."""
    if "--version" in sys.argv or "-v" in sys.argv:
        from src import __version__
        print(f"Kyro Downloader v{__version__}")
        return

    try:
        import customtkinter as ctk
        from src.gui.app import KyroApp
        from src.config.manager import load_config
        from src.utils.ytdlp_updater import auto_update_on_startup

        config = load_config()
        if getattr(config.general, "auto_update", False) and not os.environ.get("PYTEST_CURRENT_TEST"):
            auto_update_on_startup(check_only=False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        app = KyroApp()
        app.mainloop()
    except Exception as e:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Kyro Downloader Error",
                f"The application encountered an error:\n\n{str(e)}\n\n"
                f"Please check the logs and restart the application.",
            )
            root.destroy()
        except Exception:
            print(f"Fatal error: {e}", file=sys.stderr)
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()
