"""
Fetches and parses the weekly mess menu from a photo (no spreadsheet exists
upstream — the mess menu only ever exists as the image posted to the batch
WhatsApp group). Gemini's vision + JSON-mode output does the OCR/structuring
in one call; this module just wraps that with a Drive fetch and a fallback.

Output shape (unchanged from the earlier Excel-based version, so query.py
and time_logic.py need no changes):
  {
    "Monday": {"date": "14-Sep", "Breakfast": {category: item, ...},
               "Lunch - Rice Bowl (Rasoi Dining)": {...}, "Lunch": {...},
               "Evening Snacks": {...}, "Dinner": {...}},
    ...
    "Sunday": {"date": "20-Sep", "Brunch": ["item", "item", ...]},
  }
"""

import os
from pathlib import Path

import requests

from gemini_client import GeminiError, generate_json

SAMPLE_MENU_PATH = Path(__file__).parent / "sample_menu.jpg"
CACHED_MENU_PATH = Path(__file__).parent / ".cache" / "menu.jpg"

# The real photo already sitting in the student's shared Drive folder.
# Update this each week after re-uploading a fresh menu photo to Drive.
DRIVE_FILE_ID = os.environ.get("DRIVE_FILE_ID") or "1-oPVFOPdBshCwpXypDPgZlIj84hoI4w0"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

MENU_PROMPT = """
You are reading a weekly mess/canteen menu from a photo. It's a grid: days
of the week as columns (Monday through Sunday, each with a date), and food
categories as rows, grouped under meal-section banners such as Breakfast,
a "Rice Bowl Concept" lunch line, the main Lunch line, Evening Snacks, and
Dinner. Sunday typically breaks the pattern with its own "Brunch Menu"
column that does not line up with the weekday categories — treat Sunday's
items as a flat list instead of category:item pairs.

Return ONLY JSON matching exactly this shape (no extra commentary):

{
  "Monday": {
    "date": "<date text as shown, e.g. 14-Sep>",
    "Breakfast": {"<category>": "<item>", ...},
    "Lunch - Rice Bowl (Rasoi Dining)": {"<category>": "<item>", ...},
    "Lunch": {"<category>": "<item>", ...},
    "Evening Snacks": {"<category>": "<item>", ...},
    "Dinner": {"<category>": "<item>", ...}
  },
  "Tuesday": { ... same shape ... },
  "Wednesday": { ... },
  "Thursday": { ... },
  "Friday": { ... },
  "Saturday": { ... },
  "Sunday": {
    "date": "<date text>",
    "Brunch": ["<item>", "<item>", ...]
  }
}

Rules:
- Use the exact section names shown above as JSON keys, even if the photo's
  own labels are ambiguous or repeated (e.g. two "Lunch" banners in the photo
  map to "Lunch - Rice Bowl (Rasoi Dining)" for the rice-bowl-concept block
  and "Lunch" for the regular detailed lunch block).
- Category labels are whatever the row label says (e.g. "Cereal", "Dal",
  "Soup"). If a category legitimately repeats within a section in the photo
  (e.g. two separate beverage rows), disambiguate with a short parenthetical
  so JSON keys stay unique, e.g. "Beverage (Tea)" and "Beverage (Coffee)".
- If a cell is genuinely blank/not on the menu for that day, omit that
  category for that day rather than inventing a value.
- If a day/section isn't visible in the photo at all, omit that key entirely.
"""

TRACKER_PROMPT_TEMPLATE = """
Here is a photo of a food tray. Here is today's actual menu item list:
{items}

Which of these EXACT items (only from this list, verbatim) are visibly
present on the tray in the photo? Return ONLY JSON: {{"detected": ["item",
...]}}. If none are clearly identifiable, return {{"detected": []}}. Do not
include any item not in the list above.
"""


def fetch_menu_image(file_id: str = None) -> Path:
    """
    Download the menu photo from Google Drive (file must be shared as
    "Anyone with the link"). Falls back to the bundled sample photo if the
    fetch fails, so the app always has something to run against.
    """
    file_id = file_id or DRIVE_FILE_ID
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        if not response.content:
            raise ValueError("empty response body")
    except Exception:
        return SAMPLE_MENU_PATH

    CACHED_MENU_PATH.parent.mkdir(exist_ok=True)
    CACHED_MENU_PATH.write_bytes(response.content)
    return CACHED_MENU_PATH


def parse_menu_image(image_path: Path = None, attempts: int = 3) -> dict:
    """
    OCR + structure the menu photo via Gemini vision.

    Observed in testing: this call occasionally (~1 in 4-5 tries) returns a
    response that doesn't match the expected shape — likely the model
    struggling with the length/complexity of a full weekly grid in one
    shot, not a prompt bug (the same image parses correctly most of the
    time). Retrying is the practical fix; only raises after all attempts
    fail so a real, persistent problem still surfaces to the UI.
    """
    image_path = image_path or SAMPLE_MENU_PATH

    last_error = None
    for _ in range(attempts):
        try:
            menu = generate_json(MENU_PROMPT, image_path=image_path)
        except GeminiError as exc:
            last_error = exc
            continue

        if any(day in menu for day in DAYS):
            return menu
        last_error = GeminiError(
            "Gemini's response didn't contain any recognizable day of the week."
        )

    raise GeminiError(
        f"Couldn't get a usable menu reading after {attempts} attempts "
        f"(last error: {last_error}) — the photo may be unreadable."
    )


def load_menu() -> dict:
    """Convenience wrapper: fetch (or use sample) then parse via Gemini."""
    path = fetch_menu_image()
    return parse_menu_image(path)


def detect_items_in_photo(photo_path, candidate_items: list) -> list:
    """
    Ask Gemini which of today's real menu items are visible in a tray photo.
    Grounded against candidate_items so it can never invent a dish that
    isn't actually on the menu. Returns [] (rather than raising) on any
    Gemini failure, so the UI can fall back to manual selection.
    """
    if not candidate_items:
        return []
    prompt = TRACKER_PROMPT_TEMPLATE.format(items="\n".join(f"- {i}" for i in candidate_items))
    try:
        result = generate_json(prompt, image_path=photo_path)
    except GeminiError:
        return []

    detected = result.get("detected", [])
    candidate_set = set(candidate_items)
    return [item for item in detected if item in candidate_set]


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
