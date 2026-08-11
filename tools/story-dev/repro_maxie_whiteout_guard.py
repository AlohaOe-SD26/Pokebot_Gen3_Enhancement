"""Regression test for KI-51: the Maxie challenge loop must notice that a WHITEOUT moved the
player off `MAGMA_HIDEOUT_4F`. NO EMULATOR — the loop's exit conditions are read from the source.

WHAT WENT WRONG (measured 2026-08-11, `--profile mh-anchor`). `do_magma_hideout`'s final loop was

    while not _groudon_awakened():
        _check_abort()
        press A/B
        if frames > 60000: raise "the Maxie challenge never resolved"

The run LOST to Maxie, whited out, and the game teleported the player to MAUVILLE_CITY (22,6).
`_groudon_awakened()` can never become true from there, so the loop went on mashing at an empty
overworld: **13 STUCK dumps, 18,300+ frames of "no progress"**, with the step message frozen at
`"at (15, 21), facing Right at Maxie (16, 21)"` while the avatar stood two towns away.

It was BOUNDED (60,000 frames), so this was never an infinite hang. The defect is that the bound's
message names the wrong cause — *"the Maxie challenge never resolved"* when the party had fainted —
which is the standing rule this project keeps re-learning: **a failure message must report STATE,
not a HYPOTHESIS** (`08-MISTAKES` 2026-08-10: "check the destination is walkable", on three runs
where it always was).

‼ WHY `_check_abort()` DID NOT SAVE IT, which is the subtle part. That call raises on
`_STORY_ABORT`, which **StoryMode's** whiteout handling sets — but a harness driver does not
necessarily mirror StoryMode's overrides (`04-HANDOFF`: "a harness driver must mirror the
OVERRIDES of the mode it stands in for; `on_whiteout()` defaults to False while StoryMode
overrides it to True"). So under the harness the abort flag is never set and the loop had no
escape at all. **A guard that only works in one of the two ways the code is run is not a guard.**

‼ WHAT THIS FILE DOES *NOT* CLAIM. A second driven run (`mh-anchor2`) also lost and stopped at
~20,600 frames into the Maxie step — far short of the 60,000 bound — but **that is not proof the
new guard fired**, because `_check_abort()` is an equally possible raise and the run's stdout was
lost. The live firing is UNCONFIRMED. What is confirmed is here (the structure) plus the map
comparison, verified both directions on real saves:

    magma_door.ss1     (24,13) == JAGGED_PASS      -> True    == MAGMA_HIDEOUT_4F -> False
    magma_1f_fail.ss1  (24,91) == MAGMA_HIDEOUT_4F -> True

i.e. on 4F the guard cannot fire, off 4F it can. (That control also showed `magma_1f_fail.ss1` is
misnamed — it stands on 4F.)

THE RULE THIS FILE PINS: **a loop whose exit condition is a story flag must ALSO watch for the
ways the game can move the player out from under it. A whiteout satisfies no flag.**

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_maxie_whiteout_guard.py
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = os.environ.get("REPRO_BUILD", "sandbox").strip().lower()
if BUILD not in ("sandbox", "custom"):
    raise SystemExit(f"REPRO_BUILD must be 'sandbox' or 'custom', got {BUILD!r}")
EARLY = REPO / f"{BUILD}-pokebot" / "modules" / "story" / "early_game.py"
print(f"(build: {BUILD} -> {EARLY.relative_to(REPO)})")

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


if not EARLY.exists():
    raise SystemExit(f"repro cannot run: missing {EARLY}")
src = EARLY.read_text(encoding="utf-8")

print("1. the loop this test reasons about is where it thinks it is")

fn = re.search(r"\ndef do_magma_hideout\(\).*?(?=\ndef do_magma_hideout_chapter)", src, re.S)
check("do_magma_hideout's body can be located", fn is not None)
body = fn.group(0) if fn else ""

# ‼ Anchor on the CONDITION, not on a line number or a comment — both drift, the condition is
# what defines this loop (it is the only `while not _groudon_awakened()` in the function).
loop = re.search(r"while not _groudon_awakened\(\):(.*?)\n    yield from wait_until", body, re.S)
check("the Maxie challenge loop can be located", loop is not None)
loop_src = loop.group(1) if loop else ""

print("2. THE FIX: the loop watches the MAP, not only the completion flag")

check(
    "the loop reads the current map",
    "get_map_data_for_current_position()" in loop_src,
    "a whiteout satisfies no flag — the only signal is that the player MOVED",
)
check(
    "it compares against MAGMA_HIDEOUT_4F specifically",
    "MapRSE.MAGMA_HIDEOUT_4F.value" in loop_src,
    "`map_group_and_number` is a plain tuple, so `== MapRSE.X.value` is a valid identity test",
)
check(
    "there is an off-map counter, i.e. the check is DEBOUNCED",
    "off_map" in loop_src and re.search(r"off_map\s*>\s*\d+", loop_src) is not None,
    "an INSTANT check could end a HEALTHY fight on one odd frame across a battle transition",
)
m = re.search(r"off_map\s*>\s*(\d+)", loop_src)
debounce = int(m.group(1)) if m else -1
check(
    "the debounce is long enough to outlast a battle transition but far below the 60,000 bound",
    120 <= debounce <= 3000,
    f"debounce = {debounce} frames",
)

print("3. THE FIX: an unreadable map can never END the fight")

# The map read must be wrapped, and its failure must mean "assume still on 4F" — the opposite
# default would turn a transient reader error into a lost boss fight.
guard_block = re.search(r"try:\s*\n\s*_on_4f = \((.*?)\n\s*except[^\n]*\n\s*_on_4f = (\w+)",
                        loop_src, re.S)
check("the map read is wrapped so a reader error cannot escape", guard_block is not None)
check(
    "…and an unreadable map defaults to STILL ON 4F (never to 'leave')",
    guard_block is not None and guard_block.group(2) == "True",
    "defaulting the other way turns a transient read error into a lost boss fight",
)

print("4. THE FIX: the failure reports STATE, not a hypothesis")

raise_m = re.search(r"if off_map > \d+:(.*?)\n            \)", loop_src, re.S)
raise_src = raise_m.group(1) if raise_m else ""
check("the off-map branch raises", raise_m is not None and "BotModeError" in raise_src)
for field, why in (
    ("map=", "which map we actually ended up on"),
    ("tile=", "where on it"),
    ("party_alive", "the fact that makes 'whiteout' the diagnosis rather than a guess"),
):
    check(f"the message carries {field}", field in raise_src, why)
check(
    "the message names WHITEOUT as the likely cause",
    "WHITEOUT" in raise_src.upper(),
    "so the reader does not have to re-derive it",
)

print("5. ORDER: the cheap off-map exit must come BEFORE the 60,000-frame bound")

off_at = loop_src.find("off_map >")
bound_at = loop_src.find("frames > 60000")
check("the 60,000-frame bound still exists", bound_at != -1,
      "it is the backstop for a fight that genuinely never resolves ON 4F")
check(
    "…and the off-map exit is checked first",
    off_at != -1 and bound_at != -1 and off_at < bound_at,
    "otherwise a whiteout still costs the full bound before anything notices",
)
check(
    "the bound's message no longer implies the fight is the only explanation",
    "still on 4F" in loop_src,
    "it can now say so, because the off-map case has its own exit",
)

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")
