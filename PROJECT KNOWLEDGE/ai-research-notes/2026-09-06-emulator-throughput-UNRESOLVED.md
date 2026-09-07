# Emulator throughput is UNRESOLVED — and it decides whether an overnight grind is possible

**Status: a NOTE, not truth.** Two independent estimates disagree by ~5×, and the answer changes an
L75 grind from "a comfortable 3 hours" to "does not fit in a night".

## The two numbers

| Source | Figure | How it was obtained |
|---|---|---|
| Subagent research, 2026-09-06 | **~760 frames/sec** (~12.6× real time) | INFERRED from the wall-clock span of `Story-debug-20260904-102145.log` vs its frame count. The agent labelled this INFERRED, not measured. |
| My own drives, 2026-09-06 | **112 / 123 / 148 frames/sec** (~2–2.5×) | Frame delta in three `ch24probe` debug logs divided by (file mtime − filename timestamp). |

## Why neither is trustworthy yet

* ⚠ **Mine are contaminated.** All three ran with `POKEBOT_KI93_CENSUS=1` (heavy per-frame logging),
  and **two of them overlapped** — I started a second drive before the first had exited, so they
  contended for CPU. `ch24probe` also spends its time pathfinding and walking, not spinning battles.
* ⚠ **The subagent's is inferred from timestamps**, and a debug log's mtime is when it was last
  *flushed*, which need not be when the run ended.
* ⚠ Different drivers, different maps, different logging — these may simply not be the same quantity.

## Why it matters

Re-deriving with the measured Victory Road rate (775.6 EXP/battle, ~3,192 frames/battle):

| Target | Frames | @760 f/s | @150 f/s |
|---|---|---|---|
| L60 (clears Glacia) | ~2.1M | ~45–60 min | **~4 h** |
| L75 (clears the gauntlet) | ~6.6M | ~2.5–3 h | **~12 h** |

⇒ At the low figure an L75 grind **does not fit in a night**, and an L60 checkpoint is the most that
can be attempted. At the high figure both fit comfortably.

## ⛔ The rule this is an instance of

`03-PUNCH-LIST.md:571` prices training at "**~5 hours**" — and those are **emulator minutes at 60 fps**,
not wall clock. Nobody has ever measured this project's actual throughput on a clean run, so every
training estimate in the docs is expressed in a unit that has never been converted.

**⇒ BEFORE ANY LONG GRIND: run a SHORT CALIBRATION** — one training driver, logging OFF, no other
process running, a fixed `--frames`, and time it. That single measurement retires this note and turns
every stale hour-estimate in the punch list into a real number. It is minutes of work and it is the
difference between a productive night and a wasted one.

‼ This is the project's own standing rule for grinds, restated: *a grind is the one kind of work where
"just run it and see" is the expensive option.*
