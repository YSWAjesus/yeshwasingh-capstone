"""
BatchCaptain.AI — ask what's for lunch, track what you actually ate.

One screen: the captain, the conversation, and a prompt bar pinned to the
bottom. The bar's "+" takes a photo of your tray, so both flows live in the
same place.

Menu source: the weekly mess menu photo (there is no spreadsheet upstream —
it only ever exists as the image posted to the batch WhatsApp group), fetched
from Google Drive and OCR'd by Gemini. See menu_data.py.

IMPORTANT: st.chat_input must stay at module top level. Streamlit only pins it
to the bottom of the viewport when it has no ancestor block — putting it inside
st.tabs, st.container or a column silently makes it scroll with the page.

Run with: streamlit run app.py
"""

import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

import halls
import macros
import menu_data
import query
import time_logic
import ui
from gemini_client import GeminiError

st.set_page_config(page_title="BatchCaptain.AI", page_icon="🍛",
                   layout="centered")
ui.inject_theme()

SUGGESTIONS = [
    "What's there to eat today?",
    "What's the most protein-rich thing at dinner?",
    "What's for snacks?",
    "What's for lunch?",
]


@st.cache_data(ttl=1800, show_spinner="Reading this week's menu photo...")
def get_menu():
    return menu_data.load_menu()


@st.cache_data(ttl=3600, show_spinner=False)
def get_detected_items(photo_bytes: bytes, candidate_items: tuple):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(photo_bytes)
        tmp_path = Path(tmp.name)
    try:
        return menu_data.detect_items_in_photo(tmp_path, list(candidate_items))
    finally:
        tmp_path.unlink(missing_ok=True)


st.session_state.setdefault("messages", [])
st.session_state.setdefault("tray_photo", None)
st.session_state.setdefault("pose", 0)

avatar_slot = st.empty()
with avatar_slot:
    ui.avatar("thinking")  # swapped to idle once the menu is in

# --------------------------------------------------------------- menu load
try:
    menu, menu_source = get_menu()
    menu_error = None
except GeminiError as exc:
    menu, menu_source, menu_error = {}, None, str(exc)

if menu_error:
    with avatar_slot:
        ui.avatar("error")
    st.error(f"Couldn't read this week's menu: {menu_error}")
    st.stop()

with avatar_slot:
    ui.avatar("idle")

if menu_source == "sample":
    st.warning("Showing the bundled sample menu — couldn't reach the Drive "
               "photo, so this may not be this week's food.")
elif menu_source == "cache":
    st.info("Showing the last menu photo downloaded — couldn't reach Drive "
            "just now.")

# ------------------------------------------------------------- transcript
pending = st.session_state.pop("pending_prompt", None)

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        is_last = index == len(st.session_state.messages) - 1
        if is_last and message.get("follow_up_prompt"):
            if st.button(message["follow_up_label"], key=f"followup_{index}"):
                st.session_state.pending_prompt = message["follow_up_prompt"]
                st.rerun()

if not st.session_state.messages:
    st.caption("Ask me about the mess menu — or hit + to photograph your tray.")
    columns = st.columns(2)
    for position, suggestion in enumerate(SUGGESTIONS):
        if columns[position % 2].button(suggestion, key=f"suggest_{position}",
                                        use_container_width=True):
            st.session_state.pending_prompt = suggestion
            st.rerun()

# ------------------------------------------------------------ tray tracker
tray_photo = st.session_state.tray_photo
if tray_photo is not None:
    today = datetime.now().strftime("%A")
    today_items = sorted(set(menu_data.all_items_for_day(menu, today)))

    with st.chat_message("user"):
        st.image(tray_photo, width=220)

    with st.chat_message("assistant"):
        if not today_items:
            st.write(f"I don't have {today}'s menu to check your tray against.")
        else:
            with avatar_slot:
                ui.avatar("thinking")
            with st.spinner("Looking at your tray..."):
                detected = get_detected_items(tray_photo, tuple(today_items))
            st.write("Tick what's actually on your plate — I've pre-selected "
                     "what I could recognise.")
            selected = st.multiselect("On your tray", options=today_items,
                                      default=detected,
                                      label_visibility="collapsed")
            if selected:
                for entry in macros.per_item_macros(selected):
                    st.markdown(
                        f"- {entry['item']} — {macros.format_macros(entry['macros'])}"
                    )
                totals, unmatched = macros.estimate_macros(selected)
                st.metric("Total", f"{totals['calories']} kcal")
                left, middle, right = st.columns(3)
                left.metric("Protein", f"{totals['protein']} g")
                middle.metric("Carbs", f"{totals['carbs']} g")
                right.metric("Fat", f"{totals['fat']} g")
                if unmatched:
                    st.caption("No estimate yet for: " + ", ".join(unmatched))
            if st.button("Clear tray"):
                st.session_state.tray_photo = None
                st.rerun()

# ------------------------------------------------------------- prompt bar
# TOP LEVEL ONLY — see the module docstring.
submitted = st.chat_input("What's there to eat?", accept_file=True,
                          file_type=["jpg", "jpeg", "png"])

typed = pending
if submitted is not None:
    if getattr(submitted, "files", None):
        st.session_state.tray_photo = submitted.files[0].getvalue()
        st.rerun()
    typed = submitted.text or pending

if typed:
    st.session_state.messages.append({"role": "user", "content": typed})
    with avatar_slot:
        ui.avatar("thinking")
    with st.spinner("Checking the menu..."):
        result = query.answer(typed, menu, now=datetime.now())
    st.session_state.pose += 1
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["reply"],
        "follow_up_prompt": result["follow_up_prompt"],
        "follow_up_label": result["follow_up_label"],
    })
    st.rerun()

# Show the answering pose once a reply is on screen.
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    with avatar_slot:
        ui.avatar("answering", st.session_state.pose)

context = time_logic.meal_context(datetime.now())
window = time_logic.window_for(context["meal_type"])
when = {"serving": "on now", "just_ended": "just finished",
        "upcoming": f"from {window[0].strftime('%H:%M')}" if window else ""}
st.caption(f"{context['meal_type']} — {when.get(context['status'], '')}")
