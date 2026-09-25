# GRADED — §Ch24 LEG 1, `prepare_and_open_the_league`

Graded **2026-09-24** against `2026-09-24-ch24-entry-leg-PREDICTIONS.md`, committed **before** the
drive (`bb2ffa09`). Evidence: `tools/story-dev/evidence/2026-09-24-ch24entry.{log,stdout.txt}` and
the two fault arms `…-ARM-skiptalk.log`, `…-ARM-nolatch.log`.

**THE RUN:** `CH24_ENTRY_FLOOR=1 --driver ch24entry` from `post_ch24_atdoor_L75.ss1`
→ **`ACCEPTANCE: PASS`, 7 readings, `missing=[]`, `whiteouts=0`, `failure=None`.**

---

## THE GRADE

| # | prediction | verdict | the reading it rests on |
|---|---|---|---|
| P1 | the leg LATCHES before any button | ✅ **CONFIRMED** | `latch_calls = 1` |
| P2 | the door starts SHUT | ✅ **CONFIRMED** | `flag_at_start = False` |
| P3 | ⭐ the guards actually move, and the leg PROVES it | ✅ **CONFIRMED** | `flag_at_end = True` **and** `guard_tiles_clear = True` |
| P4 | the bot ends ON the talk tile, not through the door | ✅ **CONFIRMED** | `end_tile = (9,3)`, map `(16,10)` — **never HALL5** |
| P5 | the readiness branch is a NO-OP on this fixture | ⛔ **REFUTED** | see below |
| P6 | no whiteouts | ✅ **CONFIRMED** | `whiteouts = 0` |

## ⛔ P5 IS REFUTED, AND THE REFUTATION IS ENTIRELY MINE

I predicted the readiness branch would be a no-op *"the party is L75"*. **It is not.**
`post_ch24_atdoor_L75.ss1` carries **Zigzagoon L19 and Castform L36** alongside the L75 battlers —
the same two mules this session spent hours training in the §Ch24 climb drives. The leg correctly
found **2 mōn below L65** and began training, **outside, before entering** — which is exactly the
designed behaviour, and is why the first drive burned 400,000 frames with no verdict.

⇒ **The design was validated by the refutation.** What failed was my reading of the fixture: I saw
`L75` in its *name* and inferred the whole party. ‼ A fixture's name is a label, not an inventory.

⇒ The drive was then re-scoped with `CH24_ENTRY_FLOOR=1`, which makes the readiness half a no-op so
the **travel + guard** half can be driven in minutes. The ACCEPTANCE line reports the floor and says
plainly that it is **not** production's 65.

## ✅ FAULT ARMS — BOTH FAIL FOR THEIR OWN REASON

| arm | result | what it proves |
|---|---|---|
| `POKEBOT_CH24_FAULT_SKIPTALK=1` (read in PRODUCTION) | `missing=['E1-AT-DOOR','E1-GUARDS','T-CONTINUE']`, raised *"the door is shut; do NOT walk at it"* | the assertion is **live**, not decoration |
| `POKEBOT_CH24ENTRY_FAULT=nolatch` | `missing=['E1-LATCHED']` **only**, `latch_calls = 0` | the latch reading is real, and the arm **isolates** — it removes exactly one reading and leaves the other six |

## ⛔⛔ THE BUG THIS DRIVE FOUND, AND HOW IT WAS ACTUALLY FOUND

Two drives failed with `ENTERED_ELITE_FOUR` still False while **every other reading looked perfect**.
Two rounds of "fix the A-press" changed nothing.

⭐ **It was instrumentation, not iteration, that found it.** Recording the world at the moment of the
press showed `talk_tile=(9,3)`, `talk_facing='Up'`, guards present at `(9,2)`/`(10,2)`,
`script_active_after_A=True`, `talk_completed=True` — i.e. **the press and the ride-out were both
already correct.** What was missing was a settle: `wait_for_no_script_to_run("B")` starts **pressing
B immediately**, and called straight after the A it races the guard script's own startup.

‼ **The fix first appeared only as a SIDE EFFECT of adding those diagnostics** (a 30-frame wait).
⇒ it is now a named, documented constant `_GUARD_SCRIPT_SETTLE_FRAMES = 30` with its reasoning in
the leg, **so that deleting the diagnostics cannot silently delete the fix**.

⇒ This extends a lesson already in the tree (`victory_road.py:2986-2996`, *"copy the proven SHAPE,
not just the intent"*): copying the shape is necessary and was **not sufficient** — the nurse
sequence answers a yes/no prompt first, which supplies the settle the guard sequence lacks.

## ⚠ AND ONE PROCESS FAILURE WORTH RECORDING

I nearly reported a PASS that was **not from the run I had just launched**. An edit script wrote a
broken file and *then* failed its own `ast.parse`; the harness never started, and the log I read was
the previous run's. ⇒ **when an edit step reports an error, the next command's output is suspect — a
stale log is indistinguishable from a fresh one.** Fixed by deleting the logs and re-driving.

## ⛔ WHAT THIS DRIVE DOES NOT SETTLE

* **The gauntlet.** Not one of the five fights is in this leg, and the leg deliberately stops before
  the point of no return.
* **The production floor.** This ran at `floor=1`. At the real `CH24_LEVEL_FLOOR = 65` the readiness
  branch would train two mūles for ~20 h first — proven to work by the §Ch24 climb drives, but not
  exercised end-to-end *within this leg*.
* **Re-entry after a loss.** `ENTERED_ELITE_FOUR` is permanent, so a future gauntlet leg must not
  treat *"healthy again"* as *"ready again"*: a free nurse heal would re-pass a health-based gate
  forever while levels never change.
* **One trajectory**, one fixture.
