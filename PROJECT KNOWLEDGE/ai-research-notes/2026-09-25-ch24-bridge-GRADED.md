# GRADED — §Ch24 THE BRIDGE (`enter_the_league`)

Graded **2026-09-25** against `2026-09-25-ch24-bridge-PREDICTIONS.md`, committed **before** the
drive (`1c0dc794`). Evidence: `tools/story-dev/evidence/2026-09-25-ch24bridge.stdout.txt`.

**THE RUN:** `CH24_ENTRY_FLOOR=1 --driver ch24bridge` from `post_ch24_atdoor_L75.ss1`
→ **`ACCEPTANCE: PASS`**, all 9 readings, `missing=[]`, `whiteouts=0`, `failure=None`.

```
start_at            = EVER_GRANDE_CITY(18, 6)             <- outside, door SHUT, Sidney UNBEATEN
hall5_at            = HALL5 (5, 12)                       <- the commitment step fired
room_at             = SIDNEYS_ROOM (6, 7)                 <- the cutscene's TRUE end tile
end_at              = SIDNEYS_ROOM (6, 6)
sidney_flag_at_end  = True        phoebe_flag_at_end = False
next_leg_premise_ok = True        latch_calls = 2
fixture RESTORED
```

⇒ ⭐⭐ **THE GAUNTLET CAN NOW TAKE ITS FIRST SWING.** The run ends on exactly
`fight_one_room(from_room=SIDNEYS_ROOM, …)`'s premise, and it got there from OUTSIDE the building
in one continuous run through **two production legs**.

---

## THE GRADE

| # | prediction | verdict | evidence |
|---|---|---|---|
| P1 | the two legs compose across the seam | ✅ **CONFIRMED** | leg 1's five readings all present, then the bridge ran without touching its own premise guard |
| P2 | ⭐ the COMMITMENT step works via `_pass_through_door` | ✅ **CONFIRMED** | `E2-COMMITTED`, `hall5_at = HALL5 (5,12)` |
| P3 | the cutscene is settled on the VAR, not a tile | ✅ **CONFIRMED — AND IT FIXED A KNOWN SAMPLING BUG** | see below |
| P4 | Sidney is beaten, asserted on the FLAG | ✅ **CONFIRMED** | `sidney_flag_at_end = True`, `whiteouts = 0` |
| P5 | ⭐⭐ ends on `fight_one_room`'s premise | ✅ **CONFIRMED** | `next_leg_premise_ok = True` |
| P6 | the latch is the leg's first act | ✅ **CONFIRMED** | `latch_calls = 2` (both legs latch) |
| P7 | ⭐ Sidney engages via our A-press (`suspension`) | ⛔ **REFUTED** | `engage_signal = victory_flag` — see below |

### ✅ P2 ANSWERED A REAL OPEN QUESTION

The 2026-09-17 probe reached HALL5 with `_navigate_riding_out`; this leg uses `_pass_through_door`.
**Different helpers, and only the former had ever driven this door.** The build spec's own M2 slot
was commissioned to settle exactly this and was never run. ⇒ **`_pass_through_door` DOES drive a
step-on `MB_NON_ANIMATED_DOOR`.** That question is now closed by measurement rather than by
assumption.

### ⭐ P3 — THE VAR SETTLE FIXED A BUG THE OLD PROBE SHIPPED WITH

`room_at = (6,7)`. The 2026-09-17 probe recorded **`(6,11)`** — and `(6,11)` is *not where the
cutscene ends*. It is a **mid-`lockall` sample**, taken because `wait_until_truly_controllable`
reads True under `lockall` and returns silently on timeout. `Common_Movement_WalkUp6` ends the
player on **`(6,7)`**, which is what this leg measured once it settled on
`VAR_ELITE_4_STATE >= 1` (`cutscene_settled = True`, `elite4_state_in_room = 1`) instead of on
controllability.
⇒ **the discriminator choice was load-bearing, not stylistic**, and ⛔ neither tile should ever be
hardcoded — the point is that the VAR advances only after `WalkInCloseDoor` returns.

### ⛔ P7 REFUTED — AND IT CHANGES THE COUNT

I predicted `suspension` because the tree records Sidney as an **INTERACTION** trainer. Measured:
**`engage_signal = victory_flag`** — the engage loop's FIRST reading already found the defeat flag
set, so the fight began **and ended** before the press loop ran at all.

| room entered | `engage_signal` |
|---|---|
| PHOEBE's | `suspension` (9,864 frames) |
| GLACIA's | `suspension` (26,772 frames) |
| DRAKE's | **`victory_flag`** |
| ⭐ SIDNEY's (this drive) | **`victory_flag`** |

⇒ **TWO of the four measured rooms fire before the engage loop, not one.** This is no longer an
oddity of Drake's room.

⛔ **MEASURED vs INFERRED, kept apart:**
* **MEASURED:** the signal is neither suspension variant — the only two ways this instrument can
  report a battle spanning one of its own `yield`s — so the fight happened before the loop's first
  iteration.
* **INFERRED, NOT ASSERTED:** *why*. Likely a sight line during the short approach from the
  cutscene's end tile `(6,7)` to the stand tile `(6,6)`, firing inside `_navigate_riding_out` whose
  frames are absorbed by its own budget. ⛔ **NOT VERIFIED.**
* ⚠ **AND IT WEAKENS AN EXISTING TREE CLAIM.** The note that Sidney is an interaction trainer came
  from a probe that sampled `(6,11)` — two tiles further back than where the cutscene actually
  ends. From `(6,7)` the approach is shorter and the geometry differs. ⇒ *"Sidney is an interaction
  trainer"* should be read as **"a press from (6,11) started his script"**, which is a narrower
  claim than it has been used as.

⇒ **THE PRACTICAL RULE IS UNCHANGED AND NOW BETTER EVIDENCED: a leg must NEVER assume its own press
caused the battle.** All three signals stay.

---

## ⛔ WHAT THIS DRIVE DOES **NOT** SETTLE

* **The room loop.** It ends where `fight_one_room` begins; it does not run it. The full chain
  bridge → 3 pairs has **not** been driven as one run.
* **The CHAMPION** — no defeat flag, no A-press trigger, no door, tail is a console reboot.
  Deliberately out of scope per `#24-leg2spec`.
* **RULING 11.** Harness driver, pinned fixture, `floor=1` — not "the real story mode, no fixture,
  at ×1". ⛔ `enter_the_league` is **NOT wired into `_play`**, and must not be until the Champion
  leg and a retargeted END-OF-CONTENT banner land with it.
* **The production floor.** This ran at `floor=1`; at 65 the readiness branch would train two mules
  for ~20 h first.
* **The loss path.** USER RULING 12 (restock, then retry) is authorised and UNBUILT, blocked on
  `#24-marthreachable`.
* **One trajectory, one fixture.**
