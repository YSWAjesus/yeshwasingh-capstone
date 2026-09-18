---
name: refresh-macros
description: End-to-end weekly refresh — re-read the mess menu photo from Drive, find dishes with no macro data, research and fill them, then verify the app reports no missing estimates. Run this after uploading a new week's menu photo.
disable-model-invocation: true
---

# Weekly macro refresh

The whole pipeline, on real input, in one command. This spends Gemini and
search calls and rewrites `data/macros.json`, so it is user-triggered only.

## Step 1 — Snapshot this week's real menu

```bash
source .venv/bin/activate && python3 tools/snapshot_menu.py
```

Downloads the menu photo from the shared Drive folder and OCRs it into
`data/menu_snapshot.json`. Check `image_source` in the output:

- `drive` — a live download, which is what we want
- `cache` / `sample` — Drive was unreachable and this is an older photo. **Stop
  and say so.** Continuing would research last month's menu while claiming it
  was this week's.

## Step 2 — Measure the gap before

```bash
python3 tools/menu_macro_audit.py
```

Record the starting number — it's the first rung of the pass ladder and the
headline evidence that the loop did real work.

## Step 3 — Run the agent loop

Delegate to the **macro-gap-filler** subagent. It owns the
perceive → reason → act → observe loop and will keep going until the audit
comes back empty, it stalls, or it hits its pass cap.

## Step 4 — Verify against what a user would see

```bash
python3 tools/menu_macro_audit.py --json
python3 tools/check_app_replies.py
```

`check_app_replies.py` asks the app every day/meal combination a student could
and fails if any reply still says "no macro estimate yet". A full table with a
failing acceptance test means the names in the table don't match the names on
the menu — an alias problem, not a data problem.

## Step 5 — Log it

Append a `BUILD_LOG.md` entry, newest at the top, matching the existing format:
date, time spent, approximate tokens, and what shipped. Include the pass ladder
and the before/after gap counts.

Leave committing to a human — every diff gets read before it lands.
