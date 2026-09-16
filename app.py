"""
BatchCaptain.AI — MVP web app.

Two tabs:
  1. Chat  — ask "what's there to eat?" and get today's menu + macros,
             with a follow-up prompt for the next meal.
  2. Photo Tracker — upload/take a photo of your tray; since there's no
             vision API key wired in yet, you manually tick off which of
             today's actual menu items are on your tray, and macros are
             summed the same way as the chat answers. Auto-recognition
             from the photo itself is a final-goal item (see plan.md).

Run with: streamlit run app.py
"""

from datetime import datetime

import streamlit as st

import menu_data
import query
import time_logic
from macros import estimate_macros

st.set_page_config(page_title="BatchCaptain.AI", page_icon="🍛")


@st.cache_data(ttl=300)
def get_menu():
    return menu_data.load_menu()


st.title("🍛 BatchCaptain.AI")
st.caption("Ask what's for lunch. Track what you actually ate.")

menu = get_menu()

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
        "Snap or upload a photo, then tick off what you actually took from "
        "today's menu. (Auto-recognizing dishes straight from the photo needs "
        "a vision API key we don't have wired in yet — that's a final-goal "
        "item, not this MVP. For now this is a manual confirm, backed by the "
        "same macros table the chat uses.)"
    )

    photo = st.camera_input("Take a photo of your tray") or st.file_uploader(
        "...or upload one", type=["jpg", "jpeg", "png"]
    )
    if photo is not None:
        st.image(photo, caption="Your tray", width=300)

    today = datetime.now().strftime("%A")
    today_items = sorted(set(menu_data.all_items_for_day(menu, today)))

    if not today_items:
        st.info(f"No menu items found for {today} to build a checklist from.")
    else:
        selected = st.multiselect(
            f"Select what's on your tray ({today}'s menu items)",
            options=today_items,
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
