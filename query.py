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


# The order a day is actually eaten in, for whole-day answers.
MEAL_ORDER = ["Breakfast", "Lunch", "Snacks", "Dinner"]


def _meal_label(meal_type: str, servings) -> str:
    """What to call this meal in the reply.

    Sunday's breakfast and lunch rows are one combined brunch column, so
    calling it "breakfast" reads as wrong to anyone looking at the photo.
    """
    if any(s.hall is None for s in servings):
        return "brunch"
    return meal_type.lower()


def _whole_day_answer(menu: dict, weekday: str) -> dict:
    """Every meal of a named day.

    Asking "what is there on Thursday" used to answer with Thursday's lunch
    alone, because with no meal named the app fell back to whichever meal the
    clock was pointing at. Naming a weekday is a planning question, so it
    gets the whole day.
    """
    day_menu = halls.resolve_day(menu, weekday)

    blocks = []
    for meal_type in MEAL_ORDER:
        servings = halls.servings_for_meal(day_menu, meal_type)
        if not servings:
            continue
        # Sunday's brunch satisfies both Breakfast and Lunch, which would
        # otherwise print the same combined list twice under two headings.
        if blocks and servings[0].hall is None and blocks[-1][1][0].hall is None:
            continue
        blocks.append((meal_type, servings))

    if not blocks:
        return {"reply": f"I don't have {weekday} in this week's menu photo.",
                "meal_type": None, "follow_up": None, "follow_up_label": None,
                "follow_up_prompt": None, "servings": []}

    opener = f"Here's all of {weekday}:"
    parts = [opener]
    html = [f'<div class="lead">{_escape(opener)}</div>']

    for meal_type, servings in blocks:
        label = _meal_label(meal_type, servings).title()
        parts.append(f"### {label}")
        parts.append("\n\n".join(_render_serving(s) for s in servings))
        html.append(f'<div class="meal">{_escape(label)}</div>')
        html += [_render_serving_html(s) for s in servings]

    every_serving = [s for _m, servings in blocks for s in servings]
    missing = sum(1 for s in every_serving
                  for _c, d in s.rows if not macros.lookup(d))
    if missing:
        noun = "dish isn't" if missing == 1 else "dishes aren't"
        parts.append(f"_{missing} {noun} in the macro table yet — "
                     f"no numbers invented for them._")
        html.append(f'<div class="none">{missing} {noun} in the macro table '
                    f'yet — nothing invented for them.</div>')

    return {
        "reply": "\n\n".join(parts),
        "reply_html": "".join(html),
        # No meal-specific pill: every meal is already on screen, so offering
        # one would just re-show a section the user is looking at.
        "follow_up_options": [{"label": "Track what I ate", "action": "tray"}],
        "meal_type": None,
        "follow_up": None,
        "follow_up_label": None,
        "follow_up_prompt": None,
        "servings": every_serving,
    }


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
    now = now or time_logic.now()

    asked_meal = time_logic.meal_type_from_text(user_text)
    asked_day, day_kind = time_logic.day_reference_from_text(user_text, now)

    # A named weekday with no meal ("what's on Thursday") is a planning
    # question about the whole day. "Tomorrow" is not: it keeps the sense of
    # the current time of day, so at lunchtime it still means tomorrow's lunch.
    if asked_meal is None and day_kind == "weekday":
        target = now + timedelta(days=asked_day)
        return _whole_day_answer(menu, target.strftime("%A"))

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
    label = _meal_label(meal_type, servings)
    if status == "just_ended":
        opener = f"{meal_type} is just finishing — here's what was on:"
    elif status == "upcoming":
        window = time_logic.window_for(meal_type)
        starts = window[0].strftime("%H:%M") if window else ""
        opener = f"{meal_type} starts at {starts} — here's what's coming:"
    elif when == weekday:
        # Naming the weekday twice ("Thursday's (Thursday) dinner") is what
        # the parenthetical did whenever the day was further out than tomorrow.
        opener = f"Here's {weekday}'s {label}:"
    elif offset:
        opener = f"Here's {when}'s ({weekday}) {label}:"
    else:
        opener = f"Here's {weekday}'s {label}:"

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
        # Rendered as pills inside the prompt bar. Each is a real action the
        # app can carry out, so none of them is a dead end. The first is the
        # next meal that actually has data; the second opens the tray tracker,
        # which is where totalling macros is meaningful (you tick your own
        # plate) rather than summing a whole buffet.
        # Terse on purpose. "What's for snacks?" is a sentence, and two
        # sentence-length chips plus the send arrow do not fit a 375px bar --
        # they either cover the arrow or get ellipsised. As a follow-up chip
        # sitting under an answer about lunch, "Snacks?" says the same thing.
        # The PROMPT it sends is unchanged; only the label shortened.
        "follow_up_options": (
            [{"label": f"{m}?", "prompt": f"what's for {m.lower()}"}
             for m in follow_ups[:1]]
            + [{"label": "Track what I ate", "action": "tray"}]
        ),
        "meal_type": meal_type,
        "follow_up": follow_up,
        "follow_up_label": f"What's for {follow_up.lower()}?" if follow_up else None,
        "follow_up_prompt": f"what's for {follow_up.lower()}" if follow_up else None,
        "servings": servings,
    }
