# CH3-RECON report

Source: pret/pokeemerald@731ad5bfd6e6f265508d0efcca0ba42f9dcf5881. Data: `ai_player/knowledge/seasoned/ch3_maps.json`. Static knowledge only (USER RULING 40); nothing was run in an emulator.
Wall time: about 1 min (101 s) to this point.

## Counts (from the JSON)
| Map | connections | warps | trainers | item balls | coord events | hidden items |
|---|---|---|---|---|---|---|
| ROUTE104 | 3 | 8 | 8 objects (7 distinct trainers) | 4 | 1 | 5 |
| PETALBURG_WOODS | 0 | 6 | 2 | 4 | 2 | 4 |
| RUSTBORO_CITY | 3 | 12 | 0 | 1 | 21 | 0 |
| RUSTBORO_CITY_GYM | 0 | 2 | 4 (incl. ROXANNE) | 0 | 0 | 0 |

## ROUTE104
There is no separate north map. The north part (Rustboro side) is the same MAP_ROUTE104. `Route104_Prototype` is a different, empty map with no events.
Connections: up to RUSTBORO_CITY, down to ROUTE105, right to PETALBURG_CITY (offset 50). Warps include Mr. Briney's house and the Pretty Petal flower shop.
Gating: the only coord event is the rival trigger at (17,51), active while `VAR_ROUTE104_STATE`=1. It sets the state to 2 and plays the rival's music. It is not a battle gate.
Trainers (local id, x,y, sight, party):
- HALEY (3; 31,24; sight 7): Lotad 6, Shroomish 6
- IVAN (9; 29,8; sight 0): Magikarp 5, 6, 7
- GINA & MIA (23 and 24; 27,15 and 28,15; sight 1): double battle, Seedot 6 and Lotad 6
- WINSTON (25; 21,25; sight 3): Zigzagoon 7
- CINDY (26; 11,44; sight 3): Zigzagoon 7
- BILLY (28; 18,67; sight 2): Zigzagoon 5, Seedot 7
- DARIAN (33; 15,59; sight 0): Magikarp 9

Item balls: PP Up (39,15), Poke Ball (29,53), X Accuracy (37,22), Potion (5,8). Hidden items: Super Potion (7,6), Poke Ball (3,9), Potion (14,55), Antidote (16,72), Heart Scale (16,64).

## PETALBURG_WOODS
No map connections, only warps (6). Two coord events at (26,23) and (27,23) fire while `VAR_PETALBURG_WOODS_STATE`=0. They start the scripted Devon researcher / Team Aqua scene, which ends in a forced battle with the Aqua GRUNT (Poochyena 9, TRAINER_GRUNT_PETALBURG_WOODS). This is the gate: the woods cannot be crossed past that point until the scene is done. The state variable is set to 1 afterwards.
Trainers: LYLE (7,32; sight 3): Wurmple 3 x4. JAMES (4,14; sight 3): Nincada 6 x2.
Item balls: Great Ball (45,7), X Attack (35,20), Ether (4,8), Paralyze Heal (4,26). Hidden items: Potion (39,35), Tiny Mushroom (26,6), Tiny Mushroom (40,29), Poke Ball (4,19).

## RUSTBORO_CITY
Connections: up ROUTE115, down ROUTE104, right ROUTE116. 12 warps. One item ball: X Defend (36,51).
Its 21 coord events are all story triggers keyed on `VAR_RUSTBORO_CITY_STATE`: stolen-goods scene (state 1, x=23, y=20..24), help get goods (state 2, around x=29..30, y=9..12), return goods (state 4, same area), and rival triggers (state 7, y=53, x=12..19). They are scripted scenes. The rival one plays the rival's music. See the JSON for the exact positions and scripts.

## RUSTBORO_CITY_GYM
Warps: 2. Trainers: JOSH (Geodude 10), TOMMY (Geodude 8 x2), MARC (Geodude 8 x2), and ROXANNE (Geodude 12, Geodude 12, Nosepass 15 holding an Oran Berry). All use single battles. Roxanne's moves: Geodude Tackle/Defense Curl/Rock Throw/Rock Tomb, Nosepass Block/Harden/Tackle/Rock Tomb. Roxanne's script gives TM Rock Tomb on first win. She has the AI flags CHECK_BAD_MOVE, TRY_TO_FAINT and CHECK_VIABILITY.

## Not extracted / caveats
- The Aqua GRUNT in the woods and the rival objects on ROUTE104 are scripted (added or hidden by script) so they are not in the trainer list, apart from the grunt's party above.
- Local ids with no explicit `local_id` field are computed as the 1-based index in object_events. I did not verify that against the compiled game.
- Trainer sight is the raw `trainer_sight_or_berry_tree_id` value. Wild encounter tables and tile maps were out of scope.
- Rematch parties and the shop and NPC objects (listed under other_objects) are not summarized here.
