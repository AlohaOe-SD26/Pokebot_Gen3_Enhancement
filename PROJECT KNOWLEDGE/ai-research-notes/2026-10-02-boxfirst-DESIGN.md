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

## THE FIX: decided under USER RULING 30, filed 2026-10-02 BEFORE any fix code

**The decision:** a credible box counter is still used first; a type-only box pick becomes a FALLBACK. The rule is
"use a real answer from the box if you have one; otherwise go catch one; only if that is impossible, field what you
have". It matches what a player does at Norman: catch a Machop at Fiery Path rather than send out an untrained L8
Makuhita with no Fighting move.
- It KEEPS `06`'s own-type acceptance as the fallback, so Wattson's Ground picks still work.
- It sets no level threshold.
- It costs no extra losses. Each loss halves the money, which "field it first, then hunt" (the recon's O6) would pay
  6 or more times.
- **Rejected:**
  - O6, field first and hunt after: extra losses, and the proof review warned that a naive version loops without the
    latch.
  - A credible-move requirement: it breaks Wattson.
  - A level floor: arbitrary, and H14 run 5 walled at L21-23.

**The change** (`story_mode.py` `_counter_ladder`; nothing else):
- box-first registers its pick only when it is CREDIBLE (`credible` in `box_counter_choice`'s answer);
- a type-only pick is held as `fallback`, and the ladder goes on to the planner and the hunt exactly as today;
- at each point where the ladder would return False after that, the held fallback is registered instead and the
  ladder returns True. Those points are: the planner raises, a resource blocker, no shortlist, a hunt that finds
  nothing, and no destination working;
- the `_counter_hunts[key]` text names the fallback and why;
- the once-per-boss latch is UNCHANGED: it is written before anything acts, so a lost or uncleared latch cannot loop;
- **the fault switch `POKEBOT_KI118_FAULT_TYPEONLYFIRST=1` restores today's behaviour** (a type-only pick taken at
  once). It is a §B row in `29`.
- An UPSTREAM-mirrored file? No: `story_mode.py` is ours, so this is a fork change, logged in `DIVERGENCE-LOG` only if
  it is promoted.

**The driver extensions**, folding the proof review (`BFREV-1`…`BFREV-8`):
- the hunt stand-in can return a caught counter (a boxed Machop L15 with Karate Chop) as well as None;
- a Wattson cfg (copied from `story_mode.py`) with a boxed type-only Geodude, needing Ground;
- STAGE2 is allowed on X13 (a positive control for the hopeless reading);
- `reg4 == reg3` (no second registration) is graded;
- a T0 conjunct: FIERY_PATH is reachable from PETALBURG_CITY within `COUNTER_MAX_HOPS`;
- fault arms: CONFIG (X plus the old fault switch gives a CONFIG ABORT), and DERIV (5 seeded defeats → not hopeless →
  a DERIVATION ABORT);
- the post-verdict restore exception is annotated in each evidence header.

### PREDICTIONS for the fix (each graded arm runs twice; the repeats are a determinism check)

| # | Arm | Prediction | Falsified by |
|---|---|---|---|
| BF-10 | **XF**: the fix; L8 Makuhita boxed; hunt stand-in returns None | the pick is still 'own type' (type-only), but CALL 1 ENTERS the planner (1 call); the stand-in is called with `Machop@FIERY_PATH`; the fallback then registers the Makuhita; CALL 1 returns True; `_counter_hunts` names the fallback and "none found"; CALL 2 returns False with planner calls still 1 and no second register | 0 planner calls (the fix not live); no fallback register |
| BF-11 | **XF-CAUGHT**: the fix; L8 Makuhita boxed; the stand-in returns a boxed Machop | 1 planner call; the Machop is registered (`PC box`), and the Makuhita is NOT; CALL 1 returns True | the Makuhita registered |
| BF-12 | **X13F**: the fix; a credible L13 Makuhita | identical to today's X13: box-first registers it with 0 planner calls (the credible path is unchanged) | a planner call |
| BF-13 | **YF**: the fix; empty box | identical to today's Y | any difference from Y |
| BF-14 | **XFAULT**: L8 Makuhita plus `POKEBOT_KI118_FAULT_TYPEONLYFIRST=1` | identical to today's X: 0 planner calls, immediate box-first registration | a planner call |
| BF-15 | **WATTSON-F / WATTSON-OLD**: a boxed type-only Geodude; the Wattson cfg; the stand-in returns None | the fix registers the Geodude as the fallback after 1 planner call. The old code registers it at once with 0 planner calls. Either way the Ground pick is accepted | the Geodude never registered (Wattson broken) |
| BF-16 | **X13 STAGE2**: today's code (positive control) | after the heal withdraws the credible Makuhita L13, the T5 hopeless reading returns (False, []) | it reads (True, …) (then the stage-2 hopeless reading cannot discriminate) |
| BF-17 | fault arms **CONFIG** and **DERIV** | CONFIG ABORTs at the config check; DERIV ABORTs at the derivation premise | no ABORT |
| BF-18 | the gate: `run_gates.py`, and the existing `probe_r20_counterbox.py` | the full suite passes. `probe_r20_counterbox`'s C1 ("own type is enough") still passes: `box_counter_choice` is unchanged | a suite FAIL |
| BF-19 | an INDEPENDENT adversarial pass on the fix | no non-equivalent mutant of the fallback logic survives the driver plus gate rows | a survivor |

## What comes after the proof (the USER decides; superseded for the Norman fix by USER RULING 30 above)

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
