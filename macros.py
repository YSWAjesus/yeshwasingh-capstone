"""
Approximate macro reference table for common mess/canteen dishes.

Values are per typical single serving, in {calories (kcal), protein (g),
carbs (g), fat (g)}. These are rough estimates for demo purposes, not
verified nutrition-lab numbers — good enough to show "roughly what am I
eating", not for medical/dietary compliance use.

MVP note: this table is looked up by dish name (case-insensitive, trimmed).
Any dish not in the table is reported as "not estimated yet" rather than
guessing a number, so the UI never silently fabricates a macro estimate.
Swapping this out for a real vision/LLM-based estimator is a final-goal item
(see plan.md) once an API key is available.
"""

MACROS = {
    # Breakfast — cereals, milk, beverages
    "cornflakes": {"calories": 120, "protein": 2, "carbs": 26, "fat": 1},
    "wheat flakes": {"calories": 130, "protein": 3, "carbs": 27, "fat": 1},
    "choco flakes": {"calories": 150, "protein": 2, "carbs": 30, "fat": 3},
    "hot & cold milk": {"calories": 120, "protein": 6, "carbs": 9, "fat": 6},
    "tea": {"calories": 60, "protein": 2, "carbs": 8, "fat": 2},
    "coffee": {"calories": 60, "protein": 2, "carbs": 8, "fat": 2},
    "coffee/ bournvita": {"calories": 110, "protein": 3, "carbs": 18, "fat": 3},
    "mix cut fruit": {"calories": 70, "protein": 1, "carbs": 17, "fat": 0},
    "fruit juice": {"calories": 90, "protein": 1, "carbs": 22, "fat": 0},
    "banana": {"calories": 105, "protein": 1, "carbs": 27, "fat": 0},
    "cucumber juice": {"calories": 40, "protein": 1, "carbs": 9, "fat": 0},
    "cut papaya": {"calories": 55, "protein": 1, "carbs": 14, "fat": 0},
    "brown bread": {"calories": 80, "protein": 3, "carbs": 15, "fat": 1},
    "white bread": {"calories": 80, "protein": 2, "carbs": 15, "fat": 1},
    "wheat bread": {"calories": 80, "protein": 3, "carbs": 15, "fat": 1},
    "butter": {"calories": 100, "protein": 0, "carbs": 0, "fat": 11},
    "mixed fruit jam": {"calories": 55, "protein": 0, "carbs": 14, "fat": 0},
    "ghee podi idly": {"calories": 220, "protein": 5, "carbs": 32, "fat": 8},
    # Indian breakfast mains
    "poori bhaji": {"calories": 350, "protein": 6, "carbs": 45, "fat": 16},
    "medu wada": {"calories": 180, "protein": 5, "carbs": 20, "fat": 9},
    "idly": {"calories": 150, "protein": 4, "carbs": 30, "fat": 1},
    "veg upma": {"calories": 220, "protein": 5, "carbs": 35, "fat": 7},
    "masala poha": {"calories": 250, "protein": 5, "carbs": 40, "fat": 8},
    "daliya upma": {"calories": 210, "protein": 6, "carbs": 38, "fat": 5},
    "sabudana khichdi": {"calories": 300, "protein": 3, "carbs": 45, "fat": 12},
    "matki sample": {"calories": 180, "protein": 9, "carbs": 26, "fat": 4},
    "pongal": {"calories": 260, "protein": 6, "carbs": 40, "fat": 8},
    "vermicelli upma": {"calories": 230, "protein": 5, "carbs": 38, "fat": 6},
    "uttapam": {"calories": 200, "protein": 5, "carbs": 32, "fat": 5},
    # Chutneys / accompaniments
    "aloo bhaji": {"calories": 150, "protein": 3, "carbs": 22, "fat": 6},
    "coconut chutney": {"calories": 90, "protein": 1, "carbs": 4, "fat": 8},
    "tomato chutney": {"calories": 60, "protein": 1, "carbs": 10, "fat": 2},
    "sambar": {"calories": 130, "protein": 6, "carbs": 20, "fat": 3},
    "matki sambar": {"calories": 130, "protein": 6, "carbs": 20, "fat": 3},
    "farshan / chop onion": {"calories": 90, "protein": 2, "carbs": 12, "fat": 4},
    "punjabi chole": {"calories": 280, "protein": 11, "carbs": 35, "fat": 10},
    "pancake": {"calories": 200, "protein": 4, "carbs": 30, "fat": 7},
    "french fried": {"calories": 260, "protein": 3, "carbs": 33, "fat": 13},
    "chocolate honey": {"calories": 120, "protein": 1, "carbs": 25, "fat": 3},
    "kulcha": {"calories": 210, "protein": 5, "carbs": 35, "fat": 6},
    "kashmiri pulao": {"calories": 320, "protein": 6, "carbs": 55, "fat": 9},
    "boondi raita": {"calories": 140, "protein": 4, "carbs": 12, "fat": 8},
    "fryums": {"calories": 120, "protein": 1, "carbs": 15, "fat": 6},
    "chocolate icecream": {"calories": 220, "protein": 4, "carbs": 26, "fat": 11},
    # Lunch/dinner — soups, salads, starters
    "rasam": {"calories": 60, "protein": 2, "carbs": 9, "fat": 2},
    "sweet corn veg soup": {"calories": 90, "protein": 3, "carbs": 15, "fat": 2},
    "manchow soup": {"calories": 100, "protein": 3, "carbs": 14, "fat": 3},
    "hot garlic vegetable soup": {"calories": 90, "protein": 3, "carbs": 13, "fat": 3},
    "veg chowder soup": {"calories": 120, "protein": 3, "carbs": 16, "fat": 5},
    "minestorni soup": {"calories": 110, "protein": 4, "carbs": 17, "fat": 3},
    "onion lachha salad": {"calories": 40, "protein": 1, "carbs": 8, "fat": 0},
    "tandoori salad": {"calories": 50, "protein": 2, "carbs": 8, "fat": 1},
    "mix salad": {"calories": 45, "protein": 1, "carbs": 8, "fat": 1},
    "green salad": {"calories": 35, "protein": 1, "carbs": 7, "fat": 0},
    "kimchi": {"calories": 30, "protein": 1, "carbs": 5, "fat": 1},
    "carrot beet salad": {"calories": 45, "protein": 1, "carbs": 9, "fat": 0},
    "tossed salad": {"calories": 40, "protein": 1, "carbs": 7, "fat": 1},
    "veg salad": {"calories": 40, "protein": 1, "carbs": 8, "fat": 0},
    "dhokla": {"calories": 160, "protein": 5, "carbs": 24, "fat": 5},
    "tandoori potato": {"calories": 170, "protein": 3, "carbs": 26, "fat": 6},
    "dahi wada": {"calories": 200, "protein": 6, "carbs": 24, "fat": 8},
    "potato 65": {"calories": 220, "protein": 3, "carbs": 28, "fat": 11},
    "mix veg pakoda": {"calories": 210, "protein": 4, "carbs": 22, "fat": 12},
    "moong dal kachori": {"calories": 230, "protein": 5, "carbs": 28, "fat": 11},
    "veg manchurian": {"calories": 200, "protein": 5, "carbs": 22, "fat": 10},
    "chinese samosa": {"calories": 220, "protein": 4, "carbs": 26, "fat": 11},
    "corn cheese ball": {"calories": 210, "protein": 5, "carbs": 20, "fat": 12},
    "chana dal wada": {"calories": 200, "protein": 7, "carbs": 22, "fat": 9},
    "papadi chat": {"calories": 250, "protein": 5, "carbs": 30, "fat": 12},
    "ragda chat": {"calories": 260, "protein": 8, "carbs": 34, "fat": 9},
    "green & sweet chutney": {"calories": 40, "protein": 1, "carbs": 9, "fat": 0},
    # Curries and mains
    "mix veg handi": {"calories": 180, "protein": 5, "carbs": 15, "fat": 11},
    "turai masala": {"calories": 130, "protein": 3, "carbs": 12, "fat": 8},
    "lauki do pyaza": {"calories": 120, "protein": 3, "carbs": 11, "fat": 7},
    "tindli chana": {"calories": 160, "protein": 6, "carbs": 18, "fat": 7},
    "mix veg peshwari": {"calories": 190, "protein": 5, "carbs": 16, "fat": 12},
    "moong home style": {"calories": 170, "protein": 9, "carbs": 22, "fat": 5},
    "black chana masala": {"calories": 210, "protein": 10, "carbs": 28, "fat": 6},
    "paneer mutter": {"calories": 280, "protein": 13, "carbs": 12, "fat": 20},
    "chole masala": {"calories": 220, "protein": 10, "carbs": 30, "fat": 7},
    "rajma masala": {"calories": 210, "protein": 11, "carbs": 30, "fat": 5},
    "capsicum zunka": {"calories": 140, "protein": 5, "carbs": 12, "fat": 8},
    "aloo tomato rassa": {"calories": 150, "protein": 3, "carbs": 20, "fat": 7},
    "banana tomato rassa": {"calories": 140, "protein": 2, "carbs": 22, "fat": 5},
    "double dal tadka": {"calories": 180, "protein": 9, "carbs": 22, "fat": 6},
    "dal adraki": {"calories": 170, "protein": 9, "carbs": 20, "fat": 5},
    "dal tadka": {"calories": 170, "protein": 9, "carbs": 20, "fat": 5},
    "dal fry": {"calories": 180, "protein": 9, "carbs": 21, "fat": 6},
    "dal dhaba": {"calories": 190, "protein": 9, "carbs": 21, "fat": 7},
    "dal waran": {"calories": 160, "protein": 8, "carbs": 19, "fat": 5},
    "dal kich": {"calories": 170, "protein": 8, "carbs": 20, "fat": 5},
    # Grains/breads
    "jeera rice": {"calories": 220, "protein": 4, "carbs": 42, "fat": 5},
    "brown onion rice": {"calories": 230, "protein": 4, "carbs": 44, "fat": 5},
    "plain rice": {"calories": 200, "protein": 4, "carbs": 44, "fat": 0},
    "steam rice": {"calories": 200, "protein": 4, "carbs": 44, "fat": 0},
    "steamed rice": {"calories": 200, "protein": 4, "carbs": 44, "fat": 0},
    "onion rice": {"calories": 220, "protein": 4, "carbs": 43, "fat": 4},
    "vegetable garlic fried rice": {"calories": 260, "protein": 5, "carbs": 45, "fat": 8},
    "phulka": {"calories": 90, "protein": 3, "carbs": 18, "fat": 1},
    "taak": {"calories": 90, "protein": 3, "carbs": 18, "fat": 1},
    "pav": {"calories": 130, "protein": 4, "carbs": 24, "fat": 2},
    "curd": {"calories": 60, "protein": 3, "carbs": 5, "fat": 3},
    "butter milk": {"calories": 40, "protein": 2, "carbs": 4, "fat": 1},
    "mixed pickle": {"calories": 25, "protein": 0, "carbs": 3, "fat": 2},
    "roasted papad": {"calories": 35, "protein": 2, "carbs": 6, "fat": 0},
    "rice kheer": {"calories": 210, "protein": 5, "carbs": 32, "fat": 6},
    "moong dal halwa": {"calories": 320, "protein": 6, "carbs": 34, "fat": 18},
    "pal payassam": {"calories": 260, "protein": 5, "carbs": 40, "fat": 8},
    "jalebi": {"calories": 300, "protein": 2, "carbs": 55, "fat": 9},
    "lancha": {"calories": 280, "protein": 3, "carbs": 48, "fat": 9},
    "malpua": {"calories": 290, "protein": 3, "carbs": 45, "fat": 11},
    # Evening snacks
    "maggi": {"calories": 350, "protein": 8, "carbs": 50, "fat": 13},
    "peanut chana chat": {"calories": 230, "protein": 9, "carbs": 22, "fat": 12},
    "masala bhel": {"calories": 220, "protein": 5, "carbs": 32, "fat": 8},
    "chilly bhaji": {"calories": 210, "protein": 3, "carbs": 22, "fat": 12},
    "bombay sandwich": {"calories": 280, "protein": 7, "carbs": 38, "fat": 10},
    "lemon / sev": {"calories": 90, "protein": 2, "carbs": 12, "fat": 4},
    "coconut chutney/ curd": {"calories": 75, "protein": 2, "carbs": 5, "fat": 5},
    "tomato ketchup": {"calories": 20, "protein": 0, "carbs": 5, "fat": 0},
    "punugulu": {"calories": 210, "protein": 4, "carbs": 26, "fat": 10},
    # Dinner extras
    "green peas chowder": {"calories": 120, "protein": 5, "carbs": 16, "fat": 4},
    "sabz shorba": {"calories": 90, "protein": 3, "carbs": 13, "fat": 3},
    "roasted vegetable soup": {"calories": 90, "protein": 3, "carbs": 13, "fat": 2},
    "dal rasam": {"calories": 90, "protein": 4, "carbs": 12, "fat": 3},
    "mixk salad": {"calories": 40, "protein": 1, "carbs": 8, "fat": 0},
    "mixed veg salad": {"calories": 40, "protein": 1, "carbs": 8, "fat": 0},
    "hakka noodles": {"calories": 320, "protein": 7, "carbs": 48, "fat": 10},
    "matki sprouts dry": {"calories": 150, "protein": 9, "carbs": 20, "fat": 4},
    "hot & sour sauce": {"calories": 20, "protein": 0, "carbs": 4, "fat": 0},
    "schezwan sauce": {"calories": 25, "protein": 0, "carbs": 5, "fat": 0},
    "dum aloo banarasi": {"calories": 240, "protein": 4, "carbs": 26, "fat": 13},
    "dum banana": {"calories": 180, "protein": 2, "carbs": 24, "fat": 9},
    "vegetable fried rice": {"calories": 260, "protein": 5, "carbs": 46, "fat": 7},
    "mangotang": {"calories": 100, "protein": 0, "carbs": 25, "fat": 0},
    "mango tang": {"calories": 100, "protein": 0, "carbs": 25, "fat": 0},
    "jaljeera": {"calories": 30, "protein": 0, "carbs": 7, "fat": 0},
    "lemon juice": {"calories": 30, "protein": 0, "carbs": 8, "fat": 0},
    "dry fruit sheera barfi": {"calories": 300, "protein": 5, "carbs": 32, "fat": 16},
    "gulab jamun": {"calories": 280, "protein": 3, "carbs": 45, "fat": 10},
    "shahi tukda": {"calories": 320, "protein": 4, "carbs": 42, "fat": 15},
    "sheer khurma": {"calories": 260, "protein": 4, "carbs": 34, "fat": 11},
    "banana custard": {"calories": 200, "protein": 4, "carbs": 30, "fat": 7},
    "motichoor ladoo": {"calories": 260, "protein": 3, "carbs": 34, "fat": 12},
    "slice cake": {"calories": 250, "protein": 3, "carbs": 36, "fat": 10},
    "pizza": {"calories": 280, "protein": 10, "carbs": 33, "fat": 12},
    "mili juli veg": {"calories": 150, "protein": 4, "carbs": 14, "fat": 8},
    "chana gassi": {"calories": 200, "protein": 8, "carbs": 22, "fat": 9},
    "parwal masala": {"calories": 140, "protein": 3, "carbs": 13, "fat": 8},
    "masala bhat": {"calories": 240, "protein": 5, "carbs": 42, "fat": 6},
    "mirchi salan": {"calories": 160, "protein": 3, "carbs": 12, "fat": 11},
    "chilka wali green moong": {"calories": 180, "protein": 10, "carbs": 24, "fat": 5},
    "garlic dal tadka": {"calories": 180, "protein": 9, "carbs": 20, "fat": 6},
    "mix bhaji": {"calories": 150, "protein": 3, "carbs": 15, "fat": 8},
    "tang": {"calories": 90, "protein": 0, "carbs": 23, "fat": 0},
}


def _normalize(name) -> str:
    return str(name).strip().lower()


def lookup(dish_name):
    """Return macro dict for a single dish, or None if not in the table."""
    return MACROS.get(_normalize(dish_name))


def per_item_macros(items):
    """[{'item': str, 'macros': {...} or None}] — order preserved.

    macros=None means "not in the table". It never means a guessed number.
    """
    return [{"item": str(item), "macros": lookup(item)} for item in items]


def format_macros(macro) -> str:
    """One rendering shared by chat and the tray tracker, so they can't disagree."""
    if not macro:
        return "no macro estimate yet"
    return (f"{macro['calories']} kcal · {macro['protein']}g P · "
            f"{macro['carbs']}g C · {macro['fat']}g F")


def estimate_macros(items):
    """
    Sum macros across a list of dish names.

    Only meaningful when the caller knows the person is eating all of them —
    i.e. the tray tracker, where the user ticks their own plate. A whole
    buffet menu must NOT be summed; use per_item_macros for that.

    Returns (totals, unmatched); unmatched lists dishes with no entry so the
    UI can say "not estimated yet" instead of inventing a number.
    """
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    unmatched = []
    for entry in per_item_macros(items):
        if entry["macros"] is None:
            unmatched.append(entry["item"])
            continue
        for key in totals:
            totals[key] += entry["macros"][key]
    return totals, unmatched
