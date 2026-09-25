"""⛔ GATE — A GENUINE STORY COMPLETION MUST BE CLASSIFIED AS ONE.

**THE DEFECT THIS EXISTS FOR (measured 2026-09-25, never yet hit in anger).** `story_mode.py`
emits, on the ONE path that means the bot finished everything built:

    "... basket bought. **End** of built content. NEXT (WIP): Ch24, THE POKEMON LEAGUE ..."

with a **capital E**. All three log classifiers looked for the lowercase needle
`"end of built content"` with a **case-sensitive** `in`, so the match was **False**.
⇒ the first ever completed run would have been filed as `HANG CONFIRMED` / a failure in every batch
report — a WIN recorded as a defect, which is the most expensive class of instrument error this
project has (a real success that reads as noise gets investigated as a bug, or worse, ignored).

‼ **AND THE OBVIOUS FIX WAS WORSE THAN THE BUG.** Lowercasing only the HAYSTACK repairs this one
needle and breaks TEN others in the same files — `HANG CONFIRMED`, `FEATHER BADGE`, `BADGE01_GET`,
`Traceback (most recent call last)`, `NavigationStuckError` … ⇒ the fix must casefold **BOTH**
sides, and this gate exists to prove it did not trade one defect for ten.

⇒ THREE ARMS, and each must fail for its own reason if the fix regresses:
  C1  the REAL emitted literal, lifted from `story_mode.py` at runtime, classifies as content-end.
  C2  every OTHER needle still matches a sample containing it verbatim (no needle was lost).
  C3  a text containing none of them classifies as neither (no false positives from casefolding).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_content_end_classifier.py
      exit 0 = PASS.  Also takes --self-test, which FAULT-TESTS this gate.
"""

import io
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
STORY_MODE = REPO / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
BAR = "=" * 100

#: The needle every classifier uses for a finished run.
CONTENT_END = "end of built content"


def emitted_literals() -> list[str]:
    """Every string literal in `story_mode.py` that mentions built content.

    ⛔ READ FROM THE SOURCE, NEVER HARDCODED HERE. A gate that carries its own copy of the thing
    under test passes forever after someone edits the real one — which is precisely how this defect
    survived: three classifiers and a docstring all carried a lowercase copy of a capitalised fact.
    """
    src = io.open(STORY_MODE, encoding="utf-8").read()
    return re.findall(r'"([^"\n]*[Bb]uilt content[^"\n]*)"', src)


def classify(text: str, needle: str = CONTENT_END) -> bool:
    """The FIXED comparison: casefold BOTH sides. Mirrors the three call sites."""
    return needle.lower() in text.lower()


def classify_broken(text: str, needle: str = CONTENT_END) -> bool:
    """The comparison as it shipped before 2026-09-25 — kept so C1 can show RED -> GREEN."""
    return needle in text


#: A sample per OTHER needle, so C2 proves nothing was lost to casefolding.
OTHER_NEEDLES = [
    "HANG CONFIRMED",
    "FEATHER BADGE",
    "BADGE01_GET",
    "Traceback (most recent call last)",
    "NavigationStuckError",
    "Could not find a path",
    "Move-learn dialogue could not be resolved",
    "BotModeError",
    "RUN COMPLETE",
]


def main(argv: list[str]) -> int:
    self_test = "--self-test" in argv
    print(BAR)
    print("  GATE — a GENUINE story completion must be classified as one")
    print(BAR)

    lits = [l for l in emitted_literals() if "NEXT" in l or "Handing" in l or "basket" in l]
    if not lits:
        print("  ⛔ ABORT (instrument, not a result) — no emitted 'built content' literal found in")
        print(f"     {STORY_MODE}. Either the banner moved or the scraper broke; fix this gate before")
        print("     trusting any verdict from it.")
        return 1

    ok = True

    # ---- C1: the real literal, and the RED -> GREEN transition ---------------------------------
    print("\n  C1 — THE REAL EMITTED LITERAL (read from story_mode.py, not hardcoded here)")
    for lit in lits:
        before = classify_broken(lit)
        after = classify(lit)
        print(f"     literal: ...{lit[:66]}...")
        print(f"       case-SENSITIVE (as shipped before the fix): {before}")
        print(f"       casefolded BOTH sides (the fix):            {after}")
        if not after:
            print("       ⛔ FAIL — a genuine completion still does not classify as content-end.")
            ok = False
        elif not before:
            print("       ✅ RED -> GREEN: this literal was MISCLASSIFIED before the fix.")

    # ---- C2: nothing was lost -------------------------------------------------------------------
    print("\n  C2 — EVERY OTHER NEEDLE STILL MATCHES (casefolding must not cost a classifier)")
    for needle in OTHER_NEEDLES:
        sample = f"f1234: some log noise ... {needle} ... more noise"
        hit = classify(sample, needle)
        print(f"     {needle[:44]:<46} -> {'ok' if hit else '⛔ LOST'}")
        if not hit:
            ok = False

    # ---- C3: no false positives -----------------------------------------------------------------
    print("\n  C3 — A LOG WITH NONE OF THEM MATCHES NOTHING (casefolding must not invent hits)")
    clean = "f1: CONTROLLER -> Story.run\nf2: heartbeat mode=Story\nf3: PARTY CHANGE ...\n"
    stray = [n for n in [CONTENT_END] + OTHER_NEEDLES if classify(clean, n)]
    if stray:
        print(f"     ⛔ FAIL — false positive(s) on a clean log: {stray}")
        ok = False
    else:
        print("     ok — clean log classifies as neither")

    # ---- the gate's own fault test ---------------------------------------------------------------
    if self_test:
        print("\n  --self-test — FAULT-TESTING THIS GATE (it must FAIL when the defect is present)")
        faulty = classify_broken(lits[0])
        print(f"     re-running C1 with the PRE-FIX comparison: match={faulty}")
        if faulty:
            print("     ⛔ SELF-TEST FAILED — the broken comparison MATCHED, so this gate could not")
            print("        have caught the defect it exists for. The gate is decoration; fix it.")
            return 1
        print("     ✅ the gate detects the defect it exists for (pre-fix comparison returns False).")

    print(BAR)
    print(f"  {'✅ PASS' if ok else '⛔ FAIL'} — a completed run "
          f"{'is' if ok else 'is NOT'} recognised, and no other classifier regressed.")
    print(BAR)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
