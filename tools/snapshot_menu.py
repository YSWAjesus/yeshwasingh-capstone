"""
The real input: download this week's menu photo from Drive, OCR it, and save
the structured result to data/menu_snapshot.json.

Records WHICH image it actually read. menu_data falls back to a cached or
bundled photo when Drive is unreachable, and claiming a live run that quietly
used September's sample would be dishonest.

    source .venv/bin/activate && python3 tools/snapshot_menu.py
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import menu_data  # noqa: E402

SNAPSHOT = ROOT / "data" / "menu_snapshot.json"
# The sha256 of the image this parse came from. menu_data serves the snapshot
# when Gemini is unavailable, but only if the photo still hashes to this --
# without it, a fallback would be a stale-menu bug rather than a safety net.
DIGEST = ROOT / "data" / "menu_snapshot.sha256"


def main():
    menu, source = menu_data.load_menu()
    SNAPSHOT.parent.mkdir(exist_ok=True)
    SNAPSHOT.write_text(json.dumps(menu, indent=2, sort_keys=True) + "\n")

    image_path, _ = menu_data.fetch_menu_image()
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()[:16]
    DIGEST.write_text(digest + "\n")

    days = [d for d in menu_data.DAYS if d in menu]
    print(json.dumps({
        "snapshot": str(SNAPSHOT.relative_to(ROOT)),
        "image_source": source,  # drive | cache | sample
        "image_sha256": digest,
        "days_read": len(days),
    }, indent=2))

    if source != "drive":
        print(f"\nWARNING: read the {source} image, not a fresh Drive download.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
