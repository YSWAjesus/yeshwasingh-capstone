"""
The oracle: which dishes on the real menu have no macro data?

This script is deliberately the ONLY thing allowed to say the gap is closed.
The macro-gap-filler agent may not declare success on its own — a model
grading its own homework turns "observe" into self-assessment, and the loop
collapses into a single batch. Here the loop ends only when this prints an
empty `missing` list.

It imports the app's real modules, so it measures what a user would actually
see, not a private copy of the data.

    python3 tools/menu_macro_audit.py --json
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import halls  # noqa: E402
import macros  # noqa: E402

SNAPSHOT = Path(__file__).resolve().parent.parent / "data" / "menu_snapshot.json"
MEALS = ["Breakfast", "Lunch", "Snacks", "Dinner"]


def audit(snapshot_path: Path = SNAPSHOT) -> dict:
    if not snapshot_path.exists():
        raise SystemExit(
            f"No menu snapshot at {snapshot_path}. Run tools/snapshot_menu.py first."
        )
    menu = json.loads(snapshot_path.read_text())

    # Count how often each dish appears across the week, so the agent can
    # prioritise the ones a student will actually hit.
    frequency = Counter()
    for day in halls.DAYS:
        day_menu = halls.resolve_day(menu, day)
        if not day_menu:
            continue
        for meal in MEALS:
            for serving in halls.servings_for_meal(day_menu, meal):
                for _category, dish in serving.rows:
                    frequency[dish] += 1

    missing = sorted(
        (dish for dish in frequency if macros.lookup(dish) is None),
        key=lambda d: (-frequency[d], d.lower()),
    )
    return {
        "missing": missing,
        "missing_count": len(missing),
        "covered": len(frequency) - len(missing),
        "total_dishes": len(frequency),
        "frequency": {dish: frequency[dish] for dish in missing},
        "table_size": len(macros.all_dishes()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="machine-readable")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    args = parser.parse_args()

    result = audit(args.snapshot)
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"{result['covered']}/{result['total_dishes']} dishes on this week's "
          f"menu have macros ({result['missing_count']} missing).")
    for dish in result["missing"]:
        print(f"  {result['frequency'][dish]}x  {dish}")


if __name__ == "__main__":
    main()
