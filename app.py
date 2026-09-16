"""
BatchCaptain.AI — MVP web app.

Two tabs:
  1. Chat  — ask "what's there to eat?" and get today's menu + macros,
             with a follow-up prompt for the next meal.
  2. Photo Tracker — upload/take a photo of your tray; Gemini looks at it
             and pre-selects which of today's real menu items it can see,
             grounded against the actual menu so it can't invent a dish
             that isn't on offer. You review/adjust the checklist before
             macros are summed — a human-reviewed step, not blind trust.

Menu source: a photo of the weekly mess menu (there's no spreadsheet
upstream — this is the only artifact that exists), fetched from Google
Drive and OCR'd/structured by Gemini. See menu_data.py.

Run with: streamlit run app.py
"""

import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

import menu_data
import query
import time_logic
from gemini_client import GeminiError
from macros import estimate_macros

st.set_page_config(page_title="BatchCaptain.AI", page_icon="🍛")


@st.cache_data(ttl=1800, show_spinner="Reading this week's menu photo...")
def get_menu():
    return menu_data.load_menu()


@st.cache_data(ttl=3600, show_spinner="Looking at your tray...")
def get_detected_items(photo_bytes: bytes, candidate_items: tuple):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(photo_bytes)
        tmp_path = Path(tmp.name)
    try:
        return menu_data.detect_items_in_photo(tmp_path, list(candidate_items))
    finally:
        tmp_path.unlink(missing_ok=True)


st.title("🍛 BatchCaptain.AI")
st.caption("Ask what's for lunch. Track what you actually ate.")

try:
    menu = get_menu()
    menu_error = None
except GeminiError as exc:
    menu = {}
    menu_error = str(exc)

if menu_error:
    st.error(f"Couldn't read this week's menu: {menu_error}")
    st.stop()

tab_chat, tab_tracker = st.tabs(["Chat", "Photo Tracker"])

# ---------------------------------------------------------------- Chat tab
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hey, I'm BatchCaptain.AI. Ask me what's for breakfast, "
                "lunch, snacks, or dinner — or just ask what's there to eat "
                "and I'll guess based on the time.",
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("What's there to eat?")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        result = query.answer(user_input, menu, now=datetime.now())
        with st.chat_message("assistant"):
            st.markdown(result["reply"])
        st.session_state.messages.append({"role": "assistant", "content": result["reply"]})

# ------------------------------------------------------------- Tracker tab
with tab_tracker:
    st.subheader("What's on your tray?")
    st.caption(
        "Snap or upload a photo — Gemini will pre-tick what it recognizes "
        "from today's actual menu. Double-check the list (it can miss "
        "things or misread the photo) before the macro total is computed."
    )

    photo = st.camera_input("Take a photo of your tray") or st.file_uploader(
        "...or upload one", type=["jpg", "jpeg", "png"]
    )

    today = datetime.now().strftime("%A")
    today_items = sorted(set(menu_data.all_items_for_day(menu, today)))

    if not today_items:
        st.info(f"No menu items found for {today} to check against.")
    else:
        default_selection = []
        if photo is not None:
            st.image(photo, caption="Your tray", width=300)
            try:
                default_selection = get_detected_items(photo.getvalue(), tuple(today_items))
                if not default_selection:
                    st.caption("Didn't confidently recognize any menu items — pick manually below.")
            except GeminiError as exc:
                st.warning(f"Auto-recognition failed ({exc}) — pick manually below.")

        selected = st.multiselect(
            f"Select what's on your tray ({today}'s menu items)",
            options=today_items,
            default=default_selection,
        )
        if selected:
            totals, unmatched = estimate_macros(selected)
            st.metric("Calories", f"{totals['calories']} kcal")
            col1, col2, col3 = st.columns(3)
            col1.metric("Protein", f"{totals['protein']} g")
            col2.metric("Carbs", f"{totals['carbs']} g")
            col3.metric("Fat", f"{totals['fat']} g")
            if unmatched:
                st.caption(f"Not estimated yet: {', '.join(unmatched)}")

st.divider()
st.caption(
    f"Meal-time logic currently thinks it's **{time_logic.infer_meal_type(datetime.now())}** "
    f"time on **{datetime.now().strftime('%A')}**."
)
