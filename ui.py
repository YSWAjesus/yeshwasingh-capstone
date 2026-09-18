"""
Presentation layer: the pixel-art skin, the avatar, and the speech bubbles.

Layout follows the Figma mock:

  Landing  — the captain large and centred, two pixel speech bubbles flanking
             her head carrying the value proposition. Nothing else but the
             prompt bar. The minimalism is the point.
  Answering — the answer fills a large bubble, and the captain is SMALL and
             propped on the prompt bar at bottom left. That is what the
             "_promptbar" suffix on the sprite filenames means: those poses are
             drawn to sit on the bar, not to float at the top of the page.
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

# Cycled so repeated answers don't look identical.
ANSWER_POSES = [
    "avatar_response5_promptbar.png",
    "avatar_response3_promptbar.png",
    "avatar_response2_promptbar.png",
    "avatar_response4_promptbar.png",
]

ACCENT = "#FF8A3D"
LILAC = "#B28CFF"


def _data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def _sprite(name: str):
    path = SPRITES / name
    return _data_uri(path) if path.exists() else None


def inject_theme() -> None:
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

/* The prompt bar sits on the gradient, not on a slab. Streamlit paints a
   background on several nested containers down there, so all of them have to
   be cleared or a lighter purple band shows through behind the bar. */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] > div,
.stBottom, .stBottom > div {{
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: none !important;
}}
[data-testid="stBottomBlockContainer"] {{
  padding-bottom: 1.5rem !important;
  padding-top: .5rem !important;
}}

[data-testid="stChatInput"] {{
  background: rgba(20,10,44,.72) !important;
  border: 2px solid {LILAC} !important;
  border-radius: 14px !important;
  box-shadow: 0 6px 26px rgba(0,0,0,.45);
  backdrop-filter: blur(6px);
}}
[data-testid="stChatInputTextArea"] {{
  font-family: 'Pixelify Sans', monospace !important;
  font-size: .92rem !important;   /* Pixelify runs wide; larger clips the hint */
  caret-color: {LILAC} !important;   /* the blinking lilac insertion point */
  color: #F3ECFF !important;
}}
[data-testid="stChatInputTextArea"]::placeholder {{
  color: rgba(243,236,255,.38) !important;
  font-family: 'Pixelify Sans', monospace !important;
}}
[data-testid="stChatInputFileUploadButton"] svg {{ display: none !important; }}
[data-testid="stChatInputFileUploadButton"] button::after {{
  content: "+";
  font-size: 1.8rem; line-height: 1; color: {LILAC};
  font-family: 'Pixelify Sans', monospace;
}}

/* Wordmark */
.bc-mark {{
  font-family: 'Pixelify Sans', monospace;
  font-size: 1.15rem; letter-spacing: .5px;
  margin: -1rem 0 0 0; opacity: .95;
}}
.bc-mark em {{ color: {LILAC}; font-style: normal; }}

/* ---------------- landing hero ----------------
   A three-column row rather than absolute positioning, so the bubbles can
   never overlap the captain or each other however narrow the window gets.
   The bubbles are drawn in CSS: the exported bubble.png is a 216x174 sprite
   whose chunky border does not survive being stretched to arbitrary sizes. */
.bc-hero {{
  display: flex; justify-content: center; align-items: flex-start;
  gap: .6rem; margin: 1.5rem 0 0 0; flex-wrap: nowrap;
}}
.bc-hero-figure {{ flex: 0 0 auto; align-self: flex-end; }}
.bc-hero img {{
  height: 44vh; max-height: 380px; min-height: 210px;
  display: block; pointer-events: none;
}}
.bc-say {{
  position: relative; flex: 1 1 0; max-width: 11rem; margin-top: 2.2rem;
  font-family: 'Pixelify Sans', monospace;
  font-size: .78rem; line-height: 1.4; text-align: center;
  color: #16141f; background: #e9e9e9;
  padding: .7rem .75rem;
  border: 3px solid #14121c;
  box-shadow: 5px 5px 0 rgba(0,0,0,.45);
}}
.bc-say::after {{        /* pixel tail pointing down at the captain */
  content: ""; position: absolute; bottom: -9px; width: 12px; height: 12px;
  background: #e9e9e9;
  border-right: 3px solid #14121c; border-bottom: 3px solid #14121c;
  transform: rotate(45deg);
}}
.bc-say-l::after {{ right: 18px; }}
.bc-say-r::after {{ left: 18px; }}
.bc-say-r {{ margin-top: .6rem; }}

@media (max-width: 720px) {{
  .bc-hero {{ flex-wrap: wrap; justify-content: center; }}
  .bc-say {{ flex: 0 0 auto; max-width: 47%; margin-top: 0; font-size: .72rem; }}
  .bc-hero-figure {{ order: 3; flex-basis: 100%; text-align: center; }}
  .bc-hero img {{ margin: 0 auto; height: 34vh; }}
}}

/* ---------------- answer bubble ---------------- */
.bc-answer {{
  position: relative;
  background: rgba(30,14,64,.66);
  border: 2px solid rgba(178,140,255,.55);
  border-radius: 26px;
  padding: 1.4rem 1.6rem;
  margin: 0 0 1.1rem 0;
  backdrop-filter: blur(4px);
  font-size: .95rem; line-height: 1.6;
}}
.bc-answer::after {{           /* tail pointing down-left to the captain */
  content: ""; position: absolute; left: 34px; bottom: -14px;
  border-width: 14px 14px 0 0; border-style: solid;
  border-color: rgba(30,14,64,.66) transparent transparent transparent;
}}
.bc-answer h4 {{
  font-family: 'Pixelify Sans', monospace;
  margin: 1rem 0 .35rem 0; font-size: 1rem; color: {LILAC};
}}
.bc-answer .kcal {{ color: {ACCENT}; font-family: 'Pixelify Sans', monospace; }}
.bc-answer .macros {{ opacity: .62; font-size: .8rem; }}
.bc-answer .none {{ opacity: .45; font-size: .8rem; font-style: italic; }}
.bc-answer .lead {{ font-size: 1.02rem; margin-bottom: .2rem; }}
.bc-answer ul {{ margin: .1rem 0 .2rem 0; padding-left: 1.1rem; }}
.bc-answer li {{ margin: .18rem 0; }}

/* ---------------- captain on the prompt bar ---------------- */
/* She stands ON the bar: low enough to overlap its top edge, and behind it
   in z-order so the input always stays clickable. */
.bc-perch {{
  position: fixed; left: 0; right: 0; bottom: 64px;
  pointer-events: none; z-index: 1;
}}
.bc-perch-inner {{
  max-width: 46rem; margin: 0 auto; padding-left: .5rem;
}}
.bc-perch img {{ height: 104px; display: block; }}

/* Suggested follow-up button, indented clear of the captain and kept
   inside the column so a long meal name can't run off the edge. */
.stButton {{ margin-left: 100px; max-width: calc(100% - 108px); }}
.stButton > button {{ white-space: normal; text-align: left; }}
.stButton > button {{
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(178,140,255,.5);
  border-radius: 10px;
  color: #E8DCFF; font-size: .85rem;
}}
.stButton > button:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
</style>
""",
        unsafe_allow_html=True,
    )


def wordmark() -> None:
    st.markdown('<div class="bc-mark">🍛 BatchCaptain<em>.AI</em></div>',
                unsafe_allow_html=True)


def hero(left_line: str, right_line: str) -> None:
    """Landing state: the captain large, with the value proposition either side."""
    src = _sprite(AVATAR["idle"])
    if not src:
        return
    st.markdown(
        f"""
<div class="bc-hero">
  <div class="bc-say bc-say-l">{left_line}</div>
  <div class="bc-hero-figure"><img src="{src}"/></div>
  <div class="bc-say bc-say-r">{right_line}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def perch(state: str, pose_index: int = 0) -> None:
    """The captain, small, standing on the prompt bar."""
    if state == "answering" and ANSWER_POSES:
        name = ANSWER_POSES[pose_index % len(ANSWER_POSES)]
    else:
        name = AVATAR.get(state, AVATAR["idle"])
    src = _sprite(name)
    if not src:
        return
    st.markdown(
        f'<div class="bc-perch"><div class="bc-perch-inner">'
        f'<img src="{src}"/></div></div>',
        unsafe_allow_html=True,
    )


def answer_bubble(html_body: str) -> None:
    st.markdown(f'<div class="bc-answer">{html_body}</div>',
                unsafe_allow_html=True)
