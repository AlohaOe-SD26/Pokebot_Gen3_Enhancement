# §Ch22 PART A — LIVE PROBE: PRE-REGISTERED PREDICTIONS (filed BEFORE the drive)

> ‼ **A NOTE, NOT TRUTH.** Filed before `--driver ch22probe` runs, so its readings are graded against
> predictions rather than rationalised after (the §Ch20 cavern method). Sources: the decomp recon
> `2026-09-02-ch22-juan-BUILD-SPEC.md` and a static verification I did myself. **Nothing here is
> measured yet.** A reading that contradicts a prediction is a RESULT, never a driver failure.
> Fixture: `post_hm07.ss1` (md5 `bc3686118ac70a9aa1aa6501618adbac`).

## WHY THIS PROBE EXISTS

Three things block §Ch22 and none can be settled on paper:
1. **Can we even SEE the ice floor?** `_live_collision_grid` provably cannot (verified statically:
   the gym's `setmetatile`s pass `FALSE`, so collision bits never change). A new
   `_live_metatile_grid` should. ⇒ **P3 is an empirical A/B of that blindness**, not another
   argument about it.
2. **Is the ice puzzle really exact cover** — 64 thin-ice tiles in sections of 7/19/38?
3. **What does the bot actually own** — money, Potions, Revives — for the readiness problem?

## P0 — PREMISE + INVENTORY (no movement)

| reading | PREDICTION |
|---|---|
| map/tile | `SOOTOPOLIS_CITY (31,34)` |
| `BADGE08_GET` | **False** (else the run is vacuous and says so) |
| party | 6 alive, **629/694 (91%)**, lead Swellow 52/115 — ⛔ NOT the fainted 25/115 party, which belongs to a different run |
| money | **UNPREDICTED — this is one of the numbers the probe exists to get** |
| Potions / Revives / Full Heals | recon says 1 / 0 / ? — REPORTED, and I have not verified it myself |

## P1 — HEAL

| reading | PREDICTION |
|---|---|
| `heal_in_pokemon_center(PokemonCenter.SootopolisCity)` → (43,31) | returns; every party PID present and `hp == total` (**PID-keyed**, never a count) |
| rest tile after the heal | UNPREDICTED — reported; the PC exit tile has never been measured on this map |

## P2 — ENTER THE GYM

| reading | PREDICTION |
|---|---|
| path to the gym apron (31,32) | OK (MEASURED 2 wp from (31,34) during §Ch21) |
| entering | map becomes `SOOTOPOLIS_CITY_GYM_1F` |
| arrival tile | ~(8,25); REPORTED, not asserted — the game owns the landing tile |
| `ICE_STEP_COUNT` on arrival | **1** (`OnTransition` does `setvar VAR_ICE_STEP_COUNT, 1`) |

## P3 — ⛔ THE HEADLINE: IS THE COLLISION READER BLIND HERE? An empirical A/B.

| reading | PREDICTION |
|---|---|
| thin-ice tiles (metatile `0x20D` or `0x215`) on 1F | **64**, in three sections of **7 / 19 / 38** |
| locked stairs (`0x20F`) present | yes — that is what makes the sections one-way |
| live-vs-static **METATILE** diff *at entry* | **0** (nothing has been stepped on yet — the map starts in its base state) |
| live-vs-static **COLLISION** diff *at entry* | **0** |
| **then step ONCE onto a thin-ice tile** (derived from the grid, never hardcoded) | |
| live-vs-static **METATILE** diff *after the step* | **≥ 1** — the stepped tile becomes cracked (`0x20E`) |
| ⛔ live-vs-static **COLLISION** diff *after the step* | ⛔ **STILL 0 — THIS IS THE PROOF.** The floor demonstrably changed, and the collision reader cannot see it. If this reads 0 while the metatile diff is ≥1, then `probe_live_mapgrid.py` would PASS on a broken model, empirically and not just by argument. |
| `ICE_STEP_COUNT` after the step | **2** |

⛔ **FALSIFIER:** if the collision diff is also ≥1, my static analysis was wrong, the collision
reader is NOT blind here, and the KI-73 entry I wrote today needs correcting. That is a RESULT.

## P4 — IS THE PLANNER BLIND TOO?

| reading | PREDICTION |
|---|---|
| `calculate_path(entrance → Juan's tile (8,3))` | **SUCCEEDS** and returns a short straight walk up column x=8 — i.e. the planner proposes a route through locked stairs and un-walked ice. ⇒ the planner cannot be trusted inside this gym, and the route must be a table. |
| live **walls** on that proposed path | **0** (collision is 0 everywhere on the column) — another way of showing the collision oracle is useless here |

## P5 — LEAVE, AND CONFIRM THE PUZZLE RESETS

| reading | PREDICTION |
|---|---|
| walk back out to `SOOTOPOLIS_CITY` | OK |
| re-enter, read `ICE_STEP_COUNT` | **1** again, and the metatile diff back to **0** — `ClearTempFieldEventData()` wipes the visited bitmask on every map change and `OnTransition` resets the counter ⇒ **every entry gets virgin ice**, which is what makes a precomputed route table safe |

## ACCEPTANCE

P0–P5 each executed to a reading, `whiteouts == 0`, and the run ends back on `SOOTOPOLIS_CITY` with
a live path to the gym apron. ⛔ **The grade must NOT include "the predictions were right"** — this
is a measurement, and the ice-count/section numbers are exactly the sort of thing recon gets wrong.

## WHAT THIS PROBE DELIBERATELY DOES NOT DO
- It does not walk the puzzle, fight anyone, or approach Juan.
- It takes **exactly one** ice step, and only to prove the blindness A/B. The puzzle resets on exit,
  so this is fully reversible.
- It writes no state and captures no fixture.
