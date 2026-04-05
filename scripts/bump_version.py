#!/usr/bin/env python3
"""Version bump script for Kyro Downloader.

Usage:
    python scripts/bump_version.py patch    # 1.0.0 -> 1.0.1
    python scripts/bump_version.py minor    # 1.0.0 -> 1.1.0
    python scripts/bump_version.py major    # 1.0.0 -> 2.0.0
    python scripts/bump_version.py 1.2.3    # Set specific version
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def get_current_version():
    init_file = ROOT / "src" / "__init__.py"
    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else "0.0.0"


def bump_version(part):
    current = get_current_version()
    major, minor, patch = map(int, current.split("."))

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        # Specific version
        try:
            major, minor, patch = map(int, part.split("."))
        except ValueError:
            print(f"Invalid version: {part}")
            sys.exit(1)

    new_version = f"{major}.{minor}.{patch}"
    return new_version


def update_files(new_version):
    # Update src/__init__.py
    init_file = ROOT / "src" / "__init__.py"
    content = init_file.read_text()
    content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"', content)
    init_file.write_text(content)

    # Update pyproject.toml
    pyproject = ROOT / "pyproject.toml"
    content = pyproject.read_text()
    content = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_version}"', content, count=1)
    pyproject.write_text(content)

    # Update app_updater.py
    updater = ROOT / "src" / "utils" / "app_updater.py"
    if updater.exists():
        content = updater.read_text()
        content = re.sub(r'CURRENT_VERSION\s*=\s*"[^"]+"', f'CURRENT_VERSION = "{new_version}"', content)
        updater.write_text(content)

    print(f"Version bumped to {new_version}")
    print(f"  - src/__init__.py")
    print(f"  - pyproject.toml")
    print(f"  - src/utils/app_updater.py")


def main():
    if len(sys.argv) < 2:
        print(f"Current version: {get_current_version()}")
        print("Usage: bump_version.py [major|minor|patch|X.Y.Z]")
        sys.exit(1)

    part = sys.argv[1]
    new_version = bump_version(part)
    update_files(new_version)
    print(f"\nNext steps:")
    print(f"  1. Update CHANGELOG.md")
    print(f"  2. git add -A && git commit -m 'Bump version to {new_version}'")
    print(f"  3. git tag v{new_version}")
    print(f"  4. git push origin main --tags")
    print(f"  5. GitHub Actions will build and release automatically!")


if __name__ == "__main__":
    main()
