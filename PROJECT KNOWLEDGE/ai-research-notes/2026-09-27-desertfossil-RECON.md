# 2026-09-27 — Desert fossil (#27-desertfossil): Mirage Tower decomp recon — a NOTE

> ⛔ **A NOTE, NOT A SOURCE OF TRUTH.** One read-only Claude agent (recon), then a second one told to REFUTE each
> key claim against the decomp / logs / code (verification). Line numbers refer to the branch `wt/r20fly` or the
> running sandbox as each section says. Verify a load-bearing claim yourself before code depends on it.

## Recon

DESERT FOSSIL (#27-desertfossil): DECOMP RECON. This is a NOTE, not truth. Decomp = pret/pokeemerald master, fetched 2026-09-27. Nothing was edited or run in sandbox-pokebot.

REFERENT: Mirage Tower on Route 111 (MEASURED). Its door is Route111 warp 3 at (19,58), leading to MAP_MIRAGE_TOWER_1F.

1. WHEN IT APPEARS (MEASURED). It is NOT a daily event. `SetMirageTowerVisibility` (src/mirage_tower.c:315-340) flips a 50/50 coin (`Random() & 1`) every time Route111's OnTransition runs (Route111/scripts.inc:42). That includes crossing a map seam, because LoadMapFromCameraTransition runs OnTransition (overworld.c:807).
- If the coin says hidden, the map is swapped to `LAYOUT_ROUTE111_NO_MIRAGE_TOWER` (scripts.inc:43,87-89).
- Entering 1F sets FLAG_FORCE_MIRAGE_TOWER_VISIBLE (MirageTower_1F/scripts.inc:7). The tower then stays up until you enter Mauville, Route 112 or Route 113, which clear that flag.
- Once VAR_MIRAGE_TOWER_STATE is non-zero, the tower is always hidden (mirage_tower.c:320-325).
- Our flag and var ids match the decomp: flags 157, 334, 335, 336, 267 and 874; vars 196, 197 and 203 (flags.h:179,293,362-364,925; vars.h:216,217,223).

2. REQUIREMENTS
- Go-Goggles (MEASURED). The Route 111 sandstorm triggers run `checkitem ITEM_GO_GOGGLES` and push you back if you lack them (Route111/scripts.inc:189-203). The rival hands them over automatically outside the Lavaridge gym after Badge 4: Gym_1F:62 sets the badge, :68 sets VAR_LAVARIDGE_TOWN_STATE=1, then LavaridgeTown:41 and :62-63 give the item.
- Mach Bike, needed on 2F ONLY. MEASURED from the layout data with my own static BFS script, not a live probe.
  - 2F has 11 cracked tiles. The 3F warp cannot be reached without crossing at least 4 of them: (3,7), (2,8), (2,9), (2,10).
  - 3F does have cracked tiles, at (17,6), (16,7) and (18,7), but none are on the required path.
  - The fall rule is field_tasks.c:824-827: stepping on a cracked tile at any speed other than PLAYER_SPEED_FASTEST drops you. Only the Mach Bike at bikeFrameCounter 2 reaches that speed (bike.c:1029-1030, 237-240).
- Rock Smash (MEASURED, static BFS). The rocks at 3F (3,7) and (4,8) and at 4F (6,7) block the only corridor. Without smashing them, BFS reaches neither the 4F warp nor the fossils.
- Repel is advised. Every floor has encounter rate 10, with Sandshrew and Trapinch at Lv20-24 (wild_encounters.json). INFERRED: a battle in the middle of the crossing stops the bike.

3. FLOOR LAYOUT (MEASURED, from the map.json files)
- 1F: enter at (10,14), stairs at (15,2). No floor mechanic.
- 2F: arrive at (15,2), exit at (18,12). Holes drop you to 1F.
- 3F: arrive at (18,12), exit at (2,4). Holes drop you to 2F.
- 4F: arrive at (1,4). The Root Fossil object is at (5,4) and the Claw Fossil object at (7,4). From (6,4), facing West picks Root and facing East picks Claw. Upstream's solver stops exactly at (6,4) (puzzle_solver.py:139).

4. THE CHOICE AND WHAT FOLLOWS (MEASURED)
- Taking a fossil is a YES/NO prompt. NO leaves it and changes nothing (4F/scripts.inc:19-22).
- YES gives ITEM_ROOT_FOSSIL or ITEM_CLAW_FOSSIL, hides both fossil objects, sets FLAG_CHOSE_ROOT_FOSSIL or FLAG_CHOSE_CLAW_FOSSIL, shakes the camera, sets VAR_MIRAGE_TOWER_STATE=1 and warps you to Route111 (19,59) (4F/scripts.inc:4-57).
- Back on Route 111, a locked OnFrame cutscene disintegrates the tower, sets the state to 2, clears FLAG_HIDE_DESERT_UNDERPASS_FOSSIL and shows a message box (Route111:103-131). The next time you enter Route 111 the state becomes 3 (:45,91-93).
- The tower collapses only when you take a fossil. The other fossil is recoverable after the Hall of Fame (already validated in CLAUDE-VALIDATED-story-round1 rows 8.6 and 8.7).

5. REVIVING THE FOSSIL (MEASURED)
- Where: the Fossil Scientist on Devon Corp 2F at (14,8). He is always present (his object flag is 0).
- The only access gate is the 1F stair guard, who lets you up once FLAG_RETURNED_DEVON_GOODS is set (DevonCorp_1F:5-12).
- Hand over the fossil: VAR_FOSSIL_RESURRECTION_STATE becomes 1.
- It becomes 2 when you re-enter 2F, or when you talk to any other scientist on that floor (DevonCorp_2F:5-11).
- Talk to him again to receive Lileep or Anorith at Lv20 (:142,187). There is a nickname prompt, and the Pokémon goes to the PC if the party is full (:143-145).

6. EARLIEST STORY POINT
- Any time after Badge 4 (MEASURED gate: the Go-Goggles). The bot also needs the Mach Bike (Rydel checks only FLAG_RECEIVED_BIKE and FLAG_DECLINED_BIKE, BikeShop:7-8) and a Rock Smash user (Badge 3).
- INFERRED: the desert is a detour off the Lavaridge-to-Mauville leg (12-STORYMODE-DESIGN.md:97-104). The Devon revival could ride along with the Norman trip, since Rustboro is next to Petalburg.

7. RISKS
- R1, the bot has no bike: sootopolis.py:1362 records it as bikeless (MEASURED-PROD). The bike is not auto-registered, because the BikeShop script has no `registeritem`. Upstream `mount_bike` loops forever if there is no bike (puzzle_solver.py:39-42). Both the bike pickup and registering it to Select have to be built.
- R2, the pathfinder ignores cracked floors: map_path.py has 0 hits for "Cracked" (MEASURED). It will plan across 2F at walking speed and fall to 1F. A fall can be retried, because 2F re-fixes its floor on entry (2F/scripts.inc:3), but the retry loop must be bounded. This is the #24-crackedfloorpathfinder item.
- R3, momentum: the counter drops whenever the D-pad is released (bike.c:249-250). The minimal 2F route makes 3 turns inside the crossing. Whether a turn keeps full speed is INFERRED from bike.c:160-176. Probe it live before trusting it.
- R4, the layout swap and the phantom warp: map_path adds warps from map_data.warps without checking what tile they sit on (map_path.py:119-124,387-405). In the no-tower layout, (19,58) is MB_NORMAL instead of MB_NON_ANIMATED_DOOR (MEASURED from both map.bin files), and a warp event only fires on a warp tile (field_control_avatar.c:706). The bot must check flag 334 first and re-roll with a map transition. This is one more member of the known "layout-swapped at runtime" class.
- R5, emulator quirk: vanilla `CaveHole_FixCrackedGround` is `copyvar VAR_ICE_STEP_COUNT, 1` without UBFIX (cave_hole.inc:5-11). That means it reads through a NULL var pointer, not the literal 1 that row 9.17 of the validated note states. Behaviour on our emulator is UNMEASURED.
- R6: the upstream Puzzle Solver ends with `set_manual_mode()` (puzzle_solver.py:141). It never takes a fossil and never handles the cutscene.
- R7, irreversible: the choice cannot be undone (mirage_tower.c:320-325). Store the per-run random pick and log it before walking to (6,4).

CORRECTIONS TO EXISTING NOTES
- The punch-list entry omits Rock Smash.
- story-notes-s9 names FLAG_HIDE_ROUTE_111_MIRAGE_TOWER. That flag is a phantom; the real mechanism is flag 334 plus the layout swap.
- item-notes-i04 puts the fossils at (5,5)/(6,5) and the recovery at the Desert Ruins. Both are wrong.
- chapters.py:155-156 says Chapter 9 gets "the Bike", which contradicts the measured bikeless state.

## Adversarial verification

I checked all 17 claims (claim 7 split into 7a and 7b) against pokeemerald master and the pokebot-wt-ch24 worktree. Result: 17 confirmed, 1 refuted, nothing unverifiable. Everything I checked is read-only; I wrote only to my own scratchpad.

**Refuted:**
- **7b.** 3F rock (4,8) does not block the corridor. My BFS still reaches the fossils with (4,8) as the only blocker. Only 3F (3,7) and 4F (6,7) must be smashed, and upstream puzzle_solver.py:126-136 does exactly those two.
- **7a stands:** Rock Smash is required.

**Adversarial caveats on confirmed claims:**
- **Claim 5 (inferred from code, not measured).** The 4-tile route across 2F is the static minimum, but it takes three direction changes in a row. By bike.c:249-250 (TrySlowDown sets counter to --bikeSpeed), speed drops 3 → 2 → 1 → 0, so (2,8) is entered below FASTEST and the player falls. A 5-tile route through (4,7), (3,7), (2,7) and then south to (2,10) alternates turn, straight, turn and by the same arithmetic stays at FASTEST.
  - Consequence: a pathfinder that treats cracked tiles as fine at full speed could pick a route the bike cannot survive.
  - Test with a live A/B before relying on either route.
- **Claim 10.** Re-entering Devon 2F is not the only way to move the fossil to "ready". Talking to any of the other four 2F scientists does it too (scripts.inc:16, 24, 38, 52).
- **Claim 14.** The cited range skips BikeShop scripts.inc:55 (special SwapRegisteredBike). That call only swaps a bike that is already registered (item.c:572-583), so the claim still holds.
- **Claim 16 (inferred mechanism).** copyvar with source 1 reads memory address 0 (the BIOS), because GetVarPointer returns NULL for ids below the variable range (scrcmd.c:368-373, event_data.c:164-167).
  - If an emulator returned 0 there, the player would fall on arrival at 2F or 3F.
  - On our emulator this is still unmeasured.
- **Claim 4, upgraded from citation to data.** My BFS of Route 111, started from every map edge, cannot reach the tower door (19,59) when the Go-Goggles trigger tiles are blocked. With the triggers unblocked (control arm) it can.

**Tooling gotcha (measured):** on this machine, `gh api` corrupts binary files. MirageTower_3F map.bin came back as 789 bytes instead of 714, whether fetched raw or as base64. `curl` from raw.githubusercontent.com returns the correct bytes.
- Any static analysis built from binaries fetched with `gh api` here should be re-checked.
- The other agent's crack and rock coordinates match mine from clean data, so its results happen to hold.

What I did not do: no live emulator probe, and no reachability check of the Devon stair guard. The bikeless claim rests on a documented reading in sootopolis.py:1362, which I did not re-measure.

Scratch scripts and decoded data are in <session scratchpad>/fv\:
- bfs.py: Mirage Tower search
- r111.py: Route 111 search
- mt.py: map decoder

- **[CONFIRMED]** 1. Mirage Tower visibility is a 50/50 Random()&1 roll on every Route 111 OnTransition, not daily; forced visible after entering 1F; hidden once VAR_MIRAGE_TOWER_STATE != 0  
  How: MEASURED from source: mirage_tower.c:315-340 (state!=0 clears FLAG_MIRAGE_TOWER_VISIBLE and returns; rand&1; the force flag overrides). Route111/scripts.inc:42-43; MirageTower_1F/scripts.inc:7 setflag FLAG_FORCE_MIRAGE_TOWER_VISIBLE. gh code search: SetMirageTowerVisibility is called only from Route111 scripts, so there is no daily hook. Nuance: in state 1, Route111 OnLoad (scripts.inc:10,19-38) redraws a temporary tower with setmetatile for the cutscene.
- **[CONFIRMED]** 2. FLAG_FORCE_MIRAGE_TOWER_VISIBLE is cleared on entering Mauville, Route 112 and Route 113  
  How: MauvilleCity/scripts.inc:7, Route112/scripts.inc:6, Route113/scripts.inc:11 each clearflag it in OnTransition. Code search finds no other writer besides 1F:7. Route111 map.json connections are only Mauville, Route 113 and Route 112, so leaving Route 111 by any seam clears the force flag.
- **[CONFIRMED]** 3. Crossing a map seam also runs OnTransition, so visibility is re-rolled  
  How: overworld.c:784 LoadMapFromCameraTransition calls LoadCurrentMapData (795; it resets mapLayoutId from the header at 593) and then RunOnTransitionMapScript at 807, before InitMap at 808.
- **[CONFIRMED]** 4. Go-Goggles are required to enter the desert and are auto-given by the rival after Badge 4  
  How: Route111/scripts.inc:189-203 runs checkitem ITEM_GO_GOGGLES, and without them the player is pushed back. Gym_1F:62 FLAG_BADGE04_GET and :68 VAR_LAVARIDGE_TOWN_STATE=1. LavaridgeTown:41 is the OnFrame trigger; :62-63 gives the goggles to a male player (female player at :70-71). MEASURED with my own static BFS over the decoded Route111 map.bin plus mauville/general attributes, starting from every edge: with the ViciousSandstorm trigger tiles blocked, (19,59) is unreachable in both layouts. With them unblocked (control arm) it is reachable.
- **[CONFIRMED]** 5. The Mach Bike is needed on 2F only: at least 4 cracked tiles, (3,7),(2,8),(2,9),(2,10), must be crossed; 3F cracked tiles are off the required path  
  How: Own 0-1 BFS (collision, elevation, directional blocks, warps) over curl-fetched MirageTower_1F-4F map.bin: the minimum is 4 cracked tiles, exactly those, all on 2F, with 0 on 3F. 2F/3F scripts.inc:7-9 are setstepcallback STEP_CB_CRACKED_FLOOR plus setholewarp. INFERRED caveat (not measured): the 4-tile route takes three direction changes in a row, (4,7)W, (3,7)S, (3,8)W. bike.c:249-250 TrySlowDown sets counter=--bikeSpeed, so full speed (3, counter 2) falls to 2, then 1, then 0, and (2,8) would be entered below FASTEST, which means a fall. A 5-tile route, (4,7)W to (3,7)C to (2,7)C then S through (2,8)-(2,10), alternates turn/straight/turn and by the same arithmetic keeps counter 2.
- **[CONFIRMED]** 6. A cracked tile drops the player unless GetPlayerSpeed()==PLAYER_SPEED_FASTEST, which only the Mach Bike at bikeFrameCounter 2 returns  
  How: field_tasks.c:824-827; bike.c:111 sMachBikeSpeeds={NORMAL,FAST,FASTEST}; bike.c:1029-1030 (the Acro Bike returns FASTER at 1032); bike.c:237-240 caps the counter at 2. Extra: field_tasks.c:815-816 means stepping on an already-formed hole drops the player at any speed.
- **[CONFIRMED]** 7a. Rock Smash is required  
  How: BFS: with all rocks treated as solid, the fossils are unreachable. Blocking only 3F (3,7) gives unreachable, and blocking only 4F (6,7) gives unreachable. Rocks are in MirageTower_3F/map.json:17-42 and 4F/map.json:45-57.
- **[REFUTED]** 7b. Rocks at 3F (3,7),(4,8) AND 4F (6,7) all block the only corridor  
  How: MEASURED by BFS: blocking only 3F (4,8) still reaches the fossil, because the path goes (3,9) to (3,8) to smashed (3,7). Only 2 smashes are needed. Independently matches upstream puzzle_solver.py:126-136, which smashes just (3,7), facing Up from (3,8), and 4F (6,7), from (5,7).
- **[CONFIRMED]** 8. Root Fossil at 4F (5,4), Claw at (7,4); taking one is YES/NO, sets FLAG_CHOSE_*, hides both, sets VAR_MIRAGE_TOWER_STATE=1 and warps to Route111 (19,59)  
  How: 4F/map.json:17-44 gives the coordinates (the Claw object's elevation is 0 and the Root's is 4). 4F/scripts.inc:7-8/27-28 is the YESNO; :11-12/:31-32 hide both; :15/:35 set FLAG_CHOSE_*; :52 sets state 1; :54 warps to MAP_ROUTE111 19,59.
- **[CONFIRMED]** 9. The Route 111 OnFrame cutscene disintegrates the tower, sets state 2 and clears FLAG_HIDE_DESERT_UNDERPASS_FOSSIL; the next entry sets state 3  
  How: Route111/scripts.inc:103-104 (OnFrame fires on state 1), :119-122 (disintegration, setvar 2, clearflag), :45 plus :91-93 (OnTransition, state 2 becomes 3).
- **[CONFIRMED]** 10. The fossil is revived by the Devon 2F scientist at (14,8): give it, re-enter 2F (state 1 to 2), then receive a Lv20 Lileep/Anorith with a PC fallback  
  How: DevonCorp_2F/map.json: LOCALID_FOSSIL_SCIENTIST is at (14,8). scripts.inc:5-11 (OnTransition sets 1 to 2), :57-111 (give), :142/:187 (givemon at 20), :143-145/:188-190 (party/PC/no room). Nuance: talking to any of the other four 2F scientists also flips 1 to 2 (:16,:24,:38,:52), so re-entering is sufficient but not the only way.
- **[CONFIRMED]** 11. Devon 2F is reachable only after FLAG_RETURNED_DEVON_GOODS (stair guard)  
  How: DevonCorp_1F/scripts.inc:5-12: without the flag, the guard is moved to (14,2). I did not BFS-check that (14,2) fully seals the stairs. The point is moot at the fossil phase.
- **[CONFIRMED]** 12. With the tower hidden, Route111 (19,58) is MB_NORMAL (a door otherwise); warps only fire on warp-behaviour tiles, but map_path attaches warps regardless of tile  
  How: Decoded curl-fetched map.bin: in Route111, (19,58) is metatile 996 MB_NON_ANIMATED_DOOR. In Route111_NoMirageTower it is 289 MB_NORMAL. field_control_avatar.c:706 plus IsWarpMetatileBehavior :751-765 (includes NonAnimDoor). pokebot-wt-ch24 sandbox-pokebot/modules/map_path.py:119-124 builds warp_cache from every warp event; :387-405 attaches warps_to with the tile type used only for the arrow direction.
- **[CONFIRMED]** 13. The bot is bikeless, and the pathfinder has no Cracked Floor concept  
  How: sootopolis.py:1362 says 'bikeless here (MEASURED-PROD: RECEIVED_BIKE False)'. That is a prior documented reading scoped to the Sootopolis leg, not re-measured by me. grep -ci crack map_path.py = 0. map_path does have has_mach_bike for Muddy Slopes only (:727, :839).
- **[CONFIRMED]** 14. The Mach Bike from Rydel is not auto-registered, and upstream mount_bike loops forever without a bike  
  How: The cited range 7-49 omits BikeShop/scripts.inc:55 'special SwapRegisteredBike', which does run on first receipt. However, item.c:572-583 only swaps when a bike is already registered, so on first receipt it is a no-op and the claim holds. puzzle_solver.py:39-42 is an unbounded while/press Select loop. Note that the upstream solver guards it with assert_registered_item at :116.
- **[CONFIRMED]** 15. Upstream Puzzle Solver's Mirage Tower path stops at 4F (6,4) and hands off to manual; it never takes a fossil  
  How: puzzle_solver.py:139-141: navigate_to 4F (6,4), then 'puzzle complete', then context.set_manual_mode(). grep -i fossil finds 0 hits in the file.
- **[CONFIRMED]** 16. Vanilla CaveHole_FixCrackedGround uses copyvar VAR_ICE_STEP_COUNT, 1 without UBFIX; behaviour on our emulator is unmeasured  
  How: cave_hole.inc:5-11. INFERRED mechanism: scrcmd.c:368-373 plus event_data.c:164-167 mean GetVarPointer(1) returns NULL, so the var is loaded from address 0 (BIOS open-bus). If an emulator returned 0 there, OnFrame CaveHole_CheckFallDownHole (cave_hole.inc:1-2) would drop the player on arrival at 2F/3F. Unmeasured.
- **[CONFIRMED]** 17. All Mirage Tower floors have land encounter rate 10, Sandshrew/Trapinch Lv20-24  
  How: Parsed curl-fetched wild_encounters.json. MAP_MIRAGE_TOWER_1F..4F (json lines 10282/10351/10420/10489): land_mons only, rate 10, species {SANDSHREW, TRAPINCH}, levels 20-24.
