# Emulator throughput — ✅ RESOLVED 2026-09-07 BY MEASUREMENT: **~1030 frames/sec (~17× real time)**

**Status: MEASURED, and it retires this note's original question.** (Filename kept so existing links
still resolve; the "UNRESOLVED" in it is now historical.)

## The measurement

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 story_harness.py prenorman_fodder_grind.ss1 --driver traintest102 \
    --frames 100000 --log calib.log          # census OFF, no turn recorder, nothing else running

WALL SECONDS = 96      LAST FRAME = 99138      => 1032 frames/sec
```
⭐ Clean conditions were the whole point: **logging off and no second drive.** That is exactly what my
earlier figures lacked.

## What it corrects

| source | figure | verdict |
|---|---|---|
| ⛔ my own drives, 2026-09-06 | 112 / 123 / 148 f/s | **CONTAMINATED — do not cite.** `POKEBOT_KI93_CENSUS=1` was on (per-frame logging) and TWO drives overlapped, contending for CPU. |
| subagent inference from log timestamps | ~760 f/s | the right order of magnitude; low, because a log's mtime is its last FLUSH, not the run's end |
| ✅ **this measurement** | **1032 f/s** | clean, timed, single process |

‼ **The lesson is about the instrument, not the number.** My contaminated figure was ~9× low, and I
came within one decision of sizing a night's work with it. *A measurement taken while something else is
running is not a measurement of the thing you meant.*

## What it means for a grind

Re-derived with the measured Victory Road rate (775.6 EXP/battle, ~3,192 frames/battle):

| target | frames | **wall clock @1032 f/s** |
|---|---|---|
| L60 — clears Glacia in simulation | ~2.1M | **~34 minutes** |
| L75 — clears the gauntlet in simulation | ~6.6M | **~1.8 hours** |

⇒ **A grind is CHEAP, and the "~5 hours" priced in `03-PUNCH-LIST.md` was in EMULATOR minutes at
60 fps, never converted to wall clock.** Every training estimate in the docs carries that unit error.

⛔ **THIS DOES NOT MAKE THE GRIND SAFE TO START BLIND — two blockers stand**, both measured by a
subagent sweep and unrelated to speed:
1. `train_for_victory_road` **refuses before spending a frame** at L60+ — `MAX_TRAINING_FRAMES =
   250_000` is a PER-MON ceiling (`victory_road.py:508`, checked at `:1815-1822`) and L75 is ~9× over.
   The ceiling lives in the CALLERS, so a driver calling `train_team` directly bypasses it.
2. `Ch23TrainMode.on_whiteout` (`story_harness.py:13235`) only counts and logs — it never calls
   `set_story_abort(True)`, so `train_team`'s abort check cannot fire and a wipe has **no recovery**.
   Production `StoryMode` DOES recover (bounded at 40); the harness driver is the gap.
