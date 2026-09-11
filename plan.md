# BatchCaptain.AI — Capstone Plan

## Problem
Our campus mess/canteen menu is only announced in one centralized WhatsApp
announcements channel, posted by our batch captains. Every time someone wants
to know what's being served, they have to dig through that WhatsApp thread —
or just ask the batch captains directly, who frequently don't remember either.
It's a small, everyday annoyance, but a genuinely useful one to fix.

## Solution
BatchCaptain.AI is a conversational agent students can query in plain language
(e.g. "what's there to eat?"). It infers the relevant meal from the current
time of day, replies with that meal's menu plus macros (calories/protein/carbs/
fat), and offers a natural follow-up — e.g. after answering lunch, asking
"want to know what's for dinner too?".

## MVP scope (required for this course)
- A day's menu loaded into a simple structured store (e.g. JSON), entered
  manually or pasted from the WhatsApp announcement text — no live WhatsApp
  integration required for MVP.
- A small macros reference table per dish (approximate values are fine).
- Natural-language query handling for at least: "what's for breakfast/lunch/
  dinner" and "what's there to eat" (time-of-day-aware default).
- A working chat interface (CLI is sufficient) a real user can try end to end.
- At least one working follow-up flow (answer lunch → offer dinner).

## Final / stretch goals (not required for MVP grading)
- Automated ingestion straight from the WhatsApp announcements channel
  (WhatsApp Business API, or a forwarded-message parser) instead of manual entry.
- Menu history so past-date queries work ("what was lunch last Tuesday?").
- Running macro totals for a user across a day/week.
- Deploy as an actual WhatsApp/Telegram bot so batch captains post once and
  it's queryable directly in chat, no separate app needed.
- Dietary-preference filtering (veg / non-veg / allergens).

## AI-Involvement Level: AI-led with review

I'm aiming for **AI-led with review**: Claude will generate most of the actual
implementation (menu parsing, the query/NLU handling, the chat interface) from
my direction, and my role is to define scope, review generated code for
correctness, test it against real menu data from our WhatsApp channel, and make
the product calls on what belongs in MVP vs. later. I'm choosing this level
because the project's value is in solving a real, specific annoyance quickly and
well — not in the mechanics of writing a menu parser by hand — so I'd rather
spend my own effort on direction, review, and validating it actually works for
my batch, and let AI carry the bulk of implementation.
