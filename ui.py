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
/* Dark at the top, opening into purple toward the prompt bar — the light
   sits low, behind the captain, as in the mock. */
.stApp {{
  background: linear-gradient(180deg,#07040f 0%,#160a33 38%,#341a6b 72%,#5a2da8 100%) !important;
  background-attachment: fixed !important;
}}

/* Wide layout, reined back in to the design's column width. */
[data-testid="stMainBlockContainer"] {{
  max-width: 1150px !important;
  padding-top: 3.4rem !important;
  margin: 0 auto !important;
}}
[data-testid="stBottomBlockContainer"] {{ max-width: 1290px !important; }}
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

/* Wordmark, pinned to the top-left of the viewport rather than sitting in
   the centred content column. */
.bc-mark {{
  position: fixed; top: 14px; left: 26px; z-index: 80;
  font-family: 'Pixelify Sans', monospace;
  font-size: 1.15rem; letter-spacing: .5px; opacity: .95;
  pointer-events: none;
}}
.bc-mark em {{ color: {LILAC}; font-style: normal; }}

/* ---------------- landing hero ----------------
   The bubbles are positioned against the FIGURE, not the page, so they stay
   tucked either side of her head at any window width instead of drifting to
   the far edges. */
.bc-hero {{
  display: flex; justify-content: center; align-items: flex-end;
  min-height: 62vh; margin-top: .5rem;
}}
.bc-hero-figure {{ position: relative; flex: 0 0 auto; }}
.bc-hero img {{
  height: 58vh; max-height: 560px; min-height: 260px;
  display: block; pointer-events: none;
}}
.bc-say {{
  position: absolute; width: 12.5rem;
  font-family: 'Pixelify Sans', monospace;
  font-size: .8rem; line-height: 1.45; text-align: center;
  color: #16141f; background: #e9e9e9;
  padding: .75rem .8rem;
  border: 3px solid #14121c;
  box-shadow: 6px 6px 0 rgba(0,0,0,.5);
}}
/* Anchored to the tight hero crop, so these land beside her head: a small
   gap on the left, a slight overlap on the right, as drawn. */
.bc-say-l {{ right: 100%; margin-right: 26px; top: 19%; }}
.bc-say-r {{ left: 100%;  margin-left: -30px;  top: 11%; }}

/* Two-step staircase, so the tail reads as pixel art rather than a smooth
   triangle. bubble.png's own tail can't be used here: border-image repeats
   it along the whole edge. */
.bc-say::before, .bc-say::after {{
  content: ""; position: absolute; background: #e9e9e9;
}}
.bc-say::before {{
  bottom: -11px; width: 22px; height: 11px;
  border-left: 3px solid #14121c; border-right: 3px solid #14121c;
}}
.bc-say::after {{
  bottom: -21px; width: 11px; height: 11px;
  border: 3px solid #14121c; border-top: none;
}}
.bc-say-l::before {{ right: 26px; }}
.bc-say-l::after  {{ right: 26px; }}
.bc-say-r::before {{ left: 26px; }}
.bc-say-r::after  {{ left: 37px; }}

@media (max-width: 900px) {{
  .bc-say {{ width: 9.5rem; font-size: .72rem; }}
  .bc-say-l {{ margin-right: -.6rem; }}
  .bc-say-r {{ margin-left: -.6rem; }}
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
/* She stands ON the bar. The sprites are cropped tight to their own pixels,
   so the image's bottom edge is her feet — anchoring that just inside the
   bar's top edge plants her on it rather than floating her above it. */
.bc-perch {{
  position: fixed; left: 0; right: 0; bottom: 54px;
  pointer-events: none; z-index: 1;
  display: flex; justify-content: center;
}}
.bc-perch-inner {{
  width: 100%; max-width: 1290px; padding-left: 3.6rem;
  display: flex; align-items: flex-end; height: 120px;
}}
.bc-perch img {{
  max-height: 118px; max-width: 150px; width: auto;
  display: block; object-fit: contain;
}}

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
    src = _sprite("hero_idle.png") or _sprite(AVATAR["idle"])
    if not src:
        return
    st.markdown(
        f"""
<div class="bc-hero">
  <div class="bc-hero-figure">
    <div class="bc-say bc-say-l">{left_line}</div>
    <div class="bc-say bc-say-r">{right_line}</div>
    <img src="{src}"/>
  </div>
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
    # Tight-cropped variant, so the bottom of the image is her feet.
    src = _sprite(f"perch_{name}") or _sprite(name)
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
