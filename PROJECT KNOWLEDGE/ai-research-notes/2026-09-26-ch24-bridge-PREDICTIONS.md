# 2026-09-26 — `#26-ch24organic` GAP 2 (THE RETURN BRIDGE) — PRE-REGISTERED PREDICTIONS (written BEFORE any drive)

> `return_to_league_door()` (new, `pokemon_league.py`) runs inside `prepare_and_open_the_league` AFTER R1 and
> BEFORE "GET INSIDE": no-op in the lobby / on (18,6); WALK when Ever Grande's plateau connects us to (18,6)
> without crossing the Victory Road return trap (18,27); otherwise step out of Victory Road if inside, check
> Fly's preconditions BY NAME, fly to the Pokémon League and ASSERT THE TILE (18,6) (`fly_to_destination`
> only asserts that the bot moved). Arms read in production: `POKEBOT_CH24_FAULT_NOBRIDGE=1` (skip-the-fix),
> `POKEBOT_CH24_FAULT_BRIDGEDEST=1` (fly to Lilycove — the tile assert must fire). Branch `wt/ch24organic`.
> Driver `--driver ch24entry` with `CH24_ENTRY_EXPECT_BRIDGE=<mode>` (enter grade) or
> `CH24_ENTRY_EXPECT=refuse-bridge:<noflyer|wrongtile>`; every drive uses `HARNESS_EXIT_ON_MANUAL=1`.

## THE DISCRIMINATOR, MEASURED BEFORE THE DRIVE (`probe_ch24_readiness_inputs.py`)

| fixture (md5) | position | Fly knower | LANDMARK_POKEMON_LEAGUE | ENTERED_ELITE_FOUR | below at the arm's floor | basket |
|---|---|---|---|---|---|---|
| `post_ch24ready.ss1` (`cf383b5b2567`) | EVER_GRANDE_CITY **(27,49)** — the SOUTH half | Swellow (knows Fly) | True | False | floor 19 → 0 | 30/3/8/3 full |
| `post_e4ice_FINAL.ss1` (`ebfafa71fa99`) | **VICTORY_ROAD_1F (15,39)** (Fly illegal) | Swellow L75 | True | False | floor 19 → 0 | 37/3/18/3 full |
| `post_league_shop.ss1` (`1564948368f6`) | EVER_GRANDE_CITY **(18,6)** | none | True | False | floor 19 → 0 | full |
| `post_ever_grande.ss1` (`18203e997edc`) | EVER_GRANDE_CITY **(18,42)** (south half) | **none** | **False** | False | floor 1 → 0 | **empty** |
| `post_vr_exit.ss1` (`0ad243164fd6`) | EVER_GRANDE_CITY **(18,28)** — the NORTH plateau, one tile below the (18,27) trap | none | False | False | floor 1 → 0 | **empty** |

## PREDICTIONS

| arm | fixture · env | prediction | falsifier |
|---|---|---|---|
| **T1** FLY-FROM-SOUTH | `post_ch24ready` · floor 19 · `EXPECT_BRIDGE=fly` | `ACCEPTANCE: PASS`; bridge `start=((0, 8), (27, 49))`, `walk_refused` set (no path to (18,6) from the south half), `mode='fly'`, fly `arrived=((0, 8), (18, 6))`, `B-POSITIONED`; then all five `E1-*` + `T-CONTINUE` | a walk succeeds (the south↔north NO PATH finding would be wrong); a landing ≠ (18,6); any missing `E1-*` |
| **T2** FLY-FROM-VICTORY-ROAD | `post_e4ice_FINAL` · floor 19 · `EXPECT_BRIDGE=fly` | `ACCEPTANCE: PASS`; `stepped_out=True` (VR1F → EG (27,49)), then `mode='fly'` → (18,6), `B-POSITIONED`, entry completes | the step-out fails; Fly refused as illegal; a landing ≠ (18,6) |
| **V** ALREADY-THERE (vacuity) | `post_league_shop` · floor 19 · `EXPECT_BRIDGE=already` | `ACCEPTANCE: PASS`; `mode='already'`, NO `fly` sub-report — the bridge spends nothing on a party already at the door (this is R1's arm C plus the bridge conjunct) | any flight or walk |
| **F1** NO-FLYER | `post_ever_grande` · floor 1 · `POKEBOT_CH24_FAULT_NOREADY=1` (R1's empty-basket refusal disarmed so the bridge is reached) · `EXPECT=refuse-bridge:noflyer` | `ACCEPTANCE: PASS`; `§Ch24 bridge: cannot return to the League door from EVER_GRANDE_CITY (18, 42) — … flying back is impossible: no party member knows Fly; the Pokémon League was never visited (LANDMARK_POKEMON_LEAGUE is unset)`; `flag_final=False`; `E1-INSIDE` absent | a flight attempted; the refusal missing either named reason; a walk "succeeds" |
| **F2** WRONG-TILE | `post_ch24ready` · floor 19 · `POKEBOT_CH24_FAULT_BRIDGEDEST=1` · `EXPECT=refuse-bridge:wrongtile` | `ACCEPTANCE: PASS`; the flight lands in LILYCOVE_CITY (`fly_to_destination` itself accepts it: `moved=True`), then `§Ch24 bridge: expected to stand on EVER_GRANDE_CITY (18, 6) … but we are at LILYCOVE_CITY (…)`; `flag_final=False` | the bridge accepts the landing (the assert is dead); `fly_to_destination` refuses Lilycove as unvisited (then the arm tests nothing — inconclusive) |
| **NB** SKIP-THE-FIX | `post_ch24ready` · floor 19 · `POKEBOT_CH24_FAULT_NOBRIDGE=1` · `EXPECT=enter` | `ACCEPTANCE: FAIL`; failure at GET INSIDE — either `tried to enter the League but we are at …` (the held Up walks into the Poké Center door (27,48)) or an exception from the unreachable door-apron walk; `E1-INSIDE` absent; `flag_final=False` ⇒ **the bridge is what gets this party to the door** | NB PASSES (then (18,6) IS walkable from (27,49) and the bridge is unnecessary for this start) |

| **W** WALK (the north plateau) | `post_vr_exit` · floor 1 · `NOREADY=1` (its basket is empty) · `EXPECT_BRIDGE=walk` | bridge `mode='walk'`, `plan_wp` > 0, NO `walk_refused`, NO `fly`, `B-POSITIONED` at (18,6) — the planner's route avoids the (18,27) trap one tile north; the entry then continues. ⚠ `ACCEPTANCE: FAIL` is EXPECTED and must be for ONE reason only: `missing=['E1-READY']` (R1 is disarmed by design) | `mode` ≠ walk; the trap guard refuses; any OTHER missing reading or a failure |

**G (static gate `probe_ch24_bridge.py`):** B1 R1 < bridge < first door walk/warp/press; B2 a TILE assertion after
every walk/flight; B3 both bounded by `_yield_bounded_by_frames`; B4 both arms read + registered; three built-in
fault arms turn it red. ✅ Already PASS on the unrun code (static).

## WHAT THIS WILL NOT SETTLE
* Whether ORGANIC parties have a flyer (13 of 30 did not — gaps 3 and 5) or walk off the plateau with none (gap 4).
* The WALK branch is exercised only from (18,28) (arm W) — one plateau start, with R1 disarmed.

## ADDENDUM (after the code review's KICK-BACK, BEFORE the re-run) — the regression arm it asked for

The review found `BRIDGE_READINGS` SHADOWED by `enter_the_league`'s constant of the same name (renamed
`RETURN_BRIDGE_READINGS`, imported by the harness; gate B5 now refuses any duplicate `*_READINGS`), and that no arm
re-drove the PROVEN chain that also calls `prepare_and_open_the_league`. All seven arms above are re-run on the
fixed code, plus:

| arm | fixture · env | prediction | falsifier |
|---|---|---|---|
| **RG** REGRESSION — `--driver ch24bridge` (leg 1 → `enter_the_league` → beat SIDNEY) | `post_ch24_atdoor_L75.ss1` (`8b8cd907db09`) · its default `CH24_ENTRY_FLOOR=1` | `ACCEPTANCE: PASS` exactly as on 2026-09-25; the entry leg's new `bridge` sub-report reads `mode='already'` (the fixture stands on (18,6)); R1 passes (L75×4 + L19/L36 ≥ floor 1; basket 37/3/18/3) | any FAIL; the bridge flying or walking; R1 refusing |
