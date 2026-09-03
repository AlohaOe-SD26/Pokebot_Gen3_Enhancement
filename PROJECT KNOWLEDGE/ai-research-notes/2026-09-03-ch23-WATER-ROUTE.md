# §Ch23 — THE WATER ROUTE: SOOTOPOLIS → EVER GRANDE

> ‼ **A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`), 2026-09-03.
> ⛔ **SCRIPTS, FLAGS, WARPS, OBJECTS AND TILE BYTES ARE READS. FLOOD FILLS, REACHABILITY, PATROL
> GEOMETRY AND THE 48-CONFIGURATION SIGHT TABLE ARE SIMULATION.** Nothing has touched an emulator.
> ✅ Read from a clean on-disk decomp clone (HEAD `5eff7864`) — **no `gh api`, no base64**, and every
> map asserts `len(map.bin) == w*h*2`: Sootopolis **7200**, Underwater_Sootopolis **400**, Route126
> **12800**, Route127 **12800**, Route128 **9600**, EverGrande **6400**, all ✅.
> All coordinates are RAW LAYOUT SPACE. *(The engine adds `MAP_OFFSET = 7` internally and
> `TrySetDiveWarp` subtracts it back — `field_control_avatar.c:965-983`.)*

---

## §0. ⛔⛔ THREE THINGS I HAD RECORDED THAT ARE WRONG

1. ⛔ **THE WATERFALL IS NOT ON ROUTE 128 — IT IS ON EVER GRANDE'S OWN MAP.**
   `MB_WATERFALL` counts: **Route126 = 0, Route127 = 0, Route128 = 0, EverGrandeCity = 96.**
   One solid block, 12 wide × 8 tall: **x = 15..26, y = 60..67** (collision 0, elevation 1), with
   `MB_OCEAN_WATER` at y=68 (the base) and y=59 (the top pool).
2. ⛔ **THE ROUTE HAS *TWO* UNDERWATER TRANSITIONS, NOT ONE.** "Sootopolis → a dive warp → Routes
   126/127/128" is wrong. The dive lands on a **separate 20×10 map**, `UNDERWATER_SOOTOPOLIS_CITY`,
   which reaches Route 126 only through a **walk-on warp** — not by diving.
3. ⛔ **DIVE IS GATED ON `FLAG_BADGE07_GET`, NOT BADGE 8.** (Waterfall is Badge 8 — that part was
   right.) Harmless: we hold all eight. `field_control_avatar.c:463-471`, `party_menu.c:3725`.

## §1. THE EXIT FROM SOOTOPOLIS — `setdivewarp`, NOT A CONNECTION

Emerald has two dive mechanisms (`overworld.c:756-772`): a `dive`/`emerge` **connection** (identity
x/y), else a script-set **fixed** destination. **Sootopolis uses the second.**
* `SootopolisCity/map.json:15` — `"connections": []`. **Zero connections, confirmed.**
* Only 7 maps in the repo have a `"direction": "dive"` connection (Routes 105, 124, 125, 126, 127,
  128, 129). **Sootopolis is not among them.**
* `SootopolisCity/scripts.inc:161-163` — `ON_RESUME: setdivewarp MAP_UNDERWATER_SOOTOPOLIS_CITY, 9, 6`
* `Underwater_SootopolisCity/scripts.inc:5-7` — `ON_RESUME: setdivewarp MAP_SOOTOPOLIS_CITY, 29, 53`

**The 19 dive tiles** (`MetatileBehavior_IsDiveable` = `MB_INTERIOR_DEEP_WATER` ∥ `MB_DEEP_WATER` ∥
`MB_SOOTOPOLIS_DEEP_WATER`, `metatile_behavior.c:853-861`), one pool on the crater floor:
`y=53: x=27-29 · y=54: x=25-31 · y=55: x=24-32`.
**The destination is fixed** — any of the 19 lands on `UNDERWATER_SOOTOPOLIS_CITY (9,6)`.

✅ **UNGATED BY STORY STATE.** Both `setdivewarp` lines sit in bare `ON_RESUME` handlers with **no
`goto_if`/`call_if`**, unconditional on every map load; a repo-wide grep finds no flag/var condition.
⭐ **And the `LEGENDS_BATTLE` alternate layout was decoded: its 19 dive tiles are BYTE-IDENTICAL.**
So the Sootopolis layout swap (`VAR_SOOTOPOLIS_CITY_STATE` 1-4, or 5 with `SKY_PILLAR_STATE <= 1`)
does not affect the exit.

✅ **REVERSIBLE AND EXACTLY SYMMETRIC.** `UNDERWATER_SOOTOPOLIS_CITY` has **zero** no-surfacing tiles;
surfacing anywhere lands at `SOOTOPOLIS_CITY (29,53)`, which is itself one of the 19 dive tiles.
✅ From the tile below the Poké Center door (43,32), the land component is 198 tiles with **18
surf-entry points** onto the water body holding **all 19/19** dive tiles (e.g. stand (40,37) face
west, or (40,39) face south).

⚠ **THE EMERGE-TILE TRAP — DO NOT USE THE ARRIVAL TILE.** `UNDERWATER_ROUTE126 (45,65)` is
`MB_WATER_DOOR`, which is emergible in vanilla **only because a `#ifdef BUGFIX` is OFF** — the source
itself calls this "the dive glitch" (`metatile_behavior.c:863-877`).
⇒ **Step ONE SOUTH to (45,66)** — plain `MB_NORMAL` — and surface there onto Route126 (45,66).

## §2. ⭐ THE FULL ROUTE, TILE BY TILE

1. **Sootopolis**: surf (e.g. from (40,37) facing west), reach a dive tile such as **(29,53)**, press **A**.
2. → **`UNDERWATER_SOOTOPOLIS_CITY (9,6)`**; swim to **(9,8)** or **(10,8)**
   (`MB_WATER_SOUTH_ARROW_WARP`, a walk-on warp).
3. → **`UNDERWATER_ROUTE126 (45,65)`**; step **south to (45,66)**; press **B** to emerge.
4. → **`ROUTE126 (45,66)`**; surf **east** to the right edge **x=79, y ∈ 29..58**.
5. → **`ROUTE127 (0, same y)`**; surf to the bottom edge **y=79 at x ∈ {19,20,21} ∪ {24..40}**.
6. → **`ROUTE128 (x, 0)`** (basin A); surf **east**. ⛔ **Fight Carlee and Harrison at x=101,
   y=22..29** (§3). Exit at **(119, y ∈ 27..32)**.
7. → **`EVER_GRANDE_CITY (0, y+40)` = (0, 67..72)**; surf to the waterfall base **(18,68)**; face
   **NORTH**; press **A**.
8. → lands **(18,59)**; surf to **(18,56)**; step **north onto land (18,55)**.
9. Walk **16 steps** → **(18,41) = VICTORY ROAD 1F**.
   *(Waypoints: (18,55) → (19,55) → (19,44) → (18,44) → (18,41).)*

**Seam arithmetic (READ, reciprocal offsets agree): `EverGrande_y = Route128_y + 40`.**
**Valid Route128 → Ever Grande crossings: (119, y) for y = 27..32.** ⚠ y=26 fails — EG (0,66) is land.

### THE WATERFALL, PRECISELY
`field_control_avatar.c:448-461`: the behaviour tested is the tile **one step in front**, and
`IsPlayerSurfingNorth` requires `DIR_NORTH` **and** the surfing flag (`field_player_avatar.c:1314`).
⇒ **stand at (x, 68) for any x in 15..26, surfing, facing NORTH, press A.**
`WaterfallFieldEffect_ContinueRideOrEnd` (`field_effect.c:1880-1897`) steps north while the tile the
player now stands on is `MB_WATERFALL` ⇒ **ends at (x, 59), same x, still surfing.**
⭐ **Use x = 18** — it lines up with the Victory Road door at x=18, minimising the land walk.
⚠ It is **one-way by default**: standing on a waterfall tile with controls released triggers
`ForcedMovement_PushedSouthByCurrent`, un-badge-gated — an accidental entry from the north pushes you
back down, never up.
✅ **The waterfall is genuinely mandatory**: re-flooding with `MB_WATERFALL` excluded leaves a
below-waterfall component of 180 tiles spanning y=67..77 that **never reaches y < 60**.

## §3. ⛔⛔ THE x=101 PINCH IS SETTLED — **THE BATTLES ARE UNAVOIDABLE**

This was the one place the earlier decomp work could not settle. It is settled now, and the answer is
**fight them**.

**The trainers (READ, `Route128/map.json`).** Only the four at **elevation 1** can matter:

| name | pos | elev | sight | movement |
|---|---|---|---|---|
| **Carlee** | **(101,29)** | 1 | **4** | `WALK_UP_AND_DOWN` |
| **Harrison** | **(101,22)** | 1 | **4** | `WALK_DOWN_AND_UP` |
| Isaiah | (35,33) | 1 | 3 | `WALK_SEQUENCE_RIGHT_UP_LEFT_DOWN` |
| Katelyn | (78,24) | 1 | 7 | `WALK_RIGHT_AND_LEFT` |

⭐ **LAND TRAINERS CANNOT SEE A SURFING PLAYER** *(inferred from `IsElevationMismatchAt`)*: a trainer
at elevation 3 checking a water tile at elevation 1 gets `COLLISION_ELEVATION_MISMATCH`, which is
evaluated **before** the object-event case, so it never returns `COLLISION_OBJECT_EVENT`.
⇒ Wayne (sight 0 — can never initiate anyway), Ruben and Alexa are all harmless.

**The geometry (READ, decoded).** Column x=101 has three water bands separated by rock:
```
y =  0..17   water   — basin B only (a dead end)
y = 18..21   BLOCKED
y = 22..29   water   — basin A: THE ONLY WAY THROUGH   ← 8 tiles
y = 30..36   BLOCKED
y = 37..39   water   — in neither basin
```
Basin A's width at x=99/100/101 is exactly y=22..29. **Harrison's patrol clips to (101, 22..25) and
Carlee's to (101, 26..29) — between them they occupy the ENTIRE 8-tile channel.**

**All 48 configurations (position × facing) enumerated for each of the 8 crossing rows:**

| player y | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 |
|---|---|---|---|---|---|---|---|---|
| safe / 48 | 21 | 18 | 15 | 12 | 12 | 15 | 18 | **21** |

⛔ **GUARANTEED-SAFE ROW: NONE.** Best odds are y=22 or y=29 at ~44%, and those are the trainers'
own home tiles.
**Bypasses ruled out (READ):** no alternate column — basin A is a single channel at x=99-101; and the
**underwater bypass fails** — Route128's diveable tiles in basin A span x=25..81, and flooding every
underwater component reachable from basin A gives 482 tiles with **max x = 81**, never reaching 101.

⇒ ⛔ **THE BOT MUST BE ABLE TO FIGHT CARLEE AND HARRISON, NOT ROUTE AROUND THEM.** Once their trainer
flags are set they never re-trigger, so this is a first-pass cost only.

## §4. ⚠ ROUTE 128 HAS TWO DISJOINT WATER BASINS — AND WE CANNOT FALL INTO THE WRONG ONE

Flood fill proves (40,0) and (75,0) are in **separate** components (overlap 0):

| basin | size | entered from the Rt127 seam at x | exits at x=119, y | lands in Ever Grande |
|---|---|---|---|---|
| **A** (west/south) | 1766 | 19-21, 24-43 | **26-32** | y=66-72 → **below the waterfall** ✅ |
| **B** (north-east) | 766 | 73-79 | 0-23 | y=40-63 → a **23-tile dead-end cove** ❌ |

✅ **GOOD NEWS:** Route127's reachable bottom-edge x values (18-21, 24-40, 55, 56, 59-61) map onto
Route128 north-edge tiles that are **entirely in basin A** — x=55/56/59/60/61 hit wall, and **none**
lands in basin B. ⇒ **a bot arriving from Route 127 cannot fall into the dead end.**

## §5. SCRIPTS THAT CAN SEIZE CONTROL

| map | can seize? | gate |
|---|---|---|
| Route126 | ✅ **No** — ON_TRANSITION is weather only | — |
| Route127 | ⚠ **Yes** | `VAR_SHOULD_END_ABNORMAL_WEATHER == 1` → `lockall` (`abnormal_weather.inc:173-191`); self-clears to 0 |
| Route128 | ⚠ **Yes** | `VAR_ROUTE128_STATE == 1` → `lockall` + ~6 msgbox cutscene (`scripts.inc:14-69`); self-clears to 2 |
| EverGrandeCity | ✅ **No** — weather only | — |

⭐ **AND A CORRECTION TO OUR OWN TEST.** `MapHeaderCheckScriptTable` (`script.c:299-326`) is **exact
equality**, and `Route128/scripts.inc:11` is `map_script_2 VAR_ROUTE128_STATE, 1, …`.
⇒ **only the value 1 fires; 0 and 2 are both safe.** The correct bot test is **`!= 1`**, NOT `>= 2`.
⚠ Route127's ON_LOAD rewrites water metatiles at (56-59, 9-12) or (60-63, 30-33) when
`VAR_ABNORMAL_WEATHER_LOCATION` is 13 or 14 — **a walkability change**, though it never touches the
player. *(This is KI-74's shape: `setmetatile` is invisible to a static layout reader.)*

## §6. EVER GRANDE CITY — EMPTY, AND SPLIT BY THE WATERFALL

40×80, `MAP_TYPE_CITY`, **`allow_escaping: false`**. One connection: left → Route128, offset +40.
✅ **`"object_events": []` — ZERO objects: no trainers, no NPCs, no item balls.** Nothing blocks arrival.

| warp | coord | destination |
|---|---|---|
| 0 | (18, 5) | Pokémon League 1F |
| 1 | **(27, 48)** | **Poké Center 1F** |
| 2 | **(18, 41)** | **VICTORY ROAD 1F warp 0 ← the entrance** |
| 3 | (18, 27) | Victory Road 1F warp 1 (the far-side exit) |

⛔ **(27,48), (18,27) and (18,5) are NOT reachable from below the waterfall** — they sit in the upper
city, gated behind Victory Road. ‼ **This retires an earlier claim that the Ever Grande Poké Center
is reachable before the cave**: `--driver ch23route` measured (18,41) → (27,49) = 23 wp, which is a
path *within the upper city*, not one the bot can walk on arrival.
⭐ The top pool is 44 tiles (x=15..26, y=56..59) and its **only** surf→land exits are
**(18..22, 56) stepping NORTH onto (18..22, 55)**.
The 11 `coord_events` at y=58, x=16..26 run only `setflag FLAG_VISITED_EVER_GRANDE_CITY` +
`setvar VAR_TEMP_1, 1` — **no `lock`, no `lockall`, no msgbox.** They cannot interrupt the bot.

## §7. ✅ NO CURRENTS ANYWHERE ON THE ROUTE
`MB_*_CURRENT` counts on Routes 126/127/128: **0, 0, 0.** There is **no `MB_WHIRLPOOL` constant in
pokeemerald at all.** The only forced-movement tile on the entire route is the Ever Grande waterfall.

## §8. ⚠ THE RISKIEST REMAINING UNKNOWN — AND IT IS DYNAMIC, SO STATIC WORK CANNOT CLOSE IT

**The patrol PHASE of Carlee and Harrison when the bot arrives** — how many of the two battles
actually fire (0, 1 or 2), and **whether our navigator thrashes in the 8-tile channel while a moving
trainer physically occupies its chosen tile.** Two moving solid objects in a corridor one tile wide
per row is exactly the shape that produces a re-path loop. The static analysis proves the *battles*
are certain; the *navigator's behaviour around the bodies* is unknown.

### ⭐ THE CHEAPEST LIVE CHECK
**One observe-only probe: park the bot at `ROUTE128 (99,25)` and log, once per frame for ~600 frames,
`(player_x, player_y, carlee_y, carlee_facing, harrison_y, harrison_facing)` — issuing NO movement
input.** That passive capture gives the real patrol period and phase, proves the two stay clipped to
y=22-25 / 26-29 as derived, and lets the 48-configuration table be replayed against real data offline.
Then, for the actionable half, an A/B on the crossing: **arm A walks through at y=29, arm B at y=22**,
discriminating on battles-triggered ∈ {0,1,2} plus wall-clock time in the channel.
‼ **Log the tile the bot ACTUALLY STEPS ON, not the candidate it considered** (house rule 7).
