# 2026-09-26 — `#26-ch24organic` GAP 3 (TEACH FLY IN PRODUCTION) + THE HAND-OFF CHAIN — PRE-REGISTERED PREDICTIONS (written BEFORE any drive)

> `ensure_fly_learner()` (new, `pokemon_league.py`) teaches HM02 from the bag when nobody knows Fly, to the
> highest-level COMPATIBLE member that still has a non-HM slot to spend (`ensure_waterfall_learner`'s rule),
> verified BY PID; it never raises for a missing learner or a missing HM02 — it reports and returns.
> Production wiring: `story_mode._play` latches §Ch24, calls `ensure_fly_learner`, then `train_for_league`.
> Driver `--driver ch24handoff` runs the SAME order as `_play` minus the gauntlet: latch → `ensure_fly_learner`
> → `train_for_league(floor)` → `prepare_and_open_the_league(floor)` (R1 → bridge → door) — and a gate pins
> `_play`'s order so the driver cannot drift from it. `HARNESS_EXIT_ON_MANUAL=1` on every drive.
> Arm: `POKEBOT_CH24_FAULT_NOFLYTEACH=1` (skip-the-fix: the teach is skipped). Driver env: `CH24_HANDOFF_FLOOR`
> (default 21), `CH24_HANDOFF_EXPECT=door|refuse`. Gate `probe_ch24_flyteach.py` (static) already PASSES —
> including its fault arms (a level-only picker; a `_play` that teaches after training).

## DISCRIMINATOR (measured on the fixture before the drive)
`post_league_shop.ss1` (`1564948368f6`): EVER_GRANDE_CITY (18,6); NO party member knows Fly; Swellow#0B30A747
L48 `canLearnFly=True` (the only compatible member), moves Peck 35 / Wing Attack 60 / Aerial Ace 60 / Quick Attack
40 (no HM); HM02 in the bag; at floor 21 the only trainee is Zigzagoon#33CB74C3 L19; basket full.
⇒ the two arms differ in exactly one input: whether a Fly knower exists when `train_for_league` picks a ground.

| arm | env | prediction | falsifier |
|---|---|---|---|
| **H1** HAND-OFF (teach) | floor 21 | Swellow#0B30A747 learns Fly and loses **Peck** (lowest base power, not an HM); Zigzagoon L19 → ≥ L21 on a ground reached BY FLY (a `rungs` entry with `finished=True`); the bridge FLIES back to EVER_GRANDE_CITY (18,6) (`mode='fly'`); R1 passes (`E1-READY`); the door opens (`E1-AT-DOOR`) — `ACCEPTANCE: PASS`, 0 whiteouts | no teach; a different learner or lost move; `no_ground`; the bridge walks or refuses; any missing reading |
| **H0** CONTROL (`NOFLYTEACH=1`) | floor 21 | no teach; Zigzagoon `no_ground` (nothing walkable from the plateau that a L19 out-levels — Victory Road 1F's band 36-40 is excluded by `max_wild_max = level + 1`); the bot never leaves (18,6); **R1 REFUSES**: `1 mōn below the L21 floor: Zigzagoon#33CB74C3 L19`; door shut ⇒ **the teach is what makes the climb possible** | Zigzagoon trains anyway (then walkable ground exists and gap 3 is not the blocker for this party) |
| **K** ALREADY-KNOWN (vacuity) | `post_ch24ready` (`cf383b5b2567`; Swellow knows Fly; (27,49)) · floor 21 | `fly_teach='already'`, no teach menu; the rest as H1 (it starts at (27,49), so the bridge flies) | a teach attempted on a party that already flies |
