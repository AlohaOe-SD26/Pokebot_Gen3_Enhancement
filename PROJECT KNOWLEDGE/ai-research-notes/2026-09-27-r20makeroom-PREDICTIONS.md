# 2026-09-27 — RULING 20 Phase 1, increment A (one deposit-victim rule): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any drive. Branch `wt/r20phase1`. Design: `2026-09-27-ruling20-phase1-DESIGN.md` (a NOTE).
> Gate already green: `probe_r20_makeroom.py`, which is pure and has 4 fault arms.

## THE DRIVE — `--driver r20makeroom`

- Fixture: `fortree_gym_wedge.ss1` (PINNED). Read before this file was written: FORTREE CITY (4,19), 5 badges, box empty.
  The party:
  - Mightyena L38
  - Sceptile L39, the sole Rock Smash carrier
  - Swellow L33
  - Skitty L17
  - Zigzagoon L3, the sole Surf carrier
  - Castform L25
- `find_dead_weight` on it: **Skitty (L17), then Castform (L25)**.
- The driver registers counters as hunted and owed to the NEXT badge (`_hunted_counter_pids` +
  `_hunted_counter_badges` = the current count). It then sets `_needs_party_slot` (the HM make-room request) and runs
  production `heal_in_pokemon_center(PokemonCenter.FortreeCity)`.
- It records every `PCAction.deposit_pokemon_to_box` call: the ACTION, graded by PID.

## PREDICTIONS (each deposit graded by PID; the expected victim is computed in the driver WITHOUT calling the code under test)

| Case | Registered as owed counters | FIX (default) | Fault arm |
|---|---|---|---|
| **protect** | Skitty | deposits **Castform** (the next dead weight); Skitty stays | `POKEBOT_R20_FAULT_NOPROTECT=1` ⇒ deposits **Skitty**, the owed counter (the old live path) |
| **required** | Skitty + Castform | deposits **Swellow** (L33): the lowest remaining member that is not a sole HM carrier (Sceptile has Rock Smash, Zigzagoon has Surf) | `POKEBOT_R20_FAULT_NOREQUIRED=1` ⇒ deposits **nobody**; the party stays 6 (the old "nothing is safe" decline) |

**Premise conjuncts, in both cases:**
- the fixture's dead weight is exactly [Skitty, Castform];
- the heal ran, and the make-room rule was consulted: a deposit, or the "nothing is safe" line, is observed.

## FALSIFIERS

- **The deposit's PID differs from the table's in any arm:** the rule or its wiring is wrong. This is a RESULT, not a
  driver failure; read the failing line first.
- **The fault arm behaves like the fix:** the guarded behaviour is not what the arm removes. The arm would be
  decoration.
- **Nothing is consulted:** the piggyback never fired, e.g. the heal took a path that skips it. The drive is VACUOUS.

## WHAT THIS DOES NOT SHOW

- The HM errand end to end (`ensure_hm_learner_making_room`, then a hunt).
- The withdraw's own make-room step. It shares the rule, and M3 wires it statically, but it is not driven here.
- Frequency. One trajectory per arm.
