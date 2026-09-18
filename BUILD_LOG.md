# Build Log

One entry per commit, newest at the top. Ask Claude to fill in / update this
entry (date, time spent, rough tokens used, what shipped) right before each
commit + push.

---

### 2026-09-18 — Agentic macro-gap pipeline (Assessment 2)
- **Time spent:** ~2 hr
- **Tokens used (approx.):** ~254k (agent runs: 82k + 172k)
- **Shipped:** Branch `feat/agentic-macro-refresh`. A custom Skill, a looping
  subagent, two MCP servers and a workflow, run end-to-end on the real menu.
  - **Skill** `nutrition-lookup` — one dish in, one schema-conformant record
    out. Carries the serving conventions (1 katori dal ≈ 150g, 1 chapati ≈
    40g), a source hierarchy topped by IFCT/NIN-ICMR, the sanity gate, a Jain
    derivation rule, and an explicit `unresolved` protocol instead of guessing.
  - **Agent** `macro-gap-filler` — perceive (audit script) → reason (rank by
    how often a dish appears; decide new record vs alias vs not-a-dish) → act
    (skill + MCP search) → observe (merge script's accept/reject verdict).
  - **MCP** — `filesystem` sandboxed to `data/`, and `tavily` for research.
    The agent is denied `Write`/`Edit`, so MCP is its only route to write.
  - **Result: 48 missing dishes → 2, over 13 passes.** 36 accepted, 0 rejected
    on macro grounds, 2 deliberate `unresolved`. Table 154 → 188 entries, all
    188 passing independent re-validation. 33 carry cited URLs.
  - The 2 remaining are `Beverage of the Day` and `Pastry of the Day` —
    placeholders, not food. The drink varies buttermilk-to-squash, a five-fold
    calorie spread, so any single number would be fabricated. The app keeps
    showing "no macro estimate yet" for them, which is the correct outcome.
  - **What broke:** Tavily reported *connected* with all 5 tools registered and
    401'd on every query — `${TAVILY_API_KEY}` isn't expanded anywhere in
    `.mcp.json`, so the server launched with the literal string as its key. A
    green status line only proves a process started. Fixed by launching it
    through bash sourcing the gitignored `.env`. Earlier the same day,
    `${CLAUDE_PROJECT_DIR}` failed the same way in `args` and took the
    filesystem server down with `CONNECTION_CLOSED`.
  - **What the design caught:** the agent surfaced both of those as explicit
    blockers instead of inventing 34 plausible numbers, because it cannot
    declare its own success and its skill forbids unsourced guesses. It also
    caught a bug in my validator — a 40 kcal floor rejected the table's own
    `mixed pickle` (25) and `roasted papad` (35) — and refused to raise 25 to
    45 to clear it, calling it the "nudging numbers to fit" the skill forbids.
    It was right; the gate was wrong. Floor is now 10 kcal with a 20 kcal
    absolute Atwater tolerance, verified against all 154 pre-existing entries.

### 2026-09-18 — Dining halls, per-dish macros, pixel-art UI
- **Time spent:** ~3 hr
- **Tokens used (approx.):** ~430k (incl. a 3-agent research pass)
- **Shipped:** Branch `feat/dining-halls-ui`.
  - **Dining halls:** new `halls.py` models Rasoi (rice-bowl counter), Aahar
    (main line) and the Jain counter (a row filter inside Aahar, not a
    section). Replies now read "Today in Rasoi there's X, in Aahar there's Y,
    and the Jain counter has the same thing." A hall with no data is silently
    absent rather than invented — snacks correctly shows Aahar only.
  - **Per-dish macros** replace the aggregate total. The old total wasn't just
    meaningless for a buffet, it was wrong: the Jain rows duplicate the main
    rows, inflating Monday lunch from 1595 to 1985 kcal. The tray tracker keeps
    its total, because there you tick only your own plate.
  - **Real serving windows** (7:30–10:00 / 11:30–15:00 / 17:00–18:00 /
    19:30–22:00) in one editable config, plus a 10-minute grace rule. Fixes the
    reported bug where 10:15 answered breakfast; it now answers lunch.
  - **UI:** dropped `st.tabs` so `st.chat_input` actually pins to the bottom
    (it only pins with no ancestor block — this was the real cause, not CSS),
    Pixelify Sans + purple gradient theme, pixel-art avatar with idle /
    thinking / answering / error states, the canned greeting replaced by four
    suggestion chips, and the follow-up turned into a real clickable button.
  - **Bugs fixed while in there:** "what's for dinner this evening?" returned
    Snacks (keyword matched by dict order); 23:00 showed this morning's
    breakfast; Sunday's snacks and dinner were discarded by the OCR prompt and
    then reported as non-existent; "N/A" cells surfaced as dishes; a lapsed
    Drive link could serve an HTML page to Gemini as an image; a stale bundled
    menu could be shown silently as this week's; six macro entries were
    unreachable due to trailing spaces.
  - **Startup:** parsed menus are cached on disk keyed by image hash — cold
    start went from 47.8s to 2.4s, and restarts no longer re-roll the ~1-in-5
    malformed-OCR dice.

### 2026-09-16 — Switch ingestion to Gemini OCR, real photo recognition
- **Time spent:** ~1.5 hr
- **Tokens used (approx.):** ~110k
- **Shipped:** Replaced the Excel-based ingestion with real Gemini vision
  OCR, after confirming with the professor that no spreadsheet exists
  upstream of the menu photo (only ever posted as an image in the batch
  WhatsApp group) — OCR-ing the photo directly is the intended approach,
  using the Gemini Edu API. Removed `generate_sample_menu.py`/
  `sample_menu.xlsx` and the pandas/openpyxl dependency; added
  `gemini_client.py` (thin wrapper around `google-generativeai`, `.env`-based
  key handling) and rewrote `menu_data.py` to fetch the real menu photo from
  Drive and OCR/structure it into the same internal shape as before, so
  `query.py`/`time_logic.py`/the chat UI needed no changes. Upgraded the
  Photo Tracker from a manual-only stub to real Gemini-based recognition,
  grounded against the day's actual menu items so it can't hallucinate a
  dish that isn't on offer — still human-reviewable before macros are
  computed. Found and fixed a real ~20% intermittent failure rate in the
  menu OCR call (confirmed via repeated testing, not assumed) by adding a
  retry-with-validation loop. Verified end-to-end against the real Drive
  photo and real API key: menu OCR, time/keyword-based chat queries, and
  the tray-recognition grounding logic (correctly returns nothing on a
  non-food test image) all confirmed working live.

### 2026-09-16 — MVP build (menu chat + photo tracker)
- **Time spent:** ~2 hr
- **Tokens used (approx.):** ~140k
- **Shipped:** First working MVP on branch `mvp-build`. Investigated the
  shared Google Drive folder — found a WhatsApp screenshot of the real mess
  menu (no Excel yet), downloaded and read it at full resolution to get the
  actual grid structure and real dish names. Built: `menu_data.py` (format-driven
  parser for the day-columns/category-rows grid, with Sunday's irregular
  "Brunch" block special-cased), `generate_sample_menu.py` + `sample_menu.xlsx`
  (real dish data, stands in until the mess uploads the actual file to Drive),
  `time_logic.py` (time-of-day → meal inference), `macros.py` (~90-entry
  reference table built from the real dishes seen in the photo), `query.py`
  (intent parsing, reply formatting, macro summary, follow-up prompts), and
  `app.py` (Streamlit chat UI + a photo-tracker tab that accepts a tray photo
  and has the user confirm today's real menu items from a checklist, since no
  vision API key is available yet — clearly marked as a stub, not a fake AI
  claim). Verified end-to-end in a real browser: chat correctly answers
  meal-specific and time-inferred queries with real data, macros, and
  follow-ups; photo tracker renders the real per-day checklist correctly.
  Updated `plan.md`'s data-ingestion/MVP/final-goals sections to reflect the
  professor's constraints (no WhatsApp scraping, Drive Excel instead, webpage
  not full app, photo tracker added to MVP).

### 2026-09-11 — Refined plan
- **Time spent:** ~25 min
- **Tokens used (approx.):** ~20k
- **Shipped:** Expanded `plan.md` with the fuller BatchCaptain.AI vision —
  core agent mechanics, experience design/gamification, high-level technical
  architecture, and a phased development roadmap. MVP scope and final goals
  updated to match; AI-Involvement Level section retained.

### 2026-09-11 — Repo setup
- **Time spent:** ~45 min
- **Tokens used (approx.):** ~35k
- **Shipped:** Initial repo setup — `plan.md` (MVP vs. final scope, AI-Involvement
  Level) and this `BUILD_LOG.md` scaffolding. No implementation code yet.
