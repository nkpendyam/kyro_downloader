#!/usr/bin/env python3
"""Generate all icon formats using Pillow (no cairo needed).

Usage:
    python scripts/generate_icons.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
ASSETS = ROOT / "src" / "gui" / "assets"


def create_icon_image(size):
    """Create a simple download icon using Pillow."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background
    radius = size // 5
    margin = size // 16
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(26, 115, 232, 255),
    )

    # Download arrow
    stroke = max(2, size // 16)
    center_x = size // 2
    arrow_top = size // 4
    arrow_bottom = size * 3 // 4
    arrow_width = size // 5

    # Vertical line
    draw.line(
        [(center_x, arrow_top), (center_x, arrow_bottom)],
        fill=(255, 255, 255, 255),
        width=stroke,
    )

    # Arrow head (left diagonal)
    draw.line(
        [(center_x - arrow_width, arrow_bottom - arrow_width), (center_x, arrow_bottom)],
        fill=(255, 255, 255, 255),
        width=stroke,
    )

    # Arrow head (right diagonal)
    draw.line(
        [(center_x + arrow_width, arrow_bottom - arrow_width), (center_x, arrow_bottom)],
        fill=(255, 255, 255, 255),
        width=stroke,
    )

    # Horizontal line at bottom
    line_y = arrow_bottom + arrow_width
    draw.line(
        [(center_x - arrow_width, line_y), (center_x + arrow_width, line_y)],
        fill=(255, 255, 255, 255),
        width=stroke,
    )

    return img


def main():
    from PIL import Image

    print("Generating icons with Pillow...")

    sizes = [16, 32, 48, 64, 128, 256, 512]
    images = []

    for size in sizes:
        img = create_icon_image(size)
        png_path = ASSETS / f"icon_{size}.png"
        img.save(png_path, "PNG")
        print(f"  Created icon_{size}.png")
        images.append(img)

    # Create ICO
    ico_path = ASSETS / "icon.ico"
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(img.width, img.height) for img in images],
    )
    print(f"  Created icon.ico ({len(images)} sizes)")

    # Create ICNS (macOS)
    icns_path = ASSETS / "icon.icns"
    images[-1].save(icns_path, format="ICNS")
    print(f"  Created icon.icns")

    # Copy 256 as icon.png for general use
    images[-2].save(ASSETS / "icon.png", "PNG")
    print(f"  Created icon.png (256x256)")

    print("\nIcon generation complete!")


if __name__ == "__main__":
    main()
