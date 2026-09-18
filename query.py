"""
Turns a chat message into a menu answer: work out which meal is meant, which
halls are serving, and render it with per-dish macros and a follow-up the user
can actually click.
"""

from datetime import datetime, timedelta

import halls
import macros
import time_logic

# What to offer next after answering each meal.
_NEXT_MEAL = {
    "Breakfast": ["Lunch", "Snacks", "Dinner"],
    "Lunch": ["Snacks", "Dinner", "Breakfast"],
    "Snacks": ["Dinner", "Breakfast", "Lunch"],
    "Dinner": ["Breakfast", "Lunch", "Snacks"],
}


def _headline(servings) -> str:
    """One sentence naming what each hall has — only halls with real data."""
    clauses = []
    for serving in servings:
        if serving.hall is None:
            return ""  # Sunday brunch: no hall split to report
        dish = halls.headline_dish(serving)
        if not dish:
            continue
        if serving.same_as_main:
            clauses.append("the Jain counter has the same thing")
        elif "Jain" in serving.hall:
            clauses.append(f"the Jain option is {dish}")
        else:
            clauses.append(f"in {serving.hall} there's {dish}")
    if not clauses:
        return ""
    if len(clauses) == 1:
        return f"Today {clauses[0]}."
    return f"Today {', '.join(clauses[:-1])}, and {clauses[-1]}."


def _render_serving(serving) -> str:
    if serving.hall is None:
        lines = [f"**Sunday brunch** — {serving.note}"]
    else:
        note = serving.note
        if serving.same_as_main:
            note += ", same as the main line today"
        title = serving.hall[0].upper() + serving.hall[1:]  # "the Jain counter"
        lines = [f"**{title}** — {note}"]

    for category, dish in serving.rows:
        label = f"{category}: {dish}" if category else dish
        macro = macros.lookup(dish)
        if macro:
            lines.append(f"- {label} — {macros.format_macros(macro)}")
        else:
            lines.append(f"- {label} — _no macro estimate yet_")
    return "\n".join(lines)


def _suggest_follow_up(menu, weekday, meal_type):
    """Only offer a meal that actually has data — never a dead end."""
    for candidate in _NEXT_MEAL.get(meal_type, []):
        day_menu = halls.resolve_day(menu, weekday)
        if halls.servings_for_meal(day_menu, candidate):
            return candidate
    return None


def answer(user_text: str, menu: dict, now: datetime = None) -> dict:
    """
    Returns:
      reply             markdown answer
      meal_type         the meal that was answered
      follow_up         meal type to offer next, or None
      follow_up_label   button text, or None
      follow_up_prompt  what clicking the button should ask, or None
      servings          the Serving objects behind this answer
    """
    now = now or datetime.now()

    asked = time_logic.meal_type_from_text(user_text)
    if asked:
        meal_type = asked
        weekday = now.strftime("%A")
        status = None
    else:
        context = time_logic.meal_context(now)
        meal_type = context["meal_type"]
        status = context["status"]
        weekday = (now + timedelta(days=context["day_offset"])).strftime("%A")

    day_menu = halls.resolve_day(menu, weekday)
    servings = halls.servings_for_meal(day_menu, meal_type)

    if not servings:
        reply = (f"I don't have {meal_type.lower()} listed for {weekday} in "
                 f"this week's menu photo.")
        return {"reply": reply, "meal_type": meal_type, "follow_up": None,
                "follow_up_label": None, "follow_up_prompt": None,
                "servings": []}

    if status == "just_ended":
        opener = f"{meal_type} is just finishing — here's what was on:"
    elif status == "upcoming":
        window = time_logic.window_for(meal_type)
        starts = window[0].strftime("%H:%M") if window else ""
        opener = f"{meal_type} starts at {starts} — here's what's coming:"
    else:
        opener = f"Here's {weekday}'s {meal_type.lower()}:"

    parts = [opener]
    headline = _headline(servings)
    if headline:
        parts.append(headline)
    parts.append("\n\n".join(_render_serving(s) for s in servings))

    missing = sum(1 for s in servings for _c, d in s.rows if not macros.lookup(d))
    if missing:
        parts.append(f"_{missing} dish{'es' if missing > 1 else ''} "
                     f"aren't in the macro table yet — no numbers invented for them._")
    parts.append("_Taking some of this? The tray tracker totals up just what's "
                 "on your plate._")

    follow_up = _suggest_follow_up(menu, weekday, meal_type)
    return {
        "reply": "\n\n".join(parts),
        "meal_type": meal_type,
        "follow_up": follow_up,
        "follow_up_label": f"What's for {follow_up.lower()}?" if follow_up else None,
        "follow_up_prompt": f"what's for {follow_up.lower()}" if follow_up else None,
        "servings": servings,
    }
