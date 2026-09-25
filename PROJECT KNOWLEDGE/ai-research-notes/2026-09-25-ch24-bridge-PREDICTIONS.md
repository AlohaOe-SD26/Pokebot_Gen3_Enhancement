# PRE-REGISTERED PREDICTIONS — §Ch24 THE BRIDGE (`enter_the_league`)

**Written 2026-09-25, BEFORE the drive**, per `.claude/skills/story-drive` §1 and gate #72.

DRIVER: ch24bridge

FIXTURE: `post_ch24_atdoor_L75.ss1` (`8b8cd907db09`, PINNED and asserted) — the door APRON on
`EVER_GRANDE_CITY`, **outside** the building, door SHUT, Sidney UNBEATEN.
KNOB: `CH24_ENTRY_FLOOR=1` ⇒ the readiness branch is a no-op, so TRAVEL + COMMIT + FIGHT is what
runs. ⚠ That is **not** production's floor of 65, and the ACCEPTANCE line says so.

---

## WHAT THIS IS, AND WHY IT IS THE ONE THAT MATTERED

`prepare_and_open_the_league()` stops ON `(9,3)`. `fight_one_room()` begins *already in room N
having beaten trainer N*. **Nothing connected them** — `enter_the_league` and `ch24_chapter_done`
had **zero occurrences in the tree** — so a sequencer written as "loop over `PAIRS`" could not have
taken its first swing. This drive tests the step that closes that gap.

⭐ **IT DRIVES BOTH LEGS IN ONE RUN ON PURPOSE.** The seam is the thing under test; two separately
green legs prove nothing about the join between them.

⛔⛔ **THIS RUN CROSSES THE POINT OF NO RETURN** — it steps onto `(9,1)`, setting
`ENTERED_ELITE_FOUR` **permanently**, with every warp behind it inert. It is **HARNESS-ONLY** and
the driver **restores the fixture in a `finally`**, because `current_state.ss1` is what the real bot
resumes from.

---

## PREDICTIONS

### P1 — the two legs compose: leg 1 hands off on `(9,3)` with the door open.
GRADED-BY: entry, entered_flag_at_start
Predicted `entered_flag_at_start = False`, then leg 1's own readings all present and the bridge's
premise satisfied without intervention.
**FALSIFIER:** the bridge raises its lobby/door premise ⇒ the two legs do **not** join, and the
gauntlet still has no first step.

### P2 — ⛔ the COMMITMENT step works: `(9,1)` warps us to HALL5.
GRADED-BY: leg
Predicted `E2-COMMITTED` taken, `hall5_at` on `EVER_GRANDE_CITY_HALL5`.
**FALSIFIER:** still in the lobby ⇒ our door helper does not drive a step-on
`MB_NON_ANIMATED_DOOR`. ‼ **THIS IS A REAL OPEN QUESTION** — the 2026-09-17 probe reached HALL5
using `_navigate_riding_out`, while this leg uses `_pass_through_door`. **Different helpers, and
only the former has ever driven this particular door.** ⛔ If it fails, do NOT retry backward.

### P3 — the entry cutscene is settled on the VAR, not on a tile.
GRADED-BY: leg
Predicted `cutscene_settled = True` and `elite4_state_in_room >= 1`.
**FALSIFIER:** `cutscene_settled = False` ⇒ `VAR_ELITE_4_STATE` did not advance within the budget,
and `room_at` would then be a mid-`lockall` sample — exactly how a 2026-09-17 probe recorded
`(6,11)`, a tile the cutscene does not end on. ‼ Recorded, never asserted: the var counts rooms
ENTERED at the predecessor value.

### P4 — ⭐ SIDNEY IS BEATEN, and the leg asserts it on the FLAG.
GRADED-BY: sidney_flag_at_end, leg
Predicted `DEFEATED_ELITE_4_SIDNEY = True`, `whiteouts = 0`.
**FALSIFIER — AND THE MEANING IS PRE-COMMITTED:** this exact party beat Sidney from this exact
fixture on 2026-09-17 (`evidence/2026-09-17-ch24probe-SIDNEY-L75.txt`, 15 HP lost, zero faints).
⇒ a loss here would **not** mean "the party is too weak"; it would mean **this production leg
dropped something the probe had.** That is diagnosable by diff, and it is why the fixture was held
constant.

### P5 — ⭐⭐ THE RUN ENDS EXACTLY ON `fight_one_room`'s PREMISE FOR THE FIRST PAIR.
GRADED-BY: next_leg_premise_ok, end_at, phoebe_flag_at_end
Predicted `next_leg_premise_ok = True` — on `SIDNEYS_ROOM`, Sidney beaten, **Phoebe still unbeaten**.
**FALSIFIER:** anything else ⇒ the bridge does not actually hand off, and the gauntlet still cannot
start. ‼ This is the reading the whole leg exists to produce; P2-P4 are the means.

### P6 — the latch is the leg's FIRST act.
GRADED-BY: latch_calls
Predicted `latch_calls >= 1`. ⛔ `ch23_chapter_done()` needs `_on_map(EVER_GRANDE)`, which is FALSE
on every map past the lobby door — an unlatched run resuming in there re-enters §Ch23.
**FALSIFIER:** `0` ⇒ the run can be inside the sealed zone without owning itself.

### P7 — ⭐ WHICH ENGAGE SIGNAL FIRES FOR SIDNEY? (a genuine unknown, pre-committed)
GRADED-BY: leg
Predicted **`engage_signal = "suspension"`** — Sidney is measured to be an **INTERACTION** trainer
(*"my first cadence DID start Sidney's script"*), so our A-press should start the fight, as in
Phoebe's and Glacia's rooms.
**FALSIFIER:** `victory_flag` ⇒ Sidney's room fires on SIGHT during the approach, as DRAKE's does —
which would make **two of five** rooms sight-triggered and would matter for every future room leg.
⚠ Either outcome is informative; I am recording the prediction so the result cannot be rationalised
afterwards.

---

## ⛔ WHAT THIS DRIVE WILL NOT SETTLE

* **The room loop.** It ends where `fight_one_room` begins; it does not run it.
* **The CHAMPION**, whose room has no defeat flag, no A-press trigger and no door, and whose tail is
  a console reboot. ⛔ Deliberately not in scope, per `#24-leg2spec`.
* **RULING 11.** Harness driver, pinned fixture, `floor=1` — not "the real story mode, no fixture,
  at ×1".
* **The loss path.** USER RULING 12 (restock, then retry) is authorised and UNBUILT, and blocked on
  `#24-marthreachable`.
* **Basket consumption across a continuous run** — this drive fights exactly one trainer.
