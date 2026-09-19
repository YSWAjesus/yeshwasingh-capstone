# Reflection

BatchCaptain.AI has one narrow, fixed **goal**: answer what's being served
right now, and attach honest macros to it. The **model** does the single
thing only a model can — read a photograph of a hand-drawn menu grid into
structured JSON — and deliberately nothing after that, because a model left
free to guess a calorie count will guess one. Its **tools** are what let it
reach past the prompt: the Drive fetch that pulls this week's photo, the
filesystem and search MCP servers the macro-gap-filler agent uses to research
missing dishes, and a validator that rejects the agent's own proposals when
the macros don't reconstruct the calorie figure. **Memory** is split on
purpose — `data/macros.json` is durable memory that survives every restart,
the on-disk parse cache is short-term memory keyed to the image hash, and
session state remembers only the conversation in front of it. The agent loop
that closed the macro gap from 48 dishes to 2 worked precisely because the
agent could not mark its own homework: an external audit script decided when
the goal was met, so a rejected dish stayed missing and the agent had to
change its approach instead of restating its answer. The lesson I'll carry
is that the model was rarely the hard part — the OCR failing about one call
in five was fixable with retries and a structural check, but a deployment
reporting SUCCESS while the live site returned 502 taught me that a green
status is not evidence of a working system.
