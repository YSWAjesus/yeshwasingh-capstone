# BatchCaptain.AI

Ask what's for lunch. Track what you actually ate.

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

To point it at a new week, put the new photo in Drive (shared as "anyone with
the link") and set `DRIVE_FILE_ID` in `menu_data.py` to the new file's ID.

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

## Tools

```bash
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
