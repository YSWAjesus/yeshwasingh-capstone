"""
Which question goes where.

"What is there to eat today" and "what did I eat today" share almost every
word and have completely different answers. The routing between them is one
regex and an ordering, and until now nothing tested it — which is precisely
how the "toms" and "sat" bugs reached the live app: a confident answer about
the wrong thing looks exactly like a right one.

The menu cases matter more than the log cases. A missed log question is a
visibly unhelpful answer; a menu question wrongly captured by the log makes
the app look broken for its main purpose.

    python3 tools/test_intents.py
"""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import meal_log  # noqa: E402
import time_logic  # noqa: E402

# Asking about YOURSELF — must open the log, never the mess menu.
LOG_QUESTIONS = [
    "what did i eat today",
    "my log",
    "my macros",
    "calories so far",
    "show me the log",
    "how much have i eaten",
    "how much protein have i had today",
    "how many calories have i eaten",
    "how many calories did i eat",
    "set my protein target to 120g",
    "set my calorie goal",
    "my targets",
]

# Asking about the MESS — must never be swallowed by the log router.
MENU_QUESTIONS = [
    "what's for lunch",
    "what is there to eat",
    "most protein at dinner",
    "how much protein is in dinner",
    "how many calories is the paneer",
    "what's for lunch tomorrow",
    "whats the menu for friday",
    "thursday dinner",
    "show me friday",
    "sunday brunch",
    "toms lunch",
    "tom yum soup",
]


def test_routing():
    failures = []
    for question in LOG_QUESTIONS:
        if not meal_log.is_log_question(question):
            failures.append(f"{question!r} should open the log, went to the menu")
    for question in MENU_QUESTIONS:
        if meal_log.is_log_question(question):
            failures.append(f"{question!r} is about the mess, was captured by the log")
    assert not failures, "routing regressions:\n  " + "\n  ".join(failures)
    print(f"PASS  routing: {len(LOG_QUESTIONS)} log questions and "
          f"{len(MENU_QUESTIONS)} menu questions each go the right way")


def test_logging_sentences_never_reach_time_logic():
    """A sentence about eating must not be mined for a day or a meal.

    time_logic matches "sat" as Saturday and finds meal keywords by unbounded
    substring, so "i sat down and ate 2 rotis" reads as a Saturday query and
    "a bowl of snacks" reads as the Snacks meal. Any future parser for typed
    logging has to consume the text before either function sees it; this test
    exists to make that trap visible rather than to assert current behaviour.
    """
    traps = {
        "i sat down and ate 2 rotis": "sat -> Saturday",
        "log a bowl of snacks": "snacks -> the Snacks meal",
    }
    now = datetime(2026, 9, 23, 13, 0)
    found = []
    for sentence, why in traps.items():
        day = time_logic.day_reference_from_text(sentence, now)
        meal = time_logic.meal_type_from_text(sentence)
        if day[0] is not None or meal is not None:
            found.append(f"{sentence!r} -> day={day} meal={meal}  ({why})")
    assert found, (
        "These sentences used to be mis-parsed by time_logic. If none are any "
        "more, this test is stale — but check it was fixed deliberately."
    )
    print("PASS  documented traps still present, so a future typed-logging "
          f"parser must strip text first ({len(found)} cases)")


def test_target_phrases_reach_the_panel_that_holds_the_form():
    """The target form lives inside the log panel, so target phrases must
    route there rather than needing their own intent and their own screen."""
    for phrase in ["set my protein target to 120g", "change my calorie goal",
                   "my daily targets", "update my macro goal"]:
        assert meal_log.is_log_question(phrase), f"{phrase!r} does not open the panel"
    print("PASS  target phrases open the panel that contains the target form")


def main():
    test_routing()
    test_target_phrases_reach_the_panel_that_holds_the_form()
    test_logging_sentences_never_reach_time_logic()
    print("\nAll intent checks passed: questions about the mess and questions "
          "about you go to different places.")


if __name__ == "__main__":
    main()
