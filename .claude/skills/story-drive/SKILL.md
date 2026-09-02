---
name: story-drive
description: The protocol for building and driving a Story-bot leg, chapter, or probe in the emulator harness. Use before writing any new --driver, before any live drive, and when a drive fails. Encodes the pre-registration, vacuity, fault-arm and evidence rules this project has paid for, plus the known live-emulator traps.
---

# story-drive — how a leg gets built and proven here

⛔ **The bar is not "it worked once". It is: predictions filed BEFORE the run, a grade a no-op cannot
satisfy, every guard fault-tested, and the evidence COMMITTED.**

## 0. BEFORE ANY CODE — recon, and do not blindly test

- Use agents on DIFFERENT ANGLES (decomp mechanics, how a human plays it, an audit of OUR code, a
  live tile dump, and one explicitly ADVERSARIAL "refute this"). Send them in ONE message.
- ⛔ **Their output is a NOTE, never truth.** Verify every load-bearing claim yourself at FILE:LINE.
  *A refuter has caught invented defects, an invented map, and a claim that would have created the
  very bug the module exists to avoid.*
- **Agreement between agents is NOT a confidence signal** — measured. Disagreement is a good search
  strategy; agreement proves nothing, because models share misconceptions.

## 1. PRE-REGISTER PREDICTIONS IN A COMMITTED FILE

Write `ai-research-notes/<date>-<leg>-PREDICTIONS.md` **before the drive**, listing per-reading
expectations AND the falsifiers ("what result would mean the build is wrong"). Grade after.
⇒ A reading that contradicts a prediction is a **RESULT**, never a driver failure.

## 2. THE DRIVER'S SHAPE (non-negotiable parts)

- `on_whiteout()` must latch the story abort and return **True** — returning False hands the run to
  Manual and DISCARDS the generator, so no verdict prints.
- ⛔ **And the latch is only true if a `try/except` lets the verdict run.** Wrap the body in ONE
  top-level try/except and compute the verdict from partial state. *Copying an `on_whiteout` comment
  does not copy the wrapper that makes it honest.*
- **A VACUITY / PREMISE CONJUNCT in the grade.** Test it mechanically: **point the driver at its own
  OUTPUT fixture. If it passes, the grade is measuring nothing.** *A chapter driver once printed
  `ACCEPTANCE: PASS` having executed ZERO frames.*
- **Readings recorded AT THEIR TAKE POINT** (`_take`), plus an ORDER trace — a set cannot distinguish
  "got the item, then proved it can continue" from the reverse.
- **The grade must include "and the bot can CONTINUE"**: a real `calculate_path` off the END tile,
  aimed at **what the NEXT chapter starts at**. ⛔ Not "somewhere reachable".
- Every yielding call inside an explicit frame budget. Bound every loop. `_check_abort()` first in
  every loop body, outside any `try`.

## 3. FAULT ARMS — one per guard, or the guard is decoration

Each arm is env-read INSIDE the production code (driver-proof), and the happy path reaches none.
Name them `POKEBOT_<CH>_FAULT_<NAME>`. Every arm must FAIL for **its own** reason — except arms that
prove a RECOVERY, which must still PASS.
⛔ **Register every new flag in `29-DISABLED-FEATURES-REGISTRY.md`** — `lint_docs.py` R6 enforces it.
Arms that have earned their keep here: skip-the-fix (proves it is load-bearing), stop-early (the
"passed while stranded" shape), suppress-one-reading, aim-the-control-at-a-reachable-tile,
face-the-wrong-way (proves a missed-press bail is live code).

## 4. RUNNING

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 verify_fixtures.py --assert <fixture>=<md5-prefix>   # FIRST, always
PYTHONUTF8=1 py -3.12 story_harness.py <fixture> --driver <name> --frames <N> --log x.log
```
- ⛔ **SMOKE TEST WITH A TINY `--frames` FIRST.** It catches import/attribute errors in seconds.
- ⛔ **`--log` IS HALF THE TRANSCRIPT.** The driver's `log()` goes there; the LEG's `console.print`
  goes to **stdout**. Capture BOTH (`> run.stdout.txt 2>&1`) or the evidence file will silently omit
  exactly the lines a fault arm exists to produce.
- Copy both into `tools/story-dev/evidence/<date>-<driver>-<ARM>.txt` and **commit them**. Then
  **grep the committed file for the line your claim rests on.**
- Fixtures: verify a capture with `probe_anchor_inventory.py`, then pin it in `saves/FIXTURES.md5`.

## 5. KNOWN LIVE TRAPS (each cost a drive)

- ⛔ **A layout-swapped map lies to every static reader**, including
  `get_map_data_for_current_position()` — it uses the live header but a SHARED layout cache. On such
  a map, `tile_type`/`collision`/`elevation` guards are worthless until you PIN it. The only true
  live oracle is the `gBackupMapLayout` grid. Un-pinned, a plan may not merely be wrong — it may not
  EXIST (`PathFindingError`, bot never moves).
- ⛔ **A cutscene ends AFTER its var.** One writes its var ~309 frames and a screen-fade before it
  finishes, and `player_avatar_is_controllable()` reads True under `lockall`. Settle on conjuncts:
  script inactive ∧ var advanced ∧ live layout back to normal ∧ controllable.
- ⛔ **A talk is over when the SCRIPT is, not when its flag is set.** Flags are written mid-body;
  the tail may move an NPC off a door you need. Require `not get_global_script_context().is_active`.
- ⛔ **Pressing a button every frame is HOLDING it.** Gen-3 `waitbuttonpress` needs a JOY_NEW edge, so
  a mashed msgbox never closes. Press on a duty cycle (one frame in four).
- ⛔ **`get_map_objects()` is a CAMERA-RANGE WINDOW.** Check presence from an ADJACENT tile; an empty
  list from across the map means nothing.
- A same-map `warpsilent` is a MAP RELOAD — never inherit position across a scripted talk.
- Arrow warps fire only while their direction is HELD; reach them as a final waypoint, never by a
  hand-rolled press loop, and never jolt the D-pad near one.

## 6. WHEN A DRIVE FAILS

Read the harness's no-progress dump — it names the generator, the map, the tile, and the active
script stack. **Read the failing line before touching the thing under test**: repeatedly the subject
was correct and the CHECK was wrong. And when a newly-tightened predicate produces a hang, suspect a
LATENT bug the old predicate skipped past — do not revert the predicate.
