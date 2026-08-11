"""Regression test for `#24-teachmsgstall`: the HM-teach flow must not depend on a ONE-FRAME
sighting of `Task_ReplaceMoveYesNo`. NO EMULATOR — the detection policy is read out of the source.

WHAT WENT WRONG (root-caused 2026-08-11 with `TEACH_TRACE=1`, after four rounds of refuted
hypotheses). `teach_hm_move`'s post-select loop waited for the replace prompt like this:

    if "Task_ReplaceMoveYesNo" in t and "Task_PrintAndWaitForText" not in t:
        _post_select_exit = "replace-prompt"; break
    ...
    if _f % 12 == 0: press A

MEASURED (frame trace, `magma_door.ss1`, HM02 -> Swellow):

    f3232735  tasks=['Task_ReplaceMoveYesNo']              <- the ONLY frame it is visible
    f3232736  tasks=['Task_HandleReplaceMoveYesNoInput']   <- gone, and it never comes back

`pret/pokeemerald src/party_menu.c` says why, exactly:

    static void Task_ReplaceMoveYesNo(u8 taskId) {
        if (IsPartyMenuTextPrinterActive() != TRUE) {
            PartyMenuDisplayYesNoMenu();
            gTasks[taskId].func = Task_HandleReplaceMoveYesNoInput;   // <- swaps ITSELF out
        }
    }

So the task **retires itself on the very frame it becomes answerable** — which is precisely the
frame the old condition first became true. The detector's window was one frame wide.

WHAT MISSING IT COST. The loop kept mashing A every 12 frames, and per the same decomp
`Task_HandleStopLearningMoveYesNoInput` reads **A as YES = ABANDON THE TEACH** (case 0 ->
"<mon> did not learn <MOVE>" -> `Task_ClosePartyMenuAfterText`). Our own buttons therefore
walked the flow: YES-replace -> summary screen (`Task_ClosePartyMenuAndSetCB2`) -> "Stop trying
to teach?" -> **YES** -> back to the bag -> and the same mash re-armed the teach from the item.

‼ THAT IS WHY THE FAILURE POINT "MOVED" ACROSS RUNS and looked like three different bugs. The
three recorded task sets are three phases of one road:

    ['Task_ClosePartyMenuAndSetCB2']                              summary-screen handoff
    ['Task_ClosePartyMenuAfterText', 'Task_PrintAndWaitForText']  "did not learn FLY"
    ['ListMenuDummyTask', 'Task_BagMenu_HandleInput']             back in the bag, re-arming

‼ AND WHY IT READ AS DETERMINISTIC *AND* INTERMITTENT AT ONCE — the thing that made it
unfalsifiable for four rounds. A `.ss1` replays identical frame timing, so a save that misses
the window misses it on EVERY replay (0 of 3 from the old `magma_door.ss1`); live runs land on a
random phase and hit it rarely (38 of 42 in batch `20260810-082509`, ~90% pass). One bug, both
readings.

LIVE A/B (`--driver teachfull`, `magma_door.ss1`, HM02 -> Swellow, `TEACH_MISS_WINDOW=1` models
the mistimed frame by ignoring the 1-frame sighting — the game state is untouched, only our
observation of it):

    OLD arm (POKEBOT_TEACHWINDOW_A=1)   learned=False
    NEW arm (default)                   learned=True

THE RULES THIS FILE PINS:
  1. **Never key a detector on a task that retires itself on the frame it becomes useful.**
     Watch the task that READS INPUT (`Task_Handle...Input`) as well as the one that displays.
  2. **Never blind-mash the ACCEPT button at a live yes/no.** Somewhere in Gen 3 there is a
     prompt where A means "give up", and a 900-frame mash will find it.
  3. A detector that can only be true for one frame is not a detector; it is a lottery.
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
# `REPRO_BUILD=custom` points this at the promoted fork, so a promotion can be checked
# STRUCTURALLY and not only by `diff -rq`. (A byte-identical copy makes the two equivalent, but
# the day the copy is partial is exactly the day nobody re-runs the diff.)
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

print("1. the loops this test reasons about are where it thinks they are")

fn = re.search(r"\ndef teach_hm_move\(.*?(?=\ndef get_rock_smash_hm)", src, re.S)
check("teach_hm_move's body can be located", fn is not None)
body = fn.group(0) if fn else ""

# ‼ Anchor the post-select loop on the variable it EXISTS to set, not on `range(900)` — the
# budget is a tuning knob and has been changed four times; `_post_select_exit` is the contract.
post = re.search(
    r"_post_select_exit = \"exhausted\"\n    for _f in range\(\d+\):(.*?)\n    if _post_select_exit",
    body,
    re.S,
)
check("the post-select loop can be located", post is not None)
post_src = post.group(1) if post else ""

ride = re.search(r"for _f in range\(_TEACH_RIDE_HARD_CAP\):(.*?)\n    # ", body, re.S)
check("the ride loop (bounded by _TEACH_RIDE_HARD_CAP) can be located", ride is not None)
ride_src = ride.group(1) if ride else ""

print("2. THE FIX, part 1: the prompt is recognised by BOTH of its task spellings")

check(
    "a shared _PROMPT_TASKS tuple exists",
    "_PROMPT_TASKS = (" in body,
    "one definition, so the two loops can never drift apart again",
)
prompt_tuple = re.search(r"_PROMPT_TASKS = \(([^)]*)\)", body)
prompt_names = prompt_tuple.group(1) if prompt_tuple else ""
for task in ("Task_ReplaceMoveYesNo", "Task_HandleReplaceMoveYesNoInput"):
    check(f"_PROMPT_TASKS includes {task}", task in prompt_names)
check(
    "the DISPLAY task alone is not what the post-select loop breaks on",
    "_PROMPT_TASKS" in post_src or "Task_HandleReplaceMoveYesNoInput" in post_src,
    "keying only on Task_ReplaceMoveYesNo is the one-frame window itself",
)

print("3. THE FIX, part 2: an already-answered prompt is picked up, not hunted")

check("the post-select loop has an `already-advanced` exit", '"already-advanced"' in post_src)
adv_tuple = re.search(r"_ADVANCED_TASKS = \(([^)]*)\)", body)
adv_names = adv_tuple.group(1) if adv_tuple else ""
for task in (
    "Task_ShowSummaryScreenToForgetMove",
    "Task_SetHandleReplaceMoveInput",
    "Task_HandleReplaceMoveInput",
    "Task_ReturnToPartyMenuWhileLearningMove",
):
    check(f"_ADVANCED_TASKS includes {task}", task in adv_names)
check(
    "the downstream replace block also runs on the `already-advanced` path",
    '_post_select_exit == "already-advanced"' in body.split("_TEACH_RIDE_HARD_CAP")[0].split(
        '_teach_exit("post-select-900-exhausted"'
    )[-1],
    "otherwise the flow falls into the ride loop with the forget-move screen still waiting",
)
check(
    "that new path cannot raise where the old code fell through",
    "required=" in body and "required: bool = True" in body,
    "a NEW run-ending class is not an acceptable price for this fix",
)

print("4. THE FIX, part 3: A is never mashed at a prompt where A means 'give up'")

stop_tuple = re.search(r"_STOP_TASKS = \(([^)]*)\)", body)
stop_names = stop_tuple.group(1) if stop_tuple else ""
for task in ("Task_StopLearningMoveYesNo", "Task_HandleStopLearningMoveYesNoInput"):
    check(f"_STOP_TASKS includes {task}", task in stop_names)
# ORDER IS THE BEHAVIOUR: the B branch must come BEFORE the `_f % 12` A fallback, or it does
# nothing on the frames that matter.
stop_at = post_src.find("_STOP_TASKS")
mash_at = post_src.find("_f % 12")
check(
    "the post-select loop presses B at the stop-learning prompt",
    stop_at != -1 and '_press("B")' in post_src,
)
check(
    "…and it does so BEFORE the blind A fallback",
    stop_at != -1 and mash_at != -1 and stop_at < mash_at,
    "an elif after the fallback parses fine and never fires",
)
# ‼ The ride ladder matches against `_STOP_MATCH` / `_PROMPT_MATCH`, which are `_STOP_TASKS` /
# `_PROMPT_TASKS` unless the OLD arm is selected. Assert BOTH halves: that the ladder uses the
# indirection, AND that the indirection defaults to the full tuple. Checking only the first
# would pass even if `_STOP_MATCH` were hard-wired back to the single display task.
for label, match_name, full_name in (
    ("stop-learning", "_STOP_MATCH", "_STOP_TASKS"),
    ("replace", "_PROMPT_MATCH", "_PROMPT_TASKS"),
):
    check(
        f"the ride loop's {label} branch also covers both spellings",
        match_name in ride_src,
        "it named only the display task, so the answerable frames fell through to `_f % 3` -> A",
    )
    m = re.search(rf"{match_name} = \([^)]*\) if _WINDOW_A else {full_name}", body)
    check(
        f"…and {match_name} falls back to the full {full_name} when the OLD arm is off",
        m is not None,
    )

print("5. the OLD arm and the REPRO are both still reproducible on demand")

check(
    "the pre-fix loop can be restored without reverting code",
    "POKEBOT_TEACHWINDOW_A" in body,
)
check(
    "the one-frame miss can be injected on demand",
    "TEACH_MISS_WINDOW" in body,
    "this is the repro — the natural fixture stopped reproducing when magma_door.ss1 was re-captured",
)
for flag, default in (("POKEBOT_TEACHWINDOW_A", "_WINDOW_A"), ("TEACH_MISS_WINDOW", "_MISS_WINDOW")):
    m = re.search(rf'{default} = _os_trace\.environ\.get\("{flag}", "(\d)"\) == "1"', body)
    check(f"{flag} defaults to OFF (the fix is the default)", m is not None and m.group(1) == "0")

check(
    "the frame trace that found this is still available",
    "TEACH_TRACE" in body and "pressed_since" in body,
    "the buttons WE pressed must appear beside the state they produced, or the trace proves nothing",
)

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")
