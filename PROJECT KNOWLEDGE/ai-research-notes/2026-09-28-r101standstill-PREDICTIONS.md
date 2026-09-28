# 2026-09-28 — `#27-r101standstill` (the Surf-learner hunt stands still on Route 101): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any fix. Recon: a 4-angle workflow (logs, code, map, adversarial), a NOTE:
> `ai-research-notes/2026-09-28-r101standstill-RECON.md`. **Verified by me in our own harness** (the bot's `get_map_data`
> on `norman_done.ss1`):
> - `ROUTE101 (9,9)` is `tile_type='Normal'`, `has_encounters=False`;
> - `(12,10)`, `(12,11)`, `(13,9)`, `(13,10)` and `(14,10)` are `Tall Grass`, and all path both ways to the travel
>   waypoint `(9,9)`, the south end `(10,19)` and the north end `(11,0)`.

## THE MECHANISM (the recon, CONFIRMED by two or more angles; the drive tests it)

1. `ensure_hm_learner(HM03)` runs right after the Surf handoff, while the player is INSIDE Wally's house
   (`PETALBURG_CITY_WALLYS_HOUSE (8,0)`; 185/185 batch episodes).
2. Its "prefer a reachable ground" check calls `calculate_path`, which does not cross warps. From an interior EVERY
   candidate fails, so the fallback takes `grounds[0]` = `TRAINING_GRASS`'s `ROUTE101 (9,9)`.
3. That row's tile is the travel waypoint (`# tile used by travel_to_route103()`), NOT grass. The spin can never roll
   an encounter (0 battles in 204 episodes), and the global 18,000-frame watchdog fires first.

## THE FIX (planned)

- (a) The `ROUTE101` row uses `(12,10)` (verified above). The hard-coded travel waypoints stay `(9,9)`: they do not
  read the table.
- (b) `_hm_hunting_grounds` keeps a ground only if its spin tile rolls LAND encounters. This also drops the three
  `TRAINING_GRASS` rows on OCEAN WATER (Routes 115, 118, 119), which a land-species HM hunt could never succeed on.
- (c) After `_navigate_riding_out`, the hunt ASSERTS that the tile under the player rolls land encounters. If not, it
  raises a named `BotModeError` instead of spinning to the watchdog.
- (d) A ROM gate over every `TRAINING_GRASS` row and the named spin constants: the tile must roll encounters. With a
  separating control.
- Fault arm `POKEBOT_R101_FAULT_OLDTILE=1`: restores `(9,9)` and skips (b), so (c) must fire.

## THE DRIVE — `--driver r101hunt` on `norman_done.ss1` (`e6fb7d5f36db`), `--set-balls 20`

Premises, read at load (a false premise = VACUOUS):
- PETALBURG_CITY `(7,6)` outdoors;
- no party mon can learn Surf (all five checked offline: False);
- party 5 < 6.

Arm INDOOR: the driver steps Up into Wally's house (premise: map `(8,0)`), then runs `ensure_hm_learner(HM03)`.
Arm OUTDOOR: the same, without entering. Readings (rule 7): the `(map, tile)` actually passed to
`_navigate_riding_out`, the tile type under the player when the spin starts, the battles during the spin, and the exit
(a slot, or the raised text). Each arm is bounded at 20,000 frames from the spin's start.

| Arm | Unfixed | Fixed | Fixed + `POKEBOT_R101_FAULT_OLDTILE=1` |
|---|---|---|---|
| INDOOR | ground `ROUTE101 (9,9)`; spin tile `Normal`; **0 battles in 20,000 frames**; no exit within the bound | ground `ROUTE101 (12,10)`; spin tile `Tall Grass`; **≥1 battle** within 20,000 frames | ground `ROUTE101 (9,9)`; a named `BotModeError` ("… cannot roll a wild encounter …") within 600 frames of arrival; 0 battles |
| OUTDOOR | a ground other than ROUTE101 (9,9) (the recon predicts `ROUTE103 (5,7)`); `Tall Grass`; ≥1 battle | same as unfixed | (not run) |

## FALSIFIERS

- Unfixed INDOOR picks any ground but `ROUTE101 (9,9)`: the fallback mechanism is wrong. STOP.
- Unfixed INDOOR gets any battle on `(9,9)`: the tile claim is wrong. STOP.
- Unfixed OUTDOOR also picks `ROUTE101 (9,9)`: the "indoors defeats the check" claim is wrong.
- Fixed INDOOR gets 0 battles on a `Tall Grass` tile in 20,000 frames: something beyond the tile suppresses
  encounters (a Repel, a script).
- The fault arm spins without raising: guard (c) is dead.

## WHAT THIS DOES NOT SHOW

- That a Surf learner gets CAUGHT: Zigzagoon is about 10% of Route 101's slots, so catching is a frequency question.
- The separate P4r1/P4r7 fast-fail ("Could not reach (9, 9) … still at (10, 29)"). It is a provisioning and routing
  bug on Route 104 and is filed separately.
- Whether the three ocean rows are right for TRAINING (not HM hunts). They are gated "surf" in the capability table,
  so they may be deliberate; that is a question, not a finding.
