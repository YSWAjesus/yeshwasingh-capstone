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

import hashlib
import json
import os
from pathlib import Path

import requests

import halls
from gemini_client import GeminiError, generate_json

SAMPLE_MENU_PATH = Path(__file__).parent / "sample_menu.jpg"
CACHED_MENU_PATH = Path(__file__).parent / ".cache" / "menu.jpg"

# The real photo already sitting in the student's shared Drive folder.
# Update this each week after re-uploading a fresh menu photo to Drive.
DRIVE_FILE_ID = os.environ.get("DRIVE_FILE_ID") or "1-oPVFOPdBshCwpXypDPgZlIj84hoI4w0"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# The exact section banners halls.py knows how to resolve. This is an enum in
# the response schema, not a request in the prompt, so the model physically
# cannot return "Evening Snack" or "Rice Bowl" and quietly lose a whole meal.
SECTION_NAMES = [
    "Breakfast",
    "Lunch - Rice Bowl (Rasoi Dining)",
    "Lunch",
    "Evening Snacks",
    "Dinner",
]

# Arrays rather than objects-with-dynamic-keys, because a response schema can
# only constrain fixed field names. Category labels vary week to week ("Dal",
# "Soup", "Gravy Veg"), so they live in a `category` VALUE that the schema can
# require, instead of being a KEY it could not describe. _menu_from_payload
# folds this back into the dict shape query.py and halls.py already expect.
MENU_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "days": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "day": {"type": "STRING", "enum": DAYS},
                    "date": {"type": "STRING"},
                    "sections": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "section": {"type": "STRING", "enum": SECTION_NAMES},
                                "rows": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "category": {"type": "STRING"},
                                            "dish": {"type": "STRING"},
                                        },
                                        "required": ["category", "dish"],
                                    },
                                },
                            },
                            "required": ["section", "rows"],
                        },
                    },
                    "brunch": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["day", "date", "sections"],
            },
        }
    },
    "required": ["days"],
}

MENU_PROMPT = """
You are reading a weekly mess/canteen menu from a photo. It's a grid: days
of the week as columns (Monday through Sunday, each with a date), and food
categories as rows, grouped under meal-section banners such as Breakfast,
a "Rice Bowl Concept" lunch line, the main Lunch line, Evening Snacks, and
Dinner.

Return one entry per day you can see, each with:
- "day": which weekday the column is.
- "date": the date text exactly as printed, e.g. "21-Sep".
- "sections": one entry per meal banner in that column. "section" must be
  the banner it corresponds to; "rows" are the category/dish pairs under it.
  Where the photo shows two lunch banners, the rice-bowl-concept block is
  "Lunch - Rice Bowl (Rasoi Dining)" and the regular detailed lunch block is
  "Lunch".
- "brunch": ONLY for Sunday, and only if Sunday replaces its breakfast and
  lunch rows with a single combined brunch column. Put those items here as a
  flat list. Leave it empty for every other day. Sunday usually still has its
  own Evening Snacks and Dinner rows — read those into "sections" as normal.

Rules:
- "category" is whatever the row label says ("Cereal", "Dal", "Soup"). If the
  same category appears twice in one section, just return it twice; the rows
  are a list, so nothing is lost.
- If a cell is genuinely blank or not on the menu that day, omit that row
  rather than inventing a dish.
- If a day or section isn't visible in the photo at all, omit it entirely.
  Do not pad the response with empty days to make it look complete.
"""

TRACKER_PROMPT_TEMPLATE = """
Here is a photo of a food tray. Here is today's actual menu item list:
{items}

Which of these EXACT items (only from this list, verbatim) are visibly
present on the tray in the photo? Return ONLY JSON: {{"detected": ["item",
...]}}. If none are clearly identifiable, return {{"detected": []}}. Do not
include any item not in the list above.
"""


TRACKER_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {"detected": {"type": "ARRAY", "items": {"type": "STRING"}}},
    "required": ["detected"],
}


_IMAGE_MAGIC = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")


def fetch_menu_image(file_id: str = None):
    """
    Download this week's menu photo from Google Drive (shared as "Anyone with
    the link"). Returns (path, source) where source is "drive", "cache" or
    "sample", so the UI can say which menu it is actually showing.

    Falling back silently would be dangerous: a lapsed share link or a brief
    network blip would make the app present a months-old bundled menu as if it
    were today's.
    """
    file_id = file_id or DRIVE_FILE_ID
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.content
        if not content:
            raise ValueError("empty response body")
        # A lapsed share link returns 200 OK with an HTML sign-in page, which
        # would otherwise be written as .jpg and posted to Gemini as an image.
        if not content.startswith(_IMAGE_MAGIC):
            raise ValueError("Drive returned something that isn't an image "
                             "(the share link may have lapsed)")
    except Exception:
        if CACHED_MENU_PATH.exists():
            return CACHED_MENU_PATH, "cache"
        return SAMPLE_MENU_PATH, "sample"

    CACHED_MENU_PATH.parent.mkdir(exist_ok=True)
    CACHED_MENU_PATH.write_bytes(content)
    return CACHED_MENU_PATH, "drive"


def _menu_from_payload(payload: dict) -> dict:
    """Fold the schema's array shape back into the dict shape the app uses.

    The schema guarantees field names and the day/section vocabularies; it
    cannot guarantee the content is sane, so this still drops rows it can't
    use rather than letting a half-formed entry through.
    """
    if not isinstance(payload, dict):
        return {}

    menu = {}
    for entry in payload.get("days") or []:
        if not isinstance(entry, dict):
            continue
        day = entry.get("day")
        if day not in DAYS:
            continue

        day_out = {"date": str(entry.get("date") or "")}
        for section in entry.get("sections") or []:
            if not isinstance(section, dict):
                continue
            name = section.get("section")
            if not name:
                continue
            rows = {}
            for row in section.get("rows") or []:
                if not isinstance(row, dict):
                    continue
                category, dish = row.get("category"), row.get("dish")
                if not category or not dish:
                    continue
                # A repeated category (two beverage rows, say) used to need the
                # model to invent a parenthetical to keep JSON keys unique, and
                # a collision silently dropped a dish. Rows are a list now, so
                # the disambiguation happens here where it cannot lose one.
                key, suffix = str(category), 2
                while key in rows:
                    key = f"{category} ({suffix})"
                    suffix += 1
                rows[key] = str(dish)
            if rows:
                day_out[str(name)] = rows

        brunch = [str(i) for i in (entry.get("brunch") or [])
                  if isinstance(i, str) and i.strip()]
        if brunch:
            day_out["Brunch"] = brunch

        menu[day] = day_out
    return menu


def parse_menu_image(image_path: Path = None, attempts: int = 3) -> dict:
    """
    OCR + structure the menu photo via Gemini vision.

    Observed in testing: this call occasionally (~1 in 4-5 tries) returns a
    response that doesn't match the expected shape — likely the model
    struggling with the length/complexity of a full weekly grid in one
    shot, not a prompt bug (the same image parses correctly most of the
    time). Retrying is the practical fix; only raises after all attempts
    fail so a real, persistent problem still surfaces to the UI.

    The response schema removes one whole class of that failure — misnamed
    fields, invented day labels, a section banner spelled differently enough
    to lose a meal. What it cannot prevent is the model simply not reading
    part of the grid, which is why the >= 5 days check below still stands.
    """
    image_path = image_path or SAMPLE_MENU_PATH

    last_error = None
    for _ in range(attempts):
        try:
            payload = generate_json(MENU_PROMPT, image_path=image_path,
                                    schema=MENU_RESPONSE_SCHEMA)
            menu = _menu_from_payload(payload)
        except GeminiError as exc:
            last_error = exc
            continue

        days_found = [d for d in DAYS if halls.resolve_day(menu, d)]
        # Accepting a single day would let through exactly the partial
        # response this retry loop exists to catch.
        if len(days_found) >= 5:
            return menu
        last_error = GeminiError(
            f"Gemini returned only {len(days_found)} of 7 days — partial read."
        )

    raise GeminiError(
        f"Couldn't get a usable menu reading after {attempts} attempts "
        f"(last error: {last_error}) — the photo may be unreadable."
    )


PARSE_CACHE_DIR = Path(__file__).parent / ".cache" / "parsed"


def load_menu(use_cache: bool = True):
    """Fetch this week's photo and OCR it. Returns (menu, source).

    The parsed result is cached on disk keyed by a hash of the image bytes, so
    restarting the app doesn't re-run a 15-60s OCR call on an unchanged photo
    (and doesn't re-roll the ~1-in-5 malformed-response dice). A new photo has
    different bytes, so it misses the cache and is read fresh.
    """
    path, source = fetch_menu_image()
    image_bytes = path.read_bytes()
    digest = hashlib.sha256(image_bytes).hexdigest()[:16]
    cache_file = PARSE_CACHE_DIR / f"{digest}.json"

    if use_cache and cache_file.exists():
        try:
            return json.loads(cache_file.read_text()), source
        except ValueError:
            cache_file.unlink(missing_ok=True)

    menu = parse_menu_image(path)
    PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(menu, indent=2))
    return menu, source


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
        result = generate_json(prompt, image_path=photo_path,
                               schema=TRACKER_RESPONSE_SCHEMA)
    except GeminiError:
        return []

    # Gemini occasionally returns a bare list instead of the object we asked
    # for; .get() on that would raise straight past the caller's handler.
    if not isinstance(result, dict):
        return []

    detected = result.get("detected", [])
    if not isinstance(detected, list):
        return []
    candidate_set = set(candidate_items)
    return [item for item in detected if item in candidate_set]


def all_items_for_day(menu: dict, day: str):
    """Every real dish on a given day, across all sections.

    Filters out the "N/A"/"N/L" placeholders the mess prints in empty cells,
    which would otherwise show up as tickable items on the tray tracker.
    """
    items = []
    day_menu = halls.resolve_day(menu, day)
    for section, content in day_menu.items():
        if section == "date":
            continue
        if isinstance(content, dict):
            items.extend(content.values())
        elif isinstance(content, list):
            items.extend(content)
    return [i for i in items if halls.is_real_dish(i)]
