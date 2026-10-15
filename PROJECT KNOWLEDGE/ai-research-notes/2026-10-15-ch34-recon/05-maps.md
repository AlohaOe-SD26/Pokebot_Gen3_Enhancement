# 05 — Static map facts for chapters 3–4 (Route 104, Petalburg Woods, Rustboro City, Rustboro Gym)

> ⚠ **This is a RESEARCH NOTE, not a source of truth** (`ai-research-notes/00-READ-THIS-FIRST.md`). On any
> contradiction the authoritative docs win until a claim is verified in our harness.
>
> ⛔ **FOR DEVELOPERS ONLY (proof design and expectations).** Under USER RULINGS 35–37 the AI player is
> person-fair: it may use only what is on screen, plus hints at the level the game's DIALOGUE or SIGNS give.
> **No coordinate, route, choke point, sight line or hidden-item location in this file may be given to the AI
> as a hint.** Section 7 lists the few facts the game itself tells a player, which the AI may legitimately read.

Written 2026-10-15 by a read-only Claude research agent (angle: static map facts). Nothing outside this file was
written. No emulator was started.

## Evidence grades used below

- **VERIFIED**: read directly in the pokeemerald decomp (`gh api repos/pret/pokeemerald/contents/...`,
  master branch, fetched 2026-10-15) or in our own code. A citation is given.
- **DERIVED**: computed by my static script from decomp data (`map.json`, `layouts.json`, `map.bin`,
  `metatile_attributes.bin`), using movement and sight rules I read in the cited C code. It is exact for
  per-tile facts (behaviour, collision, elevation) and approximate for reachability and sight lines; the
  approximations are listed in §8. **Treat it as UNVERIFIED for anything code will depend on** until a
  live probe confirms it.
- **UNVERIFIED**: inference or recall, flagged where used.

Why decomp-direct and not `tools/story-dev/mapfacts.py` / `maprecon.py`: those tools need a `LibmgbaEmulator`
built from a `sandbox-pokebot` profile (and `maprecon.py` loads a save state). A full regression was running in
this checkout, and this task was read-only, so I read the same ROM data from the decomp instead. The facts below
are the authored map, which is exactly what `get_map_data((g, n), (0, 0))` reports (playbook §3 item 5).

---

## 0. Headline findings (the ones that change how a proof should be designed)

1. **Route 104 is ONE ROM map, `MAP_ROUTE104` = (0,19), 40×80.** There are no separate "north" and "south" maps.
   The halves are cut apart by a solid impassable band (rows y=31..37, every tile has collision). **The only
   on-foot link between the halves is through Petalburg Woods.** VERIFIED for the map id: decomp
   `data/maps/map_groups.json` (`gMapGroup_TownsAndRoutes` index 19) and our `sandbox-pokebot/modules/map_data.py:813`.
   The band is DERIVED from `map.bin`.
   - Trap: `MAP_ROUTE104_PROTOTYPE` = (27,0) and `MAP_ROUTE104_PROTOTYPE_PRETTY_PETAL_FLOWER_SHOP` = (27,1) also exist
     (`map_data.py:1344-1345`). `LAYOUT_ROUTE104_PROTOTYPE` is 1×1 (`layouts.json`). They are unused leftovers, and
     a name match on `ROUTE104*` will pick them up.
2. **Petalburg Woods has THREE exits, not two:** north `(14,5)/(15,5)`, south-west `(16,38)/(17,38)` and
   **south-east `(36,38)/(37,38)`**. The south-east exit lands in a ledge-locked pocket of Route 104 at
   `(32,42)/(33,42)`. That pocket can only be LEFT (down ledges), never entered from Route 104. VERIFIED warps
   (`PetalburgWoods/map.json` `warp_events`, `Route104/map.json` `warp_events` 6-7). The one-way property is DERIVED.
3. **The Aqua-grunt and researcher scene is FORCED on the first northbound crossing, but it does NOT start at the
   Woods entrance.** It is a coord trigger on `(26,23)` and `(27,23)` (gated on `VAR_PETALBURG_WOODS_STATE == 0`),
   which is 15 rows north of the south doors (y=38). The two tiles span the whole width of a 2-tile-wide corridor
   (x=26..27, y=16..27), the only northbound link from the middle of the Woods to the upper half. VERIFIED trigger
   (`PetalburgWoods/map.json` `coord_events`). The choke is DERIVED: with those two tiles removed, the north exit
   becomes unreachable from either south door.
   - Note for `ai_player/knowledge/milestones.json` (ch3_woods, `taught_by` → `early_game.py:1684`
     "begins just inside the Woods south entrance"): that is the BOT's segment start, not where the scene fires.
     A proof that expects the scene on entry will fail.
4. **Gina & Mia (the Route 104 twins, a DOUBLE battle) stand on the only bridge north to Rustboro.** Sight range 1,
   facing down, at `(27,15)` and `(28,15)`, so the tiles `(27,16)` and `(28,16)` are forced. **But they do not
   trigger at all unless the player has two usable Pokémon**: `trainer_see.c:279-285`, `CheckTrainer` returns 0 for
   a `trainerbattle_double` script when `GetMonsStateToDoubles_2() != PLAYER_HAS_TWO_USABLE_MONS`. So the same walk
   gives a battle with a 2-Pokémon party and no battle with a 1-Pokémon party. The choke is DERIVED. The gating
   is VERIFIED.
5. **Rustboro Gym, tile `(1,9)`, a two-trainer trap.** It is seen by BOTH Tommy (facing west, range 3) and Marc
   (facing south, range 3). The game collects up to two spotting trainers per frame when the player has two usable
   Pokémon (`trainer_see.c:191-245`, especially 203-220), so stepping on `(1,9)` with two or more usable Pokémon
   should start a **two-trainer double battle** (Tommy + Marc). With one usable Pokémon it is a single battle with
   whichever trainer is checked first. **The shortest entrance-to-Roxanne path passes `(1,9)`.** DERIVED from
   verified code plus verified object positions. **Not live-tested. Probe this before any gym proof relies on
   "3 single battles".**
6. **Every trainer sight check runs EVERY overworld frame, not only after a step.** It is called from
   `ProcessPlayerFieldInput` (`field_control_avatar.c:147`), which `DoCB1_Overworld` calls on every frame where
   controls are unlocked (`overworld.c:1438-1457`). It uses the player's destination tile. So a ROTATING trainer
   (Winston, Lyle, James) can spot a player who is standing still when it turns to face them. "Stop and wait"
   is not safe inside a rotating trainer's line.
7. **Cut gates in these maps (none needed for the story):**
   - **Petalburg Woods:** the north-east half, from about x=24..45, y=4..31, is behind the two cut trees `(19,10)` and
     `(19,11)`. Behind them are the **Great Ball `(45,7)`**, the **X Attack `(35,20)`**, the **MIRACLE SEED girl
     `(33,5)`** and both hidden **Tiny Mushrooms** `(26,6)` and `(40,29)`. That region drains south by one-way ledges.
   - **Route 104 north:** the **X Accuracy `(37,22)`** is behind the cut tree `(35,22)`.
   - DERIVED (cut trees treated as solid). That cut trees are objects with `FLAG_TEMP_11` / `FLAG_TEMP_12` is VERIFIED
     (`map.json`).
8. **Item balls that are NOT reachable on foot in ch3–4:** Route 104 **PP Up `(39,15)`**, on an islet in the pond,
   needs Surf. The X Accuracy and the Woods items above need Cut. **Route 104 Poké Ball `(29,53)`** is reachable
   ONLY by leaving the Woods through the south-east exit. **Rustboro X Defend `(36,51)`** is reachable ONLY from
   Route 104's north strip by walking north at **x=33** into a Rustboro pocket that is not connected to the city
   streets. All DERIVED.
9. **After the badge, the Devon-goods theft scene is forced on leaving the gym plaza.** Defeating Roxanne sets
   `VAR_RUSTBORO_CITY_STATE = 1` (`RustboroCity_Gym/scripts.inc:20`). The coord triggers `(23,20..24)`
   (`StolenGoodsTrigger0..4`, gated on state 1) cover the plaza's only exit column. Heading to the PC, the south
   exit or Route 116 all cross it. VERIFIED triggers; DERIVED choke. **The end-of-ch4 proof must expect this scene**
   if the AI walks anywhere after the badge.
10. **No layout swaps on these four maps.** A grep of all four `scripts.inc` files finds no `setmaplayoutindex` and
    no `setmetatile`. The static-vs-live differences are all OBJECT-level (hide flags, `setobjectxyperm`, berry state;
    see §6). VERIFIED by grep.

---

## 1. Identity, size, connections and seams

| Map | (group, num) | Size | Tilesets | Type / weather | Connections (decomp `map.json`) |
|---|---|---|---|---|---|
| `MAP_ROUTE104` | (0,19) | 40×80 | General + Rustboro | ROUTE, SUNNY, running/cycling OK | up → RUSTBORO_CITY off 0; down → ROUTE105 off 0; right → PETALBURG_CITY off 50 |
| `MAP_PETALBURG_WOODS` | (24,11) | 48×44 | General + Rustboro | ROUTE, **SHADE** (darker screen), running/cycling OK | none (warps only) |
| `MAP_RUSTBORO_CITY` | (0,3) | 40×60 | General + Rustboro | CITY, SUNNY | up → ROUTE115 off 0; down → ROUTE104 off 0; right → ROUTE116 off 0 |
| `MAP_RUSTBORO_CITY_GYM` | (11,3) | 11×20 | Building + RustboroGym | INDOOR, no running, no cycling, `MAP_BATTLE_SCENE_GYM` | none |

VERIFIED: ids from `map_groups.json` and `map_data.py:797,813,952,1091`; sizes and tilesets from
`data/layouts/layouts.json`; the other columns from each `map.json`.

**Walkable seams** (where the screen scrolls into the next map with no warp). DERIVED from both maps' `map.bin`:

| From | To | Crossing tiles (source-map coords) | Notes |
|---|---|---|---|
| Route 104 east edge x=39 | Petalburg City x=0 | **y=62..63** (Petalburg y=12..13) | Route 104 (39,61) is walkable but Petalburg (0,11) is not: it bumps. |
| Route 104 top y=0 | Rustboro bottom y=59 | **x=12..19** (the main road) and **x=33** (Rustboro's isolated SE pocket, X Defend) | Route 104 y=0 is walkable at x=10..33, but Rustboro y=59 is open only at 12..19 and 33. |
| Route 104 bottom | Route 105 | none on foot; needs Surf | Route 104's bottom row y=79 is all water or wall (DERIVED). Route 105 is 40×80. |
| Rustboro top y=0 | Route 115 bottom | **x=19..23** | A wandering AI can leave north here. Not on the story path. |
| Rustboro east x=39 | Route 116 x=0 | **y=8..13** | The usual pre-gym training route (`12-STORYMODE-DESIGN.md:1191`). |

---

## 2. ROUTE 104 (0,19)

### 2a. Warps (VERIFIED `Route104/map.json` `warp_events`; behaviours DERIVED from tileset attributes)

| # | Tile | → Destination (dest warp) | Tile behaviour | How it fires |
|---|---|---|---|---|
| 0 | (17,50) | ROUTE104_MR_BRINEYS_HOUSE #0 | `MB_NON_ANIMATED_DOOR` | Step on it (`IsNonAnimDoor`, `field_control_avatar.c:751-763`). |
| 1 | (5,18) | ROUTE104_PRETTY_PETAL_FLOWER_SHOP #0 | `MB_NON_ANIMATED_DOOR` | Step on it. |
| 2,3 | (10,30),(11,30) | PETALBURG_WOODS #0/#1 (Woods (14,5)/(15,5)) | `MB_DEEP_SOUTH_WARP` | Step on it while walking south. It counts as a non-animated door (`metatile_behavior.c:262-270`). |
| 4,5 | (10,38),(11,38) | PETALBURG_WOODS #2/#3 (Woods (16,38)/(17,38)) | `MB_NON_ANIMATED_DOOR` | Step on it while walking north from (10/11,39). |
| 6,7 | (32,42),(33,42) | PETALBURG_WOODS #4/#5 (Woods (36,38)/(37,38)) | `MB_NON_ANIMATED_DOOR` | Arrival point of the Woods SE exit. Not reachable from the rest of Route 104 (DERIVED). |

Coord event: `(17,51)`, `VAR_ROUTE104_STATE == 1` → `Route104_EventScript_RivalTrigger`. This is post-PokéNav, not ch3–4.

### 2b. Terrain (DERIVED from `map.bin` and tileset behaviours)

- **Tall grass (126 tiles).** North half: ONLY the north-west pocket, x=2..9 y=4..12 (34 tiles), plus x=6..7 y=4..5
  (3 tiles). **The north-half walking line has no grass**: the shortest Woods-to-Rustboro path crosses 0 grass
  tiles. South half: x=7..18 y=41..46 (29 tiles) and x=12..16 y=41..42 (9 tiles) around Cindy and the Woods SW door;
  x=20..29 y=54..61 (51 tiles), right on the walk from Petalburg (the shortest Petalburg-to-Woods path crosses 13 of them).
- **Water:** north ponds at x=13..37 y=9..21 (two bodies, 261 `MB_POND_WATER` tiles, with a wooden bridge). South:
  sea, x=0..28 y=39..79 (`MB_OCEAN_WATER`).
- **Bridge:** 38 `MB_REFLECTION_UNDER_BRIDGE` tiles at ground elevation 3, all walkable. The route runs north over
  x=30..31 y=17..21, then west over the 2-tall deck y=15..16 x=24..31, then north up x=24..25 y=9..14.
- **Ledges** (the ledge tile itself has collision=1; walking INTO it in its direction jumps 2 tiles,
  `field_player_avatar.c:693-714`):
  - `MB_JUMP_WEST`: x=28, y=49..54; and (30,56).
  - `MB_JUMP_SOUTH`: (29,55); x=31..33 at y=57.
  - `MB_JUMP_SOUTHWEST` at (28,55) and (30,57): no cardinal jump, so effectively walls (UNVERIFIED that a diagonal
    behaviour never jumps; I read only the cardinal ledge functions).
  - Together these make the SE pocket x≈29..33 y=42..56 exit-only.
- **Cut tree:** (35,22), guarding the X Accuracy (37,22).
- **Rocks in the sea:** `MB_MOUNTAIN_TOP` at (5,54),(5,55),(5,68),(5,69). Irrelevant on foot.

### 2c. Objects (VERIFIED `Route104/map.json` `object_events`; index = 1-based local id)

| # | What | Tile | Facing / movement | Notes |
|---|---|---|---|---|
| 3 | LASS **Haley** (`TRAINER_HALEY_1`, `scripts.inc:842`) | (31,24) | FACE_LEFT, sight **7** | north half |
| 9 | FISHERMAN **Ivan** (`TRAINER_IVAN`, `:832`) | (29,8) | FACE_DOWN, sight **0** | **talk-only**: range 0 never matches (`trainer_see.c:327-368`) |
| 23,24 | TWINS **Gina & Mia** (`TRAINER_GINA_AND_MIA_1`, double, `:965,:972`) | (27,15),(28,15) | FACE_DOWN, sight 1 | on the bridge; see §0.4 |
| 25 | RICH BOY **Winston** (`TRAINER_WINSTON_1`, `:883`) | (21,25) | **ROTATE_COUNTERCLOCKWISE**, sight 3 | north half |
| 26 | WOMAN **Cindy** (`TRAINER_CINDY_1`, `:924`) | (11,44) | FACE_UP_AND_RIGHT, sight 3 | south half, by the Woods SW door |
| 28 | YOUNGSTER **Billy** (`TRAINER_BILLY`, `:837`) | (18,67) | WALK_SEQUENCE_DOWN_RIGHT_UP_LEFT, range 5,6, sight 2 | walks a loop; see 2d |
| 33 | FISHERMAN **Darian** (`TRAINER_DARIAN`, `:979`) | (15,59) | FACE_LEFT, sight **0** | **talk-only** |
| 32 | BOY_2, gives **TM09 Bullet Seed** (`:317-326`) | (5,26) | LOOK_AROUND | north half, reachable |
| 16 | EXPERT_F, gives a **Chesto Berry** (`:248-258`) | (37,8) | FACE_LEFT r1,1 | north strip, reachable |
| 22 | WOMAN_5, White Herb florist | (8,19) | wander | **hidden until `FLAG_MET_PRETTY_PETAL_SHOP_OWNER` AND `FLAG_BADGE03_GET`** (`scripts.inc:20-28`) |
| 1,2,4,6 | NPCs (Bug Catcher, Girl ×2, Boy) | (15,60),(25,49),(27,63),(28,74) | | south half; flavour text |
| 5 | WOMAN_2 (talk) | (30,50) | wander | **inside the SE pocket**: talk-reachable only from the Woods SE exit (DERIVED) |
| 7 | Briney's BOAT | (12,54) | on `MB_OCEAN_WATER` | **visible from New Game**: its hide flag is not set in `new_game.inc` (only `FLAG_HIDE_ROUTE_104_MR_BRINEY` is, at line 134) |
| 8 | MR BRINEY | (12,51) | | hidden at New Game (`new_game.inc:134`) |
| 34 | RIVAL | (17,50), **on the cottage door** | | hidden at New Game (`new_game.inc:231`); `setobjectxyperm` to (17,52) under conditions (`scripts.inc:30-35`) |
| 21 | Item **PP Up** | (39,15) | | needs Surf (DERIVED) |
| 27 | Item **Poké Ball** | (29,53) | | SE pocket only (DERIVED) |
| 29 | Item **X Accuracy** | (37,22) | | behind cut tree (35,22) (DERIVED) |
| 31 | Item **Potion** | (5,8) | | north-west grass pocket, reachable (DERIVED) |
| 10–15, 17–20 | Berry trees | (34..36,6), (22..24,41), (3,22..25) | solid objects | At New Game these have berries: CHERI_1 (34,6), LEPPA (36,6), ORAN_2 (22,41), PECHA (24,41), ORAN_1 (3,23), CHERI_2 (3,25). The SOIL_* trees are empty. (`new_game.inc:7-12`) |

Hidden items (bg events, VERIFIED `map.json`): Super Potion (7,6), Poké Ball (3,9), Potion (14,55),
Antidote (16,72), Heart Scale (16,64). All are on reachable tiles (DERIVED).
Signs: Briney's cottage (20,50), route sign "→ PETALBURG CITY" (27,66), route sign "↑ RUSTBORO CITY" (23,5),
flower shop (7,20), TRAINER TIPS double battles (17,23).

### 2d. Forced-battle tiles (sight lines; DERIVED with `trainer_see.c:301-405`)

| Trainer | Trigger tiles (player standing there while the trainer faces that way) | Forced on the story walk? |
|---|---|---|
| Haley (W, 7) | (24..30, 24) | No. Rows 22, 23, 25 and 26 bypass her. |
| Winston (rotating, 3) | N: (21,22),(21,23),(21,24); S: (21,26); W: (18..20,25); E: (22..24,25) | **Timing-dependent.** Every path north must cross column x=21 in rows 22..26, and all of those tiles lie in one of his lines. He is avoided only when he faces away at that moment. The shortest path crosses at (21,22) (his N line). |
| Gina & Mia (S, 1) | (27,16), (28,16) | **Yes, IF the party has 2 usable Pokémon** (§0.4). Otherwise never. |
| Cindy (N/E, 3) | N: (11,41),(11,42),(11,43); E: (12,44),(13,44),(14,44) | No. The shortest path hits (11,41), but going round her south side via x=10 avoids both lines (choke test: still reachable). |
| Billy (walking loop, 2) | Loop (18,67)↓(18,73)→(23,73)↑(23,67)←(18,67). Union of his lines (exact): (16..21,67), (23,67), (18,68..73), (20..25,73), (23,65), (23,66), (23,68..71) | No. He is south of the Petalburg-to-Woods line (y=61..63, then north). Choke test: still reachable. |
| Ivan, Darian | none (range 0) | Never. Talk to battle. |

### 2e. What a person walking it would see

- **South half, from Petalburg:** you step off Petalburg's west edge onto a sandy beach. The sea is to the west and
  south. A route sign points back east to PETALBURG CITY. A big tall-grass patch sits just north-west of the
  entrance. Fishermen and children stand on the beach. Further north-west are **Mr. Briney's seaside cottage** (sign)
  and a moored boat on the water. North past the cottage there is more grass, a woman trainer (Cindy) standing beside
  it, three berry trees, and **a gap in the tree wall to the north-west: the Woods entrance**. Ledges on the east
  side drop you down from a fenced pocket, which you can see but cannot climb into.
- **North half, leaving the Woods:** you come out of the forest edge heading north into a wide east-west clearing.
  In it are a rich boy turning in place (Winston), a TRAINER TIPS sign about double battles, a boy who hands out a
  TM, four berry trees by the west fence, and a **flower shop** up a short path to the north-west, behind which a
  grassy corner hides a Potion. A lass (Haley) stares west along the clearing. At the east end the path turns north
  onto a **wooden bridge over a pond**, where **twin girls block half of the bridge**. Past the bridge, a path runs
  north beside a fisherman, a woman with berries and three berry trees, to a sign reading "↑ RUSTBORO CITY"; the
  city's south road is straight ahead.
- **Choke points:** the Woods doors; the bridge deck (twins); the Winston column; the 8-tile road into Rustboro
  (x=12..19).

---

## 3. PETALBURG WOODS (24,11)

### 3a. Warps (VERIFIED `PetalburgWoods/map.json`)

| # | Tile | → Route 104 | Behaviour | How it fires |
|---|---|---|---|---|
| 0,1 | (14,5),(15,5) | #2/#3 = (10,30)/(11,30) | `MB_NORTH_ARROW_WARP` | **Stand on the tile and hold UP** (arrow warp: player's own tile + held direction, `field_control_avatar.c:164-168`) |
| 2,3 | (16,38),(17,38) | #4/#5 = (10,38)/(11,38) | `MB_SOUTH_ARROW_WARP` | stand on it, hold DOWN |
| 4,5 | (36,38),(37,38) | #6/#7 = (32,42)/(33,42) | `MB_SOUTH_ARROW_WARP` | stand on it, hold DOWN; lands in the exit-only SE pocket |

### 3b. Terrain (DERIVED)

- **Tall grass: 325 tiles**, the densest of these maps. Main patches: x=4..13 y=25..33 (60), x=4..10 y=8..12 and
  x=4..10 y=15..19, x=16..25 y=17..19, x=18..25 y=24..25, x=21..27 y=32..35, x=36..41 y=34..37. The NE region (cut-gated)
  has x=37..45 y=4..29 and x=21..37 y=8..11. No water.
- **Ledges, all `MB_JUMP_SOUTH` (one-way southbound):** y=8 x=41..45; y=14 x=14..18; y=20 x=42..45; y=22 x=12..15;
  y=30 x=16..21; y=32 x=32..35. **The ledges make the northbound route unique; southbound has slack.**
- **Cut trees:** (19,10), (19,11). They gate the NE region (§0.7).

### 3c. The northbound spine (DERIVED shortest path, SW door to N exit, 84 steps, 31 grass tiles)

SW door inside (17,37) → north to row 33 → **west along row 32-33 past Lyle** → north up the west grass column
(x≈9, y=24..31; the Paralyze Heal is at (4,26)) → east along row 24 → **corridor x=26..27 north through the scene
trigger (26/27,23)** → past the researcher's (26,20) and the grunt's (26,17) start tiles → west along row 16 →
**north through x=5..7 at row 14, past James** → rows 8..13 (Ether (4,8), TRAINER TIPS PP sign (11,8)) → east to
x=12..14 y=6..7 → north arrow (14/15,5). From the SE door, the route joins the same spine.

Choke facts (DERIVED by tile removal; every one passes the control "reachable normally = True"):
- (26,23)+(27,23) removed: the N exit is **unreachable** from either south door. **The scene is forced northbound.**
  Southbound (N exit to SW door) is still reachable, but by then `VAR_PETALBURG_WOODS_STATE` is 1 (`scripts.inc:92`).
- All of Lyle's lines removed: unreachable. One facing removed: reachable. **Lyle (`FACE_DOWN_LEFT_AND_RIGHT`,
  range 3) is timing-dependent.**
- James's EAST line (5,14),(6,14),(7,14) alone removed: unreachable. **James (`FACE_DOWN_UP_AND_RIGHT`, range 3) is
  met only if he faces east as you cross row 14**; his N and S lines (x=4) are not on the route.
- Southbound with every Lyle and James line removed: still reachable. **Southbound, all Woods trainers are avoidable.**

### 3d. Objects (VERIFIED `map.json`; scene facts VERIFIED `PetalburgWoods/scripts.inc`)

| # | What | Tile | Notes |
|---|---|---|---|
| 3 | AQUA GRUNT (`LOCALID_PETALBURG_WOODS_GRUNT`) | (26,17) FACE_RIGHT | **Visible from New Game**: no script sets its hide flag except `removeobject` at `scripts.inc:70` (GitHub code search shows the flag only in `flags.h` and `map.json`). Battle `TRAINER_GRUNT_PETALBURG_WOODS` via `trainerbattle_no_intro` (`:23`, `:51`): **no running, no avoiding**. |
| 4 | DEVON researcher | (26,20) LOOK_AROUND | Same visibility. Gives a **Great Ball** after the battle (`:73`). Removed, and `VAR_PETALBURG_WOODS_STATE=1` set (`:91-92`). |
| 9 | BUG CATCHER **Lyle** (`TRAINER_LYLE`, `:253`) | (7,32), on tall grass | sight 3: S (7,33..35); W (4..6,32); E (8..10,32) |
| 10 | BUG CATCHER **James** (`TRAINER_JAMES_1`, `:258`) | (4,14) | sight 3: S (4,15..17); N (4,11..13); E (5..7,14) |
| 13 | GIRL_2, gives the **MIRACLE SEED** (`:229-238`) | (33,5) | **behind Cut** (DERIVED) |
| 8 | BOY_2 (wanders up/down, r=1,2) | (15,19) | on the upper path; can stand in your way |
| 11 | BOY_3 (wanders, r=2,1), explains hidden items | (30,34) | |
| 7 | Ether | (4,8) | reachable |
| 12 | Paralyze Heal | (4,26) | reachable |
| 5, 6 | Great Ball (45,7), X Attack (35,20) | | **Cut-gated** |

Hidden (VERIFIED): Potion (39,35), reachable; Poké Ball (4,19), reachable; Tiny Mushroom (26,6) and (40,29),
Cut-gated (DERIVED). Signs: TRAINER TIPS (EXP) (14,32), TRAINER TIPS (PP) (11,8).

**Scene geometry** (VERIFIED `scripts.inc:4-60`, movements `:104-140`). On (26,23), the "Left" script runs: the
researcher walks down 2 to face you. On (27,23), the "Right" script runs: he walks down 3 and turns. Then the grunt
walks in, and the battle starts with no intro. Afterwards the grunt runs, you get a Great Ball, and the researcher
walks off north. The whole scene is `lockall`: no input is needed except advancing text and the battle.

### 3e. What a person walking it would see

A dark, shaded forest (shade weather) with **tall grass almost everywhere**. You enter from the bottom edge. A bug
catcher stands in the grass to the west, turning between left, right and down. The only way on north is up through
that western grass and then east along an open strip, to a **narrow two-tile path heading north**. Partway up it, a
man in a lab coat is searching for Shroomish when a Team Aqua member jumps out. Past that, the path opens west into
more grass, where a second bug catcher guards a narrow gap. Then there is a sign about PP, and the **exit at the top
edge, left of centre**. Two small trees (cuttable) block a side path to the east; the area beyond them, with a girl and
some items, is visible but unreachable without Cut. Several one-way ledges lead back south.

---

## 4. RUSTBORO CITY (0,3)

### 4a. Warps (VERIFIED `RustboroCity/map.json`)

`MB_ANIMATED_DOOR` tiles have collision=1. You **face north from the tile below and hold UP** (`TryDoorWarp` looks
at the tile in front, direction north, `field_control_avatar.c:170-179, 833-855`). The Devon doors are
`MB_NON_ANIMATED_DOOR` with collision 0: step on them.

| # | Door tile | Approach tile | → |
|---|---|---|---|
| 0 | (27,19) | (27,20) | **RUSTBORO_CITY_GYM** |
| 3 | (16,38) | (16,39) | **POKÉMON CENTER 1F** (signs (17,38),(18,38)) |
| 2 | (16,45) | (16,46) | MART (signs (17,45),(18,45)) |
| 4 | (27,34) | (27,35) | **POKÉMON SCHOOL** (sign (25,35)). UNVERIFIED (recall, not checked in this pass): the Quick Claw gift is inside. |
| 8 | (9,38) | (9,39) | CUTTER'S HOUSE (HM01 Cut; sign (12,38)) |
| 5,6 | (11,15),(12,15) | step on from (11/12,16) | DEVON CORP 1F (sign (17,20)) |
| 1 | (13,30) | (13,31) | FLAT1 1F |
| 7 | (33,19) | (33,20) | HOUSE1 |
| 9 | (30,28) | (30,29) | HOUSE2 |
| 10 | (5,51) | (5,52) | FLAT2 1F |
| 11 | (26,46) | (26,47) | HOUSE3 |

DERIVED: every approach tile is reachable from the south road.

### 4b. Terrain (DERIVED)

No tall grass. No ledges. Water at x=0..9 y=0..33 (142 `MB_OCEAN_WATER` tiles), along the west side. Several walkable
tiles along the x=39 edge (y≥15) are isolated and unreachable: **a tile drawn as walkable is not necessarily
reachable.** The SE pocket x=21..36 y=51..58 is reachable only from Route 104 at x=33. It holds the X Defend (36,51).

### 4c. Objects at ch3–4 time (VERIFIED `map.json`; hide flags VERIFIED `new_game.inc:127-130`)

- Visible: Woman (22,34), Fat Man (19,13), Ninja Boy (25,37), Twin (21,46), Boy (12,45), Man (26,23, in the gym
  plaza), Little Boy and Little Girl (24,51),(25,51), Devon employee (13,34, wanders), Man (19,27), Boy (31,36),
  Item X Defend (36,51).
- **Hidden at New Game:** the Aqua grunt (13,21), Devon employee 1 (30,10), the rival (16,50), the scientist (11,15).
- **No trainers with sight anywhere in the city.** Every "forced" event is a coord trigger gated on
  `VAR_RUSTBORO_CITY_STATE`: state 1 = theft (23,20..24); 2 = help (30,9),(29,10),(30,11),(30,12);
  4 = return goods (30,9),(31,10),(30,11),(30,12); 7 = rival, the whole row (12..19,53). **During ch3–4 the state
  is 0, so none are armed.**
- `OnTransition` sets `FLAG_VISITED_RUSTBORO_CITY` on every entry (`scripts.inc:7`). This is the save-side proof
  of arrival, and it matches milestone `ch3_rustboro` (`VISITED_RUSTBORO_CITY: 2169`).

### 4d. Shortest static paths (DERIVED)

- South edge (16,59) → **PC approach (16,39)**: 24 steps, straight up the road x=16, then x=14..15 round the Mart.
  It crosses (16,53), the rival row (inactive in ch3–4).
- South edge (16,59) → **gym approach (27,20)**: 50 steps, north on x=16 to y=46, east, north on x=20 to y=20, then
  east along y=20 **across (23,20)** (the theft trigger, inactive until the badge).

### 4e. What a person walking it would see

A big stone city. You come up the south road, past the city sign, with a **Pokémon Center (red roof) and a Mart
(blue roof) on your left** a few blocks north. Cutter's house is west of the Center. The Trainer's School is on the
right. The large **DEVON CORPORATION building fills the north-west**. The **GYM is in a plaza to the north-east**,
with a sign at its west entrance. The east road leads to Route 116 (a tunnel sign at (30,8)), and a northern road
leads to Route 115. The sea runs along the west side.

---

## 5. RUSTBORO CITY GYM (11,3)

```
    00000000001          R = Roxanne (5,2), talk from (5,3) facing up
    01234567890          T = trainers; * = their trigger tiles; n = Gym Guide (3,18)
  0 ###########          s = statues (2,18),(8,18) (signs, read facing north)
  1 ###########          W = exits (5,19),(6,19): stand on one, hold DOWN
  2 #..#.R.#..#
  3 ...#...#...
  4 ...........
  5 ...........
  6 #T.########          Marc (HIKER) (1,6) faces S, range 3
  7 #*.########
  8 #*.......##
  9 #**T#.##.##          Tommy (YOUNGSTER) (3,9) faces W, range 3   <- (1,9) seen by BOTH (§0.5)
 10 #...#.##.##
 11 #.###....##
 12 #.....#####
 13 #.##.T.####          Josh (YOUNGSTER) (5,13) faces S, range 2
 14 #.##.*...##
 15 #.###*##.##
 16 ...........
 17 ...........
 18 ..sn....s..
 19 .....WW....
```

- VERIFIED: objects and sight ranges (`RustboroCity_Gym/map.json`); `trainerbattle_single` for Josh, Tommy and Marc
  (`scripts.inc:42,47,52`). **Roxanne has `TRAINER_TYPE_NONE`, so she never spots you: you must talk to her.**
- Badge script (`scripts.inc:12-27`): `FLAG_DEFEATED_RUSTBORO_GYM`, `FLAG_BADGE01_GET`, `VAR_RUSTBORO_CITY_STATE=1`,
  then **TM39 Rock Tomb** (`:29`).
- DERIVED: the shortest entrance-to-Roxanne path (23 steps) crosses Josh's (5,14),(5,15) and **(1,9) (Tommy + Marc)**.
  **All three are avoidable**: (5,16) → x=1 up to y=12 → east to (5,12) → (5,11) → (8,11) → x=8 up to (8,8) →
  west along row 8 to (2,8) → (2,7),(2,6) → up to (5,3). Choke test with all lines removed: still reachable.
- A person would see a small indoor gym of rock walls, with a man by the door (the Gym Guide), two statues, and a
  maze of short corridors with three trainers before Roxanne at the top centre.

---

## 6. Where a static reader goes wrong on these maps

1. **Hidden-at-New-Game objects are still listed in `map.json`.** That includes the Route 104 rival on the cottage
   door (17,50), so a static reader would wrongly treat the door as blocked. The others: Briney (12,51), the florist
   (8,19), the Rustboro grunt, Devon employee 1, the rival and the scientist. Filter by the hide flag
   (`new_game.inc:127-139, 231`). **The Woods grunt and researcher are the opposite case:** they are listed with hide
   flags but ARE visible until the scene removes them.
2. **Positions moved by script:** the Route 104 rival goes to (17,52) (`scripts.inc:30-35`); the Rustboro scientist
   goes to (11,15)/(12,15) at state 6; the Rustboro Devon employee goes to (14,21) and later (30,10).
3. **Berry trees are solid objects that change appearance.** Six Route 104 trees start with berries. Picking one is
   a free, human-like healing errand (it supports USER RULING 33).
4. **Cut trees use TEMP flags**, so they reappear on re-entry (UNVERIFIED that TEMP flags clear on map load; I
   did not read it).
5. **Animated doors have collision=1.** A reachability check must target the tile below and then press UP. A
   BFS that counts only walkable tiles calls every Rustboro building unreachable.
6. **Arrow warps (Woods exits, gym exit) fire on HOLDING the direction while standing on the tile**, not on
   stepping off it.
7. **The map edge is not the seam.** The walkable part of a shared edge is the intersection of both maps (see §1).
8. **Indoor maps report fake "edge" reachability** (gym x=0/x=10): there is no connection there.

---

## 7. What the game itself TELLS a player (the only parts of this note the AI may use, as dialogue or sign text)

- DAD names RUSTBORO CITY (already used by `milestones.json`). The route signs read "ROUTE 104 ↑ RUSTBORO CITY" at
  (23,5) and "ROUTE 104 → PETALBURG CITY" at (27,66) (`Route104/scripts.inc:1045-1051`). The Rustboro city sign
  is at (19,49) and the gym sign at (23,19).
- After the scene, the Devon researcher: "TEAM AQUA ... after something in RUSTBORO" (`milestones.json`, ch3_rustboro).
- **Gym Guide** (talk at (3,18)): "ROXANNE ... is a user of ROCK-type POKéMON ... it can't stand WATER-type and
  GRASS-type moves." (`RustboroCity_Gym/scripts.inc:106-125`). This is the dialogue-level type hint USER RULING 33's
  "type advantages" can lean on.
- TRAINER TIPS signs: double battles (Route 104 (17,23)); EXP for anything that appears in battle (Woods (14,32));
  PP and the Pokémon Center (Woods (11,8)).
- Route 104 Boy (Bullet Seed), Expert F (Chesto) and the Woods girl (Miracle Seed) explain their items when talked to.

Everything else here (coordinates, chokes, sight lines, hidden items, the Cut-gated areas) is for building proofs
and expectations only.

---

## 8. Method, approximations and how to re-derive

- **Sources fetched:** `data/maps/{Route104,PetalburgWoods,RustboroCity,RustboroCity_Gym,PetalburgCity,Route105,
  Route115,Route116}/map.json`, the four `scripts.inc`, `data/layouts/layouts.json`, the eight relevant `map.bin`,
  `data/tilesets/{primary/general,secondary/rustboro,primary/building,secondary/rustboro_gym}/metatile_attributes.bin`,
  `include/constants/metatile_behaviors.h`, `include/global.fieldmap.h`, `include/fieldmap.h`,
  `src/{trainer_see,event_object_movement,field_control_avatar,field_player_avatar,metatile_behavior,overworld}.c`,
  `src/data/tilesets/{headers,metatiles}.h`, `data/scripts/new_game.inc`, `data/maps/map_groups.json`,
  `src/data/wild_encounters.json`.
- **Fetch gotcha (worth a line in the playbook):** for **binary** files the contents API returned a corrupted body
  once: `data/layouts/PetalburgWoods/map.bin` decoded to 5914 bytes, not 4224. Fetch `.bin` files through the blob
  API (`gh api repos/pret/pokeemerald/git/blobs/<sha>`), and **assert `len(data) == size`**.
- **Grid decode (VERIFIED):** cell = u16; metatile = bits 0-9, collision = 10-11, elevation = 12-15
  (`global.fieldmap.h:7-12`). Behaviour = attribute bits 0-7 (`:39`). Metatile ids below 512 use the primary tileset
  and ids from 512 the secondary (`fieldmap.h:6`).
- **Approximations in the DERIVED results:**
  - walking only (no Surf or bike);
  - cardinal ledges only;
  - objects with a non-zero hide flag are left out of the blockers (except cut trees), so the Woods grunt and
    researcher are counted as blockers;
  - wanderers are placed at their template tile;
  - coord triggers do not block;
  - elevation uses `IsElevationMismatchAt` (`event_object_movement.c:7673-7689`), with the player taking the new
    tile's elevation unless it is 15;
  - sight follows `GetTrainerApproachDistance` and `CheckPathBetweenTrainerAndPlayer`: the tiles in between must be
    free of collision, directional blocks, elevation mismatches and static objects, and the player's tile must be
    passable at the trainer's elevation;
  - Billy's loop is simulated with `MoveNextDirectionInSequence` (`event_object_movement.c:3827-3853, 4071-4078`).
- **Scripts:** this session's scratchpad (`fetch.py`, `analyze.py`, `chokes.py`, `shortest.py`, `cells.py`). They are
  not committed. The algorithm above is enough to rebuild them. A permanent home would be `tools/story-dev/`, if the
  user wants it.
- **Wild encounters (VERIFIED `wild_encounters.json`):** Route 104 grass: Poochyena 40%, Wurmple 20%, Marill 20%,
  Taillow 10%, Wingull 10%, all Lv3-5. Woods grass: Poochyena 30%, Wurmple 25%, **Shroomish 15%**, Silcoon 10%,
  Cascoon 10%, Taillow 5%, **Slakoth 5%**, all Lv5-6. Rustboro: none.

## 9. Recommended live checks before code depends on this (cheap, bounded, on a fixture COPY)

1. **Gym (1,9) two-trainer battle** with a party of 2 or more usable Pokémon. The discriminator is a party of 1 vs
   2: the arms must differ (single battle vs two-trainer double).
2. **Twins on the Route 104 bridge** with 1 vs 2 usable Pokémon. The arms must differ (no battle vs double battle).
3. **The Woods scene choke:** from the SW door, assert that `VAR_PETALBURG_WOODS_STATE` turns 1 before the N exit
   is reached, using the AI's own walk (no forced path).
4. **Theft trigger on leaving the gym plaza after the badge** (`VAR_RUSTBORO_CITY_STATE` 1 → 2).
5. Spot-check two DERIVED reachability claims with `calculate_path` from a real captured position, plus a control
   tile that does path (`ai-research-notes/00-READ-THIS-FIRST.md` gate): Route 104 PP Up unreachable without Surf,
   and the Woods Miracle Seed girl unreachable without Cut.

---

## Appendix — ASCII renders (DERIVED from `map.bin` + tileset behaviours; developers only)

Legend: `W` warp; `T` trainer (sight > 0 or talk-only); `*` trainer sight trigger tile (any facing it can have);
`n` NPC (Roxanne shows as `n`); `?` object with a hide flag (state-dependent); `o` item ball; `C` cut tree;
`b` berry tree; `s` sign; `h` hidden item; `!` coord trigger; `#` collision; `"` tall grass; `~` water;
`v ^ < >` ledge (the direction of the jump); `D` door not overwritten by `W`; `.` walkable (it may still be unreachable).
An overlay hides the terrain underneath it.

### Route 104 (40×80)

```
    0000000000111111111122222222223333333333
    0123456789012345678901234567890123456789
  0 ##########........................######
  1 ############......................######
  2 ############................,,..########
  3 ##############..............,,,.########
  4 ######""######...............,,.########
  5 ######."######....,,...s........########
  6 ##"."""h""####....,,.......,,.....bbb.##
  7 ##""""""".######.....,,....,,.........##
  8 ##"""o""""##########.,,......T.......n##
  9 ##"h""""############~~~~..~~~~~~~~~~~~##
 10 ##""""##############~~~~..~~~~~~~~~~~~##
 11 ##""""##############~~~~..~~~~~~~~~~~~##
 12 ##."############~~~~~~~~..~~~~~~~~~~~~##
 13 ##..##########~~~~~~~~~~..~~~~~~~~~~~~##
 14 ##..##########~~~~~~~~~~..~~~~~~~~~~~~##
 15 ##..#########~~~~~~~~~~~...TT...~~~~~~.o
 16 ##.##########~~~~~~~~~~~...**...~~~~~~..
 17 ##.##########~~~~~~~~~~~~~~~~~..~~~~~~##
 18 ##.##W#######~~~~~~~~~~~~~~~~~..~~~~~~##
 19 ##......?..##~~~~~~~~~~~~~~~~~..~~~~~~##
 20 ##.....s...##~~~~~~~~~~~~~~~~~..~~~~~~##
 21 ##...........~~~~~~~~~~~~~~~~~..~~~~~~##
 22 ##.b.................*.............C.o##
 23 ##.b.............s...*............######
 24 ##.b.................*..*******T..######
 25 ##.b..............***T***.......########
 26 ##...n...............*..........########
 27 ##............##########################
 28 ##########..##...##....###....##########
 29 ########......##########################
 30 ##########WW############################
 31 ########################################
 32 ########################################
 33 ########################################
 34 ########################################
 35 ########################################
 36 ########################################
 37 ########################################
 38 ##########WW############################
 39 ~~~~######..############################
 40 ~~~~######..############################
 41 ~~~~~##""".*""""#####.bbb.##############
 42 ~~~~~~#""".*""""".........######WW######
 43 ~~~~~~#""".*..............######..######
 44 ~~~~~~##"".T***...........#####...######
 45 ~~~~~~~#""""""""""........#####...######
 46 ~~~~~~~####"""""""".......#####...######
 47 ~~~~~~~~~~#####............###....######
 48 ~~~~~~~##~~~~~######.......###....######
 49 ~~~~~~~##~~~~~######.....n..<.....######
 50 ~~~~~~~~~##~~~###W##s.......<.n...######
 51 ~~~~~~~####~?....!..........<.....######
 52 ~~~~~####~~~................<.....######
 53 ~~~~~##~~~~~~~#.............<o..########
 54 ~~~~~#~~~~~~?~##..##....."""<...########
 55 ~~~~#.#~~~~~~~h....#."""""""#v#.########
 56 ~~~~###~~~~~~~~....#""""""""""<.########
 57 ~~~~~##~~~~~~~~....#""""""""""#vvv######
 58 ~~~~~##~~~~~~~~....##"""""""""....######
 59 ~~~~~~##~~~~~~~T....#"""""".......######
 60 ~~~~~~##~~~~~~~n....##"""...........####
 61 ~~~~~~##~~~~~~.......#"""...............
 62 ~~~~~~##~~~~~~.......###................
 63 ~~~~~~~##~~~~~.........#...n............
 64 ~~~~~####~~~~~..h......##...........####
 65 ~~~~~##~~~~~~~.........*#...........####
 66 ~~~~~~##~~~~~~~........*###s......######
 67 ~~~~~~##~~~~~~~.**T***.*..#.......######
 68 ~~~~~#~~~~~~~~~...*....*..#.....########
 69 ~~~~#.#~~~~~~~~...*....*..#.....########
 70 ~~~~###~~~~~~~~~..*....*..##..##########
 71 ~~~~~~~##~~~~~~~..*....*.......#########
 72 ~~~~~~~##~~~~~~~h.*............#########
 73 ~~~~~~##~~~~~~~~~~*.******.....#########
 74 ~~~~~~##~~~~~~~~~~~~........n..#########
 75 ~~~~~##~~~~~~~~~~~~~~~~........#########
 76 ~~~~~####~~~~~~~~~~~~~~~~~~~~..#########
 77 ~~~~~~~##~~~~~~~~~~~~~~~~~~~~###########
 78 ~~~~~~##~~~~~~~~~~~~~~~~~~~#############
 79 ~~~~~~##~~~~~~~~~~~~~~~~~~~##~~#########
```
`,` = puddle (walkable). On row 28 only x=10..11 (the path to the Woods door) is reachable; the other `.` runs
on that row are unreachable (DERIVED).
Ivan (29,8) and Darian (15,59) are `T` with no `*` because their range is 0.

### Petalburg Woods (48×44)

```
    000000000011111111112222222222333333333344444444
    012345678901234567890123456789012345678901234567
  0 ################################################
  1 ################################################
  2 ################################################
  3 ################################################
  4 ################################......""""""####
  5 ##############WW################.n..."""""""####
  6 ############......########h####......####"""..##
  7 ############......########.####......####""..o##
  8 ####o..""""s......######""......"""..####vvvvv##
  9 ####."""""".......######"""..."""""".####.....##
 10 ####"""""""........C."""""""######"""........"##
 11 ####*""""".........C..""""""######""""......""##
 12 ####*"""######....######################..."""##
 13 ####*...######....######################..."""##
 14 ####T***######vvvvv######################.."""##
 15 ####*.."######.....######################.."""##
 16 ####*"""""".................##############."""##
 17 ####*""""""......"""".....?.##############..""##
 18 ####"""""""....."""""""""...##############..."##
 19 ####h""""".....n""""""""""..##############....##
 20 ############....##########?.######.o######vvvv##
 21 ############....##########..######..######"...##
 22 ############vvvv##########..####".....####""..##
 23 ############....##########!!####".....####""".##
 24 ######............""""""""..####""......""""".##
 25 ######"""..........""""""...####"""...."""""""##
 26 ####o""""""""...............####""""##."""""""##
 27 ####""""""""""..............####""""##."""""""##
 28 ####""""""######......##########""""####""""####
 29 ####""""""######......##########."""####h"""####
 30 ####""""""######vvvvvv##########..."############
 31 ####""""""######......##########....############
 32 ####***T***"""s.......""""######vvvv############
 33 ####...*"""""........"""""######....############
 34 ######.*............."""""""..n.....""""""######
 35 ######.*.............""""""..........""h""######
 36 ##############......##############..."""""######
 37 ##############......##############....""""######
 38 ################WW##################WW##########
 39 ################################################
 40 ################################################
 41 ################################################
 42 ################################################
 43 ################################################
```
The grunt is the `?` at (26,17) and the researcher the `?` at (26,20); the triggers are `!!` at (26,23),(27,23).
The Miracle Seed girl is the `n` at (33,5), behind the `C` trees. Everything east of x≈24 above y=32 is Cut-gated.

### Rustboro City (40×60)

```
    0000000000111111111122222222223333333333
    0123456789012345678901234567890123456789
  0 ##~~~~~~~~#########.....################
  1 ##~~~##~~~#########.....################
  2 ~~~~~##~~~#########.....################
  3 ~~~~~~~~~~#########.....################
  4 ~~~~~~~~~~#########.....################
  5 ~~~~~~#....########.......##############
  6 ~~##~#.......######.......##############
  7 ~~##~#.############.....#############.##
  8 ~~~~~#############............s.........
  9 ~~~~~#############............!.........
 10 ~~~~~#############...........!?!........
 11 ##~~~#############............!.........
 12 ##~~~#############............!.........
 13 ~~~~~#############.n....###############.
 14 ~~~~~#############......#...........###.
 15 ~~~~~##...#WW#...#......#...........#.##
 16 ~~~~~##..........#.#..#.######.######.##
 17 ~~~~~##..........#......######.########.
 18 ~~~~#.#.#......#.#......######.########.
 19 ~~~~#.#.........##.....s..#W#..##W###.##
 20 ~~~~#.#..#....#..s.....!............#.##
 21 ~~~~#.#......?.........!............###.
 22 ~~~~#.#................!............###.
 23 ~~~#..############.....!..n.........#.##
 24 ~~~#..#............#..#!............#.##
 25 ~~~#..#.................###############.
 26 ~~~####..#########......#...#####...###.
 27 ~~#.###..#########.n....#.#######...#.##
 28 ~~#.###..#########......#.####W##...#.##
 29 ~~#.###..#########......#...........###.
 30 ~#..###..####W####......#...........###.
 31 ~#..###............#..#.#######...###.##
 32 ~######.................#######.....#.##
 33 ~######.................#######.....###.
 34 ..#####......n........n.###W###.....###.
 35 ..##########.............s..........#.##
 36 ############...####............n....#.##
 37 ############...####......n..........###.
 38 #########W##s..#Wss#..#....###......###.
 39 #######....................###......#.##
 40 #######....................###.####.#.##
 41 ###............................####.###.
 42 ###............................####.###.
 43 ###............####.....######.####.#.##
 44 ##########.....####.....######.####.#.##
 45 ##########..n..#Wss#..#.######.####.###.
 46 ##########...........n..##W###.####.###.
 47 ##########..........................#.##
 48 ##########..........................#.##
 49 ##########.........s.........#......###.
 50 ##########......?..............########.
 51 #####W####..............nn.....#....o##.
 52 ###............................#.######.
 53 ###.........!!!!!!!!...........#.####.##
 54 ############........############.##.####
 55 ##.........#..#..#..#............##.####
 56 ##########.#........#.##################
 57 ##########.#........#.##################
 58 ######.....#........#.............######
 59 ############........#############.######
```
Gym door `W` (27,19), PC `W` (16,38), Mart `W` (16,45), School `W` (27,34), Cutter `W` (9,38), Devon `WW` (11..12,15).
The `!` column at x=23 (y=20..24) is the post-badge theft trigger. The `!` row at y=53 is the post-PokéNav rival.
The `.` column along x=39 below y=14 is unreachable decoration.
