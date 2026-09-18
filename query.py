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


def _headline(servings, when: str = "Today") -> str:
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
        return f"{when} {clauses[0]}."
    return f"{when} {', '.join(clauses[:-1])}, and {clauses[-1]}."


def _render_serving(serving) -> str:
    if serving.hall is None:
        lines = [f"**Sunday brunch** — {serving.note}"]
    else:
        note = serving.note
        if serving.same_as_main:
            note += ", same as the main line today"
        title = serving.hall[0].upper() + serving.hall[1:]  # "the Jain counter"
        lines = [f"**{title}** — {note}"]

    for _category, dish in serving.rows:
        macro = macros.lookup(dish)
        if macro:
            lines.append(f"- {dish} — {macros.format_macros(macro)}")
        else:
            lines.append(f"- {dish} — _no macro estimate yet_")
    return "\n".join(lines)


def _escape(text) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _render_serving_html(serving) -> str:
    if serving.hall is None:
        title = "Sunday brunch"
        note = serving.note
    else:
        title = serving.hall[0].upper() + serving.hall[1:]
        note = serving.note
        if serving.same_as_main:
            note += ", same as the main line today"

    rows = []
    for _category, dish in serving.rows:
        # Just the dish. The menu's row labels ("Gravy Veg", "Dry Veg- jain")
        # are how the mess organises its grid, not something a hungry student
        # needs read back to them.
        label = _escape(dish)
        macro = macros.lookup(dish)
        if macro:
            rows.append(
                f'<li>{label} <span class="kcal">{macro["calories"]} kcal</span>'
                f'<br><span class="macros">{macro["protein"]}g protein · '
                f'{macro["carbs"]}g carbs · {macro["fat"]}g fat</span></li>'
            )
        else:
            rows.append(f'<li>{label}<br>'
                        f'<span class="none">no macro estimate yet</span></li>')
    return (f'<h4>{_escape(title)} <span class="macros">— {_escape(note)}'
            f'</span></h4><ul>{"".join(rows)}</ul>')


def _suggest_follow_ups(menu, weekday, meal_type, limit=2):
    """Offer only meals that actually have data — never a dead end."""
    day_menu = halls.resolve_day(menu, weekday)
    found = []
    for candidate in _NEXT_MEAL.get(meal_type, []):
        if halls.servings_for_meal(day_menu, candidate):
            found.append(candidate)
        if len(found) == limit:
            break
    return found


def _suggest_follow_up(menu, weekday, meal_type):
    found = _suggest_follow_ups(menu, weekday, meal_type, limit=1)
    return found[0] if found else None


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

    asked_meal = time_logic.meal_type_from_text(user_text)
    asked_day = time_logic.day_offset_from_text(user_text)

    if asked_meal:
        meal_type = asked_meal
        # An explicit day wins; otherwise the meal they named is today's.
        offset = asked_day if asked_day is not None else 0
        status = None
    else:
        context = time_logic.meal_context(now)
        meal_type = context["meal_type"]
        # "what's there to eat tomorrow" keeps the time-of-day sense of the
        # question but moves the day, so at lunchtime it means tomorrow's lunch.
        if asked_day is not None:
            offset = asked_day
            status = None
        else:
            offset = context["day_offset"]
            status = context["status"]

    target = now + timedelta(days=offset)
    weekday = target.strftime("%A")

    day_menu = halls.resolve_day(menu, weekday)
    servings = halls.servings_for_meal(day_menu, meal_type)

    if not servings:
        reply = (f"I don't have {meal_type.lower()} listed for {weekday} in "
                 f"this week's menu photo.")
        return {"reply": reply, "meal_type": meal_type, "follow_up": None,
                "follow_up_label": None, "follow_up_prompt": None,
                "servings": []}

    when = {0: "today", 1: "tomorrow"}.get(offset, weekday)
    if status == "just_ended":
        opener = f"{meal_type} is just finishing — here's what was on:"
    elif status == "upcoming":
        window = time_logic.window_for(meal_type)
        starts = window[0].strftime("%H:%M") if window else ""
        opener = f"{meal_type} starts at {starts} — here's what's coming:"
    elif offset:
        opener = f"Here's {when}'s ({weekday}) {meal_type.lower()}:"
    else:
        opener = f"Here's {weekday}'s {meal_type.lower()}:"

    parts = [opener]
    headline = _headline(servings, "Tomorrow" if offset == 1
                         else ("Today" if offset == 0 else f"On {weekday}"))
    if headline:
        parts.append(headline)
    parts.append("\n\n".join(_render_serving(s) for s in servings))

    missing = sum(1 for s in servings for _c, d in s.rows if not macros.lookup(d))
    if missing == 1:
        parts.append("_1 dish isn't in the macro table yet — "
                     "no number invented for it._")
    elif missing:
        parts.append(f"_{missing} dishes aren't in the macro table yet — "
                     f"no numbers invented for them._")
    parts.append("_Taking some of this? The tray tracker totals up just what's "
                 "on your plate._")

    html = [f'<div class="lead">{_escape(opener)}</div>']
    if headline:
        html.append(f"<div>{_escape(headline)}</div>")
    html += [_render_serving_html(s) for s in servings]
    if missing:
        noun = "dish isn't" if missing == 1 else "dishes aren't"
        html.append(f'<div class="none">{missing} {noun} in the macro table '
                    f'yet — nothing invented for them.</div>')

    follow_ups = _suggest_follow_ups(menu, weekday, meal_type)
    follow_up = follow_ups[0] if follow_ups else None
    return {
        "reply": "\n\n".join(parts),
        "reply_html": "".join(html),
        # Rendered as pills inside the prompt bar. Each is a real query the
        # app can answer, so none of them is a dead end.
        "follow_up_options": [
            {"label": f"What's for {m.lower()}?", "prompt": f"what's for {m.lower()}"}
            for m in follow_ups
        ],
        "meal_type": meal_type,
        "follow_up": follow_up,
        "follow_up_label": f"What's for {follow_up.lower()}?" if follow_up else None,
        "follow_up_prompt": f"what's for {follow_up.lower()}" if follow_up else None,
        "servings": servings,
    }
