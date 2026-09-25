# PRE-REGISTERED PREDICTIONS — §Ch24 S2b: DOES `fight_one_room()` **COMPOSE**?

**Written 2026-09-24, BEFORE the drives.** Sidney → Phoebe is already driven and passing
(`272c226f`). This asks the next question, and it is the one the SEQUENCER depends on:

> **Does the SAME production function, unmodified, work for the OTHER room pairs — or did it only
> ever fit the one room it was written against?**

DRIVER: ch24room

FIXTURES (both PINNED and md5-verified before writing this):
* `post_phoebe_L75.ss1` (`87d2fe61774a`) — `PHOEBES_ROOM (6,6)`, **HP 1198/1214 (99 %)**, 0 fainted.
* `post_glacia_L75.ss1` (`da06afe74131`) — `GLACIAS_ROOM (6,6)`, **HP 776/1214 (64 %), MIGHTYENA
  FAINTED.**

⇒ these two are **not** the same test twice, and that is why both are worth driving.

---

## ⭐ WHY THIS IS A REAL TEST AND NOT A VICTORY LAP

`fight_one_room` hardcodes exactly two coordinates — `ROOM_EXIT_DOOR = (6,2)` and
`HALL_FAR_DOOR = (5,2)` — on the claim that they are **identical in all four rooms and all five
halls**. That claim is inherited from the three harness drivers; **the production leg has only ever
been run in ONE room.** A single-room pass cannot distinguish *"the constants are universal"* from
*"the constants happen to match Sidney's room"*.

⭐⭐ **AND `post_glacia_L75.ss1` IS THE HARD CASE, DELIBERATELY CHOSEN.** Sidney → Phoebe healed with
ONE Super Potion. Here the party arrives **64 % and a member down** — the Drake commit records this
as *"a party the previous room broke"* — so the heal must **REVIVE and then top up**, and
`heal_ready` has to flip from False to True on a party that genuinely is not ready.

---

## PREDICTIONS

### P1 — the unit COMPOSES unmodified for PHOEBE → GLACIA.
GRADED-BY: pair, victory_flag_set, end_at
Predicted `ACCEPTANCE: PASS`, all 9 readings, `DEFEATED_ELITE_4_GLACIA = True`, ending
`GLACIAS_ROOM (6,6)`.
**FALSIFIER:** stuck at either door ⇒ `(6,2)`/`(5,2)` are **not** uniform, and the sequencer needs a
per-room table rather than two constants. ‼ That would be a genuinely useful negative result.

### P2 — the unit COMPOSES unmodified for GLACIA → DRAKE.
GRADED-BY: pair, victory_flag_set, end_at
Predicted `ACCEPTANCE: PASS`, `DEFEATED_ELITE_4_DRAKE = True`, ending `DRAKES_ROOM (6,6)`.
**FALSIFIER:** as P1.

### P3 — ⭐⭐ THE HEAL REVIVES A FAINTED MEMBER AND FLIPS `heal_ready` FALSE → TRUE.
GRADED-BY: leg
Predicted, from `post_glacia_L75.ss1`: a non-empty `heal_plan` including a **Revive** for
Mightyena, `heal_actions >= 2`, and `heal_ready = True` at the end.
**FALSIFIER — AND IT WOULD BE A RESULT ABOUT THE BASKET, NOT A PORT DEFECT:** `heal_ready = False`
⇒ the bag could not restore the party, and `ACCEPTANCE` fails on the `heal_ready` conjunct **alone**
(`missing=[]`). That is the LEAGUE_BASKET economy telling us it is under-provisioned for a
four-fight gauntlet, which is exactly the kind of thing the re-entry predicate (S3) must price.
⛔ Do NOT read such a failure as "the leg is broken" — read the `heal_plan`.

### P4 — the heal is a NO-OP on the PHOEBE fixture, and still reports ready.
GRADED-BY: leg
Predicted, from `post_phoebe_L75.ss1` (99 %, 0 fainted): `heal_actions = 0` **and**
`heal_ready = True` — `heal_party_from_bag` sets `heal_ready = party_is_gauntlet_ready(before)` on
its early-out path, so "nothing to do" must still grade as ready.
**FALSIFIER:** `heal_ready` False or missing on an already-healthy party ⇒ the conjunct I added in
`272c226f` would fail runs that are perfectly fine, and it would need to distinguish
*"no plan because nobody needs healing"* from *"no plan because the bag is empty"*.
‼ This is the prediction that could show my own new grade conjunct is **too strict**. Writing it
down first is the point.

### P5 — no whiteouts in either drive.
GRADED-BY: leg
**FALSIFIER:** a whiteout from the 64 % fixture ⇒ the heal ran too late or not at all, and the
sealed-zone ordering (heal BEFORE crossing, never after) needs re-examining.

---

## ⛔ WHAT THESE DRIVES WILL NOT SETTLE

* **The CHAMPION room.** Not this unit — forced battle on entry, no `WalkInCloseDoor` seal. It is
  NOT in `PAIRS` and must not be added to it without its own design.
* **The sequencer**, which still does not exist, and the `_play` dispatch.
* **RULING 11.** Still a harness driver, still a fixture, still not ×1 from a real run.
* **Whether the basket survives a FULL five-fight run.** Each drive starts from a pinned mid-gauntlet
  fixture with its own bag; consumption across the whole gauntlet is not measured by three
  independent legs.
