"""
Every everyday food offered as a tap must still resolve to a real record.

pantry.EVERYDAY_FOODS creates no nutrition data — it points at records that
already exist. If a later table edit renames a key, a name here silently
becomes a chip that logs "no macro estimate yet", which looks like the app
failing rather than like a rename.

Deliberately SEPARATE from tools/menu_macro_audit.py: that script is the
oracle for the menu gap and must stay scoped to the menu snapshot, so pantry
vocabulary can never contaminate what it reports.

    python3 tools/check_quick_add.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import macros  # noqa: E402
import pantry  # noqa: E402


def main():
    missing = [f for f in pantry.EVERYDAY_FOODS if macros.lookup(f) is None]
    print(f"{len(pantry.EVERYDAY_FOODS) - len(missing)}/"
          f"{len(pantry.EVERYDAY_FOODS)} everyday foods resolve.")
    if missing:
        print("\nThese would render as 'no macro estimate yet':", file=sys.stderr)
        for food in missing:
            print(f"  - {food}", file=sys.stderr)
        sys.exit(1)
    print("Every quick-add name points at a real, sourced record.")


if __name__ == "__main__":
    main()
