"""
BatchCaptain.AI — ask what's for lunch, track what you actually ate.

One screen, two states. Landing: the captain large and centred with the value
proposition in two speech bubbles. Answering: the answer in a big bubble, the
captain small and propped on the prompt bar.

Menu source: the weekly mess menu photo (there is no spreadsheet upstream — it
only ever exists as the image posted to the batch WhatsApp group), fetched from
Google Drive and OCR'd by Gemini. See menu_data.py.

IMPORTANT: st.chat_input must stay at module top level. Streamlit only pins it
to the bottom of the viewport when it has no ancestor block — putting it inside
st.tabs, st.container or a column silently makes it scroll with the page.

Run with: streamlit run app.py
"""

import random
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

import macros
import menu_data
import query
import ui
from gemini_client import GeminiError

st.set_page_config(page_title="BatchCaptain.AI", page_icon="🍛",
                   layout="centered")
ui.inject_theme()

# Shown in the prompt bar, one per session, in placeholder grey.
# Kept short: Pixelify Sans runs wide, and a longer hint wraps and clips
# inside the single-line prompt bar.
TAGLINES = [
    "What's there to eat today?",
    "Most protein at dinner?",
    "What's for snacks?",
    "What's for lunch tomorrow?",
]

HERO_LEFT = "Upload images of your meal to get exact macro counts!"
HERO_RIGHT = "Ask what's for lunch and track what you actually ate..."


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
st.session_state.setdefault("tagline", random.choice(TAGLINES))

ui.wordmark()

# --------------------------------------------------------------- menu load
try:
    menu, menu_source = get_menu()
    menu_error = None
except GeminiError as exc:
    menu, menu_source, menu_error = {}, None, str(exc)

if menu_error:
    ui.perch("error")
    st.error(f"Couldn't read this week's menu: {menu_error}")
    st.stop()

if menu_source == "sample":
    st.warning("Showing the bundled sample menu — couldn't reach the Drive "
               "photo, so this may not be this week's food.")
elif menu_source == "cache":
    st.info("Showing the last menu photo downloaded — couldn't reach Drive "
            "just now.")

pending = st.session_state.pop("pending_prompt", None)
has_conversation = bool(st.session_state.messages) or st.session_state.tray_photo

# ------------------------------------------------------------ landing state
if not has_conversation:
    ui.hero(HERO_LEFT, HERO_RIGHT)

# -------------------------------------------------------------- transcript
for index, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
        continue

    ui.answer_bubble(message.get("html") or message["content"])
    if index == len(st.session_state.messages) - 1 and message.get("follow_up_prompt"):
        if st.button(message["follow_up_label"], key=f"followup_{index}"):
            st.session_state.pending_prompt = message["follow_up_prompt"]
            st.rerun()

# ------------------------------------------------------------ tray tracker
tray_photo = st.session_state.tray_photo
if tray_photo is not None:
    today = datetime.now().strftime("%A")
    today_items = sorted(set(menu_data.all_items_for_day(menu, today)))

    st.image(tray_photo, width=200)
    if not today_items:
        st.write(f"I don't have {today}'s menu to check your tray against.")
    else:
        with st.spinner("Looking at your tray..."):
            detected = get_detected_items(tray_photo, tuple(today_items))
        st.caption("Tick what's actually on your plate — I've pre-selected what "
                   "I could recognise.")
        selected = st.multiselect("On your tray", options=today_items,
                                  default=detected, label_visibility="collapsed")
        if selected:
            for entry in macros.per_item_macros(selected):
                st.markdown(f"- {entry['item']} — "
                            f"{macros.format_macros(entry['macros'])}")
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

# ------------------------------------------------- captain on the prompt bar
if has_conversation:
    last = st.session_state.messages[-1] if st.session_state.messages else None
    state = "answering" if last and last["role"] == "assistant" else "thinking"
    ui.perch(state, st.session_state.pose)

# ------------------------------------------------------------- prompt bar
# TOP LEVEL ONLY — see the module docstring.
submitted = st.chat_input(st.session_state.tagline, accept_file=True,
                          file_type=["jpg", "jpeg", "png"])

typed = pending
if submitted is not None:
    if getattr(submitted, "files", None):
        st.session_state.tray_photo = submitted.files[0].getvalue()
        st.rerun()
    typed = submitted.text or pending

if typed:
    st.session_state.messages.append({"role": "user", "content": typed})
    result = query.answer(typed, menu, now=datetime.now())
    st.session_state.pose += 1
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["reply"],
        "html": result.get("reply_html"),
        "follow_up_prompt": result["follow_up_prompt"],
        "follow_up_label": result["follow_up_label"],
    })
    st.session_state.tagline = random.choice(TAGLINES)
    st.rerun()
