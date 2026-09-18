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
# Every perch pose uses this SAME box so she doesn't jump position when the
# app swaps states; it's sized to contain the widest pose plus the lightbulb
# glow of the "answering" sprite.
CROP = (500, 330, 1400, 1700)

TARGET_WIDTH = 420  # what the app actually renders at

# The hero pose is cropped tight to her body instead. The shared box leaves
# ~180px of transparent margin beside her, and the landing page anchors the
# speech bubbles to the image's edges — with the loose box they end up a
# quarter of the screen away from her head. Only the idle pose needs this,
# because the hero never swaps states.
HERO_SOURCE = "avatar_idle.png"
HERO_PAD = 18


def _save(image, crop, width, out):
    cropped = image.crop(crop)
    ratio = width / cropped.width
    resized = cropped.resize((width, int(cropped.height * ratio)), Image.LANCZOS)
    resized.save(out, optimize=True)
    return resized.size


def main():
    DEST.mkdir(exist_ok=True)
    for path in sorted(SOURCE.glob("avatar_*.png")):
        image = Image.open(path).convert("RGBA")
        size = _save(image, CROP, TARGET_WIDTH, DEST / path.name)
        print(f"{path.name:34s} -> derived/{path.name}  {size}")

    hero = Image.open(SOURCE / HERO_SOURCE).convert("RGBA")
    bbox = hero.getbbox()
    tight = (bbox[0] - HERO_PAD, bbox[1] - HERO_PAD,
             bbox[2] + HERO_PAD, bbox[3] + HERO_PAD)
    size = _save(hero, tight, 320, DEST / "hero_idle.png")
    print(f"{'hero (tight crop)':34s} -> derived/hero_idle.png  {size}")

    # Perch poses, each cropped tight to its OWN pixels. The shared box left
    # up to 180px of invisible margin, which is why she kept landing away
    # from the prompt bar instead of on it: the app was positioning the
    # bounding box, not the character. Cropped tight, the image's bottom edge
    # IS her feet, so planting her on the bar is exact.
    for path in sorted(SOURCE.glob("avatar_*.png")):
        image = Image.open(path).convert("RGBA")
        box = image.getbbox()
        size = _save(image, box, 200, DEST / f"perch_{path.name}")
        print(f"{'perch ' + path.stem:34s} -> derived/perch_{path.name}  {size}")


if __name__ == "__main__":
    main()
