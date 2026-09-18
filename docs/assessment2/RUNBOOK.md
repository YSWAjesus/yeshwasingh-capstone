# Assessment 2 — how to run it

The pipeline has to run in a Claude Code session where the MCP servers are
connected, because the proof this assignment asks for is a transcript
containing real `mcp__*` tool calls. Follow these in order.

## 1. Get a Tavily API key (free, ~2 minutes)

1. Go to <https://www.tavily.com> and sign up.
2. Copy the API key from the dashboard (starts with `tvly-`).
3. Add it to `.env` alongside the Gemini key:
   ```
   TAVILY_API_KEY=tvly-...
   ```

`.env` is gitignored, so neither key reaches GitHub. Both the Python app and
the MCP server read from it — see the note at the bottom for why `.mcp.json`
sources the file rather than referencing `${TAVILY_API_KEY}`.

## 2. Restart Claude Code so it picks up `.mcp.json`

Quit and reopen Claude Code in this folder. It will ask whether to trust the
project's MCP servers — approve them.

Then check they're live:

```
/mcp
```

Both `filesystem` and `tavily` must show as connected. If they don't, nothing
below will produce the evidence the assignment wants.

## 3. Do a dry check of the gap

```bash
source .venv/bin/activate
python3 tools/snapshot_menu.py      # downloads this week's real photo, OCRs it
python3 tools/menu_macro_audit.py   # how many dishes have no macros
```

Note the starting number — it is the first rung of the pass ladder.

## 4. Run the workflow (this is the bit to screen-record)

In Claude Code:

```
/refresh-macros
```

It will snapshot the menu, hand off to the `macro-gap-filler` subagent, and
loop until the audit comes back empty or it stalls. Record your screen while
this runs — the passes scrolling by are the clearest evidence of a real
multi-step loop.

To capture a machine-readable transcript at the same time, run it headless
instead:

```bash
mkdir -p docs/assessment2
claude -p "/refresh-macros" --output-format stream-json --verbose \
  2>&1 | tee docs/assessment2/run.jsonl
```

Then count the MCP calls for the PR description:

```bash
grep -c 'mcp__' docs/assessment2/run.jsonl
```

## 5. Verify what a user actually sees

```bash
python3 tools/menu_macro_audit.py          # should be 0 missing, or a short honest list
python3 tools/check_app_replies.py         # asks every day/meal combination
streamlit run app.py                       # then ask "what's for lunch"
```

Take before/after screenshots of the same question in the app. The "before" is
already captured in this repo's history if you forget — but a fresh pair is
better.

## 6. What goes in the PR description

- The pass ladder (`pass 1: 48 missing → pass 2: ... → 0`)
- `grep -c 'mcp__'` count, as a checkable claim
- Before/after screenshots
- What broke on the first try, and what you changed

## Expected honest leftovers

Some menu cells aren't dishes — `Beverage of the Day`, `Pastry of the Day`.
The skill is instructed to return `unresolved` for these rather than invent
numbers. Leaving them visibly unresolved is the correct outcome and worth
saying so in the PR.

## Note for anyone cloning this repo

`.mcp.json` points the filesystem server at an absolute path:

```
/Users/jesussingh/Downloads/yeshwasingh-capstone/data
```

Change that one line to your own checkout's `data/` directory, and the `.env`
path in the tavily entry too. They are absolute on purpose: `${VAR}` is not
expanded anywhere in `.mcp.json`, and a relative path depends on whatever
working directory Claude Code launches the server with. Absolute paths remove
both failure modes at once.

## Why `.mcp.json` sources `.env` instead of using `${TAVILY_API_KEY}`

`${VAR}` inside `.mcp.json` is **not** expanded — not in `args`, and not in
`env` either. The trap is that the tavily server still *starts* and still
registers its 5 tools with the literal string as its key, so `/mcp` shows it
**connected** and everything looks fine. It then returns
`Unauthorized: missing or invalid API key` on every single query.

Connected is not the same as authenticated. If a server is green but every
call 401s, check that the key actually reached the process:

```bash
bash -c 'set -a; . ./.env; set +a; echo "${TAVILY_API_KEY:0:9}"'
```

The server is therefore launched through `bash -c 'set -a; . .env; set +a; exec npx ...'`,
which sources the gitignored `.env` so the key never enters a committed file.
