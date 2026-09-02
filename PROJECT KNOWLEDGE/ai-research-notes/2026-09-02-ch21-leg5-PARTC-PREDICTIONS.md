# §Ch21 LEG 5 — PART C LIVE-PROBE: PRE-REGISTERED PREDICTIONS (filed BEFORE the drive)

> ‼ **THIS IS A NOTE, NOT TRUTH.** It exists so that the probe's readings are graded against
> predictions written down BEFORE the run (the §Ch20 cavern method) — a reading that contradicts a
> prediction is a RESULT, never a driver failure. Predictions come from `2026-09-02-ch21-leg5-RECON.md`
> (PART C) plus a 6-agent workflow (5 recon angles + 1 adversarial refuter, 2026-09-02, workflow
> `wf_e009f534-de4`). Where the refuter CORRECTED the recon, the correction is marked ⚠ and the
> reason cited. Nothing here is measured yet; the measurement is
> `--driver ch21leg5probe` on `post_rayquaza_gone.ss1` (md5 35cb5e6502fd613fb7460e27aa79fd68).

Driver: `tools/story-dev/story_harness.py --driver ch21leg5probe` (class `Ch21Leg5ProbeMode`).
Fixture premise (vacuity gate — the run is VACUOUS and says so if any conjunct fails):
`SKY_PILLAR_ENTRANCE (14,3)`, vars `SOOTOPOLIS_CITY_STATE=5 / SKY_PILLAR_STATE=1 /
SKY_PILLAR_RAYQUAZA_CRY_DONE=1`, `RECEIVED_HM_WATERFALL=False`, `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE=False`,
controllable.

---

## P0 — PREMISE + PRE-READINGS (no movement)

| reading | PREDICTION | source | grade |
|---|---|---|---|
| map/tile | `SKY_PILLAR_ENTRANCE (14,3)` | fixture row | gate |
| vars CITY/SKY/CRY | `5 / 1 / 1` | RECON A0 | gate |
| `RECEIVED_HM_WATERFALL` (0x138) | False | RECON A | gate |
| `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` (0x9E) | False | RECON A | gate |
| `KYOGRE_ESCAPED_SEAFLOOR_CAVERN` | True | decomp OnLoad | report |
| `LEGENDARIES_IN_SOOTOPOLIS` | **True** (the scene clears it — cheap scene-ran discriminator) | decomp FromDive tail | report |
| `SOOTOPOLIS_WALLACE_STATE` | 0 (⚠ refuter: Wallace's tile is (31,33) ONLY at 0) | scripts.inc:119-127 | report |
| `MET_MAXIE_SOOTOPOLIS` / `MET_ARCHIE_SOOTOPOLIS` | False / False | RECON A | report |
| `can_surf` precondition: `BADGE05_GET` ∧ party has Surf | True ∧ True (⚠ refuter: without it arm B degrades to PathFindingError and the A/B differs for the WRONG reason) | map_path.py:784-788 | gate |
| `BADGE07_GET` ∧ party has Dive | True ∧ True | leg 1/3 premise | gate |
| HM07 in bag (item index 345, `quantity_of`) | 0 | RECON A | report |
| lastHealLocation (SaveBlock1+0x1C, `<bbbxhh`) | `(0,7,-1,43,32)` = HEAL_LOCATION_SOOTOPOLIS_CITY — the PC (43,31) was entered on leg 3 (`setrespawn`) | RECON C gate 4 + decomp heal_locations | report; CONTROL: `+0x04 location` (group,num) == live map (0,?) SKY_PILLAR_ENTRANCE |
| party by PID | 6 tuples, HP ≥ 91% | fixture row | report |

## P1 — EXIT THE TOWER: ENTRANCE (14,3) → (6,15) → held-Down (6,16) → ROUTE131

| reading | PREDICTION |
|---|---|
| plan (14,3)→(6,15) | OK, every waypoint on ENTRANCE, **no waypoint at (14,4)** (the seam warp) — if (14,4) is in the plan the probe REFUSES to walk it |
| `navigate_to(ENTRANCE,(6,16))` | map becomes ROUTE131 (the leg-4 R-SEAM held-direction idiom) |
| rest tile after `wait_until_truly_controllable()` | **(36,7)** MB_SAND, facing Down, ON FOOT (⚠ refuter/decomp: (36,6) is the door target; the exit task walks ONE tile south). The resting-tile rule's second arrow/door-warp control. |
| `_route131_layout_reading()` at rest | `agree=False` — planner STATIC (seeded by P1's own `calculate_path` via `_get_all_maps_metadata`), live = SKY_PILLAR layout |

## P2 — GATE 1: THE ROUTE131 LIVE-PIN A/B (the queue's "FIRST")

Both arms call `calculate_path((ROUTE131, rest), (ROUTE126, (45,66)))`.

| arm | PREDICTION |
|---|---|
| **A** (static, as seeded) | path OK (~322 wp, leg 3's reverse); `surf_actions == 0`; first waypoint `is_water_tile=True` while the avatar is on foot on live SAND; static elevation of the rest tile = 1 (deep water) |
| **B** (after `_pin_planner_to_live_layout(ROUTE131)`) | `agree=True`; path OK; **exactly ONE `WaypointAction.Surf`** at the sand→ocean mount ((36,8)→(36,9)); first waypoint `is_water_tile=False`; live elevation of the rest tile = 3; live walls on the path = 0 |
| discriminator | arms DIFFER iff `surf_actions` differ ∨ live-wall counts differ ∨ the waypoint sequences diverge (first divergent index printed). ⚠ refuter: the live-WALL count alone is ZERO in both arms (ocean has collision 0) and would read INCONCLUSIVE forever — the Surf-action count is the value KI-73 hinges on (`map_path.py:916` seeds the source elevation from the LAYOUT). |
| optional live control `CH21_PROBE_NOPIN131=1` | skips the pin: `_navigate_riding_out(ROUTE126,(45,66),tries=2)` FAILS (`NavigationStuckError`/timeout) with the avatar still on ROUTE131 at (36,8) facing Down on foot — the walker holds Down into the ocean without pressing A for Surf (`walking.py:354-362`). A second run, not the main run. |

## P3 — THE RETURN SWIM + DIVE (pinned arm only)

| reading | PREDICTION |
|---|---|
| `_navigate_riding_out(ROUTE126, DIVE_TILE=(45,66), tries=30)` | arrives; battles logged with map + frame (⚠ refuter: swimmers on 131/129/128 are NOT proven beaten — each one is a ride-out, not a strand) |
| tile_type at (45,66) | one of the Deep-Water types leg 1 accepts |
| `dive()` → `navigate_to(UW_ROUTE126,(45,65),False)` | lands `UNDERWATER_SOOTOPOLIS_CITY` at **(9,8)** |
| `navigate_to(UW_SOOTOPOLIS,(9,7),False)` | at (9,7), tile_type 'Deep Water' |

## P4 — SURFACE + THE RAYQUAZA-ARRIVAL SCENE (one-shot #3 of the chapter)

| reading | PREDICTION |
|---|---|
| `surface_from_dive()` | map SOOTOPOLIS_CITY; ⚠ refuter: the city tile is **(29,53) for ANY UW tile** (`Underwater_SootopolisCity_OnResume: setdivewarp SOOTOPOLIS_CITY 29,53` — the fixed dive warp, NOT an (x,y)-preserving emerge). Reported as `(uw_tile, city_tile)`; the KI-72 wording in `sootopolis.py:222-230` is a doc bug to fix WITH the leg. |
| `_ride_summit_scene("SKY_PILLAR_STATE", 2)` returns | MID-SCENE at tile **(29,49)** (4× walk_up from (29,53)), script context ACTIVE, var == 2. ⚠ refuter CRITICAL: the var flips ~120 frames + one `warpwhitefade` BEFORE the scene ends, and `player_avatar_is_controllable()` is True under `lockall`, so `wait_until_truly_controllable()` returns in ~30 frames mid-scene (leg 1 measured the same, `sootopolis.py:128-130`). A tile/pin taken here is WRONG. |
| SETTLE (bounded 6000 frames): script inactive ∧ `SKY_PILLAR_STATE == 3` ∧ live `gMapHeader[:4]` == static NORMAL header ∧ controllable | reached; frames-to-settle recorded |
| rest tile / facing | **(29,53)** / Up (OnWarp `turnobject north`) |
| vars after | CITY 5, **SKY 3** (OnWarp promotes 2→3 on the reload; both variants rest at 3 — the VARIANT is graded on the tile, (29,53) dive vs (43,32) PokeCenter) |
| `LEGENDARIES_IN_SOOTOPOLIS` | **False** |
| `HIDE_SOOTOPOLIS_CITY_ARCHIE/MAXIE` | False / False (they are placed OUTSIDE the gym at state 5) |
| capture `CH21_CAPTURE_ARRIVAL=post_legends_calmed.ss1` | written only when the settle passed on (29,53) with SKY==3 |

## P5 — GATE 2: THE STATE-5 SOOTOPOLIS LAYOUT + THE HM07 NPCS (from the rest tile)

| reading | PREDICTION |
|---|---|
| `_pin_planner_to_live_layout(SOOTOPOLIS_CITY)` | **`changed=False`** — a NO-OP: the static header IS the NORMAL layout and after a correct settle the live header is NORMAL too (⚠ refuter LOW-7: never report this pin as a fix) |
| whole-map live-vs-static collision diff | **0 tiles** differ (⚠ refuter: OnLoad's gym-door/house-door `setmetatile`s are already collision 1 in static NORMAL; `SetRoughWater` metatiles are passable). Any nonzero count is a FINDING about the "DIRTY post-crisis layout" claim in HANDOFF:304-306. |
| RAM object templates (SaveBlock1+0xC70, 64×24 B, `localId u8@0, x s16@4, y s16@6, flagId u16@0x14`); CONTROL: exactly 18 non-zero localIds | Steven **7 @ (29,33)**, Maxie **16 @ (33,35)**, Archie **17 @ (34,35)**, Wallace **18 @ (31,33)** (`SetOutsideGymObjPos`, scripts.inc:114-127; local_id == template index, Steven=7 measured live 2026-08-27) |
| `get_map_objects()` from (29,53) | ⚠ refuter HIGH-3: NONE of the three are loaded (spawn window ≈ y ∈ [46,62]); the empty set is EXPECTED, not a finding |
| path matrix from the rest tile | (33,36) OK, (32,35) OK, (34,36) OK, (34,34) OK, (31,34) OK, (43,32) OK; **negative control (33,34) REFUSED** (live collision 1 — the control is only valid if `_live_collision_grid` reads it as 1; otherwise the probe picks another wall and SAYS so) |

## P6 — ONE WALK: rest → (33,36) (Maxie's south approach), then the loaded objects

| reading | PREDICTION |
|---|---|
| `_navigate_riding_out(SOOTOPOLIS_CITY,(33,36),tries=6)` | arrives, 0 live walls on the plan |
| `get_map_objects()` at (33,36) | local_id 16 @ (33,35), 17 @ (34,35), 18 @ (31,33), 7 @ (29,33) all LOADED |
| path matrix from (33,36) | (34,36) OK, (34,34) OK, (31,34) OK, (32,35) OK; (33,34) REFUSED |
| whiteouts | 0 |

## What this probe deliberately does NOT do
- No `A` press near any NPC (the talks are the LEG's one-shots; the probe measures the approach).
- No state-writes. No pin before the settle. No `navigate_to` without an outer frame budget.
- Gate 5 of the RECON ("ONE live-pinned plan stitches Entrance→Sootopolis") is UNSATISFIABLE as
  phrased (Sootopolis has no connections) and is replaced by the per-segment plans above.
