# BatchCaptain.AI

Ask what's for lunch. Track what you actually ate.

**Live:** https://yeshwasingh-capstone-production.up.railway.app — open it on a phone; photographing your tray is half the point.

Build history and honest failure notes: [BUILD_LOG.md](BUILD_LOG.md). Closing reflection: [REFLECTION.md](REFLECTION.md).

Campus mess menus at FLAME are only ever published as a **photo** posted to a
WhatsApp announcements channel by the batch captains — who, when you ask them
what's for dinner, usually don't remember either. There is no spreadsheet
anywhere upstream of that image.

BatchCaptain.AI reads that photo with Gemini, answers questions about it in
plain language, and attaches macros to every dish. It knows which dining hall
serves what — Rasoi's rice-bowl counter, Aahar's main line, and the Jain
counter inside Aahar — and it never invents a nutrition number it doesn't have.

---

## Run it locally

You need Python 3.10+ (3.12 recommended) and a free Gemini API key.

```bash
git clone https://github.com/YSWAjesus/yeshwasingh-capstone.git
cd yeshwasingh-capstone

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then put your keys in it
streamlit run app.py
```

Opens at <http://localhost:8501>.

### Keys

| Key | Needed for | Where to get it |
|---|---|---|
| `GEMINI_API_KEY` | Reading the menu photo, and recognising your tray | <https://aistudio.google.com/apikey> |
| `TAVILY_API_KEY` | Only the macro-research agent (below) — the app runs fine without it | <https://www.tavily.com> |

`.env` is gitignored. Neither key ever reaches the repo.

### Using it on your phone

Tray photos are the point, so it's built to work on a phone. With the app
running on your laptop and both devices on the same WiFi:

```bash
streamlit run app.py --server.address 0.0.0.0
```

then open `http://<your-laptop-ip>:8501` on the phone.

One caveat: browsers only allow the in-page camera on `localhost` or over
HTTPS, so on a plain-http LAN address the camera widget is blocked. Use the
**+** button instead — on iOS and Android it opens the native "Take Photo"
picker. On the deployed HTTPS URL, both work.

---

## Where the menu comes from

1. Someone uploads the week's menu photo to a shared Google Drive folder.
2. The app downloads it and Gemini OCRs it into structured JSON — days,
   meal sections, dishes.
3. That parse is cached on disk keyed by a hash of the image, so a restart
   doesn't re-run a 15–60 second OCR on an unchanged photo.

### Asking about it

Any meal on any day of the uploaded week:

- `what's for dinner` — the meal you can still go and eat, from the clock
- `lunch tomorrow`, `toms lunch`, `dinner tmrw` — relative days, spelling-tolerant
- `thursday dinner`, `fri lunch`, `whats for dinner sat` — any weekday, abbreviated or not
- `what's on Thursday`, `show me friday` — a named weekday with no meal returns the
  **whole day**, every meal. "Tomorrow" deliberately does not: it keeps the sense of
  the current time of day, so at lunchtime it still means tomorrow's lunch.

### Each new week

The app re-downloads the photo every 30 minutes (`ttl=1800` on the cached
loader), and the parse cache is keyed on the image bytes — so a changed photo
re-OCRs by itself. What you do depends on how the new menu is posted:

- **Same Drive file, new version** (in Drive: right-click the file →
  *Manage versions* → *Upload new version*): nothing to do. The new week
  appears within half an hour.
- **A new Drive file**: copy its ID out of the share link — the part between
  `/d/` and `/view` — and set `DRIVE_FILE_ID` to it. It is a **Railway
  variable**, so change it in the dashboard; no code edit, no redeploy of the
  app itself. `menu_data.py` only holds the fallback default.

Then check the new week's dishes for macro gaps, since a new menu usually
brings a few:

    python3 tools/menu_macro_audit.py --json

Anything it lists is missing. Close the gap with the agent
(`macro-gap-filler`, below), then commit the updated `data/macros.json` and
redeploy. Until you do, those dishes simply show "no macro estimate yet" —
the app stays correct, just less complete.

The OCR is not always right first time — roughly one call in four or five comes
back with a partial grid. `menu_data.parse_menu_image` retries, and rejects any
reading covering fewer than five days rather than presenting half a week as the
whole thing. `tools/test_failure_modes.py` drives that failure deliberately and
asserts the app degrades cleanly.

---

## The macro table, and the agent that fills it

Macros live in `data/macros.json`, matched to dishes by name. When a dish isn't
in the table the app says so — it does not guess.

Keeping that table current is a real recurring chore, so it's automated as a
Claude Code pipeline:

| Piece | File | Job |
|---|---|---|
| Skill | `.claude/skills/nutrition-lookup/SKILL.md` | Macros for **one** dish, to a fixed schema, with serving conventions and a sanity gate |
| Agent | `.claude/agents/macro-gap-filler.md` | Loops: find gaps → research → validate → re-check |
| MCP | `.mcp.json` | `filesystem` (sandboxed to `data/`) and `tavily` (search) |
| Workflow | `.claude/skills/refresh-macros/SKILL.md` | The whole thing end to end |

Two deliberate constraints make it trustworthy:

- **The agent cannot declare its own success.** `tools/menu_macro_audit.py`
  decides when the gap is closed. A model grading its own homework turns the
  "observe" step into self-assessment.
- **The agent cannot write the live table.** It has no `Write` or `Edit` tool;
  it proposes records through the filesystem MCP and
  `tools/macros_store.py` re-applies the sanity gate before anything lands.

Run it with `/refresh-macros` in Claude Code. See
[`docs/assessment2/RUNBOOK.md`](docs/assessment2/RUNBOOK.md).

> **If you cloned this:** `.mcp.json` points the filesystem server at an
> absolute path on the original author's machine. Change it to your own
> checkout's `data/` directory. It is absolute because `${VAR}` is not
> expanded anywhere in `.mcp.json` and a relative path depends on the working
> directory Claude Code happens to launch the server with.

---

## Tracking a day

Log anything you ate, not just what the mess served. Tap **Track what I ate**
(no photo needed — photographing a tray makes sense, photographing a banana
does not), pick from today's menu or the everyday-foods list, or type any food
at all. Set servings per item. Optionally set a daily target and watch the day
against it.

**Where the numbers come from, and what happens when there are none.** Every
macro in this app comes from a validated record with a source and a confidence
band — nothing is estimated at request time, and no model is asked to guess a
calorie count. So a food with no record is logged and *disclosed*, never
invented:

- the entry form says which items have a number before you commit
  (`banana — 105 kcal each` against `protein shake — no macro estimate yet`)
- the day view names the foods it has no record for, rather than counting them
- a target bar over such a day **drops the percentage entirely**, reads
  `315 / 2030kcal, at least`, and hatches the fill. A percentage would assert a
  completeness the data does not have.

There is no default daily target. Setting one is the student's call; a 2000
kcal default would be the app inventing a number about their body.

`pantry.py` lists the everyday foods offered as taps. It creates no nutrition
data — every name already resolves to an existing record, and
`tools/check_quick_add.py` fails if one stops.

---

## The meal log

Photograph your tray, tick what you actually took, and log it. The app keeps
a running day total and a Monday-to-Sunday week, matching the mess's own
menu week.

There are no accounts. A short opaque id lives in the URL — bookmark the page
and your log comes back; open it in a private window and you are a new
person. Nothing identifying is stored.

Ask for it in words (`what did I eat today`, `my log`, `calories so far`) or
open it from the tray panel.

Storage is `BC_LOG_DIR`, one JSON-lines file per person. **Set it to a
mounted volume in any real deployment** — a container's own filesystem is
wiped on every deploy. With no volume the app says the log is temporary
rather than implying otherwise. On Railway:

```bash
railway volume add --mount-path /data
railway variables --set "BC_LOG_DIR=/data/logs"
railway variables --set "BC_CACHE_DIR=/data/cache"
```

**`BC_TZ` matters as much.** It defaults to `Asia/Kolkata` and decides which
meal the app thinks is being served. Railway containers run UTC; before this
was threaded through, the deployed app told a student at 13:00 in the lunch
queue that breakfast was on, and at 20:30 at dinner that it was lunch — every
day, silently. `tzdata` is pinned for it, and a zone that cannot be resolved
raises rather than falling back to UTC.

`BC_CACHE_DIR` matters more than it looks. The menu photo and its parse are
cached there; on the container's own disk they are wiped by every deploy, so
each deploy costs a fresh 40-90 second OCR. The free tier allows **20
requests per day** for this model, and the parse retries up to 3 times, so a
few deploys can exhaust a day's quota. On the volume, a deploy costs nothing.

As a second line of defence, `load_menu` falls back to the committed
`data/menu_snapshot.json` when Gemini is unavailable — but only if the photo
still hashes to `data/menu_snapshot.sha256`. Change the photo and the
fallback correctly refuses: a wrong menu is worse than no menu.

---

## Tools

```bash
python3 tools/test_clock.py           # the app answers the meal you're standing in front of
python3 tools/test_intents.py         # menu questions and log questions go different places
python3 tools/check_quick_add.py      # every quick-add food still resolves
python3 tools/snapshot_menu.py        # fetch + OCR this week's photo
python3 tools/menu_macro_audit.py     # which dishes have no macros
python3 tools/check_app_replies.py    # ask every day/meal, report gaps
python3 tools/test_failure_modes.py   # prove bad AI output degrades cleanly
python3 tools/prepare_sprites.py      # re-cut artwork after a Figma export
```

`check_app_replies.py` exits non-zero while any dish lacks macros. Two always
will: `Beverage of the Day` and `Pastry of the Day` are placeholders, not food
— the drink ranges from buttermilk to squash. Refusing to invent a number for
them is the intended behaviour.

---

## Project docs

- [`plan.md`](plan.md) — scope, MVP vs final goals, AI-involvement level
- [`BUILD_LOG.md`](BUILD_LOG.md) — every session: time, tokens, what shipped
- [`docs/assessment2/RUNBOOK.md`](docs/assessment2/RUNBOOK.md) — running the agent pipeline
