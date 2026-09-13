"""GATE — the Mauville Wally masher must never be able to press B at a yes/no box.

‼ WHY THIS IS A GATE AND NOT A COMMENT. `#24-wallydecline` (2026-09-13) was the largest measured
defect in the project: `fight_wally_mauville` mashed `"B" if frames % 3 else "A"` into
`msgbox MauvilleCity_Text_WallyWillYouBattleMe, MSGBOX_YESNO`, and at a Gen-3 yes/no **B is "NO"**
(`src/script_menu.c Task_HandleYesNoInput`: `case MENU_B_PRESSED:` falls through to
`gSpecialVar_Result = 0`). Declining sets a flag **nothing in the decomp ever clears**, and Wally
stands on the only tile the gym door opens from ⇒ **124 of 143 ended runs died there.**

⛔ THE PROOF THAT A COMMENT IS NOT ENOUGH: the defect is PHASE-LOCKED, so removing the guard does
NOT reliably fail a test run — a fixture whose phase lands on A passes happily with the guard gone.
(It did: the pre-fix `mash` arm returns `ACCEPTANCE: PASS` on `mauville_prewattson.ss1`, and so did
the very first repro against unfixed code.) ⇒ **a behavioural test cannot be trusted to catch this
regression, so a STATIC one must.** That is the whole reason this file exists.

WHAT IT CHECKS, in BOTH builds (sandbox and custom — `lint_docs` R6 once passed while the SHIPPING
fork was unscanned, and that lesson applies here):
  C1  `fight_wally_mauville` still contains a mash of the `"B" if ... else "A"` shape.        (premise)
  C2  every `press_button(button)` in that function is preceded, inside the same function, by a
      `_yes_no_menu_is_open()` guard that can rewrite the button to "A".                      (the fix)
  C3  `_yes_no_menu_is_open` is still DEFINED and is what `_dialogue_button` delegates to, so the
      two predicates cannot drift apart.
⚠ C1 is a PREMISE check, not a style rule: if the mash is ever replaced by something better this
gate must be re-read, not silenced — it reports that case distinctly instead of failing blind.

⛔ BOTH BUILDS ARE ENFORCED (since the 2026-09-13 promotion). The gate ORIGINALLY made custom
advisory "until promoted", deciding that by whether custom happened to have the guard. ‼ That rule
was retired the same day as a self-defeating design: had custom ever LOST the guard, the gate would
have flipped itself back to advisory and printed "EXPECTED while UNPROMOTED" over a real REGRESSION.
**A gate whose strictness is derived from the state it polices cannot detect that state getting
worse.** The fix is in custom (`DIVERGENCE-LOG.md` 2026-09-13), so a missing guard there is now a
regression by definition.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_yesno_guard.py
"""
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
REL = pathlib.Path("modules") / "story" / "early_game.py"
BUILDS = {"sandbox": REPO / "sandbox-pokebot" / REL, "custom": REPO / "custom-pokebot" / REL}
FUNC = "fight_wally_mauville"
LINE = "=" * 92


def _function_source(text: str, name: str) -> str:
    m = re.search(rf"^def {re.escape(name)}\(", text, re.M)
    if not m:
        return ""
    nxt = re.search(r"^(def |class )", text[m.end():], re.M)
    return text[m.start(): m.end() + nxt.start()] if nxt else text[m.start():]


def check(build: str, path: pathlib.Path) -> tuple[bool, bool, list[str]]:
    """Returns (guard_present, premise_ok, problems)."""
    problems: list[str] = []
    if not path.is_file():
        return False, False, [f"{build}: {path} is missing"]
    text = path.read_text(encoding="utf-8", errors="replace")
    src = _function_source(text, FUNC)
    if not src:
        return False, False, [f"{build}: {FUNC}() not found — this gate's premise is gone, re-read it"]

    # C1 — premise
    premise = bool(re.search(r'"B" if \w+ % 3 else "A"', src))

    # C2 — the guard, in the same function, able to rewrite the button to "A"
    guard = bool(re.search(r'_yes_no_menu_is_open\(\)', src)) and bool(
        re.search(r'button\s*=\s*"A"', src))
    if premise and not guard:
        problems.append(
            f"{build}: {FUNC}() mashes B/A with NO `_yes_no_menu_is_open()` guard that forces \"A\". "
            "At Wally's MSGBOX_YESNO a B answers NO, which sets a flag nothing clears and blocks the "
            "gym door forever (#24-wallydecline: 124 of 143 ended runs).")

    # C3 — one predicate, two callers
    if guard:
        if "def _yes_no_menu_is_open" not in text:
            problems.append(f"{build}: the guard is called but `_yes_no_menu_is_open` is not DEFINED")
        dlg = _function_source(text, "_dialogue_button")
        if dlg and "_yes_no_menu_is_open" not in dlg:
            problems.append(
                f"{build}: `_dialogue_button` no longer delegates to `_yes_no_menu_is_open` — the two "
                "yes/no predicates have been allowed to DRIFT, which is how one of them silently "
                "stops recognising a choice box and starts B-mashing NO into it.")
    return guard, premise, problems


def main() -> int:
    print(LINE)
    results = {}
    for build, path in BUILDS.items():
        guard, premise, problems = check(build, path)
        results[build] = (guard, premise, problems)
        print(f"  {build:8} guard={'YES' if guard else 'no ':3}  mash_present={premise}  {path.name}")

    sandbox_guard = results["sandbox"][0]
    fatal: list[str] = list(results["sandbox"][2])

    # ⛔ BOTH BUILDS ARE ENFORCED SINCE THE 2026-09-13 PROMOTION — and the earlier "advisory until
    # promoted" rule had to go, because it was keyed on whether custom HAPPENED to have the guard.
    # ‼ That is self-defeating: if custom ever LOST the guard, the gate would flip itself back to
    # advisory and print "EXPECTED while UNPROMOTED" over an actual REGRESSION. A gate whose
    # strictness is derived from the state it is policing cannot detect that state getting worse.
    # The fix shipped to custom on 2026-09-13 (`DIVERGENCE-LOG.md`), so a missing guard there is now
    # a regression by definition, never an expected state.
    custom_guard, _custom_premise, custom_problems = results["custom"]
    fatal.extend(custom_problems)
    if sandbox_guard and not custom_guard:
        fatal.append(
            "custom-pokebot has NO guard while sandbox does. `#24-wallydecline` was PROMOTED on "
            "2026-09-13, so this is a REGRESSION in the shipping fork, not an unpromoted state.")

    print(LINE)
    if fatal:
        for f in fatal:
            print(f"  ⛔ {f}")
        print("  FAILED")
        return 1
    if not results["sandbox"][1]:
        print("  ⚠ the B/A mash is gone from sandbox — this gate's PREMISE changed. Re-read it")
        print("    rather than deleting it: the rule (never let B answer a choice) still holds.")
    print("  ✅ the yes/no guard is in place where it is required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
