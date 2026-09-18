"""
The nominated failure case: Gemini returns garbage or a partial menu reading.

Observed base rate in real testing: roughly 1 call in 4-5 comes back as a
partial grid (a day or two instead of seven). This test drives that failure
deterministically and asserts the app degrades the way it is supposed to:
retry, validate, then surface ONE clean sentence -- never a traceback, and
never a half-menu presented to a student as the full week.

    python3 tools/test_failure_modes.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import menu_data  # noqa: E402
from gemini_client import GeminiError  # noqa: E402

# What a partial read actually looks like: plausible, well-formed, and wrong.
# One day out of seven. Without the structural gate this would sail through.
PARTIAL = {"Monday": {"date": "14-Sep", "Lunch": {"Gravy Veg": "Paneer Kadai"}}}


def case(name, fake, expect_attempts):
    calls = {"n": 0}

    def stub(prompt, image_path=None):
        calls["n"] += 1
        return fake()

    real, menu_data.generate_json = menu_data.generate_json, stub
    try:
        menu_data.parse_menu_image(menu_data.SAMPLE_MENU_PATH)
    except GeminiError as exc:
        assert calls["n"] == expect_attempts, f"{name}: {calls['n']} attempts"
        assert "unreadable" in str(exc) or "attempts" in str(exc)
        print(f"PASS  {name}: retried {calls['n']}x, "
              f"then raised GeminiError -> {exc}")
        return
    finally:
        menu_data.generate_json = real
    raise AssertionError(f"{name}: a bad reading was accepted as a real menu")


def case_recovers():
    """The common case: one bad reading, then a good one. The user sees nothing."""
    calls = {"n": 0}
    good = menu_data.json.loads(
        (ROOT / "data" / "menu_snapshot.json").read_text())

    def stub(prompt, image_path=None):
        calls["n"] += 1
        return PARTIAL if calls["n"] == 1 else good

    real, menu_data.generate_json = menu_data.generate_json, stub
    try:
        menu = menu_data.parse_menu_image(menu_data.SAMPLE_MENU_PATH)
    finally:
        menu_data.generate_json = real
    assert len([d for d in menu_data.DAYS if d in menu]) >= 5
    print(f"PASS  recovers: 1st reading partial, 2nd good, "
          f"served the good one after {calls['n']} calls")


def main():
    case("partial grid", lambda: PARTIAL, 3)
    case("API error", lambda: (_ for _ in ()).throw(GeminiError("503")), 3)
    case_recovers()
    print("\nAll failure-mode checks passed: bad AI output never reaches "
          "the user as a menu.")


if __name__ == "__main__":
    main()
