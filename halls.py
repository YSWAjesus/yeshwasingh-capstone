"""
Dining geography: which physical hall/counter serves which menu rows.

The halls are NOT in the menu photo — the photo is one flat weekly grid. This
is a fact about campus layered on top of it:

  Rasoi -> the "Rice Bowl Concept only in Rasoi Dining" block (lunch only)
  Aahar -> the plain Breakfast / Lunch / Evening Snacks / Dinner blocks
  Jain  -> a counter INSIDE Aahar. Not a section of its own — just the category
           rows whose label carries "jain" ("Dry Veg- jain", "Gravy Veg (Jain)").

Everything matches through norm() because the real photo spells it
"Dry Veg- jain" (lowercase j, space after the hyphen) and Gemini's OCR varies
its punctuation run to run.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


def norm(text) -> str:
    """Lowercase, punctuation collapsed to single spaces, stripped.

    'Dry Veg- jain', 'Dry Veg (Jain)' and 'DRY VEG-JAIN' all become
    'dry veg jain'.
    """
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def is_jain_row(category) -> bool:
    """Token-prefix match, so a dish like 'Jaipuri' can never register as Jain."""
    return any(token.startswith("jain") for token in norm(category).split())


def base_category(category) -> str:
    """'Gravy Veg- jain' -> 'gravy veg', for pairing against the main line."""
    return " ".join(t for t in norm(category).split() if not t.startswith("jain"))


# Cells the mess prints to mean "nothing here". These are not dishes, and they
# must never reach the chat reply or the tray checklist.
_NOT_A_DISH = {"", "-", "--", "n a", "n l", "na", "nl", "nil", "none", "tbd"}


def is_real_dish(value) -> bool:
    return norm(value) not in _NOT_A_DISH  # norm("N/A") == "n a"


@dataclass(frozen=True)
class Hall:
    key: str
    display: str
    note: str
    sections: dict  # meal_type -> [canonical section name, ...]
    rows: str  # "exclude_jain" | "only_jain"
    headline: Tuple[str, ...] = ()  # normalised categories to quote first


# ---------------------------------------------------------------------------
# EDIT ME if the dining setup changes. Adding Rasoi at dinner, for example, is
# a one-line change: add "Dinner": ["Dinner"] to its sections.
# ---------------------------------------------------------------------------
HALLS = (
    Hall(
        "rasoi", "Rasoi", "rice-bowl counter",
        {"Lunch": ["Lunch - Rice Bowl (Rasoi Dining)"]},
        "exclude_jain",
        headline=("bowl", "starter"),
    ),
    Hall(
        "aahar", "Aahar", "main line",
        {"Breakfast": ["Breakfast"], "Lunch": ["Lunch"],
         "Snacks": ["Evening Snacks"], "Dinner": ["Dinner"]},
        "exclude_jain",
        headline=("gravy veg", "dry veg", "main", "indian breakfast"),
    ),
    Hall(
        "jain", "the Jain counter", "inside Aahar",
        {"Lunch": ["Lunch"], "Dinner": ["Dinner"]},
        "only_jain",
        headline=("gravy veg jain", "dry veg jain"),
    ),
)

SECTION_FINGERPRINTS = {
    "Lunch - Rice Bowl (Rasoi Dining)": ("rasoi", "rice bowl"),
    "Evening Snacks": ("snack",),
    "Brunch": ("brunch",),
    "Breakfast": (),
    "Lunch": (),
    "Dinner": (),
}

# Most specific first, so a plain "Lunch" key can never swallow the Rasoi block.
RESOLVE_ORDER = ["Lunch - Rice Bowl (Rasoi Dining)", "Evening Snacks",
                 "Brunch", "Breakfast", "Lunch", "Dinner"]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
        "Sunday"]


def resolve_day(menu: dict, weekday: str) -> dict:
    """Day lookup that survives OCR returning 'monday' instead of 'Monday'."""
    target = norm(weekday)
    for key, value in menu.items():
        if norm(key) == target:
            return value if isinstance(value, dict) else {}
    return {}


def resolve_sections(day_menu: dict) -> dict:
    """Canonical section name -> the key actually present in day_menu.

    A slightly-off OCR key (e.g. 'Lunch - Rice Bowl (Rasoi)') would otherwise
    silently delete a whole dining hall from the answer with no warning.
    """
    pool = {k: norm(k) for k in day_menu if k != "date"}
    found = {}
    for canonical in RESOLVE_ORDER:
        target = norm(canonical)
        hit = next((k for k, n in pool.items() if n == target), None)
        if hit is None:
            for fingerprint in SECTION_FINGERPRINTS[canonical]:
                hit = next((k for k, n in pool.items() if fingerprint in n), None)
                if hit:
                    break
        if hit:
            found[canonical] = hit
            pool.pop(hit)
    return found


@dataclass
class Serving:
    hall: Optional[str]  # None => cannot be attributed to a hall
    note: str
    rows: List[Tuple[str, str]]  # [(category label, dish)]; "" for flat lists
    same_as_main: bool = False


def _row_wanted(hall: Hall, category) -> bool:
    if hall.rows == "only_jain":
        return is_jain_row(category)
    return not is_jain_row(category)


def _mark_jain_duplicates(servings: List[Serving]) -> None:
    aahar = next((s for s in servings if s.hall == "Aahar"), None)
    jain = next((s for s in servings if s.hall and "Jain" in s.hall), None)
    if not (aahar and jain and jain.rows):
        return
    main = {base_category(c): norm(d) for c, d in aahar.rows}
    jain.same_as_main = all(
        main.get(base_category(c)) == norm(d) for c, d in jain.rows
    )


def servings_for_meal(day_menu: dict, meal_type: str) -> List[Serving]:
    """Which halls are serving what, for this day and meal.

    A hall with no data is simply absent — never rendered as an empty or
    invented block.
    """
    resolved = resolve_sections(day_menu)

    # Sunday brunch is a flat list spanning rows that on weekdays belong to two
    # different halls, so it genuinely cannot be attributed to one. Say so
    # rather than guessing.
    if meal_type in ("Breakfast", "Lunch") and "Brunch" in resolved:
        content = day_menu[resolved["Brunch"]]
        if isinstance(content, list):
            return [Serving(None, "listed as one combined brunch menu",
                            [("", d) for d in content if is_real_dish(d)])]

    out = []
    for hall in HALLS:
        rows = []
        for canonical in hall.sections.get(meal_type, []):
            key = resolved.get(canonical)
            if key is None:
                continue
            content = day_menu[key]
            if isinstance(content, dict):
                rows += [(c, d) for c, d in content.items()
                         if _row_wanted(hall, c) and is_real_dish(d)]
            elif isinstance(content, list):
                rows += [("", d) for d in content if is_real_dish(d)]
        if rows:
            out.append(Serving(hall.display, hall.note, rows))
    _mark_jain_duplicates(out)
    return out


def headline_dish(serving: Serving) -> str:
    """The one dish worth naming in a one-line summary of this hall."""
    hall = next((h for h in HALLS if h.display == serving.hall), None)
    if hall:
        for wanted in hall.headline:
            for category, dish in serving.rows:
                if base_category(category) == wanted or norm(category) == wanted:
                    return dish
    return serving.rows[0][1] if serving.rows else ""


def all_dishes(servings: List[Serving]) -> List[str]:
    """Every dish across these servings, de-duplicated, order preserved."""
    seen = set()
    out = []
    for serving in servings:
        for _, dish in serving.rows:
            if norm(dish) not in seen:
                seen.add(norm(dish))
                out.append(dish)
    return out
