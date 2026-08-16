# Known-Issues Archive
> APPEND-ONLY history. Superseded write-ups of issues that are now resolved live here, so
> `05-KNOWN-ISSUES.md` can stay a CURRENT-STATE file within its line budget (CLAUDE.md rule R3).
>
> ‼‼ **NOT EVERYTHING IN HERE IS RESOLVED — CHECK EACH HEADING.** `KI-59` (`map_path` inverts
> `Impassable *`) and `KI-60` (`calculate_path` never validates its SOURCE) are **OPEN,
> code-verified, unfixed bugs in the SHARED pathfinder**. They were moved here for LENGTH, not
> because they were fixed, and a cold read of this file's header would conclude the opposite —
> which is exactly the wrong conclusion to reach about two live bugs that are armed in the
> Seafloor Cavern. `05-KNOWN-ISSUES.md` carries a pointer to them for this reason.
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


## Archived 2026-08-12 — KI-56 and KI-57, both RESOLVED, DRIVEN and superseded

Both were fixed and driven on 2026-08-11 and are fully described in `07-CHANGELOG.md` and
`08-MISTAKES.md`. They are moved here so `05-KNOWN-ISSUES.md` stays inside its line budget
(CLAUDE.md rule R3) without losing a word of the evidence.

‼ KI-56 remains the most-cited entry in this project, because its prevention rule — *a chapter's
test must include "and the bot can continue"* — was violated AGAIN on 2026-08-12 by §Ch18, which
passed `badge + controllable` while leaving the avatar on an eleven-tile island. Read it before
writing any chapter's acceptance test.

## KI-56 — ‼‼ Ch15 STRANDS THE BOT INSIDE THE MAGMA HIDEOUT. Strength boulders RESET on map reload (2026-08-11, severity: HIGH, MEASURED)

**Found by driving §Ch16**, whose first leg is "leave the hideout and cross to Slateport". It never
got out of the dungeon.

```
[ch16] START  MAGMA_HIDEOUT_4F(15, 21)  SLATEPORT_HARBOR_STATE=1
[ch16] FAILED: Could not find a path from (25/34 @ MAGMA_HIDEOUT_1F) to (10/34 @ MAGMA_HIDEOUT_1F)
[ch16] RESULT harbor_state=1 controllable=True map=MAGMA_HIDEOUT_1F at=(25, 34) whiteouts=0
```

### THE MEASUREMENT — it is stranded, not merely mis-routed
From the failure state (`profiles/ch16a/current_state.ss1`), on `MAGMA_HIDEOUT_1F`:
| question | answer |
|---|---|
| component containing the bot at `(25,34)` | **248 tiles** |
| exit warp `(10,34)` → JAGGED_PASS reachable? | **NO** |
| warp `(31,3)` → 2F_2R reachable? | **NO** |
| warp `(20,22)` → 2F_3R reachable? | **NO** |
| the INBOUND direction `(10,34)` → `(25,34)` | **NO** — the route it walked in through is gone |
| push-from tiles `(7,23)` / `(6,22)` reachable? | **NO** — it cannot even re-push |
| adjacent tiles `(24,34)`, `(26,34)`, `(25,33)` | OK — so the planner works and it is not boxed in locally |

**The only warp in its component is the one it is standing on** — `(25,34)`, back up to 2F_1R.

### ‼ THE CAUSE: the boulders RESET
| | boulders |
|---|---|
| `MAGMA_HIDEOUT_1F_PUSHES` predicted end state | `(4,22)`, `(5,23)`, `(7,22)` |
| **measured live after the chapter** | **`(5,22)`, `(7,22)`, `(6,23)`** |

The measured set is the **ORIGINAL, un-pushed configuration**. Neither push persisted.
⇒ **Strength boulder positions are not saved; they reset when the map reloads** — the same shape
as the already-documented "Rock-Smash rocks RESPAWN on map reload" note in `_navigate_riding_out`.

So the chapter pushes its way in, climbs to 4F, beats Maxie, walks back down to 1F — **and 1F has
re-sealed behind it**, with the boulders on the far side of the wall from where it now stands.

### ‼‼ WHY THE ACCEPTANCE TEST DID NOT CATCH THIS
Ch15 is graded **binary on `GROUDON_AWAKENED_MAGMA_HIDEOUT`**, and that flag is set the moment
Maxie is beaten — four floors deep. **The grade never asked whether the bot could LEAVE.** The
chapter passes its own test on a run that ends permanently stuck.

⇒ **NEW RULE (added to `14-AGENT-PLAYBOOK`): a chapter's acceptance test must include "and the bot
can continue".** A completion flag proves the CONTENT ran, not that the run survived it.

### THE FIX IS NOT YET CHOSEN — options, none taken
1. **Escape Rope support** — the faithful player answer, and the bot has **none**
   (`grep` for escape.?rope / dig across `modules/story/` and `modules/modes/util/`: **0 hits**).
   ‼ The hideout has **no `setescapewarp`** in any of its four map scripts (decomp-checked), so
   what an Escape Rope does from here needs verifying before relying on it. Generally useful — every
   dungeon needs it.
2. **A return-route study** — is there a walk-out at all? All three non-exit warps sit on small
   islands per §Ch15's own recon (9-tile and 70-tile), so this may be genuinely impossible once the
   boulders reset.
3. **Re-push on the way out** — ‼ **ruled out by measurement**: the push-from tiles are not
   reachable from the stranded side.

**Until this is fixed, §Ch16 cannot start from `post_maxie.ss1`,** because its first leg is leaving
the hideout. ‼ The Ch16 code itself is **unexercised beyond leg 1** — it is not implicated, and it
is not yet proven either.

### ✅ 2026-08-11 (later) — CAUSE CONFIRMED, FIX CHOSEN. `probe_hideout_warp_graph.py`
The original entry proved a *same-map* path failure and inferred the strand. That inference was
re-tested against the **whole eight-map warp graph**, because `calculate_path`'s own docstring says
*"It is not able to use warps"* — so "no path from 1F (25,34) to 1F (10,34)" is also exactly what a
**routing gap** would look like on a map whose rooms are joined by warps. It is not one.

`probe_hideout_warp_graph.py` reads every warp from the ROM warp table, adds a walk edge wherever
`calculate_path` plans between two nodes on one map, and BFSes. From the stranded tile it reaches
**18 of 20 nodes**. The only two it cannot reach are the exit warp `1F (10,34)` and `JAGGED_PASS`:

| control | result |
|---|---|
| POSITIVE — the driven ascent `1F (25,34) -> 4F` must be findable | **OK**, 5 hops, matches §Ch15 |
| REPRODUCTION — walk-only, `(25,34)` must not reach the exit | **OK**, reproduces KI-56 exactly |
| WARP-TABLE — the three driven inbound hops must be in the ROM table | **OK**, all three |

⇒ **KI-56's stated cause is CONFIRMED** and **option 2 (a return-route study) is formally DEAD**:
the bot can reach every chamber of the hideout *except* the 44-tile entrance pocket holding the
exit. Option 3 (re-push) was already dead. **The fix must leave the map without walking.**

‼ **The positive control had to be the ASCENT, not the full inbound journey.** The first inbound
leg `1F (10,34) -> (25,34)` is opened by two **Strength pushes** (`MAGMA_HIDEOUT_1F_PUSHES`), and
no static planner models a push — the first version of this probe used that leg as its control,
failed, and correctly withheld its verdict. See `08-MISTAKES` 2026-08-11.

### ‼ THE FIX: the dungeon supplies its own Escape Rope. No detour, no shopping.
`MagmaHideout_3F_3R/map.json` places an **ITEM BALL holding an Escape Rope at `3F_3R (9,19)`** —
inside a room §Ch15 already walks through, and (per the reachable set above) **still reachable from
the stranded tile**. All four facts are measured, with controls:

| fact | value | how |
|---|---|---|
| item ball | `MAGMA_HIDEOUT_3F_3R (9,19)` | decomp `map.json` |
| flag | `ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE` (1059), **unset** on the stranded save | live |
| approach tile | **`(9,20)` only** — face **Up**. `(9,18)`/`(8,19)`/`(10,19)` all unreachable | `calculate_path` |
| reachable from | both 3F_3R warp nodes, `(16,1)` and `(16,21)` | live |
| Escape Rope lands at | **`JAGGED_PASS (16,19)`**, collision=0, walkable | live, `probe_escape_warp.py` |

**Why the landing tile is knowable even though the hideout has no `setescapewarp`:**
`UpdateEscapeWarp` (decomp `src/overworld.c:677`, called from `src/field_control_avatar.c:826`)
stamps `gSaveBlock1Ptr->escapeWarp` on **every** warp step where the map being LEFT is outdoors and
the map being ENTERED is not. Walking Jagged Pass -> 1F sets it automatically.
`MagmaHideout_1F/map.json` has `"allow_escaping": true`, so `CanUseDigOrEscapeRopeOnCurMap()`
(`src/item_use.c:911`) permits the item. **NEGATIVE ARM:** on `magma_door.ss1` (hideout not yet
entered) the same field reads `ROUTE112 (28,28)` — so the JAGGED_PASS value is the entry stamp, not
a coincidence.

‼ **THE FLAG IS MISSPELLED IN THE DECOMP — "ECAPE", not "ESCAPE"** — and
`modules/data/event_flags/emerald.txt` carries the typo through as flag 1059. The correctly-spelled
name **does not exist**, and an unknown flag name reads `False` **silently**, which is
indistinguishable from "the ball is still there". Spelled right, that check is a permanent lie.

**Bag state: 0 Escape Ropes on every save read** (`STRANDED`, `post_maxie`, `magma_door`,
`post_mtpyre`), so the pickup is not optional — it is the whole acquisition. ‼ **Lavaridge Mart
does NOT stock Escape Rope** (decomp): the only marts that do are Rustboro, Petalburg, Fallarbor,
Slateport and Lilycove Dept. 2F — all a long detour from the Jagged Pass approach. The in-dungeon
ball avoids that entirely.

### ✅✅ RESOLVED 2026-08-11 — BUILT AND DRIVEN. `--driver magmaexit`, VERDICT PASS
```
[mhexit] START  MAGMA_HIDEOUT_4F(15, 21) inside=True ropes=0 ball_taken=False
[mhexit] RESULT out=True map=JAGGED_PASS at=(16, 19) controllable=True
                landed_on_jagged_pass=True ropes=0 whiteouts=0
[mhexit] VERDICT PASS - acceptance is BOTH halves: outside AND controllable, on JAGGED_PASS.
```
‼ **The landing tile is `(16,19)` — the exact coordinate read out of `gSaveBlock1Ptr->escapeWarp`
before a line of code was written.** The prediction and the driven result agree tile-for-tile.

**What was built** (`modules/story/early_game.py`): `collect_hideout_escape_rope()`,
`use_escape_rope_to_leave_hideout()`, `leave_magma_hideout()`, and the chapter now ENDS with
`yield from leave_magma_hideout()` — deliberately **outside** the `_groudon_awakened()` guard, so a
run resumed after the flag was set still finishes the exit. Driver: `--driver magmaexit`. Guard:
`repro_hideout_exit.py` (24 structural checks, **fault-injected both ways** — "correcting" the flag
typo and nesting the exit inside the guard each turn it red).

### ‼ THE ONE THING THAT DID NOT WORK FIRST TIME — and the general rule it produced
The first driven run **consumed the rope and went nowhere**: same tile, `controllable=False`,
`ropes=0`. Not a refusal — the item was accepted. The harness's no-progress dump named the cause:
**`Task_ContinueTaskAfterMessagePrints` was active.** `ItemUseOnFieldCB_EscapeRope` (decomp
`src/item_use.c:903`) calls `DisplayItemMessageOnField(..., Task_UseDigEscapeRopeOnField)`, and
`StartEscapeRopeFieldEffect()` runs only from that **callback**, which fires when the message is
DISMISSED. The wait loop only `yield`ed, so it waited for ever on a text box. Fixed by pressing
**B** every 4th frame while waiting (B dismisses and interacts with nothing; a stray A on the far
side of the warp would talk to whoever is standing on Jagged Pass).

⇒ **The Strength lesson generalises to items: a consumed item is NOT the end of the script that
consumed it.** Added to `14-AGENT-PLAYBOOK`.

**Still true / still not proven:** this was driven from `post_maxie.ss1` (on 4F). The exit has
**not** been driven from a run that walked all the way back down to `1F (25,34)` — the warp graph
says 3F_3R is reachable from there, but that is static. And `#24-slateportsub` (§Ch16) is now
UNBLOCKED but still unexercised beyond leg 1.

## KI-57 — ‼ §Ch16 leg 1: **beating Maxie PARKS Capt. Stern on the tile Ch16 walks to** (2026-08-11, severity: HIGH, MEASURED, decomp-confirmed)

Found by re-driving §Ch16 once KI-56 was fixed. The bot got **out of the Magma Hideout, across the
region, and into Slateport** — then died on the last step of leg 1:

```
[ch16] PRE-STEP done - now at JAGGED_PASS(16, 19)          <- KI-56's fix, working
[ch16] WHITEOUT #1 - recovering, as StoryMode does
[ch16] FAILED: UnreachableDestinationError: Could not reach (28, 13) on SLATEPORT_CITY:
       the field is idle and we are still at (19, 20), so retrying cannot change the result
[ch16] RESULT harbor_state=1 controllable=True map=SLATEPORT_CITY at=(19, 20) whiteouts=1
```

### THE CAUSE — decomp, not inference
`SlateportCity_OnTransition` calls `SlateportCity_EventScript_MovePeopleForSternInterview`
whenever `VAR_SLATEPORT_CITY_STATE == 1`, and that script begins:
```
setobjectxyperm       LOCALID_SLATEPORT_CAPT_STERN, 28, 13
setobjectmovementtype LOCALID_SLATEPORT_CAPT_STERN, MOVEMENT_TYPE_FACE_DOWN
```
`SLATEPORT_HARBOR_DOOR_APPROACH` **is** `(28,13)`. ‼ **And §Ch15 is what sets that var** — the
same `MagmaHideout_4F_EventScript_Maxie` that ends Ch15 sets `SLATEPORT_CITY_STATE` and clears
`FLAG_HIDE_SLATEPORT_CITY_CAPTAIN_STERN` / `..._GABBY_AND_TY`. **Completing Ch15 spawns the thing
that blocks Ch16.**

It is `setobjectxyperm` with a `FACE_*` movement type ⇒ **stationary and deterministic**. Waiting
or retrying can never clear it. (An early reading of this guessed "a wandering NPC may clear on its
own" — the movement types refute that.)

### THE MEASUREMENT (`probe_slateport_harbor_approach.py`, from `saves/stalls/ch16b-f20252.ss1`)
| query | live (NPCs visible) | static (city not loaded) |
|---|---|---|
| `(19,20) -> (28,13)` | **FAIL** (reproduces) | **OK, 20 wp** |
| `(28,13) -> (19,20)` | FAIL | OK, 20 wp |
| control `(19,20) -> (20,20)` | OK, 1 wp | — |

Live objects occupy **`(28,13)` Capt. Stern, `(28,14)` Gabby, `(29,13)` Ty** — a three-tile plug.
Reachable near the door: `(27,13)` 19 wp, `(27,14)` 18 wp, `(28,15)` 18 wp, `(29,14)` 20 wp.

### ‼ AND NO STAGING TILE WORKS — the plug seals the door, it does not merely cover it
| candidate | reachable from `(19,20)`? | can it reach the door `(28,12)`? |
|---|---|---|
| `(27,13)` `(28,15)` `(27,14)` `(29,14)` | **yes** | **NO** |
| `(27,12)` `(29,12)` `(28,11)` | **NO** | yes, 1 wp |

The door's neighbours and the reachable tiles are in **different components**: `(28,13)` is a
one-tile neck, and Stern is standing in it. So this is **not** fixable by picking a different
staging tile near warp 8.

### THE LEAD, NOT YET AN ANSWER — there is a SECOND harbor entrance
The ROM warp table for `SLATEPORT_CITY` has **two** warps to `SLATEPORT_CITY_HARBOR`:
* **warp 8 `(28,12)`** -> harbor `(11,14)` — the one Ch16 uses, and the one Stern seals.
* **warp 9 `(40,7)`** -> harbor `(19,15)` — **unused by our code.**

`(39,7)`, immediately west of it, **plans in 37 wp** from the stuck tile. But `(40,7)` itself does
not plan, and the harbor-side arrival `(19,15)` raised `IndexError` when asked to path to the
trigger `(8,14)` (whereas warp 8's arrival `(11,14) -> (8,14)` plans in 3 wp). **So warp 9 is a
lead worth one probe, not a fix.** Do not wire it in on this evidence.

### ‼ ALSO NOTE — the run WHITED OUT first
`(19,20)` is directly below `warp 0 (19,19) -> SLATEPORT_CITY_POKEMON_CENTER_1F`, so the bot is
standing where a **whiteout recovery** left it, not where it walked. That is incidental to this
blocker (the static arm plans from there fine), but it means leg 1 also lost a fight somewhere on
the Jagged Pass -> Slateport haul, which is unmeasured.

**Repro fixture:** `tools/story-dev/saves/stalls/ch16b-f20252.ss1` (VOLATILE — a stall save; the
harness overwrites the `stalls/` directory per run).

### ✅✅ KI-57 RESOLVED 2026-08-11 — Stern is not an obstacle, he is THE DOOR
```
[ch16] RESULT harbor_state=2 controllable=True map=SLATEPORT_CITY_HARBOR at=(8, 13) whiteouts=1
[ch16] ACCEPTANCE: PASS (needs harbor_state==2 AND controllable==True)
```

**The measurement that cracked it was a PICTURE, not more spot-checks.**
`probe_slateport_harbor_map.py` draws the collision map with live objects overlaid:
```
  12 ....####D###.~~~     <- the door (28,12) is set into a SOLID WALL
  13 .....O..OO......     <- (28,13) Stern, (29,13) Ty; (27,13) is his one free neighbour
```
`(28,13)` is the **only** tile touching the door, and Stern is on it. So the door genuinely is
sealed — KI-57's geometry was right. What was wrong was the CONCLUSION drawn from it.

‼ **The door is not meant to be walked through in this era.** `SlateportCity_EventScript_CaptStern`
— i.e. **talking to him** — plays the interview and the Team Aqua announcement and ends:
```
removeobject LOCALID_SLATEPORT_CAPT_STERN
setvar       VAR_SLATEPORT_CITY_STATE, 2
warp         MAP_SLATEPORT_CITY_HARBOR, 11, 14
```
**The script carries the player in**, landing on `(11,14)` — the same tile the door warp lands on,
so leg 3 needed no change at all. It is also the faithful reading: a human talks to the man being
interviewed rather than shoving past him.

**What changed in §Ch16:** legs 1+2 are now "walk to `SLATEPORT_STERN_APPROACH (27,13)`, face
Right, A/B-ride the scene until the map changes or `SLATEPORT_CITY_STATE == 2`". The old
door-walking path is kept as the **resume branch only** (`_city_state() >= 2`, i.e. Stern already
`removeobject`ed). Bounded at 30,000 frames with a state-reporting failure message.

### ‼ AND AN INSTRUMENT GOTCHA THAT PRODUCED A WRONG SUB-CLAIM
KI-57 originally reported that `(27,12)`, `(29,12)` and `(28,11)` are "walkable tiles adjacent to
the door" that "reach it in 1 wp" but sit in a different component. **They are walls.**
`calculate_path` **does not validate its SOURCE tile** — asked for a path *from* a blocked tile it
happily returns one. Every "OK, 1 wp" in that table was an artifact.
⇒ **A `calculate_path` result is only evidence about the DESTINATION side unless the source has
been independently shown to be walkable.**

---

# ARCHIVED 2026-08-12 — KI-58 (RESOLVED), moved out of `05-KNOWN-ISSUES.md` for the R3 budget
> Moved verbatim, not rewritten. The live file keeps a one-paragraph stub pointing here.

## KI-58 — the Mossdeep Gym statue puzzle (2026-08-12, RESOLVED — see the two sections below)

‼ **This issue was written up three times with three different wrong causes before it was
understood.** Those superseded write-ups are archived in **`31-KNOWN-ISSUES-ARCHIVE.md`** rather
than deleted — they are the record of how a shared blind spot survived four instruments, and the
lessons drawn from them are in `08-MISTAKES.md`. What follows is the CURRENT state only.

## ✅✅ KI-58 RESOLVED 2026-08-12 — the Mossdeep Gym is a ROTATING-TILE STATUE PUZZLE, not a maze

Four passes of my own offline models all said "no route", which could not be true. The cause was a
**movement primitive the model had no concept of**. Found by five parallel research agents (user
directive) and then **verified in our own harness**.

### THE MECHANIC — verified, not recalled
Nine of the gym's `coord_events` are **floor switches**. Their scripts
(`data/maps/MossdeepCity_Gym/scripts.inc:307,319,331,343,355`) run:
```
initrotatingtilepuzzle FALSE / moverotatingtileobjects N / turnrotatingtileobjects / freerotatingtilepuzzle
```
`MoveRotatingTileObjects` (`src/rotating_tile_puzzle.c:108-188`) walks every object template, reads
the metatile underneath it, and if that metatile is a coloured ARROW of the pressed colour it shifts
the object one tile in the arrow's direction — **mutating
`gSaveBlock1Ptr->objectEventTemplates[i].x/.y`**. All 21 `TRICK_HOUSE_STATUE` objects stand on arrow
tiles, and they are what seal the corridors to the `(11,3)`, `(13,32)` and `(21,10)` panels.

‼ **PROVEN LIVE, in our harness** (not taken on trust — the standing rule is that agent output is a
NOTE). From `in_mossdeep_gym.ss1`, walking onto the yellow switch at `(3,30)`:
```
objects BEFORE : (1,29) (1,30) (2,30) (4,29) (4,30) (5,29) (5,33) (11,34) (12,33) (12,34)
objects AFTER  : (1,30) (2,29) (2,30) (4,23) (4,29) (4,30) (5,30) (5,33) (11,34) (12,33) (12,34)
   left  : (1,29) (5,29)        now occupy : (2,29) (5,30)
```
Statues moved. **The mechanic is real and it fires on stepping.**

### WHY EVERY MODEL FAILED, INCLUDING THE BRUTE FORCE
`probe_gym_bruteforce.py` presses buttons and reads positions, so it cannot be wrong about the map
— yet it found only 35 tiles and **0 warp panels**. Because it was *changing the map while
exploring it*: it stepped on switches, statues moved, and its state key was only
`(map, position)`, so two genuinely different worlds collapsed into one node. **In a puzzle whose
world state mutates, the search state must include that state.** Its key now carries the live
object positions.

### THE OTHER FACTS THAT CAME OUT OF IT (each independently confirmed)
| fact | why it matters |
|---|---|
| the gym's tile vocabulary is **only** `MB_NORMAL`, `MB_MOSSDEEP_GYM_WARP` (13 tiles), `MB_SOUTH_ARROW_WARP` (2) | no ice/slide/arrow forced movement anywhere — `MetatileBehavior_IsForcedMovementTile` matches none of them |
| **`(23,7)` and `(24,7)` are `collision == 1`** | Tate and Liza stand on WALL metatiles. Target `(23,8)`/`(24,8)` and face NORTH — a planner asked for their own tiles can only ever say "no route" |
| **`(21,6)` is a TRAP** | it carries `MB_MOSSDEEP_GYM_WARP` but has **no warp event**; its coord_event runs `warpmossdeepgym MAP_MOSSDEEP_CITY_GYM, 7, 30` and dumps you back near the entrance. It is 4 tiles north of the champion-room arrival `(21,10)`, so a naive walk north loses the room. **Treat as blocked.** |
| statue state is **5 counters mod 4** (1024 states) | arrows start at `METATILE_MossdeepGym_YellowArrow_Right = 0x250`; colour = `(mt-0x250)/8`, direction = `(mt-0x250)%8` (0 R, 1 D, 2 L, 3 U). Each pad is a 2x2 4-cycle |
| switch tiles | Yellow `(2,21) (3,30)` · Blue `(8,10) (6,7)` · Green `(15,34)` · Purple `(23,24) (23,21)` · Red `(8,6)`. `VAR_TEMP_1` is never set, so they **re-fire every time** |
| ‼ **gym-internal warps PRESERVE puzzle progress; leaving the gym RESETS it** | `DoMossdeepGymWarp` calls `SaveObjectEvents()` + `SetObjectEventLoadFlag(SKIP_OBJECT_EVENT_LOAD)`, and `LoadMapFromWarp` then skips `LoadObjEventTemplatesFromHeader()` — that is *why* the gym needed its own warp function. The flag is cleared on gym exit, so **the bot must treat leaving the gym as a full puzzle reset** |
| trainers sit on pads too and rotate with the statues | so NPC positions are part of the puzzle state, not fixed obstacles |

### A CANDIDATE SOLVED ROUTE — ‼ AGENT-DERIVED, NOT YET DRIVEN
A BFS over (player tile x 5 rotation counters) reportedly reaches `(23,8)` in 116 steps:
```
(6,34) walk (1,33) WARP (20,24) | (23,24) PURPLE | (15,34) GREEN x2 | (23,24) PURPLE
| (23,21) PURPLE | (23,20) WARP (9,18) | (7,18) WARP (8,12) | (8,10) BLUE x3
| (6,7) BLUE x3 | (8,6) RED x3 | (6,7) BLUE | (8,10) BLUE | (11,3) WARP (11,35)
| (13,32) WARP (21,10) | (21,9) (22,9) (23,9) (23,8) face NORTH -> talk to Tate
```
**Do not trust this until it is driven.** Yellow and the `(3,28)<->(1,23)` pair are said to be
unnecessary. The right next step is to let `probe_gym_bruteforce.py` — now statue-aware, and
model-free by construction — find and CONFIRM a route itself, using this as a sanity check on its
answer rather than as the answer.

## KI-59 — ‼ `map_path` INVERTS `Impassable *` directions: an over-block on every such tile (2026-08-12, severity: MEDIUM, code-verified)

> ⛔⛔ **CORRECTION BANNER, 2026-08-13 — READ BEFORE ACTING ON ANYTHING BELOW.**
> The inversion described below **is real and is confirmed by the decomp**. Two things in it are
> **WRONG**, both measured by `tools/story-dev/probe_impassable_dirs.py` over all 518 maps:
> 1. ⛔ **"ARMED IN THE SEAFLOOR CAVERN … fix it with an A/B on `SEAFLOOR_CAVERN_ROOM1`" is FALSE.**
>    The handler is the **`elif` of `if tile.collision != 0:`**, and **all 115 cavern tiles have
>    `collision=1`**, so **none of them reach it**. That A/B would have measured a **zero delta**.
>    Game-wide: 2,658 such tiles, **2,257 dormant, only 401 (15.1%) live**. KI-59 is a prerequisite
>    of the **REGI ARC** (144 live tiles across Desert Ruins / Island Cave / Ancient Tomb), not of
>    the cavern.
> 2. ⚠ **"every such tile is over-blocked" understates it.** For `Impassable North` the shipped
>    model `[--S-]` is the *exact complement* of correct `[NE-W]`: it refuses the three legal
>    entries **and permits the one illegal one**. It under-blocks as well as over-blocks.
> The "also missing: the decomp blocks *leaving* a tile too" paragraph below is **correct and
> important** — see `#24-impassabledirs` for the specified fix. Everything else below stands.

Found by an independent audit while chasing KI-58. **Not** the Mossdeep cause (that map has no
`Impassable *` tiles) — a separate latent bug in a SHARED subsystem.

`sandbox-pokebot/modules/map_path.py` (~line 128), building `accessible_from_direction`:
```python
accessible_from_direction = [False, False, False, False]
...
elif tile.tile_type.startswith("Impassable "):
    impassable_directions = tile.tile_type[11:].replace(" and ", "/").split("/")
    for direction in impassable_directions:
        dir = Direction[direction]
        accessible_from_direction[dir.opposite()] = True    # <-- SETS the only True
```
It starts all-`False` and **sets exactly one direction True per impassable direction**. The correct
model (decomp `src/event_object_movement.c:4715-4722`) is the inverse: **start all-`True` and CLEAR
the opposite of each impassable direction.**

⇒ `"Impassable North and South"` — a horizontal barrier that should be enterable from **E/W** — is
modelled as enterable **only from N/S**. `"Impassable East"` becomes enterable only from the West
instead of from everywhere except the East. Every such tile is over-blocked, so the planner refuses
routes that are legal in game.

‼ **Also missing:** the decomp blocks *leaving* a tile too (`gOppositeDirectionBlockedMetatileFuncs`
applied to the tile you stand ON). `map_path` has no "cannot EXIT in direction D" concept at all.

**NOT FIXED, deliberately.** `map_path` is shared by every bot mode, and a change here alters
navigation everywhere — the same reasoning that kept KI-52's battle-policy change scoped. Tracked as
`#24-impassabledirs`. ‼ Before fixing, find a map that actually HAS `Impassable *` tiles and build a
reproduce → fix → prove A/B on it; do not fix it blind.

## KI-60 — `calculate_path` never validates its SOURCE tile (2026-08-12, severity: LOW-MEDIUM, code-verified)

`modules/map_path.py` seeds the search with
`open_queue.put(PathNode(source_tile, source_tile.elevation, None, None, 0, ...))` and **never runs
the source through `is_tile_accessible`**. Its collision, elevation, object occupancy and direction
data are all ignored.

Consequences, both already paid for in this project:
* asked for a path **out of a wall**, it happily returns one — which is exactly the artifact that
  sent KI-57's first write-up toward a "different components" story about three tiles
  (`(27,12)`, `(29,12)`, `(28,11)`) that turned out to be solid rock;
* a source that is a warp pad or an object's tile yields a bare *"Could not find a path"* rather
  than "invalid source", so the failure surfaces far from its cause.

⇒ **A `calculate_path` result is evidence about the DESTINATION only** (already a playbook rule; this
is the code reason). Tracked as `#24-pathsourcecheck`. A cheap, low-risk fix is to raise a distinct
error when the source is inaccessible — but it is still shared code, so it needs its own A/B.

### KI-58 addendum — the gym is SIX ISLANDS, and the puzzle's key idea is a switch you cannot reach
A third independent agent decoded the layout and confirmed everything above, adding the structural
facts that make the route make sense. **Its route matched a published walkthrough step for step**,
and agrees with the other solver's (117 vs 116 steps, same structure).

**The gym's walkable tiles form 6 disconnected islands.** No walkable tile joins them — the ONLY
links are the warp pads. So any plain A* over collision is *correct* to say "no path"; that was
never the bug.

| island | region | pads | switches on it |
|---|---|---|---|
| entrance hall | y28-35 | doors `(6,35)/(7,35)`; `(1,33)`; `(3,28)` | YELLOW `(3,30)` |
| south-east | y20-34 | `(20,24)`; `(23,20)` | **GREEN `(15,34)`**, PURPLE x2 |
| mid-west | y18-23 | `(1,23)`, `(7,18)`, `(9,18)` | YELLOW `(2,21)` |
| north-west | y3-12 | `(8,12)`; `(11,3)` | BLUE x2, RED `(8,6)` |
| green antechamber | 9 tiles | `(11,35)`; `(13,32)` | **NONE** |
| leaders' platform | 11 tiles | `(21,10)`; ‼ `(21,6)` trap | none |

**‼ THE DESIGN'S KEY IDEA, and the thing a naive solver will never find:** the green antechamber has
three statues in a green loop and **no green switch on it**. The only green switch is `(15,34)`, in
the south-east island. Enumerating all four green rotations, **only `green == 2` frees `(12,34)`** —
the unique tile joining `(12,35)` to `(13,34)`. So the green statues must be **pre-set to exactly 2
before you ever warp in**; every other value is a dead end you cannot fix from inside. Hence exactly
**two green presses**, early.

**Other operational facts:**
* **Two switches are unavoidable transit tiles:** `(23,24)` (PURPLE, the only link east from
  `(20,24)`) and `(8,10)` (BLUE, the only link from pad `(8,12)` into the north-west island). The
  bot WILL rotate purple and blue just by walking — budget for it rather than treating it as an error.
* **Rotation moves the TRAINERS too**, changing their facing and sight lines; the route crosses ~8
  sight lines, so treat gym trainer battles as expected, not as a derail.
* **YELLOW and the `(3,28)<->(1,23)` branch are entirely off the critical path** — do not spend
  solver effort there.
* Elevations are only 0 and 3, and 0 is the wildcard ⇒ **elevation never blocks anything here**.
* `(21,6)`'s trap uses `warpmossdeepgym` and does **not** reset the statues — it just costs the trip.

‼ **Still not driven.** Two independent solvers agree and one matches a walkthrough, which is strong
— but by this project's own rule that is a NOTE. The build order is: let the statue-aware
`probe_gym_bruteforce.py` confirm a route empirically, using these as the cross-check.

### ✅ KI-58 — the model is now BUILT AND VALIDATED (2026-08-12, later). Corrections below.

`sandbox-pokebot/modules/story/mossdeep_gym_puzzle.py` simulates the puzzle; `probe_gym_arrows.py`
dumps the arrow field it reads; `probe_gym_simulate.py` is the validation gate and **PASSES** —
11/11 loaded objects predicted on a live press, identity-keyed on `local_id`, plus a period-4
identity control on all five colours. The route planner may now be built on this model.

**The encoding, derived from the ROM dump rather than assumed.** Arrows are metatiles `0x250..0x27F`;
band = `(mt-0x250)//8` → `0 Yellow 1 Blue 2 Green 3 Purple 4 Red`; code = `(mt-0x250)%8` →
`0 Right 1 Down 2 Left 3 Up`. ‼ **Codes 4 and 5 are that colour's floor SWITCH, not an arrow** —
which is why the dir-4/5 tiles reproduce the nine-switch list exactly. `METATILE_ROW_WIDTH` is 8 and
`METATILE_MossdeepGym_YellowArrow_Right = 0x250` is the *only* MossdeepGym label in the decomp.

#### ‼ WHAT WAS WRONG IN THE ENTRIES ABOVE
| claim above | correction | evidence |
|---|---|---|
| statue state is "**5 counters mod 4**" | **Unsafe as a state model.** It holds only for a pad carrying three objects; the yellow pad at `(4,20)-(5,21)` carries two. Use the full tuple of object positions — hashable, small, and always right | `probe_gym_arrows.py` occupancy dump |
| the 21 **statues** are what seal the corridors | **Nine TRAINERS stand on arrow pads and rotate with them** — Preston, Blake, Maura, Virgil, Nate, Sylvia, Clifford, Kathleen, Nicholas. A statue-only model mispredicts every pad holding one | decomp `map.json` × layout; live press moved trainer ids 2 and 4 |
| statues are the `trainer_type == "None"` objects | **Statues are `graphics_id == 224`** (exactly 21). The `trainer_type` filter also catches Tate, Liza and the gym guide | template dump |
| the gym is **6 islands** | **8 collision components.** `(6,1)` and `(23,18)` are collision-0 pockets walled in on all four sides with no warp — permanently unreachable | flood fill of `map.bin`'s 175 walkable tiles |
| "the **ONLY** links are warp pads" | False. The `(21,6)` coord event is a seventh, non-warp, **one-way** link (platform → entrance hall) | `map.json` has no warp event at `(21,6)` |
| `(21,6)` is a **TRAP** | Operationally yes — but it is **not gated on any flag**, so it is equally the designed one-way exit, live from arrival. "Treat as blocked" stays correct; the *reasoning* in the entry above is wrong | `scripts.inc:199-204`, no flag check |
| **two** switches are unavoidable transit tiles | **Three.** `(23,20)`'s only walkable neighbour is `(23,21)`, the second purple switch. Budget for purple advancing twice on the way | neighbour scan of the collision map |
| the green antechamber is a "**dead end you cannot fix from inside**" | Overstated. `(11,35)` is itself a return warp, so a wrong green value costs a lap, not the run | warp table |

#### FACTS CONFIRMED (do not re-litigate)
* **`MoveRotatingTileObjects` has NO collision check** — `objectEvents[i].x += x` is unconditional
  (`src/rotating_tile_puzzle.c:171-172`). Two statues *could* collide, land on the player, or enter a
  wall; none happens, because every colour's arrows form **disjoint closed 2x2 4-cycles**. A rotation
  is therefore a permutation, and four presses of any colour is the identity (verified for all five).
* It mutates **both** the save-block template (unconditionally) and the live object (if spawned).
* Switches **re-fire every time**: `VAR_TEMP_1` is never written anywhere, and
  `ClearTempFieldEventData()` zeroes temp vars on every map load. There is no "already triggered"
  bookkeeping of any kind.
* **Gym-internal warps preserve the puzzle; leaving resets it.** The 12 internal panels route to
  `DoMossdeepGymWarp` by *metatile behaviour* `MB_MOSSDEEP_GYM_WARP == 14`, which sets
  `SKIP_OBJECT_EVENT_LOAD` so `LoadMapFromWarp` skips `LoadObjEventTemplatesFromHeader()`. The two
  exit tiles `(6,35)/(7,35)` are behaviour 101 → ordinary `DoWarp()` → full reset.
* **Green must be 2 before warping into the antechamber.** Only `green == 2` frees `(12,34)`, the
  unique tile joining `(11,35)`'s side to `(13,32)`'s. Exhaustively checked over all four values.
* **No configuration is unsolvable.** 114,929 reachable states; **0** from which `(23,8)` or the exit
  becomes unreachable. The purple pad at `(21,22)-(22,23)` holds four objects, so it is inert.
* **Tate & Liza cannot approach you.** Both are `TRAINER_TYPE_NONE` with sight id 0, so
  `CheckForTrainersWantingBattle` never considers them — the player *must* reach `(23,8)` or `(24,8)`
  and face NORTH and press A. They need **≥2 usable Pokémon** (`GetMonsStateToDoubles`: party count
  of 1 short-circuits; otherwise ≥2 non-egg, HP>0 party members).
* **Ordinary gym trainers have sight range 1 ⇒ ZERO approach steps** — they never leave their tile
  when they spot you. This is what keeps live positions in sync with the templates the puzzle mutates,
  and it is why an offline model is sound at all.

#### ‼ THE OPERATIONAL FACT THE EXECUTOR MUST HANDLE
**Solving the puzzle aims the trainers at you.** Pressing yellow at `(3,30)` slides Maura from
`(4,29)` to `(4,30)` — adjacent to the player standing on the switch — and turns her to face them;
`EventScript_ShowTrainerIntroMsg` fires before the bot can step off. This is not avoidable by
approaching the switch differently, and it is not a fault: **gym trainer battles are a consequence of
the mechanic**. The executor must fight them, and a wait loop that does not expect a script will
simply hang with the avatar "refusing to walk".

---

# ARCHIVED 2026-08-12 — KI-61 (FIXED), moved out of `05-KNOWN-ISSUES.md` for the R3 budget
> Moved verbatim, not rewritten. The live file keeps a stub pointing here.

## KI-61 — the chapter DETECTOR named the wrong beat after badge 7 (2026-08-12, MEASURED, ✅ FIXED)

**Symptom.** With seven badges and Dive not yet received, `progress.detect_live()` reported the
current chapter as **"Seafloor Cavern — Kyogre"**, skipping both the Space Center and HM08 Dive.

**Cause — a registry ORDER bug with a non-obvious blast radius.** `modules/story/chapters.py` listed
*"Mossdeep & Space Center"* (milestone `RECEIVED_HM_DIVE`) **before** *"Gym 7 — Tate & Liza"*
(`BADGE07_GET`). That order is impossible: the Space Center's Team Magma and Steven are HIDDEN until
Tate & Liza are beaten — `MossdeepCity_Gym_EventScript_TateAndLizaDefeated`
(`data/maps/MossdeepCity_Gym/scripts.inc:73-76`) is what clears the three `HIDE_..._SPACE_CENTER_*`
flags. ‼ `12-STORYMODE-DESIGN.md` had recorded this order as **"order confirmed"**.

The order is not cosmetic, and that is the part worth remembering: `_compute_badges_before()` derives
each chapter's badge count *by walking the list*, and `current_chapter()` picks the bracket for the
player's badge level and then the first unmet chapter in it. Listed ahead of the gym, the Space
Center was computed as a **six**-badge chapter, so the instant the seventh badge landed it fell out
of the bracket entirely and the detector jumped to the next seven-badge chapter.

**MEASURED IN OUR OWN HARNESS** (`tools/story-dev/probe_chapter_order.py`), not taken from the decomp:
| save | badges | Space Center objects hidden | `MOSSDEEP_SPACE_CENTER_STATE` |
|---|---|---|---|
| `post_aqua.ss1` | 6 | **3 of 3 — Magma and Steven do not exist yet** | 0 |
| `post_mossdeep_gym.ss1` | 7 | **0 of 3 — both present** | 1 |

**A/B on the fix:** before, `post_mossdeep_gym.ss1` → `ch20 'Seafloor Cavern — Kyogre'`; after,
→ `ch19 'Mossdeep & Space Center'`. `badges_before` for the Space Center went 6 → 7.

**Prevention rule.** *When a list's ORDER is read as meaning by more than one consumer, a wrong
order is a silent logic bug, not a cosmetic one. Order claims in docs need the same evidence bar as
code — "order confirmed" was written here and was wrong.*

---

# ARCHIVED 2026-08-12 — KI-52 (FIXED 2026-08-11), moved out of `05-KNOWN-ISSUES.md`
> Moved verbatim, not rewritten. The live file keeps a stub pointing here.

## KI-52 — ✅ FIXED 2026-08-11 (user directive). A WILD battle used to end the run when the LEAD dropped below `hp_threshold`, with a full healthy bench unused

**What was measured** (`mintrun1`, driving the Magma Hideout from a freshly-minted `magma_door.ss1`):
```
Bot stopped: Your Pokémon cannot battle due to HP below threshold, and escape is not possible.
map=MAGMA HIDEOUT(24,91) pos=(15,6)  game_state=4  battle: active=True
callback=HandleTurnActionSelectionState  battle_text='What will SCEPTILE do?'
party=['Sceptile L46 10/128', 'Zigzagoon L7 24/24', 'Swellow L40 112/112',
       'Skitty L17 45/45', 'Mightyena L43 127/127', 'Castform L35 100/100']
```
**Five healthy party members**, and the run stopped. It then sat wedged **mid-battle in Manual for
18,000+ frames** (the `[STUCK — 18000 frames no progress]` dump above is that).

**The chain**, all in stock code:
* `profiles/battle.yml`: `hp_threshold: 20`, `lead_cannot_battle_action: flee` (the **upstream
  default** — `modules/config/templates/battle.yml:16`).
* Sceptile at 10/128 = **7.8%** < 20 ⇒ `_is_healthy()` False ⇒ `_handle_lead_cannot_battle`.
* Action is `flee`; this was a **WILD** battle (a Magma Hideout Geodude — had it been a trainer the
  message would have been *"'flee' is not allowed in a trainer battle"*), so it tried to escape,
  `get_best_escape_method()` returned None, and it raised
  `BotModeError("… escape is not possible.")` → Manual.
* `modules/battle_strategies/default.py:242-273`.

⇒ **`rotate` is the obviously correct action here and it already exists.** `_handle_rotate` switches
to a rotation target and only raises when there is genuinely no eligible switch — which was not the
case: there were five.

### ‼ WHY THE FIX IS *NOT* "flip the global config"
**`flee` is CORRECT for shiny hunting**, which is what this bot mostly does — you do not want a
hunting run rotating in a fresh mon and fighting every wild that outlasts the lead. A global flip
would trade a story-mode derail for a hunting-mode regression across every other mode.

**Candidate shapes (none chosen — this is a design decision):**
1. **Mode-scoped override**: StoryMode sets `rotate` for its own duration. Narrow blast radius,
   matches how `on_whiteout` is already overridden per-mode.
2. **A story battle strategy** that subclasses the default and rotates instead of fleeing.
3. Leave the config and make the story chapters heal more aggressively — weakest option, because it
   treats a symptom and the lead can always be unlucky.

### ‼ WHAT IS NOT YET KNOWN
This was measured under the **harness driver**, which does not necessarily mirror StoryMode's
overrides (`04-HANDOFF`: "a harness driver must mirror the OVERRIDES of the mode it stands in for").
**Whether production StoryMode recovers from this `BotModeError` is UNMEASURED.** Do not record it
as a live run-killer until a batch log shows it; do not record it as harmless either. The wedge
itself — Manual, mid-battle, 18,000 frames — is real in the harness.

### ✅ THE FIX (user directive: "carry out the fight until it wins/loses so it does not get wedged")
Ladder is now **rotate → flee → FIGHT ON**; no default path can end the run.
`_fight_on()` returns ONE action for ONE turn (strongest move, slot 0 if nothing ranks — the game
substitutes Struggle, which still ends the battle). ‼ It does **not** loop: the bound is the battle.
A TRAINER battle no longer raises either — gyms/rivals/bosses can never be fled, which is normal.
`POKEBOT_LEADCANTBATTLE_A=1` restores the old raise. Full trapping set + the game's "can't escape"
strings are in `_escape_block_reason()`'s docstring and in `07-CHANGELOG` 2026-08-11.

**Why it was fleeing with a healthy bench:** `lead_cannot_battle_action` asks *"can the LEAD
fight?"*, never *"can ANYONE fight?"*. **Nothing trapped it** — the opponent was a wild Torkoal
(White Smoke) and Sceptile was far faster. The 0 came from the run formula's own **u8 wraparound**
(decomp `u8 speedVar = (speed*128)/oppSpeed + runTries*30`), which in the real game just fails ONE
attempt — our reader turned it into "impossible" permanently.

**Proof:** ✅ `repro_lead_cannot_battle.py`, 34 checks, fault-injected red then restored green.
❌ **NO live A/B** — the reproduction was lost before it ran (`08-MISTAKES`: the fixture was pinned
*after* an in-flight job overwrote it). **Do not record the fallback as live-proven.** ✅ What the
void A/B does show: OLD and NEW both completed the chapter identically, so the change is
**behaviourally inert on a healthy run**.

**Repro (to re-obtain a wedging save):** drive `--driver magmahideout` from a `magma_door.ss1` whose
lead takes a bad wild encounter on 4F, or lower `hp_threshold` in a profile to force it. ‼ **md5 the
save and put that md5 in the A/B command.**

### ‼‼ KI-52 REPRODUCES DETERMINISTICALLY — AND "MINT A FRESH SAVE" IS NOT A REROLL (2026-08-11)
Two rounds of *mint a new `magma_door.ss1` via `magmatravel`, then drive the dungeon* produced
**byte-identical failures**:
```
mintrun1  30 [TURN] lines  md5 ed42726c80d4
mintrun2  30 [TURN] lines  md5 ed42726c80d4   -> IDENTICAL
both stop at MAGMA_HIDEOUT_4F (15,6), Sceptile L46 10/128, five healthy mons on the bench
```
‼ **Even though the two minted saves have DIFFERENT md5s** (`58a191a14478`, `8171734228f3`).

**Why: the travel leg is DETERMINISTIC.** Both `magmatravel` runs reported the *identical* frame
count (`frames=3244720`) and identical result fields. The saves differ only in incidental bytes
(in-game clock / RTC); the game state that drives the dungeon is the same every time. ⇒
**`--driver magmatravel` cannot produce a VARIED anchor, so re-minting is not a reroll and running
it repeatedly is waste.** The loop was stopped after round 2 rather than running round 3.

⇒ **The blocker for §Ch16 is KI-52, not the Maxie fight.** From the current `post_mtpyre.ss1` the
chapter now dies to a wild Geodude on 4F **before ever reaching Maxie**, every single time. The
earlier Maxie analysis (confusion + the Camerupt heal) came from the OLD `magma_door.ss1`, whose
party was a level lower (`Sceptile L44` vs `L46`) — it is still true of that save, but it is no
longer the thing standing in the way.

**What would actually vary a run** (none tried): a different starting anchor than
`post_mtpyre.ss1`; a party/level change; or fixing KI-52 so the wild fight stops ending the run.
The third is the real fix and it is the one that needs the scope decision.

---

---

# ARCHIVED 2026-08-12 — KI-55 (RESOLVED 2026-08-11), moved out of `05-KNOWN-ISSUES.md`
> Moved verbatim, not rewritten. The live file keeps a stub pointing here.

## KI-55 — ✅ RESOLVED 2026-08-11 by batch `20260811-130454`: the STATUS TAX is **32.6% vs a 3.8% control, z = +62.2**

**Built before changing anything:** `tools/story-dev/probe_status_tax.py` counts turns where a move
was **selected but never executed** (PP did not decrement on the actor's next selection of that same
move). ‼ A MISS still consumes PP, so frozen PP is "it never acted", not "it missed".

**Result over the instrumented logs (588 turns):**
| bucket | lost / total | rate |
|---|---|---|
| turns while **incapacitated** (Confused/Sleep/Freeze/Paralysis/Flinched/Recharging) | **18 / 28** | **64.3%** |
| turns while **clean** — the CONTROL | **0 / 290** | **0.0%** |

**The control is what makes this trustworthy: zero false positives across 290 clean turns.** The
instrument is sound.

### ‼ WHAT IS *NOT* ESTABLISHED — the rate
n is **28 incapacitated turns across roughly TWO distinct battles**. Verified by md5-ing each run's
turn telemetry: `ki52-old` and `ki52-new` are byte-identical (the same fight, as designed), and
`mh-status` is a different one. **Replaying one fight five times is not five samples** — the exact
error that produced today's withdrawn "the chapter wins 1 in 3". ⇒ **Do not change battle policy on
this.** A policy change touches every mode using `DefaultBattleStrategy`.

### ‼ TWO FLAWS THIS PROBE HAD, BOTH CAUGHT BY ITS OWN CONTROL
1. **Not every "status" incapacitates.** `status_temporary` includes `Foresight`, `Wrapped`,
   `Substitute`, `FocusEnergy`. Counting them diluted the tax — `mintrun1/2/3` read `0/4 lost` on
   Foresight/Wrapped beside `2/2` on Confused. Only the incapacitating set is counted now.
2. **The clean control was CONTAMINATED.** The status field only exists from 2026-08-11, so all 180
   older logs carry no marker and their *confused* turns were being counted as *clean*. The first
   draft's headline (6.2% over 145,683 turns) was therefore meaningless as a comparator. The control
   is now computed **only over logs that carry the instrument**, and uninstrumented logs are
   excluded and counted separately.
‼ A silent zero is reported as "the instrument was not present", never as "no status occurred".

### ✅ THE BATCH RESULT (n is now real)
| bucket | lost / total | rate |
|---|---|---|
| incapacitated | **960 / 2,945** | **32.6%** |
| clean CONTROL | 1,259 / 33,017 | 3.8% |
**8.5×, z = +62.2, RESOLVABLE**, over 47,789 turns from 36 independent lane logs.

‼ **My earlier n=2 figure of 64.3% was ~2× TOO HIGH** — the Magma Hideout fight is worse than
typical. ‼ **And the control found a gap in the instrument**: `Infatuated` skips turns without
consuming PP and was missing from the incapacitating set, so real losses sat in the clean bucket.
Added. **A control that is not ~zero is telling you the buckets are wrong.**

⇒ **A status response is now justified by a RATE, not an anecdote.** It remains a battle-policy
change touching every mode using `DefaultBattleStrategy`, so it is still the user's call — but the
evidence bar this needed has been met.

### HISTORICAL — the pre-batch position
Run a batch on the current build and re-run this probe over it. That single batch would also give
the **first outcome data for three promoted-but-unmeasured changes** (`#24-teachmsgstall`, KI-51,
KI-52), none of which has any batch evidence. Only then is a status-response policy justifiable.

---

---

# ARCHIVED 2026-08-12 — KI-67's superseded first half, moved out of `05-KNOWN-ISSUES.md`
> Superseded by the FULLY CLOSED section. Kept for the harness design notes.

## ✅ KI-67 — PRODUCTION HALF FIXED 2026-08-12; the DRIVEN half is still open

‼ **MY ORIGINAL FILING ABOVE OVERSTATED IT ON TWO POINTS**, both corrected by two independent
reviews that agreed:
* **§Ch18 does NOT burn three attempts.** Its re-entry navigation (`mossdeep_gym.py:515-521`) sits
  OUTSIDE the `try`, so after a whiteout `_on_gym_map()` is False, the navigation runs, and the
  abort escapes on attempt 2. Only §Ch19 wrapped all five legs and burned the full budget.
* **The run does not die.** `StoryMode.run` branches on `self._whiteout_pending` (not on the
  exception), so even the fabricated "still unset after 3 attempts" error takes the WHITEOUT
  recovery path and re-runs `_play()`. ⇒ Severity is **wasted budget and a lying error message**,
  not a dead run. The real bound has always been `run()`'s 40-recovery cap, not the chapters' 3.

**‼ AND THE WORST PART WAS NOT THE SWALLOW — IT WAS THE LAUNDERING.** Our inner loops catch an
error and raise a BRAND-NEW one naming the goal they failed to reach. After a whiteout those
messages are **fabricated diagnoses**: *"the Team Magma NPCs are still standing on the only land
bridge"*, *"could not clear the grunt plugging the stairs"*, *"cannot reach Steven"* — confident,
plausible, and wrong, about maps the player has already left. This project has lost multi-day
investigations to exactly that shape (the reachability failures behind KI-59/KI-60).

**THE FIX (two mechanisms, because one is not enough):**
1. `StoryAbort(BotModeError)` — identity while the ORIGINAL object is in flight. Subclassing means
   every existing `except BotModeError` behaves exactly as before.
2. **`reraise_if_aborting(error)` — keyed on the LATCH**, which survives conversion. This is the one
   that matters: a type-based guard cannot see an abort that an inner loop has already replaced with
   a fresh error.
Applied at the two chapter loops plus the three §Ch19 laundering sites and §Ch18's `require_in_gym`.

**PROVEN** by `repro_whiteout_abort.py` (10/10, no emulator) and `repro_gym_whiteout_guard.py`
(now 5/5). The controls are the point:
```
ARM A control  old loop      -> 3 attempts burned, 2 fabricated reasons   (the bug reproduces)
ARM C control  type-only     -> laundered into "NPCs still on the bridge" (why the type is not enough)
ARM C          latch-keyed   -> StoryAbort survives the conversion
[5]            real whiteout -> escapes after ONE attempt, not three
latch CLEAR    -> reraise_if_aborting does nothing (ordinary retries still work)
```


---

# 📦 ARCHIVED 2026-08-13 — KI-14 / KI-15 / KI-16, all ✅ FIXED same-day in July 2026

> Moved out of `05-KNOWN-ISSUES.md` verbatim, unedited, because that file crossed its 3000-line
> budget (lint rule R3) when KI-70/KI-71 were filed. Nothing was deleted.

## KI-14 ✅ FIXED 2026-07-23 (same day) — teach flow stranded the START MENU open → travel wedge → Manual
The Ch10b teach itself WORKED (the new compat picker chose Grovyle L29 on a Treecko run
— validation of #24-hm-learner on a non-Mudkip start). The failure is AFTER: the
teach's "hard menus-closed guarantee" B-mashes out of the BAG but its exit condition is
`game_state == OVERWORLD` — which is ALREADY true while the START MENU is open (the
start menu is an overworld state), so the loop exits with the menu still up
(`Task_ShowStartMenu` active, controllable=False). Then the Fallarbor travel wedges:
`wait_until_truly_controllable` presses nothing by design, and `_wait_until_cutscene_over`
— since the 2026-07-23 museum fix — only presses when a script is active or a text
printer waits, and an open MENU is neither → nobody ever closes the menu → 8000-frame
"cutscene did not end" derail → recovery hits the same wall → Manual at Mauville (32,15).
CLASS: a latent bug (menu left open, previously papered over by blind B-mash recovery)
EXPOSED by the museum fix making the presser conservative. FIXED (both halves, same
day): (a) the teach's hard-close loop breaks only when the overworld is MENU-FREE
(`_menu_task_active()` — Task_ShowStartMenu/ListMenuDummyTask/ChooseMonInput — plus
avatar controllable); (b) `_wait_until_cutscene_over` also presses B while a menu task
is open (B closes menus, can never start a dialogue → museum guarantee preserved).
PROVEN: story run rocksmash_got.ss1 → teach → Mauville → Rt 111 → 112 → Fiery Path →
Rt 113, 0 derails (ki14_run1); museum repro re-run clean.

## KI-15 (2026-07-23) — post-battle STORY-RESUME hang ✅ FIXED 2026-07-24 (pending batch validation)
**FIXED via three complementary changes, each proven on a captured state** (changelog
2026-07-23 "KI-15 FIXED" has the full detail; 08-MISTAKES 2026-07-24 has the two lessons
from failed intermediate designs):
1. `navigate_to` no-progress bail → `NavigationStuckError` after ~8 progress-free re-paths
   (walking.py; covers the ROUTE 104 `(5,6)↔(5,7)` oscillation; A/B: repro_navigate_stuck.py).
2. `_wait_until_cutscene_over` KEPT at its old museum-green behavior (parked waits = free;
   contract pinned by repro_cutscene_waiting_msg.py) — the wedge is reader-identical to a
   dialogue tail and both ignore B, so the rider cannot safely clear it (3 attempts failed).
3. The clearer: StoryMode run-loop nudge — waiting + no scripts + **position frozen** for
   240 frames → ONE A → 1200f cooldown. Only the wedge blocks movement, so only it matches.
   (A on the wedge clears it instantly — proven on `ki15_gotaway_wedge.ss1`; never
   A-mashes a live dialogue — `ki15_nurse_wedge.ss1` lesson.)
Faithful goods_recovered runs: previously-terminal wedge episodes now self-recover
(one 90k run crossed to Dewford/Granite Cave, 0 Manual). REMAINING: watch the overnight
fresh batches — if a lane still shows a 20k stall with `cb=ReturnFromBattleToOverworld`,
capture the state (probe_stuck_state.py / probe_press_variants.py are the tools) rather
than re-tuning thresholds blind.

### (superseded original diagnosis below, kept for the record)
## KI-15 (original) — post-battle STORY-RESUME hang after an inline battle ⚠ RE-DIAGNOSED 2026-07-23
> ‼ **The original write-up (an "after-faint PARTY_MENU chooser hang" with a 1-HP Wonder Guard
> Shedinja) was a MISDIAGNOSIS.** It was never supported by a log — `grep -r "SHEDINJA fainted"`
> across EVERY livetest run.log (current + archive) returns ZERO hits. The party/coords/stack
> cited (Marshtomp/Shedinja/Swellow/Poochyena/Ninjask at (7,9)) do not appear in any captured
> hang. A long repro session chasing the party-menu sweep (burn-injection, `faintrepro`) PROVED
> that sweep handles rapid back-to-back faints correctly (0 livelock over 5 successive faints).
> **Do NOT chase the party menu. The real bug is below.**

**Real symptom (from 3 CONFIRMED 20k-frame hangs — 002057/run05, archive/…-093125/run01,
archive/…-101814/run01).** After an INLINE battle (trainer or wild) fires during story
NAVIGATION or a scripted scene, the story flow fails to resume. All three share the same
post-battle stale reads: `state=OVERWORLD`, `cb=ReturnFromBattleToOverworld`,
`instr=BattleScript_PayDayMoneyAndPickUpItems`, `tasks=[]`, `bt='… gained … EXP'` / `'… won $…'`.
Two distinct manifestations observed:
  1. **Stuck cutscene-wait** (002057/run05, RUSTBORO, `return_devon_goods_and_get_pokenav`):
     `_wait_until_cutscene_over` rides forever. Its 8000-frame timeout RAISES, the caller's
     recovery retries, the retry re-hits the same state → raise/retry loop → 20k watchdog.
  2. **Navigator oscillation** (both archive hangs, ROUTE 104): after a trainer battle the
     player BOUNCES between two adjacent tiles `(5,6)↔(5,7)` — `navigate_to` re-paths back and
     forth and never advances.
**Frequency.** ~1/5 lanes; intermittent — needs a random battle to interrupt at a specific
navigation/scene moment. The HEALTHY version of the same scene rides fine.

**Why the existing phantom-script escape does NOT cover it** (`_wait_until_cutscene_over`,
early_game.py). The escape (added for the Route-111 Rock-Smash case) needs **600 CONSECUTIVE
`controllable=True` frames** while a script is active. Live trace of the real post-battle scene
(env `KI15_TRACE=<file>`, `story_harness.py goods_recovered.ss1 --driver story`) shows the
parked/multi-part state has `controllable` OSCILLATING (True for a stretch — phantom climbs to
~339 — then a long `controllable=False` stretch that RESETS phantom), so 600-consecutive is
never reached. NOTE the field-script `bytecode_pointer` DOES advance in the healthy multi-part
scene (so a naive "frozen-pointer" escape would need care not to fire on genuine long cutscenes).

**Repro status (2026-07-23).** Faithful `--driver story` runs from `goods_recovered.ss1` ride the
scene cleanly (no live permanent hang caught yet — the hang needs the rare battle-interrupt race).
Instrumentation is IN PLACE and env-gated (`KI15_TRACE`) inside `_wait_until_cutscene_over`
(reader profile + script pointers + escape/raise markers) — the tool to catch the live state next.
**NEXT STEPS (pick one; the fix is NOT to be guessed without catching the permanent state):**
  (a) Reproduce the ROUTE 104 `(5,6)↔(5,7)` navigator oscillation from a near-there save — the
      most concrete manifestation (2/3 hangs, identical tiles) — and fix the re-path bounce.
  (b) Catch the live cutscene-wait hang with `KI15_TRACE` set on a batch, capture the exact
      reader/pointer profile, and make `_wait_until_cutscene_over` escape it robustly (tolerate
      `controllable` oscillation; e.g. don't reset the parked counter on brief False blips, and
      turn the 8000 raise into a clean return when the state is the stale post-battle signature)
      WITHOUT false-firing on genuine long multi-part cutscenes (whose pointers advance).
Do NOT patch the battle handler for this — it is not a battle-handler bug.

## KI-16 ✅ FIXED 2026-07-23 (same day) — the wedge was _smash_rock returning before EventScript_SmashRock finished
**Symptom.** ALL 5 lanes resuming from `wattson_done.ss1` hang identically at frame f74383,
at Route 111 (18,99), in `travel_to_fallarbor` → `_enter_warp_by_navigation` (Fiery Path
south door) → navigate_to → follow_waypoints → ensure_facing_direction. A WILD BATTLE ends
right at (18,99) (`bt='MARSHTOMP gained 110 EXP'`), and the post-battle
ReturnFromBattleToOverworld transition leaves the avatar unable to move; the navigation
retry loops with no progress. NO safety net fires (not the story 18k watchdog, not the
follow_waypoints 20-frame timeout, not ensure_facing_direction) — the spin location is
elusive (bounding ensure_facing_direction / navigate_to did NOT catch it; reverted those).
**Scope.** SPECIFIC to the wattson_done save's state/RNG — FRESH runs pass travel_to_fallarbor
fine (Pass 1: 3/5 reached HEAT BADGE), and `rocksmash_taught.ss1` (a nearer post-Wattson
checkpoint) travels the same code cleanly end-to-end. So it is a NARROW post-battle navigator
robustness gap this particular save triggers, not a broad regression.
**REPRO (deterministic).** `story_harness.py wattson_done.ss1 --driver story --frames 120000`
→ HANG at f74383. Use it for a focused fix (the post-battle transition freeze class —
Bug 2 lineage; the real fix likely ensures the navigator waits for a truly-controllable
avatar after a mid-navigation battle, or prevents the wild encounter on that leg).
**WORKAROUND.** For milestone/continuing validation use `rocksmash_taught.ss1` (proven), not
wattson_done, until KI-16 is fixed. Consider regenerating wattson_done (may be a stale-state
artifact like the rocksmash_taught menu case).

## KI-17 (2026-07-24) — after-faint party-menu RESHOW freeze (severity: HIGH, 2/5 fresh lanes)
> ‼ This is the bug the original (later "re-diagnosed") KI-15 write-up was actually
> describing — the Shedinja/Ninjask/(7,9) party from that write-up appears verbatim in
> batch 20260724-004252/run04. It is REAL, distinct from the (fixed) KI-15 resume wedge,
> and now the top intermittent.
- **Symptom:** an inline wild battle where a mon faints opens the after-faint chooser;
  a replacement IS chosen (cursor on a living slot, action=1), and the game then freezes
  mid-transition back to battle: `state=PARTY_MENU`,
  `main_cb=CB2_SETUPRESHOWBATTLESCREENAFTERMENU`,
  tasks `Task_ReturnToChooseMonAfterText`+`Task_PrintAndWaitForText` (which never run —
  that CB2 doesn't pump tasks), `instr=BattleScript_FaintedMonTryChoose`. 20k-frame hang;
  `handle_fainted_pokemon`'s sweep presses A/B/Down to no effect (probed: the state is
  INPUT-IMMUNE, video on or off).
- **Evidence/states:** `saves/ki17_partymenu_wedge.ss1` (run05: Skitty 40HP alive,
  Taillow+Grovyle fainted) + `saves/ki17_partymenu_wedge2.ss1` (run04: the Shedinja
  party). ⚠ loaded states stay frozen — good repro material.
- **Suspected cause:** the ReshowBattleScreenAfterMenu state machine parks on one of its
  gfx-reload steps (or the savestate merely preserves a live race). NOT a renderer
  dependency (video=True doesn't advance it). Needs a decomp read of
  `CB2_SetUpReshowBattleScreenAfterMenu` / `gReshowState` — Gemini escalation drafted in
  `sandbox-pokebot/profiles/GEMINI-PROMPTS.md` (2026-07-24 entry).
- **Workaround:** none in-run yet; frequency ~2/5 fresh lanes at long horizons. The
  watchdog kills the run (no silent corruption). NEXT: decomp-verify what advances
  gReshowState; if it's waiting on a paletted/task resource our sweep's button timing
  starves, fix the sweep's press cadence; consider a bounded state-write fallback ONLY
  per the faithfulness rules (documented last resort).

## KI-18 — DOUBLE-battle replacement swap loops forever (user report, 2026-07-24) — HIGH

**Symptom.** In a double battle in Mauville Gym the bot reordered the party over and over —
Shedinja shuffling slot 0 ↔ slot 4 while Grovyle/Ninjask/Mightyena rotated — for ~23,000 frames,
`controllable=False`, until the mode dropped to Manual. A healthy **Beautifly L23 67/67** was
available the whole time and never came in.

**Evidence** (user log `7881406e-...20260724233227.log`):
```
party=['Grovyle L22 0/56', 'Ninjask L21 11/61', 'Mightyena L21 67/67',
       'Beautifly L23 67/67', 'Shedinja L20 1/1']
repeated [PARTY] slotN X -> Y reorderings, never resolving
stack: StoryMode._prepare_for_fight :1108 -> train_team early_game.py:1680 -> _story_spin
```
Grovyle is at **0 HP** (fainted), so this is the after-faint replacement path.

**HYPOTHESIS — NOT YET PROVEN.** A replacement picker written for SINGLE battles: in a double
battle TWO slots are already on the field, so the chosen mon can be one the party menu refuses
(already active / "NOT ABLE"), and the bot retries forever. Two existing comments in our own code
describe adjacent symptoms and should be read first:
* `story_mode.py:~185` — "rotating into a weak/underlevelled bench can HANG the in-battle
  party-menu switch (battle_action_selection.py — `while PARTY_MENU: press A`)" — the Roxanne hang.
* `story_mode.py:~1983` — "the party menu shows an incompatible mon as NOT ABLE and refuses the …"

Shedinja is a likely trigger: 1 max HP + Wonder Guard means one check can judge it unusable while
another still selects it.

**Do NOT patch on the hypothesis.** Reproduce first: force a double battle with a fainted lead
and Shedinja on the bench, and log (a) which function chooses the replacement, (b) what the party
menu reports for each slot, (c) which press sequence the swap driver issues. The single loop in
`battle_action_selection.py:132` (`while get_game_state() == GameState.PARTY_MENU`) is the prime
suspect for where it spins.

**Why HIGH:** it is a run-killer in a mandatory gym, and **Mossdeep gym 7 is a required DOUBLE
battle**, so this will block Ch15 as well as costing runs now.


---

# 📦 ARCHIVED 2026-08-13 (second batch) — KI-11, ✅ RESOLVED 2026-07-22

> Moved verbatim from `05-KNOWN-ISSUES.md` when KI-63's resolution pushed that file back over
> its 3,000-line budget (lint rule R3). Nothing deleted.

## KI-11 — Oceanic Museum entrance grunt-sealed at Devon-goods time — ✅ RESOLVED 2026-07-22
**RESOLUTION:** NOT a state bug — a missing STORY STEP. The museum grunts clear when you talk
to **Dock at Stern's Shipyard** (`SlateportCity_SternsShipyard_1F_EventScript_Dock` runs
`setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA`). User-supplied + decomp-confirmed; built into
`deliver_devon_goods_to_stern` (Shipyard→Dock→museum). The doc was wrong (had the museum
freely enterable) — corrected in §Ch8b. This is the motivating case for the /validate-docs
process. Original write-up kept below for reference.

- **Symptom:** `deliver_devon_goods_to_stern` cannot reach the museum. The doors are city
  warps (30,26)/(31,26); the ONLY tiles below them, (30,27)/(31,27), are occupied by two
  Team Aqua grunts (obj id 18/5, `SlateportCity_EventScript_AquaGrunt2/1`). The whole
  y=27 row from x=22-31 is a grunt wall (gap at x=27, but (27,26) above it is collision).
  So the museum is physically SEALED — navigate_to (interior or door tile) plan-fails, and
  a walk-into-door bumps the grunt forever.
- **What's verified (probes 2026-07-22):** all 11 outside grunts share hide-flag
  `FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` (882). It is UNSET by default (confirmed on an
  INDEPENDENT fresh game at Rustboro AND on slateport.ss1), `VAR_SLATEPORT_CITY_STATE=0`,
  and the SlateportCity map.json has NO coord-trigger near the museum to reposition them
  (its only coord_event is the Battle Tent Scott scene at (10,13)). The 2F Stern-fight
  grunts are SEPARATE 2F objects (id 2-4 spawned at the stairs), not this outside crowd.
- **The contradiction:** vanilla canon = the museum IS enterable on the first (Devon-goods)
  visit, yet structurally it's sealed with flag 882 unset. Something clears/repositions the
  crowd that our static read isn't capturing (a map ON_TRANSITION/ON_FRAME script setting a
  var, an event on the Slateport dock arrival, or the flag being set earlier than found).
- **DO NOT guess a state-write** (setting flag 882 hides the crowd, but proving that matches
  vanilla's exact state at this point needs the mechanism first — house rule).
- **Fastest ground truth = the USER:** on a real first Slateport visit, are Aqua grunts
  blocking the Oceanic Museum doors, or is the entrance clear? Then either build the faithful
  trigger or document the state-write. `deliver_devon_goods_to_stern` (interior logic sound)
  stays defined but UNWIRED; frontier honestly = Slateport arrival.

---

# 📦 ARCHIVED 2026-08-13 (third batch) — KI-6 and KI-7, both resolved July 2026

> Moved verbatim from `05-KNOWN-ISSUES.md` when KI-73 pushed that file over its 3,000-line
> budget (lint rule R3). Nothing deleted.

## KI-6 — Tab bar overcrowds with 6 tabs — RESOLVED 2026-07-19 (sandbox)
- **Symptom:** Adding the Hunt tab (#9) made 6 tabs overflow the ~360px
  tool-column width — labels overlapped/truncated.
- **Fix (done):** tab bar wraps to two balanced rows when there are >4 tabs
  (3+3 for six), legible in both desktop and the handheld drawer
  (screenshots ki6_1/ki6_2). Gamepad focus-nav + tab persist unaffected.

## KI-7 — fly_to() checks the wrong badge for Emerald — ✅ FIXED 2026-07-24 (sandbox)
- **Fix:** RSE branch now gates on BADGE06_GET (Feather Badge) — the stock BADGE03 check
  was FR/LG's. Fixed ahead of Ch14's first Fly usage; DIVERGENCE-LOG entry due at
  promotion (upstream-file edit).

## (old text) KI-7 — fly_to() checks the wrong badge for Emerald (opened 2026-07-19, severity: low)
- **Symptom:** `modules/modes/util/higher_level_actions.py` fly_to() gates on
  BADGE03_GET (Dynamo) — correct for FR/LG but WRONG for Emerald, where Fly
  needs the Feather Badge (BADGE06). Inherited from upstream. Story-mode #24
  must not rely on fly_to as-is; fix when wiring Fly into story navigation.


> Plus **KI-9** (MITIGATED 2026-07-21), moved the same day for the same reason:

## KI-9 — Training spin could silently stall (no encounters) — MITIGATED 2026-07-21
- **Symptom:** during pre-gym / pre-rival training, the grind `spin()` could end up where it
  can't trigger wild encounters (walked out of grass, trainer line-of-sight, bad respawn spot)
  and walk in place FOREVER — the level never reaches target, the stop-condition never fires, no
  whiteout, no derail → hard stall (harness-repro'd from `route116team.ss1`: stuck at Marshtomp
  L16 with no EXP for 20k+ frames). Position/RNG-dependent (a clean fresh run trains fine).
- **Mitigation (done):** `_story_spin` now has a **no-progress watchdog** — if the party gains
  no EXP for `_STORY_SPIN_NO_PROGRESS_FRAMES` (2400) consecutive OVERWORLD frames, it bails so
  the caller (`train_team`'s loop) **re-navigates to the grass and retries**, which un-sticks it.
  Overworld-only counting means a long single battle can't false-trigger it. VALIDATED: the same
  `route116team` run that hung before now trains past L16, beats Roxanne, and reaches the rival
  prep with all fixes. Bounded by `train_team`'s outer guard (500) → derail recovery if truly stuck.


> Plus **KI-10** (MITIGATED 2026-07-22), moved the same day for the same reason:

## KI-10 — Post-sail whiteout can respawn the run on the MAINLAND (Dewford arc) — MITIGATED 2026-07-22
- **Scenario:** the Emerald whiteout respawn point is the last Poké Center USED. After the first
  Briney sail (Ch6), Mr. Briney leaves his cottage (FLAG_HIDE_BRINEYS_HOUSE_MR_BRINEY) and waits
  at his BOAT: vanilla re-sails happen by talking to him on the Route 104 beach (his Route104
  object is un-hidden by the sail script) or at the Dewford dock (12,9). If the bot whites out on
  the Dewford side BEFORE ever healing at the Dewford PC, it respawns at Rustboro's PC — and
  `sail_to_dewford`'s cottage leg (Leg 3-4) would knock on an EMPTY house.
- **Mitigation (done):** `deliver_stevens_letter` heals at the Dewford PC FIRST when starting
  from town, so from the moment the Dewford arc begins, whiteouts respawn IN Dewford (the
  Segment-6 whitelist also stops any Dewford-side resume from re-running the sail). Remaining
  edge: a whiteout in the sail leg itself (route trainers) before the first Dewford heal — rare
  (the leg heals before the rival and fights little), but if hit, the run derails to Manual at
  the cottage instead of re-sailing.
- **Proper fix (when Ch8 needs re-sailing anyway):** teach the sail leg to talk to BOAT-Briney —
  if `HIDE_BRINEYS_HOUSE_MR_BRINEY` is set, engage his Route 104 beach object (live local_id via
  `_talk_to_wandering_npc`-style lookup) instead of entering the house.

> 📦 **KI-11 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — ✅ RESOLVED 2026-07-22. Moved
> verbatim, nothing deleted, to keep this file inside its 3,000-line budget (lint rule R3).


> 📦 **KI-14, KI-15 and KI-16 moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13** — all three

> Plus **KI-19** (FIXED-PENDING-WIRING, 2026-07-24), moved 2026-08-13 for the same budget reason:

## KI-19 — Route 111 training band was paired with a heal 2.2× farther than necessary (2026-07-24) — FIXED-PENDING-WIRING

`ROUTE111_OLD_LADYS_REST_STOP` (map `(18,1)`, door at ROUTE111 `(26,18)`) contains ONE NPC —
`Route111_OldLadysRestStop_EventScript_OldLady`, `flag_id=0` so always present and ungated — that
gives a **full HP + status + PP heal, repeatable**. PROVEN live: all four party members damaged to
1 HP with four different status conditions and spent PP, verified in memory, then fully restored;
repeated a second time with no change in behaviour. Static dump confirms **zero `bg_events`** — no
bed exists in that building.

**Distances from the Route 111 training tile (25,55):** rest stop **96 steps**, Fallarbor Poké
Center **213 steps**.

`training_areas.py` / `_training_area_heal_map()` currently pairs ROUTE111 with
`PokemonCenter.FallarborTown` because that was the only heal verifiable at the time. Re-pairing
needs a heal-at-NPC helper (the existing path is `heal_in_pokemon_center(PokemonCenter.X)`, which
assumes a Poké Center layout) — punch-list `#24-npcheal`.


> Plus **KI-46** (FIXED same day, 2026-08-03), moved 2026-08-13 for the same budget reason:

## KI-46 — Battle ACTION SELECTION spins for ever on an unrecognised controller callback (2026-08-03, FIXED same day)

**KI-45 was one instance of a pattern. This is another, at a different site.**

**Observed**, batch10 (`x4-runs/20260803-164713`): lanes **H2 and H8 both wedged for ~59
minutes**. **H8 completed 0 runs in the whole 180-minute batch**; H2 managed 2 against 4-5
elsewhere. Both stacks stopped at `battle_action_selection.py:55`, with **zero**
`_select_in_menu` dumps — so the KI-45 bound was not involved.

```
BattleListener.fight → handle_battle → handle_battle_action_selection  @ :55
```

**Cause.** `handle_battle_action_selection`'s loop conditions are sound (battle over, or the
main callback moves on). But if the battle stays ACTIVE in turn-action-selection while the
CONTROLLER callback matches none of the branches, control reaches a bare
`else: yield; continue` and spins there indefinitely.

**Fix.** `_MAX_UNRECOGNISED_FRAMES = 600` (~10 s) counting only frames where the state is NOT
recognised; the counter **resets the moment a real decision is made**, so a long multi-turn
battle never accumulates toward it. On exhaustion it reports via
`battle_fault.request_mode_recovery()` — one recoverable derail for an opted-in mode — and
raises `BotModeError` otherwise. The message carries **both observed callbacks**, because that
is the diagnosis: it names the unrecognised state so the branch can be added properly.

‼ **The fix contained the exact bug it was fixing a sibling of.** `BotModeError` is not
imported at that module's top, so the first version would have raised `NameError` *instead of*
the honest error — the same shape as the swallowed `get_party` NameError that made
`#24-leadcounter` silently dead for two batches. Caught only because
`repro_ki46_action_selection_bound.py` **drives the real generator** and asserts the exception
is not a `NameError`. A source-text assertion would have passed.

**Repro:** `repro_ki46_action_selection_bound.py` — drives the generator, and check 5 proves a
battle that ends normally is unaffected (no false positive).

‼ **THE STANDING LESSON (now twice measured): both project-level guards are structurally blind
to any loop on the battle path.** The global watchdog needs an UNCHANGED progress signature and
a battle keeps changing it; the per-run frame budget is KI-36's documented "cannot fire while a
battle handler is on the stack". **Any `while` loop under `BattleListener.fight` has no safety
net but its own bound.** Audit the remaining ones rather than waiting for the next lost lane.

---


> Plus **KI-32** (✅ FIXED 2026-07-29), moved 2026-08-13 for the same budget reason:

## KI-32 — the stall detector was STRUCTURALLY BLIND to any in-battle wedge — ✅ FIXED 2026-07-29
- **Symptom:** user log `20260729-122709`. A mid-battle rotation wedged the PARTY MENU in
  Fortree Gym; the run then held `state=3 controllable=False` at one fixed position for
  **~280,000 frames** and emitted **ZERO stuck dumps** — no generator call stack, the single
  most useful artefact the logger produces.
- **Cause:** `modules/debug_logger.py` stall detection did
  `if st.get("battle_active"): _stall_frames = 0` on EVERY in-battle frame. The intent was
  sound (a battle legitimately holds still mid-turn and during the EXP fill, so the 300-frame
  overworld threshold would false-trigger every turn) but the implementation meant **no
  in-battle wedge could ever be reported, however long it lasted.**
- **Same shape as KI-27** (Weather Institute): the guard could not fire on the thing it was
  guarding. A guard must not share its subject's failure mode.
- **Fix:** a battle now gets a much LARGER threshold, not an exemption —
  `_BATTLE_STALL_DUMP_AFTER = 18_000` (5 min at 60fps, ~60× the overworld threshold and
  ~2 orders of magnitude above the longest legitimate quiet stretch). Overworld sensitivity
  unchanged at 300.
- **Repro:** `tools/story-dev/repro_battle_stall_blindspot.py` — proves a frozen battle now
  dumps, a healthy/changing battle never does, 300/3,000/10,000-frame in-battle quiet is not
  disturbed, the overworld path is unchanged, and a long wedge re-dumps periodically.


## KI-51 — FIXED 2026-08-11: `do_magma_hideout` rode 60,000 frames at an empty overworld after a whiteout, then blamed the wrong thing

**Symptom (found by KI-50's run).** After the whiteout above, the Maxie challenge loop kept
mashing A/B for **18,300+ frames and counting** — 13 `STUCK` dumps — with the step message frozen
at `"at (15, 21), facing Right at Maxie (16, 21)"` while the avatar was standing in
**MAUVILLE CITY (22,6)**, two towns away.

**Root cause.** The loop's only exit condition was `while not _groudon_awakened()`. A whiteout
cannot make that true, so the loop was structurally incapable of noticing it. It *was* bounded
(60,000 frames), so this was never an infinite hang — but the bound's message names the wrong
cause entirely: *"the Maxie challenge never resolved in 60,000 frames"*, when what actually
happened is that the party fainted and the game teleported the player out.

‼ **Same class as the 2026-08-10 lesson, one week later**: *a failure message must report STATE,
not a HYPOTHESIS* — that one said "check the destination is walkable" across three runs where it
always was.

**The fix.** The loop now also watches the map: if the player is off `MAGMA_HIDEOUT_4F` for more
than **300 consecutive frames**, it raises immediately and reports the real state (map, tile,
`party_alive`, frames elapsed) instead of riding the bound out.
* **Debounced, deliberately.** An instant check would risk ending a HEALTHY Maxie fight on one
  odd frame across a battle screen transition — a far worse bug than the one being fixed. 300
  frames (~5s) is longer than any transition here and still ~200x cheaper than the full bound.
* **An unreadable map counts as "still on 4F"**, so a reader error can never end the fight.

✅ **CONFIRMED LIVE 2026-08-11** (`mh-try1`, the anchor retry loop) — the guard fired and printed
its own message, which is the evidence that was missing when this entry was first written:
```
[magmahideout] FAILED: BotModeError: Magma Hideout: left MAGMA_HIDEOUT_4F during the Maxie
challenge without Groudon awakening — almost certainly a WHITEOUT. map=(0, 2) tile=(22, 6)
party_alive=6/6 (was standing (15, 21) facing Right at Maxie (16, 21), 2209 frames in).
```
`map=(0,2)` is MAUVILLE_CITY and `(22,6)` is the whiteout respawn tile — exactly the state the
pre-fix loop rode straight past. **It stopped at 2,209 frames against a 60,000-frame bound**, so
this failure cost ~57,800 fewer frames than it used to. (An earlier run stopping at ~20,600 frames
was NOT counted as proof, because `_check_abort()` is an equally possible raise in the same loop
and that run's stdout was lost. This one prints the message, so it is decided.)

‼ **AND IT CORRECTS ONE OF MY OWN CHOICES: `party_alive=6/6` is NOT diagnostic here.** I put that
field in the message expecting it to be the corroborating fact for "whiteout" — but a whiteout
HEALS the party, so it reads full precisely BECAUSE the thing happened. The diagnosis rests
entirely on the **map**. The field is still worth printing (it rules out "the party is dying right
now"), but a future reader must not treat 6/6 as contradicting the whiteout call.
‼ And note WHY `_check_abort()` did not save the PRE-fix run: it raises on `_STORY_ABORT`, which
**StoryMode's** whiteout handling sets — a harness driver need not mirror that override
(`04-HANDOFF`: "a harness driver must mirror the OVERRIDES of the mode it stands in for"). **A
guard that only works in one of the two ways the code is run is not a guard**, which is the
argument for the map check existing at all.

**Structural proof:** `repro_maxie_whiteout_guard.py` (no emulator, 18 checks — the map read, the
debounce, the unreadable-map default, the STATE fields in the message, and the ordering against
the 60,000 bound). Fault-injected to **2 red**, restored to **ALL PASS**.

**Verified, both directions, on real committed saves** (`map_group_and_number` is a plain tuple;
`== MapRSE.X.value` is a valid identity test):
```
magma_door.ss1      (24,13)  == JAGGED_PASS       -> True    == MAGMA_HIDEOUT_4F -> False
magma_1f_fail.ss1   (24,91)  == MAGMA_HIDEOUT_4F  -> True
```
⇒ on 4F the guard never fires; off 4F it fires. ‼ Note the second control also shows
**`saves/magma_1f_fail.ss1` is misnamed — it stands on 4F, not 1F.**

**Prevention rule.** *A loop whose exit condition is a story flag must ALSO watch for the ways the
game can move the player out from under it. A whiteout satisfies no flag.*

---

## KI-64 — the multi-battle faint replacer would send out the ALLY's Pokémon (2026-08-12, code-verified, ✅ FIXED)

Found while building §Ch19 by an audit of our own code, and confirmed by reading both choosers.

`SPECIAL_BATTLE_STEVEN` (the Mossdeep Space Center) runs `ReducePlayerPartyToSelectedMons` and then
`FillPartnerParty`, which writes Steven's max-IV **Metang L42 / Skarmory L43 / Aggron L44 into
`gPlayerParty[3..5]`** and sets the party count to 6. So `get_party()` returns **six** Pokémon, only
the first three of which are ours.

Both replacement choosers excluded **only the two mons currently on the field**:
* `modules/battle_strategies/default.py` `choose_new_lead_after_faint` — ranks by highest current HP;
* the story override in `plugins/custom_modes/story_mode.py` — ranks by `(incoming, -outgoing,
  -hp_fraction, -level)`.

Under either rule **three fresh high-level mons beat our damaged party outright**, so the chooser
would return the ally's slot. The game then refuses ("Can't switch with ALLY!") and the party menu is
handed a target it can never accept.

‼ **The guard already existed and had ZERO callers in the entire tree:**
`BattleState.is_double_battle_with_partner` (`modules/battle_state.py:288`). Written, never wired up.
`BattleType.Multi` is likewise never referenced anywhere. **FIXED** by cutting the candidate list at
`MULTI_PARTY_SIZE = 3` in both choosers when that property is true.

‼ **Why it was latent, not harmless:** §Ch19 is the FIRST content in this project to reach a multi
battle. Nothing before it could ever have exercised this path — which is exactly why "no bug has
been observed" said nothing about whether one existed.

‼ **AND THE PASSING RUN PROVED NOTHING ABOUT THE FIX.** §Ch19's end-to-end PASS reported
`whiteouts=0` and **zero faints**, so `choose_new_lead_after_faint` was never called once — the fix
rode along entirely unexercised. Proven instead by **fault injection**,
`tools/story-dev/repro_multi_battle_partner.py` (no emulator, milliseconds), **3/3**:
```
ARM A  old rule      -> slot 5 (Aggron)     ALLY   [AS PREDICTED] the bug reproduces
ARM B  shipped code  -> slot 2 (Mightyena)  OURS   [AS PREDICTED] the fix holds
ARM C  plain double  -> slot 5                     unchanged (no over-correction)
```
ARM A is the **positive control** and is the reason ARM B means anything: a fixture where our own
mon happened to win the ranking would pass under both arms and prove nothing. ARM C exists because a
fix that also changed ordinary double battles would be a regression wearing a fix's clothes.

‼ **THE FIRST FIX WAS WRONG TWICE, AND THE FIRST A/B PASSED IT ANYWAY** (corrected 2026-08-12 by an
adversarial review; full write-up in `08-MISTAKES.md`):
1. **It was DEAD CODE on the story path.** The MRO is `StoryItemBattleStrategy` →
   `LevelUpTravelBattleStrategy` → **`LevelUpLeadBattleStrategy`** → `DefaultBattleStrategy`, and
   `level_up.py:41` has its own `choose_new_lead_after_faint`, so the base-class guard never ran.
2. **The `index >= 3` cut was in the WRONG INDEX SPACE.** Opening the battle party menu runs
   `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES `gPlayerParty`. Measured in our own passing
   run (`ch19d.log` f37745): `[Sceptile|Mightyena|Swellow|Metang|…]` → `[Sceptile|**Metang**|Mightyena|**Swellow**|…]`.
   Index 1 becomes the ALLY's Metang and OUR Swellow moves to index 3 — so the cut **offers the ally
   and hides one of ours**, precisely when a replacement is needed.

**The correct fix:** `ally_party_indices(battle_state, party)` in `battle_strategies/default.py`,
keyed on **ORIGINAL TRAINER ID** — identity travels with the Pokémon, position does not. Wired at all
three call sites (`default.py`, `level_up.py`, the story override in `story_mode.py`). It FAILS
CLOSED: an unreadable player/OT excludes nobody rather than everybody, because excluding everybody
would return `None` and push the caller into its full-party fallback — the very bug this prevents.

**Now 5/5 in `repro_multi_battle_partner.py`**, including the two arms that matter:
```
D  permuted array  -> slot 3 (Swellow) OURS   ‼ a positional `<3` rule would have hidden this
                                                 and allowed slot 1 (Metang, the ALLY)
E  LevelUpLead...  -> slot 3 (Swellow) OURS   the class the story bot ACTUALLY calls
```
§Ch19 re-driven end-to-end afterwards: still `ACCEPTANCE: PASS`, `whiteouts=0`.

**RESOLVED, previously flagged unverified:** `BattleType.InGamePartner = 1 << 22` **is** correct —
`battle_tower.c:2122` sets `TRAINER|DOUBLE|TWO_OPPONENTS|MULTI|INGAME_PARTNER`, so
`is_double_battle_with_partner` genuinely reads True in this battle.

⚠ **STILL UNPROVEN LIVE.** Every driven run had `whiteouts=0` and **zero faints**, so no chooser has
ever run in a real multi battle. The repro pins the LOGIC; only a driven loss can pin the whole path.
See KI-66 for the other party scans this fix does NOT cover.



# ARCHIVED 2026-08-13 from 05-KNOWN-ISSUES.md (R3 budget) — KI-63's SUPERSEDED original filing
> ‼ KI-63 is RESOLVED; its current entry lives in `05-KNOWN-ISSUES.md`. This is the ORIGINAL
> 2026-08-12 filing, kept verbatim for its diagnosis.

## KI-63 — NO party member can learn Dive, and the party is full: §Ch21 is BLOCKED (2026-08-12, MEASURED)

Measured on `post_mossdeep_gym.ss1` by `tools/story-dev/probe_ch19_hazards.py`:
```
party 6/6: Sceptile L48, Zigzagoon L15, Swellow L40, Skitty L17, Mightyena L44, Castform L36
Dive learners in party: NONE
```
Only 76 species learn Dive and none of ours is among them.

**‼ WHAT THIS DOES AND DOES NOT BLOCK.** Receiving **HM08 is a scripted gift and needs no learner**,
so §Ch19 (Space Center) and the Dive hand-over in Steven's house are unaffected — `FLAG_RECEIVED_HM_DIVE`
will set normally, and it is that flag which removes the Seafloor Cavern entrance guard. What is
blocked is **USING** Dive, i.e. actually reaching the Seafloor Cavern (§Ch21).

**Why it is not a small fix.** The party is FULL, so a catch would go to the PC, and
`early_game.py:4294` already refuses exactly this case:
> `No party mon can learn {move} and the party is full — needs PC box management (#24-pc) or a
> manual swap.`
And `#24-roster`/`#24-pc` is itself gated by KI-54 (the box is empty and the deposit path was
measured harmful). ⇒ **`#24-pc` is a PREREQUISITE of the Seafloor Cavern, not a later nicety.**

**‼ The natural swap is not the obvious one.** Zigzagoon L15 is the party's ONLY Surf carrier, so it
cannot simply be dropped. A **Wailmer or Tentacool** — both on the water this arc already crosses
(Routes 124/126/127/128) — learns **Surf and Dive**, which makes it a single swap that covers both
duties. To settle before building: confirm the encounter tables in `modules/data` rather than
trusting this note.

‼ **NOW REPRODUCIBLE — `tools/story-dev/probe_dive_learner.py` (added 2026-08-12).** The correction
below was first committed as **docs only**, labelled "measured", with **no script and no artifact**.
An adversarial pass called that out: every number was independently re-derived and turned out to be
right, but it was *right by a good recall, not by anything anyone could re-run* — the exact failure
this project's rules exist to prevent, committed by the agent enforcing them. The probe reads
`species.json` + the encounter index and reproduces all of it:
```
species that learn Dive: 76      Dive learners in the party: NONE
evolution escape: NONE — a CATCH IS MANDATORY  (Zigzagoon->Linoone, Skitty->Delcatty, neither learns it)
 50%  Shoal Cave (Low Tide), Entrance Room   Spheal  L26-32  +SURF (covers BOTH duties)
 15%  Route 120                              Marill  L25-27  +SURF      <- tide-free fallback
```
‼ It carries a printed CONTROL on every id→name resolution, and they earned their place at once:
the first draft read `evolutions[].target_species` as a national dex number and produced
*"Zigzagoon -> Slaking"*. That wrong mapping would still have returned the RIGHT ANSWER to the
question being asked ("no evolution learns Dive") — a correct conclusion from garbage data.
**Sanity-check an id→name mapping against a pair you already know before trusting it on pairs you
do not.**

**‼ CORRECTION 2026-08-12 (measured, supersedes the swap suggestion above).** **Wailmer is ROD-ONLY
and the bag has no rod**, and Tentacool is a surf slot spanning L5-35. The better candidate from our
own species data is **Spheal** — ~50% of the Shoal Cave low-tide **land** table at L26-32, Ice/Water,
and it learns **both Surf and Dive** with no rod needed. Also: `RECEIVED_SUPER_ROD` is **False** and
the free Super Rod is in `MOSSDEEP_CITY_HOUSE3`, which would additionally make **Sharpedo** (40% of
casts, L30-35) available — it learns both too. ⚠ Shoal Cave HIGH-tide rooms returned **no encounter
header at all** in our ROM, so tide timing matters. Still blocked by the 6/6 party + KI-54.



# ARCHIVED 2026-08-13 from 05-KNOWN-ISSUES.md (R3 budget) — KI-67's original filing (CLOSED)
> ‼ KI-67 is FULLY CLOSED; the closing write-up remains in `05-KNOWN-ISSUES.md`. This is the
> original 2026-08-12 filing, kept verbatim for its diagnosis.

## KI-67 — the chapter retry loop swallows the WHITEOUT ABORT (2026-08-12, ✅ CLOSED — original filing, kept for the diagnosis)

`StoryMode.on_whiteout` sets `set_story_abort(True)`; only `StoryMode.run` clears it.
`do_space_center_chapter` catches `BotModeError` — **including the abort raised by `_check_abort()`**
— and retries in place with the latch still set. Attempts 2 and 3 therefore raise instantly at the
first `_check_abort()` inside `_navigate_riding_out`, so **one whiteout consumes the entire retry
budget in a handful of frames** and the chapter reports three failures, two of them fabricated.

‼ **And the harness cannot see it**: `set_story_abort` appears **zero** times in `story_harness.py`,
so every driver's `on_whiteout` only increments a counter and `_check_abort()` is effectively dead
code under test. `SpaceCenter1Mode`'s docstring claims it "MIRRORS StoryMode's own choice" — it
mirrors `on_battle_started` and **not** `on_whiteout`. So every retry-path claim in these docstrings
is untested prose.



# ARCHIVED 2026-08-13 from 05-KNOWN-ISSUES.md (R3 budget) — KI-39 (corrected & largely resolved 2026-07-31)

## ‼ KI-39 — CORRECTED AND LARGELY RESOLVED 2026-07-31. Read this before the section above.

**The KI-39 entry above states the cause wrongly, and the handoff repeated it.** The claim
was *"`calculate_path` only spans directly-connected maps"* and *"the bot has NO cross-map
overworld route planning"*. Both are false. Measured live from `rocksmash_taught.ss1`
(Mauville 32,15) with the SAME `calculate_path` the production path uses
(`tools/story-dev/probe_journey_legs.py`, `probe_journey_why.py`, `probe_journey_walls.py`):

* `map_path.py` assigns **every** edge-connected map a global offset and a shared `level`,
  and its own docstring says it "supports paths across several maps, but only if they are
  connected". Mauville, Routes 110/111/112/116/117 and Verdanturf are **all level 459** — so
  `calculate_path` was trying, and failing at TILE level, not refusing to plan.
* Partial reachability proves it: **ROUTE110 17/125 tiles reachable, ROUTE111 11/173,
  ROUTE117 22/41, VERDANTURF 14/23.** A planner that could not cross maps would score 0.

### The four blocked trips had FOUR DIFFERENT causes. Only one was route planning.

| trip | measured cause | status |
|---|---|---|
| Mauville → **ROUTE116** | Verdanturf declares a North map CONNECTION to Route 116, so the union-find merges them into one region — but **0 of 40 sampled Route 116 tiles are walkable from Verdanturf**, while the RUSTURF_TUNNEL door at VERDANTURF (8,1) is. The real link is a **warp inside one region**, and `WarpGraph.plan()` returns `[]` for any same-region pair. **This is the genuine KI-39.** | **FIXED** (see below) |
| Mauville → **ROUTE110** (12,60) | reachable strip ends at y≈20 (column 12); the rest is behind the cycling-road gate structures — same warp-inside-a-region class | fixed in kind; specific tile still needs the gates |
| Mauville → **ROUTE112 / FIERY_PATH** | the **Rock Smash twin-rocks choke on ROUTE111 at (18,101)**. Column-by-column probe: reachable y≥102, blocked y≤101 across columns 17–20. Route 112 scores **0/76**, and Fiery Path's only two doors are both on Route 112. | **NOT a planner problem** — see KI-41 |
| Mauville → **ROUTE111** (25,55) | the Go-Goggles desert. Genuinely gated; the south strip is reachable, the north is not. | correct refusal |

### The fix that shipped
`WarpGraph.warp_candidates()` — warp planning at **MAP** granularity instead of REGION
granularity, so a warp route can be returned even when start and goal share a region. The
map-level adjacency is now kept (it was previously consumed by the union-find and discarded);
`CACHE_VERSION` 1→2 so stale caches rebuild rather than silently loading a degraded graph.
`navigate_to_anywhere` now (1) asks `calculate_path` whether a plain walk works — unchanged
fast path if yes — and only then (2) asks for warp candidates and **validates each one's
first leg with `calculate_path` before committing**, remembering warps it has taken so a
re-plan cannot ping-pong.

‼ Also fixed in the same change: `navigate_to_anywhere`'s "did the warp fire?" test compared
**regions**. A warp between two maps of the same region — exactly the class this makes
plannable — leaves the region unchanged, so a *working* warp would have been reported as
`"Warp at … did not trigger (locked or event-gated?)"`. It compares maps now.

### Proof
* `tools/story-dev/repro_journey_planner.py` — 27 checks, no emulator, pins the whole
  topology including the two traps below.
* `tools/story-dev/probe_journey_live.py` (+ `story_harness.py --driver journey`) — live
  fault-injected A/B in the faithful harness:
  **OLD arm `arrived=False map=MAUVILLE_CITY`** (never left the starting map) vs
  **NEW arm `arrived=True map=ROUTE116`, 33,725 frames**, walking Mauville → Route 117 →
  Verdanturf → Rusturf Tunnel → Route 116.

### Two traps found while building it, both pinned by the repro
1. **The progress filter must be NON-INCREASING, not strictly decreasing.** The phantom
   Verdanturf→Route116 connection puts the target 1 hop away, so *nothing* can be strictly
   closer and a strict filter drops the very warp that works.
2. **Banning the previous answer produces junk candidates.** Verdanturf→Route116 offered the
   BATTLE TENT LOBBY and the MART as candidates 5 and 6 — real routes (walk in, walk out,
   then take the tunnel) that make no progress. Harmless only while an earlier candidate
   validates, which is not a guarantee.

### ‼ What this does NOT fix — correct the handoff's expectations
The handoff said `#24-journey` *"unblocks the thing that is killing runs"*. **It does not.**
The counter the ladder names is Machop @ FIERY_PATH, and measured after the fix: a warp route
to FIERY_PATH **is** found (2 candidates, both ROUTE112 doors) and **neither first leg is
walkable**, because of the Rock Smash choke. The planner was never the blocker there — see
**KI-41**, which is now the thing standing between the counter chain and acting.



---

# ARCHIVED 2026-08-13 from `05-KNOWN-ISSUES.md` (R3 budget; content verbatim, nothing deleted)

## KI-64 — ✅ FIXED 2026-08-12 — the multi-battle faint replacer would have sent out STEVEN’s Pokémon (ARCHIVED)

Full diagnosis moved to `31-KNOWN-ISSUES-ARCHIVE.md` on 2026-08-13 to keep this current-state file
inside its 3,000-line R3 budget. Keep only this: **`FillPartnerParty` writes the ally’s team into
`gPlayerParty[3..5]`, so never identify a Pokémon by PARTY INDEX across a battle-menu boundary** —
the party menu physically permutes the array (`UpdatePartyToBattleOrder`). The fix keys on
**original trainer ID** via `ally_party_indices()`; guard is `repro_multi_battle_partner.py` (5/5).
‼ Print the MRO before "fixing" a strategy method — the first fix was dead code on the story path.

---
## ‼‼ KI-68 — §Ch21 IS NOT BLOCKED BY THE PARTY SLOT. **DIVE IS NOT ROUTABLE AT ALL.** (2026-08-12, code-verified) — ✅ **THE ROUTE IS NOW DRIVEN, 2026-08-13**

> ### ✅ RESOLVED IN PRACTICE 2026-08-13 — read this before the (still accurate) analysis below.
> **The first driven dive in this project: `--driver ch20dive`, `ACCEPTANCE: PASS`, `legs=6/6`,
> Mossdeep → `SEAFLOOR_CAVERN_ENTRANCE (10,17)` AND back out to the open ocean.**
> ```
> ROUTE128 (38,27) Deep Water -> dive()  -> UNDERWATER_ROUTE128 (38,27)   [same x,y]
> navigate (38,26) Water Door -> warp    -> UNDERWATER_SEAFLOOR_CAVERN (6,7)
> navigate the pool (6,6)     -> surface -> SEAFLOOR_CAVERN_ENTRANCE (10,17)
> ```
> Everything KI-68 says below is confirmed. **Two corrections:**
> 1. It says *"only (b) is missing, and it is one call."* It is **TWO** calls — `dive()` **and**
>    `surface_from_dive()`. Entering underwater and never surfacing is how a run strands.
> 2. ‼ **THE STATIC WARP DATA IS MISLEADING AT BOTH ENDS.** `UNDERWATER_SEAFLOOR_CAVERN` has no
>    warp or connection into the entrance at all — that edge is a RUNTIME `setdivewarp` from
>    `Underwater_SeafloorCavern_OnResume`. And the table's
>    `(10,18) -> UNDERWATER_ROUTE128 (38,26)` is **not what happens live**: diving there drops you
>    back into the pool at (6,5), and the real exit is three hops. **Drive it; do not read it.**
>
> Measured route + raw transcripts: `ai-research-notes/2026-08-13-ch20-dive-leg-predictions.md`
> and `tools/story-dev/probe_ch20_topology.py`. ‼ **This does NOT make §Ch21 unblocked** — the run
> injected Dive with a debug write. Acquiring a real Dive learner (KI-63) is still open. And see
> **KI-72**: never let the planner choose a surfacing tile.
> ‼ Also read `ai-research-notes/2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md`
> — the cavern INTERIOR is already implemented in upstream code.


**This supersedes the framing in KI-63 and KI-54.** I was one edit away from building the wrong
thing, and an adversarial pass caught it before the code shipped.

**THE MEASUREMENT** (verified by me, not taken on trust):
* `modules/map_path.py:592-593` — `WaypointAction.Dive` and `WaypointAction.Emerge` are **declared
  and assigned NOWHERE in the tree.** A repo-wide search for `WaypointAction.Dive` /
  `WaypointAction.Emerge` returns **zero** assignments.
* `map_path.py:690` — `can_dive()` exists; its only references are its own definition and cache
  lines (`:678, :681, :690-696`). **Zero callers.**
* `modules/warp_graph.py:342` — `continue  # Dive/Emerge need HM08 — excluded on purpose`;
  `modules/story/region_reach.py:68-70` does the same; `modules/modes/util/global_navigation.py:12`
  documents Dive routes as unsupported.
* `modules/modes/util/higher_level_actions.py:682` `dive()` exists, but its only callers are
  `puzzle_solver.py` and a test — **nothing in `modules/story/` or `story_mode.py`.**

⇒ **The planner cannot emit a Dive waypoint.** So the whole "free a party slot → catch a Dive
learner → teach Dive" chain, even executed perfectly, ends at `UnreachableDestinationError` on the
first navigation into a dive spot. **It moves the failure one line down and costs a party member.**

### ‼ REFINED 2026-08-12 (`probe_dive_routing.py`) — "NOT ROUTABLE" ≠ "NOT POSSIBLE"

Do **not** read the above and conclude the Dive content is out of reach. Measured:
* `warp_graph.py:20` and `:342` say it explicitly — *"Dive/Emerge connections … excluded on
  purpose"*. **This is a DESIGN state, not a defect.** A dive is not a warp event at all: it is a
  MOVE used on a deep-water tile that lands you on a different map at the same coordinates, so no
  warp-graph solver could ever offer it and `calculate_path` was never going to.
* **`dive()` ALREADY EXISTS AND WORKS** — `modules/modes/util/higher_level_actions.py:682`, drives
  `Task_UseDive`, and refuses unless the tile really is Deep/Semi-Deep Water and the player is not
  already underwater. So a wrong tile fails LOUDLY.
⇒ **The fix is a CHAPTER that drives the transition, not a change to the planner** — exactly the
pattern already used three times here (§Ch18's `(21,6)` coord-event exit, Steven's bottom-row door
via `_walk_through_warp`, the Magma Hideout Escape Rope). The legs split cleanly:
```
a. surf to the deep-water tile          -> PLANNER   (Surf IS routable)
b. call dive() standing on it           -> CHAPTER   (one call; the missing piece)
c. navigate the UNDERWATER map          -> PLANNER   (ordinary same-map)
d. surface / take the warp in           -> CHAPTER or PLANNER (a real warp)
```

### ✅ THE TOPOLOGY IS FULLY MAPPED, and most of it needs no Dive at all
Read from our own ROM (`probe_dive_routing.py`):
```
UNDERWATER_ROUTE134      (8,8)  -> UNDERWATER_SEALED_CHAMBER
UNDERWATER_SEALED_CHAMBER (7,1) -> UNDERWATER_ROUTE134
SEALED_CHAMBER_OUTER_ROOM (10,2)-> SEALED_CHAMBER_INNER_ROOM
UNDERWATER_SEAFLOOR_CAVERN (6,7)-> UNDERWATER_ROUTE128        (§Ch21)
DESERT_RUINS  (8,29) -> ROUTE111     ISLAND_CAVE (8,29) -> ROUTE105
ANCIENT_TOMB  (8,29) -> ROUTE120
```
‼ **The three Regi tombs are ORDINARY MAP WARPS from routes the bot already reaches.** Only the
**Sealed Chamber unlock** is behind a dive. So the Regi arc is not gated on Dive end-to-end — it is
gated on ONE underwater errand, after which the tombs are ordinary navigation.
‼ Note `UNDERWATER_SEALED_CHAMBER` has **no warp to `SEALED_CHAMBER_OUTER_ROOM`** — that transition
is a SURFACE/emerge, i.e. a second chapter-driven action, not a warp.

‼ **`can_dive()` needs the move KNOWN, not learnable.** Measured on `post_dive.ss1`: `BADGE07_GET`
True, party members knowing Dive **NONE** → it would return False. HM08 being in the bag is not
enough, which is the same distinction KI-63 makes.

### ⇒ THE CORRECT ORDER (and why the obvious order is wrong)
1. **FIRST, prove what the planner needs.** `modules/debug_utilities.py:611` can inject
   `LearnedMove.create(get_move_by_name("Dive"))` onto an existing party mon. Do that and drive
   Route 128 → Seafloor Cavern. **This work is required no matter how the learner is acquired**, and
   it is near-zero risk — no deposit, no new data row, no party change.
2. `_hm_hunting_grounds(HM08)` — **already measured**: it returns `(ROUTE117, (31,16), ['Marill'])`
   TODAY (`probe_slot_free_plan.py`). Marill learns Surf and Dive. So no new hunting ground is
   *required*; Spheal is only a quality upgrade (50%/L26-32 vs 10%/L13).
3. **‼ IF a new ground is ever added, it must NOT go in `TRAINING_GRASS`.** Measured with the real
   function: a `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM (25,30) (26,32)` row makes it the **highest band
   in the table**, and `best_training_area` then flips for every team from ~L30 up:
   ```
   BEFORE  team L30/34/36/40/44/48 -> (ROUTE121, (44,14), (25,28))
   AFTER   team L30/34/36/40/44/48 -> (SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM, (25,30), (26,32))
   ```
   `TRAINING_GRASS` is primarily the **training-relocation** table, not an HM registry — so the row
   would send every post-Winona boss-prep relocation into a cave across the ocean, with **no
   `_training_area_heal_map` entry** and **no `NO_RETURN_GROUNDS` entry**. `AREA_PREREQ = "surf"`
   does not save it (`_training_area_allowed` passes once any mon knows Surf), and
   `_hm_hunting_grounds` never reads `AREA_PREREQ` at all — the guard would protect every consumer
   except the one it was added for. Use `HUNTING_GROUNDS` (catch-and-leave) or a new `HM_GROUNDS`.
4. **Prefer the ALREADY-PROVEN route over a new deposit.** `#24-pcoverflow` solved this exact
   problem for counters 90 lines away: `POKEBOT_BOX_OVERFLOW_CATCH` defaults ON and is live-proven,
   `counter_hunt.hunt` already returns `{"slot": None, "pid": ...}` for a boxed catch, and
   `withdraw_from_box` collects it at the next heal — **net-zero on party size**. The HM branch
   (`story_mode.py:2158`) still carries the `len(party) < 6` gate the counter branch dropped.

### If a `free_one_party_slot()` is ever built anyway — four things it MUST do
Recorded because I wrote a draft and reverted it; these are the defects the review found in it:
* **Raise on a non-Poké-Centre map.** `pc_trip`'s contract is *"PIGGYBACK, DO NOT DETOUR"*; the
  extracted block does `navigate_to(here, PC_STAND_TILE)` on **whatever map it is on**.
* **Honour `_hunted_counter_pids`.** That protection lives in `plan_deposits`, NOT in the block
  being extracted — batch8 threw away 2 of 5 hunted counters exactly this way.
* **Recompute `party_count`.** `early_game.py:4395` reuses the pre-deposit count as `before`, so
  `_story_spin`'s `len(party) > before` stop condition could never fire.
* **Protect the freshly caught learner.** `_only_hm_carrier` keys on **known moves**, so a Spheal is
  unprotected in the window between the catch and the teach — and it is the lowest-level mon, i.e.
  first in `find_dead_weight`. That is a catch → deposit → catch oscillation.

‼ **What the victim chooser gets RIGHT, so nobody re-derives it:** Zigzagoon L15 IS correctly spared
(sole Surf carrier), Sceptile too (sole Rock Smash + Strength carrier), and the pick is Skitty L17.
Measured, `probe_slot_free_plan.py`.


---

# ARCHIVED 2026-08-14 from `05-KNOWN-ISSUES.md` — KI-39's ORIGINAL (REFUTED) entry, kept verbatim beside its correction

> ‼ The refutation of this entry's stated cause is earlier in THIS archive (the 2026-07-31
> correction block, which says "The KI-39 entry above states the cause wrongly" — 'above'
> refers to THIS text, which lived in `05-KNOWN-ISSUES.md` until 2026-08-14).

## KI-39 — The bot has NO cross-map overworld route planning; long journeys are hand-coded (2026-07-30)

**This is the root cause behind every "unreachable counter destination", and it is much
bigger than `#24-counters`.** It is also the direct answer to the user's question *"is there
a way to get the bot to map to already traveled locations?"* — today, no.

### Measured, from `rocksmash_taught.ss1` (standing in MAUVILLE_CITY (32,15))
| destination | `calculate_path` |
|---|---|
| ROUTE117 (31,16) — directly connected | **OK, 72 waypoints** |
| ROUTE110 (12,60) — joined through a gate BUILDING (a warp) | FAIL |
| ROUTE116 (11,7) — several maps west | FAIL |
| ROUTE111 (25,55) — same map, other side of the Go-Goggles desert | FAIL |

### Why `navigate_to_anywhere` does not rescue it
It branches on REGION, and a region is the connected component over direct N/S/E/W map
connections. Measured: `region_of(MAUVILLE_CITY) == region_of(ROUTE111) ==
region_of(ROUTE116) == region_of(LAVARIDGE_TOWN) == region_of(FALLARBOR_TOWN) == **0**`.
**The whole Hoenn overworld is ONE region.** So for any overworld→overworld trip the
same-region branch is taken, the warp planner is never consulted, and the entire journey is
handed to `calculate_path` — which only spans directly-connected maps. The warp route often
EXISTS and is simply never asked for: `graph.plan(MAUVILLE → FIERY_PATH)` returns a valid
one-warp edge (ROUTE112 (11,36) → FIERY_PATH), yet the navigation fails at 255 frames because
leg 1 — *walk to that warp tile* — is itself a multi-map journey `calculate_path` cannot plan.

### Why nobody noticed
The story chapters hand-code their long journeys leg by leg (`_hold_walk_route` exists
precisely to "bridge the planner can't cross"). Every long trip the bot makes today was
written out by hand, so the generic capability was never exercised — and its absence looks
exactly like "that destination is unreachable".

### Consequences to hold in mind
* A counter hunt only reaches destinations a leg or two away. FIERY_PATH (18,19) arrives in
  2,922 frames from **Lavaridge**, but Norman is fought at **Petalburg** — so even the one
  rung measured "live" is probably inert at the moment it actually fires. Expect the counter
  chain to stop honestly far more often than it hunts.
* `#24-dexhunt`, `#24-pc` (box trips), `#24-catchcap` and the whole team/PC-reserve plan all
  assume the bot can travel to a known place on request. **They are gated on this.**

### What the fix looks like (NOT built)
A cross-map journey planner: BFS the map-connection graph **plus** warp edges to produce an
ordered leg list, then execute leg by leg with `navigate_to`, re-planning from the real
position after each leg (the shape `navigate_to_anywhere` already uses for cross-region
routes — it just never gets to use it). Needs: the desert/elevation splits expressed as
sub-map partitions (Route 111 north vs south are the same map but not mutually walkable),
capability gates (Surf/Fly/Go-Goggles), and a frame budget per leg.

‼ **Do not "fix" this by adding gateway waypoints.** Tried and refuted 2026-07-30: a gateway
in the same region is routed by the same broken same-region branch, so it fails identically.
Fallarbor PC, Lavaridge PC and Fiery Path were all tried as gateways from Mauville; every
leg failed at 255 frames (`probe_counter_gateway.py`).

## KI-40 — Runs stopped FINISHING and the global watchdog fires ~77x more often (2026-07-30, UNATTRIBUTED)

**Measured**, bundle `20260730-204036` (build `ffb062ce`, 4 lanes, ~3h11m) vs bundle
`20260730-062818` (build `21b587f1`, ~13h):

| metric | `21b587f1` | `ffb062ce` |
|---|---|---|
| runs reaching `finished` | 29 of 60 run-ends (48%) | **0 of 30** |
| `global watchdog — nothing progressed` | 5 (~0.4/h) | **94 (~29.5/h)** |
| dominant run-end reason | `boss: N losses…` (22) | **global watchdog (23 of 30)** |

**Not environmental:** RUN HEADERs are identical — Python 3.13.7, same ROM, `speed=0
video=True audio=False`, fodder rule `xp_rate`. **Not an instrument change:** the watchdog
message and its 18,000-frame bound are unchanged since `88a0e307`, present in both builds.

**Observed wedge sites:** `training N battler(s) to Lv 31 in ROUTE117` (stage 9, map (10,0)),
and the `Rock Smash teach skipped → Fallarbor travel not applicable → Meteor Falls scene
already done` sequence (stage 11, map (24,12)). In both, recovery re-enters the same step and
the watchdog fires again — derail #2, #3, #5 on the identical step.

**‼ ATTRIBUTION IS OPEN.** The bundles are 16 commits apart. Ten are prior-session work
(KI-34, KI-35, KI-36, KI-37 fixes); four are mine and touch production code (`5229e780`,
`f74fab6c`, `31647da3`, `06807942`). The `21b587f1` bundle is the already-reviewed
`20260730-062818` batch, i.e. it predates ALL of them. **Do not blame or clear either group
from this data.**

**Refuted already:** that `_counter_ladder`'s `_note_training_unreachable` calls poison the
training-area picker. Only 2 blacklist events came from the ladder; `ROUTE111 (25,55)`
dominates in both builds (14 new / 24 old) and is the training picker's own doing.

**THE EXPERIMENT THAT SETTLES IT (do this before any more long batches):** ~1 hour on
`d7d493d8` and ~1 hour on `ffb062ce`, same lanes and settings, comparing **watchdog fires per
hour** and **finish rate**. `d7d493d8` is the last build the handoff records as
live-validated — but note that validation was *"no unrecovered errors"* and never checked
finish rate, so it may not be a clean baseline either. If `d7d493d8` is clean, bisect my four
commits; if it is not, the cause is in the KI-34/35/36/37 work.

### KI-40 — ATTRIBUTED 2026-07-30 by controlled A/B. The 2026-07-30 counter-chain work is CLEARED.

Baseline arm run on the user's machine: bundle `20260730-214525`, build **`d7d493d8`**
(detached HEAD via tag `baseline/ki40`), launch `212123`, ~24 min, 4 lanes.

| build | window | watchdog fires | **per hour** | runs `finished` |
|---|---|---|---|---|
| `21b587f1` (pre-KI-34/35/36/37) | ~13 h | 5 | **0.4** | 29 of 60 |
| **`d7d493d8` (baseline arm)** | ~0.4 h | 8 | **~20** | **0 of 2** |
| `ffb062ce` (counter-chain work) | ~3.2 h | 94 | **~29.5** | 0 of 30 |

**`d7d493d8` already wedges at ~50× the old rate**, in the same order of magnitude as
`ffb062ce`. The discrimination required was "≈0 or ≈30 per hour"; it came back ≈20.
⇒ **The regression entered between `21b587f1` and `d7d493d8`** — i.e. in the
**KI-34 / KI-35 / KI-36 / KI-37** work (`00db4a81`, `4f1e02f9`, `d7d493d8`), NOT in the
2026-07-30 counter-chain or menu commits.

‼ **This also corrects the handoff.** `d7d493d8` was recorded as live-validated — but that
validation was *"no unrecovered errors"*, and it never checked **finish rate**. On the
finish-rate metric `d7d493d8` is badly broken, and that went unnoticed for a full day of work
built on top of it. **A "clean" verdict is only as good as the metric it was measured on.**

**The wedge is the TARGETED-TRAINING path, in both builds:**
* `d7d493d8`: `Taillow is the answer to this gym but needs Lv 18 — targeted top-up of just
  that mon` → wedge. Stage 7 (Brawly), map (3,3) = DEWFORD_TOWN_GYM.
* `ffb062ce`: `prepping — training 3 battler(s) to Lv 31 in ROUTE117` → wedge. Stage 9,
  map (10,0); also the Rock Smash→Fallarbor→Meteor Falls sequence at map (24,12).
In both, recovery re-enters the identical step and the watchdog fires again (derail #2, #3,
#5 on the same step), so the step itself never becomes completable.

**Leading hypothesis — the mode is being STARVED, not stuck.** The watchdog reports "nothing
progressed for 18,000 frames", which is what a listener sitting above the mode produces.
`04-HANDOFF` Rule 2 already warns: *"Every listener that can sit above the mode must honour
`battle_fault_pending()` and be bounded… `BattleListener` and `TrainerApproachListener` now
do; **others are UNAUDITED**."* The window's diff is +143 lines in `battle_handler.py` and
+21 in `_listeners.py`. **Audit every remaining listener next**; a training spin walks in
grass and is exactly where listener traffic is heaviest.

**Next step is DIAGNOSIS, not more batches** — the remaining suspect set is 3 commits and the
symptom is reproducible in-run. A further 1-hour arm on `00db4a81` or `4f1e02f9` would bisect
it if reading the diffs does not.

### KI-40 → ROOT-CAUSED 2026-07-30: it is **KI-38**, and KI-38 is not "residual" — it is the dominant run-killer

`05-KNOWN-ISSUES`/`04-HANDOFF` describe KI-38 as *"3 residual after-faint give-ups"*. That
figure came from one sample. Measured across both A/B arms it is the thing ending the runs.

**The STUCK dump (baseline `d7d493d8`, P2, f623813) is unambiguous:**
```
message='Story: entering Dewford Gym to challenge Brawly...'
game_state=3  controllable=False
battle: active=True  instr=BattleScript_FaintedMonTryChoose
tasks=['Task_HandleChooseMonInput']            <- the after-faint party menu is OPEN
party=['Taillow L19 0/48', 'Marshtomp L17 55/55', 'Nincada L10 0/28', 'Whismur L17 51/51']
controllers=['StoryEndlessResetMode.run']      <- ‼ NO battle handler on the stack
===== DUMP [STUCK — 111000 frames no progress] =====
```
Two healthy mons (Marshtomp 55/55, Whismur 51/51) were available to send in. Nothing was
driving the battle: the faint chooser had already given up and left the menu open.

**Rates (`GAVE UP` / hour), stable across builds:** baseline `d7d493d8` 9 in ~0.4 h ≈ **22/h**;
`ffb062ce` 75 in ~3.2 h ≈ **23/h**. Faults handed to the mode: 5 and 48 respectively.
‼ **`NO ELIGIBLE REPLACEMENT` = 0 in BOTH.** The chooser always had a valid, living target and
still failed to select it. This is not a "no legal move" case; it is a selection bug.

**Why KI-34's fix made the SYMPTOM worse while being correct in itself.** `4f1e02f9` added
`FAINT_CHOOSER_GIVEUP_LIMIT = 3` to bound an unbounded re-entry (previously ~35 re-entries /
210,000 frames per battle). The bound works — but on giving up it leaves **the battle still
active with the menu open**, hands a fault to the mode, and the mode's recovery (B-ride,
re-orient, resume) cannot answer an in-battle party menu. So recovery re-enters the same step
and wedges again — derail #2, #3, #5 on the identical step. Before the limit, the handler span
forever inside one battle (wasteful, but it stayed on the stack and could still succeed, which
is why `21b587f1` still finished 48% of its runs). **The limit converted a slow leak into a
hard stop.** Both the index-space fix and the bound are right; what is missing is a
give-up path that RESOLVES the battle instead of abandoning it.

**Therefore the fix must be one of:**
1. ‼ **Make the chooser actually select** — `#24-menutext`, already named in the handoff as
   the resolver: read the party-menu text so the bot knows what the cursor is on, instead of
   inferring from indices. **The string MUST come from the decomp.** KI-38's own evidence
   (`presses={'Down': 3, 'A': 273}`, `cursors_seen=[0,2,3,7]` in a 4-mon party, where 7 is
   probably CANCEL) says the cursor model is wrong, which no amount of retrying fixes.
2. **Make the give-up SAFE** — on give-up, drive the battle to a resolved state rather than
   returning with the menu open. A fault the mode cannot act on is worse than no fault.
3. **Interim mitigation only:** raise `FAINT_CHOOSER_GIVEUP_LIMIT`. This trades a hard wedge
   for the old slow leak; it keeps KI-34's index-space fix (which is correct and unrelated).
   Cheap to try, one constant, and it should restore something like the 48% finish rate —
   but it is a mitigation, not a fix, and it must not be mistaken for one.

---

# KI-67 — FULL ENTRY, MOVED here from `05-KNOWN-ISSUES.md` (2026-08-15, on the R3 line budget when KI-79 and KI-80 were filed)

> ‼ **Why it moved:** KI-67 is CLOSED and DRIVEN, and its 77 lines were sitting in a
> CURRENT-STATE file. Verbatim below; a 4-line pointer replaced it there. Nothing deleted.

## KI-67 — the earlier 'production half fixed' write-up is SUPERSEDED (ARCHIVED)

Superseded in full by the '✅✅ KI-67 FULLY CLOSED' section below, which carries the driven
evidence. The archived text is kept only for its harness DESIGN NOTES (the four parts a driver
must mirror, and why half a mirror is worse than none) — see `31-KNOWN-ISSUES-ARCHIVE.md`.

## ✅✅ KI-67 FULLY CLOSED 2026-08-12 — the FIRST DRIVEN WHITEOUT RECOVERY IN THIS PROJECT

`StoryWhiteoutRecoveryMixin` (`tools/story-dev/story_harness.py`) gives a driver all four parts of
production's behaviour, and `SpaceCenter2Mode` uses it. **Driven both ways:**

| run | result |
|---|---|
| healthy, `--driver spacecenter2` | `PASS`, `whiteouts=0 recoveries=0`, frame-identical to before |
| **deliberate loss, `--inject-weak`** | `whiteouts=3 recoveries=3`, ends controllable at `MOSSDEEP_CITY (28,17)` |

‼ **THE FRAME DELTAS ARE THE PROOF, not the counts** — the count alone cannot tell the fixed code
from the broken code:
```
WHITEOUT #1  frame 3532810
WHITEOUT #2  frame 3540599   (+7,789)
WHITEOUT #3  frame 3547686   (+7,087)
```
**Broken = three attempts in a handful of frames after ONE whiteout. Fixed = each attempt costs
~7,000 frames and produces ITS OWN whiteout** — i.e. the bot really did walk back from the Pokémon
Center to Steven and fight again, three times. And the error it finally reported was a
**`StoryAbort`**, not the fabricated *"cannot reach Steven at (1,8)"* the laundering used to produce.
The ACCEPTANCE **FAIL** is correct: a lone Lv3 Poochyena genuinely cannot win that battle.

**Five defects in the mixin were found by an adversarial review BEFORE it was driven**, all fixed:
* `except BotModeError` was too narrow — **`PathFindingError` is a `RuntimeError`**, so a laundered
  abort would have escaped the recovery loop and been graded a genuine failure;
* **MRO silent-revert**: ten other drivers still define their own `on_whiteout`, and mixing this in
  without deleting theirs would leave the driver *looking* converted while never setting the latch.
  `__init_subclass__` now REFUSES that at class-creation time (proved dynamically in the repro);
* `self.tag` was dereferenced on the *listener's* stack, where an `AttributeError` kills the run
  before any RESULT line — now `getattr`;
* the recovery budget compared a never-reset CLASS counter to a per-call limit — now a delta;
* falling out of the loop returned `None` = **success** — the silent-green pattern; now returns the
  last error.

‼ **AND A REAL BLOCKER THE REVIEW CAUGHT: an injected run could have overwritten a committed
anchor.** `--inject-weak` replaces the party with a lone Lv3 Poochyena; had such a run reached the
completion var it would have written `post_space_center.ss1` — a fixture `--driver spacecenter` and
`FIXTURES.md5` depend on — with a joke party, **silently**. Anchor capture now refuses whenever the
run injected a party. (Verified after the fact: the injected runs captured nothing; the anchor on
disk came from the healthy run.)

**Also fixed in PRODUCTION, not just the harness:** `StoryMode.run`'s `recoveries > 40` exit raised
**without clearing the process-global latch**, so whatever ran next would abort at its first
`_check_abort()` for no visible reason. The harness must not be stricter than the thing it mirrors.

**Superseded — the old "still open" text follows for its design notes:**

⛔ **STILL OPEN — THE DRIVEN HALF, AND DO NOT HALF-DO IT.** `set_story_abort` still appears **zero**
times in `story_harness.py`. ‼ **Both reviews independently warned that adding the latch to drivers
WITHOUT also mirroring `run()`'s clear-and-retry loop makes it a ONE-WAY DOOR** — the latch is
process-global and nothing else clears it, so every later `_check_abort()` would raise forever and
currently-passing drivers would go red over correct production code (`--driver spacecenter`,
`--driver mossdeeptravel`; anchors would stop refreshing). **So it is all four or nothing:**
`on_whiteout` sets the latch AND `_whiteout_pending`; the driver wraps the chapter in a
clear-and-retry loop; the whiteout branch clears the latch BEFORE navigating and calls
`exit_building_after_whiteout()`; and the RESULT line reports the recovery count. Cheapest safe
shape is ONE shared mixin the eleven drivers inherit, so it cannot drift again.
**Then prove it with `--driver spacecenter2 --inject-weak`** from the 2F anchor (past the grunts,
at Steven) — a 1-mon party is legal (`GetMinBattleEntries()` is 1) and loses fast, and
`Cmd_checkteamslost` sums HP over the player's picks only. ‼ Assert `_whiteout_pending` in the log:
the whole severity assessment rests on it being True when the error arrives, and that was traced
statically, never run.

**Also still open (pre-existing, adjacent):** the latch is process-global and `run()` does not clear
it in a `finally`, so an exit via `derails > 4` or `recoveries > 40` leaves it set for whatever runs
next. Harmless today only because nothing else sets it — it goes live the moment the harness mirror
lands. And ~48 further swallow sites remain in `early_game.py`; most self-heal because the next
abort-aware call re-raises, but they should get the same one-line guard, enforced by an AST check
rather than by prose.

