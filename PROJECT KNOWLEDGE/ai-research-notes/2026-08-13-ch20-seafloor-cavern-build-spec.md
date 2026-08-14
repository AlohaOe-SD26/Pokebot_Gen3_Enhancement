# §Ch20 Seafloor Cavern — decomp build spec (2026-08-13)

> ‼ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. Produced by a Claude subagent
> reading `pret/pokeemerald` master live (tarball + `gh api`), parsing the actual `map.bin` block
> data, and running an exhaustive Sokoban-style search over (player × boulder) states using the
> decomp's own movement rules. **Every load-bearing claim must still be verified in our harness
> before code depends on it** — the verification list is at the bottom.
>
> ✅ **Independently corroborated where it overlaps our own measurement:** our
> `probe_ch20_interior.py` found Rooms 1/2/3/5/8 severed by objects and Rooms 6/7 open water with
> zero objects, from ROM data, with no knowledge of this note. The two agree.

---

## ⛔ THREE CORRECTIONS TO WHAT WE CURRENTLY BELIEVE

### 1. ‼ **ROCK SMASH IS MANDATORY. STRENGTH ALONE CANNOT LEAVE ROOM 1.**
Our docs framed §Ch20 as a Strength-boulder dungeon. It is **Strength *and* Rock Smash**, and the
exhaustive search says a Strength-only party is **physically stuck in Room 1**:
* **Room 1** — the only route into the row-11 corridor requires pushing boulder `(5,11)` **north**,
  and `(5,10)` is a breakable rock. Every alternative was searched and fails: pushing `(5,11)` east
  strands you at `(10,11)`; `(12,11)` can only be pushed east from `(11,11)`, which is on the far
  side of `(5,11)`; and `(7..10,12)` are `MB_IMPASSABLE_NORTH` **with `collision=1`**, sealing row 11
  from row 12.
* **Room 2** — rock `(8,7)` is the only east↔west link; rows 4-6 are walled at x=8,9.
⇒ **The chapter's pre-flight must assert Rock Smash, Strength AND Surf**, not just Strength.
(We have all three: Rock Smash + Strength on Sceptile, Surf on Zigzagoon — `probe_regi_capabilities`.)

### 2. ⛔ **THE TRIGGER TILE IS `(17,42)`, NOT `(16,42)` — and our handoff says the wrong one.**
`SeafloorCavern_Room9/map.json:124-134` is the cavern's **only** coord event:
```json
{ "type": "trigger", "x": 17, "y": 42, "elevation": 3,
  "var": "VAR_SEAFLOOR_CAVERN_STATE", "var_value": "0",
  "script": "SeafloorCavern_Room9_EventScript_ArchieAwakenKyogre" }
```
`(16,42)` — where upstream `puzzle_solver.py` stops, and which our handoff calls "Archie's cutscene
tile" — is **plain floor and fires nothing**. Both statements were wrong in the same way.

### 3. ‼ **THE CHAPTER'S COMPLETION BOUNDARY IS `VAR_ROUTE128_STATE == 2`, NOT THE KYOGRE FLAG.**
`FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` is set at `Room9/scripts.inc:128` — **before** the
`warp MAP_ROUTE128, 38, 22` at `:138` and before `releaseall` at `:140`. And that `releaseall` does
**not** free the player, because Route 128 immediately runs a **second `lockall` cutscene**:
`Route128_OnFrame` → `map_script_2 VAR_ROUTE128_STATE, 1, Route128_EventScript_KyogreAwakenedScene`
(Room 9 set `VAR_ROUTE128_STATE, 1` at `:115`). That scene ends with `setvar VAR_ROUTE128_STATE, 2`.
⇒ **A chapter graded on the Kyogre flag alone would report success while the bot is still inside
two nested scripted scenes.** This is the §Ch19 `RECEIVED_HM_DIVE` shape exactly.
‼ **And the landing tile `(38,22)` is `MB_SHALLOW_WATER` elev 3 — a walkable SANDBAR ringed by
ocean.** The bot arrives on foot, on an island, and **must Surf to leave**. Three chapters have
shipped stranded; this one lands you on a sandbar by design.

---

## THE ROOM GRAPH AND THE ACTUAL ROUTE (search-verified, not guessed)

```
UNDERWATER_SEAFLOOR_CAVERN --dive-surface--> ENTRANCE (10,17)
  --Surf N, walk to (10,1)-->            ROOM1 (5,18)
  --Rock Smash + 2 Strength pushes-->    ROOM1 (6,2)  --> ROOM2 (10,7)
  --Rock Smash + 3 Strength pushes-->    ROOM2 (6,1)  --> ROOM6 (11,21)
  --Surf the CURRENT maze-->             ROOM6 (4,1)  --> ROOM3 (4,15)
  --walk-->                              ROOM3 (8,1)  --> ROOM8 (5,12)
  --9 Strength pushes-->                 ROOM8 (5,2)  --> ROOM9 (5,4)
  --walk 62 tiles-->                     ROOM9 (17,42) = THE TRIGGER
```
* ‼ **`UNDERWATER_SEAFLOOR_CAVERN → ENTRANCE (10,17)` is NOT a `warp_event`** — it is a
  `setdivewarp` in `Underwater_SeafloorCavern/scripts.inc:35-37`. Our `(10,17)` is right; it just
  is not in `map.json`, so a warp-table scan will never find it. (We already knew the static warp
  data lies at both ends of this cavern; this is the citation.)
* ‼ **ROOM 6 IS ONE-WAY**: `(11,21)→(4,1)` works, the reverse does **not** (the currents forbid it).
  It is not a trap — from `(4,1)` you can still reach Room 6 warp 2 `(14,8)` → Entrance.
  **Room 7 is two-way** — it is the room to use if a retreat is ever needed, at the cost of one
  extra Rock Smash `(9,3)` + 2 pushes of `(10,3)` east.
* **Rooms 4 and 5 are a side loop.** Nothing on the Kyogre path passes through them.
* **Room 9 has exactly one warp** — a cul-de-sac.

## ‼ PUZZLE STATE RESETS ON EVERY MAP RE-ENTRY
Boulders and rocks are objects flagged `FLAG_TEMP_11…FLAG_TEMP_1C` and are re-spawned from
`map.json` on map load. **Leaving a room and returning means redoing every push and re-smashing
every rock.** Never cache "Room 8 is solved". (Contrast: `FLAG_SYS_USE_STRENGTH` **persists** across
maps — activate Strength once in Room 1 and it holds for the whole cavern.)

## THE SOLVED PUSH SEQUENCES (exhaustive search)
* **Room 1** (31 steps): Rock Smash `(5,10)` → push `(5,11)` **N** → east along row 11 → push
  `(12,11)` **E** to `(13,11)` → north up x=12 to `(12,7)` → west along row 7 → `(6,2)`.
* **Room 2**: Rock Smash `(8,7)` → push `(4,5)` **N** ×3 → row 3 → `(6,2)` → `(6,1)`.
* **Room 8** (22 steps, 9 pushes, no single removal suffices):
  `(5,7)N, (4,7)W, (5,6)E, (5,5)N, (4,5)W, (4,4)N, (6,5)E, (6,4)N, (5,4)W`.
  ‼ One-way ledge row `MB_JUMP_SOUTH` at `(4,10),(5,10),(6,10)` — going north use x=3 or x=7.

## THE ARCHIE BATTLE — must WIN, no lose-branch
`trainerbattle_no_intro TRAINER_ARCHIE` (`Room9/scripts.inc:29`) — **single** battle
(`.doubleBattle = FALSE`), party **Mightyena L41 / Crobat L41 / Sharpedo L43**, holds 2 Super
Potions. Trainer battle ⇒ **not fleeable**. **There is no lose-branch in the script**: losing
white-outs, leaves `VAR_SEAFLOOR_CAVERN_STATE` at 0, re-arms the trigger, and **resets every boulder
and rock**. The whole dungeon must be re-solved.

## UNAVOIDABLE TRAINERS ON THE PATH (sight-line, not must-talk; none fleeable)
| room | at | sight | trainer | party |
|---|---|---|---|---|
| Room1 | `(8,6)` | 2, rotates | `GRUNT_SEAFLOOR_CAVERN_1` | Poochyena L36 |
| Room3 | `(5,5)` | 4 | `GRUNT_SEAFLOOR_CAVERN_5` | Mightyena L35, Golbat L35 |
| Room3 | `(9,5)` | 6 | `SHELLY_SEAFLOOR_CAVERN` | Sharpedo L37, Mightyena L37 |
Room 1 `(15,10)` and both Room 4 grunts are avoidable/off-path. *(The "unavoidable" column is a
geometric derivation from the parsed grid + sight radius — high confidence, but derived.)*

## OTHER FACTS WORTH HAVING
* **Rooms 6 and 7 are CURRENT mazes** (`MB_*WARD_CURRENT`, 108 and 117 current tiles) with **no
  objects and no scripts** — pure navigation. A plain A* over "passable tiles" will emit paths the
  game refuses; stepping on a current slides you. **Our `map_path` does model currents**
  (`forced_movement_to`) — that must be verified live, it is not assumed.
* **Wild encounters**: Zubat L28-35 / Golbat L33-36 on land in Rooms 1-8. **Room 9 has no encounter
  table at all** — no wilds in the Kyogre room.
* **Free TM26 Earthquake** at `ROOM9 (14,5)`, flag `FLAG_ITEM_SEAFLOOR_CAVERN_ROOM_9_TM_EARTHQUAKE`,
  11 steps from the room entrance. Optional.
* ⛔ **DEAD CONTENT — do not write a leg for it:** the Aqua grunt at `ENTRANCE (10,2)` is hidden by
  `FLAG_HIDE_SEAFLOOR_CAVERN_ENTRANCE_AQUA_GRUNT`, which is set in
  `MossdeepCity_StevensHouse/scripts.inc:49` — **the same script that hands you HM Dive**. Since
  Dive is the only way to reach the cavern, **he can never be encountered in normal play.**
* **The only YES/NO prompt in the whole chapter** is `Text_WantToStrength` on the first boulder
  (and the same shape for Rock Smash). Neither cutscene has one; every `msgbox` is `MSGBOX_DEFAULT`.
* **Point of no return:** stepping on `(17,42)`. Everything before it is reversible via Room 7.
* `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` = `0x81`, **set in exactly one place and never cleared**
  (14 repo hits: 1 `setflag`, 0 `clearflag`, 13 read-only). **Grading chapter 20 on it is safe.**

---

## THE LEG LIST (each with an assertable condition — no step counts)

| # | leg | completion condition |
|---|---|---|
| 0 | **Pre-flight** (before entering, not a leg) | party knows **Surf**, **Strength** AND **Rock Smash**; `FLAG_BADGE04_GET`. ‼ Rock Smash is mandatory |
| 1 | Dive at Route 128, surface | `map == SEAFLOOR_CAVERN_ENTRANCE` and at `(10,17)` |
| 2 | Surf the entrance pool, north door | `map == ROOM1` and at `(5,18)` |
| 3 | Room 1 puzzle (+ grunt battle) | `map == ROOM2` and at `(10,7)` |
| 4 | Room 2 puzzle | `map == ROOM6` and at `(11,21)` |
| 5 | Room 6 current maze — **ONE-WAY** | `map == ROOM3` and at `(4,15)` |
| 6 | Room 3 walk (+ 2 unavoidable trainers incl. Shelly) | `map == ROOM8` and at `(5,12)` |
| 7 | Room 8 boulder maze, 9 pushes | `map == ROOM9` and at `(5,4)` |
| 8 | *(optional)* TM26 Earthquake at `(14,5)` | its item flag set |
| 9 | Walk to the trigger | at `ROOM9 (17,42)` while `VAR_SEAFLOOR_CAVERN_STATE == 0` |
| 10 | Ride the cutscene, **WIN** Archie | `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` set and `VAR_SEAFLOOR_CAVERN_STATE == 1` |
| 11 | **"and the bot can continue"** — ride the Route 128 follow-up | `map == ROUTE128`, at `(38,22)`, **and `VAR_ROUTE128_STATE == 2`**, **and a Surf-initiated move off the sandbar succeeds** |

## ‼ VERIFY IN OUR HARNESS BEFORE CODE DEPENDS ON IT
1. **That our planner survives the Rooms 6/7 currents** — it has `forced_movement_to`, but no
   chapter has ever driven a current maze. This is the single biggest unknown.
2. **The trigger tile `(17,42)`** — drive to it and watch the scene fire (and confirm `(16,42)`
   does nothing).
3. **The push sequences** — re-derive them against LIVE object positions from inside each room;
   `probe_ch20_interior.py` measured from outside and its per-room routing is a lower bound.
4. **`VAR_ROUTE128_STATE == 2`** as the real release point, and that Surf off `(38,22)` works.
