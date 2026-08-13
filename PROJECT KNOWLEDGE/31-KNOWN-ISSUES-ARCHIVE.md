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

