"""
The clock: one timezone, and the meal a student is actually standing in front of.

Railway runs containers in UTC. The serving windows are IST. Before this was
fixed the deployed app told a student at 13:00 in the lunch queue that
breakfast was being served, and at 20:30 at dinner that it was lunch — every
day, silently, for the app's single most important question.

These cases are the ones that were wrong. If this file ever fails, the clock
has come unthreaded again.

    python3 tools/test_clock.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import time_logic  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))

# (IST wall clock, the meal a student at that time is actually dealing with)
CASES = [
    ((8, 0), "Breakfast", "serving"),
    ((13, 0), "Lunch", "serving"),
    ((17, 30), "Snacks", "serving"),
    ((20, 30), "Dinner", "serving"),
    ((21, 45), "Dinner", "serving"),
    ((10, 5), "Breakfast", "just_ended"),
    ((16, 0), "Snacks", "upcoming"),
]


def test_meal_inference():
    for (hour, minute), meal, status in CASES:
        ist = datetime(2026, 9, 23, hour, minute)
        got = time_logic.meal_context(ist)
        assert got["meal_type"] == meal and got["status"] == status, (
            f"{hour:02d}:{minute:02d} IST -> {got['meal_type']}/{got['status']}, "
            f"expected {meal}/{status}"
        )
    print(f"PASS  meal inference: {len(CASES)} IST times map to the right meal")


def test_utc_container_would_have_been_wrong():
    """The bug itself, pinned — so nobody 'simplifies' the clock away later."""
    wrong = 0
    for (hour, minute), meal, _status in CASES:
        as_utc = (datetime(2026, 9, 23, hour, minute, tzinfo=IST)
                  .astimezone(timezone.utc).replace(tzinfo=None))
        if time_logic.meal_context(as_utc)["meal_type"] != meal:
            wrong += 1
    assert wrong >= 4, (
        "Reading the clock as UTC used to give the wrong meal for most of the "
        f"day; only {wrong} of these cases now differ, so this test is no "
        "longer pinning what it was written to pin."
    )
    print(f"PASS  the old UTC reading gets {wrong}/{len(CASES)} of these wrong")


def test_one_clock():
    """time_logic.now() and .today() must agree with each other."""
    now = time_logic.now()
    assert now.date() == time_logic.today(), "now() and today() disagree"
    assert now.tzinfo is None, "now() must be naive; downstream compares naive"
    print(f"PASS  one clock: {time_logic.BC_TZ} via {time_logic.TZ_SOURCE} "
          f"-> {now:%Y-%m-%d %H:%M}")


def test_no_silent_utc_fallback():
    """A missing timezone database must never degrade to UTC in silence."""
    assert time_logic.TZ_SOURCE in ("zoneinfo", "fixed-offset")
    assert time_logic._FIXED_OFFSETS["Asia/Kolkata"] == timedelta(hours=5, minutes=30)
    print("PASS  no silent UTC fallback: "
          f"{sorted(time_logic._FIXED_OFFSETS)} have exact fixed offsets")


def test_callers_do_not_read_the_clock_themselves():
    """Every module must take its time from time_logic, not datetime.now()."""
    offenders = []
    for name in ("app.py", "meal_log.py", "query.py", "targets.py"):
        path = ROOT / name
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#")[0]
            if "datetime.now()" in code or "date.today()" in code:
                offenders.append(f"{name}:{number}: {line.strip()}")
    assert not offenders, (
        "these read the clock directly instead of going through time_logic:\n  "
        + "\n  ".join(offenders)
    )
    print("PASS  no module reads the clock behind time_logic's back")


def main():
    test_one_clock()
    test_meal_inference()
    test_utc_container_would_have_been_wrong()
    test_no_silent_utc_fallback()
    test_callers_do_not_read_the_clock_themselves()
    print("\nAll clock checks passed: the app answers the meal you are "
          "actually standing in front of.")


if __name__ == "__main__":
    main()
