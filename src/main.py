"""Main entry point for Kyro Downloader by nkpendyam."""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Kyro Downloader by nkpendyam")
    parser.add_argument("--ui", choices=["cli","tui","web"], default="cli")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--config", type=str)
    parser.add_argument("--no-banner", action="store_true")
    args, remaining = parser.parse_known_args()
    if args.ui == "web":
        from src.ui.web.server import run_web
        print(f"Starting Web UI at http://{args.host}:{args.port}")
        run_web(host=args.host, port=args.port)
    elif args.ui == "tui":
        from src.ui.tui import run_tui
        run_tui()
    else:
        cli_args = [sys.argv[0]]
        if args.config:
            cli_args.extend(["--config", args.config])
        if args.no_banner:
            cli_args.append("--no-banner")
        cli_args.extend(remaining)
        sys.argv = cli_args
        from src.cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()
