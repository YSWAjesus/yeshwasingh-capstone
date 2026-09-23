"""
What you actually ate, kept between visits.

The tray tracker could already total a plate, but the total died with the
page. This stores each logged meal so "what have I eaten today" and "how did
this week go" become answerable.

Storage is one JSON-lines file per person under LOG_DIR. Append-only: a
logged meal is a fact about the past, so nothing here rewrites history except
an explicit undo of the most recent entry.

LOG_DIR is configurable because a container's own filesystem is wiped on
every deploy. Pointed at a mounted volume it persists; left at the default it
does not, and the app says so rather than pretending otherwise.
"""

import json
import os
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import time_logic

LOG_DIR = Path(os.environ.get("BC_LOG_DIR")
               or Path(__file__).parent / "data" / "logs")

# Set when LOG_DIR points somewhere that survives a restart. The UI uses this
# to decide whether it can honestly promise the log will still be there.
LOG_IS_DURABLE = bool(os.environ.get("BC_LOG_DIR"))

MEALS = ["Breakfast", "Lunch", "Snacks", "Dinner"]

# Asking about your own log, as opposed to asking about the menu. Kept here
# rather than in query.py because query.py answers questions about the mess;
# this is a question about you, and the two have different answers for the
# same words ("what did I eat" is not "what is there to eat").
_LOG_INTENT = re.compile(
    r"\b(?:"
    r"my\s+(?:log|day|week|meals?|macros|intake|calories|protein)"
    r"|(?:what|how\s+much)\s+(?:have\s+)?i\s+(?:ate|eaten|had|logged)"
    r"|what\s+did\s+i\s+(?:eat|have)"
    r"|(?:show|see|open)\s+(?:me\s+)?(?:the\s+)?log"
    r"|calories?\s+(?:so\s+far|today)"
    r"|protein\s+so\s+far"
    r")\b"
)


def is_log_question(text: str) -> bool:
    """True when the user is asking about their own eating, not the menu."""
    return bool(_LOG_INTENT.search(str(text).lower()))


def new_user_id() -> str:
    """A short opaque id. Not an account — nothing here identifies a person."""
    return uuid.uuid4().hex[:12]


def _is_safe_id(user_id) -> bool:
    """Guard the path join: the id arrives from a URL the user can edit."""
    return (isinstance(user_id, str) and 6 <= len(user_id) <= 32
            and all(c in "0123456789abcdef" for c in user_id))


def _path_for(user_id: str):
    return LOG_DIR / f"{user_id}.jsonl" if _is_safe_id(user_id) else None


def log_meal(user_id: str, items, totals: dict, meal: str = None,
             unmatched=None, when: datetime = None) -> dict:
    """Append one eaten meal. Returns the stored entry."""
    path = _path_for(user_id)
    if path is None:
        raise ValueError("bad user id")

    # time_logic owns the clock. Stamping from datetime.now() here would file
    # an IST evening meal under the previous UTC day on a Railway container,
    # and a day tracker cannot have a day boundary that is 5h30m out.
    when = when or time_logic.now()
    entry = {
        "id": uuid.uuid4().hex[:12],
        "ts": when.isoformat(timespec="seconds"),
        "date": when.date().isoformat(),
        "meal": meal or "",
        "items": [str(i) for i in items],
        "calories": int(totals.get("calories", 0)),
        "protein": int(totals.get("protein", 0)),
        "carbs": int(totals.get("carbs", 0)),
        "fat": int(totals.get("fat", 0)),
        # Kept per entry so a day's total can say how complete it is, rather
        # than quietly under-reporting dishes with no macro record.
        "unmatched": [str(i) for i in (unmatched or [])],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry


def entries(user_id: str) -> list:
    """Every logged meal, oldest first. A corrupt line is skipped, not fatal."""
    path = _path_for(user_id)
    if path is None or not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("date"):
            out.append(row)
    return out


def undo_last(user_id: str):
    """Drop the most recent entry. Returns it, or None if there was nothing."""
    path = _path_for(user_id)
    if path is None or not path.exists():
        return None
    rows = entries(user_id)
    if not rows:
        return None
    removed = rows[-1]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows[:-1]))
    return removed


def _sum(rows) -> dict:
    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for row in rows:
        for key in total:
            total[key] += int(row.get(key, 0))
    total["meals"] = len(rows)
    total["incomplete"] = sum(1 for row in rows if row.get("unmatched"))
    return total


def day_summary(user_id: str, on: date = None) -> dict:
    on = on or time_logic.today()
    rows = [r for r in entries(user_id) if r["date"] == on.isoformat()]
    return {**_sum(rows), "date": on.isoformat(), "rows": rows}


def week_summary(user_id: str, anchor: date = None) -> dict:
    """Monday-to-Sunday totals, per day and combined.

    Monday-start matches the mess's own menu week, so "this week" in the app
    means the same seven days the menu photo covers.
    """
    anchor = anchor or time_logic.today()
    monday = anchor - timedelta(days=anchor.weekday())
    rows = entries(user_id)

    # Hoisted: date.today() was re-read on every iteration, so a run spanning
    # midnight could mark two different days "today".
    real_today = time_logic.today()
    days = []
    for offset in range(7):
        current = monday + timedelta(days=offset)
        day_rows = [r for r in rows if r["date"] == current.isoformat()]
        days.append({
            "date": current.isoformat(),
            "name": current.strftime("%A"),
            "short": current.strftime("%a"),
            "is_today": current == real_today,
            "is_future": current > real_today,
            **_sum(day_rows),
        })

    week_rows = [r for r in rows if monday.isoformat() <= r["date"]
                 <= (monday + timedelta(days=6)).isoformat()]
    logged = [d for d in days if d["meals"]]
    combined = _sum(week_rows)
    # Averaged over days actually logged, not over seven: two logged days
    # divided by seven reads as starvation rather than as a partial week.
    combined["days_logged"] = len(logged)
    combined["avg_calories"] = (
        round(combined["calories"] / len(logged)) if logged else 0)
    return {"start": monday.isoformat(), "days": days, "total": combined}
