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
# response4 is deliberately absent: it is a head and one arm with no lower
# body, so perched on the bar it reads as a figure lying down rather than
# standing on it. The file is kept in assets/ rather than deleted, so it can
# come back if it is ever re-drawn full-length.
ANSWER_POSES = [
    "avatar_response5_promptbar.png",
    "avatar_response3_promptbar.png",
    "avatar_response2_promptbar.png",
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

/* Near-black fill with a thin lilac edge, per the mock — not a purple slab. */
[data-testid="stChatInput"] {{
  background: #0d0620 !important;
  border: 1.5px solid rgba(178,140,255,.75) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 30px rgba(0,0,0,.55);
}}
/* Divider after the "+", as drawn. */
[data-testid="stChatInputFileUploadButton"] {{
  border-right: 1px solid rgba(178,140,255,.35);
  margin-right: .55rem; padding-right: .2rem;
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
/* When the CTA pills are on the bar they occupy the same space as the hint,
   so the hint is hidden rather than left to collide with them. */
body:has(.bc-cta-anchor)
  [data-testid="stChatInputTextArea"]:not(:focus)::placeholder {{
  color: transparent !important;
}}
[data-testid="stChatInputTextArea"]::placeholder {{
  transition: color .18s ease;
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
  /* It is fixed, so answers scroll underneath it — this keeps it legible
     instead of tangling with the dish list. */
  background: rgba(7,4,15,.82);
  padding: .12rem .55rem .18rem .5rem; border-radius: 9px;
  backdrop-filter: blur(6px);
}}
.bc-mark em {{ color: {LILAC}; font-style: normal; }}

/* ---------------- landing hero ----------------
   One exported graphic: the captain with both speech bubbles already set in
   Figma. Nothing to position, and the pixel tails are the real artwork
   rather than a CSS approximation of them. */
.bc-hero {{
  display: flex; justify-content: center; align-items: flex-end;
  min-height: 60vh; margin-top: .5rem;
}}
.bc-hero img {{
  max-height: 62vh; max-width: 100%;
  display: block; pointer-events: none;
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
/* Meal heading in a whole-day answer. Sits above the hall headings (h4), so
   it is the brighter of the two and carries a rule to group what follows. */
.bc-answer .meal {{
  font-family: 'Pixelify Sans', monospace;
  font-size: 1.05rem; color: #F3ECFF;
  margin: 1.15rem 0 .1rem 0; padding-bottom: .25rem;
  border-bottom: 1px solid rgba(178,140,255,.22);
}}
.bc-answer .meal:first-of-type {{ margin-top: .7rem; }}
.bc-answer .meal + h4 {{ margin-top: .45rem; }}
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

/* ---------------- follow-up pills, sitting in the prompt bar ----------------
   Streamlit's chat input is a sealed component, so real buttons cannot be
   placed inside its DOM. These are genuine st.buttons lifted into position
   over the bar: visually inside it, structurally layered on top. Only the
   pills take pointer events, so the rest of the bar stays clickable to type
   in. The block is found via :has() on a marker div rather than a Streamlit
   class name, because those are emotion hashes that change every release. */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bc-cta-anchor) {{
  position: fixed; left: 50%; transform: translateX(-50%);
  /* Anchored off the bar's BOTTOM edge, which is stable — its top moves as
     the input grows and shrinks with focus. */
  bottom: 32px; z-index: 120;
  width: 1290px; max-width: 94vw;
  padding-left: 8.4rem;                /* clears the "+" and its divider */
  pointer-events: none;
  gap: .4rem !important;
  /* Animated so focusing the bar doesn't snap them away. Opacity and
     transform only — both composite on the GPU, so this can't jitter the
     fixed-position bar the way animating height or bottom would. */
  transition: opacity .18s ease, transform .18s ease;
}}

/* Typing is the one moment the pills are in the way: they sit ON the bar, so
   they'd overlap the caret and the text being typed. Focus the bar and they
   drop out; click away and they come back. :has() on :focus is why this needs
   no rerun — Streamlit never re-renders, so there is no flash. */
body:has([data-testid="stChatInputTextArea"]:focus)
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bc-cta-anchor) {{
  opacity: 0;
  transform: translateX(-50%) translateY(5px);
}}
/* An invisible pill must not still be clickable. */
body:has([data-testid="stChatInputTextArea"]:focus)
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bc-cta-anchor)
  .stButton > button {{
  pointer-events: none;
}}
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bc-cta-anchor)
  [data-testid="stHorizontalBlock"] {{ gap: .45rem !important; }}

.bc-cta-anchor {{ height: 0; }}

/* ------------------------------- the eaten log -------------------------- */
.bc-log-today {{ margin: 0 0 .15rem; font-size: 1rem; }}
.bc-log-today b {{ color: {ACCENT}; }}
.bc-log-sub {{ margin: 0 0 .6rem; font-size: .82rem; opacity: .72; }}
.bc-log-sub b {{ color: {ACCENT}; opacity: 1; }}
.bc-log-warn {{
  margin: .7rem 0 0; font-size: .74rem; opacity: .6;
  border-top: 1px solid rgba(178,140,255,.18); padding-top: .5rem;
}}
.bc-log-week {{ display: flex; flex-direction: column; gap: .3rem;
                margin: .5rem 0 .7rem; }}
/* Grid, not flex: the day labels and the values must line up in columns even
   though the bar between them is elastic. */
.bc-log-day {{
  display: grid; grid-template-columns: 2.4rem 1fr 4.6rem;
  align-items: center; gap: .55rem; font-size: .76rem;
}}
.bc-log-name {{ font-family: 'Pixelify Sans', monospace; opacity: .62; }}
.bc-log-day.is-today .bc-log-name {{ opacity: 1; color: {LILAC}; }}
.bc-log-day.is-future {{ opacity: .34; }}
.bc-log-bar {{
  display: block; height: 7px; border-radius: 999px;
  background: rgba(178,140,255,.13); overflow: hidden;
}}
.bc-log-bar i {{
  display: block; height: 100%; border-radius: 999px;
  background: {ACCENT}; min-width: 0;
  transition: width .3s ease;
}}
.bc-log-day.is-today .bc-log-bar i {{ background: {LILAC}; }}
.bc-log-value {{ text-align: right; opacity: .66; font-variant-numeric: tabular-nums; }}

.stButton > button {{
  pointer-events: auto;
  /* Fully opaque: these sit ON the bar, so any transparency lets the
     placeholder text show through them. */
  background: #1a0d3d;
  border: 1.5px solid rgba(178,140,255,.75);
  border-radius: 999px;
  color: #CDB8FF;
  font-family: 'Pixelify Sans', monospace;
  font-size: .78rem;
  /* Deliberately shorter than the bar so it reads as sitting inside it. */
  height: 28px; min-height: 28px; line-height: 1;
  padding: 0 .85rem;
  white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}}
.stButton > button:hover {{
  border-color: {ACCENT}; color: {ACCENT};
  background: rgba(255,138,61,.08);
}}

/* ---------------- phone ----------------
   Photographing a tray is the whole reason this has to work on a phone, so
   the desktop tuning above gets pulled in: the bar spans the screen, the
   pills shrink enough that two still fit beside the "+", and the captain
   moves to the right-hand end of the bar so she cannot sit under them. */
@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"] {{
    padding-top: 3rem !important;
    padding-left: .75rem !important; padding-right: .75rem !important;
  }}
  [data-testid="stBottomBlockContainer"] {{
    padding-left: .5rem !important; padding-right: .5rem !important;
  }}
  .bc-mark {{ font-size: .95rem; top: 10px; left: 12px; }}

  .bc-hero {{ min-height: 44vh; }}
  .bc-hero img {{ max-height: 42vh; max-width: 94vw; }}

  .bc-answer {{
    padding: .95rem 1rem; border-radius: 18px;
    font-size: .9rem; margin-bottom: .8rem;
  }}
  .bc-answer::after {{ left: 24px; }}
  .bc-answer h4 {{ font-size: .92rem; }}
  .bc-answer .macros {{ font-size: .75rem; }}

  /* Captain to the right-hand end, clear of the pills. */
  .bc-perch {{ bottom: 46px; }}
  .bc-perch-inner {{
    padding-left: 0; padding-right: .4rem;
    justify-content: flex-end; height: 86px;
  }}
  .bc-perch img {{ max-height: 82px; max-width: 98px; }}
  /* A phone's bar is too narrow for the captain AND two pills. The pills do
     a job; she is decoration, so she stands down while they are showing. */
  body:has(.bc-cta-anchor) .bc-perch {{ display: none; }}

  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bc-cta-anchor) {{
    width: 100%; max-width: 100%;
    padding-left: 3rem; padding-right: .4rem;
    bottom: 30px;
  }}
  /* Streamlit stacks columns on narrow screens, which would push a pill
     out of the bar. Keep them inline and size them to fit a phone. */
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bc-cta-anchor)
    [data-testid="stHorizontalBlock"] {{
    flex-wrap: nowrap !important; gap: .3rem !important;
  }}
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .bc-cta-anchor)
    [data-testid="stColumn"] {{
    width: auto !important; flex: 0 0 auto !important;
    min-width: 0 !important;
  }}
  .stButton > button {{
    font-size: .62rem; height: 24px; min-height: 24px; padding: 0 .45rem;
  }}
  [data-testid="stChatInputTextArea"] {{ font-size: .85rem !important; }}
  [data-testid="stChatInputFileUploadButton"] button::after {{ font-size: 1.5rem; }}
}}

</style>
""",
        unsafe_allow_html=True,
    )


def wordmark() -> None:
    st.markdown('<div class="bc-mark">🍛 BatchCaptain<em>.AI</em></div>',
                unsafe_allow_html=True)


def hero() -> None:
    """Landing state: the composed graphic, exactly as exported from Figma."""
    src = _sprite("hero_composed.png")
    if not src:
        return
    st.markdown(f'<div class="bc-hero"><img src="{src}"/></div>',
                unsafe_allow_html=True)


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


def log_panel(day: dict, week: dict, durable: bool) -> None:
    """Today's plate and the week behind it.

    Built as one HTML block rather than st.columns because Streamlit restacks
    columns on narrow screens, and a seven-day strip that becomes a seven-row
    list stops being a strip. Bars are percentage widths of the week's own
    peak, so the shape is readable without an axis.
    """
    peak = max([d["calories"] for d in week["days"]] + [1])

    rows = []
    for entry in week["days"]:
        width = round(entry["calories"] / peak * 100)
        classes = "bc-log-day"
        if entry["is_today"]:
            classes += " is-today"
        if entry["is_future"]:
            classes += " is-future"
        value = f"{entry['calories']} kcal" if entry["calories"] else "—"
        rows.append(
            f'<div class="{classes}">'
            f'<span class="bc-log-name">{entry["short"]}</span>'
            f'<span class="bc-log-bar"><i style="width:{width}%"></i></span>'
            f'<span class="bc-log-value">{value}</span>'
            f"</div>"
        )

    if day["meals"]:
        eaten = ", ".join(
            f"{r['meal'].lower()}" for r in day["rows"] if r.get("meal"))
        headline = (
            f'<p class="bc-log-today">Today: <b>{day["calories"]} kcal</b> · '
            f'{day["protein"]}g protein · {day["carbs"]}g carbs · '
            f'{day["fat"]}g fat</p>'
            f'<p class="bc-log-sub">{day["meals"]} meal'
            f'{"" if day["meals"] == 1 else "s"} logged'
            f'{" — " + eaten if eaten else ""}.'
            + (f' {day["incomplete"]} had a dish with no macro estimate, so '
               f'the real total is a little higher.'
               if day["incomplete"] else "")
            + "</p>"
        )
    else:
        headline = ('<p class="bc-log-today">Nothing logged today yet.</p>'
                    '<p class="bc-log-sub">Photograph your tray and tick what '
                    'you took — it adds up here.</p>')

    total = week["total"]
    if total["days_logged"]:
        footer = (f'<p class="bc-log-sub">This week: <b>{total["calories"]} '
                  f'kcal</b> across {total["meals"]} meal'
                  f'{"" if total["meals"] == 1 else "s"} on '
                  f'{total["days_logged"]} day'
                  f'{"" if total["days_logged"] == 1 else "s"} — averaging '
                  f'{total["avg_calories"]} kcal on the days you logged.</p>')
    else:
        footer = ""

    warning = "" if durable else (
        '<p class="bc-log-warn">This log lives on the server\'s own disk, '
        'which is wiped whenever the app redeploys. Treat it as temporary '
        'until a persistent volume is attached.</p>')

    st.markdown(
        f'<div class="bc-answer bc-log">{headline}'
        f'<div class="bc-log-week">{"".join(rows)}</div>'
        f"{footer}{warning}</div>",
        unsafe_allow_html=True,
    )
