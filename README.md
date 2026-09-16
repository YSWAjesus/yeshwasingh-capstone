# BatchCaptain.AI

A conversational agent for campus mess menus — ask what's for lunch, get the
menu plus a rough macro estimate, and track what's actually on your tray with
a photo. See [`plan.md`](plan.md) for the full project plan (MVP vs. final
goals, AI-Involvement Level) and [`BUILD_LOG.md`](BUILD_LOG.md) for the
build history.

## Running it (no coding needed)

1. Make sure you have Python 3.9+ installed (check with `python3 --version`
   in Terminal).
2. In this folder, create a virtual environment and install dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   streamlit run app.py
   ```
   This opens a browser tab with the app. Leave the terminal window open —
   closing it stops the app.

Next time, you only need step 3 (after running `source .venv/bin/activate`
once per terminal session).

## What it does right now (MVP)

- **Chat tab:** ask "what's for lunch", "what's there to eat", etc. — it
  infers the meal from the current time if you don't say one, replies with
  today's real menu items, a rough macro estimate, and offers a follow-up
  ("want to know what's for dinner too?").
- **Photo Tracker tab:** take/upload a photo of your tray, then manually tick
  off which of today's actual menu items are on it — macros get summed the
  same way as in chat. Auto-detecting food straight from the photo needs a
  vision API key that isn't wired in yet (final-goal item, see `plan.md`).

## Menu data

The menu is read from `sample_menu.xlsx` (a stand-in built from a real photo
of the mess's WhatsApp menu — see `generate_sample_menu.py`). Once the mess
uploads the real Excel file to Google Drive and shares it as "Anyone with
the link", set the `DRIVE_FILE_ID` environment variable to that file's ID
and the app will fetch and parse it directly — no other code changes needed
as long as the sheet keeps the same day-columns / category-rows grid shape.
