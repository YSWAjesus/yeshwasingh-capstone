"""
Acceptance test: does a real user actually see complete macros now?

Asks the app the same questions a student would, for every day and meal, and
reports any reply still admitting a missing estimate. This is the user-visible
criterion — the table being "full" in the abstract is not the point.

    python3 tools/check_app_replies.py
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import halls  # noqa: E402
import macros  # noqa: E402
import query  # noqa: E402

SNAPSHOT = ROOT / "data" / "menu_snapshot.json"
MEALS = ["Breakfast", "Lunch", "Snacks", "Dinner"]

# A Monday, so weekday arithmetic below lines up with the menu's day names.
BASE_MONDAY = datetime(2026, 9, 14, 13, 0)


def main():
    if not SNAPSHOT.exists():
        raise SystemExit("No menu snapshot. Run tools/snapshot_menu.py first.")
    menu = json.loads(SNAPSHOT.read_text())

    incomplete = []
    checked = 0
    for offset, day in enumerate(halls.DAYS):
        when = BASE_MONDAY + timedelta(days=offset)
        for meal in MEALS:
            result = query.answer(f"what's for {meal.lower()}", menu, now=when)
            if not result["servings"]:
                continue
            checked += 1
            gaps = [dish for serving in result["servings"]
                    for _c, dish in serving.rows if macros.lookup(dish) is None]
            if gaps:
                incomplete.append({"day": day, "meal": meal, "missing": gaps})

    print(json.dumps({
        "replies_checked": checked,
        "replies_with_gaps": len(incomplete),
        "detail": incomplete,
    }, indent=2))

    if incomplete:
        print(f"\n{len(incomplete)} of {checked} replies still say "
              f"'no macro estimate yet'.", file=sys.stderr)
        sys.exit(1)
    print("\nEvery reply has complete macros.")


if __name__ == "__main__":
    main()
