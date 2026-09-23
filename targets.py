"""
Daily macro targets — the denominator a day is measured against.

Deliberately separate from meal_log: a logged meal is a fact about the past
and that file is append-only, while a target is mutable settings. Same volume,
same opaque user id, same path guard.

THERE IS NO DEFAULT TARGET, and that is a design decision rather than an
omission. Shipping a 2000 kcal default would mean the app inventing a number
about a student's body — their age, weight, activity, goals — which is the
same class of fabrication the project refuses for food. An unset macro has no
bar and no percentage; the app simply has no opinion until asked.
"""

import json

import meal_log

# The four a student would actually set. Order is the order they render in.
TARGET_KEYS = ("calories", "protein", "carbs", "fat")

UNITS = {"calories": "kcal", "protein": "g", "carbs": "g", "fat": "g"}

# Above these, a "target" is a typo rather than an intention. Generous on
# purpose: an athlete eating 5000 kcal is real, 50000 is a stray zero.
CEILINGS = {"calories": 8000, "protein": 400, "carbs": 1200, "fat": 400}


def _path_for(user_id: str):
    base = meal_log._path_for(user_id)
    return None if base is None else base.with_suffix(".targets.json")


def load(user_id: str) -> dict:
    """The targets this person has set. Absent keys mean "no target"."""
    path = _path_for(user_id)
    if path is None or not path.exists():
        return {}
    try:
        stored = json.loads(path.read_text())
    except ValueError:
        return {}
    if not isinstance(stored, dict):
        return {}
    return {k: int(stored[k]) for k in TARGET_KEYS
            if isinstance(stored.get(k), (int, float))
            and not isinstance(stored.get(k), bool)
            and 0 < stored[k] <= CEILINGS[k]}


def save(user_id: str, values: dict) -> dict:
    """Store the targets that were actually set. Zero or blank clears one."""
    path = _path_for(user_id)
    if path is None:
        raise ValueError("bad user id")

    kept = {}
    for key in TARGET_KEYS:
        value = values.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = int(value)
            if 0 < value <= CEILINGS[key]:
                kept[key] = value

    path.parent.mkdir(parents=True, exist_ok=True)
    if kept:
        path.write_text(json.dumps(kept, indent=2, sort_keys=True) + "\n")
    elif path.exists():
        path.unlink()
    return kept


def progress(user_id: str, day: dict) -> list:
    """One row per target the person has actually set.

    `complete` is False when any food that day has no macro record. A bar over
    an incomplete day is a FLOOR, not a measurement, and the renderer is
    expected to drop the percentage when it sees this — a percentage asserts
    a completeness the data does not have.
    """
    stored = load(user_id)
    if not stored:
        return []

    complete = not day.get("unknown_items")
    rows = []
    for key in TARGET_KEYS:
        if key not in stored:
            continue
        target = stored[key]
        consumed = int(day.get(key, 0))
        rows.append({
            "key": key,
            "label": key.title() if key != "calories" else "Calories",
            "unit": UNITS[key],
            "target": target,
            "consumed": consumed,
            # Clamped for geometry only; the numbers themselves are never capped.
            "fill_pct": max(0, min(100, round(consumed / target * 100))),
            "pct": round(consumed / target * 100),
            "complete": complete,
        })
    return rows
