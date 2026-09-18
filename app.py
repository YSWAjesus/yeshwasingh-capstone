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

# "wide" then constrained in CSS: the default "centered" layout caps the
# content column at ~704px, which pinches the prompt bar well short of the
# width the design calls for.
st.set_page_config(page_title="BatchCaptain.AI", page_icon="🍛",
                   layout="wide")
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
st.session_state.setdefault("show_tray", False)
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
has_conversation = (bool(st.session_state.messages)
                    or st.session_state.tray_photo is not None
                    or st.session_state.show_tray)

# ------------------------------------------------------------ landing state
if not has_conversation:
    ui.hero()

# -------------------------------------------------------------- transcript
for index, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
        continue

    ui.answer_bubble(message.get("html") or message["content"])

# ------------------------------------------------------------ tray tracker
if st.session_state.show_tray and st.session_state.tray_photo is None:
    st.caption("Add a photo of your tray — **+** in the bar below opens your "
               "camera roll (and the camera itself on a phone).")
    # The in-page camera widget needs a secure context: it works on localhost
    # and over HTTPS, but a phone hitting this over plain http on the LAN gets
    # a blocked camera. The "+" upload path has no such restriction and opens
    # the native "Take Photo" picker on iOS and Android, so it is the reliable
    # route on a phone until this is deployed behind HTTPS.
    snap = st.camera_input("Photograph your tray", label_visibility="collapsed")
    if snap is not None:
        st.session_state.tray_photo = snap.getvalue()
        st.rerun()
    if st.button("Never mind"):
        st.session_state.show_tray = False
        st.rerun()

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
            st.session_state.show_tray = False
            st.rerun()

# ------------------------------------------- follow-up pills in the prompt bar
# Rendered just before the input so they land next to it in the DOM; CSS
# lifts the whole block into position over the bar.
last_message = st.session_state.messages[-1] if st.session_state.messages else None
options = (last_message or {}).get("follow_up_options") or []
if options:
    with st.container():
        st.markdown('<div class="bc-cta-anchor"></div>', unsafe_allow_html=True)
        # Weighted so the pills sit next to each other rather than being
        # spread evenly across the full bar width.
        columns = st.columns([3] * len(options) + [14])
        for position, option in enumerate(options):
            if columns[position].button(option["label"], key=f"cta_{position}"):
                if option.get("action") == "tray":
                    st.session_state.show_tray = True
                else:
                    st.session_state.pending_prompt = option["prompt"]
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
        "follow_up_options": result.get("follow_up_options") or [],
    })
    st.session_state.tagline = random.choice(TAGLINES)
    st.rerun()
