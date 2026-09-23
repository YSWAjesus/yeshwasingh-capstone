# Build Log

## Project totals

Running total across every session below, Assessment 1 through deployment.

| | |
|---|---|
| **Sessions logged** | 12 |
| **Total time** | ~23 hr |
| **Total tokens (approx.)** | ~4.5M |
| **Commits** | 31 across 5 branches (the last thirteen straight to `main`) |
| **Span** | 2026-09-11 → 2026-09-23 |

Per-session detail follows, newest first. One entry per commit; date, time
spent, rough tokens used, what shipped.

---

### 2026-09-23 — A day tracker, and the clock that made it possible

- **Time spent:** ~3 hr
- **Tokens used (approx.):** ~1.8M (a 12-agent design workflow accounts for ~1.5M)
- **Approach:** the brief ("track all macros in a day, like Healthify") collides
  head-on with the rule the project is built around — every macro comes from a
  validated record, and off-menu food has none. Rather than pick a resolution
  silently, six agents mapped the subsystems, three designed the feature from
  different angles (smallest-change, Healthify-parity, honesty-first), and three
  judged all three on nutrition honesty, phone usability and blast radius. The
  minimal design won on all three lenses; the honesty-first design's treatment
  of incomplete days was grafted onto it. Every load-bearing claim was then
  re-verified by hand before any code was written.
- **What the mapping found, before the feature — the app was answering the
  wrong meal all day, every day.** Railway runs containers in UTC; the serving
  windows are IST. At 13:00 in the lunch queue the app said breakfast was being
  served; at 20:30 at dinner it said lunch. Nothing crashed, so it had been live
  and unnoticed. Five of seven meal times were wrong. time_logic now owns a
  single clock (BC_TZ, default Asia/Kolkata) and app.py, meal_log and query all
  take their time from it. A missing tzdata is refused rather than silently
  degrading to UTC, because that would restore the bug while looking fine.
- **Shipped:** off-menu food via free text; 36 everyday foods offered alongside
  today's menu, every one already resolving to a sourced record; quantity as
  repetition (the existing schema could always express it — only the UI could
  not); per-user daily targets with no default.
- **The honesty work, which was most of the work:** unknown foods are NAMED not
  counted; a target bar over an incomplete day drops the percentage entirely and
  reads "at least", with a hatched fill, because a percentage asserts a
  completeness the data does not have; the entry form says which foods have a
  number before you commit; and no runtime model call estimates unknown food.
  Five names that were pure naming misses (milk, idli, roti, chapati, dahi) were
  added as aliases through the validator — table size unchanged at 291.
- **Two traps found while building:** `st.expander` renders its children whether
  open or not, so the camera widget mounted on every visit and the browser asked
  for camera permission just for opening the panel; and the pill-hiding CSS keyed
  only on the chat input, so a multiselect dropdown opened underneath the pills.
- **New tests:** `test_clock.py` (pins the seven meal times, asserts the old UTC
  reading fails most of them, greps for modules reading the clock directly),
  `test_intents.py` (12 log questions and 12 menu questions — nothing tested
  routing before, which is how "toms" and "sat" reached production), and
  `check_quick_add.py`.

### 2026-09-23 — Any meal, any day; and surviving the free tier

- **Time spent:** ~2 hr
- **Tokens used (approx.):** ~300k
- **Shipped:**
  - **Meal log verified end to end on the live app.** Injected a tray photo,
    ticked dishes, logged it, then restarted the container: the log came
    back. That closes the "writability inferred, not proven" caveat from the
    previous session — the mounted volume is genuinely durable.
  - **Any meal on any day.** Day abbreviations (`sat`, `thurs`, `weds`), and
    naming a weekday with no meal now returns the whole day rather than
    whichever meal the clock pointed at.
- **What broke:**
  - `whats for dinner sat` answered **today's** dinner. "sat" was
    unrecognised, so the day parser returned None and it silently fell back
    to today — the same failure shape as "toms" the week before. A confident
    answer about the wrong day is indistinguishable from a right one.
  - Building the whole-day view exposed an older bug: day parsing read
    `datetime.now()` directly while `query.answer` worked from an injected
    `now`. Whenever those differed, every named weekday came out shifted by a
    day. Caught only because the date rolled over mid-session and a test
    written against a fixed Tuesday started returning Wednesday.
  - **Ran out of Gemini quota on the live app.** The free tier allows 20
    requests per *day* for this model, not per minute as the first 429
    implied. Verification runs plus cold starts — each able to spend 3 on the
    retry loop — exhausted it, and the deployed app sat on its error message
    for a menu that had been read correctly hours earlier. Two fixes: the
    parse cache moved onto the volume so a deploy no longer throws away a
    good parse and pays for a fresh OCR, and `load_menu` now falls back to
    the committed snapshot when the photo still hashes to the recorded
    sha256. The hash guard is what separates a safety net from a stale-menu
    bug: change the photo and the check fails and the error stands.

### 2026-09-22 — New week, schema-constrained OCR, and a meal log

- **Time spent:** ~2 hr
- **Tokens used (approx.):** ~400k (incl. ~183k in the macro agent)
- **Shipped:**
  - **New week ingested end to end with no code change.** The mess photo was
    replaced in Drive at the same file id; the app re-downloaded it, re-OCR'd
    it and served 21-27 Sep on its own. That is the ingestion design working
    as intended.
  - **Macro gap closed, 129 -> 4.** A near-total menu changeover left most of
    Tuesday's Rasoi line with no estimate. The gap-filler agent converged
    129 -> 101 -> 62 -> 4 and grew the table 188 -> 291. Re-validated every
    record independently afterwards: 0 of 291 failed the sanity gate. The 4
    left are placeholders ("Beverage of the Day") plus one genuine either/or
    cell, `Phulka/ Puran Poli` — ~90 kcal of dry wholewheat against a ~300
    kcal stuffed sweet flatbread, where one number would be wrong for
    whichever the student takes.
  - **Response schema on the Gemini calls.** The JSON shape had been
    described in the prompt and nowhere else, which made it a request rather
    than a rule. Day and section names are now enums enforced by the API.
    Confirmed the enum binds by asking for "any day names you like, e.g.
    Friday" against a Monday/Tuesday enum and getting only Monday/Tuesday.
  - **Meal log.** Logging a tray now survives a refresh: per-person
    JSON-lines file, identity a short opaque id in the URL rather than an
    account, day and Monday-start week totals. Stored on a mounted Railway
    volume, because a container's own disk is wiped on every deploy.
- **What broke / what I was careful about:**
  - A response schema can only constrain fixed field names, and the menu's
    category labels change weekly. The JSON had to become arrays so the
    category moved from a KEY the schema cannot describe into a VALUE it can
    require. Conversion back to the internal dict shape happens in code, so
    no downstream module changed.
  - The schema does **not** fix partial reads — a one-day response is
    entirely valid JSON. Three parses gave 7/7 days each, which is not
    enough runs to claim the ~1-in-5 rate moved. The >= 5 days gate still
    does that job.
  - "What did I eat today" and "what is there to eat today" share nearly
    every word and have completely different answers, so log questions are
    routed away from `query.answer` before it can reply with the mess menu.
  - The week strip is hand-rolled HTML on a CSS grid rather than
    `st.columns`, which restacks on narrow screens. Checked at 375px.

### 2026-09-18 — Railway deployment (live)

- **Time spent:** ~1 hr
- **Tokens used (approx.):** ~120k
- **Shipped:** BatchCaptain.AI is live at
  https://yeshwasingh-capstone-production.up.railway.app — deployed from
  `main` on Railway, verified on the real URL rather than locally: the menu
  photo OCRs on the server, "what's for dinner" returns Friday's Aahar and
  Jain counter lines with per-dish macros, and the layout holds at 375px.
- **What broke — two things, one hiding behind the other:**
  - The deployed app kept answering `API_KEY_INVALID`. The key itself was
    fine (verified against the Gemini endpoint, HTTP 200). The cause was the
    Railway RAW variables editor, which takes `NAME=value` lines — only the
    bare key had been pasted, so `GEMINI_API_KEY` didn't exist as a variable
    at all. Same mistake as the local `.env` earlier in the project.
  - Fixing that exposed a second fault. A rebuild came back with
    `startCommand` unset in the service manifest, so Railpack fell back to
    its default `python app.py`. Running a Streamlit script under bare
    Python executes it and exits — nothing binds to `$PORT` — so the site
    502'd while the build still reported SUCCESS. A green build is not a
    running app. Fixed with a `Procfile`, which Railpack always reads, so
    the entrypoint survives a rebuild; `railway.json` keeps the same command.
  - Worth recording: pushing the fix to GitHub did **not** trigger a Railway
    build on its own. The deploy had to be run explicitly.

### 2026-09-18 — Figma artwork, in-bar CTAs, mobile, deploy prep
- **Time spent:** ~2 hr 20 min
- **Tokens used (approx.):** ~300k
- **Shipped:** The landing page now renders `hero_composed.png` — the captain
  with both speech bubbles positioned in Figma — as a single exported image,
  which deleted every line of bubble-placement CSS. Trying to rebuild that
  composition in CSS was the wrong call; the artwork was always the answer.
  Perch poses use tight crops so the image's bottom edge is her feet and
  planting her on the prompt bar is exact.
  - Follow-up CTAs moved **into** the prompt bar as pills. Streamlit's chat
    input is sealed, so these are real buttons lifted over it — visually
    inside, structurally layered. The second one opens the tray tracker;
    the mock's "Want to know macros?" had no honest behaviour behind it,
    since macros already show per dish.
  - **Mobile**, because photographing a tray means a phone. Bar spans the
    screen, hero scales, pills stay inline and fit; the captain stands down
    when pills are up, as a 375px bar can't hold both.
  - Deploy prep: pinned `requirements.txt`, `.python-version`, `railway.json`
    with an explicit Streamlit start command, and a README rewritten so a
    stranger can clone and run it.
  - **What broke:** the CTA pills rendered see-through. The alpha wasn't the
    cause — a stale duplicate `.stButton` rule sat *after* the new one and
    won on source order, resetting the background. Also, Streamlit stacks
    columns on narrow screens, which pushed a pill clean out of the bar on
    mobile until the row was forced inline.

### 2026-09-18 — UI rebuilt to the Figma mock; day queries
- **Time spent:** ~3 hr
- **Tokens used (approx.):** ~610k (includes two parallel research passes)
- **Shipped:** The landing page is the hero it was designed as — captain large
  and centred, value proposition in two pixel speech bubbles either side —
  and the `_promptbar` sprites finally sit *on* the prompt bar, which is what
  that filename always meant. Body text moved to Inter (Pixelify Sans is now
  display only; it cost too much readability on long menu replies). Removed
  the slab behind the prompt bar so the page gradient runs clean, flipped the
  gradient to dark-top/purple-bottom, switched `layout="centered"` to `"wide"`
  (the default caps the column at ~704px and was pinching the bar), and gave
  the insertion point its blinking lilac caret. Replies now name the dish
  alone rather than reading the mess's own grid labels back at you.
  - **What broke:** "what is there for dinner tommorow" answered *today's*
    dinner. The day matcher listed exact spellings and that misspelling wasn't
    among them, so it silently fell through. Fixing it surfaced a second bug
    in the same function — the "day after tomorrow" branch prefixed an
    un-grouped regex alternation, so "dinner tmrw" returned offset 2. Both
    have cases now.
  - Also: the speech bubbles were siblings of the figure rather than children,
    so their absolute positioning resolved against the page and pinned them
    419px from her head instead of 26px.

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
