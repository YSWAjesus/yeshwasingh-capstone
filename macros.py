"""
Approximate macro reference table for common mess/canteen dishes.

Values are per typical single serving, in {calories (kcal), protein (g),
carbs (g), fat (g)}. These are rough estimates for demo purposes, not
verified nutrition-lab numbers — good enough to show "roughly what am I
eating", not for medical/dietary compliance use.

Looked up by dish name (case-insensitive, trimmed), with an optional per-dish
`aliases` list for the name variants the OCR produces. Any dish not in the
table is reported as "not estimated yet" rather than guessing a number, so the
UI never silently fabricates an estimate.

The data lives in data/macros.json, not in this file, so the macro-gap-filler
agent can extend it without ever editing Python (a dropped comma in a dict
literal would take the whole app down).
"""

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "macros.json"


@lru_cache(maxsize=4)
def _load(mtime_ns: int) -> dict:
    """mtime_ns is the cache key: it changes whenever the file is rewritten,
    so a running Streamlit process picks up the agent's writes. Without it,
    `import macros` would hit sys.modules and serve a stale table forever."""
    with open(_DATA_PATH) as handle:
        return json.load(handle)


def _table() -> dict:
    return _load(_DATA_PATH.stat().st_mtime_ns)


def all_dishes() -> dict:
    """The whole table, keyed by normalised dish name."""
    return _table()


_ALIAS_CACHE_KEY = None
_ALIAS_INDEX = {}


def _aliases() -> dict:
    """alias -> canonical dish key, rebuilt only when the file changes."""
    global _ALIAS_CACHE_KEY, _ALIAS_INDEX
    key = _DATA_PATH.stat().st_mtime_ns
    if key != _ALIAS_CACHE_KEY:
        index = {}
        for dish, record in _table().items():
            for alias in record.get("aliases", []):
                index[_normalize(alias)] = dish
        _ALIAS_INDEX, _ALIAS_CACHE_KEY = index, key
    return _ALIAS_INDEX



def _normalize(name) -> str:
    return str(name).strip().lower()


def lookup(dish_name):
    """Return macros for a single dish, or None if it isn't in the table.

    Matching stays deliberately conservative — exact name after normalising,
    then an explicit alias. No fuzzy matching: claiming an estimate we don't
    actually have would be worse than admitting the gap.
    """
    key = _normalize(dish_name)
    table = _table()
    record = table.get(key) or table.get(_aliases().get(key, ""))
    if record is None:
        return None
    return {k: record[k] for k in ("calories", "protein", "carbs", "fat")}


def per_item_macros(items):
    """[{'item': str, 'macros': {...} or None}] — order preserved.

    macros=None means "not in the table". It never means a guessed number.
    """
    return [{"item": str(item), "macros": lookup(item)} for item in items]


def format_macros(macro) -> str:
    """One rendering shared by chat and the tray tracker, so they can't disagree."""
    if not macro:
        return "no macro estimate yet"
    return (f"{macro['calories']} kcal · {macro['protein']}g P · "
            f"{macro['carbs']}g C · {macro['fat']}g F")


def estimate_macros(items):
    """
    Sum macros across a list of dish names.

    Only meaningful when the caller knows the person is eating all of them —
    i.e. the tray tracker, where the user ticks their own plate. A whole
    buffet menu must NOT be summed; use per_item_macros for that.

    Returns (totals, unmatched); unmatched lists dishes with no entry so the
    UI can say "not estimated yet" instead of inventing a number.
    """
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    unmatched = []
    for entry in per_item_macros(items):
        if entry["macros"] is None:
            unmatched.append(entry["item"])
            continue
        for key in totals:
            totals[key] += entry["macros"][key]
    return totals, unmatched
