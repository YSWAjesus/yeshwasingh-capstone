---
name: nutrition-lookup
description: Produce a per-serving macro estimate (calories, protein, carbs, fat) for ONE Indian mess/canteen dish, in BatchCaptain's macros.json schema, with a cited source and a confidence band. Use when a dish is missing from data/macros.json or its numbers need re-sourcing.
argument-hint: "<dish name>"
---

# Nutrition lookup for one mess dish

You are estimating macros for **one** dish: `$ARGUMENTS`.

Write the result to `data/proposals/<slug>.json` (slug = the dish name,
lowercased, non-alphanumerics replaced with `-`). Write it through the
**filesystem MCP server**, not the Write tool — you are not permitted to touch
the live table, only to propose.

## Output schema

```json
{
  "dish": "pav bhaji",
  "calories": 400,
  "protein": 9,
  "carbs": 52,
  "fat": 17,
  "source": "https://... (what you actually read)",
  "confidence": "high | medium | low",
  "aliases": ["pav bhaaji"],
  "serving_basis": "1 pav + 150g bhaji, as served on a mess plate"
}
```

All four macro numbers are integers, per **one mess serving** — not per 100g,
and not per whole recipe. Getting this wrong is the single most common failure.

## Serving conventions — use these, they are the house standard

Mess portions are fairly consistent. Unless the source clearly describes the
exact serving you're modelling, assume:

| Item | Serving |
|---|---|
| Dal / gravy sabzi / kadhi | 1 katori ≈ 150 g |
| Dry sabzi | 1 serving ≈ 100 g |
| Cooked rice (plain/jeera/pulao) | ≈ 150 g |
| Chapati / phulka | 1 piece ≈ 40 g |
| Pav / slice of bread | 1 piece ≈ 40 g |
| Curd / raita | 1 katori ≈ 100 g |
| Soup | 1 bowl ≈ 200 ml |
| Sweet (halwa, kheer, ladoo) | 1 serving ≈ 80 g |
| Chutney / pickle / sauce | 1 tbsp ≈ 15 g |
| Papad / fryums | 1 piece |

Consistency matters more than precision here. Two dishes measured on different
bases make the whole table incoherent.

## Source hierarchy

1. **IFCT 2017 / NIN-ICMR Indian Food Composition Tables** — best for Indian
   staples. URL required.
2. Established nutrition databases with explicit Indian preparations. URL required.
3. **Ingredient-level reconstruction** — build the dish from its components at
   the serving sizes above, and say so in `source`. Confidence at most `medium`.
4. **Nearest analogue** — e.g. an unlisted regional dish modelled on a close
   relative. Confidence `low`, and name the analogue in `source`.

Use the **web search / fetch MCP tools** for research. Do not rely on memory
alone for tiers 1–2; if you cite a URL, you must have actually retrieved it.

## Sanity gate — pre-check this yourself

`tools/macros_store.py` re-applies these independently and will reject the
record, which just means the dish reappears in the next audit. Save the round
trip:

- `4×protein + 4×carbs + 9×fat` must be within **±15%** of `calories`
- `40 ≤ calories ≤ 900` per serving
- `protein ≤ 40 g`, `fat ≤ 45 g`, `carbs ≤ 150 g`
- not all zero

If your numbers fail the Atwater check, you have almost certainly mixed two
serving bases. Re-derive rather than nudging numbers to fit.

## Jain variants

Jain cooking drops onion, garlic, potato and other root vegetables. Derive from
the base dish minus the root-veg contribution — typically slightly fewer carbs
and calories, similar protein. Set `confidence: medium` and record the
derivation in `source` (e.g. "derived from mix veg handi, minus potato").

## When a dish isn't a dish

Some menu cells are placeholders, not food: `Beverage of the Day`,
`Pastry of the Day`, `Sweet of the Day`. Do not invent numbers for these.

## Prefer an alias over a new record

Before proposing a new entry, check `data/macros.json` for the same food under
another name. The OCR introduces typos and variants — `Banana Custurd` vs
`banana custard`, `Cucumbar Juice` vs `cucumber juice`, `Pickle` vs
`mixed pickle`, `Kulche` vs `kulcha`. If it is genuinely the same dish, propose
the **existing** dish key with the new name added to `aliases`, rather than a
duplicate record with slightly different numbers.

Long parenthetical names (`Exotic Veggies Alfredo (2 types of zucchini, ...)`)
should become an alias of the short form, with the ingredient list stripped.

## If you cannot resolve it

Write `{"dish": "...", "status": "unresolved", "reason": "..."}` instead of
guessing. The project's standing rule is that a missing estimate is shown to
the user as missing — never fabricated. An honest `unresolved` is a correct
outcome, not a failure.
