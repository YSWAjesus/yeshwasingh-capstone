"""
Time-of-day -> meal section inference.

Time blocks (from plan.md):
  Breakfast   07:00-10:30
  Lunch       12:00-14:30
  Snacks      16:00-18:00
  Dinner      19:30-22:00

Outside these windows, we fall back to whichever meal is coming up next so
the agent never just says "nothing right now" during a quiet hour.
"""

from datetime import datetime, time

BLOCKS = [
    ("Breakfast", time(7, 0), time(10, 30)),
    ("Lunch", time(12, 0), time(14, 30)),
    ("Snacks", time(16, 0), time(18, 0)),
    ("Dinner", time(19, 30), time(22, 0)),
]

# Order used to find "the next upcoming meal" when we're between windows.
_ORDER = ["Breakfast", "Lunch", "Snacks", "Dinner"]


def infer_meal_type(now: datetime = None) -> str:
    """
    Return one of "Breakfast", "Lunch", "Snacks", "Dinner" based on the
    current time. Sunday callers should map this through to "Brunch" for
    Breakfast/Lunch — see menu_data.sections_for_meal_type.
    """
    now = now or datetime.now()
    current = now.time()

    for name, start, end in BLOCKS:
        if start <= current <= end:
            return name

    # Between windows: pick the next one that starts later today, else
    # wrap around to the first block of the next day.
    for name, start, _ in BLOCKS:
        if current < start:
            return name
    return BLOCKS[0][0]


# Keywords a user might type, mapped to the meal type they mean.
MEAL_KEYWORDS = {
    "breakfast": "Breakfast",
    "brunch": "Breakfast",
    "lunch": "Lunch",
    "snack": "Snacks",
    "snacks": "Snacks",
    "evening": "Snacks",
    "dinner": "Dinner",
    "supper": "Dinner",
}


def meal_type_from_text(text: str):
    """Return a meal type if the text names one explicitly, else None."""
    lowered = text.lower()
    for keyword, meal_type in MEAL_KEYWORDS.items():
        if keyword in lowered:
            return meal_type
    return None
