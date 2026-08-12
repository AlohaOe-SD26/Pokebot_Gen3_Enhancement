# Known-Issues Archive
> APPEND-ONLY history. Superseded write-ups of issues that are now resolved live here, so
> `05-KNOWN-ISSUES.md` can stay a CURRENT-STATE file within its line budget (CLAUDE.md rule R3).
> Nothing here is deleted — a wrong cause that was expensive to disprove is evidence, and this
> project treats negative results as its most valuable asset.


## Archived 2026-08-12 — KI-58's three superseded write-ups (the Mossdeep Gym)

These are the ORIGINAL entry and its two corrections, written before the puzzle was understood.
They are kept because they are the record of three confidently-wrong causes on one issue, and the
lessons drawn from them are in `08-MISTAKES.md`. The CURRENT state of KI-58 — resolved, modelled and
validated — is in `05-KNOWN-ISSUES.md`.

## KI-58 — the MOSSDEEP GYM is not a warp-event maze; its tiles are `MB_MOSSDEEP_GYM_WARP` (2026-08-12, severity: MEDIUM, blocks §Ch18, MEASURED)

Found while reconning §Ch18 with the newly generalised `probe_warp_maze.py`. The gym *looks* like
the two hideouts — `MossdeepCity_Gym/map.json` has **14 warps, 12 of them same-map** in 6 pairs —
so the warp-graph method should have solved it. It does not, and the tool **withheld its verdict**
rather than guessing.

### WHAT WAS MEASURED
The gym is genuinely a set of disconnected rooms joined only by those tiles (collision map drawn
tile-by-tile). The apparent chain from the entrance is:
```
(6,34) --walk--> (1,33) --warp--> (20,24) --walk--> (23,20) --warp--> (9,18)
       --walk--> (7,18) --warp--> (8,12) --walk?--> (11,3) --warp--> (11,35) --walk?--> (13,32)
       --warp--> (21,10) --walk--> (23,8)  [beside Tate & Liza at (23,7)/(24,7)]
```
Four of those walks plan cleanly and **two do not**:
| link | result |
|---|---|
| `(6,34) -> (1,33)` | OK, 10 wp, panel-free |
| `(20,24) -> (23,20)` | OK, 7 wp |
| `(9,18) -> (7,18)` | OK, 2 wp |
| `(21,10) -> (23,8)` | OK, 4 wp |
| **`(8,12) -> (11,3)`** | **FAIL, no path** |
| **`(11,35) -> (13,32)`** | **FAIL, no path** |

‼ **And it is neither collision nor elevation.** Every tile along both failing links reads
`collision=0`, and the elevations alternate `0`/`3` — where `0` is the wildcard `map_path` accepts
against anything (`tile.elevation not in (0, 15)`), so no transition there should be refused.

### THE CAUSE — a distinct metatile BEHAVIOUR, not a warp event
Reading `tile_type` on those tiles returns **`'Mossdeep Gym Warp'`** (`MB_MOSSDEEP_GYM_WARP`), not
the ordinary warp behaviour the hideouts use. That is its own mechanic: in the decomp these tiles
choose a destination from gym-specific logic rather than simply firing the warp event at their
coordinates, so **modelling them as ordinary warp-table edges is wrong** — which is exactly why two
links in a chain built that way have no walkable counterpart.

### WHAT THIS MEANS FOR §Ch18
The Aqua/Magma method does **not** transfer. Before building, read how the decomp handles
`MB_MOSSDEEP_GYM_WARP` (start from `src/field_control_avatar.c` / `src/overworld.c` and the gym's
own scripts) and decide whether the traversal can be expressed as a route at all, or has to be
driven as a sequence of directional steps.
‼ Do NOT extend `probe_warp_maze.py`'s `MAZES` table with a "fixed" Mossdeep entry until that
question is answered — the tool's value is that it refuses mazes it cannot model.

### ‼‼ KI-58 CORRECTED 2026-08-12 — my stated cause was WRONG on both counts
The entry above blamed `MB_MOSSDEEP_GYM_WARP` ("a distinct behaviour whose destination comes from
gym-specific logic"). **Both halves of that are false**, and the correction matters more than the
original finding.

**1. `MB_MOSSDEEP_GYM_WARP` is an ORDINARY warp.** In `src/field_control_avatar.c` it sits in the
same `IsWarpMetatileBehavior` list as `MetatileBehavior_IsAquaHideoutWarp` — the panels the graph
already models correctly — and `DoMossdeepGymWarp()` (`src/field_screen_effect.c:559`) is a normal
warp with a different fade plus `SKIP_OBJECT_EVENT_LOAD`:
```
SetObjectEventLoadFlag(SKIP_OBJECT_EVENT_LOAD); LockPlayerFieldControls(); SaveObjectEvents();
TryFadeOutOldMapMusic(); WarpFadeOutScreen(); PlaySE(SE_WARP_IN);
CreateTask(Task_WarpAndLoadMap, 10); gFieldCallback = FieldCB_MossdeepGymWarpExit;
```
The destination is still the warp event's. **The warp-event model was never the problem.**

**2. The two failing walks are blocked by STATUES**, found by flood-filling the collision map with
`probe_gym_components.py` and cross-checking it against the planner. The two models DISAGREED on
exactly the two failing links (flood: connected, planner: no), and the disagreement located the
cause immediately:
| link | blocked by |
|---|---|
| `(8,12) -> (11,3)` | `OBJ_EVENT_GFX_TRICK_HOUSE_STATUE` at **`(11,5)`** |
| `(11,35) -> (13,32)` | `OBJ_EVENT_GFX_TRICK_HOUSE_STATUE` at **`(12,34)`** |

The gym has **36 object templates, 21 of them statues** — they are the puzzle's barrier walls, so
the planner refusing those routes is CORRECT. Statue tiles:
`(1,29) (2,30) (4,30) (5,21) (5,29) (6,5) (6,6) (7,9) (10,8) (11,5) (11,34) (12,5) (12,33) (12,34)
(21,22) (21,23) (22,22) (23,25) (23,26) (24,22) (24,23)`

### ‼ THE GENERAL LESSON, which is the valuable part
`map_path.is_tile_accessible` blocks any tile carrying an object template whose object is **not
currently loaded**:
```python
if (tile.dynamic_collision_flag is None and tile.dynamic_object_id
        and (tile.map.map_group_and_number, tile.dynamic_object_id) not in active_objects):
    return False
```
`active_objects` comes from `get_map_objects()` — **the CURRENTLY LOADED map**. So static recon of a
map from an anchor standing somewhere else treats **every object-template tile as a wall**.
⇒ **Static recon of an object-dense map is PESSIMISTIC, not optimistic**, which is the opposite of
the caveat this project has been writing on every probe ("static may call a walled tile walkable").
Both directions are now known to happen. For the two hideouts it did no harm (few objects, and the
routes worked when driven); for a 36-object gym it is decisive.

### STATUS: §Ch18 still NOT solved, but the diagnosis is now correct
The warp graph and the statue blocking are both faithful, so the route to Tate & Liza genuinely is
not the chain assumed above. **Next step:** re-run `probe_warp_maze.py --maze mossdeep_gym` from an
anchor where the GYM IS THE LOADED MAP, so the statues are live objects at their real positions
rather than pessimistic template walls, and see whether a route appears. That requires a save
standing in the gym — capture one, or drive the travel leg first.

### KI-58, third pass 2026-08-12 — the pessimism was REAL but was not the whole story
`--driver mossdeeptravel` now captures **`saves/in_mossdeep_gym.ss1`** (driven PASS, `whiteouts=0`),
so the maze could finally be reconned with the gym as the LOADED map and its 21 statues as live
objects at their real positions. **The route is still not found.** So the object-template pessimism
was a genuine instrument bug — worth fixing, and now fixed — but it was not what was hiding the
gym's route.

**Three mechanisms RULED OUT, each decomp-confirmed:**
| candidate | ruled out because |
|---|---|
| `MB_MOSSDEEP_GYM_WARP` has special destination logic | `DoMossdeepGymWarp()` is an ordinary warp; destination comes from the warp event |
| the exit is direction-dependent | `FieldCB_MossdeepGymWarpExit` is cosmetic — music, fade, `Task_ExitNonDoor` |
| the R/S switch-and-arrow puzzle moves barriers | ‼ the gym's own scripts say so: *"Mossdeep Gym was redesigned between R/S and E… All the below checks are leftover from RS. **`FLAG_MOSSDEEP_GYM_SWITCH_X` is never set**"* — that whole `setmetatile` machinery is DEAD CODE in Emerald |

**So the open question is narrow and honest: what actually connects the Emerald gym's rooms?**
The warp graph (14 warps, 12 same-map) plus live statues yields no path from `(6,34)` to Tate &
Liza's room, and the game plainly permits one. Something structural in the model is still wrong.

**‼ NEXT STEP, and it is cheap now that the anchor exists:** stop asking STATIC questions. Drive it
— from `in_mossdeep_gym.ss1`, have the bot's own runtime router (`navigate_to_anywhere` /
`_navigate_riding_out`) attempt `MOSSDEEP_CITY_GYM (23,8)` and watch where it actually goes. Every
model used so far has been offline; the live router has information none of them had. (This is the
KI-57 lesson again: when a measurement implies the game soft-locks itself, the measurement is the
suspect — and three of them now say the same wrong thing.)

