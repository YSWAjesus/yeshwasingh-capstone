"""
Turns a user's chat message into a menu answer: figure out which meal they
mean (explicit keyword, else time-of-day), look up that day's items, format
a reply, and suggest a follow-up (a different meal they might want next).
"""

from datetime import datetime

import menu_data
import time_logic
from macros import estimate_macros

FOLLOW_UP_ORDER = ["Breakfast", "Lunch", "Snacks", "Dinner"]


def _next_meal_type(meal_type: str) -> str:
    idx = FOLLOW_UP_ORDER.index(meal_type)
    return FOLLOW_UP_ORDER[(idx + 1) % len(FOLLOW_UP_ORDER)]


def _format_section(section_name: str, content) -> str:
    lines = [f"**{section_name}**"]
    if isinstance(content, dict):
        for category, item in content.items():
            lines.append(f"- {category}: {item}")
    elif isinstance(content, list):
        for item in content:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _items_from_sections(day_menu: dict, section_names) -> list:
    items = []
    for section in section_names:
        content = day_menu.get(section)
        if isinstance(content, dict):
            items.extend(content.values())
        elif isinstance(content, list):
            items.extend(content)
    return items


def answer(user_text: str, menu: dict, now: datetime = None) -> dict:
    """
    Returns:
      {
        "reply": str,              # chat-style markdown reply
        "meal_type": str,          # the meal that was answered
        "follow_up": str,          # suggested next meal to ask about
      }
    """
    now = now or datetime.now()
    weekday = now.strftime("%A")

    meal_type = time_logic.meal_type_from_text(user_text) or time_logic.infer_meal_type(now)
    section_names = menu_data.sections_for_meal_type(weekday, meal_type)
    day_menu = menu.get(weekday, {})

    if not section_names or not any(s in day_menu for s in section_names):
        reply = (
            f"I don't have {meal_type.lower()} data for {weekday} yet — "
            "the menu file might not cover it (e.g. no evening snacks/dinner "
            "listed for Sunday in the current sheet)."
        )
        return {"reply": reply, "meal_type": meal_type, "follow_up": _next_meal_type(meal_type)}

    parts = []
    for section in section_names:
        if section in day_menu:
            parts.append(_format_section(section, day_menu[section]))
    body = "\n\n".join(parts)

    items = _items_from_sections(day_menu, section_names)
    totals, unmatched = estimate_macros(items)
    macro_line = (
        f"\n\n_Roughly {totals['calories']} kcal · {totals['protein']}g protein · "
        f"{totals['carbs']}g carbs · {totals['fat']}g fat "
        f"(estimated across everything above)_"
    )
    if unmatched:
        macro_line += f"\n_Not estimated yet: {', '.join(unmatched)}_"

    reply = f"Here's {weekday}'s {meal_type.lower()}:\n\n{body}{macro_line}"

    follow_up = _next_meal_type(meal_type)
    reply += f"\n\nWant to know what's for {follow_up.lower()} too?"

    return {"reply": reply, "meal_type": meal_type, "follow_up": follow_up}
