"""
Presentation layer: the pixel-art skin, the avatar state machine, and the
speech bubble. Kept out of app.py so the app file stays about behaviour.
"""

import base64
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"
SPRITES = ASSETS / "derived"

# ---------------------------------------------------------------------------
# AVATAR STATES — remap here if the art changes; nothing else needs editing.
# ---------------------------------------------------------------------------
AVATAR = {
    "idle": "avatar_idle.png",
    "thinking": "avatar_response1_promptbar.png",
    "answering": "avatar_response5_promptbar.png",  # the lightbulb pose
    "error": "avatar_erroroccured.png",
}

# Extra poses, cycled so repeated answers don't look identical.
ANSWER_POSES = [
    "avatar_response5_promptbar.png",
    "avatar_response3_promptbar.png",
    "avatar_response2_promptbar.png",
    "avatar_response4_promptbar.png",
]

ACCENT = "#FF8A3D"


def _data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def inject_theme() -> None:
    """Gradient background, pixel chrome, and the sticky prompt bar styling."""
    bubble = _data_uri(ASSETS / "bubble.png")
    st.markdown(
        f"""
<style>
.stApp {{
  background: linear-gradient(180deg,#4b2494 0%,#2a1358 45%,#0b0618 100%) !important;
  background-attachment: fixed !important;
}}
[data-testid="stHeader"], .stAppHeader {{ background: transparent !important; }}
[data-testid="stToolbar"], .stAppToolbar {{ display: none !important; }}
[data-testid="stBottom"] {{ background: transparent !important; }}
[data-testid="stBottomBlockContainer"] {{
  background: transparent !important;
  padding-bottom: 1.75rem !important;
  padding-top: .75rem !important;
}}

/* The prompt bar. It only pins to the bottom because app.py calls
   st.chat_input at top level — putting it inside any container or tab makes
   Streamlit render it inline instead. */
[data-testid="stChatInput"] {{
  background: rgba(255,255,255,.07) !important;
  border: 3px solid #B28CFF !important;
  border-radius: 0 !important;
  box-shadow: 4px 4px 0 rgba(0,0,0,.45);
}}
/* Pixelify renders wide, so the default size clips the placeholder. */
[data-testid="stChatInputTextArea"] {{
  font-size: .95rem !important;
  line-height: 1.5 !important;
}}
[data-testid="stChatInputTextArea"]::placeholder {{
  color: rgba(243,236,255,.40) !important;
}}
[data-testid="stMainBlockContainer"] {{ padding-top: 2rem !important; }}
[data-testid="stChatInputFileUploadButton"] svg {{ display: none !important; }}
[data-testid="stChatInputFileUploadButton"] button::after {{
  content: "+";
  font-size: 1.7rem; line-height: 1; color: #B28CFF;
}}

/* Pixel speech bubble, sliced from the exported art so the border keeps its
   chunky pixels at any size. */
.bc-bubble {{
  border-style: solid;
  border-width: 34px 30px 46px 30px;
  border-image: url("{bubble}") 34 30 46 30 repeat;
  background: #e9e9e9;
  color: #14121c;
  padding: .25rem 1rem 1rem 1rem;
  margin: 0 auto 1.5rem auto;
  max-width: 44rem;
  image-rendering: pixelated;
}}
.bc-bubble p, .bc-bubble li {{ color: #14121c !important; }}

.bc-avatar {{ pointer-events: none; }}
.bc-kcal {{ color: {ACCENT}; font-weight: 700; }}
.bc-macros {{ font-size: .78rem; opacity: .72; }}

/* Suggestion chips */
.stButton > button {{
  background: rgba(255,255,255,.06);
  border: 2px solid rgba(178,140,255,.55);
  border-radius: 0;
  color: #E8DCFF;
}}
.stButton > button:hover {{
  border-color: {ACCENT};
  color: {ACCENT};
}}
</style>
""",
        unsafe_allow_html=True,
    )


def avatar(state: str, pose_index: int = 0):
    """Render the character in the given state, centred."""
    if state == "answering" and ANSWER_POSES:
        filename = ANSWER_POSES[pose_index % len(ANSWER_POSES)]
    else:
        filename = AVATAR.get(state, AVATAR["idle"])
    path = SPRITES / filename
    if not path.exists():
        return
    st.markdown(
        f'<div class="bc-avatar" style="text-align:center">'
        f'<img src="{_data_uri(path)}" width="190"/></div>',
        unsafe_allow_html=True,
    )


def bubble(markdown_html: str) -> None:
    st.markdown(f'<div class="bc-bubble">{markdown_html}</div>',
                unsafe_allow_html=True)
