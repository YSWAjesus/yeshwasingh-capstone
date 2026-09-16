# BatchCaptain.AI — Capstone Plan

## 1. Problem Statement
Campus mess and canteen menus at FLAME University are announced through a
single, centralized WhatsApp channel managed by batch captains. Finding out
what's for the next meal means digging through chat history or asking the
captains directly — who often don't know either. The information is manual,
buried in text, and completely disconnected from the nutritional data
students need to align meals with their training/diet routines.

## 2. Solution Overview
BatchCaptain.AI is a gamified, UI-centric conversational agent that acts as a
virtual, interactive proxy for the real batch captains. Students query it in
natural language ("what's there to eat?"); the agent infers the relevant meal
from time of day, retrieves the menu, calculates macros, and keeps the
conversation going with natural follow-ups — all through a pixel-art
companion interface rather than a plain text bot.

## 3. Core Agent Mechanics & Logic
- **Time-aware intent parsing:** local clock infers meal context automatically
  (e.g. querying at 2 PM defaults to lunch).
  - Time blocks: Breakfast 07:00–10:30, Lunch 12:00–14:30, Snacks 16:00–18:00,
    Dinner 19:30–22:00.
- **Macro-nutrient enrichment:** menu items are cross-referenced against a
  nutrition reference table; responses surface protein, carbs, fats, and
  calories.
- **Predictive conversational routing:** responses end with a contextual
  follow-up instead of a dead end — e.g. "want me to load up the dinner menu
  too?" or "looking for the vegetarian alternatives?"

## 4. Experience Design & Gamification
- **The avatar:** an 8-/16-bit pixel-art character styled after the real batch
  captain — the visual feedback loop for the agent's state.
- **Animation states:** Idle (breathing/checking a phone), Thinking/Fetching
  (flipping papers), Serving (handing over/uncovering a tray), Error/Unknown
  (shrugging).
- **Macro visuals:** retro-styled progress bars/stat screens for protein,
  carbs, and fats.
- **Gamification:** daily query streaks, unlockable avatar accessories (hats,
  jackets) for consistent use, and easter-egg queries ("what's the worst
  thing on the menu?") that trigger unique responses/animations.

## 5. Technical Architecture (high-level)
- **Data ingestion layer:** there is no spreadsheet anywhere upstream — the
  mess menu only ever exists as the photo posted to the batch WhatsApp
  group, and WhatsApp itself blocks automated/agentic access. So the app
  fetches that photo from a shared Google Drive folder (student manually
  re-uploads the week's photo there) and OCRs/structures it directly with
  Gemini's vision + JSON output. No macro data exists in the photo itself —
  macros come from a separate reference table, matched by dish name.
- **AI & logic layer:** rule-based intent parsing (keyword-match meal names,
  else infer from time of day); a rules layer combines parsed intent +
  current timestamp to fetch the right section of the OCR'd menu. Gemini is
  also used, grounded against the day's real menu items, to pre-recognize
  what's in a tray photo for the macro tracker.
- **Frontend layer:** for this stage, a webpage (Streamlit) — not the full
  app that's the final vision. Includes the chat UI and the photo-based tray
  tracker (see MVP scope below).

## 6. MVP Scope (required for this course)
- Data ingestion: the week's menu photo (manually re-uploaded to Drive by
  the student each week) fetched and OCR'd/structured via Gemini vision —
  no spreadsheet, no live WhatsApp integration, no manual retyping.
- Time-inference logic: rule-based mapping from local time → meal
  (breakfast/lunch/snacks/dinner).
- Conversational interface: a basic web chat UI (Streamlit) for
  natural-language queries, replying with real menu items + a macro estimate.
- Macro estimation: a hand-built reference table matched by dish name,
  flagging anything not in the table rather than inventing a number.
- **Photo-based macro tracker** (added per professor's feedback): take/upload
  a photo of your tray; Gemini pre-recognizes which of today's actual menu
  items are visible (grounded against the real menu, so it can't invent a
  dish that isn't on offer), you review/adjust the checklist, then macros
  are summed the same way as in chat.
- Static visuals: a static pixel-art avatar in the UI — animations are a
  final-goal item, not MVP.

## 7. Final / Stretch Goals (not required for MVP grading)
- Automate the weekly photo upload itself (batch captain's WhatsApp post →
  Drive, without the student doing it by hand).
- Full dynamic avatar state machine (idle/thinking/serving/error animations
  tied to agent state).
- Gamification layer: streaks, unlockable accessories, easter eggs.
- Predictive follow-up routing refined into a natural multi-turn flow.
- Deeper macro tracking (running totals across a day/week).
- Full native app (the ultimate vision) — this stage is deliberately just a
  webpage per the professor's guidance.

## 8. Development Roadmap
1. **Data structuring & logic** — WhatsApp-to-JSON pipeline, time-inference
   algorithm, basic text response loop.
2. **Avatar & UI prototyping** — core pixel-art sprite sheets, state-to-
   animation mapping.
3. **Macro & conversation refinement** — macro-calculation logic, predictive
   follow-up prompts.
4. **Gamification & polish** — streaks, unlockables, user testing on UI
   responsiveness and intent-parsing accuracy.

## 9. AI-Involvement Level: AI-led with review
I'm aiming for **AI-led with review**: Claude generates most of the
implementation — menu parsing, the intent/time-inference logic, the chat
interface, and the animation/state-machine wiring — from my direction, while
I own scope decisions, review generated code for correctness, test it against
real menu data and real usage from my batch, and make the creative calls on
the avatar's design and personality. I'm choosing this level because the
project's value is in solving a real, specific annoyance well and making it
delightful to use — not in hand-writing parsers or animation boilerplate —
so I'd rather spend my own effort on direction, review, and the product/
design decisions, and let AI carry the bulk of implementation.

## 10. Brainstorming Notes (not scoped yet)
- High-protein query → avatar flexes.
- Mess closed → avatar in pajamas with a "Zzz" bubble.
- Universally loved item on the menu → a distinct celebratory animation.
