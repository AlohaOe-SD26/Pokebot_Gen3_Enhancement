# 2026-10-02 — `#27-boxfirsttype` (KI-118): the PROOF DRIVER — DESIGN + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.**
- This item first PROVES the mechanism on TODAY's code, with no fix: a type-only box-first pick spends Norman's
  once-per-boss counter ladder and blocks the Machop hunt.
- The FIX is a USER decision. The obvious direction would reverse `06`'s logged own-type rule, so the options go to the
  user with this proof attached.
- The driver proves the BRANCH (budget spent, hunt blocked, boss still hopeless). It does NOT prove that the run would
  beat Norman without the pick. That half is observational: A's Mudkip runs went 13 of 13 through the Machop hunt.

**Recon:** `tools/story-dev/evidence/2026-10-02-boxfirst-gradeid-RECON.txt` (five read-only agents; NOTES).

**Verified by the coordinator:**
- `box_counter_choice` accepts on own type alone (`counter_hunt.py:387`).
- The box-first step registers its pick and returns True inside the once-per-boss bound (`story_mode.py:3111-3151`).
- `decide_maintenance` refuses the whole team when its single weakest battler is over budget (`story_mode.py:1920`,
  `:1932-1933`).
- The answer test skips moves at 0 PP (`:3043`).
- The fixture, by a live probe (below).

## What the recon established (the adversarial angle could not refute the Norman half)

- **Complete separation.** Among B Mudkip runs that met Norman with an unevolved Marshtomp, the 7 with a boxed
  Makuhita all walled and the 3 without all won. The two groups share lanes. Every Norman counter HUNT won, 14 of 14.
- **Resources were not the cause:** the walls held 9-25 balls, and every raise text lists Fiery Path as reachable.
- **Team strength was not the cause:** at the first Norman attempt, A and B Mudkip teams are equal (median top level
  34).
- **The mechanism is wider than KI-118 said:**
  1. the pick spends the ladder;
  2. the hopeless verdict stays, so the second wind fires;
  3. the untrained pick freezes MAINTAIN for the WHOLE team;
  4. with every battle lost, a level-36+ Marshtomp cannot evolve (evolution needs a won battle, pret
     `battle_main.c:5160`).
- **KI-118's note on H14 run 5 is wrong.** That stop was the answer test reading Vital Throw at 0 PP straight after a
  MAINTAIN session, not the hard plateau.
- **B's Tate & Liza excess is a DIFFERENT mechanism:** A 188 fights against B 437, and it appears before any ladder
  acts. It is filed separately.

## The driver: `--driver normanboxfirst` (a sibling of `CounterBoxMode`, `story_harness.py:24527`)

- **The fixture** is `prenorman_fodder_grind.ss1`, PINNED 2026-10-02 (`2580a3df…`).
  - Live probe: badges 1234, IN A BATTLE on ROUTE102 (9,2); party Combusken L35, Shedinja L25, Whismur L18, Ninjask
    L27, Mightyena L30.
  - It is the only tracked save in production's regime: 4 badges, Norman unbeaten, no credible answer to Normal.
  - The fallback is `norman_done.ss1` (pinned, PETALBURG_CITY), with `needed` passed as a literal. That one cannot run
    the hopeless reading, because its Blaziken knows Double Kick.
- **Steps:**
  1. Load the fixture and keep its bytes for the restore. Normalize to the overworld (the harness listener resolves the
     wild battle), then wait until controllable.
  2. **Premise T0, after normalize and before any write.** A failure ABORTS as "FIXTURE PREMISE", distinct from a
     FAIL. It checks:
     - the map (ROUTE102) and the hops to FIERY_PATH, which are recorded;
     - 4 badges, BADGE05 / RECEIVED_HM_SURF unset;
     - the party by (PID, species);
     - an empty box;
     - no resource blocker;
     - no party move scoring ≥ 75 against Normal.
  3. **Seed and derive (T1).** A fresh StoryMode, with `_counter_hunts` empty. Norman's cfg is copied from
     `story_mode.py:5566-5572`, with 8 defeats and 6 flat losses seeded. Then:
     - the REAL `_boss_plan_is_hopeless` must return `(True, ['Fighting'])`;
     - with the REAL planner, the shortlist must contain `Machop@FIERY_PATH`; otherwise the Y and Z arms are vacuous
       and the run ABORTS;
     - `box_counter_choice` must return None before the injection.
  4. **Inject (T2)** with `debug_create_pokemon` + `debug_write_box_slot` into box 0 slot 0, then wait 2 frames.
     Read it back through the production reader: species, level, moves, and a PID new to both party and box. The
     choice must equal its arm's expectation EXACTLY.
  5. **Instrument the actions** (restored in `finally`):
     - a delegating recorder on `counter_plan.find_counter_candidates`;
     - a recording stand-in for `counter_hunt.hunt` that returns None, so no hunt actually runs;
     - an instance wrapper on `_register_counter`.
  6. **CALL 1** to `_counter_ladder(norman_fight, 8, needed)`, recorded at T3: the result, planner calls, hunt calls,
     register calls, `_counter_hunts`, the registry and the owed counter PIDs.
  7. **CALL 2**, the same call, recorded at T4. Cumulative planner and hunt calls, plus whether `_counter_hunts` is
     unchanged.
  8. **Optional stage 2** (arms X and Y): the real heal at Petalburg collects the counter. At T5 in X: the Makuhita is in
     the party; `_boss_plan_is_hopeless` (same seed) still returns `(True, ['Fighting'])`; a CALL 3 returns False with
     planner calls still 0. That is "budget spent, boss still hopeless".
  9. Restore the fixture. Log every conjunct and ACCEPTANCE, then `set_manual_mode()`.
- **Two declared deviations from production:** the origin is ROUTE102, not PETALBURG_CITY (the hops are recorded),
  and the party has 5 mons.

## PREDICTIONS

Today's code, with no fix. Each arm runs TWICE (KI-112: the repeats are a determinism check, not a replication).

| # | Arm | Prediction | Falsified by |
|---|---|---|---|
| BF-1 | the premise (all arms) | after normalize, every T0 premise holds as listed; T1: `(True, ['Fighting'])`, a shortlist containing `Machop@FIERY_PATH`, and no pre-injection pick | any premise failure (then the run ABORTS, and that is a fixture finding, not a grade) |
| BF-2 | **X**: Makuhita L8 (moves Tackle, Focus Energy, Sand-Attack) | the pick is `(pid, 'Makuhita', 8, 'own type')`. CALL 1 returns True, with 0 planner calls, no hunt calls, and 1 register `(pid, 'PC box (box-first)')`. `_counter_hunts[(8,1)]` starts `box-first Makuhita L8`. CALL 2 returns False, with planner calls still 0 and `_counter_hunts` unchanged | a planner call, a hunt call, or a different pick |
| BF-3 | **Y**: empty box | no pick. CALL 1 enters the planner (≥ 1 call), and the hunt stand-in records `Machop@FIERY_PATH`. CALL 1 returns False (the stand-in returns None). `_counter_hunts` reads `Machop@FIERY_PATH: none found` | no planner call; no Machop hunt call |
| BF-4 | **Z**: X plus `POKEBOT_R20_FAULT_NOBOXCOUNTER=1` | identical to Y; the Makuhita stays boxed | any box-first registration |
| BF-5 | **X13**: Makuhita L13 (Vital Throw) | the pick is `(pid, 'Makuhita', 13, 'Vital Throw scores 210, own type')`, and otherwise the same as X. This is the arm a fix must NOT flip | a different pick or reading |
| BF-6 | **XBAD**: Zigzagoon L8 (a fault arm for the choice premise) | ABORT at T2: the pick is not the expected one | no ABORT |
| BF-7 | **XLATCH**: X, with `_counter_hunts` cleared between the calls (a fault arm for the latch reading) | CALL 2 enters the planner | CALL 2 does not enter it |
| BF-8 | stage 2 on X (optional) | after the Petalburg heal the Makuhita is in the party; the boss still reads `(True, ['Fighting'])`; CALL 3 returns False with planner calls still 0 | the boss reads not hopeless; a planner call |
| BF-9 | an INDEPENDENT adversarial pass on the driver | no reading is an artifact; every guard's fault arm fails for its own reason | an artifact or a guard without a working fault arm |

## What comes after the proof (the USER decides)

The options and their measured blast radius from the batch are in the recon (ANGLES 2 and 5):
- **O6:** a TYPE-ONLY pick does not spend the budget, so the hunt still runs once if the boss stays hopeless. Own-type
  acceptance and gate C1 are unchanged.
- **O5:** a type-only pick is accepted only if every ace type does ≤ 0.5× to it. Wattson's Ground picks stay.
- **A level floor:** about the boss's lowest party level minus 3. A human's view: pre-evolution Fighting types are
  one-hit KOs for Norman's team until about L20. But the batch's H14 run 5 walled even at L21-23.
- **Rejected:** "require a credible move" alone, which breaks Wattson's box-first (Ground moves are 0-3 BP in the
  data).
- **The driver is the fix's test.** X must flip while X13 stays. A Wattson regression arm (a type-only Geodude must
  still be accepted) is added for any level- or resistance-based option.
