# Capstone presentation — prep

Marking, from the brief: problem framing 15 · **live demo 25** · ai-involvement
defended 15 · **live q&a 20** · process trail 15 · effort vs shipped 10.

The demo and the Q&A are 45 of 100. The slides are the smaller half of this.

---

## Live demo script

Run it on **your phone**, on the deployed URL, not on localhost. Tracking a
tray on a phone is the whole point, and a laptop demo throws that away.

**Before you go in:** open the app once, an hour ahead. A cold container
re-OCRs the menu and that takes 40–90 seconds. Warm, it is instant.

https://yeshwasingh-capstone-production.up.railway.app

| # | Type / tap | What to say while it loads |
|---|---|---|
| 1 | `what's for dinner` | "No menu file exists. This is read off a photograph." |
| 2 | — | Point at the three halls: Rasoi, Aahar, the Jain counter. "The photo is one flat grid. Knowing which counter serves which row is campus knowledge layered on top." |
| 3 | `what's on friday` | "A named weekday with no meal means the whole day. 'Tomorrow' deliberately doesn't — it keeps the sense of the time of day." |
| 4 | Tap **Track what I ate** | "No photo needed. Photographing a tray makes sense; photographing a banana doesn't." |
| 5 | Type `protein shake` | **This is the slide-worthy moment.** It says *no macro estimate yet* before you commit. "It won't guess." |
| 6 | Add `banana`, set servings to 3 | "Quantity is the same name repeated — the schema could always express it, the UI couldn't." |
| 7 | **Log this** | Day view opens. |
| 8 | — | Point at the named gap and the target bar: "The percentage is gone and it says *at least*, because one food has no record. A percentage would claim a completeness the data doesn't have." |

If the network dies: the fallback serves the committed parse of the same
photo, hash-checked. Say that out loud — it is a feature, not a save.

---

## Q&A — the questions that are actually coming

**"Isn't this just a wrapper around Gemini?"**
The model does one job: photograph → structured JSON. Everything after it is
deterministic code — which hall, which meal, which macros, which day. The
interesting engineering is the refusal: 291 macro records each with a source
and a confidence band, and a validator that rejects numbers even when an agent
argues for them. A wrapper would have asked the model for calories.

**"Where do the macro numbers come from?"**
An offline pipeline, never at request time. A Skill defines how one dish is
researched; a subagent loops audit → research → propose → merge → re-audit; and
`tools/macros_store.py` re-applies bounds and an Atwater check before anything
lands. 34 records are high-confidence with a retrieved URL, 255 are medium
ingredient reconstructions that say so in their own `source` field, 2 are low.

**"How do you know the agent didn't just make them up?"**
It cannot mark its own homework. `tools/menu_macro_audit.py` is the only thing
allowed to say the gap is closed, and the agent has no write access to the live
table. In the last run it closed 129 missing dishes to 4 and **zero** records
failed validation. It also refused to nudge a number to pass my own bad
threshold — that bug was mine, not its.

**"What are the 4 that are missing?"**
"Beverage of the Day", "Pastry of the Day", "One Campus Festive Menu" — those
are placeholders, not dishes, and will never resolve. The fourth is
`Phulka/ Puran Poli`: one menu cell holding two different foods, ~90 kcal of
dry wholewheat against a ~300 kcal ghee-and-jaggery sweet. One number would be
wrong for whichever you actually took, and the average is a dish nobody eats.

**"What's the hardest bug you hit?"**
The clock. Railway runs UTC, the serving windows are IST, so at 13:00 in the
lunch queue the app said breakfast was being served and at 20:30 it said lunch.
Nothing crashed, so it was live and unnoticed. Five of seven meal times were
wrong. It is the shape I'd now look for first: **a confident answer about the
wrong thing looks exactly like a right one.**

**"What would you do differently?"**
Streamlit is the ceiling. Every UI fight — a sealed chat input, class names
that are build hashes, columns that restack on a phone — was the framework, not
the model. The Python logic is UI-agnostic and would move to a real frontend
unchanged.

**"How much of this did you write?"**
Effectively none of the code by hand; the involvement level is stated in
`plan.md` and the whole trail is in `BUILD_LOG.md` and git. What I did was
decide what the app is allowed to claim. The no-invented-numbers rule, the
hall model, refusing a default calorie target — those are judgement calls, and
they are what the code is shaped around.

---

## Numbers, all verifiable in the repo

| | |
|---|---|
| Sessions logged | 13 (11–24 Sept) |
| Time | ~24 hours |
| Tokens | ~5.0M |
| Commits / branches / PRs | 44 / 5 / 5 |
| Macro records | 291 (34 high, 255 medium, 2 low) |
| Menu coverage | 206 of 210 dishes |
| Agent run | 129 gaps → 4, zero validation failures |
| Test suites | 6 |

---

## If the demo dies

1. **Slow first load** — cold container re-OCRing. Keep talking; it resolves.
2. **Quota exhausted** (free tier is 20 requests/day) — it serves the committed
   parse of the same photo, hash-guarded. Demo continues normally.
3. **Railway trial expired** — this is the one that actually ends the demo.
   **Check the billing page before you go in.** Fallback: run it locally from
   the repo and say why.
