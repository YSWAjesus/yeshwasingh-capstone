"""
Prepare the Figma exports for the app.

Two kinds of asset:

  hero_composed.png  — the whole landing state as one graphic: the captain
                       with both speech bubbles already positioned. The app
                       renders this single file, so there is no bubble
                       placement to get wrong.
  avatar_*.png       — the perch poses. Each is cropped to its own pixels so
                       the image's bottom edge is her feet, which is what lets
                       the app plant her on the prompt bar exactly.

Re-run after re-exporting art:
    source .venv/bin/activate && python3 tools/prepare_sprites.py
"""

from pathlib import Path

from PIL import Image

SOURCE = Path(__file__).resolve().parent.parent / "assets"
DEST = SOURCE / "derived"

HERO_WIDTH = 900          # rendered smaller; this is for retina headroom
PERCH_BOX = (220, 300)    # max width, max height — aspect preserved


def _fit(image, box):
    width, height = image.size
    scale = min(box[0] / width, box[1] / height, 1.0)
    if scale >= 1.0:
        return image
    return image.resize((max(1, int(width * scale)), max(1, int(height * scale))),
                        Image.LANCZOS)


def main():
    DEST.mkdir(exist_ok=True)

    hero_src = SOURCE / "hero_composed.png"
    if hero_src.exists():
        hero = Image.open(hero_src).convert("RGBA")
        hero = hero.crop(hero.getbbox())
        ratio = HERO_WIDTH / hero.width
        hero = hero.resize((HERO_WIDTH, int(hero.height * ratio)), Image.LANCZOS)
        hero.save(DEST / "hero_composed.png", optimize=True)
        print(f"{'hero_composed':34s} -> derived/hero_composed.png  {hero.size}")

    for path in sorted(SOURCE.glob("avatar_*.png")):
        image = Image.open(path).convert("RGBA")
        # No-op for the already-tight exports; trims the older full-canvas ones.
        image = image.crop(image.getbbox())
        image = _fit(image, PERCH_BOX)
        out = DEST / f"perch_{path.name}"
        image.save(out, optimize=True)
        print(f"{'perch ' + path.stem:34s} -> {out.name}  {image.size}")


if __name__ == "__main__":
    main()
