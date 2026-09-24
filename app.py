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
import meal_log
import menu_data
import pantry
import query
import targets
import time_logic
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
    # Teaches the phrase that opens the day view. With pills gone from the
    # opening screen, the hint is the only thing that says the log exists.
    # Short like the rest: Pixelify runs wide and anything longer wraps to a
    # second line inside a single-line bar.
    "Protein so far today?",
    "What did I eat today?",
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
st.session_state.setdefault("show_log", False)
st.session_state.setdefault("pose", 0)
st.session_state.setdefault("tagline", random.choice(TAGLINES))

# Who this log belongs to. Carried in the URL rather than a cookie or an
# account: bookmark the page and your log comes back, open it in a private
# window and you are a new person. No sign-up, nothing identifying stored.
# Re-set on every run because Streamlit drops params it did not put there.
if "uid" not in st.session_state:
    from_url = st.query_params.get("u")
    st.session_state.uid = (from_url if meal_log._is_safe_id(from_url)
                            else meal_log.new_user_id())
st.query_params["u"] = st.session_state.uid

ui.wordmark(reset_to=st.session_state.uid)

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
                    or st.session_state.show_tray
                    or st.session_state.show_log)

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
# The panel is reachable with NO photo. Logging the mess is a photo-first
# flow, but a banana in your room is not worth photographing, and requiring
# a picture was the whole reason this could only track the mess.
if st.session_state.show_tray or st.session_state.tray_photo is not None:
    tray_photo = st.session_state.tray_photo
    today = time_logic.now().strftime("%A")
    today_items = sorted(set(menu_data.all_items_for_day(menu, today)))

    detected = []
    if tray_photo is not None:
        st.image(tray_photo, width=180)
        if today_items:
            with st.spinner("Looking at your tray..."):
                detected = get_detected_items(tray_photo, tuple(today_items))

    # Today's menu first, then everyday foods that already have a sourced
    # record. Both are real records; the pantry names simply are not on the
    # mess grid today. Anything else can still be typed.
    options = today_items + pantry.options(exclude=today_items)

    st.caption("Tick what you ate — today's menu, or type anything else."
               + (" I've pre-selected what I could recognise."
                  if detected else ""))
    selected = st.multiselect(
        "What you ate", options=options, default=detected,
        accept_new_options=True, label_visibility="collapsed",
        placeholder="Pick from today's menu, or type any food")

    # A toggle, NOT an expander. Streamlit renders an expander's children
    # whether it is open or not, so st.camera_input mounted on every visit and
    # the browser asked for camera permission just for opening the panel — for
    # a student who came to log a banana. This way the widget does not exist
    # until it is asked for.
    if tray_photo is None:
        if st.toggle("Add a photo of my tray", key="want_camera"):
            st.caption("The **+** in the bar below also works, and opens the "
                       "camera directly on a phone.")
            snap = st.camera_input("Photograph your tray",
                                   label_visibility="collapsed")
            if snap is not None:
                st.session_state.tray_photo = snap.getvalue()
                st.rerun()

    if selected:
        # Quantity is expressed by REPEATING a name: macros.estimate_macros
        # adds one record per element, so three phulkas are exactly three
        # times one phulka. Nothing in macros.py or meal_log.py had to change,
        # and the per-serving record the validator gates never sees a scaled
        # number.
        st.caption("How many servings of each?")
        plate = []
        for position, item in enumerate(selected):
            macro = macros.lookup(item)
            known = (f"{macro['calories']} kcal each" if macro
                     else "no macro estimate yet")
            count = st.number_input(
                f"{item} — {known}", min_value=1, max_value=20, value=1,
                step=1, key=f"qty_{position}_{item}")
            plate += [item] * int(count)

        totals, unmatched = macros.estimate_macros(plate)
        st.markdown(f"**{totals['calories']} kcal** · {totals['protein']}g "
                    f"protein · {totals['carbs']}g carbs · {totals['fat']}g fat")
        if unmatched:
            missing = sorted(set(unmatched))
            st.caption("No macro estimate yet for "
                       + ", ".join(missing)
                       + " — logged, but counted as zero, so this total is a "
                         "floor.")

        # Pre-picked from the clock, because you almost always log the meal
        # you are currently eating; still changeable for the times you don't.
        suggested = time_logic.meal_context()["meal_type"]
        meal_col, log_col = st.columns([2, 3])
        meal_choice = meal_col.selectbox(
            "Which meal", meal_log.MEALS,
            index=(meal_log.MEALS.index(suggested)
                   if suggested in meal_log.MEALS else 0),
            label_visibility="collapsed")
        if log_col.button("Log this", type="primary"):
            meal_log.log_meal(st.session_state.uid, plate, totals,
                              meal=meal_choice, unmatched=unmatched)
            st.session_state.tray_photo = None
            st.session_state.show_tray = False
            st.session_state.show_log = True
            st.rerun()

    tray_buttons = st.columns([2, 3])
    if tray_buttons[0].button("Never mind"):
        st.session_state.tray_photo = None
        st.session_state.show_tray = False
        st.rerun()
    if tray_buttons[1].button("See my day"):
        st.session_state.tray_photo = None
        st.session_state.show_tray = False
        st.session_state.show_log = True
        st.rerun()

# ------------------------------------------------------------- the eaten log
if st.session_state.show_log:
    day, week = meal_log.day_and_week(st.session_state.uid)
    ui.log_panel(day, week, meal_log.LOG_IS_DURABLE,
                 target_rows=targets.progress(st.session_state.uid, day))

    with st.expander("Daily target"):
        st.caption("Set only what you want to track. Leave one at 0 and it "
                   "gets no bar — the app has no opinion about what you "
                   "should eat.")
        current = targets.load(st.session_state.uid)
        entered = {}
        for key in targets.TARGET_KEYS:
            entered[key] = st.number_input(
                f"{key.title()} ({targets.UNITS[key]})",
                min_value=0, max_value=targets.CEILINGS[key],
                value=int(current.get(key, 0)), step=targets.STEPS[key],
                key=f"target_{key}")
        if st.button("Save target"):
            targets.save(st.session_state.uid, entered)
            st.rerun()

    log_buttons = st.columns([2, 2, 3])
    if log_buttons[0].button("Log more"):
        st.session_state.show_log = False
        st.session_state.show_tray = True
        st.rerun()
    if log_buttons[1].button("Undo last"):
        meal_log.undo_last(st.session_state.uid)
        st.rerun()
    if log_buttons[2].button("Close"):
        st.session_state.show_log = False
        st.rerun()

# ------------------------------------------- follow-up pills in the prompt bar
# Rendered just before the input so they land next to it in the DOM; CSS
# lifts the whole block into position over the bar.
last_message = st.session_state.messages[-1] if st.session_state.messages else None
options = (last_message or {}).get("follow_up_options") or []
# Pills are FOLLOW-UPS: they only ever appear after an answer, never on the
# opening screen. A landing screen with two calls to action stops being the
# blank slate the design is built around. The way into the log from cold is
# the bar itself -- one of the rotating hints teaches the phrase.
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
                elif option.get("action") == "log":
                    st.session_state.show_log = True
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
    # "What did I eat today?" is a question about the log, not the menu, and
    # query.answer would cheerfully answer it with today's mess listing.
    if meal_log.is_log_question(typed):
        st.session_state.show_log = True
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": typed})
    result = query.answer(typed, menu, now=time_logic.now())
    st.session_state.pose += 1
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["reply"],
        "html": result.get("reply_html"),
        "follow_up_options": result.get("follow_up_options") or [],
    })
    st.session_state.tagline = random.choice(TAGLINES)
    st.rerun()
