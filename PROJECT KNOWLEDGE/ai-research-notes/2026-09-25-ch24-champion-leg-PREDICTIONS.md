# PRE-REGISTERED PREDICTIONS — §Ch24 THE CHAMPION LEG (`fight_the_champion`)

**Written 2026-09-25, BEFORE the drive**, per `.claude/skills/story-drive` §1 and gate #72.

DRIVER: ch24champion
FIXTURE: `post_hall4_door.ss1` (`1f15cc400218`, PINNED and asserted) — HALL4 `(5,3)`, one tile from
the Champion's door, nothing fought.

⛔⛔⛔ **THIS DRIVE CLEARS THE GAME.** Forced battle → forced save → unskippable credits →
`SoftReset(RESET_ALL)`. The driver restores the fixture in a `finally`; the budget is 200,000
frames against a measured ~50,000 so the run can **finish** (a frame-capped run never resumes the
generator, so the restore would not fire).

---

## WHAT IS ACTUALLY ON TEST

Not *"can the party beat Wallace"* — that is measured, **twice**. This is the **PRODUCTION LEG**:
ten readings, seven bounded steps, a grade a no-op cannot satisfy. The tail probe that beat Wallace
twice **asserts nothing** — its ACCEPTANCE line is instrument health. This leg asserts.

⭐ **AND IT IS DELIBERATELY NOT `fight_one_room`.** `#24-leg2spec` rules room 5 out of the unit, and
the locate-trainer / stand-beside / face / three-signal-engage steps are **deleted, not ported**:
the map script `lockall`s and walks the avatar in, so `ensure_facing_direction("Up")` would press a
direction at a LOCKED avatar, and `trainerbattle_no_intro` starts the fight with no press of ours.

---

## PREDICTIONS

### P1 — ⭐ THE CROSSING WORKS: eight raw `Up` presses fire the step-on warp.
GRADED-BY: leg
Predicted `C-CROSSED`, map becomes `CHAMPIONS_ROOM` within the 600-frame bound (⭐MEASURED cost 43).
**FALSIFIER:** still HALL4 ⇒ raw presses are not how this warp is driven, and the leg needs a
different crossing primitive. ⛔ It may NOT reach for `navigate_to` / `_pass_through_door` — those
make the warp a *destination*, which is the trap a tripwire guards one tile earlier.
‼ **A GENUINE UNKNOWN:** the probe that crossed successfully used a different press loop; this is
the production leg's own first crossing.

### P2 — `C-ENGAGED` comes from the CALLBACK, not from our press.
GRADED-BY: leg, battles
Predicted `battles == 1` and `battle_started_frame` set within 6,000 frames (⭐MEASURED 1,648).
**FALSIFIER:** no battle ⇒ we are past the point of no return with no fight, which is a **STRAND**
with nothing to retreat to. That is the worst outcome available here and it is why S1 refuses early.

### P3 — ⭐⭐ WALLACE IS BEATEN A **THIRD** TIME, asserted on `BattleOutcome`.
GRADED-BY: leg, battle_outcome
Predicted `C-WON`, `whiteouts == 0`.
**FALSIFIER — AND THE MEANING IS PRE-COMMITTED:** a loss is **a RESULT, not a defect**. ⛔ Before
blaming levels, read `pp_at_door`: the lead has historically arrived with **Crunch 0/15 and Take
Down 0/20** at full HP, and PP is unrestorable past the lobby. Two wins is not a win rate, and this
is the run that could show it.

### P4 — the endgame survives the `SoftReset`.
GRADED-BY: leg
Predicted `C-INHOF` (via the SCRIPTED warp, not a walked door), then `C-CLEARED`, then
`C-REBOOTED` — an **empty party observed**, the only positive proof EWRAM was wiped and reloaded.
**FALSIFIER:** the endgame bound expires ⇒ my 40,000-frame budget is wrong against a measured
14,161, or the reboot did not complete. ⛔ If it lands on `NAMING_SCREEN` the leg **hard-aborts and
stops pressing** — continuing would overwrite a save.

### P5 — ⭐ THE SETTLE HOLDS TWICE.
GRADED-BY: leg
Predicted `C-HOME` (seven conjuncts, tile `(4,2)`), then `C-USABLE` — the same conjuncts
**re-asserted** after `wait_until_truly_controllable()`.
**FALSIFIER:** `C-HOME` taken but `C-USABLE` refused ⇒ the first controllable frame was a flicker,
which is exactly what the second reading exists to catch (`player_avatar_is_controllable` debounces
`Task_ExitDoor` but **not** `Task_ExitNonDoor`, and that is the task on the first post-CONTINUE
frame). ‼ A v1 of the tail probe shipped with precisely this failure on disk.

### P6 — the heal at the door leaves the party ready.
GRADED-BY: leg
Predicted `heal_ready is True`. ⛔ `C-HEALED` is taken UNCONDITIONALLY, so the reading set alone
cannot fail on a heal that achieved nothing — `heal_ready` is a SEPARATE grade conjunct.
**FALSIFIER:** `False`/`None` ⇒ ACCEPTANCE fails on that conjunct alone, which is the arm A4 shape.

### P7 — the bounds are right, and none is hit.
GRADED-BY: leg
Predicted every `*_frames_spent` comfortably inside its bound.
**FALSIFIER:** any bound hit ⇒ a budget derived from the measured ledger is wrong. ⚠ The FIGHT row
is the one that is NOT deterministic (30,908 → 34,795 across two runs, a 12.6 % swing), which is
why its bound is ~5× and must not be tightened.

---

## ⛔ WHAT THIS DRIVE WILL NOT SETTLE

* **The win rate.** A third win from the same fixture is still not a rate.
* **`cross_to_the_champions_door()`** — the HALL4 approach leg is NOT built; this starts at `(5,3)`.
* **RULING 11.** A driver, a pinned fixture, at speed — none of its four conjuncts.
* **`_play` wiring.** Out of scope and deliberately so: the leg is harness-only until a completion
  predicate and a retargeted banner land with it.
* **The fault arms (P4 of the spec).** They come after the treatment is believed.
