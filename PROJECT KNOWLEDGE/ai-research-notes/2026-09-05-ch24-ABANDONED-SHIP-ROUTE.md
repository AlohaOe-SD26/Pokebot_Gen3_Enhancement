# §Ch24 `#24-icebeamtrip` — THE ABANDONED SHIP: the route to TM13 Ice Beam

**Date:** 2026-09-05 · **Status:** ⭐ **UNUSUALLY WELL-EVIDENCED.** Decomp-derived by a 7-agent
adversarial workflow, **and two of its load-bearing claims are already CONFIRMED LIVE** by our own
harness. Where a claim is only decomp-derived it says so.

---

## ⭐ 0. WHY THIS NOTE EXISTS: FOUR DRIVES FAILED AND EVERY DIAGNOSIS OF MINE WAS WRONG

I mapped this route from **our own runtime map data** (`get_map_data(...).warps / .objects /
.bg_events`) and believed that outranked a decomp claim. **The coordinates were right and the route
was still wrong**, because warp TABLES do not carry:

* the warp **KIND** (arrow vs step-on vs door),
* **collision connectivity** (which tiles can actually reach which), or
* a **metatile gate** applied by a map's `OnLoad` script.

⇒ ‼ **"OUR DATA OUTRANKS THE DECOMP" IS TRUE ABOUT VALUES AND FALSE ABOUT MECHANISMS.** Reading the
warp table told me *where* the warps are; only the decomp told me *how they fire*, and only a
collision BFS told me *whether the two ends are connected*.

**The four failed diagnoses, in order:** warp-as-waypoint → elevation transition → aim-at-the-warp →
(hand-step test) — each disproven by the next measurement.

---

## 1. ✅ CONFIRMED LIVE — BOARDING IS A **NORTH ARROW WARP**

`ROUTE108 (29,6)` is `MB_STAIRS_OUTSIDE_ABANDONED_SHIP`, and **`MetatileBehavior_IsNorthArrowWarp`
returns TRUE** for it (`src/metatile_behavior.c:304-311`).

⇒ **STAND ON THE TILE AND HOLD UP.** Not a step-on, not a door.

⭐ **THE MEASUREMENT THAT PROVED IT BEFORE THE DECOMP ARRIVED:** hand-stepping **WEST across
(29,6)** walked straight through to **(28,6) without firing the warp**. A step-on warp cannot do
that. ⇒ the kind was wrong, and no amount of router-fiddling would ever have helped.

**The working sequence** (§Ch23 leg 9's proven three-step shape):
1. surf/navigate to **(29,7)** — `MB_OCEAN_WATER`, elevation 1, the sea south of the shelf;
2. `_bounded_step("Up", (29,6))` — ONE explicit step onto the arrow tile, then ASSERT we are on it;
3. `_walk_through_warp("Up", ROUTE108, timeout_frames=600)` — hold Up until the map changes.

✅ **DRIVEN: the bot is now aboard at `ABANDONED_SHIP_DECK (13,15)`.**
⭐ The **surf dismount is automatic** — `CanStopSurfing` fires because the destination elevation
equals `ELEVATION_DEFAULT` = 3 (`src/field_player_avatar.c:729-742`). No dismount command needed.
⚠ `(28,6)/(29,6)/(30,6)` are a **3-tile elevation-3 shelf** in an elevation-1 sea. `(30,6)` is
**"Shallow Water"**, not a land platform — and **aiming navigation at it WEDGES the navigator**
(the warp-override rewrites the destination to the deck, the bot walks to (30,6), then re-paths
(30,6)→(30,6) = **zero waypoints** forever).

---

## 2. ✅ CONFIRMED LIVE — ⛔⛔ THE DECK IS SPLIT INTO TWO DISCONNECTED HALVES

Decomp BFS over `data/layouts/AbandonedShip_Deck/map.bin` (966 bytes = 23×21×2, asserted): from the
Route 108 arrival **(13,15)** only **15 tiles** are reachable, and **both** the Captain's Office door
`(12,5)` **and** the west door `(8,9)` are **UNREACHABLE**. The separators are `(11,10)` and
`(12,11)`, each collision 1.

✅ **OUR OWN PLANNER INDEPENDENTLY CONFIRMS IT.** The live drive died with:
> `BotModeError: Could not find a path from (13/15 @ ABANDONED_SHIP_DECK) to (12/5 @ ABANDONED_SHIP_DECK)`

⇒ **The hop "DECK → CAPTAIN'S OFFICE" is impossible from the boarding point.** This is the single
biggest correction in the note, and it invalidated the route I had already coded.

**`ABANDONED_SHIP_CORRIDORS_1F` IS ALSO SPLIT** — column x=7 is solid. Deck `(13,9)` lands in the
**RIGHT** half at `(8,11)`; deck `(8,9)` lands in the **LEFT** half at `(0,11)`.
⚠ And no room map bridges them: `Rooms_1F` returns only to right-half warps, `Rooms2_1F` only to
left-half warps.

### ⭐ THE ONLY CROSSOVER IN THE ENTIRE SHIP IS `CORRIDORS_B1F` ROW 5
BFS from `(8,2)` reaches `(0,2)` in 14 steps along row 5.
⇒ **Reaching the Captain's Office REQUIRES: board → down to B1F → cross row 5 → up the WEST stair →
deck west half → Captain's Office.** There is no shortcut.

---

## 3. ⛔⛔ THE STORAGE ROOM DOOR IS **METATILE-GATED**, NOT WARP-GATED — AND THE KEY MUST BE *INSERTED*

`AbandonedShip_Corridors_B1F_OnLoad` runs on **every map load** and, while `FLAG_USED_STORAGE_KEY`
is unset, does:
```
setmetatile 11, 4, METATILE_InsideShip_IntactDoor_Bottom_Locked, TRUE
```
The locked metatile (id 563) has attribute `0x0000` ⇒ behaviour **`MB_NORMAL`**, and
`MetatileBehavior_IsWarpDoor(MB_NORMAL)` is FALSE ⇒ **`TryDoorWarp` CANNOT FIRE AT ALL.** The
unlocked id 555 has attribute `0x0069` ⇒ `MB_ANIMATED_DOOR`.

⇒ ‼ **HOLDING THE KEY DOES NOTHING.** The bg_event at `(11,4)` (`BG_EVENT_PLAYER_FACING_ANY`) runs
`EventScript_StorageRoomDoor`, which does `checkitem ITEM_STORAGE_KEY` → `removeitem` →
`setflag FLAG_USED_STORAGE_KEY` → `call UnlockStorageRoom` → `special DrawWholeMapView`.
⇒ **The bot must PRESS A at the door to insert the key**, and only then does the tile become a warp.
⚠ The key is **CONSUMED**, and the door stays unlocked afterwards via the flag.

⇒ My coded hop `_hop(CORR_B1F, (11,4), ROOM_B1F)` would **never** have worked — it assumed a warp
where, at that moment, there is a wall.

---

## 4. THE MEASURED FACTS THAT DID SURVIVE

From our own `get_map_data(...)`, all confirmed by the decomp pass:

| what | where | flag |
|---|---|---|
| Storage Key (item ball) | `CAPTAINS_OFFICE (0,6)` | `ITEM_ABANDONED_SHIP_CAPTAINS_OFFICE_STORAGE_KEY` |
| TM13 Ice Beam (item ball) | `ROOM_B1F (4,4)` | `ITEM_ABANDONED_SHIP_ROOMS_B1F_TM_ICE_BEAM` |
| Storage Room door | `CORRIDORS_B1F (11,4)` | `FLAG_USED_STORAGE_KEY` |
| Duncan (trainer, sight 4, undefeated) | `CORRIDORS_B1F (9,6)` | — |

✅ **NO DIVE IS REQUIRED** — structurally confirmed: the route never touches
`ABANDONED_SHIP_UNDERWATER1/2`. The Dive branch leads to the Hidden Floor (TM18, Scanner).
⚠ **TWO SIMILARLY NAMED MAPS:** the TM is in `ABANDONED_SHIP_ROOM_B1F` (**singular**, map 61), not
`ABANDONED_SHIP_ROOMS_B1F` (plural, 58) — while the FLAG is named `..._ROOMS_B1F_...`.
⚠ `ROUTE109 → ROUTE108` is a **map CONNECTION, not a warp** (`Route109` declares
`{map: ROUTE108, offset: 40, direction: left}`); Route 109's only warp is the Seashore House.

---

## 5. THE CORRECTED ROUTE

```
SLATEPORT ──surf──→ ROUTE108 (29,7)
(29,7) ──step Up──→ (29,6)  [stand ON the arrow]
(29,6) ──hold Up──→ DECK (13,15)                    ← EAST half
DECK (13,9) ───────→ CORRIDORS_1F (8,11)            ← RIGHT half   [step-on]
CORRIDORS_1F (16,2) → CORRIDORS_B1F (8,2)
CORRIDORS_B1F: cross ROW 5 west → (0,2)             ← THE ONLY CROSSOVER
(0,2) ─────────────→ CORRIDORS_1F (left half)
CORRIDORS_1F (0,11) → DECK (8,9)                    ← WEST half
DECK (12,5) ───────→ CAPTAINS_OFFICE                ← Storage Key at (0,6)
   ... and back down to CORRIDORS_B1F ...
CORRIDORS_B1F (11,4): PRESS A to INSERT the key     ← the tile is a WALL until this happens
(11,4) ────────────→ ROOM_B1F                       ← TM13 at (4,4)
```

⚠ **UNVERIFIED / STILL OWED:** everything from the deck's right half onward is decomp-derived and
**not yet driven**. Confirm each hop with `calculate_path` from the position the run actually reaches
— the deck split was caught exactly that way, by our planner refusing a hop the decomp had already
flagged.

---

## 6. ‼ THE TRANSFERABLE LESSON

⭐ **A WARP TABLE TELLS YOU WHERE, NOT HOW OR WHETHER.** Three separate blockers on one short route —
an arrow warp, a collision split, and a metatile gate — were all **invisible** in the data I trusted,
and all three were caught by asking agents to attack the route from different angles rather than by
driving into them one at a time. Four drives found one blocker; the recon found three more in the
same time.
⇒ ⛔ **For any unfamiliar route: get the warp KINDS and a collision-connectivity check BEFORE writing
hops.** The coordinates are the cheap half.
