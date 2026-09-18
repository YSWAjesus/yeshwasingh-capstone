"""
Validate and merge proposed macro records into data/macros.json.

Agent proposes, program disposes. The macro-gap-filler agent can only write
per-dish proposal files; it cannot touch the live table. This script re-applies
the sanity gate independently, rejects with reasons, and writes canonically.

That matters for the loop: a rejected dish is still missing at the next audit,
so the agent has to change its approach rather than resubmit the same numbers.

    python3 tools/macros_store.py merge --from data/proposals \\
        --into data/macros.json --log data/macro_research_log.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = ("calories", "protein", "carbs", "fat")

# A mess serving that claims 2000 kcal, or 80g of protein, is a research
# failure — usually per-100g values or a whole-recipe yield mistaken for one
# plate. Bounds are deliberately generous; they catch blunders, not nuance.
#
# The floor is 10, not 40: condiments are legitimately tiny. A 40 floor
# rejected the table's own stored values for mixed pickle (25 kcal) and
# roasted papad (35 kcal), which meant a correct record could never be
# re-submitted for them. The all-zero check below is what actually catches
# empty records.
MIN_KCAL, MAX_KCAL = 10, 900
MAX_PROTEIN, MAX_FAT, MAX_CARBS = 40, 45, 150
ATWATER_TOLERANCE = 0.15
ATWATER_FLOOR_KCAL = 20


def validate(dish: str, record: dict):
    """Return a list of reasons this record must be rejected (empty = accept)."""
    problems = []

    if not dish or not dish.strip():
        problems.append("empty dish name")

    for field in REQUIRED:
        value = record.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            problems.append(f"{field} is not a number")
        elif value < 0:
            problems.append(f"{field} is negative")
    if problems:
        return problems

    calories, protein, carbs, fat = (record[f] for f in REQUIRED)

    if all(record[f] == 0 for f in REQUIRED):
        problems.append("all macros are zero")
    if not (MIN_KCAL <= calories <= MAX_KCAL):
        problems.append(f"{calories} kcal outside {MIN_KCAL}-{MAX_KCAL} per serving")
    if protein > MAX_PROTEIN:
        problems.append(f"{protein}g protein implausible for one serving")
    if fat > MAX_FAT:
        problems.append(f"{fat}g fat implausible for one serving")
    if carbs > MAX_CARBS:
        problems.append(f"{carbs}g carbs implausible for one serving")

    # Atwater check: the macros must roughly reconstruct the calorie figure.
    # Catches the common failure of researching macros and calories separately
    # from sources using different serving sizes.
    # The absolute floor matters for condiments: at 25 kcal, rounding grams to
    # integers can shift the implied figure by more than 15% on its own, so a
    # pure percentage test rejects perfectly good records.
    implied = 4 * protein + 4 * carbs + 9 * fat
    tolerance = max(ATWATER_TOLERANCE * calories, ATWATER_FLOOR_KCAL)
    if calories > 0 and abs(implied - calories) > tolerance:
        problems.append(
            f"macros imply {implied:.0f} kcal but record says {calories} "
            f"(more than {tolerance:.0f} kcal apart)"
        )
    return problems


def merge(proposals_dir: Path, table_path: Path, log_path: Path) -> dict:
    table = json.loads(table_path.read_text()) if table_path.exists() else {}
    accepted, rejected = [], []

    for proposal_file in sorted(proposals_dir.glob("*.json")):
        try:
            proposal = json.loads(proposal_file.read_text())
        except ValueError as exc:
            rejected.append({"file": proposal_file.name, "why": f"unreadable JSON: {exc}"})
            continue

        if proposal.get("status") == "unresolved":
            rejected.append({"dish": proposal.get("dish", proposal_file.stem),
                             "why": "agent reported unresolved: "
                                    + str(proposal.get("reason", ""))})
            continue

        dish = str(proposal.get("dish", "")).strip().lower()
        problems = validate(dish, proposal)
        if problems:
            rejected.append({"dish": dish or proposal_file.stem,
                             "why": "; ".join(problems)})
            continue

        table[dish] = {
            "calories": int(round(proposal["calories"])),
            "protein": int(round(proposal["protein"])),
            "carbs": int(round(proposal["carbs"])),
            "fat": int(round(proposal["fat"])),
            "source": str(proposal.get("source", "unknown"))[:300],
            "confidence": proposal.get("confidence", "low"),
            "aliases": sorted({str(a).strip().lower()
                               for a in proposal.get("aliases", []) if str(a).strip()}),
        }
        accepted.append(dish)

    # Sorted, one key per line: a five-dish change stays a small reviewable
    # diff instead of a whole-file reserialisation.
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(json.dumps(table, indent=2, sort_keys=True) + "\n")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as handle:
        for dish in accepted:
            handle.write(json.dumps({"result": "accepted", "dish": dish,
                                     "record": table[dish]}) + "\n")
        for entry in rejected:
            handle.write(json.dumps({"result": "rejected", **entry}) + "\n")

    return {"accepted": accepted, "rejected": rejected,
            "table_size": len(table)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["merge", "validate"])
    parser.add_argument("--from", dest="proposals", type=Path,
                        default=ROOT / "data" / "proposals")
    parser.add_argument("--into", dest="table", type=Path,
                        default=ROOT / "data" / "macros.json")
    parser.add_argument("--log", dest="log", type=Path,
                        default=ROOT / "data" / "macro_research_log.jsonl")
    parser.add_argument("--clear", action="store_true",
                        help="delete proposal files after a successful merge")
    args = parser.parse_args()

    args.proposals.mkdir(parents=True, exist_ok=True)

    if args.command == "validate":
        for proposal_file in sorted(args.proposals.glob("*.json")):
            proposal = json.loads(proposal_file.read_text())
            problems = validate(str(proposal.get("dish", "")).lower(), proposal)
            print(f"{proposal_file.name}: {'OK' if not problems else '; '.join(problems)}")
        return

    result = merge(args.proposals, args.table, args.log)
    print(json.dumps(result, indent=2))

    if args.clear:
        for proposal_file in args.proposals.glob("*.json"):
            proposal_file.unlink()

    if result["rejected"]:
        sys.exit(0)  # rejections are data for the next pass, not a crash


if __name__ == "__main__":
    main()
