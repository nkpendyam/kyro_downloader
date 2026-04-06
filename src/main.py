"""Main entry point for Kyro Downloader by nkpendyam."""

import argparse
import sys


def main() -> None:
    if "--ui" in sys.argv:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--ui", choices=["cli", "tui", "web"], default="cli")
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--config", type=str)
        parser.add_argument("--no-banner", action="store_true")
        args, remaining = parser.parse_known_args()
        if args.ui == "web":
            from src.ui.web.server import run_web

            run_web(host=args.host, port=args.port)
            return
        if args.ui == "tui":
            from src.ui.tui import run_tui

            run_tui()
            return
        sys.argv = [sys.argv[0]]
        if args.config:
            sys.argv.extend(["--config", args.config])
        if args.no_banner:
            sys.argv.append("--no-banner")
        sys.argv.extend(remaining)

    from src import cli

    cli.main()


if __name__ == "__main__":
    main()
