# W7 adversarial pass: chapter pack 2 (ch2.md) load-bearing claims

Pin check (MEASURED): tools/decomp.pin = 731ad5bfd6e6f265508d0efcca0ba42f9dcf5881; `git -C _decomp/pokeemerald rev-parse HEAD` = same.
Lookup-first (MEASURED): `decomp_lookup.py ask "one-way warp Petalburg gym"` -> "NO PRIOR RULING OR FACT FOUND".

ch2.md has exactly ONE load-bearing claim (line 77).

## FALSE claims
None.

## Claim 1: TRUE (MEASURED)
"[one_way_warp] none of the 66 warps touching the area maps is one-way by warp data"

Script: scratchpad/w7/work2/warps.py reads every data/maps/*/map.json in the pinned clone, takes every warp
whose source OR destination is one of ROUTE101, OLDALE_TOWN, ROUTE102, PETALBURG_CITY, PETALBURG_CITY_GYM,
and resolves dest_map[dest_warp_id] to check that the destination warp points back to the source map.
Output: "touching warps: 66" / "from area: 48 into area from outside: 18". Every one of the 66 resolves back
to its source map. 44 return to the exact same warp id; 22 return to the partner tile of a 2-wide door/mat
(e.g. `MAP_OLDALE_TOWN_HOUSE1[1] (4,8) -> MAP_OLDALE_TOWN[0] back->MAP_OLDALE_TOWN_HOUSE1[0]`), which is not
one-way. Route101/map.json:109 and Route102/map.json:146 both read `"warp_events": [],`.
Sample READ: PetalburgCity_Gym/map.json:180-184 `"x": 1, "y": 105, ... "dest_map": "MAP_PETALBURG_CITY_GYM", "dest_warp_id": "3"`, and gym warp 3 at (7,85) returns to warp 2.

## Caveat on claim 1 (INFERRED from READ scripts): true by warp data, but the gym's 36 internal warps are NOT walkable warps in ch2
- The gym's forward doors are sign bg_events on the same tiles as the warps, e.g. PetalburgCity_Gym/map.json
  bg_events `{'x': 1, 'y': 105, ... 'script': 'PetalburgCity_Gym_EventScript_SpeedRoomDoor'}`, and the move is a scripted
  `warpdoor MAP_PETALBURG_CITY_GYM, VAR_0x8008, VAR_0x8009` (PetalburgCity_Gym/scripts.inc, EnterRoom, ~line 723).
- Locked in ch2: scripts.inc:716 `goto_if_lt VAR_PETALBURG_GYM_STATE, 6, PetalburgCity_Gym_EventScript_DoorLocked`
  (also :744). State is 2 after the Wally tutorial (scripts.inc:90 `setvar VAR_PETALBURG_GYM_STATE, 2`) and goes up by one per
  badge, e.g. LavaridgeTown_Gym_1F/scripts.inc:63 `addvar VAR_PETALBURG_GYM_STATE, 1`, so it reaches 6 at the 4th badge.
  Room-to-room doors also need the previous room's trainer beaten (scripts.inc ConfusionRoomDoor:
  `goto_if_not_defeated TRAINER_RANDALL, PetalburgCity_Gym_EventScript_DoorLocked`).
  => The pack's "Warps: PETALBURG_CITY_GYM x36" reads as walkable links. In this chapter none of them can be used.

## Load-bearing facts MISSING from the claims list (READ)
1. GATE, Petalburg Gym rooms locked until VAR_PETALBURG_GYM_STATE >= 6 (4 badges): see the caveat above. Not on the claims list.
2. SCRIPTED WARPS, not in warp data, which carry the chapter's story moves:
   - PetalburgCity_Gym/scripts.inc:188 `warp MAP_PETALBURG_CITY, 15, 8` (after Norman's first talk; :182-183 set GYM_STATE 1 and CITY_STATE 2)
   - PetalburgCity/scripts.inc:52 `warp MAP_PETALBURG_CITY_GYM, 4, 108` (end of the Wally tutorial)
   - PetalburgCity_Gym/scripts.inc:437 `warp MAP_PETALBURG_CITY, 15, 8` (sets CITY_STATE 4 at :435)
   - PetalburgCity/scripts.inc:77 `warp MAP_PETALBURG_CITY_WALLYS_HOUSE, 2, 4`
3. SCRIPTED BATTLE: PetalburgCity/scripts.inc:37 `special StartWallyTutorialBattle` (party swapped: :32-33 `special SavePlayerParty`
   / `special LoadWallyZigzagoon`, restored :50 `special LoadPlayerParty`). It is not a trainerbattle and is absent from Trainers/Bosses.
4. WEST-EXIT STEER, Petalburg: while VAR_PETALBURG_CITY_STATE == 0, PetalburgCity/scripts.inc:8
   `call_if_eq VAR_PETALBURG_CITY_STATE, 0, PetalburgCity_EventScript_MoveGymBoyToWestEntrance` (:14 `setobjectxyperm LOCALID_GYM_BOY, 5, 11`), and
   PetalburgCity/map.json coord triggers x=8, y=10..13, var VAR_PETALBURG_CITY_STATE value 0 -> ShowGymToPlayer0..3. The state leaves 0 only at
   PetalburgCity_Gym/scripts.inc:183 `setvar VAR_PETALBURG_CITY_STATE, 2` (Norman's first talk). Whether this physically blocks
   Route 104 depends on the layout: UNKNOWN (layout not read). The trigger repeats each time, because ShowGymToPlayer sets no var.
5. GATE, Oldale west to Route 102: OldaleTown/scripts.inc:8 `call_if_unset FLAG_ADVENTURE_STARTED, OldaleTown_EventScript_BlockWestEntrance`
   and an OldaleTown/map.json coord trigger (0,10) `VAR_OLDALE_TOWN_STATE` 0 -> `OldaleTown_EventScript_BlockedPath`. Both are cleared at
   LittlerootTown_ProfessorBirchsLab/scripts.inc:510-511 `setflag FLAG_ADVENTURE_STARTED` / `setvar VAR_OLDALE_TOWN_STATE, 1`.
   This is relevant to ch2_route102 if ch1 can end without the Pokedex. INFERRED that ch1 sets it.

## Spot check outside the claims (READ)
NORMAN_1 in the pack: Lv 27/27/29/31 SPINDA VIGOROTH LINOONE SLAKING. src/data/trainer_parties.h:3480-3502 gives `.lvl = 27` SPINDA,
`.lvl = 27` VIGOROTH, `.lvl = 29` LINOONE, `.lvl = 31` SLAKING. They match.
