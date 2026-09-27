# 2026-09-27 — `#26-healmap-lavaridge` (Petalburg family): the Norman heal from the Rustboro side — PRE-REGISTERED PREDICTIONS

> Filed BEFORE any drive. Branch `wt/petaheal`. Mechanism: `ai-research-notes/2026-09-27-healwalk-RECON.md` (a NOTE).

## THE CHANGE UNDER TEST

`early_game.heal_at_petalburg()` replaces the Norman segment's `heal_in_pokemon_center(PokemonCenter.PetalburgCity)`.
- It tries the generic heal FIRST.
- Only on `HealWalkFailedError`, and only from a map in `PETALBURG_ROAD_MAPS` (the maps
  `travel_lavaridge_to_petalburg` walks from), does it take the fallback:
  1. release held input (KI-106);
  2. log `PETAHEAL: generic heal failed from map …`;
  3. run `travel_lavaridge_to_petalburg()`: Rustboro → Route 104 → Petalburg Woods → Petalburg;
  4. heal.
- Arm `POKEBOT_PETAHEAL_FAULT_GENERIC=1` re-raises (the old behaviour).

## THE DRIVE — `--driver petaheal`

1. Fixture: `norman_done.ss1` (PINNED, md5 `e6fb7d5f…`): PETALBURG_CITY (7,6), badges 1-5, party at 28% HP with 3
   fainted.
2. Heal in place with the generic heal. From Petalburg it works, and it lets the walk survive.
3. Walk (production `_navigate_riding_out`) to ROUTE116 (11,7). That is where 40 of the batch's 53 Norman heals
   began.
4. Stage the lead to 50% HP (test-only).
5. Run `heal_at_petalburg()`, bounded to 80,000 frames, recording every map it enters.

## PREDICTIONS

| # | Reading | FIX (default) | GENERIC arm (old behaviour) |
|---|---|---|---|
| P0 | PREMISE: healed in Petalburg, positioned on ROUTE116, lead staged below full | yes | yes |
| P1 | the heal raises | **no** | **yes**: `HealWalkFailedError` "… PetalburgCity is BLOCKED …", naming `RUSTBORO_CITY_FLAT1_1F` (the batch's 52-event shape) |
| P2 | maps entered include RUSTBORO_CITY_FLAT1_1F (the bounce) | yes, the generic attempt runs first | yes |
| P3 | a `PETAHEAL:` event is logged (the fallback ACTED) | **yes** | **no** |
| P4 | maps entered include PETALBURG_WOODS (the road) | **yes** | no |
| P5 | ends in PETALBURG_CITY with the lead at full HP | **yes** | **no** (ends in Rustboro) |
| P6 | CONTINUE: `calculate_path` from the end tile reaches the Petalburg Gym door (15,8), `do_petalburg_gym`'s first target | **yes** | (not graded) |

⇒ The driver prints `ACCEPTANCE: PASS` when P0 holds and P1–P6 match the arm's column (P2 is logged, not graded).

## FALSIFIERS, stated in advance

- **P0 false** (the walk to Route 116 fails, or the fixture whites out): VACUOUS, not a refutation.
- **GENERIC does not raise from ROUTE116 (11,7):** the batch's bounce does not reproduce post-Norman (the recon said
  the ranking does not depend on flags, but that was INFERRED). The fix is then unproven.
- **FIX raises, or ends outside Petalburg:** the road from Rustboro is not what the batch's recovery showed. The fix is
  wrong.

## WHAT THIS DOES NOT SHOW

- Frequency.
- The Route 117 origin (9 of 53), which reaches Rustboro through Verdanturf and Rusturf. The travel road covers it by
  its own ranking, but it is not driven here.
- The Fortree family.
- One trajectory per arm.
