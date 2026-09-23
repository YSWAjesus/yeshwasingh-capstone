"""
Time-of-day -> meal inference.

A generic question ("what's there to eat?") should answer the meal you can
actually still go and eat, not the one that just closed.
"""

import re
from datetime import datetime, time

# ---------------------------------------------------------------------------
# REAL SERVING WINDOWS — EDIT ME.
# This table is the only place the app learns when meals happen; everything
# else derives from it. Times confirmed with the mess on 2026-09-17.
#     (name, opens, closes)   24h local time; "closes" = the counter shuts
# ---------------------------------------------------------------------------
SERVING_WINDOWS = [
    ("Breakfast", time(7, 30), time(10, 0)),
    ("Lunch", time(11, 30), time(15, 0)),
    ("Snacks", time(17, 0), time(18, 0)),
    ("Dinner", time(19, 30), time(22, 0)),
]

# How long after a window closes a generic "what's there to eat?" still answers
# the meal that just ended, before rolling forward to the next one.
GRACE_MINUTES = 10


def _mins(t) -> int:
    """Minutes since midnight — avoids timedelta and midnight-wrap arithmetic."""
    return t.hour * 60 + t.minute


def meal_context(now: datetime = None) -> dict:
    """
    {"meal_type", "status": serving|just_ended|upcoming, "day_offset": 0|1}

    day_offset=1 means the meal is tomorrow's — without it, a query at 23:00
    would answer with this morning's breakfast, eaten 16 hours ago.
    """
    now = now or datetime.now()
    current = _mins(now.time())

    for name, start, end in SERVING_WINDOWS:
        if _mins(start) <= current <= _mins(end):
            return {"meal_type": name, "status": "serving", "day_offset": 0}
        if _mins(end) < current <= _mins(end) + GRACE_MINUTES:
            return {"meal_type": name, "status": "just_ended", "day_offset": 0}

    for name, start, _end in SERVING_WINDOWS:
        if current < _mins(start):
            return {"meal_type": name, "status": "upcoming", "day_offset": 0}

    return {"meal_type": SERVING_WINDOWS[0][0], "status": "upcoming",
            "day_offset": 1}


def infer_meal_type(now: datetime = None) -> str:
    return meal_context(now)["meal_type"]


def window_for(meal_type: str):
    for name, start, end in SERVING_WINDOWS:
        if name == meal_type:
            return start, end
    return None


# Keywords a user might type, mapped to the meal they mean.
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


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]


# Short forms people actually type. Full names are matched first and return
# before these are consulted, so "sat" inside "saturday" never reaches here.
DAY_ABBREVIATIONS = {
    "mon": 0, "tue": 1, "tues": 1, "wed": 2, "weds": 2,
    "thu": 3, "thur": 3, "thurs": 3, "fri": 4, "sat": 5, "sun": 6,
}


def day_reference_from_text(text: str, now: datetime = None):
    """(offset, kind) where kind is "relative", "weekday" or None.

    The kind matters, not just the number. "Tomorrow" carries the sense of
    the current time of day — at lunchtime it means tomorrow's lunch. A named
    weekday is a calendar reference: you are planning, so naming "Thursday"
    with no meal means the whole of Thursday, not whichever meal happens to
    be being served as you type.

    `now` must be the same clock the caller uses to turn the offset back into
    a date. This used to read datetime.now() directly while query.answer
    worked from an injected `now`, so the two disagreed whenever they were not
    the same day and every named weekday came out shifted.
    """
    lowered = text.lower()

    offset = _relative_offset(lowered)
    if offset is not None:
        return offset, "relative"

    today_index = (now or datetime.now()).weekday()

    for index, name in enumerate(WEEKDAYS):
        if name.lower() in lowered:
            return (index - today_index) % 7, "weekday"

    for abbreviation, index in DAY_ABBREVIATIONS.items():
        if re.search(rf"\b{abbreviation}\b", lowered):
            return (index - today_index) % 7, "weekday"

    return None, None


def day_offset_from_text(text: str, now: datetime = None):
    """Days from today the user is asking about, or None if they didn't say."""
    return day_reference_from_text(text, now)[0]


def _relative_offset(lowered: str):
    """today / tonight / tomorrow / day after tomorrow, or None."""

    # Spelling-tolerant: people type tomorow / tommorow / tommorrow / tmrw.
    # Listing exact variants missed "tommorow" in real use, so match the shape.
    # Grouped, so prefixing it below binds to the whole alternation rather
    # than just its first branch.
    #
    # "toms lunch" used to fall through to None and get answered as today --
    # the worst kind of wrong, since a confident answer about the wrong day
    # looks exactly like a right one.
    #
    # Note what is deliberately NOT here: bare "tom". Rasoi's Asian counter
    # can serve Tom Yum soup, and reading that as a day would be a far worse
    # bug than the one being fixed. "toms" and "tom's" carry no such clash.
    tomorrow = re.compile(
        r"\b(?:"
        r"t(?:o|')?m+o*r+o*w"      # tomorrow, tomorow, tommorow, tmorrow
        r"|tmrw?|tmw"              # tmr, tmrw, tmw
        r"|2m(?:orrow|oro|rw)"     # 2mrw, 2moro
        r"|toms|tom's"             # toms lunch, tom's lunch
        r")\b"
    )

    if re.search(r"day\s+after\s+" + tomorrow.pattern, lowered):
        return 2
    if tomorrow.search(lowered):
        return 1
    if "today" in lowered or "tonight" in lowered:
        return 0
    return None


def meal_type_from_text(now_text: str):
    """Return the meal named in the text, or None.

    Matches on position in the sentence rather than dict order, and prefers
    longer keywords. Without this, "what's for dinner this evening?" resolves
    to Snacks, because "evening" happens to be checked first.
    """
    lowered = now_text.lower()
    best_position = None
    best_meal = None
    for keyword in sorted(MEAL_KEYWORDS, key=len, reverse=True):
        position = lowered.find(keyword)
        if position == -1:
            continue
        if best_position is None or position < best_position:
            best_position = position
            best_meal = MEAL_KEYWORDS[keyword]
    return best_meal
