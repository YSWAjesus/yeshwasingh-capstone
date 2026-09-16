"""
One-off script that builds sample_menu.xlsx.

This mirrors the real grid layout used by the mess's actual weekly menu
(seen in the WhatsApp screenshot shared in the Drive folder): days as
columns, food categories as rows, grouped under meal-section banner rows.
Real dish names from that photo are used throughout, so menu_data.py's
parser is exercised against real content rather than placeholder text.

Run once with: python generate_sample_menu.py
Re-run any time you want to regenerate sample_menu.xlsx from scratch.
"""

import openpyxl

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DATES = ["14-Sep", "15-Sep", "16-Sep", "17-Sep", "18-Sep", "19-Sep", "20-Sep"]

# Each block: (banner label, [(category, [7 items, one per day or "" ])])
BREAKFAST = (
    "Breakfast",
    [
        ("Cereal", ["Cornflakes", "Wheat Flakes", "Choco Flakes", "Cornflakes", "Wheat Flakes", "Choco Flakes", ""]),
        ("Milk", ["Hot & Cold Milk"] * 6 + [""]),
        ("Tea", ["Tea"] * 6 + [""]),
        ("Coffee", ["Coffee", "Coffee/ Bournvita", "Coffee", "Coffee/ Bournvita", "Coffee", "Coffee/ Bournvita", ""]),
        ("Fruits/Juice", ["Mix Cut Fruit", "Fruit Juice", "Banana", "Cucumber Juice", "Cut Papaya", "Mix Fruit Juice", ""]),
        ("Bread (Brown)", ["Brown Bread"] * 6 + [""]),
        ("Bread (White)", ["White Bread"] * 6 + [""]),
        ("Preserves", ["Mixed Fruit Jam"] * 6 + [""]),
        ("Indian Breakfast", ["Poori Bhaji", "Medu Wada", "Idly", "Daliya Upma", "Sabudana Khichdi", "Pongal", ""]),
        ("Indian Breakfast (Side)", ["Veg Upma", "Masala Poha", "Idly", "Matki Sample", "Sambar", "Coconut Chutney/ Curd", ""]),
        ("Accompaniment", ["Aloo Bhaji", "Coconut Chutney", "Tomato Chutney", "Sambar", "Farshan / Chop Onion", "Tomato Chutney", ""]),
    ],
)

LUNCH_RICE_BOWL = (
    "Lunch - Rice Bowl (Rasoi Dining)",
    [
        ("Salad", ["Two Bean Salad in Italian Lemon Dressing", "Kachumber Salad with Roasted Cumin", "Crunchy Veg Salad",
                    "Mixed Toppings (broken papdi, roasted peanuts, coriander leaves, mint leaves, chaat masala, black salt, brown onion)",
                    "Assorted Greens Salad", "Spicy Tangy Cabbage Salad", ""]),
        ("Starter", ["Cheesy Vegetable Arancini", "Mix Veg Baby Samosa", "Raw Banana 65", "Chatpata Dal Wada",
                     "Patatas Bravas", "Assorted Veggies Tempura", ""]),
        ("Bowl", ["Basil and Oregano Rice", "Awadhi Paneer and Vegetable Pulao", "Lemon Pepper Rice", "Surti Khawsa",
                  "Sanpish Pan Rice", "Spicy Chilli Garlic Noodles", ""]),
        ("Accompaniment (Stew)", ["Exotic Veggies Alfredo", "Dal Bukhara", "Soya Bean and Capsicum Chettinad",
                                   "Valenciana Stew", "Mapo Tofu", "Mapo Tofu", ""]),
        ("Accompaniment (Bread)", ["Bread Sticks", "Papad", "Fryums", "Fried Noodles", "Garlic Herb Crostini", "Fried Noodles", ""]),
        ("Dessert", ["Coconut and White Chocolate Mousse", "Moong Dal Halwa", "Pal Payassam", "Jalebi Cheesecake",
                     "Arroz Con Leche", "Pastry of the Day", ""]),
        ("Beverage", ["Beverage of the Day"] * 6 + [""]),
    ],
)

LUNCH = (
    "Lunch",
    [
        ("Soup", ["Rasam", "Sweet Corn Veg Soup", "Manchow Soup", "Hot Garlic Vegetable Soup", "Veg Chowder Soup", "Minestorni Soup", ""]),
        ("Salad", ["Onion Lachha Salad", "Tandoori Salad", "Green Salad", "Mix Salad", "Onion Lachha Salad", "Green Salad", ""]),
        ("Side Dish", ["Dhokla", "Tandoori Salad", "Dahi Wada", "Potato 65", "Mix Veg Pakoda", "Moong Dal Kachori", ""]),
        ("Accompaniment", ["Green & Sweet Chutney", "", "", "Green Chutney", "Green & Sweet Chutney", "", ""]),
        ("Dry Veg", ["Mix Veg Handi", "Turai Masala", "Lauki Do Pyaza", "Tindli Chana", "Mix Veg Peshwari", "Moong Home Style", ""]),
        ("Gravy Veg", ["Black Chana Masala", "Paneer Mutter", "Chole Masala", "Rajma Masala", "Moong Home Style", "Aloo Tomato Rassa", ""]),
        ("Dry Veg (Jain)", ["Mix Veg Handi", "Turai Masala", "Lauki Masala", "Tindli Chana", "Mix Veg Peshwari", "Moong Home Style", ""]),
        ("Gravy Veg (Jain)", ["Black Chana Masala", "Paneer Mutter", "Chole Masala", "Rajma Masala", "Moong Home Style", "Banana Tomato Rassa", ""]),
        ("Dal", ["Double Dal Tadka", "Dal Adraki", "Dal Tadka", "Dal Fry", "Dal Dhaba", "Dal Waran", ""]),
        ("Rice", ["Jeera Rice", "Jeera Rice", "Plain Rice", "Brown Onion Rice", "Jeera Rice", "Plain Rice", ""]),
        ("Roti", ["Phulka"] * 6 + [""]),
        ("Curd", ["Curd"] * 6 + [""]),
        ("Pickle", ["Mixed Pickle"] * 6 + [""]),
        ("Papad", ["Fryums", "Roasted Papad", "Roasted Papad", "Roasted Papad", "Fryums", "Roasted Papad", ""]),
        ("Sweet", ["Rice Kheer", "Moong Dal Halwa", "Pal Payassam", "Jalebi", "Lancha", "Malpua", ""]),
    ],
)

EVENING_SNACKS = (
    "Evening Snacks",
    [
        ("Beverage", ["Tea"] * 6 + ["Tea"]),
        ("Beverage (2)", ["Coffee"] * 6 + ["Coffee"]),
        ("Main", ["Maggi", "Peanut Chana Chat", "Masala Bhel", "Chilly Bhaji", "Bombay Sandwich", "Masala Poha", "Punugulu"]),
        ("Accompaniment", ["N/A", "N/A", "N/A", "N/A", "Tomato Ketchup", "Lemon / Sev", "Coconut Chutney"]),
    ],
)

DINNER = (
    "Dinner",
    [
        ("Soup", ["Green Peas Chowder", "Hot Garlic Soup", "Sabz Shorba", "Roasted Vegetable Soup", "Dal Rasam", "Manchow Soup", ""]),
        ("Salad", ["Kimchi", "Mixk Salad", "Carrot Beet Salad", "Mixed Veg Salad", "Tossed Salad", "Veg Salad", ""]),
        ("Side Dish", ["Chinese Samosa", "Corn Cheese Ball", "Chana Dal Wada", "Papadi Chat", "Ragda Chat", "Pizza", ""]),
        ("Accompaniment", ["Schezwan Sauce", "Tomato Ketchup", "Green Chutney", "N/L", "N/A", "Green Chutney", "N/A"]),
        ("Dry Veg", ["Hakka Noodles", "Matki Sprouts Dry", "Turai Masala", "Pav Bhaji", "Cabbage Masala", "Parwal Masala", ""]),
        ("Gravy Veg", ["Hot & Sour Sauce", "Dum Aloo Banarasi", "Rajma Masala", "Boondi Raita", "Paneer Kadai", "Punjabi Chole", ""]),
        ("Dry Veg (Jain)", ["Hakka Noodles", "Matki Sprouts Dry", "Turai Masala", "Pav Bhaji", "Cabbage Masala", "Parwal Masala", ""]),
        ("Gravy Veg (Jain)", ["Hot & Sour Sauce", "Dum Banana", "Rajma Masala", "Boondi Raita", "Paneer Kadai", "Punjabi Chole", ""]),
        ("Rice", ["Vegetable Garlic Fried Rice", "Steam Rice", "Steam Rice", "Masala Bhat", "Steam Rice", "Steam Rice", ""]),
        ("Dal", ["Dal Kich", "Dal Fry", "Chilka Wali Green Moong", "Mirchi Salan", "Garlic Dal Tadka", "Dal Fry", ""]),
        ("Phulka", ["Pav", "Phulka", "Phulka", "Phulka", "Pav", "Phulka", ""]),
        ("Drink", ["Mango Tang", "Tang", "Jaljeera", "Lemon Juice", "Mango Tang", "Tang", ""]),
        ("Pickle", ["Mixed Pickle"] * 6 + [""]),
        ("Papad", ["Roasted Papad"] * 6 + [""]),
        ("Sweet", ["Dry Fruit Sheera Barfi", "Gulab Jamun", "Shahi Tukda", "Motichoor Ladoo", "Slice Cake", "Sheer Khurma", ""]),
    ],
)

SUNDAY_BRUNCH_ITEMS = [
    "Wheat Bread", "Hot & Cold Milk", "Coffee", "Tea", "Banana", "Brown Bread", "White Bread",
    "Butter", "Ghee Podi Idly", "Sambar", "Tomato Chutney", "Pancake", "French Fried",
    "Chocolate Honey", "Punjabi Chole", "Kulcha", "Kashmiri Pulao", "Boondi Raita",
    "Fryums", "Chocolate Icecream",
]

BLOCKS = [BREAKFAST, LUNCH_RICE_BOWL, LUNCH, EVENING_SNACKS, DINNER]


def build_workbook(path="sample_menu.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Menu"

    ws.append(["Day"] + DAYS)
    ws.append(["Date"] + DATES)

    for banner, rows in BLOCKS:
        ws.append([banner] + [""] * 7)
        for category, items in rows:
            ws.append([category] + items)

    # Sunday Brunch: a flat list of items, not a per-weekday grid row.
    ws.append(["Sunday Brunch"] + [""] * 7)
    for item in SUNDAY_BRUNCH_ITEMS:
        ws.append(["", item] + [""] * 6)

    wb.save(path)
    print(f"Wrote {path}")


if __name__ == "__main__":
    build_workbook()
