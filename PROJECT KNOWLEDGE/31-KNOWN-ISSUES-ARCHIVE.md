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

