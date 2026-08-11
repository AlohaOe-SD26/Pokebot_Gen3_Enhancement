"""Regression test for `#24-hmteachloop`: after an HM is LEARNED, the teach ride must stop
accepting prompts. NO EMULATOR — the button policy is read straight out of the source.

WHAT WENT WRONG (found 2026-08-07 by instrumenting the flow's exits; user-reported 2026-08-06:
"the hm learning feature works but it still loops trying to teach/get out of the teaching cycle
after it teaches an hm").

`teach_hm_move`'s ride loop drives the post-teach dialogue with this policy:

    if   "Task_StopLearningMoveYesNo"  in t:                 press B
    elif "Task_ReplaceMoveYesNo"       in t and not _knows(): press A
    elif "Task_HandleReplaceMoveInput" in t and not _knows(): pick the slot
    elif _f % 3 == 0:                                        press A
    else:                                                    press B

The moment the move IS learned, both middle branches switch themselves OFF via `and not
_knows()` — so every remaining frame falls through to the blind `A` / `B` alternation. But a
Gen 3 bag teach ENDS on **"Do you want to teach <MOVE> to another POKéMON?"**
(`Task_CallYesOrNoCallback`), and **A on that prompt means YES**: it reopens the party menu and
re-arms the whole teach cycle, which the A-mash then drives again. The loop was never stuck —
we were re-entering it ourselves, one frame in three, until the hard cap killed it.

MEASURED, `--driver teachfull` (Mightyena with four moves — the REPLACE path; `--driver hmtest`
teaches a freshly caught mon with a free slot and is 12/12 clean, which is why four earlier
rounds never reproduced anything):

    OLD arm (POKEBOT_HMTEACH_POSTLEARN_A=1)
        TEACH EXIT reason=ride:hard-cap  frame=8999  stall_peak=171
                   tasks=['ListMenuDummyTask', 'Task_CallYesOrNoCallback']
                   moves=['Tackle', 'Rock Smash', 'Take Down', 'Bite']   <- ALREADY LEARNED
    NEW arm (default)
        TEACH EXIT reason=ride:learned   frame=479   stall_peak=171

**8,999 -> 479 frames, same outcome** (`learned=True`, `replaced=['Taunt']`), and the exit is a
clean overworld task set instead of a dangling YES/NO prompt.

WHY FOUR BUDGET ROUNDS FAILED (7 / 8 / 9 / 4 failures across four configs): the cap only ever
decided how long to churn AFTER success, and the stall detector could never fire because the
ping-pong keeps the state changing — `stall_peak=171` against a 900 threshold. Two instrument
faults hid it:
  * only the SUCCESS path emitted telemetry, so no batch could say which exit fired; and
  * `TEACH OK ... in {_f} frames` read `_f` AFTER the menus-closed loop rebound it, so the
    famous "every successful teach exits in 35-86 frames" was the MENUS loop, not the ride.
    The ride's real cost was invisible — it was 8,999.

THE RULE THIS FILE PINS: once the operation's goal is achieved, a dialogue rider must stop
pressing the ACCEPT button. Any remaining prompt can only be an offer to do it again.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
EARLY = REPO / "sandbox-pokebot" / "modules" / "story" / "early_game.py"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


if not EARLY.exists():
    raise SystemExit(f"repro cannot run: missing {EARLY}")
src = EARLY.read_text(encoding="utf-8")

print("1. the ride loop is where this test thinks it is")

fn = re.search(r"\ndef teach_hm_move\(.*?(?=\ndef )", src, re.S)
check("teach_hm_move's body can be located", fn is not None)
body = fn.group(0) if fn else ""

# ‼ Locate the ride by the CONSTANT IT IS BOUNDED BY, not by a line number or a comment.
# Both drift; the bound is the thing that defines the loop.
ride = re.search(r"for _f in range\(_TEACH_RIDE_HARD_CAP\):(.*?)\n    # ", body, re.S)
check("the ride loop (bounded by _TEACH_RIDE_HARD_CAP) can be located", ride is not None)
ride_src = ride.group(1) if ride else ""

print("2. THE FIX: a learned move short-circuits the button policy BEFORE any accept branch")

# The chain is an if/elif ladder, so ORDER IS THE BEHAVIOUR. A `_knows()` guard placed after
# the fallback `elif _f % 3 == 0` would parse fine and do nothing.
# ‼ The ladder sits at EIGHT spaces (function body 4 -> `for` body 8). Matching twelve finds
# the stall check nested inside `if _sig is not None`, which is a different decision entirely —
# the first draft of this test did exactly that and reported a green fix as broken.
# ‼ ANCHOR ON THE LADDER, NOT ON "the first `if` in the loop". The loop OPENS with its own
# `if _knows() and get_game_state() is ...: break` success test, so "the first branch" matched
# that instead — and the body regex then ran from the break test all the way to the first
# `elif`, swallowing the real branch and passing every assertion for the wrong reason. The
# ladder is identified by the branch that presses buttons.
# ‼ MATCH BOTH SPELLINGS (2026-08-11). `#24-teachmsgstall`'s frame trace routes every button in
# this flow through a recording wrapper — `_press("B")` instead of
# `context.emulator.press_button("B")` — so that a trace line can carry the buttons WE pressed
# beside the state they produced. A structural test that pins the *spelling* of a call rather
# than its *meaning* turns a legitimate refactor into three red checks, which is exactly what
# happened here. Accept either form; the wrapper's only job is to press and record.
_PRESS_B = re.compile(r'(?:context\.emulator\.press_button|_press)\("B"\)')
_PRESS_A = re.compile(r'(?:context\.emulator\.press_button|_press)\("A"\)')
_ladder_m = _PRESS_B.search(ride_src)
ladder_at = _ladder_m.start() if _ladder_m else -1
check("the button-pressing ladder can be located", ladder_at != -1)
ladder_src = ride_src[:ladder_at]
ladder_head = re.findall(r"\n        (if|elif)\b([^\n]*)", ladder_src)
check("the ladder's first branch is an `if`", bool(ladder_head))

first = ladder_head[-1] if ladder_head else ("", "")
check("the ladder's FIRST branch tests whether the move is already known",
      "_knows()" in first[1] and "GameState" not in first[1],
      f"branch is `{first[0]}{first[1].strip()[:60]}`")

# And it must press B. Pressing A here is the bug itself.
first_body = re.search(
    r"\n        if _knows\(\) and not _POSTLEARN_A:\n(.*?)\n        elif ", ride_src, re.S
)
check("that branch's body exists", first_body is not None)
if first_body:
    b = first_body.group(1)
    check("it presses B (decline 'teach it to another POKéMON?')",
          _PRESS_B.search(b) is not None)
    check("it never presses A after the move is learned",
          _PRESS_A.search(b) is None,
          "an A here re-answers YES and re-enters the teach cycle")

print("3. the accept branches still refuse to fire once the move is known")

# ‼ MEANING, NOT SPELLING (2026-08-11). `#24-teachmsgstall` replaced the literal
# `"Task_ReplaceMoveYesNo" in t` test with `any(x in t for x in _PROMPT_TASKS)`, because that
# task exists for exactly ONE FRAME before the game swaps it for
# `Task_HandleReplaceMoveYesNoInput` — naming only the first is the bug. The invariant this
# check defends is "the accept branch cannot fire once the move is known", so match the branch
# by either spelling and then assert the guard.
for label, pattern in (
    ("the replace-prompt", r'(?:"Task_ReplaceMoveYesNo" in t|_PROMPT_(?:TASKS|MATCH)\))([^\n:]*)'),
    ("Task_HandleReplaceMoveInput", r'"Task_HandleReplaceMoveInput" in t([^\n:]*)'),
):
    m = re.search(pattern, ride_src)
    check(f"{label}'s branch still carries its `not _knows()` guard",
          m is not None and "not _knows()" in m.group(1))

print("4. the exits are still instrumented (this is how the bug was found)")

check("every ride exit records WHICH break fired", "_ride_exit" in body)
check("a non-success exit emits telemetry", "_teach_exit(" in body)
check("the stall high-water mark is reported", "_stall_peak" in body)

# ‼ The `_f`-reuse trap: the menus-closed loop rebinds `_f`, so the success event MUST report
# the ride's own captured count. Reporting `_f` there is what produced the bogus "35-86 frames"
# figure that justified four budget rounds.
check("the ride's frame count is captured before another loop rebinds `_f`",
      "_ride_frames = _f" in body)
# ‼ Substring, not a regex across the literal: the event is a multi-line implicitly-concatenated
# f-string, so any pattern spanning `TEACH OK` -> `ride_frames` has quotes and newlines in
# between. The first draft used `[^"]*` and failed on correct code.
check("the success event reports ride_frames (not the menus loop's `_f`)",
      "TEACH OK" in body and "ride_frames={_ride_frames}" in body)
# ‼ Strip comments first. The note explaining this very bug QUOTES the old format string, so a
# naive substring search over the whole function matches the documentation and fails a correct
# fix — the test would then be pinned to leaving the explanation OUT.
code_only = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith("#"))
check("the success event no longer reports a bare `in {_f} frames`",
      "in {_f} frames" not in code_only,
      "that read the menus-closed loop and produced the bogus 35-86 figure")

print("5. `#24-teachpathrace`: the instant-learn exit needs POSITIVE evidence of a free slot")

# The bug: `Task_HandleChooseMonInput` is still up after the mon is chosen, so on a slow frame it
# won the race before `Task_ReplaceMoveYesNo` appeared, the flow declared the instant-learn path,
# and the replace prompt was never answered (4 of 37 teaches, batch 20260807-102552, all fatal).
sel = re.search(r"# Either it learns instantly.*?\n    if _post_select_exit", body, re.S)
check("the post-select loop can be located", sel is not None)
sel_src = sel.group(0) if sel else ""

check("a free-slot fact is computed before the loop", "_free_slots" in sel_src)
check("the instant-learn exit is gated on it", "_may_instant_learn" in sel_src)

# ‼ The gate must sit ON the party-menu branch. Computing `_may_instant_learn` and then not
# using it in the condition would read as fixed and behave exactly as before.
menu_branch = re.search(
    r"if _may_instant_learn and \(\s*\"Task_PartyMenuReplaceMove\" in t\s*or\s*\"Task_HandleChooseMonInput\" in t\s*\)",
    sel_src,
)
check("the party-menu branch itself is guarded by the free-slot fact", menu_branch is not None,
      "a task present on BOTH paths cannot discriminate between them")

# And an ungated `_knows()` exit must remain: the move actually being on the mon is the
# strongest possible evidence that this really was the free-slot path.
check("an unconditional `_knows()` exit remains", re.search(r"\n        if _knows\(\):", sel_src) is not None)

print("6. the OLD arm is still reproducible on demand")

check("the fault-injection switch exists",
      "POKEBOT_HMTEACH_POSTLEARN_A" in body,
      "so the bug can be re-measured without reverting code")
check("the fix is the DEFAULT (switch defaults to off)",
      re.search(r'POKEBOT_HMTEACH_POSTLEARN_A"?,\s*"0"\)', body) is not None)

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")
