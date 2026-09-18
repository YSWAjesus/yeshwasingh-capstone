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
3. Get a Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   (sign in with your FLAME account), then open the `.env` file in this
   folder and replace the placeholder with your real key:
   ```
   GEMINI_API_KEY=your-real-key-here
   ```
   `.env` is gitignored — it never gets committed or pushed.
4. Run the app:
   ```
   streamlit run app.py
   ```
   This opens a browser tab with the app. Leave the terminal window open —
   closing it stops the app.

Next time, you only need steps 2 (activate) and 4 (run) — `.env` and
installed packages stick around.

## What it does right now (MVP)

- **Chat tab:** ask "what's for lunch", "what's there to eat", etc. — it
  infers the meal from the current time if you don't say one, replies with
  today's real menu items, a rough macro estimate, and offers a follow-up
  ("want to know what's for dinner too?").
- **Photo Tracker tab:** take/upload a photo of your tray — Gemini
  pre-recognizes which of today's real menu items it can see (grounded
  against the actual menu, so it can never invent a dish that isn't on
  offer), you review/adjust the checklist, and macros get summed the same
  way as in chat.

## Menu data

There's no spreadsheet behind the mess menu — it only ever exists as the
photo posted in the batch WhatsApp group, and WhatsApp itself blocks
automated access, so the app can't pull it from there directly. Instead:

1. Each week, re-upload that week's menu photo to the shared Google Drive
   folder (share it as "Anyone with the link" → Viewer).
2. Update `DRIVE_FILE_ID` in `menu_data.py` (or set it as an environment
   variable) to that new file's ID.
3. The app fetches the photo and has Gemini OCR/structure it into the menu
   data automatically — no other code changes needed.

`sample_menu.jpg` (the real photo from the Drive folder at the time this was
built) is bundled as a fallback if the Drive fetch ever fails.

Note: menu OCR occasionally needs a retry (Gemini sometimes returns a
partial/malformed reading on the first try) — `menu_data.py` already retries
up to 3 times before giving up, so this is handled automatically.
