# §Ch21 LEG 5 — PART C LIVE-PROBE: RESULTS, GRADED AGAINST THE PRE-REGISTERED PREDICTIONS

> ‼ **THIS FILE IS MEASUREMENT, NOT RECALL** — unlike its two companions it reports what a live
> emulator did, so it OUTRANKS the RECON note wherever they disagree. Each row is graded against
> `2026-09-02-ch21-leg5-PARTC-PREDICTIONS.md`, which was committed BEFORE the drive.
> Driver `--driver ch21leg5probe` (`story_harness.py`), fixture `post_rayquaza_gone.ss1`
> (md5 `35cb5e6502fd613fb7460e27aa79fd68`, asserted by `verify_fixtures.py` before the run).
> Evidence: `evidence/2026-09-02-ch21leg5probe-MAIN.txt`, `-MAIN-run1.txt`, `-NOPIN131.txt`.

**VERDICT: `ACCEPTANCE: PASS`, probes P0–P6 all executed, `whiteouts=0`, `frames=16297`,
`encounters=7` (all fled).** The pin gate is settled, the arrival is settled, the NPC geometry is
settled, and the leg's remaining unknowns are named at the bottom.

⛔ **RUNS 1 AND 2 ARE ONE TRAJECTORY REPLAYED, NOT A REPLICATION.** Both produced `frames=16297`
and a byte-identical encounter list. That is a DETERMINISM check (house rule 8); it says nothing
about how the leg behaves on a different party, a different RNG, or after a lost battle.

---

## 1. WHAT HELD (predicted, and measured exactly)

| reading | measured |
|---|---|
| P0 premise: ENTRANCE (14,3), vars 5/1/1, controllable | ✅ |
| P0 flags: HM_WATERFALL F, 0x9E F, KYOGRE_ESCAPED T, LEGENDARIES T, MET_* F, WALLACE_STATE 0 | ✅ all |
| P0 `can_surf`/`can_dive` preconditions (BADGE05+Surf, BADGE07+Dive) | ✅ True×4 — the A/B is not degraded |
| P0 HM07 index 345, qty 0 | ✅ |
| P0 lastHealLocation `(0,7,-1,43,32)` | ✅ **exact** — Sootopolis PC, set by leg 3's `setrespawn` |
| P0 location-control `(+0x04)` == live map | ✅ `(24,77)` both sides |
| P1 plan (14,3)→(6,15): all on ENTRANCE, **no (14,4)** | ✅ 20 wp, `seam_14_4_at=[]` |
| P1 rest after the (6,16) door: **(36,7)**, facing **Down**, **OnFoot** | ✅ **exact** (the resting-tile rule's 2nd arrow-warp confirmation) |
| P2 planner/live disagree before the pin | ✅ `planner=0x08417FE4 live=0x0845C1B0 agree=False` |
| P2 source-tile elevation **1 → 3** across the pin | ✅ **exact** — this is the value `map_path.py:916` seeds the start node from |
| P2 arm B: 0 live walls on the ROUTE131 leg, first waypoint NOT a water tile | ✅ |
| P3 UW arrival (9,8); emerge tile (9,7) `'Deep Water'` | ✅ |
| P4 mid-scene tile **(29,49)**, script ACTIVE | ✅ **exact** |
| P4 rest **(29,53)**, facing **Up**, vars **5/3/1**, `LEGENDARIES_IN_SOOTOPOLIS` **False** | ✅ **exact** |
| P5 Sootopolis pin is a **NO-OP** (`0x083E6A04 -> 0x083E6A04`) | ✅ — and it must never be reported as a fix |
| P5 templates: 18 entries, ids 1..18; control id2 = (47,33) ⇒ **no MAP_OFFSET** | ✅ |
| P5 **Steven 7 @ (29,33), Maxie 16 @ (33,35), Archie 17 @ (34,35), Wallace 18 @ (31,33)** | ✅ **all four exact** — `SetOutsideGymObjPos` confirmed LIVE for the first time |
| P5 `get_map_objects()` from the rest tile lists NONE of them | ✅ (spawn window; an empty list here is not a finding) |
| P5 negative control (33,34): live collision 1 AND planner REFUSES | ✅ both |
| P5/P6 path matrix: (33,36) 21wp, (32,35) 21, (34,36) 22, (34,34) 24, (31,34) 21, (43,32) 37 | ✅ all OK |
| P6 walk to (33,36): 0 live walls, arrives, **all four NPCs loaded on their template tiles** | ✅ |

## 2. WHAT WAS REFUTED (the predictions that were WRONG — and what replaces them)

**R1 — ⛔ `get_map_data_for_current_position()` IS NOT A LIVE READER ONCE THE CACHE IS POISONED.**
Predicted the ROUTE131 rest tile would read as sand; it read **`tile_type='Deep Water'`** while the
avatar stood on it ON FOOT. Cause: that function builds its `MapLocation` from the live
`gMapHeader`, but `MapLocation._map_layout` resolves through the **shared**
`modules.map._map_layout_cache` (map.py:745-755), which P1's own `calculate_path` had already
seeded STATIC for ROUTE131. ⇒ **KI-73's blast radius includes the function whose NAME promises the
opposite.** The only trustworthy live tile oracle remains `_live_collision_grid`
(`gBackupMapLayout`). *A `tile_type` guard on a swapped map is worthless until that map is pinned.*

**R2 — the static arm does not mis-plan the swim; it CANNOT PLAN IT AT ALL.**
Predicted ~322 waypoints with 0 Surf actions. Measured: `PathFindingError: Could not find a path
from (36/7 @ ROUTE131) to (45/66 @ ROUTE126)`. Arm B (pinned) returns **356 wp with 3 Surf
actions** (indices 3, 225, 244 — the swim dismounts and remounts twice), 0 live walls.
⇒ the discriminator fired harder than designed, and **3 Surf actions, not 1**, is the real shape of
the return route.

**R3 — the control arm refines where the un-pinned run dies.** Predicted a walk that jams at the
water's edge (36,8). Measured (`CH21_PROBE_NOPIN131=1`): it never moves at all —
`UnreachableDestinationError ... we are still at (36,7) ... Cannot reach ROUTE126: it is not
walkable from ROUTE131`. ⇒ **the pin is load-bearing, proven by an arm with it REMOVED** (house
rule 8), and the failure is a PLANNING failure, not a walking one.

**R4 — `player_avatar_is_controllable()` read FALSE mid-scene, not True.** The settle is still
required, and for the reason that survived: `SKY_PILLAR_STATE` reaches 2 **309 frames before** the
scene ends and before the `warpwhitefade` lands. A var-keyed return is early no matter what the
controllable bit says. `SETTLE ok=True frames=309`.

**R5 — the state-5 Sootopolis layout diff is 10 tiles, not 0 — AND IT IS HARMLESS.** All ten are
`static=1 -> live=3`: **wall to the planner AND wall to the game.** The dangerous direction,
open-to-planner/wall-live, is **0 of 3600 tiles**.
⇒ **This retires the open question in `04-HANDOFF.md`** ("the SOOTOPOLIS layout at state 5 is the
DIRTY/post-crisis one and has NOT been measured"): at `SOOTOPOLIS_CITY_STATE=5` with
`SKY_PILLAR_STATE=3` the live header is the map's own NORMAL layout, the pin is a no-op, and
nothing can strand a walk. ⛔ Note the discipline: **the COUNT alone would have read as a scare**;
only the per-tile DIRECTION answers the question that matters.

## 3. WHAT WAS MEASURED THAT NOBODY HAD PREDICTED

**N1 — ⛔⛔ KI-72's WORDING IS A DOC BUG, AND THE PROBE PROVES IT.** `sootopolis.py:25-32` says
*"`Emerge` preserves (x,y), so the underwater tile IS the city tile"*. Measured: surfacing from UW
**(9,7)** landed at city **(29,53)**. `Underwater_SootopolisCity_OnResume` runs
`setdivewarp MAP_SOOTOPOLIS_CITY, 29, 53` — a FIXED destination. The leg-1 hard-coded tile is still
correct (for a different reason: it is the tile the game's own dive warp expects), but the stated
REASON is false and would mislead anyone routing a different emerge point.

**N2 — THE BOT RESTS SURFING.** Avatar flags at the (29,53) rest are
`AvatarFlags.Surfing|Controllable`, not `OnFoot`. (29,53) is water; the `warpwhitefade` puts you
back on it mounted. ⇒ leg 5 must not assume an on-foot avatar after the arrival scene.

**N3 — the capture overwrite guard fires.** Run 2 printed `CAPTURE REFUSED - post_legends_calmed.ss1
exists`, which is the guard doing its job on an unforced re-run.

## 4. THE FIXTURE THIS PRODUCED

`tools/story-dev/saves/post_legends_calmed.ss1`, md5 **`68e78a663a01b9f9cb5be1795bec5bf0`**,
independently verified by `probe_anchor_inventory.py`: `OVERWORLD SOOTOPOLIS_CITY (29,53)`,
badges 1-7, party 6 at 629/694 (**91%** — still no Poke Center since Sootopolis), and by the
driver's own readings `SOOTOPOLIS_CITY_STATE=5`, `SKY_PILLAR_STATE=3`, `LEGENDARIES_IN_SOOTOPOLIS`
CLEAR, `RECEIVED_HM_WATERFALL` unset, `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` unset. It is the cheap
iteration point for the HM07 half of leg 5 — the arrival one-shot is already spent on it.

## 5. THE HM07 CHAIN, READ OUT OF THE DECOMP (`SootopolisCity_EventScript_*`)

⛔ This is the half PART C did NOT execute (the probe presses `A` at no NPC). It is decomp-exact and
must still be PROVEN by the leg's own drive.

1. **Either leader first — the order does not matter.** `Maxie` (local_id 16) and `Archie` (17)
   each `lockall`, require `VAR_SOOTOPOLIS_CITY_STATE == 5`, set their own `MET_*` flag, and then
   `goto_if_set` the OTHER's flag. So the FIRST talk just sets a flag and releases.
2. **The SECOND talk falls into `MaxieArchieLeave`**, which sets `HIDE_MAXIE`, `HIDE_ARCHIE` and
   **`SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` (0x9E)**, clears the two Mt. Pyre hide flags, sets
   `VAR_MT_PYRE_STATE = 2`, and then — ⛔⛔ **`warpsilent MAP_SOOTOPOLIS_CITY, 31, 34`**.
   **THE PLAYER IS TELEPORTED.** After the second leader talk the bot is NOT where it was standing;
   it is at **(31,34)**, one tile SOUTH of Wallace, and a same-map warp is a MAP RELOAD (OnLoad /
   OnTransition re-run). ⇒ the leg must RE-READ its position and re-settle here, never assume.
   *(The probe measured (31,34) as reachable in 21 wp from the rest tile, so the tile is real and
   routable — but the leg does not walk there, the game puts it there.)*
3. **Wallace** (local_id 18 @ (31,33)) then hits `GiveWaterfall` — its guard is exactly
   `state != 4` ∧ `RECEIVED_HM_WATERFALL` unset ∧ **`SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` SET**:
   `giveitem ITEM_HM_WATERFALL` → `setflag FLAG_RECEIVED_HM_WATERFALL`.
4. ⛔ **WALLACE'S POST-GIFT MOVE BRANCHES ON `VAR_FACING` — THE PLAYER'S OWN FACING — AND HAS NO
   SOUTH CASE.** NORTH/EAST → he walks RIGHT and `SOOTOPOLIS_WALLACE_STATE=1`; WEST → he walks LEFT
   and state 2; **SOUTH → neither branch fires, he does not move, and the state stays 0.** He is
   standing ON the gym door, so "he moves aside" is the point. Approaching from (31,34) and facing
   **Up** takes the NORTH branch ⇒ predict Wallace at **(32,33)** and `WALLACE_STATE=1`.
   ⇒ **the leg must talk to Wallace from the SOUTH tile the game itself warped it to.**

## 6. WHAT PART D STILL HAS TO PROVE (nothing below is measured)

* the three talks actually fire from those tiles, in that order, with the project's gated-button
  idiom (`A` only when a printer waits) — and the `warpsilent` between talk 2 and talk 3;
* `RECEIVED_HM_WATERFALL` SET **and** HM07 present in the bag by ITEM ID (a flag alone is the
  §Ch15/18/19 shape — corroborate with `quantity_of`), plus POSITION and a live can-continue path;
* the resume/phase selector on POSITION **and** state together, branching on `0x9E`;
* the fault arms, each of which must FAIL for its own named reason.
