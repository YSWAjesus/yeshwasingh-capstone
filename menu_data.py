"""
Fetches and parses the weekly mess menu.

The menu lives as an Excel grid: row 1/2 are "Day"/"Date" headers across
7 day columns, then the rest of the sheet is a sequence of banner rows
(a section name in column A, rest of the row blank) each followed by
category rows (category label in column A, one item per day column).
Sunday's brunch breaks that pattern — see SUNDAY_BRUNCH_BANNER below — so
it's parsed as a flat list of items instead of a per-day grid.

This is written to be format-driven, not hardcoded to specific categories,
so a real .xlsx from Google Drive with the same shape parses correctly
without code changes — only DRIVE_FILE_ID needs to be swapped in menu_data.py
once the mess uploads the real file.
"""

import os
from pathlib import Path

import openpyxl
import requests

SAMPLE_MENU_PATH = Path(__file__).parent / "sample_menu.xlsx"
CACHED_MENU_PATH = Path(__file__).parent / ".cache" / "menu.xlsx"

# Set this once the real Excel file is uploaded to Drive and shared as
# "Anyone with the link" -> Viewer. Leave as None to use the local sample.
DRIVE_FILE_ID = os.environ.get("DRIVE_FILE_ID") or None

SUNDAY_BRUNCH_BANNER = "Sunday Brunch"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def fetch_menu_excel(file_id: str = None) -> Path:
    """
    Download the menu Excel from Google Drive (file must be shared as
    "Anyone with the link"). Falls back to the bundled sample if no
    file_id is configured, so the app always has something to run against.
    """
    file_id = file_id or DRIVE_FILE_ID
    if not file_id:
        return SAMPLE_MENU_PATH

    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    CACHED_MENU_PATH.parent.mkdir(exist_ok=True)
    CACHED_MENU_PATH.write_bytes(response.content)
    return CACHED_MENU_PATH


def parse_menu(path: Path = None) -> dict:
    """
    Parse the menu grid into:
      {
        "Monday": {"date": "14-Sep", "Breakfast": {category: item, ...}, ...},
        ...
        "Sunday": {"date": "20-Sep", "Brunch": ["item", "item", ...]},
      }
    """
    path = path or SAMPLE_MENU_PATH
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    day_row = rows[0]
    date_row = rows[1]

    days = [str(d) for d in day_row[1:8]]
    dates = [str(d) for d in date_row[1:8]]

    menu = {day: {"date": date} for day, date in zip(days, dates)}

    current_section = None
    sunday_items = []

    for row in rows[2:]:
        label = row[0]
        day_values = row[1:8]

        is_banner = label not in (None, "") and all(
            v in (None, "") for v in day_values
        )
        if is_banner:
            current_section = str(label)
            continue

        if current_section == SUNDAY_BRUNCH_BANNER:
            # Flat list: item text lives in the "Monday" column slot.
            item = day_values[0]
            if item:
                sunday_items.append(str(item))
            continue

        if current_section is None:
            continue

        category = str(label) if label else None
        if category is None:
            continue

        for day, value in zip(days, day_values):
            if value:
                menu[day].setdefault(current_section, {})[category] = str(value)

    if "Sunday" in menu:
        menu["Sunday"]["Brunch"] = sunday_items

    return menu


def load_menu() -> dict:
    """Convenience wrapper: fetch (or use sample) then parse."""
    path = fetch_menu_excel()
    return parse_menu(path)


def sections_for_meal_type(day: str, meal_type: str):
    """
    Map a (day, meal_type) pair to the section key(s) that apply.

    Sunday collapses Breakfast+Lunch into "Brunch". Weekday Lunch pulls in
    both lunch lines (the Rice Bowl concept and the regular Lunch line) —
    both are genuinely on offer the same day.
    """
    if day == "Sunday":
        if meal_type in ("Breakfast", "Lunch"):
            return ["Brunch"]
        return []  # Evening Snacks / Dinner data not available for Sunday yet

    if meal_type == "Lunch":
        return ["Lunch - Rice Bowl (Rasoi Dining)", "Lunch"]
    if meal_type == "Snacks":
        return ["Evening Snacks"]
    return [meal_type]


def all_items_for_day(menu: dict, day: str):
    """Flat list of every dish name on a given day, across all sections."""
    items = []
    day_menu = menu.get(day, {})
    for section, content in day_menu.items():
        if section == "date":
            continue
        if isinstance(content, dict):
            items.extend(content.values())
        elif isinstance(content, list):
            items.extend(content)
    return items
