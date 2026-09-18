"""
Crop the exported avatar sprites to a shared frame.

The Figma exports are 1620x2160 with the character occupying a small region in
the middle, so rendering them as-is makes her tiny and surrounds her with a
large transparent box that swallows clicks. Every sprite is cropped to the SAME
rectangle so her position stays fixed when the app swaps states — crop each one
to its own bounding box and she would jump around between poses.

Re-run after re-exporting art:
    source .venv/bin/activate && python3 tools/prepare_sprites.py
"""

from pathlib import Path

from PIL import Image

SOURCE = Path(__file__).resolve().parent.parent / "assets"
DEST = SOURCE / "derived"

# Shared crop box (left, upper, right, lower) in the 1620x2160 export space.
# Chosen to contain every pose plus the lightbulb glow of the "answering"
# sprite, with a little headroom.
CROP = (500, 330, 1400, 1700)

TARGET_WIDTH = 420  # what the app actually renders at


def main():
    DEST.mkdir(exist_ok=True)
    for path in sorted(SOURCE.glob("avatar_*.png")):
        image = Image.open(path).convert("RGBA")
        cropped = image.crop(CROP)
        ratio = TARGET_WIDTH / cropped.width
        resized = cropped.resize(
            (TARGET_WIDTH, int(cropped.height * ratio)), Image.LANCZOS
        )
        out = DEST / path.name
        resized.save(out, optimize=True)
        print(f"{path.name:34s} -> {out.relative_to(SOURCE.parent)}  {resized.size}")


if __name__ == "__main__":
    main()
