# ✅ CLAUDE-VALIDATED — story round 1 (2026-07-25)

**Scope:** the two-generation story notes (`story-notes-sN.md` = Gemini **2.5-pro** = "v1";
`story-notes-sN-v2.md` = same prompt on Gemini **3.1-pro** = "v2").
**Topics validated, in priority order:** `s7` (HM acquisition & gating), `s9` (overworld obstacle
mechanics), `s10` (main-plot FLAG_/VAR_ reference), `s8` (missable/irreversible events).

**Method:** every ruling below cites a file I actually fetched and read this session via
`gh api repos/pret/pokeemerald/contents/<path> -H "Accept: application/vnd.github.raw"`, or our own
ROM-derived tables `sandbox-pokebot/modules/data/event_flags/emerald.txt` and
`event_vars/emerald.txt`. A claim I could not reach a source for is marked **UNRESOLVED** — never
ruled from recall. Line numbers are from the file as fetched on 2026-07-25 (pokeemerald `master`).

‼ Our flag/var tables store names **WITHOUT** the `FLAG_`/`VAR_` prefix (`"RECEIVED_HM_CUT"`).

---

## 0. THE HEADLINE FINDINGS (read these even if you read nothing else)

1. **Every `ITEM_HM01_CUT` / `FLAG_RECEIVED_HM01` style constant in v2's s7 is a PHANTOM.** The real
   names are `ITEM_HM_CUT` … `ITEM_HM_WATERFALL` and `FLAG_RECEIVED_HM_CUT` … `FLAG_RECEIVED_HM_WATERFALL`.
   Our own table confirms (`event_flags/emerald.txt` ids 106,107,109,110,122,123,137,312).
2. **Four of the eight HMs are handed over by a MAP-ENTRY (`ON_FRAME_TABLE`) trigger, not by
   talking to the NPC.** Both generations say "talk to X" for Surf, Strength and Dive. A bot that
   walks up and presses A will hang forever. Details in §3.
3. **`src/field_move.c` DOES NOT EXIST**, and neither do `CheckUseCut`, `CheckUseSurf`,
   `CheckUseStrength`, `TryCutTree`, `TrySmashRock`, `DoRockSmashWildEncounter`,
   `PlayerAvatar_DoPushBoulder`, `PushObject`, `CheckForForcedMovement`, or
   `MovePlayerAvatarUsingForcedMovement` — **0 hits each** on
   `gh api "search/code?q=<name>+repo:pret/pokeemerald"`. Ten fabricated symbols across the two
   generations. The real badge gate is `src/party_menu.c:3725`.
4. **The mandatory first Sky Pillar climb has NO cracked floors and needs NO Mach Bike.**
   `SkyPillar_{1F,2F,4F,Top}_OnTransition` all do `call_if_lt VAR_SKY_PILLAR_STATE, 2, …CleanFloor`
   → `setmaplayoutindex LAYOUT_SKY_PILLAR_*_CLEAN`. The story climb happens at
   `VAR_SKY_PILLAR_STATE == 0` (proved by `SkyPillar_Top_OnWarp`:
   `map_script_2 VAR_SKY_PILLAR_STATE, 0, …RayquazaFaceDown`). State only becomes 2 at
   `SootopolisCity/scripts.inc:559`, i.e. **after** the Rayquaza scene. Both generations imply the
   Mach Bike is needed for the mandatory climb; it is needed only for the post-crisis return trip.

> CORRECTED 2026-08-24 -- "NO cracked floors" IS FALSE. `_Clean` is a PER-FLOOR fact: `2F_Clean` has 0 cracked
> tiles but **`4F_Clean` has 5** (decoded from the shipped `SkyPillar_4F_Clean/map.bin`). The ascent
> REQUIRES stepping on one: `4F (3,1)` and `3F (7,1)` are SEALED POCKETS, unreachable from the
> `4F (11,1)` arrival even if every cracked tile is treated as passable. The only way in is a
> deliberate fall through `4F (6,4)`/`(7,4)` -- NOT `(9,4)`, which lands in 3F's MAIN region and
> wastes the climb. The "no Mach Bike" half of this claim SURVIVES. See the Ch21 ATLAS in
> `12-STORYMODE-DESIGN.md`.

5. **HM07 Waterfall needs you to talk to TWO NPCs nobody mentioned.** Wallace only gives it once
   `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` is set, and that flag is set by
   `SootopolisCity_EventScript_MaxieArchieLeave`, reachable only after **both**
   `FLAG_MET_MAXIE_SOOTOPOLIS` and `FLAG_MET_ARCHIE_SOOTOPOLIS` are set by separately talking to
   Maxie and Archie in Sootopolis at `VAR_SOOTOPOLIS_CITY_STATE == 5`. The same flag unlocks the
   **Gym door and all house doors** (`SootopolisCity/scripts.inc:10,12` → `LockGymDoor` /
   `LockHouseDoors`). Miss either NPC and the game is unfinishable with no error.
6. ‼ **`FLAG_DEFEATED_MAGMA_SPACE_CENTER` IS NOT MONOTONIC — the game deliberately CLEARS it.**
   `MossdeepCity_SpaceCenter_2F_EventScript_RivalRayquazaCall` ends with
   `clearflag FLAG_DEFEATED_MAGMA_SPACE_CENTER` (`MossdeepCity_SpaceCenter_2F/scripts.inc`, the
   script right after `EventScript_TabithaTrainer`). The flag is being re-used as a one-shot latch
   for the rival's PokéNav call, so it reads True only in the window between the Steven double
   battle and that call. **Never use it as a "Space Center cleared" milestone** — a bot that does
   will re-enter the chapter forever. Use `VAR_MOSSDEEP_SPACE_CENTER_STATE == 3` (set at `:277`),
   `VAR_STEVENS_HOUSE_STATE` or `FLAG_RECEIVED_HM_DIVE`. v2 named this flag as the Dive
   prerequisite, which is *causally* correct (§1 item 7.6) but a **trap to read**.
   This is the same failure shape as the shipped `DEFEATED_RIVAL_ROUTE_110` bug, except the name
   passes the audit — **existence is necessary but not sufficient; monotonicity must be checked too.**
7. **v1's s7 HM07 entry is a fabrication and it is the designated calibration signal.** It places
   Waterfall in `MAP_SOOTOPOLIS_CITY_CAVE_OF_ORIGIN_ENTRANCE` (7,4) via a script
   `SootopolisCity_CaveOfOrigin_Entrance_EventScript_Wallace`, and marks it **VERIFIED**. The real
   giver is `SootopolisCity_EventScript_Wallace` at `data/maps/SootopolisCity/scripts.inc:1275`.
   **v2 got the map and the script label exactly right.** Treat v1's s7 "VERIFIED" tags as
   worthless; v2's tags are worth something.
8. **`VAR_SOOTOPOLIS_CITY_STATE` has SEVEN states (0-6), not five.** Both generations published a
   5-value table and neither maps onto reality. The complete machine — every setter located and read
   — is **§3f**, and it is the spine of the final chapter.
9. ‼ **On three of the four mandatory `multichoice` menus, a blind A-press picks the WRONG option —
   and one of them loops forever.** `CaveOfOrigin_B1F_EventScript_WheresRayquaza` starts on index 0
   ("Cave of Origin"); only **index 2 ("Sky Pillar")** advances the story, and cases 0/1/3, the
   `switch` default **and B-press** all `goto` straight back to the same prompt — no counter, no
   timeout, no state change. Mr. Briney's two boat menus default to **decline** and **cancel**
   respectively. I swept all 49 `multichoice` sites in `data/maps/`; the complete critical-path
   table with correct indices is **§3h**. Neither note mentions any of this.
10. **On s8, both generations invented permanence that does not exist — v1 five times, v2 three
    times.** The Master Ball, TM Thief, TM Earthquake, every Magma Hideout item, the unchosen fossil
    and the S.S. Tidal content are all **NOT missable**; the things that genuinely vanish are the
    Aqua Hideout *grunts* (at Badge 7), the Magma Hideout *grunts* (at the Groudon cutscene) and
    each *Trick House puzzle* the moment you clear it. Full table in §1/s8. Building interrupts for
    the imagined losses would have been pure wasted work.


---

## 1. DISAGREEMENTS RULED

### s7 — HM acquisition and gating

| # | claim | v1 (2.5) says | v2 (3.1) says | RULING | source I read |
|---|---|---|---|---|---|
| 7.1 | **HM07 Waterfall location** (calibration) | `MAP_SOOTOPOLIS_CITY_CAVE_OF_ORIGIN_ENTRANCE`, script `SootopolisCity_CaveOfOrigin_Entrance_EventScript_Wallace`, coords (7,4), marked VERIFIED | `MAP_SOOTOPOLIS_CITY`, `SootopolisCity_EventScript_Wallace`, outside the Gym | **CONFIRMED-v2** | `data/maps/SootopolisCity/scripts.inc:1275-1296` — `SootopolisCity_EventScript_Wallace` → `goto_if_set FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE, …GiveWaterfall` → `giveitem ITEM_HM_WATERFALL; setflag FLAG_RECEIVED_HM_WATERFALL` |
| 7.2 | **HM07 prerequisite** | "Awaken Rayquaza and resolve the Groudon/Kyogre conflict" | "Awaken Rayquaza, watch cutscene, `VAR_SOOTOPOLIS_CITY_STATE` advanced, talk to Wallace" | **BOTH-WRONG (incomplete).** Truth: `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`, which requires talking to **Maxie AND Archie** in Sootopolis at `VAR_SOOTOPOLIS_CITY_STATE == 5` | same file `:1341-1372` — `EventScript_MaxieRayquaza` sets `FLAG_MET_MAXIE_SOOTOPOLIS` then `goto_if_set FLAG_MET_ARCHIE_SOOTOPOLIS, …MaxieArchieLeave`; `EventScript_ArchieRayquaza` is the mirror; `…MaxieArchieLeave:1364` does the `setflag` |
| 7.3 | **HM06 Rock Smash prerequisite** | "Defeat Wattson, `FLAG_DEFEATED_MAUVILLE_GYM`" | "None — walk in and talk" | **CONFIRMED-v2** | `data/maps/MauvilleCity_House1/scripts.inc:4-11` — `MauvilleCity_House1_EventScript_RockSmashDude` has exactly one guard, `goto_if_set FLAG_RECEIVED_HM_ROCK_SMASH`. No badge/gym check anywhere |
| 7.4 | **HM06 script label** | `…EventScript_RockSmashGuy` | `…EventScript_RockSmashDude` (marked INFERENCE) | **CONFIRMED-v2** | same, `:4` |
| 7.5 | **HM06 map** | `MAP_MAUVILLE_CITY_HOUSE1` | `MAP_MAUVILLE_CITY_HOUSE1` (hedged "could be HOUSE2") | **BOTH CORRECT** — it is House1; v2's hedge is unnecessary | `data/maps/MauvilleCity_House1/scripts.inc` exists and contains the giver |
| 7.6 | **HM08 Dive prerequisite** | "Defeat Tate & Liza, `FLAG_DEFEATED_MOSSDEEP_GYM`" | "Mind Badge **AND** clear the Magma Space Center (`FLAG_DEFEATED_MAGMA_SPACE_CENTER`)" | **CONFIRMED-v2** | `data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc:297-303` — `setflag FLAG_DEFEATED_MAGMA_SPACE_CENTER` … `setvar VAR_STEVENS_HOUSE_STATE, 1`; and `MossdeepCity_StevensHouse/scripts.inc:25` gates the gift on `VAR_STEVENS_HOUSE_STATE == 1` |
| 7.7 | **HM02 Fly — is there a battle?** | "Rival battle after defeating Norman" | "Weather Institute cleared, cross bridge, trigger and **win** the Rival battle" | **CONFIRMED-v2 on the battle**; both wrong on the gate (see 7.8) | `data/maps/Route119/scripts.inc:79-131` — `trainerbattle_no_intro TRAINER_{MAY,BRENDAN}_ROUTE_119_{TREECKO,TORCHIC,MUDKIP}` branching on `VAR_STARTER_MON`, then `EventScript_GiveFlyHM` |
| 7.8 | **HM02 Fly gate** | `FLAG_DEFEATED_GYM_LEADER_NORMAN` | `FLAG_DEFEATED_WEATHER_INST_AQUA` | **BOTH-WRONG — both flag names are PHANTOM.** The only script-level gate is the coord trigger's own condition `VAR_ROUTE119_STATE == 0` at tiles **(25,31)** and **(26,31)** on Route 119; completion is marked by `VAR_ROUTE119_STATE = 1` + `FLAG_RECEIVED_HM_FLY` | `data/maps/Route119/map.json` `coord_events[0..1]`; `scripts.inc:145` `setvar VAR_ROUTE119_STATE, 1`; both flag names absent from `event_flags/emerald.txt` |
| 7.9 | **Badge required to USE each HM** | Cut→01, Flash→02, RockSmash→03, Strength→04, Surf→05, Fly→06, Dive→07, Waterfall→08 | identical | **BOTH CORRECT, 8/8** | `src/party_menu.c:120-127` (the enum, commented with its badge) and `:3725` `FlagGet(FLAG_BADGE01_GET + fieldMove)` |
| 7.10 | **Cut is a mandatory story block** | YES — "cuttable trees blocking the entrance to the Aqua Hideout, `MAP_LILYCOVE_CITY_AQUA_HIDEOUT_ENTRANCE` (19,9),(20,9)" | NO — "Cut, Fly and Flash are strictly optional" | **CONFIRMED-v2. v1's entry is a total fabrication**: that map does not exist (the maps are `AquaHideout_1F/B1F/B2F`), and `LilycoveCity/map.json` contains **zero** `OBJ_EVENT_GFX_CUTTABLE_TREE`. The hideout warp is `(70,5) elevation 1` — i.e. reached by **Surf** | `gh api …/contents/data/maps --jq '.[].name'`; `data/maps/LilycoveCity/map.json` `warp_events`, `object_events` |
| 7.11 | **Flash is a mandatory story block** | YES for Granite Cave + Victory Road (v1 adds "a bot would require Flash to pathfind reliably") | NO — "Flash only changes the visual blend layer; collision maps are identical" | **CONFIRMED-v2** | `map.json` `requires_flash`: `GraniteCave_B1F`/`B2F` = true, `VictoryRoad_B1F`/`B2F` = true, `GraniteCave_1F`/`StevensRoom`/`VictoryRoad_1F` = false. And it is consumed **only** as a rendering effect: `src/overworld.c` `SetDefaultFlashLevel()`(:971) / `GetFlashLevel()`(:988) feed `InitCurrentFlashLevelScanlineEffect()`(:1794-1803), a scanline-window effect. No collision, warp or script path reads it |
| 7.12 | **Where is the Ever Grande waterfall** | "at the end of Victory Road, `MAP_VICTORY_ROAD_B2F` (exit area)" | "`MAP_EVER_GRANDE_CITY` — a literal waterfall blocks the entrance to Victory Road" | **CONFIRMED-v2** | `data/maps/VictoryRoad_B2F/map.json` — **all four** of its warps go back to `MAP_VICTORY_ROAD_B1F`; Victory Road's only overworld exits are `VictoryRoad_1F` (15,40) and (39,5), both → `MAP_EVER_GRANDE_CITY`. So the approach waterfall can only be in Ever Grande City |
| 7.13 | **Where are the Victory Road boulders/rocks** | "`VICTORY_ROAD_1F` and `B1F`" | "1F, B1F and B2F need Surf+Strength+RockSmash+Waterfall" | **BOTH-WRONG. Truth: B1F ONLY** — 8 `PUSHABLE_BOULDER` and 6 `BREAKABLE_ROCK`; 1F and B2F have **zero** | `data/maps/VictoryRoad_{1F,B1F,B2F}/map.json` `object_events`. B1F boulders @ (20,5)(21,4)(4,7)(9,10)(20,26)(21,25)(35,6)(34,4); rocks @ (19,5)(20,4)(18,12)(20,25)(21,26)(34,3) — note the paired boulder+rock coords: smash the rock so the boulder has somewhere to go |
| 7.14 | **Seafloor Cavern: which HMs** | Strength only | Strength **and** Rock Smash | **CONFIRMED-v2**; and the room list from both is wrong. Truth: obstacles in **Room1, Room2, Room3, Room5, Room8 only** (Rooms 4,6,7,9 and Entrance are clear). Breakable rocks in Room1(1), Room2(2), Room5(2). Room8 is a 12-boulder Sokoban | `data/maps/SeafloorCavern_Room{1..9}/map.json` `object_events` (full census in §4) |
| 7.15 | **Magma Hideout Strength boulders** | not listed | "boulders block progress **deep inside** the hideout" | **PARTIAL-v2.** Boulders exist, but only **3, all on `MagmaHideout_1F`** @ (5,22)(7,22)(6,23). All seven other Magma Hideout maps (2F_1R…4F) have **zero** | `data/maps/MagmaHideout_*/map.json` `object_events` |
| 7.16 | **Route 111 Rock Smash is a mandatory north block** | "clearing the rocks on Route 111 to access the desert" | "smashable rocks block the path north toward Route 112 / Mt. Chimney / Fallarbor" | **CONFIRMED-v2** on the block; **v1's stated reason is wrong** (the desert is gated by Go-Goggles, not Rock Smash). The two rocks are `BREAKABLE_ROCK` @ **(18,101)** and **(19,100)** and they DO sit on the mainline Mauville→Route 112→Fiery Path→Lavaridge route | `data/maps/Route111/map.json` `object_events`; **and our own already-validated traversal**, `sandbox-pokebot/modules/story/early_game.py:4355-4368` — `_smash_rock(ROUTE111,(18,102),"Up")`, `_smash_rock(ROUTE111,(19,101),"Up")`, then `_navigate_riding_out(ROUTE111,(18,99))` and into `ROUTE112` (Fiery Path south door). The approach tiles are one below each rock, exactly matching the map.json coords |
| 7.17 | **Granite Cave B1F boulder puzzle "unique to Emerald"** (v1, s9) | exists, must push boulders in sequence | says B2F uses `PUSHABLE_BOULDER` | **BOTH-WRONG.** `GraniteCave_B1F` has **zero** boulders and zero rocks. `GraniteCave_B2F` has **7 `BREAKABLE_ROCK` and zero boulders** | `data/maps/GraniteCave_B1F/map.json`, `GraniteCave_B2F/map.json` |

### s9 — overworld obstacle mechanics

| # | claim | v1 (2.5) says | v2 (3.1) says | RULING | source I read |
|---|---|---|---|---|---|
| 9.1 | **Are cuttable trees / smashable rocks metatiles or objects?** | metatiles — `MB_CUTTABLE_TREE`, `MB_ROCK_SMASH_ROCK` | object events — `OBJ_EVENT_GFX_CUTTABLE_TREE`, `OBJ_EVENT_GFX_BREAKABLE_ROCK` | **CONFIRMED-v2.** Neither `MB_CUTTABLE_TREE` nor `MB_ROCK_SMASH_ROCK` exists in the enum at all | `include/constants/metatile_behaviors.h` (whole 250-line file read); `data/maps/*/map.json` object_events use `OBJ_EVENT_GFX_CUTTABLE_TREE` / `OBJ_EVENT_GFX_BREAKABLE_ROCK` |
| 9.2 | **field-move script labels** | `TryCutTree`, `TrySmashRock`, `Common_EventScript_PushableBoulder` | `EventScript_CutTree`, `EventScript_RockSmash`, `EventScript_StrengthBoulder` | **CONFIRMED-v2, all three exact** | `data/scripts/field_move_scripts.inc:2, 61, 124` |
| 9.3 | **Strength badge** | "**Heat Badge** (`FLAG_BADGE06_GET`) — note: 6th badge in Emerald, not the 4th as in RS" | `FLAG_BADGE04_GET` | **CONFIRMED-v2. v1 is self-contradictory AND wrong** — Strength is index 3 in the field-move enum → `FLAG_BADGE01_GET + 3` = `FLAG_BADGE04_GET` (Heat) | `src/party_menu.c:120-127, 3725` |
| 9.4 | **Strength activation** | "player faces the boulder and presses A; the game checks Strength and the badge" | "`FLAG_SYS_USE_STRENGTH` must be set first; once set, moving into the boulder pushes it" | **CONFIRMED-v2** | `data/scripts/field_move_scripts.inc:124-162` — `EventScript_StrengthBoulder` does `goto_if_set FLAG_SYS_USE_STRENGTH, …CheckActivatedBoulder`; `EventScript_ActivateStrength:146-147` does the `setflag`. Push logic is `TryPushBoulder` / `Task_PushBoulder` in `src/field_player_avatar.c:77,103-106` |
| 9.5 | **water-current metatile names** | `MB_CURRENT_UP/DOWN/LEFT/RIGHT` | `MB_CURRENT_W/E/N/S` | **BOTH-WRONG.** Truth: `MB_EASTWARD_CURRENT`, `MB_WESTWARD_CURRENT`, `MB_NORTHWARD_CURRENT`, `MB_SOUTHWARD_CURRENT` (enum values 0x50-0x53) | `include/constants/metatile_behaviors.h:85-88` |
| 9.6 | **whirlpools** | `MB_WHIRLPOOL` on Route 124/126, impassable from the surface | `MB_CURRENT_*` "Currents / Whirlpools" section | **BOTH-WRONG — there is no whirlpool mechanic and no `MB_WHIRLPOOL` in Emerald.** Hoenn has no whirlpools; that is Gen 2/4 | whole `metatile_behaviors.h` read: zero matches for `WHIRLPOOL` |
| 9.7 | **spin-tile metatile names** | `MB_MOSSDEEP_GYM_SPIN_UP/_DOWN/_LEFT/_RIGHT`, state in `VAR_MOSSDEEP_GYM_STATE` | `MB_SPIN_RIGHT/_LEFT/_UP/_DOWN` | **BOTH-WRONG.** No `MB_*SPIN*` tile exists except `MB_SECRET_BASE_SPIN_MAT`. The Mossdeep Gym uses `MB_MOSSDEEP_GYM_WARP` (0x0E) for the teleport pads and `MB_SLIDE_{EAST,WEST,NORTH,SOUTH}` (0x45-0x48) for forced sliding. `VAR_MOSSDEEP_GYM_STATE` is also a **PHANTOM var** | `metatile_behaviors.h:19, 73-76, 193`; `event_vars/emerald.txt` has only `MOSSDEEP_CITY_STATE`(93), `MOSSDEEP_SPACE_CENTER_STATE`(159), `MOSSDEEP_SPACE_CENTER_STAIR_GUARD_STATE`(158) |
| 9.8 | **forced-movement function names** | `CheckForForcedMovement`, `MovePlayerAvatarUsingForcedMovement` | (none given) | **v1 BOTH FABRICATED (0 search hits each).** Real: `TryDoMetatileBehaviorForcedMovement`, `GetForcedMovementByMetatileBehavior`, and the dispatch tables `sForcedMovementTestFuncs` / `sForcedMovementFuncs` → `ForcedMovement_PushedEastByCurrent`, `ForcedMovement_SlideNorth`, `ForcedMovement_MuddySlope`, `ForcedMovement_MatSpin`, `ForcedMovement_Slip` | `src/field_player_avatar.c:45-65, 144-188` |
| 9.9 | **Sky Pillar cracked floors — which floors** | 3F and 5F, scripts `SkyPillar_3F_EventScript_CrackedFloor` / `SkyPillar_5F_…` | **2F and 4F** | **CONFIRMED-v2.** Only `SkyPillar_2F` and `SkyPillar_4F` install `setstepcallback STEP_CB_CRACKED_FLOOR` + `setholewarp`. v1's two script labels do not exist | `data/maps/SkyPillar_2F/scripts.inc`, `SkyPillar_4F/scripts.inc` (whole files; `SkyPillar_2F_SetHoleWarp` → `setholewarp MAP_SKY_PILLAR_1F`, 4F → `MAP_SKY_PILLAR_3F`) |
| 9.10 | **Sky Pillar fall mechanic** | "the script checks speed implicitly by how fast you cross before `waitstate`" | "`src/bike.c` / `PlayerIsOnMachBike()` and maintaining maximum speed" | **BOTH-WRONG on the implementation; v2 right on the requirement.** Truth: `CrackedFloorPerStepCallback` in `src/field_tasks.c` — stepping on `MB_CRACKED_FLOOR` with `GetPlayerSpeed() != PLAYER_SPEED_FASTEST` does `VarSet(VAR_ICE_STEP_COUNT, 0)`; the map's `ON_FRAME_TABLE` `CaveHole_CheckFallDownHole` = `map_script_2 VAR_ICE_STEP_COUNT, 0, EventScript_FallDownHole` then `warphole`s you. Stepping on `MB_CRACKED_FLOOR_HOLE` always zeroes it. Each cracked tile you cross becomes a hole 3 callback ticks later (only 2 tracked at once) | `src/field_tasks.c` `CrackedFloorPerStepCallback`; `data/scripts/cave_hole.inc` |
| 9.11 | **Mach Bike needed for the story Sky Pillar climb** | implied yes | explicitly yes ("Sky Pillar is mandatory before the E4"; max-speed Mach Bike) | **BOTH-WRONG.** The mandatory climb runs on `LAYOUT_SKY_PILLAR_*_CLEAN` (`call_if_lt VAR_SKY_PILLAR_STATE, 2`), which has no cracked floors. Story climb is at state **0**. Cracked floors appear only at state ≥ 2, i.e. the optional post-crisis trip to battle Rayquaza | `data/maps/SkyPillar_{1F,2F,4F}/scripts.inc` `*_OnTransition`; `SkyPillar_Top/scripts.inc` `OnTransition` + `OnWarp` (`map_script_2 VAR_SKY_PILLAR_STATE, 0`); `SootopolisCity/scripts.inc:559` is the only `setvar …, 2` |
| 9.12 | **Rayquaza awakening is an interaction** | `SkyPillar_Top_EventScript_Rayquaza` "after interacting with Rayquaza" (s10) | "walk up to Rayquaza; it flies away" | **BOTH-WRONG for the story beat.** The story awakening is a **coord trigger at (14,9)** gated `VAR_SKY_PILLAR_RAYQUAZA_CRY_DONE == 0`, script `SkyPillar_Top_EventScript_AwakenRayquaza`. `SkyPillar_Top_EventScript_Rayquaza` is the **post-game Lv70 wild battle** on a *different* object (`OBJ_EVENT_GFX_RAYQUAZA_STILL` @ (14,6), shown only when `VAR_SKY_PILLAR_STATE >= 2` and `FLAG_DEFEATED_RAYQUAZA` unset) | `data/maps/SkyPillar_Top/map.json` (`coord_events`, both `object_events`); `SkyPillar_Top/scripts.inc:17-45` |
| 9.13 | **Mirage Tower crumbling floors — which floors, which mechanic** | 2F, 3F **and 4F**, "crumbling sand", same as Sky Pillar | 1F-4F, `MB_MUD_SLOPE`, "if speed is insufficient collision behaves as a solid wall" | **BOTH-WRONG.** Truth: **2F and 3F only** install `STEP_CB_CRACKED_FLOOR` + `setholewarp` (2F→1F, 3F→2F). 1F and 4F have no floor mechanic at all. It is the identical `MB_CRACKED_FLOOR` mechanic, **not** a mud slope; and `MB_MUD_SLOPE` is a phantom name (real: `MB_MUDDY_SLOPE`) | `data/maps/MirageTower_{1F,2F,3F,4F}/scripts.inc` (all four read); `metatile_behaviors.h:213` |
| 9.14 | **muddy-slope failure behaviour** | not covered | "collision behaves as a solid wall" | **REFUTED.** `ForcedMovement_MuddySlope` (`src/field_player_avatar.c:567-576`): if `movementDirection != DIR_NORTH` **or** `GetPlayerSpeed() < PLAYER_SPEED_FASTEST`, it locks facing and `DoForcedMovement(DIR_SOUTH, PlayerWalkFast)` — you get **pushed back down**, you are not blocked | same |
| 9.15 | **Sootopolis Gym ice — pass condition** | "step on every ice tile in a section exactly once"; "state resets on falling or leaving"; "no persistent tracking" | "`VAR_ICE_STEP_COUNT` is set to the total tile count and **decremented**; step on the exit stairs when it is exactly 0" | **BOTH-WRONG. v2's direction is inverted.** Truth (exact): `SootopolisCity_Gym_1F_OnTransition` does `setvar VAR_ICE_STEP_COUNT, 1`; each fresh `MB_THIN_ICE` step **increments** it. `OnFrame` fires stairs-unlock scripts at the exact values **8, 28, 67** (each unlock then does `addvar VAR_ICE_STEP_COUNT, 1` so the equality trigger cannot refire). Stepping on `MB_CRACKED_ICE` sets it to **0**, and `map_script_2 VAR_ICE_STEP_COUNT, 0` → `…EventScript_FallThroughIce`. So it is not "reach the stairs at 0" — 0 is the **failure** value | `data/maps/SootopolisCity_Gym_1F/scripts.inc` (`OnTransition`, `OnResume`, `OnLoad`, `EventScript_CheckSetStairMetatiles`, `OnFrame`); `src/field_tasks.c` `SootopolisGymIcePerStepCallback` |
| 9.16 | **Sootopolis Gym ice — is progress tracked persistently?** | "no persistent flags for individual tiles" | "a counter in memory" | **v1 essentially right, both incomplete.** Visited tiles are stored as **bitmasks in `VAR_TEMP_1`…`VAR_TEMP_A`**, one temp var per ice row (map rows y = 6,7,8,9, 12,13,14, 17,18,19), bit = `x - 3`. Puzzle region is x∈[3,13], y∈[6,19]. `SetSootopolisGymCrackedIceMetatiles` (called from `ON_LOAD`) repaints cracked ice from those bits. Because they are **TEMP** vars, nothing survives a map change — so the puzzle is fully restartable and **cannot permanently wedge a bot**. The decomp even warns the scheme breaks if the puzzle exceeds 16 tiles wide | `src/field_tasks.c` `sSootopolisGymIceRowVars[]` + `CoordInIcePuzzleRegion` / `MarkIcePuzzleCoordVisited` / `IsIcePuzzleCoordVisited` / `SetSootopolisGymCrackedIceMetatiles`; `SootopolisCity_Gym_1F/scripts.inc` `OnLoad` |
| 9.17 | **`VAR_ICE_STEP_COUNT` is only about ice** | implied | implied | **NEW — both missed it.** The **same var** drives Sky Pillar 2F/4F and Mirage Tower 2F/3F cracked floors, and `CaveHole_FixCrackedGround` resets it to 1. The decomp comments it `// this var does double duty`. A bot must not treat it as an ice-only signal | `src/field_tasks.c` `CrackedFloorPerStepCallback`; `data/scripts/cave_hole.inc`; `gh api search/code?q=VAR_ICE_STEP_COUNT` → `cave_hole.inc`, `field_tasks.c`, `SootopolisCity_Gym_1F`, `SkyPillar_2F`, `SkyPillar_4F` |
| 9.18 | **Desert Ruins braille: "2 right, 2 down, then Strength"** (v1) | as stated, marked VERIFIED, "checks `VAR_X_COORD`/`VAR_Y_COORD`" | not covered | **UNRESOLVED** — I did not fetch `DesertRuins/scripts.inc`. Flag it: `VAR_X_COORD` / `VAR_Y_COORD` are **not** in our var table, so at minimum those two names are phantom | `event_vars/emerald.txt` (no `X_COORD`/`Y_COORD`) |
| 9.19 | **Trick House puzzle order and `VAR_TRICK_HOUSE_PUZZLE_LEVEL` / `VAR_TRICK_HOUSE_PUZZLE1_STATE`** | as listed | similar list | **PHANTOM NAMES.** Our table has `TRICK_HOUSE_LEVEL`(68) and `TRICK_HOUSE_PUZZLE_1_STATE`…`_8_STATE`(171-178) — note `PUZZLE_1_STATE` **with** the underscore, and `TRICK_HOUSE_LEVEL` without `PUZZLE`. The per-puzzle mechanic lists are UNRESOLVED (not fetched) | `event_vars/emerald.txt:68,171-178` |

### s8 — missable / irreversible events

Grounded by a delegated Claude pass with the same tool access (real `gh api` fetches + our local
tables); every row cites a file it read. **Headline: v1 asserted five permanence claims that are
FALSE, and v2 asserted three "hardcode an interrupt here" constraints that are also FALSE — s8 is
the topic where a wrong answer wastes the most engineering in BOTH directions.**

| # | claim | v1 (2.5) says | v2 (3.1) says | RULING | source read |
|---|---|---|---|---|---|
| 8.1 | **Master Ball / Aqua Hideout after Kyogre** | Wailmer block the hideout forever → Master Ball + trainers lost | hideout stays accessible forever | **CONFIRMED-v2 — v1 is exactly inverted.** `LilycoveCity_OnLoad` does `call_if_unset FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE, …SetWailmerMetatiles`: the Wailmer wall exists **only while the flag is UNSET** and is gone permanently once Aqua flees | `data/maps/LilycoveCity/scripts.inc:14-31`; `AquaHideout_B1F/map.json` (`FLAG_ITEM_AQUA_HIDEOUT_B1F_MASTER_BALL`); `AquaHideout_B2F/scripts.inc:49-50` |
| 8.2 | **Aqua Hideout trainers** | lost forever | not addressed | **BOTH INCOMPLETE — truth: they vanish at BADGE 7**, nothing to do with Wailmer or Kyogre. `MossdeepCity_Gym_EventScript_TateAndLizaDefeated` does `setflag FLAG_BADGE07_GET` then `setflag FLAG_HIDE_AQUA_HIDEOUT_GRUNTS`. Item balls stay | `data/maps/MossdeepCity_Gym/scripts.inc:60-67` |
| 8.3 | **TM Thief (Oceanic Museum) missable?** | yes, NPC despawns after the segment | yes, must talk before defeating Archie | **BOTH-WRONG — never missable.** The giver is hidden by `FLAG_HIDE_SLATEPORT_CITY_OCEANIC_MUSEUM_FAMILIAR_AQUA_GRUNT`, set in exactly one place: **his own exit script, after he gives you the TM.** The Archie scene sets a *different* flag (`…OCEANIC_MUSEUM_AQUA_GRUNTS`) that only removes scenery grunts | `SlateportCity_OceanicMuseum_1F/scripts.inc:142-188` + its `map.json`; `…_2F/scripts.inc:65` |
| 8.4 | **TM Earthquake / Seafloor Cavern re-entry** | silent | "permanently missable — the Cavern entrance ceases to exist" | **REFUTED.** `Underwater_SeafloorCavern_OnResume` does `setdivewarp MAP_SEAFLOOR_CAVERN_ENTRANCE, 10, 17` **unconditionally**. Post-Kyogre the script rewrites the blocking tiles to `METATILE_Underwater_FloorShadow` (id `0x228`, attr `0x1012` → behaviour **18 = `MB_DEEP_WATER`**), and `MetatileBehavior_IsUnableToEmerge` blocks only `MB_NO_SURFACING`/`MB_SEAWEED_NO_SURFACING` — so surfacing still works | `Underwater_SeafloorCavern/scripts.inc`; `include/constants/metatile_labels.h:779`; `data/tilesets/secondary/underwater/metatile_attributes.bin` idx 40; `src/metatile_behavior.c:863-875` |
| 8.5 | **Magma Hideout seals after the Space Center?** | silent | yes — sweep items first | **REFUTED.** `JaggedPass_OnLoad` does `goto_if_le VAR_JAGGED_PASS_STATE, 1, …ConcealHideoutEntrance`; the reveal cutscene sets state **2** and **nothing ever lowers it** → the entrance is open forever. All item balls remain. Only the **grunts** disappear, at the Groudon 4F cutscene (`setflag FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS`) | `JaggedPass/scripts.inc:7-60` + `map.json` warp (16,18)→`MAGMA_HIDEOUT_1F`; `MagmaHideout_4F/scripts.inc:62-70` |
| 8.6 | **The unchosen fossil** | "lost forever, the choice is permanent" | recoverable post-game in the Desert Underpass | **CONFIRMED-v2.** `DesertUnderpass_EventScript_Fossil` gives the **opposite** one (`goto_if_set FLAG_CHOSE_ROOT_FOSSIL → GiveClawFossil`, and the mirror). Gated post-Hall-of-Fame via `VAR_FOSSIL_MANIAC_STATE` | `DesertUnderpass/scripts.inc`; `data/scripts/hall_of_fame.inc:5,34` |
| 8.7 | **"Mirage Tower collapses if you leave empty-handed"** | asserted | not claimed | **REFUTED.** `MirageTower_4F_EventScript_CollapseMirageTower` is reachable **only** from the two fossil-pickup scripts. Also the recovery site is the **Desert Underpass** behind the *Fossil* Maniac (Route 114), not "the Ruin Maniac tunnel on Route 111" | `MirageTower_4F/scripts.inc` (whole file) |
| 8.8 | **Berry Master's wife** | only ONE of two special berries per save | five phrases → five berries, each with its own flag | **CONFIRMED-v2, and v2's phrase→berry table is exactly right.** Five independent branches, each `goto_if_set FLAG_RECEIVED_<X>_BERRY`. The throttle is **one per day** (`FLAG_DAILY_BERRY_MASTERS_WIFE`), not one per save | `Route123_BerryMastersHouse/scripts.inc:36-130` |
| 8.9 | **Castform missable?** | "no — the game forces you to accept it" | needs an empty party slot, else come back later | **BOTH-WRONG, v2 closer.** `givemon` has a **PC fallback** (`MON_GIVEN_TO_PC`), and the scientist re-offers forever (`goto_if_set FLAG_RECEIVED_CASTFORM`). Not missable | `Route119_WeatherInstitute_2F/scripts.inc:46-126,199-204` |
| 8.10 | **Lavaridge egg flag + label** | `FLAG_RECEIVED_WYNAUT_EGG`, `LavaridgeTown_EventScript_EggGiver` | `FLAG_RECEIVED_LAVARIDGE_EGG`, `LavaridgeTown_EventScript_EggWoman` | **CONFIRMED-v2 on both.** ‼ And unlike gift mons, **eggs hard-require a free party slot** (`getpartysize == PARTY_SIZE`); the flag is set only on accept, so it is infinitely retryable | `LavaridgeTown/scripts.inc:232-261` |
| 8.11 | **Johto starter gate** | Hoenn Dex **seen**; `FLAG_RECEIVED_JOHTO_STARTER`; cites `src/prof_birch.c` | ball machine; `FLAG_SYS_ELEGANT_CAMELLIA` | **BOTH-WRONG.** Real gate: `VAR_DEX_UPGRADE_JOHTO_STARTER_STATE` plus `specialvar VAR_RESULT, HasAllHoennMons` — **caught, not seen**. Both flag names are phantoms and **`src/prof_birch.c` 404s**. v2 is right that the other two are then permanently lost (`goto_if_ge …STATE, 6`) | `LittlerootTown_ProfessorBirchsLab/scripts.inc:7-13,21-38,285-296` |
| 8.12 | **S.S. Tidal content lost at Champion** | asserted; cites `src/ss_tidal.c` and `FLAG_DEFEATED_SS_TIDAL_TRAINER_1` | silent | **REFUTED, fully inverted.** `new_game.inc:187-188` **sets** the two SS-Tidal hide flags; `hall_of_fame.inc:13-14` **clears** them and `:20` arms the S.S. Ticket. **The ship does not exist before the Hall of Fame.** `src/ss_tidal.c` 404s | `data/scripts/new_game.inc:187-188`; `data/scripts/hall_of_fame.inc:13-14,20,38-42` |
| 8.13 | **Trick House loss timing** | puzzles 1-7 lost when you finish puzzle 8; `VAR_TRICK_HOUSE_STATE` | silent | **BOTH-WRONG and the truth is WORSE.** The door warps by `switch VAR_TRICK_HOUSE_LEVEL`, one case per puzzle — **each puzzle map (with its Mail item and trainers) becomes unreachable the moment you clear that puzzle**, not at the end. Real vars: `VAR_TRICK_HOUSE_LEVEL`(68), `VAR_TRICK_HOUSE_ENTRANCE_STATE`(167) | `Route110_TrickHouseEntrance/scripts.inc:7-13,443-520` |
| 8.14 | **Latias vs Latios** | silent | TV choice sets `VAR_ROAMER_POKEMON` (0=Latias, 1=Latios); the other needs the Eon Ticket | **CONFIRMED-v2, exactly.** `special InitRoamer; copyvar VAR_ROAMER_POKEMON, VAR_RESULT` from `MULTI_TV_LATI`; `CreateInitialRoamerMon(0) → SPECIES_LATIAS`. Southern Island sets up the **opposite** species. A genuinely irreversible one-time decision | `data/scripts/players_house.inc:459-479`; `src/roamer.c:84-113`; `SouthernIsland_Interior/scripts.inc:16-30,75-76` |
| 8.15 | **TM Sludge Bomb** | Dewford Town outside, after Norman | `DewfordTown_Hall`, `DewfordTown_Hall_EventScript_SludgeBombMan`, after Knuckle | **CONFIRMED-v2 on map + label (character-exact).** Both wrong on the gate — **there is no badge check at all**, just `goto_if_set FLAG_RECEIVED_TM_SLUDGE_BOMB` then `giveitem` | `DewfordTown_Hall/scripts.inc:240-255` |
| 8.16 | **TM Skill Swap** | "Gentleman NPC on the west side of Mt. Pyre Exterior" | silent | **REFUTED — it is an item ball**, `MtPyre_Exterior_EventScript_ItemTMSkillSwap` at (19,40), flag `FLAG_ITEM_MT_PYRE_EXTERIOR_TM_SKILL_SWAP`(1074). No NPC exists | `MtPyre_Exterior/map.json:31-41` |
| 8.17 | **TM Hidden Power which-hand game** | Fortree **House4**, answer right/right/left, retryable | silent | **CONFIRMED-v1 on the mechanic** (`MULTI_RIGHTLEFT`, wrong on case 1 / case 1 / case 0 ⇒ **Right, Right, Left**) and on retryability; **wrong house** — it is `FortreeCity_House2_EventScript_HiddenPowerGiver` | `FortreeCity_House2/scripts.inc:4-27` |
| 8.18 | **Mirage Island** | daily 2-byte RNG vs a party PV; cites `src/fldeff_misc.c UpdateMirageIsland()`; "could be never" | `MAP_ROUTE130`; daily value vs the **low 2 bytes of a party mon's PV** | **CONFIRMED-v2, precisely.** `IsMirageIslandPresent()` compares `GetMirageRnd() >> 16` against `personality & 0xFFFF` per party slot. It is **deterministic and forceable** (breed for a matching PV), not "could be never". v1's citation is fabricated | `src/time_events.c:12-52`; `Route130/scripts.inc:1-33` |
| 8.19 | **Scanner → Deep Sea Tooth OR Scale** | not mentioned | not mentioned | **GAP — a real irreversible one-of-two choice both generations missed.** `removeitem ITEM_SCANNER` + `setflag FLAG_EXCHANGED_SCANNER`; the Scanner is a single item ball. Only one of the two held items is ever obtainable | `SlateportCity_Harbor/scripts.inc:344-381` |

**s8 phantom names → the real ones:** `FLAG_RECEIVED_WYNAUT_EGG`→`FLAG_RECEIVED_LAVARIDGE_EGG`(266) ·
`FLAG_RECEIVED_JOHTO_STARTER`/`FLAG_SYS_ELEGANT_CAMELLIA`→**no flag**, use
`VAR_DEX_UPGRADE_JOHTO_STARTER_STATE`(211) · `VAR_FOSSIL_CHOSEN_FROM_DESERT`→`FLAG_CHOSE_ROOT_FOSSIL`(335)/`FLAG_CHOSE_CLAW_FOSSIL`(336) ·
`FLAG_RECEIVED_TM46`→`FLAG_RECEIVED_TM_THIEF`(269) · `FLAG_RECEIVED_TM36`→`FLAG_RECEIVED_TM_SLUDGE_BOMB`(230) ·
`FLAG_RECEIVED_TM10`→`FLAG_RECEIVED_TM_HIDDEN_POWER`(264) · `FLAG_RECEIVED_TM05`→`FLAG_RECEIVED_TM_ROAR`(231) ·
`FLAG_RECEIVED_TM27`→`FLAG_RECEIVED_TM_RETURN`(229) · `FLAG_RECEIVED_TM48`→`FLAG_ITEM_MT_PYRE_EXTERIOR_TM_SKILL_SWAP`(1074) ·
`FLAG_GOT_COIN_CASE`→`FLAG_RECEIVED_COIN_CASE`(258) · `FLAG_RECEIVED_SOOT_SACK`→**no flag**, use
`VAR_GLASS_WORKSHOP_STATE`(190) · `FLAG_BERRY_MASTER_WIFE_GAVE_BERRY`→5 per-berry flags(248-252) + `FLAG_DAILY_BERRY_MASTERS_WIFE` ·
`FLAG_RECEIVED_BELUE_BERRY_FROM_LILYCOVE_FAN`→`FLAG_RECEIVED_BELUE_BERRY`(252) ·
`FLAG_HIDEPOUT_ENTRANCE_BLOCKED`→`FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE`(112) ·
`FLAG_DEFEATED_SS_TIDAL_TRAINER_1`→`FLAG_DEFEATED_SS_TIDAL_TRAINERS`(247) ·
`VAR_TRICK_HOUSE_STATE`→`VAR_TRICK_HOUSE_LEVEL`(68) ·
`FLAG_HIDE_OCEANIC_MUSEUM_AQUA_GRUNTS`→`FLAG_HIDE_SLATEPORT_CITY_OCEANIC_MUSEUM_AQUA_GRUNTS`(883).
**Fabricated citations:** `src/ss_tidal.c`, `src/prof_birch.c` (both 404),
`src/fldeff_misc.c::UpdateMirageIsland()` (file exists, function does not),
`is_stadium_and_mt_pyre_cleared()`, `is_kyogre_awakened()`.

**s8 CONFIRMED-GOOD CORE**
* **Truly irreversible one-shot decisions:** the fossil pick (loser recoverable post-HoF at the
  Desert Underpass) · **Latias vs Latios** (`VAR_ROAMER_POKEMON`) · the **Johto starter** (1 of 3) ·
  **Scanner → Deep Sea Tooth *or* Scale** · the Trick House prize Tent (Red/Blue).
* **Real points of no return for a completionist sweep:** Aqua Hideout grunts die at **Badge 7** ·
  Magma Hideout grunts die at the **Groudon 4F cutscene** · **each Trick House puzzle** (its Mail +
  trainers) is gone the moment you clear it.
* **Not missable — do not special-case:** Master Ball · every Magma Hideout item ball · TM Earthquake
  in Seafloor Cavern Room 9 · TM Thief · Castform · Amulet Coin · Coin Case · Pokéblock Case ·
  Soot Sack · the Lavaridge egg · TM Hidden Power · all five Berry-Master's-wife berries (1/day).
* **Party-full semantics:** gift **Pokémon** fall through to the PC (`MON_GIVEN_TO_PC`); gift **eggs**
  hard-require a free party slot (`getpartysize`).
* **Latent hazard:** `JaggedPass_OnResume` does `checkitem ITEM_MAGMA_EMBLEM` on **every** visit — the
  Magma Hideout cannot open unless the emblem is still in the bag. Never sell/toss it.
* **Post-Hall-of-Fame unlocks** (`data/scripts/hall_of_fame.inc`): S.S. Ticket + S.S. Tidal, the
  Beldum ball, National Dex → Johto starter, the Desert Underpass fossil, the Safari Zone expansion,
  Wally at the Victory Road exit.

**s8 UNRESOLVED:** all coordinates in either note (unverified except where a `map.json` was open) ·
v2's Route 116 "Blackglasses guy can never resolve if you sell them" (both flags exist, script not
read) · whether the non-Lilycove Contest Lobbies also give the Pokéblock Case · the Mirage Tower
daily-visibility setters · the bike-swap, Scott-encounter, Glass Ornament, Soothe Bell, TM Roar,
TM Return, Exp. Share, Devon Scope, Go-Goggles and gym-leader-TM scripts (flag existence only).

### s10 — main-plot FLAG_/VAR_ reference

The full mechanical audit is §2. Direct disagreements worth calling out:

| # | claim | v1 (2.5) says | v2 (3.1) says | RULING | source |
|---|---|---|---|---|---|
| 10.1 | flag for clearing Seafloor Cavern | `FLAG_DEFEATED_ARCHIE_IN_SEAFLOOR_CAVERN` | `FLAG_DEFEATED_SEAFLOOR_CAVERN`, hedged "might be `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN`" | **CONFIRMED-v2's hedge.** Real name: `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` (id 129) | `event_flags/emerald.txt:129` |
| 10.2 | flag for the stolen submarine | `FLAG_TEAM_AQUA_STEAL_SUBMARINE` | not named | **BOTH-WRONG/absent.** Real: `FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE` (112) | `event_flags/emerald.txt:112` |
| 10.3 | Mt. Chimney Maxie flag | `FLAG_DEFEATED_MAGMA_ON_MT_CHIMNEY` | `FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY` | **CONFIRMED-v2** (id 139) | `event_flags/emerald.txt:139` |
| 10.4 | Elite Four progress var | `VAR_PORTE_E4_STATE` (marked UNSURE), "controls which E4 room you can enter, **resets on loss**" | not named | **PHANTOM name.** Real: `VAR_ELITE_4_STATE` (156). The "resets on loss" behaviour is **UNRESOLVED** (I did not read the E4 corridor scripts) — but a related and more dangerous fact IS settled: `FLAG_DEFEATED_ELITE_4_{SIDNEY,PHOEBE,GLACIA,DRAKE}` are **cleared on entering the Hall of Fame**, so they can never mean "the E4 is beaten" (§3i) | `event_vars/emerald.txt:156`; `data/event_scripts.s:628-632` `EverGrandeCity_HallOfFame_EventScript_ResetEliteFour` |
| 10.5 | champion flag | `FLAG_DEFEATED_CHAMPION` + `FLAG_SYS_GAME_CLEAR` | `FLAG_SYS_GAME_CLEAR` | **CONFIRMED-v2.** `FLAG_DEFEATED_CHAMPION` is a PHANTOM; the real pair is `FLAG_SYS_GAME_CLEAR` (**2148**) and `FLAG_IS_CHAMPION` (**2175**) | `event_flags/emerald.txt:1034,1061` |
| 10.6 | Sootopolis calm flag | `FLAG_LEGENDARIES_IN_SOOTOPOLIS_CALMED` | not named | **PHANTOM, and inverted in meaning.** The real flag is `FLAG_LEGENDARIES_IN_SOOTOPOLIS` (83) and it is **cleared** when the crisis ends (`SootopolisCity/scripts.inc:513, 560` — `clearflag FLAG_LEGENDARIES_IN_SOOTOPOLIS`). Gating on "calmed == set" would read False forever | `event_flags/emerald.txt:83`; `SootopolisCity/scripts.inc` |
| 10.7 | Rayquaza awakened flag | `FLAG_WOKE_UP_RAYQUAZA` | not named | **PHANTOM.** Use `VAR_SKY_PILLAR_STATE` (≥1) or `VAR_SKY_PILLAR_RAYQUAZA_CRY_DONE`. `FLAG_DEFEATED_RAYQUAZA` (448) exists but means the post-game battle was resolved | `event_flags/emerald.txt`; `event_vars/emerald.txt:202,215` |
| 10.8 | Magma Emblem flag | not named | `FLAG_RECEIVED_MAGMA_EMBLEM` (UNSURE) | **PHANTOM — no `*MAGMA_EMBLEM*` flag exists at all.** Use `VAR_JAGGED_PASS_STATE` (200) or a bag check | `event_flags/emerald.txt` (zero matches for `EMBLEM`) |
| 10.9 | `VAR_LITTLEROOT_TOWN_STATE` value table | 0 start, 1 entered lab, 2 chose starter, 3 defeated rival, 4 Pokédex, 5-7 running shoes/amulet coin | 0 default, 1 saved Birch, 2 rival defeated on R103 | **UNRESOLVED — they are mutually exclusive and I did not fetch `LittlerootTown/scripts.inc`.** Do not use either table. v2 also lists `VAR_LITTLEROOT_INTRO_STATE` as a separate var, which is correct (id 146) | `event_vars/emerald.txt:80,146` |
| 10.10 | `VAR_SOOTOPOLIS_CITY_STATE` value table | 5 values: 0 pre-event, 1 awakened, 2 spoke to Wallace, 3 Rayquaza awakened, **4 crisis averted / gym open** | 5 values: 0 peaceful, 1 fighting, 2 go to Sky Pillar, 3 Rayquaza intervenes, **4 normal (gym open)** | **BOTH-WRONG — there are SEVEN states (0-6), and neither table maps onto the real one.** Complete verified machine in §3f | every setter and every reader: `SeafloorCavern_Room9:116`, `SootopolisCity:243,342`, `CaveOfOrigin_B1F:55`, `SkyPillar_Outside:82`, `SkyPillar_Top:126`, `SootopolisCity_Gym_1F:102`, plus all 30 read sites in `SootopolisCity/scripts.inc` |
| 10.11 | "Wally's uncle gives Rock Smash after `FLAG_DEFEATED_WALLY_MAUVILLE`" (v1) | as stated | — | **REFUTED.** Rock Smash comes from the Rock Smash Dude in `MauvilleCity_House1` with no prerequisite. `FLAG_DEFEATED_WALLY_MAUVILLE` (190) is a real flag but is unrelated to the HM | `data/maps/MauvilleCity_House1/scripts.inc:4-11` |
| 10.12 | "`FLAG_DEFEATED_RUSTBORO_GYM` is also known as `FLAG_BADGE01_GET`" (v1, repeated for all 8 gyms) | same flag | — | **REFUTED — they are two distinct flags** set side by side. e.g. `PetalburgCity_Gym/scripts.inc:377,379` does `setflag FLAG_DEFEATED_PETALBURG_GYM` then `setflag FLAG_BADGE05_GET`. Both exist independently in our table. Treating them as aliases is harmless for reads but wrong, and the badge flag is the one that gates HM use | `data/maps/PetalburgCity_Gym/scripts.inc:377-379`; `event_flags/emerald.txt` |

---

## 2. FLAG AUDIT — the notes' names run through the tables

Method: extracted every distinct `FLAG_*` / `VAR_*` token from both s10 files and checked each
against `sandbox-pokebot/modules/data/event_flags/emerald.txt` (1164 flags) and
`event_vars/emerald.txt` (256 vars), stripping the prefix as our table requires. Script at
`<scratchpad>/audit_notes.py`.

| file | distinct names | EXISTS | **PHANTOM** |
|---|---|---|---|
| `story-notes-s10.md` (v1, 2.5-pro) | 51 | 33 | **18 (35%)** |
| `story-notes-s10-v2.md` (v2, 3.1-pro) | 38 | 32 | **4 real (11%)** + 2 regex artefacts |
| `story-notes-s7.md` (v1) | 11 | 10 | **1** |
| `story-notes-s7-v2.md` (v2) | 20 | 11 | **9** (all of them the `FLAG_RECEIVED_HM0n` family) |

### PHANTOM — s10 v1 (18). Each of these reads **False/0 forever**.
`FLAG_CHOSE_STARTER` · `FLAG_ASSISTED_WALLY` · `FLAG_DEFEATED_SLATEPORT_MUSEUM_AQUA_GRUNTS` ·
`FLAG_DEFEATED_RIVAL_ROUTE110` · `FLAG_TEAM_AQUA_ESCAPED_METEOR_FALLS` ·
`FLAG_DEFEATED_MAGMA_ON_MT_CHIMNEY` · `FLAG_CLEARED_WEATHER_INSTITUTE` ·
`FLAG_DEFEATED_RIVAL_ROUTE119` · `FLAG_AQUA_OR_MAGMA_STOLE_ORB` ·
`FLAG_DEFEATED_MAXIE_IN_MAGMA_HIDEOUT` · `FLAG_TEAM_AQUA_STEAL_SUBMARINE` ·
`FLAG_DEFEATED_SHELLY_IN_AQUA_HIDEOUT` · `FLAG_DEFEATED_ARCHIE_IN_SEAFLOOR_CAVERN` ·
`FLAG_WOKE_UP_RAYQUAZA` · `FLAG_KYOGRE_GROUDON_IN_SOOTOPOLIS` ·
`FLAG_LEGENDARIES_IN_SOOTOPOLIS_CALMED` · `VAR_PORTE_E4_STATE` · `FLAG_DEFEATED_CHAMPION`

‼ **`FLAG_DEFEATED_RIVAL_ROUTE110` is the exact class of name that already shipped a bug in this
project** (`DEFEATED_RIVAL_ROUTE_110`). Note what the table *does* contain:
`DEFEATED_RIVAL_ROUTE103` (130, **no** underscore before the number) and
`DEFEATED_RIVAL_ROUTE_104` (125, **with** one) — the ROM is internally inconsistent, so **never
pattern-match a route flag name; always look it up.** There is **no** Route 110 rival-defeat flag
at all; the observable is `VAR_ROUTE110_STATE` / `FLAG_HIDE_ROUTE_110_RIVAL` (919).

### PHANTOM — s10 v2 (4 real)
`FLAG_RECEIVED_MAGMA_EMBLEM` (no `*EMBLEM*` flag exists) ·
`FLAG_DEFEATED_MAGMA_HIDEOUT` (offered as an alternative; real is `FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS`, which v2 also listed and which **does** exist) ·
`FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_MAGMA_TEAM` (real: `FLAG_HIDE_MOSSDEEP_CITY_TEAM_MAGMA` + `FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_{1F,2F}_TEAM_MAGMA`, per `MossdeepCity_SpaceCenter_2F/scripts.inc:278-280`) ·
`FLAG_DEFEATED_SEAFLOOR_CAVERN` (real: `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN`)
*(the two artefacts `FLAG_HIDE` / `FLAG_DEFEATED` come from my regex catching v2's prose ellipses `FLAG_HIDE...`, not from a real claim.)*

Notably v2 **correctly** predicted names v1 got wrong, including
`FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY`, `FLAG_HIDE_ROUTE_101_ZIGZAGOON`,
`FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS`, `FLAG_HIDE_AQUA_HIDEOUT_GRUNTS`, `FLAG_ADVENTURE_STARTED`,
`FLAG_SYS_POKEMON_GET`, `VAR_LITTLEROOT_INTRO_STATE`, `VAR_METEOR_FALLS_STATE`,
`VAR_SKY_PILLAR_STATE`, `VAR_BRINEY_LOCATION`, `VAR_WEATHER_INSTITUTE_STATE` **and**
`VAR_ROUTE119_STATE` (both exist, 179 and 114).

### PHANTOM — s7 v2 (9)
`FLAG_RECEIVED_HM01` … `FLAG_RECEIVED_HM08` (real: `FLAG_RECEIVED_HM_CUT`,
`_FLY`, `_SURF`, `_STRENGTH`, `_FLASH`, `_ROCK_SMASH`, `_WATERFALL`, `_DIVE`) and
`FLAG_DEFEATED_WEATHER_INST_AQUA`. Same for the item constants: `ITEM_HM01_CUT` → `ITEM_HM_CUT`.

### PHANTOM — s7 v1 (1)
`FLAG_DEFEATED_GYM_LEADER_NORMAN` (real: `FLAG_DEFEATED_PETALBURG_GYM` / `FLAG_BADGE05_GET`).

### Also phantom, from s9
`MB_CUTTABLE_TREE` · `MB_ROCK_SMASH_ROCK` · `MB_WHIRLPOOL` · `MB_CURRENT_{UP,DOWN,LEFT,RIGHT}` ·
`MB_CURRENT_{N,S,E,W}` · `MB_MOSSDEEP_GYM_SPIN_*` · `MB_SPIN_*` · `MB_CRUMBLING_FLOOR` ·
`MB_CRUMBLED_FLOOR` · `MB_MUD_SLOPE` · `VAR_MOSSDEEP_GYM_STATE` · `VAR_TRICK_HOUSE_PUZZLE_LEVEL` ·
`VAR_TRICK_HOUSE_PUZZLE1_STATE` · `VAR_X_COORD` · `VAR_Y_COORD` · `src/field_move.c` and the ten
fabricated C function names in §0.3.

### PHANTOM — s8 (both generations)
Full list with corrections at the end of §1/s8. Headline: **19 phantom names**, including two where
**no flag exists at all** and a var must be used instead (`VAR_DEX_UPGRADE_JOHTO_STARTER_STATE` for
the Johto starter, `VAR_GLASS_WORKSHOP_STATE` for the Soot Sack), and the whole
`FLAG_RECEIVED_TM<nn>` family — the ROM names TMs by **move**, not number
(`FLAG_RECEIVED_TM_THIEF`, `_SLUDGE_BOMB`, `_HIDDEN_POWER`, `_ROAR`, `_RETURN`).

### Regression check on shipped code
`python tools/story-dev/audit_flag_names.py` → **`all names valid` (2 files vs 1164 flags / 256 vars)**.
No phantom has leaked into `modules/story/early_game.py` or `plugins/custom_modes/story_mode.py`.

---

## 3. CONFIRMED-GOOD CORE — grounded, safe to build on

### 3a. HM acquisition (all eight, each read from its script)

| HM | item / flag | where | **how it is actually triggered** | prerequisite (from the script) |
|---|---|---|---|---|
| Cut | `ITEM_HM_CUT` / `FLAG_RECEIVED_HM_CUT` | `MAP_RUSTBORO_CITY_CUTTERS_HOUSE` | **talk** — `RustboroCity_CuttersHouse_EventScript_Cutter` | none |
| Flash | `ITEM_HM_FLASH` / `FLAG_RECEIVED_HM_FLASH` | `MAP_GRANITE_CAVE_1F` | **talk** — `GraniteCave_1F_EventScript_Hiker` | none |
| Rock Smash | `ITEM_HM_ROCK_SMASH` / `FLAG_RECEIVED_HM_ROCK_SMASH` | `MAP_MAUVILLE_CITY_HOUSE1` | **talk** — `MauvilleCity_House1_EventScript_RockSmashDude` | none (also sets `FLAG_HIDE_ROUTE_111_ROCK_SMASH_TIP_GUY`) |
| Surf | `ITEM_HM_SURF` / `FLAG_RECEIVED_HM_SURF` | `MAP_PETALBURG_CITY_WALLYS_HOUSE` | ‼ **WALK IN** — `map_script_2 VAR_PETALBURG_CITY_STATE, 4, …EventScript_GiveHMSurf` (an `ON_FRAME_TABLE` entry). Talking to Wally's Dad runs a *different* script that never gives it | `VAR_PETALBURG_CITY_STATE == 4`, set at `PetalburgCity_Gym/scripts.inc:448` after Norman |
| Strength | `ITEM_HM_STRENGTH` / `FLAG_RECEIVED_HM_STRENGTH` | `MAP_RUSTURF_TUNNEL` | ‼ **WALK IN after smashing the rock** — `map_script_2 VAR_RUSTURF_TUNNEL_STATE, 4/5, …EventScript_ClearTunnelScene`. Talking to Wanda's Boyfriend only sets `FLAG_TEMP_1` | `ShouldDoRusturfTunnelScene()` (`src/field_specials.c:1398-1416`): `!FLAG_RUSTURF_TUNNEL_OPENED` **and** in Rusturf Tunnel **and** (`FLAG_HIDE_RUSTURF_TUNNEL_ROCK_1` → state 4, or `_ROCK_2` → state 5). So: Rock Smash HM + Dynamo Badge, then smash a rock at (24,4)/(24,5) |
| Fly | `ITEM_HM_FLY` / `FLAG_RECEIVED_HM_FLY` | `MAP_ROUTE119` | ‼ **STEP ON (25,31) or (26,31)** → immediate `trainerbattle_no_intro` (no intro box, battle starts at once), then the gift | coord trigger requires `VAR_ROUTE119_STATE == 0`; opponent is `TRAINER_{MAY,BRENDAN}_ROUTE_119_{TREECKO,TORCHIC,MUDKIP}` chosen by `VAR_STARTER_MON` |
| Dive | `ITEM_HM_DIVE` / `FLAG_RECEIVED_HM_DIVE` | `MAP_MOSSDEEP_CITY_STEVENS_HOUSE` | ‼ **WALK IN** — `map_script_2 VAR_STEVENS_HOUSE_STATE, 1, …EventScript_StevenGivesDive` | `VAR_STEVENS_HOUSE_STATE == 1`, set at `MossdeepCity_SpaceCenter_2F/scripts.inc:302` together with `FLAG_DEFEATED_MAGMA_SPACE_CENTER` — i.e. **the Space Center double battle with Steven must be won first** |
| Waterfall | `ITEM_HM_WATERFALL` / `FLAG_RECEIVED_HM_WATERFALL` | `MAP_SOOTOPOLIS_CITY` | **talk** — `SootopolisCity_EventScript_Wallace` | `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`, which needs **both** Maxie and Archie talked to at `VAR_SOOTOPOLIS_CITY_STATE == 5` |

### 3b. Badge required to USE each field move — verbatim from the enum
`src/party_menu.c:120-127` + `:3725` `if (fieldMove <= FIELD_MOVE_WATERFALL && FlagGet(FLAG_BADGE01_GET + fieldMove) != TRUE)`:

`FIELD_MOVE_CUT`→BADGE01 Stone · `FLASH`→BADGE02 Knuckle · `ROCK_SMASH`→BADGE03 Dynamo ·
`STRENGTH`→BADGE04 Heat · `SURF`→BADGE05 Balance · `FLY`→BADGE06 Feather · `DIVE`→BADGE07 Mind ·
`WATERFALL`→BADGE08 Rain.

### 3c. Which HMs are actually load-bearing

* **Never a hard block:** **Fly** (convenience only) and **Flash** (`requires_flash` drives only a
  scanline effect; collision is unchanged).
* **Cut — almost certainly never a hard block, with one open check.** Across the 22 maps I
  enumerated (§4) the only `OBJ_EVENT_GFX_CUTTABLE_TREE` objects are: Petalburg Woods (19,10)(19,11),
  Route 104 (35,22), Route 111 (22,21), Route 118 (38,8), Route 120 (35,32)(20,1)(15,1),
  Route 121 (32,5)(65,4)(26,12). All of those are known shortcuts or optional-area entrances, and
  v1's Lilycove claim is a fabrication (§1 item 7.10). The one that mattered — Route 121, the
  approach to Mt. Pyre, i.e. the very next chapter to be built — is safe, because **Route 122
  (which holds the `MAP_MT_PYRE_1F` warp at (22,29)) has two independent approaches**:
  `Route121 --down/offset 20--> Route122` and `Route118 --> Route123 --up/offset 100--> Route122`.
  A tree on Route 121 therefore cannot hard-block Mt. Pyre.
  ‼ It is still a categorical ABSENCE claim over a subset of maps — the shape this project has been
  burned by — so treat "Cut is never needed" as *strongly supported*, not proven, and confirm with a
  `calculate_path` on the first run that reaches each chapter.
* **Hard blocks, in story order:** Rock Smash — twice, both after the Dynamo Badge: **Route 111
  (18,101)+(19,100)**, the mainline Mauville→Route 112→Fiery Path→Lavaridge route (proved by our own
  `early_game.py:4355-4368`), and **Rusturf Tunnel (24,4)+(24,5)**, which is how you obtain
  Strength at all → **Surf** (Route 118 crossing and all ocean routes) → **Strength + Rock Smash**
  (Seafloor Cavern rooms 1/2/3/5/8; Victory Road B1F) → **Dive** (Route 128 to Seafloor Cavern;
  Route 126 to Sootopolis) → **Waterfall** (Ever Grande City approach to Victory Road).
  Also Rock Smash on the 3 boulders / route rocks listed in §4 where a run needs them.

### 3d. Obstacle mechanics — exact
* **Cuttable trees / breakable rocks are OBJECT EVENTS**, `OBJ_EVENT_GFX_CUTTABLE_TREE` /
  `OBJ_EVENT_GFX_BREAKABLE_ROCK`, removed with `removeobject VAR_LAST_TALKED`
  (`field_move_scripts.inc:30, 89`). Read their **live** `gObjectEvents` coords, not `map.json`.
* **Strength boulders** are `OBJ_EVENT_GFX_PUSHABLE_BOULDER` and are **never removed**. You must
  first set `FLAG_SYS_USE_STRENGTH` (via `EventScript_ActivateStrength`); after that, walking into
  the boulder pushes it (`TryPushBoulder` / `Task_PushBoulder`, `src/field_player_avatar.c`).
* **Currents:** `MB_EASTWARD_CURRENT` / `MB_WESTWARD_CURRENT` / `MB_NORTHWARD_CURRENT` /
  `MB_SOUTHWARD_CURRENT`. Dispatch: `TryDoMetatileBehaviorForcedMovement` →
  `GetForcedMovementByMetatileBehavior` → `ForcedMovement_Pushed*ByCurrent`.
* **Forced sliding** (ice floors, gym pads): `MB_SLIDE_{EAST,WEST,NORTH,SOUTH}` →
  `ForcedMovement_Slide*`. **Slippery ice** is `MB_ICE` → `ForcedMovement_Slip`.
* **Mossdeep Gym pads:** `MB_MOSSDEEP_GYM_WARP`. **Aqua Hideout teleporters:** `MB_AQUA_HIDEOUT_WARP`.
* **Muddy slope:** `MB_MUDDY_SLOPE`; `ForcedMovement_MuddySlope` pushes you SOUTH unless you are
  facing NORTH at `PLAYER_SPEED_FASTEST`. Acro-Bike hop tile is `MB_BUMPY_SLOPE`.
* **Cracked floors:** `MB_CRACKED_FLOOR` → becomes `MB_CRACKED_FLOOR_HOLE`. Fall condition =
  `VAR_ICE_STEP_COUNT` forced to 0 by `CrackedFloorPerStepCallback`, consumed by the map's
  `CaveHole_CheckFallDownHole` `ON_FRAME_TABLE` → `EventScript_FallDownHole` → `warphole`.
  Installed on **`SkyPillar_2F`, `SkyPillar_4F`, `MirageTower_2F`, `MirageTower_3F`** and nowhere
  else among those maps.
* **Sootopolis Gym ice:** thresholds **8 / 28 / 67** on `VAR_ICE_STEP_COUNT` (starts at 1,
  increments per fresh `MB_THIN_ICE`); `MB_CRACKED_ICE` step → 0 → fall. Region x∈[3,13],
  y∈[6,19]; visited bits in `VAR_TEMP_1`…`VAR_TEMP_A`. Stairs are `setmetatile`d at
  (8,15)&(8,16), then (8,10)&(8,11), then (8,4)&(8,5). **Fully restartable — cannot wedge.**
* **Fortree bridges:** `MB_FORTREE_BRIDGE` + `STEP_CB_FORTREE_BRIDGE`. **Pacifidlog logs:**
  `MB_PACIFIDLOG_{VERTICAL,HORIZONTAL}_LOG_*` + `STEP_CB_PACIFIDLOG_BRIDGE`. **Ash grass:**
  `MB_ASHGRASS` + `STEP_CB_ASH`.

### 3e. Correct FLAG_/VAR_ names for the main plot (verified present in our tables)
`ADVENTURE_STARTED`(116) · `SYS_POKEMON_GET`(2144) · `SYS_POKEDEX_GET` · `SYS_POKENAV_GET` ·
`BADGE01_GET`…`BADGE08_GET` · `DEFEATED_{RUSTBORO,DEWFORD,MAUVILLE,LAVARIDGE,PETALBURG,FORTREE,MOSSDEEP,SOOTOPOLIS}_GYM` ·
`DEFEATED_RIVAL_ROUTE103`(130) · `DEFEATED_RIVAL_ROUTE_104`(125) · `DEFEATED_RIVAL_RUSTBORO`(211) ·
`RECOVERED_DEVON_GOODS` · `DELIVERED_DEVON_GOODS` · `DELIVERED_STEVEN_LETTER` ·
`DEFEATED_EVIL_TEAM_MT_CHIMNEY`(139) · `RECEIVED_GO_GOGGLES`(221) · `RECEIVED_CASTFORM`(151) ·
`RECEIVED_DEVON_SCOPE`(285) · `RECEIVED_RED_OR_BLUE_ORB`(212) · `RETURNED_RED_OR_BLUE_ORB`(259) ·
`TEAM_AQUA_ESCAPED_IN_SUBMARINE`(112) · `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`(129) ·
`LEGENDARIES_IN_SOOTOPOLIS`(83, **cleared** at the end) · `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`(158) ·
`MET_ARCHIE_SOOTOPOLIS`(308) · `MET_MAXIE_SOOTOPOLIS`(309) · `DEFEATED_RAYQUAZA`(448) ·
`DEFEATED_MAGMA_SPACE_CENTER` · `DEFEATED_WALLY_MAUVILLE`(190) · `DEFEATED_WALLY_VICTORY_ROAD`(126) ·
`IS_CHAMPION`(2175) · `SYS_GAME_CLEAR`(2148) · `SYS_POKEDEX_GET`(2145) · `SYS_POKENAV_GET`(2146) ·
`RUSTURF_TUNNEL_OPENED`(199) · `HIDE_RUSTURF_TUNNEL_ROCK_1`(931)/`_2`(932) ·
`HIDE_MAGMA_HIDEOUT_GRUNTS` · `HIDE_AQUA_HIDEOUT_GRUNTS` · `HIDE_ROUTE_101_ZIGZAGOON` ·
`RECEIVED_HM_{CUT,FLY,SURF,STRENGTH,FLASH,ROCK_SMASH,WATERFALL,DIVE}`.

Vars: `LITTLEROOT_INTRO_STATE`(146) · `LITTLEROOT_TOWN_STATE`(80) · `ROUTE101_STATE`…`ROUTE134_STATE`(96-129) ·
`OLDALE_TOWN_STATE`(81) · `PETALBURG_CITY_STATE`(87) · `RUSTBORO_CITY_STATE`(90) ·
`SLATEPORT_CITY_STATE`(88) · `MAUVILLE_CITY_STATE`(89) · `LILYCOVE_CITY_STATE`(92) ·
`MOSSDEEP_CITY_STATE`(93) · `SOOTOPOLIS_CITY_STATE`(94) · `BRINEY_LOCATION`(150) ·
`BRINEY_HOUSE_STATE`(144) · `RUSTURF_TUNNEL_STATE`(154) · `METEOR_FALLS_STATE`(191) ·
`WEATHER_INSTITUTE_STATE`(179) · `MT_PYRE_STATE`(185) · `JAGGED_PASS_STATE`(200) ·
`SEAFLOOR_CAVERN_STATE`(162) · `SKY_PILLAR_STATE`(202) · `SKY_PILLAR_RAYQUAZA_CRY_DONE`(215) ·
`SOOTOPOLIS_WALLACE_STATE`(216) · `STEVENS_HOUSE_STATE`(198) · `MOSSDEEP_SPACE_CENTER_STATE`(159) ·
`ELITE_4_STATE`(156) · `VICTORY_ROAD_1F_STATE`(195) · `MIRAGE_TOWER_STATE`(203) ·
`ICE_STEP_COUNT`(34) · `STARTER_MON`(35) · `TRICK_HOUSE_LEVEL`(68) · `TRICK_HOUSE_PUZZLE_1_STATE`…`_8_STATE`(171-178).

### 3f. `VAR_SOOTOPOLIS_CITY_STATE` — the complete verified state machine (NEW)

Seven states, not five. Every setter located by
`gh api "search/code?q=VAR_SOOTOPOLIS_CITY_STATE+repo:pret/pokeemerald"` then read. **This is the
spine of the next build phase's final chapter — use this table, not either note's.**

| value | meaning | set by | what the city looks like |
|---|---|---|---|
| **0** | pre-crisis | initial | `…EventScript_SetNormalLayout` + `SetNormalWeather` (`:68,85`) |
| **1** | Kyogre awakened in Seafloor Cavern. On entering Sootopolis, `map_script_2 …, 1` fires `…EventScript_StartLegendariesScene` | `data/maps/SeafloorCavern_Room9/scripts.inc:116` | legendaries layout + **downpour** (`:70,87`) |
| **2** | the Groudon-vs-Kyogre cutscene has played. Steven now says "help Wallace" (`:877`) | `SootopolisCity/scripts.inc:243` (arrived via the Poké Center) **or** `:342` (arrived via Dive) — two separate camera-pan variants, both landing on 2 | legendaries layout, abnormal weather |
| **3** | Wallace met in the Cave of Origin → go to Sky Pillar. `SkyPillar_Outside` `map_script_2 …, 3` runs `…EventScript_WallaceScene` | `data/maps/CaveOfOrigin_B1F/scripts.inc:55` | legendaries layout |
| **4** | Wallace has opened the Sky Pillar door. Talking to Wallace in Sootopolis now gives `…EventScript_GoToSkyPillar` (`:1278`) | `data/maps/SkyPillar_Outside/scripts.inc:82` | legendaries layout |
| **5** | **Rayquaza awakened.** Back in Sootopolis every NPC has Rayquaza dialogue and — critically — **Maxie and Archie are talkable** (`:1333,1348`), which is the only route to `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` → Waterfall + unlocked Gym/house doors | `data/maps/SkyPillar_Top/scripts.inc:126` — `SkyPillar_Top_EventScript_AwakenRayquaza` (:87), which in the same breath sets `VAR_SKY_PILLAR_STATE = 1` (:127) and `VAR_SKY_PILLAR_RAYQUAZA_CRY_DONE = 1` (:128) | `…EventScript_SetOutsideGymObjPos` (`:48`) |
| **6** | **crisis fully over** | `data/maps/SootopolisCity_Gym_1F/scripts.inc:102` — i.e. **defeating Juan** | back to `SetNormalLayout` + `SetNormalWeather` (`:69,86`); `…SetExpertBlockCaveEntrance` (`:49`) |

Two consequences a bot must encode:
* **The awakening trigger is a coord tile, (14,9) on `MAP_SKY_PILLAR_TOP`**, gated
  `VAR_SKY_PILLAR_RAYQUAZA_CRY_DONE == 0` — not an interaction with the Rayquaza sprite.
* Because state only becomes 5 at the top of Sky Pillar, `VAR_SKY_PILLAR_STATE` is **0 for the
  entire mandatory climb** → clean layouts → no Mach Bike (§0.4).

### 3g. The Seafloor Cavern → Sootopolis handoff, verbatim (NEW)

`data/maps/SeafloorCavern_Room9/scripts.inc` —
`SeafloorCavern_Room9_EventScript_ArchieAwakenKyogre` (`:4`) is the whole climax in one script.

* The battle is **`trainerbattle_no_intro TRAINER_ARCHIE`** (`:29`) — no intro message box, so the
  bot must already be battle-ready when the script starts. Same pattern as the Route 119 rival.
* On completion it writes this block atomically (`:115-132`) — **these are the observables**:
  `VAR_ROUTE128_STATE = 1` · `VAR_SOOTOPOLIS_CITY_STATE = 1` · `VAR_SEAFLOOR_CAVERN_STATE = 1` ·
  `VAR_STEVENS_HOUSE_STATE = 2` · `setflag FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` ·
  `setflag FLAG_LEGENDARIES_IN_SOOTOPOLIS` · `setflag FLAG_SYS_WEATHER_CTRL` ·
  `setflag FLAG_HIDE_SEAFLOOR_CAVERN_ROOM_9_ARCHIE` ·
  `clearflag FLAG_HIDE_SOOTOPOLIS_CITY_{STEVEN,ARCHIE,MAXIE,RESIDENTS,GROUDON,KYOGRE}` ·
  `clearflag FLAG_HIDE_ROUTE_128_{ARCHIE,MAXIE}` · `setflag FLAG_HIDE_SOOTOPOLIS_CITY_MAN_1` ·
  `setflag FLAG_HIDE_MOSSDEEP_CITY_STEVENS_HOUSE_STEVEN`.
* **Best "Seafloor Cavern done" check:** `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` (id 129) or
  `VAR_SEAFLOOR_CAVERN_STATE == 1`. Note this **confirms `FLAG_LEGENDARIES_IN_SOOTOPOLIS` is set
  here and cleared at the end** — it is a "crisis ACTIVE" flag.
* ‼ **This script sets `VAR_STEVENS_HOUSE_STATE = 2`, and the HM Dive gift requires state == 1.**
  Reaching Seafloor Cavern therefore closes the Dive gift permanently. In vanilla you cannot get
  there without Dive, so it is not reachable damage — but it means the Dive gift is a
  **state-window gift, not an idempotent one**, and any future save-state or warp shortcut that
  skips Steven's house would destroy it silently.

### 3h. ‼ EVERY `multichoice` ON THE CRITICAL PATH (NEW — complete sweep)

`gh api "search/code?q=multichoice+repo:pret/pokeemerald+path:data/maps&per_page=100"` → **49 files**.
After excluding Battle Frontier / Battle Tents / Contest lobbies / Dept. Store / Game Corner /
Trick House / Trainer Hill / museums / flavour NPCs, these are the ones a story bot **must** answer.
**A blind A-press gets the WRONG option in three of the four.**

| map / script | menu | default cursor | correct index | what happens on a wrong pick |
|---|---|---|---|---|
| **`CaveOfOrigin_B1F_EventScript_WheresRayquaza`** | `multichoice 0, 0, MULTI_WHERES_RAYQUAZA, FALSE` (=110) | **0** = "Cave of Origin" (**wrong**) | **2 = "Sky Pillar"** | ‼ **every other case `goto`s straight back to the same prompt** — cases 0, 1, 3, the `switch` default, **and B-press** (there is no `case MULTI_B_PRESSED`, so B falls through to `…DontRemember` → loop). No counter, no timeout, no state change: **an unbounded derail loop** |
| **`Route104_MrBrineysHouse`** (`:42`) | `multichoicedefault 20, 8, MULTI_BRINEY_OFF_DEWFORD, 1, FALSE` (=14) | **1** = decline (**wrong**) | **0 = sail to Dewford** | case 1 and `MULTI_B_PRESSED` → `…DeclineSailing`; recoverable (re-talk), but a blind A-press **never boards the boat** |
| **`DewfordTown`** (`:15`) | `multichoicedefault 21, 6, MULTI_BRINEY_ON_DEWFORD, 2, FALSE` (=0) | **2** = cancel (**wrong**) | **1 = Slateport** (0 = Petalburg) | case 2 and `MULTI_B_PRESSED` → `…CancelSailSelect`; recoverable, but a blind A-press **cancels** |
| **`MauvilleCity_BikeShop`** (`:24`) | `multichoice 21, 8, MULTI_BIKE, TRUE` (=12) | 0 | **0 = Mach Bike** (1 = Acro) | cancellable and freely swappable later, but Mach is the one needed for `MB_CRACKED_FLOOR` (post-game Sky Pillar, Mirage Tower 2F/3F) and `MB_MUDDY_SLOPE` |

Answering the Cave of Origin correctly is what actually unblocks the endgame — index 2 runs
`…EventScript_AtSkyPillar` (`:49-59`): `setflag FLAG_WALLACE_GOES_TO_SKY_PILLAR` ·
`setvar VAR_SOOTOPOLIS_CITY_STATE, 3` · `removeobject LOCALID_CAVE_OF_ORIGIN_WALLACE` ·
`clearflag FLAG_HIDE_SKY_PILLAR_WALLACE`. `FLAG_WALLACE_GOES_TO_SKY_PILLAR` is exactly what
`SkyPillar_Outside_OnLoad` tests to open the Sky Pillar door.

Also worth knowing: the irreversible **Scanner → Deep Sea Tooth *or* Scale** choice (§1 item 8.19)
is a `multichoice` in `SlateportCity_Harbor/scripts.inc`, and `Route113_GlassWorkshop`,
`FortreeCity_House2` (TM Hidden Power: **Right, Right, Left**) and
`Route124_DivingTreasureHuntersHouse` are optional-but-menu-driven.

**Prevention rule:** never resolve a `multichoice` with a blind A-press. Read the menu id, drive the
cursor to a known index, and bound the interaction with a distinct failure mode — because the one
menu on the mandatory path that cannot be escaped is also the one where the default is wrong.

### 3i. ‼ COMPLETE CENSUS OF NON-MONOTONIC FLAGS (NEW — absent from both generations)

`gh api "search/code?q=%22clearflag+FLAG_DEFEATED%22+repo:pret/pokeemerald"` → **3 files**;
`…FLAG_RECEIVED…` → **2 files**; `…FLAG_MET…` → **0**. That is the whole population, so this list
is exhaustive for the `DEFEATED_` / `RECEIVED_` / `MET_` families. **Every one of these passes
`audit_flag_names.py` and is still unsafe to use as a milestone.**

| flag(s) | cleared by | consequence for a bot |
|---|---|---|
| `FLAG_DEFEATED_MAGMA_SPACE_CENTER` | `MossdeepCity_SpaceCenter_2F_EventScript_RivalRayquazaCall` | **worst case.** True only between the Steven double battle and the rival's PokéNav call. Use `VAR_MOSSDEEP_SPACE_CENTER_STATE == 3`, `VAR_STEVENS_HOUSE_STATE` or `FLAG_RECEIVED_HM_DIVE` |
| `FLAG_DEFEATED_ELITE_4_SIDNEY` / `_PHOEBE` / `_GLACIA` / `_DRAKE` | `EverGrandeCity_HallOfFame_EventScript_ResetEliteFour` (`data/event_scripts.s:628-632`) | **E4 progress flags are wiped on entering the Hall of Fame.** They can never mean "I have beaten the Elite Four". Use `FLAG_IS_CHAMPION`(2175) / `FLAG_SYS_GAME_CLEAR`(2148); use `VAR_ELITE_4_STATE`(156) for in-run room progress |
| `FLAG_DEFEATED_MEW`, `_LATIAS_OR_LATIOS`, `_DEOXYS`, `_LUGIA`, `_HO_OH` | `data/scripts/hall_of_fame.inc:28-32` | event legendaries are deliberately re-enabled post-game. Cross-check with `CLAUDE-VALIDATED-concepts-round1.md`, which already found `FLAG_DEFEATED_LATIAS_OR_LATIOS` is written only by the Southern Island script and is NOT what the roamer clears |
| `FLAG_RECEIVED_SHOAL_SALT_1..4`, `_SHELL_1..4`, `FLAG_SYS_SHOAL_ITEM` | `ShoalCave_LowTideEntranceRoom_EventScript_ResetShoalItems` | daily reset — these are renewable, not one-time |
| `FLAG_RECEIVED_FANCLUB_TM_THIS_WEEK` | `PacifidlogTown_House2_EventScript_ClearReceivedFanClubTM` | weekly reset — confirms the round-1 finding that the Pacifidlog TM is a renewable friendship gift, not a trade |

Also worth knowing from the same file: `hall_of_fame.inc` sets `VAR_STEVENS_HOUSE_STATE, 2`
(:11) — which is why `MossdeepCity_StevensHouse_EventScript_SetStevenPos` branches on state 2 —
and `clearflag FLAG_HIDE_MOSSDEEP_CITY_STEVENS_HOUSE_BELDUM_POKEBALL` (:40), i.e. **the Beldum gift
only becomes available after the Hall of Fame.**

**Prevention rule this earns:** existence in `event_flags/emerald.txt` proves a name is *readable*;
it does not prove the flag is *monotonic*. Before gating a story segment on any
`FLAG_DEFEATED_*` / `FLAG_RECEIVED_*`, grep the decomp for a `clearflag` of that exact name.

---

## 4. OBSTACLE CENSUS — every boulder / breakable rock / cuttable tree on the maps I checked
Read directly from each `data/maps/<Map>/map.json` `object_events`. `B`=`PUSHABLE_BOULDER`,
`R`=`BREAKABLE_ROCK`, `T`=`CUTTABLE_TREE`.

| map | count | coordinates |
|---|---|---|
| `VictoryRoad_1F` | 0 | — |
| `VictoryRoad_B1F` | 8B + 6R | B (20,5)(21,4)(4,7)(9,10)(20,26)(21,25)(35,6)(34,4) · R (19,5)(20,4)(18,12)(20,25)(21,26)(34,3) |
| `VictoryRoad_B2F` | 0 | — |
| `SeafloorCavern_Room1` | 2B + 1R | B (5,11)(12,11) · R (5,10) |
| `SeafloorCavern_Room2` | 6B + 2R | B (13,3)(10,3)(13,5)(4,5)(7,4)(4,8) · R (8,7)(9,3) |
| `SeafloorCavern_Room3` | 7B | (13,10)(11,10)(12,9)(12,7)(11,8)(12,11)(13,8) |
| `SeafloorCavern_Room5` | 4B + 2R | B (3,11)(4,11)(11,7)(12,8) · R (3,13)(13,8) |
| `SeafloorCavern_Room8` | 12B | (4,7)(5,7)(6,7)(3,6)(7,6)(4,5)(5,5)(6,5)(3,4)(4,4)(6,4)(7,4) |
| `SeafloorCavern_Room{4,6,7,9}` | 0 | — |
| `MagmaHideout_1F` | 3B | (5,22)(7,22)(6,23) |
| `MagmaHideout_{2F_1R,2F_2R,2F_3R,3F_1R,3F_2R,3F_3R,4F}` | 0 | — |
| `GraniteCave_B1F` | 0 | — |
| `GraniteCave_B2F` | 7R | (5,14)(3,14)(2,16)(7,12)(4,22)(6,22)(3,21) |
| `RusturfTunnel` | 2R | (24,5)(24,4) |
| `Route111` | 2R + 1T | R (18,101)(19,100) · T (22,21) |
| `Route114` | 5R | (12,43)(29,53)(30,54)(22,69)(11,64) |
| `Route115` | 1R | (29,50) |
| `Route104` | 1T | (35,22) |
| `PetalburgWoods` | 2T | (19,10)(19,11) |
| `Route118` | 1T | (38,8) |
| `Route120` | 3T | (35,32)(20,1)(15,1) |
| `Route121` | 3T | (32,5)(65,4)(26,12) |
| `Route110`, `FortreeCity`, `LilycoveCity`, `EverGrandeCity` | 0 | — |

**Useful topology read from the same `map.json`s** (for reasoning about hard blocks):
`Route111`: down→`MAUVILLE_CITY`, left/0→`ROUTE113`, left/20→`ROUTE112`.
`Route112`: up/-60→`ROUTE113`, left/40→`LAVARIDGE_TOWN`, right/-20→`ROUTE111`; warps to
`ROUTE112_CABLE_CAR_STATION` (28,27)(29,27), `JAGGED_PASS` (6,46)(7,46), `FIERY_PATH` (11,36)(22,10).
`Route121`: down/20→`ROUTE122`, left/-80→`ROUTE120`, right/-10→`LILYCOVE_CITY`; warp
`ROUTE121_SAFARI_ZONE_ENTRANCE` (37,5).
`Route122`: up/-20→`ROUTE121`, down/-100→`ROUTE123`; warp **`MT_PYRE_1F` (22,29)**.
`Route123`: up/100→`ROUTE122`, left/0→`ROUTE118`; warp `ROUTE123_BERRY_MASTERS_HOUSE` (22,6).
`EverGrandeCity` warps: `POKEMON_LEAGUE_1F` (18,5), `POKEMON_CENTER_1F` (27,48),
**`VICTORY_ROAD_1F` (18,41) and (18,27)** — the entrance and the exit, both on the city map.
`VictoryRoad_1F` → `EVER_GRANDE_CITY` at (15,40) and (39,5); `VictoryRoad_B2F` → **only** `B1F`.

---

## 5. DO NOT USE — wrong or hallucinated, stated explicitly

**Files / symbols that do not exist**
* `src/field_move.c` — no such file.
* `CheckUseCut`, `CheckUseFly`, `CheckUseSurf`, `CheckUseStrength`, `CheckUseFlash`,
  `CheckUseRockSmash`, `CheckUseWaterfall`, `CheckUseDive` — 0 hits. v1's s7 cites these as its
  source for the badge table on all eight rows (also mislabelled as living in
  `src/field_effect_helpers.c`).
* `TryCutTree`, `TrySmashRock`, `DoRockSmashWildEncounter`, `PlayerAvatar_DoPushBoulder`,
  `PushObject`, `CheckForForcedMovement`, `MovePlayerAvatarUsingForcedMovement` — 0 hits.
* `Common_EventScript_PushableBoulder`, `SkyPillar_3F_EventScript_CrackedFloor`,
  `SkyPillar_5F_EventScript_CrackedFloor`,
  `SootopolisCity_CaveOfOrigin_Entrance_EventScript_Wallace`,
  `MauvilleCity_House1_EventScript_RockSmashGuy`,
  `RustboroCity_EventScript_GivePokenav`, `PetalburgCity_EventScript_NormanAdvice` (unverified),
  `MtChimney_EventScript_DefeatMaxie`, `MagmaHideout_4F_EventScript_Maxie`,
  `SlateportCity_Harbor_EventScript_ArchieSubmarine`,
  `SeafloorCavern_Room9_EventScript_Archie`, `Route119_EventScript_RivalDefeated` — none confirmed;
  treat every unverified `*_EventScript_*` label in either note as a guess.
* `MAP_LILYCOVE_CITY_AQUA_HIDEOUT_ENTRANCE` — no such map (`AquaHideout_1F/B1F/B2F`).
* `MAP_SOOTOPOLIS_CITY_CAVE_OF_ORIGIN_ENTRANCE` — not where Waterfall comes from.

**Mechanics claims that are false**
* "Cut is required to enter the Aqua Hideout" — the entrance is a **Surf** warp at (70,5) elev 1,
  and `LilycoveCity/map.json` has zero cuttable-tree objects. (v2's broader "Cut is strictly
  optional for game completion" is very likely right but is an absence claim — see §3c for the one
  path check still owed, on Route 121.)
* "Flash is required to traverse Granite Cave / Victory Road" — rendering only.
* "The waterfall is inside Victory Road B2F" — B2F's every warp returns to B1F.
* "Strength needs the 6th badge in Emerald" — it is BADGE04.
* "Whirlpools block Route 124/126" — no whirlpool mechanic exists in Emerald.
* "`VAR_ICE_STEP_COUNT` is initialised to the tile count and decremented; reach the stairs at 0" —
  inverted; 0 means you fell.
* "Sky Pillar cracked floors are on 3F/5F" — 2F/4F.
* "Mirage Tower uses `MB_MUD_SLOPE`, insufficient speed acts as a solid wall" — it uses
  `MB_CRACKED_FLOOR` on 2F/3F, and muddy slopes push you back south rather than blocking.
* "The Mach Bike is needed for the story Sky Pillar climb" — the story climb is on the CLEAN layout.
* "Granite Cave B1F has an Emerald-exclusive boulder puzzle" — B1F has zero boulders.
* "`FLAG_DEFEATED_<CITY>_GYM` is another name for `FLAG_BADGE0n_GET`" — two distinct flags.
* "Rock Smash requires beating Wattson to obtain" / "Wally's uncle gives it" — no prerequisite,
  and the giver is the Rock Smash Dude in `MauvilleCity_House1`.
* "Norman must be beaten to get Fly" / "a Weather-Institute flag gates Fly" — the gate is
  `VAR_ROUTE119_STATE == 0` on a coord trigger.

**Names that EXIST but must not be used as milestones** (they are cleared — full list in §3i)
* `FLAG_DEFEATED_MAGMA_SPACE_CENTER` — v2 offers it as the Dive gate; it is cleared by the rival's
  Rayquaza PokéNav call.
* `FLAG_DEFEATED_ELITE_4_{SIDNEY,PHOEBE,GLACIA,DRAKE}` — wiped at the Hall of Fame.
* `FLAG_DEFEATED_{MEW,LATIAS_OR_LATIOS,DEOXYS,LUGIA,HO_OH}` — deliberately re-enabled post-game.
* `FLAG_LEGENDARIES_IN_SOOTOPOLIS` — **cleared** when the crisis resolves, so it is a "crisis is
  ACTIVE" flag, not a "crisis is done" flag.

**Invented permanence — building an interrupt for any of these is wasted work (s8)**
* "The Master Ball / Aqua Hideout is lost after Kyogre; Wailmer block it permanently" (v1) —
  inverted; the Wailmer wall exists only *before* Aqua flees.
* "The TM Thief giver despawns after the museum segment / after Archie" (**both**) — he is hidden
  only by his own post-gift exit script.
* "TM Earthquake is permanently missable; the Seafloor Cavern entrance ceases to exist" (v2) —
  the dive warp is unconditional and the blocking tiles become `MB_DEEP_WATER`.
* "The Magma Hideout entrance seals after the Mossdeep Space Center" (v2) —
  `VAR_JAGGED_PASS_STATE` is never lowered.
* "The unchosen fossil is lost forever" (v1) — recoverable at the Desert Underpass post-HoF.
* "Mirage Tower collapses if you leave without a fossil" (v1) — the collapse script is reachable
  only from the two pickup scripts.
* "Only one of two Berry-Master's-wife special berries per save" (v1) — all five, one per day.
* "The S.S. Tidal's pre-E4 trainers/Leftovers are lost when you become Champion" (v1) — the ship
  does not exist until the Hall of Fame.
* "TM Skill Swap is an NPC gift on Mt. Pyre Exterior" (v1) — it is an item ball at (19,40).
* "The Johto starter needs the Hoenn Dex *seen*" (v1) — it needs `HasAllHoennMons`, i.e. **caught**.
* "Trick House puzzles 1-7 are lost when you finish puzzle 8" (v1) — each is lost individually and
  far earlier, the moment that puzzle is cleared.
* `src/ss_tidal.c`, `src/prof_birch.c` — both 404.
  `src/fldeff_misc.c::UpdateMirageIsland()` — file exists, function does not.
  `is_stadium_and_mt_pyre_cleared()`, `is_kyogre_awakened()` — invented; the decomp uses
  `goto_if_set FLAG_…`.

**Do not read a value out of these tables** — both generations' `VAR_LITTLEROOT_TOWN_STATE` and
`VAR_SOOTOPOLIS_CITY_STATE` value lists disagree with each other and (for Sootopolis) with the
script. Re-derive from `scripts.inc` when you need them.

---

## 6. MODEL COMPARISON — is re-running the other tainted rounds worth the tokens?

**Yes. Gemini 3.1-pro (v2) was measurably and substantially more accurate than 2.5-pro (v1) on
these topics — and, more usefully, its uncertainty markers are calibrated where v1's are not.**

Hard numbers from this session:

| metric | v1 (2.5-pro) | v2 (3.1-pro) |
|---|---|---|
| phantom `FLAG_`/`VAR_` names in s10 | **18 / 51 (35%)** | **4 / 38 (11%)** |
| head-to-head disagreements ruled, s7/s9/s10 | **v2 won 13, v1 won 0** (v1 "essentially right" once, 9.16), both wrong 9 | |
| head-to-head disagreements ruled, s8 | **v2 won 8, v1 won 1** (8.17, the which-hand mechanic), both wrong 6 | |
| the designated calibration question (HM07 Waterfall) | **fabricated map + fabricated script label, tagged VERIFIED** | **map and script label exactly right** |
| fabricated C symbols / files | 8 of 10 in s7/s9, plus `src/ss_tidal.c`, `src/prof_birch.c`, `fldeff_misc.c::UpdateMirageIsland()` in s8 | 2 of 10 |
| character-exact script labels | rare | `SootopolisCity_EventScript_Wallace`, `MauvilleCity_House1_EventScript_RockSmashDude`, `DewfordTown_Hall_EventScript_SludgeBombMan`, `LavaridgeTown_EventScript_EggWoman`, `Route113_GlassWorkshop_EventScript_GlassWorker`, `MossdeepCity_StevensHouse_EventScript_BeldumPokeball` |
| hedges that turned out to be the *correct* answer | — | `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN`, `VAR_ROUTE119_STATE`, `MAP_MAUVILLE_CITY_HOUSE1` |
| **inverted permanence claims** (the costliest error class) | **5** — Master Ball lost, TM Thief lost, fossil lost forever, Mirage Tower collapses, S.S. Tidal lost at Champion | **3** — TM Earthquake missable, Magma Hideout seals, TM Thief lost |

Three caveats that matter for how you spend the tokens:

1. **v2's remaining errors are systematic, not random** — it invented an entire consistent
   `ITEM_HM01_CUT` / `FLAG_RECEIVED_HM01` naming scheme (9 phantoms from one wrong premise). One
   `audit_flag_names.py`-style sweep kills a whole family at once, which makes v2 output *cheap to
   repair*. v1's errors are scattered fabrications that must each be checked individually.
2. ‼ **But v2's failure mode is more DANGEROUS where it matters.** v1 mostly hallucinates in
   *citations*; v2 hallucinates in the *actionable* section. All three of v2's "the bot must hardcode
   an interrupt here" architectural constraints (TM Earthquake, Magma Hideout, TM Thief) rest on
   false permanence claims — i.e. its most confident, most build-shaping output was its least
   reliable. Grade 3.1-pro's *names* highly and its *architectural advice* not at all.
3. **Where both generations agree, they are still wrong ~35% of the time** on this material
   (15 BOTH-WRONG rulings across the four topics, plus agreed-but-false items like the whirlpools,
   the "talk to the NPC" HM mechanism, and "TM Thief is missable" — which both got wrong in the
   *same* direction). **Agreement between generations is not evidence.** The disagreement-targeting
   heuristic worked well as a *search strategy* — it found the fabrications fast — but it must never
   be used as a *confidence* signal.

**Recommendation:** re-run the tainted item/concept rounds on 3.1-pro — the phantom-name rate alone
(35% → 11%) pays for it — but budget a Claude validation pass on top of every one, and treat any
"your bot must therefore do X" sentence as unvalidated regardless of generation. The cost curve
improved; the requirement did not change.

---

## 7. METHOD — what I grounded, what I did not, what blocked me

**Grounded (fetched and read this session):**
`data/maps/` `scripts.inc` for RustboroCity_CuttersHouse, PetalburgCity_WallysHouse,
PetalburgCity_Gym, MauvilleCity_House1, RusturfTunnel, GraniteCave_1F, Route119, SootopolisCity
(1400 lines), SootopolisCity_Gym_1F, MossdeepCity_StevensHouse, MossdeepCity_SpaceCenter_2F,
SkyPillar_1F/2F/4F/Top, MirageTower_1F/2F/3F/4F; `map.json` for Route119, RusturfTunnel,
SkyPillar_Top, EverGrandeCity, LilycoveCity, VictoryRoad_1F/B1F/B2F, SeafloorCavern_Room1-9,
MagmaHideout ×8, GraniteCave_1F/B1F/B2F/StevensRoom, Route111/112/114/115/110/118/120/121/104,
PetalburgWoods, FortreeCity, MeteorFalls_1F_1R; `data/scripts/field_move_scripts.inc`,
`data/scripts/cave_hole.inc`; `include/constants/metatile_behaviors.h` (complete);
`src/party_menu.c`, `src/field_player_avatar.c`, `src/field_tasks.c`, `src/field_specials.c`,
`src/overworld.c` (targeted regions); the `data/maps` and `src` directory listings;
10 × `gh api search/code` existence checks. Plus both local tables, `audit_flag_names.py`, and our
own already-validated traversal code `sandbox-pokebot/modules/story/early_game.py` (used as the
oracle for "is this obstacle on the mainline path", which the decomp alone cannot answer).

**s8 was grounded by a delegated Claude subagent** with the same tool access (real `gh api` fetches +
our local tables); its rulings are reproduced in §1/s8 with the file and line it read for each. Its
own NOT-GROUNDED list is carried over verbatim at the end of that section — most importantly **every
coordinate in either s8 note is unverified.** It reached 25 rulings across ~60 tool calls, including
decoding `data/tilesets/secondary/underwater/metatile_attributes.bin` to settle the Seafloor Cavern
re-entry question at the metatile-behaviour level.

**Not grounded — still LEADS, do not build on them:**
* `s1`–`s6` (Mt. Pyre, the two hideouts, Routes 120-123, Seafloor Cavern/Cave of Origin story,
  Gyms 7-8 battle specifics, Victory Road/E4/Champion rosters) — out of scope this round. Note
  though that §3g/§3f/§3h already cover the Seafloor Cavern climax, the Sootopolis state machine and
  the Cave of Origin question, which is most of what `s4` would be relied on for.
*(The `multichoice` sweep was completed during this session — all 49 sites enumerated, the four
critical-path menus resolved with their correct indices, in §3h.)*
* s9's Trick House per-puzzle mechanics and Desert Ruins braille sequence — I only invalidated the
  var names, not the procedures.
* s10's `VAR_LITTLEROOT_TOWN_STATE` and early-game state machines — the two generations contradict
  each other and I did not fetch `LittlerootTown/scripts.inc`.
* Whether `VAR_TEMP_*` are cleared on the Sootopolis-Gym 1F→B1F fall specifically (I know they are
  temp vars and that `OnTransition` re-seeds `VAR_ICE_STEP_COUNT` to 1, which is enough to
  conclude the puzzle restarts, but I did not read the temp-var clear site).
*(The "are other flags non-monotonic?" follow-up was closed during this session — see §3i, which is
an exhaustive census for the `DEFEATED_`/`RECEIVED_`/`MET_` families.)*

**What blocked me:** nothing hard. `gh api search/code` is rate-limited (~1 req/2 s) so existence
checks were serialised. Map *layouts* are binary (`data/layouts/*/map.bin`), so tile-level
questions — "is there an `MB_WATERFALL` tile at the Ever Grande approach", "are the Route 111 rocks
on the only path" — cannot be settled from GitHub alone and need a live probe. Everything derived
from `object_events` / `warp_events` / `coord_events` / `requires_flash` in `map.json` **is**
decidable from the decomp, and that is where §4 comes from.
