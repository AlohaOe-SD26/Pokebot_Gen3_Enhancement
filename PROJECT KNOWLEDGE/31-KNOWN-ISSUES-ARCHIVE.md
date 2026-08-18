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


---

# KI-54 — FULL ENTRY, MOVED here from `05-KNOWN-ISSUES.md` (2026-08-15, on the R3 line budget when KI-80's repro spec was measured)

> ‼ **Why it moved:** 218 lines of a CURRENT-STATE file for an entry whose own severity is
> *informational* and whose subject ("roster hygiene before bosses") was RETRACTED. Verbatim
> below; a short pointer replaced it there. Nothing deleted.

## KI-54 — "Roster hygiene before bosses" is BLOCKED: the box is EMPTY, and the deposit path it would need was already measured harmful (2026-08-11, severity: informational — a plan-blocker, not a defect)

**Context.** The user approved "roster hygiene before bosses" on 2026-08-11 after the Magma Hideout
loss showed **two dead party slots** (Zigzagoon L6, Skitty L17) in a **L38-39** boss fight, one of
which (Skitty) cost the kill on Camerupt at 22/110 immediately before Maxie healed it to 67.
**Verification before building found two blockers.**

### ‼ BLOCKER 1 — there is nothing to swap TO. The box is EMPTY.
```
post_maxie.ss1         party 6, BOX 0
magma_door_losing.ss1  party 6, BOX 0
POSITIVE CONTROL boxwithdraw.ss1 -> 2 in box: ['Poochyena:L26', 'Shuppet:L26']
```
The control matters: an empty box and a broken box reader look identical. The reader works.

### ‼ BLOCKER 2 — the deposit path EXISTS and is pinned OFF with measured harm
`modules/story/pc_trip.py: deposit_dead_weight_if_worth_it()`, gated by `POKEBOT_PC_ROTATION`
(default **0**) since 2026-08-05:
| batch | PC deposits | avg team size at Feather | Balance→Feather |
|---|---|---|---|
| b3 / b4 / b5 (OFF) | 0 | 5.65 / 5.72 / 5.81 | 83 / 75 / 70% |
| b8 (ON) | 14 | **4.45** | **52%** |
| b13 (ON) | 18 | **4.75** | **57%** |
It removed ~**one whole team member permanently** and the last funnel rung collapsed over exactly
that transition.

⇒ **The SWAP version is impossible (empty box); the DEPOSIT-ONLY version is that disproven feature
in narrower clothing.** Do not rebuild it from the boss-fight evidence alone.

### ⛔⛔ THE "MISSING PIECE" BELOW IS WRONG — RETRACTED 2026-08-12. READ THIS FIRST.

**`POKEBOT_BOX_OVERFLOW_CATCH` IS NOT DISABLED. It has defaulted to ON since 2026-08-07** —
`plugins/custom_modes/story_mode.py:2241-2243` reads
`_os.environ.get("POKEBOT_BOX_OVERFLOW_CATCH", "1")`. **Verified in the live code**, not recalled.

And the "one unhandled text box" blocker was **refuted on 2026-08-07, four days before the section
below was written**. The capability test is recorded in the comment right above the flag read:
`--driver boxcatch` on a full party with an empty box gave `caught=True box_before=0 box_after=1
exited_clean=True exit_frames=120`, then `AFTER-CATCH usable=True second_catch=True frames=20
box_now=2` — **zero forced presses**; the existing battle handler rides the box-send message out.
(The message is real decomp — `Cmd_givecaughtmon` → `B_MSG_SENT_SOMEONES_PC` — it simply needs no
handling.) `03-PUNCH-LIST.md` says so plainly: *"I 'confirmed' that wedge twice and both were my
probe idling."*

‼ **HOW THIS HAPPENED, because it is the more valuable lesson.** Four documents were written on
2026-08-11 by reading a **stale comment block** (`story_mode.py:2202-2226`, which still said
"GATED OFF … default 0") instead of the **live default twenty lines below it**. That is precisely
the failure the flag registry was created to prevent, committed one level up — in the registry
itself. ⇒ **A registry row is a claim with an expiry date too. Read the code the row describes,
not the prose next to it.**

**Consequence:** BLOCKER 1 below is void as a blocker. The box being empty was never a gate; the
counter hunt simply never had a full party when it fired.

<details><summary>Superseded text, kept because the batch evidence in it is still real</summary>

`POKEBOT_BOX_OVERFLOW_CATCH` (default **0**, `#24-pcoverflow`) is the feature that lets a catch
overflow **into the PC box** when the party is full. **It is off, so nothing ever puts anything in
the box.** That is the direct cause of BLOCKER 1.

It was gated after batch `20260806-142418` graded it against its own **pre-registered** target and
it FAILED: `withdrawing` **0** (target ≥1) and `INTO THE PC BOX` **0** — the path **never fired in
26 runs**. ‼ The code is careful to add that it is off because it **delivered nothing**, not
because it was proven harmful (only 10 of 43 watchdog dumps had a full party; the wedges were
battle-handler shaped).

‼‼ **AND THE BLOCKER IS NAMED AND SMALL:** a box-send shows an **EXTRA TEXT BOX** that the
party-catch path never shows, and the bot has no handling for it (user-identified 2026-08-06, then
decomp-confirmed).

⇒ **This re-orders the roster options.** Option (a) "populate the box first" is not a large new
project — it is **one unhandled text box** away from firing. That is a far better first move than
(b) re-enabling the measured-harmful deposit path.

‼ **How this was found is the point:** the measurement lived in a code comment in
`story_mode.py`, where nobody looks before proposing a feature. `lint_docs.py`'s new R6 rule forced
every `POKEBOT_*` flag into `29-DISABLED-FEATURES-REGISTRY.md`, and this flag surfaced immediately —
an 11th flag that my own hand-written grep had missed.

</details>

### ✅ THE ACTUAL PLAN, 2026-08-12 — deposit-first, and it is SMALLER than the box round-trip

With BLOCKER 1 void, the remaining question is only how to free one party slot for a Dive learner.
**Measured against `modules/data`, not recalled:**
* **76 species learn Dive; NONE of ours does**, and there is no evolution escape — **Linoone NO,
  Delcatty NO**, Castform has no evolution, and Beldum is post-Champion. **A catch is mandatory.**
* **Spheal is the answer: ~50% of the `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM` LAND table at L26-32,
  catch rate 255 (the maximum), and it learns BOTH Surf and Dive.** `MOSSDEEP_CITY` connects
  directly to `ROUTE125`, and Route 125 → the entrance room is **one warp** — no cave threading.
  ⚠ **TIDE IS THE RISK:** only the five LOW-tide maps have an encounter header in our ROM; the high
  tide maps have **none at all**. Which RTC hours give low tide is **UNVERIFIED**.
* **Fallback with no tide dependency: Marill on Route 120**, 15% at L25-27, learns both.
* ⛔ **Do NOT fetch the Super Rod first.** Sharpedo/Wailmer are real (40%/60% Super Rod off
  Mossdeep, both learn Surf+Dive) but need **three missing subsystems**: no rod-fetch chapter
  exists, the story bot has **no fishing capability at all**, and `_hm_hunting_grounds` reads
  `land_encounters` ONLY. One `TRAINING_GRASS` row versus three subsystems.

‼ **AND THE BOX ROUND-TRIP IS THE LONGER PATH, NOT THE SHORTER ONE** — the opposite of what I
assumed. `ensure_hm_learner`'s success test reads the **party** (`hm_learner_slot(item) is not
None`), so a catch that lands in the box never satisfies it: the spin burns its whole 40,000-frame
budget and raises "never caught one". Routing through the box would need the stop condition changed,
the new PID captured and registered, **and** a Poké Center trip anyway.

**Deposit-first is strictly smaller and reuses only PROVEN code:**
1. one `TRAINING_GRASS` row for the Shoal Cave entrance room (spin tile derived and two-way swept
   from a real anchor — never from recall);
2. replace the `raise` in `ensure_hm_learner` with a `free_one_party_slot()` factored out of
   **`withdraw_from_box:331-355`**, which already deposits **exactly one** mon, worst-first, and is
   live-proven by `--driver boxwithdraw` (three identical consecutive runs, `deposited=True
   withdrew=True party_after=6`, and the second heal produced exactly one withdraw line).
   ‼ **This is NOT the measured-harmful rotation.** That harm was `POKEBOT_PC_ROTATION`, which fires
   on **every heal** and deposits up to 2 mons down to a floor of 3. Freeing one slot once is a
   different act, and KI-54 says so itself.
3. **Verified offline against our exact party:** the real predicate picks **Skitty L17** — and
   correctly **spares Zigzagoon L15 despite it being the lowest level**, because `_only_hm_carrier`
   protects our sole Surf carrier. That is exactly the mon KI-54 named as "the real passenger".
⚠ Second-order: Spheal arrives at L26-32 against an L48 lead, so it is itself "dead weight" by the
L48−8 rule. Harmless while `POKEBOT_PC_ROTATION=0`; it becomes a **self-eviction loop** if anyone
turns that on.

### ⛔ RETRACTED 2026-08-13 — "THE TIDE IS NOT A BLOCKER" RESTS ON A MEASUREMENT THAT CANNOT SEE HIGH TIDE

> **Do not act on the section below.** Its conclusion may still be right, but **its evidence does
> not support it**, because of **KI-73**: `get_map_data` builds `_map_header_cache` **once from the
> static compile-time `gMapGroups` ROM table** (`map.py:1766-1785`), which can only ever yield the
> **compiled low-tide** layout for map (24,46). `setmaplayoutindex` patches the live `gMapHeader`
> RAM struct, which that table never reads, and nothing anywhere in `modules/` clears either cache.
>
> ⚠ **AND MY FIRST RETRACTION OVERSHOT — corrected the same day.** I wrote that the *"65 walkable
> tiles at high tide"* figure was "almost certainly two views of the same low-tide layout".
> **That is REFUTED.** `probe_shoal_tide.py` reproduced the 65 **exactly**, as a genuine high-tide
> component: 65 tiles, all `Cave`, all with encounters, spanning x 3–12, y 15–28.
> **The count was right. What was never checked was its REACHABILITY — it is an ISLAND**, not
> on-foot connected to the entrance warp. The 181-tile region the bot can actually reach at high
> tide contains **zero** encounter tiles.
>
> ⇒ **THE DECISIVE MEASUREMENT, reproduced by me:** spin tiles that are on-foot, encountering AND
> reachable from the arrival warp — **LOW: 278. HIGH: 0.** All three candidates below become
> `Shallow Water` with `has_encounters=False` at high tide. ‼ **The failure mode is a SILENT STALL,
> not a crash**: the tile is still standable, so `ensure_hm_learner` spins out its entire
> 40,000-frame budget meeting nothing.
>
> ✅ **What KI-54 got RIGHT and is now decomp-confirmed:** the hour table (LOW = **03–08 and
> 15–20**), `FLAG_SYS_SHOAL_TIDE` **set = HIGH**, the high-tide maps having no encounter header and
> no warps, and the tide being sampled **once** on `ON_TRANSITION` and frozen for the visit
> (verified against `pret/pokeemerald` — the only caller of `UpdateShoalTideFlag` is
> `ShoalCave_LowTideEntranceRoom/scripts.inc`).
> ✅ **And the bot CAN both read and predict the tide:** `get_event_flag("SYS_SHOAL_TIDE")` reports
> the frozen one, and `modules/clock.py` `get_clock_time().hours` predicts what the NEXT entry from
> outdoors will roll.
>
> ‼ **The decomp claim that the tide is "sampled ONLY on ON_TRANSITION and frozen for the visit" is
> ALSO unaudited** — `src/time_events.c` is not vendored anywhere in this repo, so per this
> project's own rule that decomp claims must be checked against `pret/pokeemerald`, it has never
> been verified here. If the tide can flip mid-visit, the stale-cache problem compounds with a live
> floor-swap under the bot's feet.
>
> **RULING 2026-08-13: Shoal Cave is NOT adopted as a hunting ground.** Rationale and the exact
> conditions that would unlock it: `06-DECISIONS-LOG.md`, 2026-08-13.

### (original, 2026-08-12) ‼ THE TIDE IS NOT A BLOCKER — measured, and it removes the plan's only unknown

The tide worry was **real but misdirected**. Findings, decomp- and ROM-measured:
* `UpdateShoalTideFlag()` (`src/time_events.c:54-92`) is a **24-entry hour table**;
  `FLAG_SYS_SHOAL_TIDE` **set = HIGH**. LOW tide is hours **03-08 and 15-20**. It is sampled ONLY on
  `ON_TRANSITION` into the entrance room from an OUTDOOR map, and is then frozen for the visit.
* ‼‼ **BUT THE TIDE GATES THE DESCENT, NOT THE HUNT.** The high-tide "maps" (24,50)/(24,51) have
  **no encounter header and zero warp edges** — they exist only to own a layout that
  `setmaplayoutindex` borrows onto map (24,46). The player stays on **(24,46)** at both tides, and
  `GetCurrentMapWildMonHeaderId` keys off map group/number, **not layout**. Measured from our ROM:
  the entrance room still has **65 walkable `MB_CAVE` encounter tiles at high tide** (332 at low).
  ⇒ **The Spheal 50% table is live at BOTH tides. No tide handling is needed at all.**
* **Surf is the only gate**, and we have it: our planner routes `MOSSDEEP_CITY (49,35) → ROUTE125
  (22,19)` in **119 waypoints**, and Zigzagoon L15 knows Surf (measured on the live save). Route 125
  → the entrance room is a single warp, (22,19) ↔ (20,30).
* Spin-tile candidates, all `MB_CAVE` with two-way static `calculate_path` PASS: **(25,30)** (5 steps
  from the arrival warp), (14,30), (20,24). ⚠ **Static evidence only — NOT the live two-way sweep
  this project requires** (the Route 114 demotion). Never promote a spin tile on this alone.
* ⚠ **A REAL HAZARD FOR ANY IN-ROOM NAVIGATION:** `MapLocation` resolves the layout from the cached
  ROM map header, i.e. **always the LOW-tide floor plan** for (24,46). At high tide the planner is
  therefore planning against the wrong map. Fix or fence this before any code paths inside that room.
* ⚠ Never spin on or south-adjacent to **(20,30)** — it is `MB_SHOAL_CAVE_ENTRANCE`, which counts as
  a south-arrow warp.

**‼ AND THE REAL BLOCKER IS STILL THE FULL PARTY:** `ensure_hm_learner` raises at
`early_game.py:4342-4348` when the party is ≥6 **before it ever calls `_hm_hunting_grounds`**. So the
hunting ground is necessary but not sufficient — freeing the slot is the gate, exactly as the
deposit-first plan above says.

**Cheapest tide-free fallback, needing ZERO new data:** `_hm_hunting_grounds(HM08)` **already**
returns one ground today — **ROUTE117 (31,16), Marill, 10%**, already two-way swept. Route 120 is not
in `TRAINING_GRASS` and would itself need a swept row, so Route 117 is strictly cheaper if the Shoal
Cave sweep fails.

### ‼ THE LIKELY CAUSAL LOOP, stated as a hypothesis
With deposits OFF, **anything caught stays in the party for ever** — so the party fills with
passengers. The dead weight may be a *symptom* of deposits being off, and deposits are off because
they thinned the team. That is a genuine tension, not an oversight.
‼ One nuance worth keeping: the old rotation policy was bad at **choosing** — it deposited a
*hunted counter* and a Machop 25 levels behind the team's best. "That policy was harmful" is not
the same claim as "depositing is harmful", but neither has been measured separately.

### What is NOT blocked
* Zigzagoon is the **HM slave** (Surf / Rock Smash / Strength) — it has a job and should not be
  treated as dead weight. **Skitty L17 has no stated job**; it is the real passenger.
* Passengers only reach the field after the competent mons faint — but that is exactly when the
  fight is decided, and in the measured fight it cost the kill. The marginal value is real but it
  is second-order to whatever fainted the first four.

### DECISION REQUIRED (not taken)
Options: (a) populate the box first — `#24-roster`'s actual scope, catch-overflow, with its own
prerequisites; (b) re-enable deposits under a much tighter policy (never a hunted counter, never
an HM carrier, never below party 5, only >N levels behind) — ‼ re-opens a measured-harmful path and
must not ship without a batch; (c) a catch/keep policy so passengers never enter the party;
(d) park roster work and do the STATUS response instead, which needs no box and has a
deterministic fixture (`magma_door_losing.ss1`).



## 2026-08-16 — archived from `05-KNOWN-ISSUES.md`: the FULL KI-79 entry, verbatim

KI-79 is FIXED, fault-proven and promoted to both forks. Moved on the 3000-line budget to make
room for KI-65's recon. ⛔ Its ONE LIVE RESIDUAL — no caller acts on the verdict — stays in
`05-KNOWN-ISSUES.md` and is tracked as `#24-orphans` item (1).

## KI-79 — `withdraw_from_box` PRINTED A SUCCESS IT NEVER VERIFIED: `len(get_party())` wearing an identity's clothes (2026-08-15, code-verified while driving (P4) Stage 2 — ✅✅ **FIXED, FAULT-PROVEN, AND PROMOTED TO BOTH FORKS 2026-08-15, user-approved — ⚠ CLOSED *FOR THE MESSAGE*, WITH ONE RESIDUAL: NO CALLER ACTS ON THE VERDICT.** `withdraw_from_box` still returns nothing and still never raises, so production can now TELL the truth about a failed withdraw and still cannot REACT to one — tracked as an open thread in `03-PUNCH-LIST.md`, because a residual filed under a header reading only "CLOSED" is a residual nobody finds)

- **The line.** `modules/story/pc_trip.py:472-474`, the tail of `withdraw_from_box()`:
  ```
  after = len(get_party())
  console.print(f"[green]Story: PC — {name} is in the party; party is now {after}.[/]")
  context.message = f"Story: withdrew {name} — party {after}."
  ```
  It reads a **COUNT** and announces an **IDENTITY**. Nothing between the `interact_with_pc(actions)`
  call and this print asks whether `name` actually arrived.
- **Why it can lie, concretely.** The whole body is wrapped in a blanket
  `except Exception: ... "could not withdraw {name} ... it stays in the box"` (`:475-478`), so the
  function **never raises**. But a PC interaction that silently completes the WRONG action — or
  completes the make-room deposit and then fails the withdraw — leaves the count **exactly the
  same** (the deposit cancels the withdraw), takes no exception path, and prints the green
  success line. ‼ **MEASURED, not theorised:** on a genuinely SUCCESSFUL withdraw this project
  records `party_before=6 party_after=6 box_before=2 box_after=2` — every count unchanged. A
  metric that is invariant across success is invariant across failure too.
- **Why it matters beyond cosmetics.** This is the project's #1 recurring bug shape
  (`CLAUDE.md` SESSION DISCIPLINE rule 3: *assert IDENTITY, never position or count*; the same
  shape produced `catch_confirmed()`'s party-COUNT delta that a Shedinja spawn could fake, fixed
  under (P1)). It is **live in production**, on the PC path, in the middle of the arc whose whole
  purpose is PC/party robustness. And a future driver or log-scraper that greps for
  `"is in the party"` would inherit the lie — `--driver boxcounter2` deliberately does NOT.
- **How it was found.** Not by a test — by reading `withdraw_from_box` end-to-end while building
  (P4) Stage 2's acceptance chain, precisely because the design note required every claim to be an
  identity. The happy path prints the same line whether or not it is true, so **no green run could
  ever have surfaced it.**
- **NOT OBSERVED FAILING.** Every (P4) Stage 2 drive so far shows the line printing truthfully
  (ARM B: `moved=True`, verified independently by PID+species and by `contains_pokemon`). This is
  a structural finding from reading the code, not a reproduction. ‼ Report it as *"cannot be
  trusted"*, never as *"is wrong"*.
- ✅ **FIXED 2026-08-15 (sandbox), exactly as scoped below.** After the PC interaction the
  function now yields two frames (party AND storage are cached per frame, so a same-frame read
  sees the PRE-withdraw state and the verification would become the new false negative), then
  resolves the target BY IDENTITY: a party member matching `(personality_value, species.name)`
  **and** `contains_pokemon(target)` now False. Both halves are required — in-party-only could be
  a copy, gone-from-box-only could be a release. On success it prints the same green line; on
  failure it prints a loud named `‼ THE WITHDRAW DID NOT LAND … in_party=… still_boxed=…` and
  ⛔ **still does not raise**, because the original contract stands: a PC hiccup must not destroy
  a heal that already succeeded. What changed is that the caller is no longer LIED TO.
  ⛔ It is NOT fixed by asserting the count changed: on the make-room path it correctly does not.
- ‼ **PROVEN BY FAULT INJECTION, because a green run cannot exercise an error path.** New
  permanent hook **`POKEBOT_PCWITHDRAW_FAULT=1`** (registered in `29-DISABLED-FEATURES-REGISTRY.md`)
  skips the PC interaction so the withdraw provably does not happen. Measured, both arms, live:
  * **FAULTED** → `Story: PC — ‼ THE WITHDRAW DID NOT LAND. Slugma in_party=False
    still_boxed=True`, and `--driver boxcounter2` reported `moved=False knows_rock_throw=False
    lead_is_counter=False noop_attributed=False` → **`ACCEPTANCE: FAIL`**. ‼ It ran to COMPLETION
    and reported — it did not throw, which is itself worth knowing.
  * **UNFAULTED** → `Story: PC — Slugma is in the party; party is now 6.` (now identity-verified)
    → **`ACCEPTANCE: PASS`**, no regression.
  ⇒ The old code printed the SAME green line in BOTH of those runs. That is the defect, shown.
  ⇒ Bonus: this also FAULT-TESTS the Stage 2 driver — all four of its graded claims flip to False
  when the thing they check is sabotaged, so it is not rubber-stamping.
- 📁 **THE RAW TRANSCRIPTS ARE COMMITTED, BY NAME** — `tools/story-dev/evidence/2026-08-15-ki79-armB-UNFAULTED.stdout.txt` and `…-FAULTED.stdout.txt` (plus their `.driver.txt` twins).
  ‼ **They exist because a Tier 1 reviewer could not verify this entry and said so.** The harness
  USED TO WRITE `harness_<build>.log` — **one fixed filename per build, overwritten by the very next
  run** — so the unfaulted PASS transcript had already been destroyed by the faulted run that
  followed it, and all that remained on disk was a FAIL. ✅ **That collision is FIXED as of
  2026-08-16** (`#24-orphans` (4)): default log names are unique per run. ‼ **Committing the raw
  transcripts is STILL right** — a gitignored log is not evidence, and stdout (production's
  `console.print`) is not in the harness log at all. The claim was true and *unverifiable*,
  which for this project's purposes is the same as unproven. ⇒ **A/B runs must be captured with
  distinct `--log` names, and stdout redirected too** (the driver's own log does NOT contain
  `console.print` output — the `‼ THE WITHDRAW DID NOT LAND` and green-success lines live in
  stdout). The faulted stdout also carries `POKEBOT_PCWITHDRAW_FAULT=1, SKIPPING the PC
  interaction`, which is what proves the fault was actually armed for that run.
- ✅✅ **PROMOTED TO BOTH FORKS 2026-08-15 (user-approved); this file is in both.** *(⚠ The
  repo-wide drift figure is no longer 0 — one UNRELATED comment-only `story_mode.py` fix awaits
  the user's promotion call. It does not touch this item.)* Restore point
  `restore/2026-08-15-pre-promotion-ki79-pctrip`.
  ‼‼ **VERIFIED BY A THREE-POINT A/B, NOT BY A BYTE-COMPARE — and the distinction is the whole
  point for a BEHAVIOUR change.** `promote.py` reporting "1/1 byte-identical" only proves the file
  was COPIED; it cannot prove the new branch is what EXECUTES. The fault hook can:
  | # | run (`--driver boxcounter2 --build custom`) | result | proves |
  |---|---|---|---|
  | 1 | **BEFORE** promotion, `POKEBOT_PCWITHDRAW_FAULT=1` | `Slugma is in the party` → **PASS** | the hook is ABSENT in custom — the variable is INERT |
  | 2 | **AFTER** promotion, same command | `‼ THE WITHDRAW DID NOT LAND` → **FAIL** | ⇒ **the new code is LIVE in custom** |
  | 3 | **AFTER** promotion, unfaulted | green line → **PASS** | no regression on the happy path |
  ‼ Run 1 is capturable ONLY before the copy and is therefore committed. ⛔ **Run 1 does NOT prove the variable was 'inert' — a run of code that never READS a variable cannot show anything about it, and its output is indistinguishable from an unfaulted run.** (A Tier 1 reviewer caught exactly that overclaim.) What run 1 DOES prove is that the identical command PASSED before the promotion. The *absence of the hook* is proven from git instead, which is stronger and re-runnable by anyone: `git show restore/2026-08-15-pre-promotion-ki79-pctrip:custom-pokebot/modules/story/pc_trip.py | grep -c POKEBOT_PCWITHDRAW_FAULT` → **0** (sandbox at the same tag → **3**; custom now → **3**).
  Transcripts:
  `tools/story-dev/evidence/2026-08-15-ki79-promotion-{BEFORE-custom-faultvar-set,AFTER-custom-FAULTED,AFTER-custom-UNFAULTED}.stdout.txt`.
  Also green on custom: `boxcounter2 --build custom` **ARM A** → `ACCEPTANCE: PASS` (transcript: `tools/story-dev/evidence/2026-08-15-ki79-promotion-AFTER-custom-ARMA.stdout.txt`, which logs `ARM=A (POKEBOT_BOXCOUNTER_TYPEONLY_A='1')` so the arm is self-evidencing), and four `--build custom` gates that each ASSERT which fork they imported.
- ⚠ **WHAT IS STILL TRUE AFTER THE FIX:** the message is now trustworthy, but **no CALLER acts on
  it.** `withdraw_from_box` still returns nothing and still never raises, so a caller that needs to
  KNOW whether the counter arrived must check identity itself — which `--driver boxcounter2` does
  and production does not. That is a deliberate scope line, not an oversight.
- **Related:** KI-78 (identity is `(personality, species)`, because a Shedinja shares its
  Ninjask's PID — so even a PID-only check is not enough here), and the (P4) Stage 2 driver, whose
  `party_map()` is keyed on that pair for exactly this reason after a PID-keyed first draft
  reported a full party of 6 as 5.

---



## 2026-08-16 — archived from `05-KNOWN-ISSUES.md`: the KI-61 stub, verbatim (compacted on the 3000-line budget)

## KI-61 — the chapter DETECTOR named the wrong beat after badge 7 (2026-08-12, ✅ FIXED — ARCHIVED)

`chapters.py` listed the Space Center BEFORE the Mossdeep gym, so `_compute_badges_before()`
put chapter 19 in the SIX-badge bracket and `current_chapter()` skipped two whole beats the
moment the seventh badge landed. A/B proven; the design doc's "order confirmed" was wrong.

Full detail moved to **`31-KNOWN-ISSUES-ARCHIVE.md`** on 2026-08-12 for the R3 budget.
‼ Keep only this here: it is guarded by `probe_chapter_order.py`, which now takes `--build` and
passes on BOTH forks — it used to hard-code the sandbox path and so could never test the build
the user runs. **ORDER in a list that more than one consumer reads is a silent logic bug, not
cosmetics.**



## 2026-08-16 — archived from `05-KNOWN-ISSUES.md`: the KI-58 stub, verbatim (compacted on the 3000-line budget)

## KI-58 — the Mossdeep Gym statue puzzle (2026-08-12, ✅ RESOLVED — detail ARCHIVED)

The gym is a **ROTATING-TILE STATUE PUZZLE**, not a maze: nine floor switches call
`moverotatingtileobjects`, moving every object on a matching coloured arrow — **including nine
of the trainers**. Four independent instruments all concluded it had no route to its own leaders
because none of them modelled that third movement primitive.

Full detail (the encoding derived from the ROM dump, the validated simulator, the per-press
object counts, and the list of things that bite) moved to **`31-KNOWN-ISSUES-ARCHIVE.md`** on
2026-08-12 to keep this file inside its R3 budget. ‼ Keep only this here: the method that cracked
it is written up in `14-AGENT-PLAYBOOK.md §4b` — *simulate the mechanic, then make the GAME grade
your simulator* — and it is the reusable part.



## 2026-08-16 — archived from `05-KNOWN-ISSUES.md`: the FULL KI-78 entry, verbatim

KI-78 Stage 1 is FIXED, GATED and PROMOTED to both forks. Moved on the 3000-line budget to make
room for KI-65's corrected discriminator. ⛔ Its RESIDUAL cases stay OPEN and are named in the
summary left behind in `05-KNOWN-ISSUES.md`.

## KI-78 — ⛔ **PERSONALITY VALUE IS NOT A UNIQUE IDENTITY IN GEN 3: a SHEDINJA carries the SAME PID as the NINJASK it came from** — and this codebase keyed "which mon do I act on" off exactly that (2026-08-14, DECOMP-VERIFIED — ✅ **FIXED IN BOTH FORKS (Stage 1, promoted 2026-08-14) — ⚠ RESIDUAL CASES REMAIN OPEN**)

> ✅ **STAGE 1 LANDED 2026-08-14 — the party/box identity lookups now key on `(personality,
> species)`** via the shared `modules/pokemon.same_pokemon` predicate. A/B proven by
> `tools/story-dev/repro_pid_identity_key.py` (gate #20), which builds a **real** twin pair with
> genuine Gen 3 substructure encryption: the OLD PID-only rule, asked for the SHEDINJA, returns
> the **NINJASK's** slot; the shipped rule returns the right one. Fault-tested both ways — revert
> the fix and the gate goes red on exactly that check.
> ✅ **PROMOTED TO `custom-pokebot` 2026-08-14** (user-approved; the FIRST promotion executed
> through `tools/story-dev/promote.py` rather than by hand). Verified IN THAT FORK by
> `repro_pid_identity_key.py --build custom` → exit 0, which **asserts which fork it imported**
> before testing anything, plus a live drive. Superseded: *"custom-pokebot has the detection
> warning but not the fix — the wrong-target release is still live there."*
> ⛔ **The residual cases below are NOT closed by Stage 1** — see "Residual collisions".

- **Why this is severe.** This project's standing rule — written into `CLAUDE.md`'s SESSION
  DISCIPLINE as rule 3 — is *"Assert IDENTITY, never position or count. PIDs — never slot
  indices."* **That remedy has a hole, and this is it.** PID is the identity key we reach for
  precisely when a count would lie, so a PID collision defeats the fix and the prevention rule at
  the same time.
- **The mechanism, verified against the decomp (not recalled).** `CreateShedinja`
  (`src/evolution_scene.c:548-583`) does `CopyMon(&gPlayerParty[gPlayerPartyCount], mon,
  sizeof(struct Pokemon))` — a plain `memcpy` (`src/pokemon.c:4420-4423`) — and then overwrites
  species, nickname, held item, markings, the encrypt separator, ribbons, status and mail.
  **`MON_DATA_PERSONALITY` is NOT among them.** OT ID is likewise inherited. ⇒ Ninjask and
  Shedinja are PID-identical and OT-identical for their whole lives.
- ‼ **AND THE TRIGGER IS MORE COMMON THAN OUR OWN CODE CLAIMS.** In Gen 3 the ONLY precondition
  is `gPlayerPartyCount < PARTY_SIZE` (`evolution_scene.c:551`) — **there is no spare-Poké-Ball
  requirement**; that rule is Gen 4+. Our `modules/obtainability.py:88` display string says
  *"level up (empty slot + spare Ball)"* and **is wrong for this ROM**. Any Nincada reaching L20
  with one free slot spawns a Shedinja.
- ⛔ *(SUPERSEDED 2026-08-15 — Stage 1 was PROMOTED on 2026-08-14, so nothing below is 'sandbox
  only' any more; the fix is in BOTH forks and drift is 0. The residual R2/R3/R5/R6 cases named in
  the header are what remain open.)* **Where it WAS armed — the first two are FIXED by Stage 1, was
  then still armed in
  `custom-pokebot`. The rest are untouched and remain PID-only ON PURPOSE:**
  * ✅ `modules/pokemon_party.py` `Party.get_index_for_pokemon` — **now matches via
    `same_pokemon` (personality AND species)**, with the R6 handling below. It used to match
    `data[:4]` alone and return the first hit, which is **the function that decides WHICH PARTY
    SLOT a PC action operates on** — the whole hazard.
  * ✅ `modules/pokemon_storage.py` `contains_pokemon` — was PID-only; now on `same_pokemon`.
    Its neighbour `get_slot_for_pokemon` was **already** composite and is refactored onto the
    shared predicate so the pair cannot drift apart again. ⚠ `contains_pokemon` has **zero callers
    today**, so its correctness is proven by routing, not by a behavioural A/B.
  * ⚠ `modules/modes/util/pc_interaction.py:464` (`_do_deposit_actions`) and **`:505` (RELEASE)**
    resolve their target through `get_index_for_pokemon`, so they inherit the fix in sandbox and
    **remain exposed in `custom-pokebot`.** ⛔ One branch of that lookup **releases a Pokémon
    permanently.**
  * ⛔ **DELIBERATELY LEFT PID-ONLY — do not "fix" these:** `modules/story/pc_trip.py:384-400`
    `find_in_box(pids)` and the protected-counter PID set at `:136`;
    `modules/story/early_game.py:1655-1656`'s `_hunted_counter_pids` matching. These mean *"do not
    touch anything in this family"*, and a twin SHOULD inherit its sibling's protection — widening
    is the safe direction, narrowing is not.
- ‼ **R6 — THE NEW FAILURE MODE STAGE 1 INTRODUCES, AND HOW IT IS HANDLED.** A mon that EVOLVES
  between the caller capturing its object and the lookup running no longer matches on species.
  Rather than abort a working flow, a **unique** PID hit whose species disagrees is **re-resolved
  from the live party and reported LOUD**; a species miss with two or more PID hits **RAISES**,
  because the caller may be about to release something. ⛔ It must NEVER fall back to "the first
  PID match" — that is the original bug. Both branches are asserted by the gate.
  ⚠ **Unexercised by any live caller today:** every current caller re-captures its target
  immediately before entering the PC menu, with no encounter-capable movement in between. It is
  defensive coding, and knowing it is untested by a real flow is part of the record.
- ✅ **One place it is NOT a problem, by luck rather than design:** `counter_hunt._stop()`'s new
  identity test (fixed 2026-08-14) *wants* the twins to share a PID — a Shedinja spawn then cannot
  look like a new catch, which is the correct answer. Do not "fix" the collision in a way that
  breaks that.
- **What a fix looks like:** key on **`(personality, species)`** wherever a PID selects a target
  for an ACTION. ⚠ Not a drive-by change — `get_index_for_pokemon` is shared by deposit, release
  and the party menu, and the release path is destructive. Needs its own fault-injected A/B with a
  fabricated twin pair.
- ✅ **THE COMPOSITE KEY IS NOT A NEW IDEA HERE — HALF THIS CODEBASE ALREADY USES IT.**
  `modules/pokemon_storage.py:128` (`get_slot_for_pokemon`) already matches
  `data[:4] == data[:4] AND species.index == species.index`. Its neighbour `:121`
  (`contains_pokemon`) and the party-side `get_index_for_pokemon` simply never got it. ⇒ frame the
  change as a **CONSISTENCY FIX**, which is the cheapest possible framing for review.

### ‼ RULED 2026-08-14 — key on **SPECIES**, never on the NAME. And the intuitive reason is WRONG.

The user proposed `(PID, name)`, reasoning that the bot never renames. An investigation fetched the
decomp live to settle it, and **refuted the objection that had been raised against the idea**
(mine: *"a default nickname is probably stale after evolution"*):

* ⛔ **THE NICKNAME IS NOT STALE. `EvolutionRenameMon` (`src/pokemon.c:5814-5821`) rewrites a
  DEFAULT nickname to the new species name on evolution**, and it runs at
  `src/evolution_scene.c:766` — **before** `CreateShedinja` at `:814`. Shedinja's own nickname is
  then set unconditionally (`:558`). So the Ninjask reads `"NINJASK"`, the Shedinja `"SHEDINJA"`,
  and **for this specific pair a name-based key WOULD have worked.** Cross-checked against
  `pret/pokefirered` — this is vanilla Gen 3, not a pret modernisation.
* ✅ **SPECIES still wins, for a stronger reason: NAME is species re-encoded as text.** Because
  `EvolutionRenameMon` keeps default-nickname and species-name in lockstep, the name carries
  **zero information species does not already carry** — it is not a second axis of discrimination,
  it is a lossy copy of the first, with its own failure modes:
  - **every EGG shares ONE nickname** — `sJapaneseEggNickname` (`src/daycare.c:838-841`), and our
    reader takes the RAW bytes (`modules/pokemon.py:1000`), so all eggs collapse to one string;
  - **the nickname CHANGES for the same physical mon at hatch** (`src/egg_hatch.c:372-373`) — the
    same PID and species, a different name before and after, so `(PID, name)` is unstable across
    an event `(PID, species)` sails through;
  - **in-game trades ship preset nicknames** (`"DOTS"`, `"PLUSES"`, `"SEASOR"`, `"MEOWOW"` —
    `src/data/trade.h`) which never match an old species name and so **never update on evolution**;
  - `language != GAME_LANGUAGE` **disables the rename entirely** (`pokemon.c:5819`).
* ⛔ **AND "the bot never renames" is true only by a hair.** Every gameplay path declines the
  naming screen (`battle_handler.py:876-881`, `_listeners.py:455-465`, `static_gift_resets.py:195-207`,
  `starters.py:62,182`, `early_game.py:1041`, `game_corner.py:125`) — but `starter_nickname` is
  **already wired end to end** (`modules/story/config.py:18,27-32`, a random pool at
  `early_game.py:998-1007`) and short-circuited by one hard-coded `"No"`, `on_should_nickname_pokemon`
  is a sanctioned plugin hook (`plugin_interface.py:196-205`), and the debug utilities/GUI set names
  like `"Hulk"`, `"Ability"` and **`"CHEAT"`** (`debug_utilities.py:551-616,653-666`,
  `gui/debug_menu.py:187-206`, `gui/debug_edit_party.py:199`).
  ⇒ **Keying a DESTRUCTIVE path on a field the project is one uncommented `if` away from making
  arbitrary is a design error regardless of the decomp.**

### ⛔ THE CALL SITES THAT MUST **NOT** GET THE SPECIES COMPONENT

**`counter_hunt.py`'s PID SETS DEPEND ON THE TWINS SHARING A PID** — `_party_pids_now` /
`_box_pids_now` and the set-difference in `catch_confirmed` (`counter_hunt.py:311-342`). That fix
(2026-08-14) works *because* a Shedinja carries its Ninjask's PID and therefore cannot look like a
NEW identity. **Adding species there would make a Shedinja spawn report a catch that never
happened — reintroducing the exact bug that code was written to fix.** Likewise leave the
protected/hunted PID *sets* alone (`pc_trip.py:136,446`, `early_game.py:1769`,
`higher_level_actions.py:245-247`): those mean "don't touch anything in this family", and a twin
SHOULD inherit its sibling's protection — widening is the safe direction, narrowing is not.

### Residual collisions after the fix (name them, do not claim uniqueness we lack)
* **R2 — debug paths** (`debug_utilities.py:314-410`, `gui/debug_edit_party.py:199`) can fabricate
  two identical-PID identical-species mons by hand ⇒ the key must **detect** ambiguity, not assume
  it away.
* **R3 — corrupt/Bad-Egg box slots** read PID 0 / species 0; the box reader filters only on
  `is_empty` (`pokemon_storage.py:101`) where the party reader also checks `is_valid`
  (`pokemon_party.py:120`).
* **R5 — Battle Frontier rentals** overwrite `gPlayerParty`; a pre-entry PID is then simply absent
  (a miss, not a mis-hit). No bot code enters the Frontier.
* **R6 — a NEW failure mode the change introduces:** if a mon evolves between object capture and
  key use, the composite key **misses** where PID-only would have hit — converting a silent
  wrong-target into a loud abort. Correct for RELEASE; a behaviour change everywhere else.
  ⇒ On a species mismatch with a unique PID hit, log LOUD and **re-resolve from the live party**;
  raise only on genuine ambiguity, and NEVER fall back to the first PID hit.
- **Cheap detection meanwhile:** a duplicate-PID check over the party would flag the condition in
  one line, and it is worth logging LOUD when it fires, because every PID-keyed decision taken
  while it holds is suspect.



---

# ARCHIVED 2026-08-16 — KI-65's 2026-08-12 SELF-CORRECTION

Moved out of `05-KNOWN-ISSUES.md` on the R3 3,000-line budget when KI-65 was FIXED and GATED.
Verbatim, unedited. Context: KI-65 is now closed in sandbox (gate #25); this is the pre-fix
narrowing of the original filing.

## ‼ KI-65 CORRECTED 2026-08-12 (same day) — my first description OVERSTATED it

I originally wrote that the re-pick *"has quite possibly never executed"*. **That is too strong, and
an inaccurate issue is worse than none.** Reading the control flow properly:

`party_index` is assigned at line 371 inside branch **(2) `AskWhetherToLearn`** — the "Delete a move
to make room for X?" prompt — which in the normal sequence runs BEFORE a slot is confirmed and
therefore before the game can refuse with `CantForgetHM`. So on an ordinary teach the name IS bound
and the re-pick DOES run.

**The real, narrower bug:** line 371 sits inside a `try:` whose `except Exception:` (line 377-381)
silently defaults `move_to_forget` when `_read_offered_move` fails. On that path `party_index` is
**never bound**, so a later `CantForgetHM` raises `UnboundLocalError` into the *second* silent
`except`, which declines. ⇒ The two failures COMPOUND: the read failed invisibly, and then the
recovery from the refusal failed invisibly too. Both look like decisions.

**Why it still matters and is still filed:** it is a real latent `UnboundLocalError` on a real path,
it is exactly the "fail-safe `except` that returns the SUCCESS value" pattern, and it is the reason
the pyflakes gate cannot yet be widened past the story surface. **Fix deliberately deferred** to a
focused pass with its own repro (force `_read_offered_move` to fail, then force `CantForgetHM`, and
assert the re-pick either runs or says loudly that it cannot) — changing the teach flow without that
repro is how `#24-teachmsgstall` got its current "the fix had no production effect" verdict.

‼ **Method note for the next agent:** this correction came from reading the ENCLOSING control flow
rather than the flagged line. A linter tells you a name is not provably bound; it does not tell you
how often that happens. Do not convert a static warning into a severity claim without tracing who
assigns it first.

---


---

# ARCHIVED 2026-08-16 — KI-65 RECON SECTION (C), the pre-fix fixture argument

Moved out of `05-KNOWN-ISSUES.md` on the R3 3,000-line budget. ‼ Kept because it is a WORKED
EXAMPLE of the failure this project cares about: careful reasoning that correctly rejected one
discriminator and then proposed a second one that was equally vacuous, because it was never run.
Verbatim, unedited.

⛔ **(C) THE CAPTURED SAVES ARE A FIXTURE, NOT A REPRO.** `saves/movelearn_hmwedge_{quickattack,slash}.ss1`
DO enter `CantForgetHM` on frame 0 (`repro_movelearn_hm_wedge.py`) — but on a fresh generator
`last_confirmed_slot is None`, so `:273` is FALSE and **`:280` never executes**. Both arms already
report `VERDICT = RESOLVED`, `moveset changed = False`. ‼ **So an A/B whose discriminator is
"moveset unchanged" is VACUOUS — that is today's GREEN result.** ⛔⛔ **AND THE DISCRIMINATOR THIS ENTRY FIRST
PRESCRIBED WAS ITSELF VACUOUS — corrected 2026-08-16 by a cold-start agent that COMPUTED it.** It
said *"a non-empty `hm_blocked` plus a `context.message` containing `Replacing slot`"*. Traced:
`hm_blocked.add(...)` is `:274`, **BEFORE** the `try:` at `:279`, so it is set whether or not `:280`
raises — it proves *a slot was refused*, never *the re-pick ran*. And `"Replacing slot"` (`:295`) is
**FALSE IN BOTH ARMS**: reaching it needs `party_index` BOUND, which is exactly when the `:395` HM
veto works, and a working veto re-picks away from the HM so the game never refuses. ⇒ the
conjunction is FALSE in both arms and would read as **NO DIFFERENCE — a refutation of a true
finding.** ‼ *The fixture was corrected once; the DISCRIMINATOR was never re-derived against it.*
✅ **THE DISCRIMINATOR THAT WORKS** (on `movelearn_hmwedge_quickattack.ss1` — COMBUSKEN L32:
Scratch, **Rock Smash HM06**, Double Kick, Ember): **ARM A (fault ON)** → `:280` raises →
`move_to_forget = 4` → the message *"Nothing else can be given up — declining the new move"* is
printed **while THREE forgettable moves exist** (Scratch, Double Kick, Ember). **That message is a
PROVABLE LIE, and the contradiction is the assertion.** **ARM B (fault OFF)** → the veto's own
lowercase text (`:428-431`) or none. ⛔ `moveset changed` stays `False` in BOTH arms — never grade
on it. Today an `UnboundLocalError` there prints *"Nothing else can be given up —
declining the new move"* **with full confidence**, which is a lie the user can read.


---

# ARCHIVED 2026-08-16 — KI-65 RECON SECTIONS (A) AND (B), the pre-fix analysis

Moved out of `05-KNOWN-ISSUES.md` on the R3 3,000-line budget once KI-65 was FIXED, GATED and
PROMOTED to both forks. Verbatim, unedited. ⚠ (B)'s closing prediction — that the ping-pong needs
a latch in the `:377` handler — was MEASURED FALSE: the HM veto's `is None` guard forces
`move_to_forget = 4` in the same iteration. Kept because the four-step conjunction it traces is
correct and is what made the repro constructible.

⛔ **(A) THERE ARE *TWO* LIVE UNBOUND READS, NOT ONE — AND THE ONE THIS ENTRY NEVER MENTIONED IS THE
MORE DAMAGING.** Besides `:280` (the re-pick), **`:397` — the HM VETO — reads `party_index` too**,
inside a `try` whose handler is a bare **`except Exception: pass`**. That is the loudest possible
silence: it leaves `move_to_forget` unchanged with no message and no flag, and is **completely
indistinguishable from the success case** "the chosen slot is not an HM, so the veto correctly did
nothing". ‼ The veto's own comment names the exact case it fails to cover — *"the `except` fallback
right above which blindly picks slot 0 without consulting any policy at all"* — and that fallback
(`:377-381`) **is precisely the path that leaves `party_index` unbound.** The last line of defence
is structurally unable to defend against the one case it was written for.

⛔ **(B) FIXING `:280` ALONE DOES NOT FIX THE BUG — the loop is driven from somewhere else.** The
precondition for `:280` to raise is a FOUR-STEP CONJUNCTION, and step 2 *causes* steps 3-4:
  1. `_read_offered_move` raises ⇒ `party_index` unbound **and** `move_to_forget = 0` (`:381`);
  2. the HM veto at `:397` silently no-ops on the same unbound name (`except` `:433`, `pass` `:434`) ⇒ a doomed
     HM pick survives that would otherwise have been re-picked away;
  3. branch (1) confirms slot 0 with A ⇒ `last_confirmed_slot = 0` (`:339`);
  4. the game refuses ⇒ `CantForgetHM` ⇒ `:273` true ⇒ `:280` `UnboundLocalError` ⇒ decline.
Then it **PING-PONGS**: `last_offered_move_name` is only set at `:376` *after* the failing call, so
branch (2) re-enters the same `try` forever, and `:380-381` **re-arms `move_to_forget = 0`** every
cycle. ⇒ `frames_in_dialogue > 6000`, `_STALLED_EXITS` increments, the caller re-invokes fresh, and
the third strike raises `BotModeError`. ‼ **That is the `#24-teachmsgstall` / `#24-movelearn-recovery`
signature** — a mechanically complete path, and **still a HYPOTHESIS until the injected repro runs.**

⛔ **(C) — THE PRE-FIX ARGUMENT ABOUT THE CAPTURED SAVES: MOVED to `31-KNOWN-ISSUES-ARCHIVE.md`
(2026-08-16).** It reasoned its way to *"the captured saves are a FIXTURE, not a repro"* and then
prescribed a discriminator that was ALSO vacuous. ✅ **Superseded by MEASUREMENT** — see "THREE THINGS
THE RECON GOT WRONG" at the top of this entry, which shows those saves cannot exercise the bug at all.


---

# ARCHIVED 2026-08-16 — KI-65's pre-fix FIX SPECIFICATION ("in three parts")

Moved out of `05-KNOWN-ISSUES.md` on the R3 3,000-line budget. ‼ Its part (3) — the
`offer_read_failed` latch, asserted as the thing without which the ping-pong survives — was
MEASURED FALSE and the latch was removed before commit. Kept verbatim as the worked example.

✅✅ **THE FIX, SPECIFIED IN THREE PARTS — ⛔ SUPERSEDED: PARTS (1) AND (2) ARE APPLIED IN SANDBOX;
PART (3) WAS BUILT AND THEN REMOVED AS MEASURABLY REDUNDANT
(2026-08-16), AFTER the repro this block demanded was built. See the FIX block at the top of this
entry. The deferral below is HISTORY and is satisfied; do not read it as an instruction to hold
off.** The specification is kept because its part (3) turned out to be WRONG in an instructive way — it
named the latch as the loop-preventer when the veto guard is:
(1) `party_index: int | None = None` beside `:185`, matching
`last_confirmed_slot: int | None = None`'s style (⚠ this said `:177` — that is `last_offered_move_name`); (2) EXPLICIT `if party_index is None:` guards at
`:280` and `:397` that say loudly they cannot act, instead of letting `except` swallow an
`UnboundLocalError` indistinguishably from success; (3) set `last_offered_move_name` (or an
equivalent "we already failed to read this offer" latch) in the `:377` handler — **without (3) the
ping-pong in (B) survives the fix.**
⛔ **`custom-pokebot`'s copy WAS byte-identical and IS NO LONGER** — the fix landed in sandbox on
2026-08-16 and was PROMOTED the same day (user-approved), so `promote.py --check` reports
**0 differing** again. Both forks carry the fix.


---

# ARCHIVED 2026-08-16 — KI-65's "DANGERS" list (pre-fix)

Moved out of `05-KNOWN-ISSUES.md` on the R3 3,000-line budget once KI-65 was closed and promoted. Verbatim.
The two entries that still bite were kept inline in KI-65 rather than archived.

⛔ **DANGERS, measured, that a naive fix walks into:**
* **`move_to_forget = 4` is OVERLOADED** — "decline" to branch (2), but a **cursor ROW** to branch
  (1) (`:328-335`). ⚠ **Branch (1) has NO `try`**, so a `None` sentinel leaking into its
  `cursor < move_to_forget` comparison raises `TypeError` into nothing at all.
* **Three callers, two of them not the battle handler:** `battle_evolution_scene.py:49` and
  `modes/util/items.py:349` (**Rare Candy from the bag**, a `while True:` whose only exit is the bag
  menu). Any change to `_read_offered_move`'s CONTRACT hits both.
* **Per-invocation vs module-level memory:** `hm_blocked`/`last_confirmed_slot` die on every return
  while `_STALLED_EXITS` deliberately does not, so a re-invoked generator **loses the refusal
  knowledge but keeps the strike count**. Promoting state to module level would need resetting at
  `:256`/`:451` or it leaks across battles — a bug already fixed once for the strike counter.
* ⚠ `get_party_menu_cursor_pos` does **not** raise on a bad cursor: it calls `set_manual_mode()` and
  returns `slot_id = -1`, and `get_party()[-1]` is the LAST party member. That failure mode is a
  **wrong mon, not an exception** — a second, separate silent-wrong-answer path.


---

# ARCHIVED 2026-08-16 — KI-65's fault-injection-seam analysis (pre-fix)

Moved out of `05-KNOWN-ISSUES.md` on the R3 budget. ⚠ It recommended faulting `map_battle_party_index` as the
"most plausible real raiser" — MEASURED INSUFFICIENT: `_read_offered_move`'s task-backed path
bypasses it entirely and binds `party_index` anyway (51 fires, zero effect). Verbatim.

✅ **THE FAULT INJECTION POINT IS IDENTIFIED AND NEEDS NO PRODUCTION EDIT.** `battle_move_replacing.py`
has **no `POKEBOT_*` hook anywhere** (checked: zero `os.environ` references). `:371` calls
`_read_offered_move` by bare name, so rebinding `bmr.get_battle_state` (or `bmr._read_offered_move`)
on the imported module object takes effect immediately — the same mechanism
`repro_hm_replace_valve_forced.py:170-188` already uses to latch `get_learn_move_state`.
‼ **Fault the CAUSE, not the function:** the most plausible real raiser is
`map_battle_party_index` → `RuntimeError` (`battle_state.py:354`), fed by a RAW byte
`read_symbol("gBattleStruct", 16, 1)[0]` read on an arbitrary frame while the UI animates — needs no
exotic conditions. Both halves are required: the fault ALONE does not reach `:280` (see (C)).


---

# ARCHIVED 2026-08-17 — KI-66 RECON (1) THE FIXTURE and (2) THE FAINT MECHANISM

Moved out of `05-KNOWN-ISSUES.md` on the R3 3,000-line budget once the driver was BUILT and
DRIVEN (`--driver ki66faint`), which embodies both. Verbatim. ⚠ Note that the SAME recon's
part (3) — a "narrowing" claiming the ally-only state coincides with the game's loss
condition — was REFUTED by the first live run; see KI-66.

**(1) THE FIXTURE EXISTS — it was never missing, only undocumented.**
`--driver spacecenter2`, anchor **`saves/at_steven_2f.ss1`** (SPACE_CENTER_2F (13,2),
`MOSSDEEP_SPACE_CENTER_STATE = 2`), drives `ChooseHalfPartyForBattle` and the real six-mon multi
battle alongside Steven. It is documented in `story_harness.py` and in NO PROJECT KNOWLEDGE file,
which is why the audit could not find it. *(Also present: `at_mossdeep_leaders.ss1`,
`post_space_center.ss1`; drivers `spacecenter1`, `spacecenter`, `faintrepro`.)*

**(2) THERE IS NO FAINT MECHANISM, AND THE FAITHFUL ONE IS NOT A MEMORY WRITE.**
MEASURED: **none** of the 16 `POKEBOT_*` hooks can faint a mon or set HP, and `debug_write_party`
writes `gPlayerParty` (out-of-battle) — **not** `gBattleMons`. ✅ **So do NOT add a `gBattleMons` HP
writer.** Pre-stage the party BEFORE the battle with one mon at **1 HP**; it then faints in real
combat. That is faithful gameplay, and it keeps this out of "documented last-resort state-write"
territory entirely. ‼ 1 HP, not 0: `GetBattleEntryEligibility` rejects a 0-HP mon, and
`battle_party_slots` (`space_center.py:503`) only offers eligible ones — a fainted mon would never
be SELECTED, so it could never faint on the field.


---

# ARCHIVED 2026-08-17 — KI-66's original 2026-08-12 site table

Moved out of `05-KNOWN-ISSUES.md` on the R3 budget once KI-66 was DRIVEN. Verbatim. ⚠ Its per-site
severity guesses are superseded by measurement: the ally inclusion at `:630-636` proved INERT
on the driven trajectory, while the on-field exclusion's index space proved to be the real
defect. See KI-66's DRIVEN block.

| site | what it does wrong |
|---|---|
| `battle_handler.py:541-545` | the `new_lead_index is None` fallback scans the FULL party — and KI-64's guard makes `None` *more* likely, so it feeds this |
| `battle_handler.py:588-598` | full-party revalidation that writes a **party-order** index into a variable used as a **menu-order** index at `:600` (the KI-34 shape) |
| `battle_handler.py:630-636` | `alive_slots` excludes only the on-field pair, so the ally's benched mons are A-press candidates; each refusal round-trips `Task_ReturnToChooseMonAfterText` — three of six slots are guaranteed-refused in this fight |
| `_util.py:522-587` `get_potential_rotation_targets` / `select_rotation_target` | full-party, called live here from `default.py`; the result reaches `battle_action_selection.py:288`, an **unbounded** `while get_game_state() == PARTY_MENU: press A` |


---

# ARCHIVED 2026-08-17 — KI-80 (full entry)

Moved out of `05-KNOWN-ISSUES.md` on the R3 3,000-line budget. The arc is CLOSED, FIXED, GATED and PROMOTED TO BOTH FORKS
(2026-08-16, user-approved). Verbatim, unedited. Header reproduced first.

## KI-80 — `grass_is_fodder` CONFLATED "no training patch configured" with "the patch is too weak", and it CO-GATED the counter-ladder (with `boss_teaches`, inside `losses >= 2`) — so giving a boss a training area silently disabled its KI-23 machinery. ✅ DECOUPLED AND PROMOTED TO BOTH FORKS 2026-08-16 (this KI's own file is in both forks) (2026-08-16, ✅ **REPRODUCED AND DRIVEN** — `--driver ki80ladder` is COMPLETE and PASSING: **4 arms**, both forks, mirror-regression guard fault-tested against the real naive edit. ✅ **AND THE DECOUPLING IS NOW BUILT, DRIVEN AND REVIEWED** — `:1901` is `if boss_teaches:`, `boss_mode` sits behind its own `if grass_is_fodder:`; `repro_boss_grass_gate.py` has SELF-RETIRED. ✅ **AND PROMOTED TO BOTH FORKS 2026-08-16 (user-approved), proven by a THREE-POINT A/B against `--build custom`; that file is in BOTH forks.** ⛔ **THIS KI STAYS OPEN ONLY FOR ITS TRACKED RESIDUAL** `#24-zerokocounter`: should `boss_teaches` come off the gate too? Not shipped because no arm can discriminate it, and an audit derived that it would need TWO new arms plus a frequency measurement first)

- **The line.** `plugins/custom_modes/story_mode.py:1899`:
  ```
  grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)
  ```
  and `:1901`:
  ```
  if grass_is_fodder and boss_teaches:
      hopeless, needed = self._boss_plan_is_hopeless(cfg)     # the ONLY call site
      if hopeless:
          acted = yield from self._counter_ladder(cfg, losses, needed)   # ditto
  ```
- **The defect.** One boolean carries two unrelated meanings — *"this boss has no patch"* and
  *"this boss's patch is far below the team"* — and it gates **KI-23's** hopeless-detector and
  counter-catch ladder. The two facts justify boss-training mode for the same reason, but they say
  nothing in common about whether the party has a TYPE ANSWER, which is what the counter ladder is
  for. ⇒ **A boss cannot be given a training patch without losing its counter machinery.**
- **‼ DERIVED CONSEQUENCE — ARITHMETIC ON MEASURED BANDS, *NOT* A REPRODUCTION** (see "NOT OBSERVED FAILING" below; the 198/41/41 figures ARE measured, but they are KI-23's history, not this scenario). On the exact boss KI-23 was filed for: `wild_max` is read from the
  ROM's LAND table for `cfg["grass"][0]` (`:1886-1890`). Winona's band is **(29,33)**; the patch
  the adjacent code comment suggests is **Route 119, band 24-27**. For any team at **L30-35** —
  i.e. her own band — `27 + 8 = 35 < team_max` is **FALSE**, so `grass_is_fodder` flips to False
  and the counter ladder is SKIPPED. Control falls to the plain
  `plus5_max`/`plus5_avg`/`escalate_band` escalation at `:1937-1951` — **the path KI-23 measured
  failing 198 attempts / 41 losses / 41 whiteouts, never converging**, because it does not
  converge when the party has no super-effective answer.
- ⛔ **AND IT IS INVISIBLE.** The regression prints a healthy-looking
  `"Story: lost here N× — training harder before re-attempting (target Lv X, plus5_max)"`.
  Nothing errors, nothing derails. The only symptom is the ABSENCE of the counter-catch message —
  and this project has been caught by absence-as-signal repeatedly.
- **How it was found.** An adversarial pass over `03-PUNCH-LIST`'s **(P6)** item, which asked for
  *"TRAINING-AREA MAPS per gym AND per boss"* and cited as its hole: *"Winona has no patch
  configured at all, so the whole relocation machinery is skipped for her."* ‼ **Acting on that
  sentence would have caused this regression.** Both of (P6)'s stated examples turned out to be
  wrong — see the (P6) entry in `03-PUNCH-LIST.md`, now corrected.
- ✅ **GATED — `tools/story-dev/repro_boss_grass_gate.py` (suite #24).** It re-derives the coupling
  from the live AST and then forbids a `"grass"` key on `winona_fight`, `flannery_fight` and
  `rival110_fight` while it stands. **AST-based**, so a mention in a comment or docstring cannot
  trigger it, and **SELF-RETIRING**: decouple the ladder and the gate stops enforcing and says so.
  `--self-test` proves all four directions (fires when broken; quiet when healthy; quiet when
  decoupled; quiet on comment-only mentions).
- ✅✅ **SUPERSEDED 2026-08-15 — IT HAS NOW BEEN OBSERVED FAILING, ON DEMAND, IN BOTH FORKS.**
  ⛔ This bullet previously read *"NOT OBSERVED FAILING … report it as 'would fire', never 'has
  fired'."* That was correct when written and is **retracted now**: `--driver ki80ladder`
  (`story_harness.py`) DRIVES production's own `_prepare_for_fight` three times on
  `saves/batch2_run04_wedge.ss1` and watches which branch it takes. **Measured, `team_max = 28`:**

  | arm | `cfg["grass"]` | `wild_max` | outcome |
  |---|---|---|---|
  | `NOGRASS` | absent | n/a | **`_counter_ladder` reached** |
  | `GRASS_FODDER` | Route 102 | **4** | **`_counter_ladder` reached** |
  | `GRASS_STRONG` | Route 119 — the patch her OWN cfg comment names (`story_mode.py:3531`: *"Route 119 is the Fortree-side band"*) — ⛔ she has NO `grass` key today, which is the only reason her ladder still works | **27** | ⛔ **plain escalation; ladder SKIPPED** |

  Same party, same seeded losses (8), same boss — **the only difference is the `grass` key.**
  `ACCEPTANCE: PASS` on `--build sandbox` AND `--build custom`. Production itself derived
  `needed = ['Rock', 'Ice', 'Dragon']` and raised *"Winona: 8 losses with no super-effective
  answer…"* on the two ladder arms, and printed *"lost here 8× — training harder before
  re-attempting"* on the third. ⇒ **the regression is real, and it is exactly as silent as
  predicted.** Transcripts: `tools/story-dev/evidence/2026-08-15-ki80ladder-*.stdout.txt`.
  ‼ **The driver EXITS 0 even on FAIL** (it is a harness driver, not a gate) — **grade on the
  `ACCEPTANCE:` line, never on the exit code.**
- ✅ **AND THE DRIVER IS FAULT-TESTED, not merely green.** Two deliberate failure runs, both
  committed as evidence: (1) against `ch13_fortree_door.ss1` — the fixture THIS ENTRY ONCE
  PRESCRIBED — it prints `ACCEPTANCE: FAIL … THE A/B WOULD BE VACUOUS: ROUTE119 does not flip
  `grass_is_fodder` at team_max=39`, **and all three arms come back `LADDER`**, demonstrating live
  that the prescribed test would have shown NO DIFFERENCE and read as a REFUTATION of a true
  finding; (2) with `POKEBOT_KI80_DECOUPLED=1` it FAILS today, which is what proves the same driver
  can serve as the AFTER run once the fix lands.
- ⛔ **WHAT THE DRIVER DOES NOT PROVE.** Its `_counter_ladder` spy replaces the ladder's BODY, and a
  tripwire in a console proxy cuts every arm off AT its decision. It proves the gate is **REACHED**;
  it proves nothing about what the hunt then does. Deliberate — the hunt travels, and travel is risk
  this test does not need. Design and the refutation that reshaped it:
  `ai-research-notes/2026-08-15-ki80-ladder-repro-design.md`.
- **What a fix looks like** (NOT attempted — it changes boss prep for EVERY gym, and KI-23's own
  entry warns about the mirror regression): split the two meanings. The counter ladder should be
  gated on *"is this fight hopeless"* — which `_boss_plan_is_hopeless` already answers on its own —
  not on whether a patch happens to be configured. ⛔ **The change may not ship on reading alone:**
  it needs the KI-23 repro conditions DRIVEN, both before and after, confirming `_counter_ladder`
  still fires rather than falling through to the plain escalation.
  ✅✅✅ **BOTH HALVES ARE NOW MET — THE DECOUPLING SHIPPED (sandbox) 2026-08-16.**
  AFTER: `POKEBOT_KI80_DECOUPLED=1` **FAIL → PASS**; arm 4 **still PASS** (no mirror regression);
  the coupled expectation now **FAILS**, proving the behaviour changed; `repro_boss_grass_gate.py`
  **SELF-RETIRED** and still exits 0. An adversarial diff review attacked six angles and all six
  SURVIVED — including that the `:1932` elif's firing condition is algebraically unchanged, that
  `_boss_plan_is_hopeless` is read-only and fails safe, and that the new `BotModeError` is caught at
  `:4080-4081` (`outcome = "derailed"`) rather than crashing a batch.
  ⚠ **Blast radius: arithmetic MEASURED, behaviour INFERRED** — Brawly/Roxanne/Wattson gain the
  machinery; **no run against those three exists**, only Winona's fixtures were driven.
  ✅ **PROMOTED 2026-08-16, user-approved, by a THREE-POINT A/B against `--build custom`** (not a
  byte-compare): `POKEBOT_KI80_DECOUPLED=1` **FAIL → PASS**, the coupled expectation **PASS → FAIL**,
  and **arm 4 PASS on both sides** — the invariance proving the mirror regression did not land.
  *(Superseded: the line below said the decoupling was merely unblocked.)* The AFTER run is the same command with
  `POKEBOT_KI80_DECOUPLED=1`, which must go from FAIL (today, measured) to PASS.
  ⛔ **The BEFORE run is unrepeatable once the fix lands — it was run and committed FIRST**, the
  rule KI-79's three-point A/B established.
- ⛔⛔ **BEFORE YOU DECOUPLE — TWO THINGS THE REPRO DRIVER CANNOT SEE (found by a Tier 2 cold-start
  agent that tried to BEGIN this item, 2026-08-15).** The naive edit is "delete `grass_is_fodder and`
  from `:1901`". ‼ **That is not sufficient, and its damage is invisible to `--driver ki80ladder`.**
  1. **`grass_is_fodder` HAS A SECOND USE SITE:** `:1932`, `elif grass_is_fodder and recent_kos and
     not boss_teaches:`. Decoupling `:1901` without deciding `:1932` leaves one boolean half-split.
  2. ⛔ **`:1925 boss_mode = True` IS ON THE *NOT-HOPELESS* PATH, AND `:1937` READS IT**
     (`if losses >= 2 and not boss_mode:`). So moving the hopeless check out from behind
     `grass_is_fodder` hands `boss_mode = True` to every boss that has a **strong patch AND a
     credible answer** — silently disabling their grass escalation. **That is precisely KI-23's
     mirror regression**, arriving through the edit meant to fix KI-80.
  ‼‼ **AND ARMS 1-3 CANNOT SEE IT.** All three use a NO_ANSWER party, so `hopeless` is True, the
  ladder fires, and `_prepare_for_fight` RETURNS at `:1924` — **`:1925` is never reached in any arm.**
- ✅✅ **SO ARM 4 IS NOW BUILT AND MEASURED — `POKEBOT_KI80_ARM4=1` (2026-08-16).**
  `POKEBOT_KI80_ARM4=1 … story_harness.py fortree_gym_wedge.ss1 --driver ki80ladder --frames 2000`
  → **`ACCEPTANCE: PASS`**, `OUTCOME=PLAIN_ESCALATION`, `INVARIANCE drift=none`.
  ‼ **Its assertion is FIX-SHAPE-AGNOSTIC and identical before and after:** a boss with a strong
  patch AND a credible answer must keep its plain grass escalation.
  ✅✅ **AND THE DETECTOR ITSELF IS NOW FAULT-TESTED AGAINST THE REAL NAIVE EDIT (2026-08-16) —
  THIS WAS A PREDICTION UNTIL AN AUDIT POINTED OUT THAT NOTHING HAD EVER SEEN IT FIRE.**
  `:1901` was temporarily changed to `if boss_teaches:` (the naive fix), both suites were run, and
  the edit reverted. The result is the strongest single argument for arm 4's existence:
  | run, under the NAIVE edit | result |
  |---|---|
  | arms 1-3, `POKEBOT_KI80_DECOUPLED=1` | ⛔ **`ACCEPTANCE: PASS`** — all three reach the ladder |
  | **arm 4**, `POKEBOT_KI80_ARM4=1` | ✅ **`ACCEPTANCE: FAIL`**, `ARM4 OUTCOME=BOSS_TRAINING_MODE` |
  ⇒ **THE THREE-ARM TEST ALONE WOULD HAVE BLESSED THE REGRESSION.** Arm 4 is the only thing that
  catches it, and it names it: *"a boss with a STRONG patch AND a credible answer entered
  BOSS-TRAINING MODE, so `:1937`'s plain grass escalation is SUPPRESSED."*
  ⇒ ‼ **THE FIX MUST KEEP `boss_mode = True` (`:1925`) BEHIND `grass_is_fodder`.**
  Transcripts: `evidence/2026-08-16-ki80ladder-FAULT-naive-edit-*`. ⚠ *A gate that has never failed
  may simply not be looking — this one has now failed on purpose.*
  ⛔⛔ **AND THE FIXTURE THIS ENTRY FIRST PRESCRIBED FOR ARM 4 WAS VACUOUS — THE SAME TRAP, THE SAME
  NUMBER, THE THIRD TIME.** It said *"`fortree_gym_wedge.ss1` … is exactly right for it"* with a
  **Route 119** patch. `fortree_gym_wedge` IS correctly HAS_ANSWER (Castform's Powder Snow scores
  **160 >= 75**) — but its **`team_max` is 39**, and `27 + 8 = 35 < 39` is TRUE, so `grass_is_fodder`
  is **True anyway** and the "strong patch" arm is silently a FODDER arm. *The check verified the
  INVERSE of condition 7 and once again never verified condition 9 — exactly how
  `ch13_fortree_door.ss1` (also `team_max` 39) survived an earlier audit.*
  ✅ **THE FIX, MEASURED 2026-08-16 across every `TRAINING_GRASS` map plus 9 candidates:** arm 4 needs
  a map with land `wild_max >= team_max - 8 = 31`, and **the ONLY one that clears it is
  `VICTORY_ROAD_1F` at 40** (Routes 121/123 peak at 28; ROUTE119 and ROUTE118/120 at 27;
  MT_PYRE_EXTERIOR 29). So arm 4 pairs `fortree_gym_wedge.ss1` with a **VICTORY_ROAD_1F** grass key:
  `40 + 8 = 48 >= 39` ⇒ `grass_is_fodder` is genuinely **False**.
  ⚠ **Victory Road is NOT a plausible training area for Winona, and the arm does not pretend it is** —
  arm 4 is a DECISION-level test of the branch, exactly as arms 1-3 are not a faithful Winona run.
  ✅ **Both of arm 4's controls are MEASURED, and the first is FAULT-TESTED:** CONTROL-A calls the
  REAL `_boss_plan_is_hopeless` and requires **not** hopeless — run against a NO_ANSWER save it FAILS
  with *"this save is NO_ANSWER (hopeless=True), so it cannot exercise the `:1925 boss_mode` path at
  all"*; CONTROL-B re-derives condition 9 INVERTED from the live ROM. Transcripts:
  `evidence/2026-08-16-ki80ladder-ARM4-*`.
- ✅ **THE PROMOTION ENTANGLEMENT IS RESOLVED (2026-08-16).** This bullet used to warn that a KI-80
  fix could not be promoted separately from an unapproved comment-only edit sitting in the SAME
  file (`plugins/custom_modes/story_mode.py`). **The user ruled, the comment-only correction was
  promoted** — so the KI-80 fix, when approved, promotes cleanly on its own.
  ✅ The KI-80 decoupling was itself promoted 2026-08-16 on that same rule. *(✅ The KI-81 whiteout guard was promoted 2026-08-16 too, which returned the figure to zero at that moment. It then went to **1** later the same day when the KI-65 fix landed in sandbox, and back to **0** when KI-65 was PROMOTED — see KI-65's header. ‼ This parenthetical asserted "NOT zero" for a while after that stopped being true, which is why the rule below exists: run the tool; never quote a drift figure from prose.)*
  *(⚠ The superseded wording is DESCRIBED rather than reprinted: `audit_doc_consistency` matches
  literal strings and cannot tell a quotation from a claim — it red-flagged the first draft of this
  very bullet for reciting the old figure.)*
  ‼ **Keep the general rule, which is what actually matters:** *`promote.py` moves whole FILES, so
  two unrelated edits to one file cannot be promoted separately.* Land an approved edit before
  starting an unapproved one in the same file, or they become a single decision. ⛔ And when the fix ships, `repro_boss_grass_gate.py`
  (suite #24) **SELF-RETIRES** — it stops enforcing and says so; that is designed, not a failure.
- ⛔⛔ **THE REPRO CONDITIONS, READ FROM THE SOURCE 2026-08-15 (a static code read, not a live
  measurement — every row carries its file:line so it is checkable) — AND THEY ARE NOT WHAT THIS
  ENTRY FIRST SAID.** An earlier draft here said *"losses >= 2, kos >= 1, no type answer"*. That is
  **INCOMPLETE, and a test built to it would be VACUOUS**: at `losses` 2-5 the ladder cannot fire
  *whatever* the grass key is, so the A/B would show NO DIFFERENCE and would look like a refutation
  of a true finding. All of these must hold together:
  | # | condition | where |
  |---|---|---|
  | 1 | `losses >= 2` — the outer boss-training block | `story_mode.py:1877` |
  | 2 | `grass_is_fodder` — TRUE today for Winona only because she has no `grass` key | `:1899` |
  | 3 | `boss_teaches` — at least one of the **LAST TWO** losses has `kos >= 1` | `:1893-1900` |
  | 4 | ‼ `losses >= PLATEAU_LOSS_THRESHOLD` = **6** | `:1507`, `:1046` |
  | 5 | ‼ `len(_loss_ko_history) >= 6` | `:1512` |
  | 6 | ‼ NOT improving: `max(kos of last 3) <= max(kos of previous 3)` | `:1514-1517` |
  | 7 | ‼ **no battler has a credible answer**: some move with `eff >= 2.0` **and** `base_power * eff * stab >= 75` | `:1573-1596`, `:1087` |
  | 8 | `"ace_types" in cfg` — absent short-circuits to `(False, [])` before the answer test | `:1557` |
  | **9** | ⛔⛔ **`team_max <= wild_max + 8` — THE ARMS MUST ACTUALLY DIFFER** | `:1899` |
  ⛔⛔ **CONDITION 9 WAS MISSING UNTIL A COLD-START AUDIT FOUND IT (2026-08-15), AND WITHOUT IT THIS
  ENTRY PRESCRIBED A VACUOUS TEST — the exact failure it was written to prevent, one condition
  over.** `grass_is_fodder` is `("grass" not in cfg) or (wild_max + 8 < team_max)`. The A/B only
  MEANS anything if adding the `grass` key FLIPS it to False, which needs
  `wild_max + 8 >= team_max`. For a **Route 119** patch `wild_max = 27`, so the fixture's
  **`team_max` must be <= 35**.
  ⇒ ⛔ **`ch13_fortree_door.ss1` — which THIS ENTRY PREVIOUSLY NAMED AS THE FIXTURE — FAILS IT.**
  Its **Blaziken L39** gives `team_max = 39`, and `27 + 8 = 35 < 39` is TRUE, so `grass_is_fodder`
  is True **in BOTH arms**, both take the same branch, and the run would show NO DIFFERENCE — which
  reads as a refutation of a true finding. It satisfies condition 7 (NO_ANSWER) and fails
  **condition 9** (which is condition 2's requirement stated as a checkable arithmetic test); the
  earlier check verified 7 and never the flip.
  ✅ **VERIFIED CANDIDATES that satisfy BOTH** (`probe_credible_answer.py`, run 2026-08-15 —
  all NO_ANSWER, `team_max` in brackets): `batch3_run03_wedge.ss1` [35, OVERWORLD, MAUVILLE_CITY],
  `batch2_run04_wedge.ss1` [28, OVERWORLD, ROUTE111], `batch3_run05_end.ss1` [34, ⚠ **in BATTLE**],
  `ch13_r119_wedge.ss1` [33, ⚠ **in BATTLE**, and ROUTE119 is a KI-24 wall map].
  ‼ **None is Winona-era** (badges 123/1234, not 12345) — which does NOT block a DECISION-level
  A/B (`_prepare_for_fight` reads party levels/moves, the grass map's `wild_max`, and the seeded
  loss history — never a badge), but it DOES mean the run is not a faithful Winona scenario and
  must not be reported as one. ⚠ `batch3_run03_wedge` sits exactly ON the boundary (`35 < 35` is
  false by one level), so a single level-up during the run would silently flip it — **prefer margin,
  and ASSERT the measured `team_max` and `wild_max` at run start rather than trusting this table.**
  ‼ A flat series of six losses each with `kos = 1` satisfies 3-6 at once.
  ⛔⛔ **AND A CEILING NOBODY WOULD GUESS: KEEP `losses` UNDER 12.** At
  `losses >= HARD_PLATEAU_LOSS_THRESHOLD` (**12**) with `len(history) >= 12` and a flat 12-series,
  `hard_plateau` becomes True (`:1541-1544`) and the answer loop runs as
  **`for i in (battlers if not hard_plateau else ()):`** (`:1573`) — i.e. over an **EMPTY tuple**.
  ⇒ `hopeless` comes back **True regardless of the party**, for a completely different reason than
  the one under test. An A/B that drifts past 12 losses would therefore go GREEN *without* proving
  anything about the no-answer path. **Seed 6-11 losses, never 12+**, and assert the count you
  seeded. *(Caught by a Tier 1 reviewer against an earlier draft of this table.)*
- ⛔ **AND THE OBVIOUS FIXTURE DOES NOT WORK — MEASURED LIVE.** `fortree_gym_wedge.ss1` (the
  anchor (P4) Stage 2 uses) **FAILS condition 7**: its **Castform L25 knows Powder Snow** (Ice,
  base_power 40), and vs Altaria (Dragon/Flying) that is `40 x (2.0 x 2.0) x 1.0 = **160** >= 75` —
  a credible answer, so `_boss_plan_is_hopeless` returns **not hopeless** and the ladder can never
  fire from that save. ✅ **9 of 10 Winona-era saves pass CONDITION 7 (NO_ANSWER)**, including
  **`ch13_fortree_door.ss1`** — ⛔ **but passing 7 is NOT "qualifying": that save FAILS condition 9
  and is unusable as the fixture (see above)** — verified live with `tools/story-dev/probe_credible_answer.py`
  (NEW), which drives production's own type chart and `_battler_slots()`.
  ‼ **The discriminator is the GATE ORDER, not the score:** those 9 saves hold moves scoring
  **97.5** (Loudred/Stomp) and **90.0** (Mightyena/Bite) — both above 75 — that never count,
  because `eff` is 1.0 and the `eff < 2.0` branch `continue`s first. A check written as
  "score >= 75" alone would call every one of them HAS_ANSWER and be confidently wrong.
- **Related:** **KI-23** (explicitly NOT closed; its own watch-item is the mirror of this),
  **KI-31** (the fodder rule as a pure function), and the `xp_rate`-vs-`legacy` `FODDER_RULE` flag,
  whose repro `repro_fodder_grass.py` *"still has not been run, on any machine"* — a separate,
  already-tracked axis that must not be conflated with this one.

## KI-65 — ARCHIVED VERBATIM from `05-KNOWN-ISSUES.md` on 2026-08-18

> Moved under the R3 line-budget relief valve (`05` hit its 3,000-line limit during the deep
> sanity check). ⛔ KI-65 ITSELF IS CLOSED — reproduced, fixed, A/B-proven, gated (#25) and
> PROMOTED to both forks 2026-08-16. ‼ BUT IT LEFT A NAMED RESIDUAL, kept visible by the stub
> in `05`: a *legitimately bound but WRONG* `party_index` (`slot_id = -1` -> the LAST party
> member) flows past both new guards. That is a wrong-mon, not an exception.

## KI-65 — ✅✅✅ **CLOSED 2026-08-16: REPRODUCED, FIXED, A/B-PROVEN, GATED (#25) AND PROMOTED TO BOTH FORKS (user-approved) — ⚠ WITH ONE NAMED RESIDUAL THIS FIX DOES NOT ADDRESS: a *legitimately bound but WRONG* `party_index` (`slot_id = -1` → the LAST party member) flows past both new guards. See "RESIDUAL LEFT OPEN BY THIS FIX" below.** Was: the HM-refusal re-pick raises `UnboundLocalError` into a silent `except` **WHEN `_read_offered_move` HAS ALREADY FAILED**, so two invisible failures compound into a silent decline (filed 2026-08-12, code-verified)

> ⛔ **STATUS IN ONE LINE:** the bug is FIXED in `sandbox-pokebot` and guarded by gate #25
> (`repro_ki65_unbound_party_index.py`). ✅ **PROMOTED 2026-08-16, USER-APPROVED — drift was 0 at that point. ✅ **AND IT WAS ZERO AGAIN as of 2026-08-17** *(✅ and it is **0 today** — the five remaining sandbox-only files were promoted 2026-08-17; this KI was already promoted. MEASURE with `promote.py --check`; a same-day past tense reads as today's figure, which is why this caveat matches KI-66's.)* — the KI-66 `_on_field` fix was PROMOTED the same day (user-approved). *(This clause briefly read "NOT ZERO … a ruling is owed", which was true for about an hour and then was not; it is the reason rule 8 below exists. MEASURE with `promote.py --check`.)*** The KI-65 fix is in BOTH forks, proven by a THREE-POINT A/B against `--build custom`: BEFORE `fault_fired=159, lie_msg=1` → `ACCEPTANCE: FAIL`; AFTER `fault_fired=87, lie_msg=0, honest_msg=1` → `ACCEPTANCE: PASS`; and `--build sandbox` still PASS. Restore point `restore/2026-08-16-pre-promotion-ki65`. ‼ Everything below the "RECON" heading is the
> PRE-FIX investigation, kept because three of its load-bearing claims were WRONG and a future
> session must not re-derive them. **Read the FIX block immediately below first.**

### ✅✅ THE FIX, AND WHAT IT COST TO GET THERE (2026-08-16)

**REPRODUCED FIRST, as this entry's own rule demanded.** `repro_ki65_unbound_party_index.py`
drives the REAL bot from `saves/route116team.ss1` with an INJECTED learner —
**MARSHTOMP L30 (1 exp short of L31), slots `0 = Rock Smash (HM06)`, 1 = Water Gun, 2 = Mud Shot,
3 = Bide** — and levels it naturally in a wild battle. **ARM A** rebinds `bmr._read_offered_move`
to raise (`:371` calls it by bare name, so the module global is the seam; no production edit).

**Measured, pre-fix (ARM A, fault fired 159x):**
`f2663: The game refused that slot (HM). Nothing else can be given up — declining the new move.`
— printed **while Water Gun, Mud Shot AND Bide were all forgettable. The message is a PROVABLE LIE**,
and it is the full four-step chain: read fails → `party_index` unbound → veto at `:397` raises into
`pass` → slot 0 (the HM) confirmed → game refuses → `:280` raises → `:291` sets 4 → `:297` lies.
**ARM B** (no fault) printed no lie and correctly replaced a non-HM slot.

**THE FIX IS TWO OF THE THREE PARTS THIS ENTRY SPECIFIED. ‼ THE THIRD WAS BUILT, MEASURED, AND
REMOVED — see the note under (3):**
1. `party_index: int | None = None` declared beside `last_confirmed_slot` — turns "unbound" into a
   value that can be **TESTED** instead of a crash that gets swallowed.
2. Explicit `if party_index is None:` guards at BOTH `:280` and `:397`, each setting a message that
   says what it could not do. ‼ **The veto now FAILS CLOSED** (declines) rather than confirming an
   unverifiable slot — see `06-DECISIONS-LOG.md`, 2026-08-16, for why that is the right trade.
3. ⛔ **AN `offer_read_failed` LATCH IN THE `:377` HANDLER — BUILT, THEN REMOVED AS REDUNDANT.**
   This entry predicted *"without (3) the ping-pong survives the fix"*, and an adversarial review
   of the diff refused to take that on trust. **The isolated A/B settled it: with the latch
   reverted and ONLY the `is None` guards kept, the gate passes IDENTICALLY**
   (`fault_fired=87, lie_msg=0, honest_msg=1`). Reason: the veto runs in the SAME iteration as the
   `except`, so whenever the handler re-arms `move_to_forget = 0`, the veto's `is None` guard forces
   it back to `4` **before any button is pressed**. ‼ **So part (2) is what prevents the loop — a
   comment at `:397` now says so, because a maintainer who believed the latch covered it might
   "simplify" away the guard that is actually load-bearing.**

**PROVEN BY A/B, both directions:** after the fix ARM A goes `lie_msg=1, honest_msg=0` →
`lie_msg=0, honest_msg=1`, still `RESOLVED`, still no derail; **ARM B is unchanged in both runs**
(`moveset_changed=1`, no lie) — that invariance is what shows the fix did not cost normal operation.
**FAULT-TESTED:** reverting the file to `HEAD` made the gate FAIL on exactly the two checks that
matter, and ARM B stayed green.

### ⛔⛔ THREE THINGS THE RECON BELOW GOT WRONG — MEASURED, DO NOT RE-DERIVE THEM

The RECON block prescribed `saves/movelearn_hmwedge_quickattack.ss1`. **That fixture cannot test
this bug at all**, for three independent reasons:
1. **`:280` IS UNREACHABLE THERE.** With `party_index` unbound, enumerate every assignment of
   `move_to_forget`: `:176` (4), `:285-289` (needs `party_index`, raises first), `:291` (4), `:373`
   (unreachable, `:371` raised), `:381` (0), `:432` (dead, `:397` raised first). **Only 0 and 4 are
   reachable.** That save's slot 0 is Scratch, not an HM, so the game ACCEPTS it and `CantForgetHM`
   never re-fires. ⇒ **`:280` requires a fixture whose SLOT 0 ITSELF HOLDS AN HM** — which is why
   the repro injects one rather than using a capture.
2. **THE OUTCOME IS DECIDED BEFORE THE BUG CAN MATTER.** That save is parked INSIDE the
   `CantForgetHM` window, so branch (1) runs at f2 with the INITIAL `move_to_forget = 4`, walks the
   cursor to the cancel row and backs out at **f12**. Policy is first consulted at **f37** — 25
   frames too late. Fault-ON and fault-OFF button traces are **BYTE-IDENTICAL**:
   `f0 A, f2 Down x5, f12 A x224`.
3. **FAULTING THE "MOST PLAUSIBLE REAL CAUSE" IS RESCUED.** `_read_offered_move` has TWO paths —
   `:135-138` task-backed via `get_party_menu_cursor_pos`, and `:140-149` via `gBattleStruct` +
   `map_battle_party_index`. Only the second can raise. On that save the task-backed path succeeds,
   binds `party_index`, and a bound function-local **stays bound for the rest of the generator's
   life**, so every later raise is inert. Measured: 51 fires, zero behavioural difference.

### ✅ THE COMPLETED THREE-POINT PROMOTION A/B (promotion DONE 2026-08-16, user-approved)

⛔ **Record, do not re-derive.** The BEFORE arm was captured and written down **before the copy**, because this project's rule is that run 1 *"is unrepeatable once the copy happens, so it runs and commits FIRST"* — and the gate's logs are **gitignored**, so these numbers exist only here.

**POINT 1 — BEFORE. `--build custom` (the fork WITHOUT the fix), gate `ACCEPTANCE: FAIL`:**

| arm | build | fault_fired | verdict | moveset_changed | **lie_msg** | **honest_msg** |
|---|---|---|---|---|---|---|
| A | custom | 159 | RESOLVED | 0 | **1** ⛔ | **0** |
| B | custom | 0 | RESOLVED | 1 | 0 | 0 |

⇒ **`custom-pokebot` REPRODUCED THE LIE LIVE** — it printed *"Nothing else can be given up"* with three forgettable moves in hand. That is what made the promotion worth doing.

**POINTS 2 AND 3 — AFTER the copy (2026-08-16, user-approved):**

| point | build | fault_fired | **lie_msg** | **honest_msg** | gate |
|---|---|---|---|---|---|
| 2 AFTER | custom | 87 | 0 | **1** | ✅ **ACCEPTANCE: PASS** |
| 3 control | sandbox | 87 | 0 | 1 | ✅ **ACCEPTANCE: PASS** |

‼ **`fault_fired` fell 159 → 87 on custom, to EXACTLY the sandbox figure** — independent evidence that the new branch RUNS there, which a byte-identical copy can never show. **A byte-compare is NOT proof for a behaviour promotion.** Restore point `restore/2026-08-16-pre-promotion-ki65`.
📁 Transcripts (COMMITTED, because paraphrased numbers are not proof): `tools/story-dev/evidence/2026-08-16-ki65-PROMOTION-{BEFORE,AFTER}-custom.stdout.txt` and `...-CONTROL-sandbox.stdout.txt`. ‼ The BEFORE arm was RE-RUN after the promotion by reconstructing the pre-fix file from the restore
tag (`git show restore/2026-08-16-pre-promotion-ki65:custom-pokebot/...`), so the committed transcript
is a real run and not a transcription of remembered numbers — it reproduced `fault_fired=159,
lie_msg=1, ACCEPTANCE: FAIL` exactly.

### ⚠ RESIDUAL LEFT OPEN BY THIS FIX — TRACKED HERE ON PURPOSE (do not let it orphan)

The guards test `party_index is None`, which covers **unbound**. They do **NOT** cover a
*legitimately bound but WRONG* index: `get_party_menu_cursor_pos` does not raise on a bad cursor —
it calls `set_manual_mode()` and returns **`slot_id = -1`**, and `get_party()[-1]` is the LAST party
member. That is a **wrong-mon, not an exception**, so it flows straight past both new guards exactly
as it did before. ⛔ **This fix does not claim to address it**, and it is a genuinely different shape
(silent wrong answer vs. silent crash). ‼ It is the same class as `#24-orphans` item (3) KI-66's
"index from the wrong space" hazard. Filed here rather than in a research note so a future session
can FIND it. **Not yet observed live; unquantified.**

‼ **ALSO CORRECTED:** `LevelUpTravelBattleStrategy.which_move_should_be_replaced` was measured
returning **slot 1 = Rock Smash, an HM**, for Quick Attack. The HM veto is what catches that, so the
veto is load-bearing in NORMAL operation, not just on the error path. *(An agent reported that no
strategy overrides `which_move_should_be_replaced` "anywhere in `modules/`" — true and misleading:
the override lives in `plugins/custom_modes/story_mode.py`, outside that tree.)*


> ⛔ **HEADER CORRECTED 2026-08-16 (P2).** It read *"the HM-refusal re-pick has NEVER executed"* —
> which **this entry's own CORRECTION section, written the same day it was filed, calls too strong**
> and refutes: on an ordinary teach, branch (2) binds `party_index` at `:371` BEFORE the game can
> refuse, so the re-pick DOES run. The header outlived its own retraction by four days and is the
> half a skimmer reads. ‼ *An entry that corrects itself in the body must correct its TITLE in the
> same edit.*

Found by running **pyflakes** over the build for the first time (see `14-AGENT-PLAYBOOK.md`).

`modules/battle_move_replacing.py:280`, inside `handle_move_replacement_dialogue`:
```python
if state == LearnMoveState.CantForgetHM:
    ...
    try:
        _mv = get_party()[party_index].moves      # <-- party_index
        ...  # re-pick a slot the game has NOT refused
    except Exception:
        move_to_forget = 4                        # decline
```
`party_index` is a **function-local assigned only at line 371** (`move_to_learn, party_index =
_read_offered_move(...)`), far below this branch. If `CantForgetHM` is reached before that
assignment has run in this generator's life, line 280 raises **`UnboundLocalError`** — which the
surrounding `except Exception` converts into `move_to_forget = 4`, i.e. **decline**.

**Why this is bad rather than merely untidy.** Declining is a *legal* outcome, so the failure is
invisible: the run looks like it made a decision. The whole point of that block — its own comment
says *"Without the second [learning from the refusal], dismissing just returns to the move list with
the same doomed pick and the loop is infinite"* — is the re-pick, and the re-pick is exactly what
never happens. This is the playbook's named pattern **"a fail-safe `except` that returns the SUCCESS
value"**, and the guard is not protecting anything.

‼ **Candidate cause for the REOPENED `#24-teachmsgstall`**, which is currently characterised as
*"there is another path to `post_select=exhausted`"*. This is a path to a silent decline in the
teach flow. **Not yet fixed and not yet proven to be that path** — it needs its own repro (force
`CantForgetHM` and assert the re-pick runs) and an A/B, which is the honest next step rather than
assuming the connection.

### ‼‼ RECON 2026-08-16 — THE ENTRY WAS RIGHT BUT INCOMPLETE ON TWO COUNTS. Read this before fixing.

⛔ **(A) AND (B) — THE PRE-FIX ANALYSIS OF THE TWO UNBOUND READS AND THE PING-PONG CHAIN: MOVED to
`31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-16), because KI-65 is CLOSED AND PROMOTED and the FIX block at
the top of this entry supersedes both.** ‼ **Keep only the two facts later work leans on:** there are
**TWO** unbound reads (`:280` the re-pick, `:397` the HM veto — the veto is the damaging one, because
its `except Exception: pass` is indistinguishable from "the slot is not an HM"); and the chain that
makes them compound is a FOUR-STEP CONJUNCTION in which the failed read *causes* the later steps.
⚠ (B) also predicted the latch as the loop-preventer — **MEASURED WRONG**; see the FIX block.

✅ **THE FAULT-INJECTION SEAM: MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-16)** — superseded by
the built gate, whose docstring documents the seam it actually uses (`bmr._read_offered_move`,
rebindable because `:371` calls it by BARE NAME, so no production edit is needed).

⛔ **DANGERS a naive edit walks into — FULL LIST MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-16).**
‼ **Keep the two that still bite anyone touching this function:** (1) **`move_to_forget = 4` is
OVERLOADED** — "decline" to branch (2) but a CURSOR ROW to branch (1), which has NO `try`, so a
`None` sentinel leaking in raises `TypeError` into nothing at all; (2) **`get_party_menu_cursor_pos`
does NOT raise on a bad cursor** — it calls `set_manual_mode()` and returns `slot_id = -1`, and
`get_party()[-1]` is the LAST party member, i.e. a WRONG MON rather than an exception. *(That second
one is the residual this fix does not close — see the RESIDUAL block above.)*

✅✅ **THE PRE-FIX FIX-SPECIFICATION ("in three parts"): MOVED to `31-KNOWN-ISSUES-ARCHIVE.md`
(2026-08-16).** Superseded by the FIX block at the top of this entry, which records what ACTUALLY
shipped: **two** parts, because the third was built, measured redundant, and removed.
‼ **Keep only this:** the spec's own part (3) is a worked example of a plausible mechanism claim
that survived review until someone ran the arm without it.

**Severity:** MEDIUM, order-dependent (on iterations where line 371 already ran, the name is bound
and the branch works), which is also why it has survived unnoticed.

## ‼ KI-65's 2026-08-12 SELF-CORRECTION — MOVED to `31-KNOWN-ISSUES-ARCHIVE.md` (2026-08-16)

Moved on the R3 3,000-line budget when the KI-65 FIX block was written. KI-65 is CLOSED (sandbox);
that section was the *pre-fix* narrowing of the original filing and is fully superseded by the FIX
block above. ‼ **Keep only its rule, which outlived it:** *an entry that corrects itself in the BODY
must correct its TITLE in the same edit* — that header outlived its own retraction by four days.

