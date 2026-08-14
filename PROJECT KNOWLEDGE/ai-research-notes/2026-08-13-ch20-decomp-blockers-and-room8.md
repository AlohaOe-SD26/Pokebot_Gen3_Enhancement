# §Ch20 — the decomp blockers, and the Room 8 adjudication (2026-08-13)

> ‼ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. Produced by Claude subagents
> reading `pret/pokeemerald` live and decoding `map.bin` layouts, plus our own ROM reader. **Nothing
> below was run on a live emulator except where it says MEASURED LIVE.**
>
> **One claim in here was already promoted to fact by a live drive on the day it was written** —
> Blocker 1 — and one was already used to *correct our own shipped source comment*. Two others
> (Blockers 2 and 3) would strand or stall a run and are **not yet tested**. Treat the untested
> ones as the highest-value work items, not as background reading.

---

## THE FOUR LIVE-DRIVE BLOCKERS

### ✅ Blocker 1 — `FLAG_SYS_USE_STRENGTH` does NOT persist across maps. **CONFIRMED, MEASURED LIVE.**

Our build spec **and our own `modules/story/early_game.py`** said the flag is *"NEVER CLEARED …
switched on ONCE PER SAVE, not once per map"*. **False.** `ClearTempFieldEventData()`
(`src/event_data.c:39-48`) calls `FlagClear(FLAG_SYS_USE_STRENGTH)`, and it is invoked from
`LoadMapFromWarp` (`src/overworld.c:848`) — i.e. **on every warp** — plus on Fly / Teleport / Dig /
white-out (`overworld.c:374,384,395,405`). The push is hard-gated on it
(`src/field_player_avatar.c:754`).

**MEASURED LIVE 2026-08-13** by `--driver ch20room2`: the flag read **`False`** immediately after
warping `SEAFLOOR_CAVERN_ROOM1 → ROOM2`, having just been activated in Room 1.
**Corroboration:** upstream re-arms Strength in *every* room (`puzzle_solver.py:373, 399, 429, 440`).

✅ **Our CODE was always safe** — `strength_push` re-checks and re-activates per call. Both wrong
comments are now corrected in place. ⛔ **The danger was never a crash; it was a future author
deleting the re-check as redundant.** Then every room after the first walks into its boulder, takes
a plain wall collision, and retries with no message and no error.

### ✅ Blocker 2 — the Route 128 landing is an ATOLL. **CONFIRMED IN OUR OWN ROM 2026-08-13 — 9/9 checks — but its FRAMING needed correcting.**

> **`tools/story-dev/probe_route128_landing.py` (NEW)** re-measured this through
> `modules.map.get_map_all_tiles` — the same reader the chapter will use — **sharing no code with
> the agent's `map.bin` decode.** Byte-for-byte agreement on every number below (71 / 41 / 1766).
>
> ```
> CONFIRMED  landing is shallow/standable            (38,22) coll=0 elev=3 'Shallow Water'
> CONFIRMED  on-foot component does NOT reach the map edge          size=71
> CONFIRMED  north water and south water are DIFFERENT components
> CONFIRMED  south water reaches the map edge (open ocean)          size=1766
> CONFIRMED  north water does NOT reach the map edge (closed lagoon) size=41
> CONFIRMED  at least one surf launch point onto the OPEN ocean exists          46 of them
> CONFIRMED  the recommended escape (38,23)/Down/(38,24) is one of them
> CONFIRMED  the landing tile itself CANNOT surf (all four neighbours are shallow)
> CONFIRMED  a TRAP exists — the closed lagoon is surfable-into from the sandbar   28 launches
> ```
>
> ⛔ **THE FRAMING BELOW IS CORRECTED: "surf north and you strand" IS TOO CRUDE and would have
> produced a wrong guard.** The sandbar is a **71-tile atoll that wraps around**, so **33 launch
> points NORTH of the landing DO reach the open ocean**. The hazard is not a compass direction — it
> is the **28 launches into the closed lagoon**, which sit on the atoll's **WESTERN** shore
> (`x = 33-35`), nowhere near due north of the landing.
> ⇒ **The actionable rule is unchanged and now measured: step SOUTH to `(38,23)`, face Down, Surf
> onto `(38,24)` — one step, confirmed a real launch.** ‼ And note the landing tile itself has
> **zero** surfable neighbours, so a naive "Surf from where you land" does nothing at all in any
> direction — it will look like a hung leg, not like a failure.
> ⚠ **Still a decomp claim, not measured:** that the cutscene releases the player *facing north*.
> The map is now proven; the facing wants a live check when the chapter is driven.
>
> *(original claim, kept for provenance)*

Leg 11's landing tile `ROUTE128 (38,22)` after the Kyogre cutscene, from a direct decode of
`data/layouts/Route128/map.bin` (120x40):

```
(38,22)  MB_SHALLOW_WATER coll=0 elev=3      all four neighbours also MB_SHALLOW_WATER
on-foot component from (38,22):   71 tiles, does NOT touch the map edge
water component NORTH (38,20):    41 tiles, does NOT reach the map edge   <-- CLOSED LAGOON
water component SOUTH (38,24):  1766 tiles, reaches the map edge          <-- OPEN OCEAN
same component? False
```

* The player is **released facing NORTH** — the last player `applymovement` in
  `Route128_EventScript_KyogreAwakenedScene` is `Common_Movement_WalkInPlaceFasterUp`
  (`data/maps/Route128/scripts.inc:61`).
* `Route128/map.json:11` is `"allow_escaping": false` — **no Escape Rope out.**
* The bot **cannot Surf from the landing tile at all**: every neighbour is `MB_SHALLOW_WATER`, which
  is absent from the surfable list (`src/metatile_behavior.c:1162-1176`), so
  `IsPlayerFacingSurfableFishableWater` never fires.

⇒ **Correct move: step SOUTH to `(38,23)`, face south, Surf onto `(38,24)`.** Surfing the direction
the game leaves you facing drops the bot into a 41-tile dead-end pond it cannot escape.
‼ **Three chapters have shipped stranded. This one is designed to strand you, and the trap points
the way the camera does.**

### ⚠ Blocker 3 — Rock Smash prompts YES/NO **every** time and can start a wild battle. **UNTESTED here** (but our `_smash_rock` is separately proven on Route 111).

`data/scripts/field_move_scripts.inc:61-76`: `EventScript_RockSmash` has **no flag gate** — it
`msgbox Text_WantToSmash, MSGBOX_YESNO` on every smash — and `EventScript_SmashRock` (`:86-97`) ends
with `special RockSmashWildEncounter`, which can drop straight into a battle.
Also: `MAP_SEAFLOOR_CAVERN_ROOM6` and `ROOM7` have full **`water_mons`** tables — and those are
exactly the two rooms the bot **surfs** through. The build spec said encounters were "on land in
Rooms 1-8" and that the only YES/NO prompt in the chapter is the first Strength boulder; **both
halves are wrong.** Upstream runs `use_repel = True` for the whole dungeon
(`puzzle_solver.py:358`); our spec has no Repel leg.

### ⚠ Blocker 4 — the pre-flight assertion is incomplete. **UNTESTED, cheap to fix.**

The spec's leg 0 asserts Surf, Strength, Rock Smash and `FLAG_BADGE04_GET`. **Four badges gate the
moves used, and Dive is missing entirely:**

| move | gate | citation |
|---|---|---|
| Rock Smash | `FLAG_BADGE03_GET` | `data/scripts/field_move_scripts.inc:63` |
| Strength | `FLAG_BADGE04_GET` | `data/scripts/field_move_scripts.inc:126` |
| Surf | `FLAG_BADGE05_GET` | `src/field_control_avatar.c:450` |
| **Dive** | **`FLAG_BADGE07_GET`** | `src/field_control_avatar.c:465` |

Dive is the only entrance (`Underwater_SeafloorCavern/scripts.inc:35-37`).

---

## OTHER CORRECTIONS TO THE BUILD SPEC

* **"Room 3 is a walk (+2 unavoidable trainers)" — REFUTED as a pair.** The push-free
  `(4,15) → (8,1)` line is 18 steps but **unavoidably** crosses `{(6,5),(7,5),(8,5)}`, the union of
  both trainer cones. With Strength through Room 3's **7-boulder puzzle — which the spec omits
  entirely** — there is a **zero-sight route** (two independent searches: 26 steps step-optimal, 28
  steps / 5 pushes push-optimal — same conclusion, different objective). Upstream takes the stealth
  route (`puzzle_solver.py:427-436`).
* **"Room 7 costs one extra Rock Smash `(9,3)` + 2 pushes of `(10,3)`" — MISFILED.**
  `SeafloorCavern_Room7/map.json` has `"object_events": []`. Those coordinates are **Room 2**
  objects. The arithmetic is right (Room 7 costs +1 smash and +2 pushes over Room 6, i.e. 5 pushes
  vs 3); only the room label was wrong.
* **Six cavern transitions are `MB_SOUTH_ARROW_WARP`, not step-on warps** — R1 `(5,18)`, R1
  `(17,13)`, **R2 `(10,7)`**, R2 `(4,10)`, R8 `(5,12)`, **R9 `(5,4)`**. `TryArrowWarp`
  (`src/field_control_avatar.c:688-700`) fires only while the direction is **HELD**
  (`:164-168`) — so **pathing onto R9 `(5,4)` does not leave Room 9**, and conversely an accidental
  step onto an arrival tile will *not* bounce the bot back. Our planner does model this
  (`map_path.py:391-399`, `extra_warp_direction`). ✅ Confirmed live: `ch20room2` arrived on R2
  `(10,7)` and R6 `(11,21)`, both `'South Arrow Warp'`, and neither warped on arrival.
* **`TryPushBoulder`'s destination guard excludes only `MetatileBehavior_IsNonAnimDoor`** — so
  **arrow-warp tiles are unguarded and a boulder can be parked on one.** Reachable in **Room 3 at
  `(9,13)`** (the Room-7 retreat warp) and in **Room 2 at `(10,7)` and `(4,10)`**. ✅ **The main
  Kyogre path touches none of them** (Room 2's route ends with the boulder at `(4,2)`), and Room 8
  was **refuted** as a hazard by a full 3,117,316-state enumeration. ⚠ Room 3's search hit a 4M-state
  cap, so its clean result is a lower bound, not a proof.
* **Currents cannot trap the bot** (terrain side). `DoForcedMovement` (`src/field_player_avatar.c:443`)
  returns `FALSE` on collision and `PlayerStep` falls through to
  `MovePlayerAvatarUsingKeypadInput` — a current that shoves you into a wall **returns control on
  that tile the same frame**. Swept over all 108 Room-6 and 117 Room-7 current tiles: **zero
  infinite loops**. ⚠ Whether *our* `forced_movement_to` matches is still unmeasured (KI-76).
* Minor: the spec's swipe at upstream "stopping one tile short" at `(16,42)` misreads it — upstream
  stops there **deliberately** before `set_manual_mode()`, and the coordinate's origin is
  `Room9/scripts.inc:38`, `dofieldeffectsparkle 16, 42, 0`.
* Confirmed clean, for the record: Room 6 one-way with a `(4,1)→(14,8)` retreat; Room 7 two-way;
  current counts 108 / 117 exact; Room 9 walk `(5,4) → (17,42)` is exactly 62 steps on land;
  `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` = 14 hits, **1 `setflag`, 0 `clearflag`**.

---

## ROOM 8 — ADJUDICATED. **Both sources work; ours is the better one.**

Twelve `PUSHABLE_BOULDER` objects (`FLAG_TEMP_11`…`FLAG_TEMP_1C`), **zero trainers, zero
coord/bg events, empty map-script header, no `setmetatile`**. Map is **11x14**. Warps: `(5,2)` →
Room 9, `(5,12)` → Room 3 (two-way; arrival from Room 3 `(8,1)` is `(5,12)` — **CONFIRMED**).

* ✅ **The `MB_JUMP_SOUTH` ledge at `(4,10) (5,10) (6,10)` is CONFIRMED** from our own ROM
  (`coll=1 elev=0 'Jump South'`), and so is the workaround: **go north via x=3 or x=7.**
* **Upstream reaches `(5,2)` in 10 pushes; our spec's 9-push line also reaches it and is shorter**,
  needing only two repositioning walks. ⇒ **Contrary to the Room 1 precedent, the spec's Room 8 line
  survives audit.** Its "22 steps / no single removal suffices" optimality claim remains
  **UNVERIFIABLE** — and per the Room 1 ruling, optimality claims from this document are graded at
  zero regardless.

### ‼ THE ENGINE RULE BOTH SEQUENCES SILENTLY DEPEND ON

`PushBoulder_Move` (`src/field_player_avatar.c:1498`) gives the **player** a
`WalkInPlace` movement and the **boulder** a `WalkSlow`. **The push does not move the player.** The
player only lands on the vacated tile because `walk_one_tile`
(`modules/modes/util/walking.py:537`) **holds the button** until the coordinates change, so once
`PushBoulder_End` clears `preventStep` the still-held press produces a second, real step.
⇒ net rule: **boulder +1, player +1** — but *only* because of how our own walker behaves.
**A/B that proves this is load-bearing:** replaying upstream under the alternative model
("boulder moves, player stays") dies at step 5 with `navigate_to((4,5)) → NO PATH from (7,7)`.

⛔ **And the corollary is a hazard:** a REFUSED push (destination solid / occupied / elevation
mismatch / Non-Anim Door — `TryPushBoulder`, `field_player_avatar.c:752`) makes `walk_one_tile`
**hang forever**, by its own docstring. Upstream's eleven blind `walk_one_tile` calls are unbounded.
⇒ **This is why our drivers push through `strength_push`** — bounded, and it verifies the boulder by
`local_id` on the destination.

### HAZARDS SPECIFIC TO ROOM 8

1. ⛔ **`(5,3)` is a hard-jam tile.** It is the only tile connecting the room to the `(5,2)` warp. A
   boulder pushed north from `(5,4)` lands there and can then only be shoved sideways — which needs
   the player on `(4,3)` or `(6,3)`, and **both sequences end with boulders on exactly those tiles.**
   Both sources dodge this correctly (upstream pushes east, ours west) **but neither says why**, so a
   future "simplification" could reintroduce it. ‼ **Step 9 must face LEFT, never UP.**
2. ⛔ **Boulders `(3,4)` and `(7,4)` can NEVER be pushed north** (`(3,3)`/`(7,3)` are `collision=1`),
   nor `(4,3)→(4,2)` or `(6,3)→(6,2)`, nor `(5,3)→(5,2)` (Non-Anim Door, explicitly refused).
   Every one of those is a refused push ⇒ an unbounded `walk_one_tile` loop.
3. **Wild encounters exist** (`gSeafloorCavern_Room8`, rate 4, Zubat L28-35). A battle mid-sequence
   is safe for boulder state (`SpawnObjectEventsOnReturnToField` restores objects at their *current*
   coords) but will interrupt a blind walk chain.
4. ✅ **A jam is RECOVERABLE and that is the right failure handler.** `(5,12)` ↔ Room 3 `(8,1)` is
   two-way and all twelve boulders respawn from the map header on re-entry, while Room 3's trainers
   stay defeated. ⇒ **on any assertion failure, exit to Room 3 and re-enter — never improvise near
   `(5,3)`.**
5. ✅ **KI-77 is REFUTED for Room 8** — the despawn window is 20x17 and the map is 11x14, so only
   `y=12` (the arrival tile, before any push) despawns anything. See KI-77's corrected entry.

### RECOMMENDED ROOM 8 SEQUENCE (9 pushes, every push preceded by a state-derived navigate)

| # | stand | face | action | boulder | player after |
|---|---|---|---|---|---|
| 0 | — | — | `navigate_to (5,8)` from `(5,12)` | — | crosses row 10 at **x=3** |
| 1 | `(5,8)` | Up | push | `(5,7)→(5,6)` | `(5,7)` |
| 2 | `(5,7)` | Left | push | `(4,7)→(3,7)` | `(4,7)` |
| 3 | `(4,6)` | Right | navigate, then push | `(5,6)→(6,6)` | `(5,6)` |
| 4 | `(5,6)` | Up | push | `(5,5)→(5,4)` | `(5,5)` |
| 5 | `(5,5)` | Left | push | `(4,5)→(3,5)` | `(4,5)` |
| 6 | `(4,5)` | Up | push | `(4,4)→(4,3)` | `(4,4)` |
| 7 | `(5,5)` | Right | navigate, then push | `(6,5)→(7,5)` | `(6,5)` |
| 8 | `(6,5)` | Up | push | `(6,4)→(6,3)` | `(6,4)` |
| 9 | `(6,4)` | **Left** ‼ never Up | push | `(5,4)→(4,4)` | `(5,4)` |
| 10 | — | — | `navigate_to (5,2)` | — | warp → `SEAFLOOR_CAVERN_ROOM9` |
