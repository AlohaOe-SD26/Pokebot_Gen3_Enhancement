# 2026-09-26 — `#26-ch24organic` GAP 4 (THE NO-FLY WALK-OFF GUARD) — PRE-REGISTERED PREDICTIONS (written BEFORE any drive)

> THE MEASURED DEFECT (observe-only run, prediction filed first — `evidence/2026-09-26-ch24gap4-OBSERVE-*`):
> a party with no Fly knower on the League plateau, `--driver ch24train` floor 50 from `post_league_shop`:
> Zigzagoon L19 / Castform L36 `no_ground`; **Wailord L47 walked through the (18,27) door into VICTORY_ROAD_1F's
> EXIT half and `train_team` raised `UnreachableDestinationError: Could not reach (15, 39) … still at (39, 5)`** —
> an unnamed crash inside a cave. The ground picker's oracle (`region_reach`) is MAP-level; the grind tile is in
> the cave's ENTRANCE half.
> THE FIX: in `train_one_for_league`, when `can_fly_to_anchor(heal_center)` is False (the bot will WALK), ask
> `calculate_path(here → (ground, tile))` first; a NO is a named `no_ground` (+ `unwalkable`), never a walk.
> Arm `POKEBOT_CH24_FAULT_NOWALKCHECK=1` (skip-the-fix). Driver `--driver ch24handoff` (production order),
> `POKEBOT_CH24_FAULT_NOFLYTEACH=1` so the party has no Fly, `CH24_HANDOFF_FLOOR=50`.

## DISCRIMINATOR (measured before the drive)
`post_league_shop.ss1` (`1564948368f6`) at EVER_GRANDE_CITY (18,6): no Fly knower; below L50: Zigzagoon L19,
Castform L36, Wailord L47, Swellow L48, Mightyena L48. Both arms identical except the pre-check.

| arm | env | prediction | falsifier |
|---|---|---|---|
| **G4** FIXED | `NOFLYTEACH=1` · floor 50 · `CH24_HANDOFF_EXPECT=refuse` | `ACCEPTANCE: PASS`; train report `unwalkable` lists Wailord, Swellow, Mightyena at VICTORY_ROAD_1F (15, 39); `no_ground` all five; NO battles; the bot never leaves EVER_GRANDE_CITY (18,6); R1 refuses naming all five below L50; door shut | any walk into VICTORY_ROAD_1F; a crash; a trainee trained |
| **G4-SKIP** `NOWALKCHECK=1` | as G4 + the arm | `ACCEPTANCE: FAIL`; failure `UnreachableDestinationError: Could not reach (15, 39) on MapRSE.VICTORY_ROAD_1F … (39, 5)`; final map VICTORY_ROAD_1F ⇒ **the pre-check is load-bearing** | G4-SKIP passes (then the walk never happened and the guard is decorative) |
| **G4-FLY** (unchanged path) | `post_league_shop` · floor 21 · teach ON (= H1 of the gap-3 note) | still PASS with `mode='fly'` — the guard never runs when Fly is available (`can_fly_to_anchor` True) | H1's result changes |
