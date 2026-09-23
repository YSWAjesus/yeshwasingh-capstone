"""
Everyday foods offered alongside today's menu.

The tray tracker could only ever offer dishes from today's mess grid, which
is why it tracked the mess rather than a day. A banana in your room, chai at
the tuck shop, Maggi at midnight — all real food, none of it on the grid.

EVERY NAME HERE MUST ALREADY RESOLVE THROUGH macros.lookup. This list creates
no nutrition data: it is a shortcut to records that already exist, each with
its own source and confidence band, most of them present because the dish
also appears somewhere on the mess menu. tools/check_quick_add.py fails if
any name here stops resolving, so a later rename cannot quietly turn a
tapable chip into "no macro estimate yet".

Anything NOT here can still be typed — it is simply logged with no estimate
and disclosed as a gap, which is the honest outcome.
"""

# Ordered roughly by how often a student reaches for them, because this is
# rendered as a list they scroll.
EVERYDAY_FOODS = [
    # drinks
    "tea", "coffee", "milk", "buttermilk", "lassi", "fruit juice",
    # fruit and cold things
    "banana", "cut fruit", "curd",
    # bread and staples
    "brown bread", "white bread", "butter", "phulka", "plain rice",
    "jeera rice", "aloo paratha", "idly", "dhokla",
    # south indian / snacks
    "sambar", "coconut chutney", "green chutney", "samosa", "maggi",
    "pizza", "papad", "mixed pickle",
    # mains people eat outside the mess too
    "dal fry", "paneer butter masala", "sprouted moong salad", "green salad",
    # sweet
    "gulab jamun", "jalebi", "slice cake", "chocolate icecream",
    # breakfast cereals
    "cornflakes", "wheat flakes",
]


def options(exclude=()) -> list:
    """Pantry names not already offered by today's menu."""
    lowered = {str(item).strip().lower() for item in exclude}
    return [food for food in EVERYDAY_FOODS if food.lower() not in lowered]
