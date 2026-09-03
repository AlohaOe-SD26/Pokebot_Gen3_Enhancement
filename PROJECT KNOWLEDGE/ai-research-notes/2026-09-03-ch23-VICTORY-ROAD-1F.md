# §Ch23 — VICTORY ROAD **1F**: THE FLOOR THAT IS CUT BY ELEVATION, NOT BY WALLS

> ‼ **A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). Produced 2026-09-03 by a decomp agent after the
> basements were audited and 1F was found to be the remaining gap on the mandatory route.
> ⛔ **SCRIPTS, FLAGS, VARS, WARPS, OBJECTS AND TILE BYTES ARE READS with citations. REACHABILITY,
> REGION SIZES, PATH LENGTHS, TRAINER AVOIDABILITY AND ITEM GATING ARE THE AGENT'S BFS OUTPUT** —
> simulation, not live observation. Nothing here has touched an emulator.
> ✅ `data/layouts/VictoryRoad_1F/map.bin` = **4,140 bytes** = 46 × 45 × 2, asserted before decoding.
> All coordinates are RAW LAYOUT SPACE.
> ⭐ **The agent found and fixed a bug in its own first pass** — it had modelled trainer sight cones
> as elevation-gated objects, which silently failed to block the elevation-15 tiles (30,17)/(31,17).
> Re-run with hard tile removal; the two MANDATORY verdicts survived, the "+0" figures are corrected.

---

## §0. ⭐⭐ THE HEADLINE: 1F IS THREE DISJOINT REGIONS, AND THE CUT IS **ELEVATION**

| region | tiles | contains |
|---|---|---|
| **A** — entrance | **479** | (15,40) Ever Grande door · **(9,14) the B1F ladder** · Max Elixir |
| **B** — exit | **185** | **(21,32) up from B1F** · (39,5) the League door |
| **C** — SE pocket | **20** (28 once the PP Up is taken) | (42,38) up from B1F · PP Up · hidden Ultra Ball |

**One-way warp matrix (simulated):** from (15,40) you can reach **only (9,14)**. From (21,32) you can
reach **only (39,5)**. **(42,38) is a DEAD END.**

### ‼ WHY — AND THIS IS THE SINGLE MOST IMPORTANT FACT ON THE MAP
**A and B physically SHARE 16 tiles** — the elevation-15 "bridges" at y=27-28 / x=26-29 and
y=17-18 / x=29-33. Region A arrives on (29,28) **carrying elevation 3**; region B arrives on *the same
tile* **carrying elevation 4**. The next tile east, (30,28), is **elevation 4**. So B walks on and
**A is refused**.
⇒ **The elevation-15 bridge lets two corridors overlap without ever letting you change level.**
⛔ **A model that made an elevation-15 tile SET the carried elevation would merge A and B and declare
the entire basement detour unnecessary.** That is the same rule that has burned this project twice,
and here it is load-bearing for the whole chapter.

⭐ **The (21,32) ladder sits in a fully walled 6-tile room** (x=20-22, y=31-32) whose only other exit
is the elevation-0 stair pair (21,30)/(21,29) lifting to (21,28) at elevation 4. **That room is
unreachable from region A. THIS is what makes the basements mandatory.**

✅ **Cross-check against OUR planner — 3 of 4 exact:** (15,40)→(9,14) = **44** ✔,
(15,40)→Wally(3,23) = **29** ✔, (3,23)→(9,14) = **15** ✔, (15,40)→(39,5) **UNREACHABLE** ✔.
⚠ **One mismatch, and it is the open question — see §5.**

## §1. ✅ THE SCRIPTS ARE HARMLESS — THE `ON_TRANSITION` WORRY IS CLOSED

`VictoryRoad_1F_OnTransition` (`data/maps/VictoryRoad_1F/scripts.inc:1-18`) checks **exactly one**
variable and does nothing else:

```
call_if_eq VAR_VICTORY_ROAD_1F_STATE, 1, ...SetEntranceWallyPos1   @ setobjectxyperm Wally, 2, 24
call_if_eq VAR_VICTORY_ROAD_1F_STATE, 2, ...SetEntranceWallyPos2   @ setobjectxyperm Wally, 3, 24
```

**It cannot move the player, cannot lock input, cannot spawn or despawn anything** —
`setobjectxyperm` only rewrites an already-defined object's template coords. **At state 0 (first
visit) it is a NO-OP.** ⇒ the least dangerous class of `ON_TRANSITION`.

## §2. ⭐ WALLY FIRES UNCONDITIONALLY ON THE FIRST VISIT — PROVEN, NOT ASSUMED

Both coord events are `elevation: 4`, `var: VAR_VICTORY_ROAD_1F_STATE`, `var_value: 0`
(`map.json:173-192`).

| trigger | Wally walks from (12,25) | he parks at |
|---|---|---|
| **(2,23)** | 10 × `walk_left` + `walk_up` | **(2,24)** |
| **(3,23)** | 9 × `walk_left` + `walk_up` | **(3,24)** |

Sequence (`scripts.inc:20-46`): `lockall` → `setvar VAR_0x8008` → `addobject` Wally → approach →
force the player to face down → msgbox → `trainerbattle_no_intro TRAINER_WALLY_VR_1` → msgbox →
`clearflag FLAG_HIDE_VICTORY_ROAD_ENTRANCE_WALLY` (0x35A) → `copyobjectxytoperm` →
**`setflag FLAG_DEFEATED_WALLY_VICTORY_ROAD` (0x7E)** ✔ → `copyvar VAR_VICTORY_ROAD_1F_STATE` →
`releaseall`.

**Three independent reasons it cannot silently fail to arm:**
1. `VAR_VICTORY_ROAD_1F_STATE` = **0x40C3**, outside the temp range `0x4000-0x400F`
   (`constants/vars.h:7-25`) ⇒ **a persistent saved var, not cleared on map load.**
2. It appears in **only three files in the entire repo** — this map's `scripts.inc`, its `map.json`,
   and `vars.h`. **Nothing else in the game can set, clear or reset it.**
3. The elevation match cannot fail: `GetCoordEventScriptAtPosition`
   (`field_control_avatar.c:897-914`) needs `coordEvent.elevation == playerElevation || == 0`; these
   are elevation 4, and **all four neighbours of both trigger tiles are elevation 4 or wall — no
   elevation-15 neighbour exists**, so `previousElevation` is never stale on arrival.

⇒ **Treat it as a one-shot: fires on the first visit, never again.**
⛔ **CORRECTION to an earlier claim — "he becomes a permanent blocker" was TOO STRONG.** He parks at
**(2,24) *or* (3,24), whichever trigger you used** — never both — and **he seals nothing**:
(15,40)→(9,14) stays reachable either way, **44 steps** vs **46**. A 2-step nuisance, not a barrier.

*(Post-game only: `hall_of_fame.inc:12-13` re-hides this Wally and reveals a rematchable
`TRAINER_WALLY_VR_2` at (31,9). Irrelevant to §Ch23.)*

## §3. ⛔ 1F NEEDS NO FIELD MOVES AT ALL — AND CANNOT BE BRICKED

**ZERO `OBJ_EVENT_GFX_PUSHABLE_BOULDER`. ZERO `OBJ_EVENT_GFX_BREAKABLE_ROCK`.** `requires_flash:
false` (`map.json:7`); no `rock_smash_mons` table for `MAP_VICTORY_ROAD_1F`. **Strength, Rock Smash
and Flash are basement-only.**
⇒ **The B1F seal hazard has NO 1F analogue**: there is no push on this floor, so no push can seal it.

⚠ **But there IS one object-gated region change, and it is not a boulder.** The **PP Up ball at
(37,39) physically blocks the corridor to the hidden Ultra Ball.** Fault-injected: ball present →
region C is **20 tiles** and (30,39) is **UNREACHABLE**; ball collected → **28 tiles** and (30,39)
reachable. Benign (it opens, never closes) — but a bot that never picks up the PP Up can never reach
the Ultra Ball.

## §4. TRAINERS — **TWO MANDATORY BATTLES, ONE PER LEG**

Nine objects (`map.json:16-201`); five are sight trainers. Cones simulated with hard tile removal:

| trainer | tile | sight | mandatory? |
|---|---|---|---|
| **Hope** (WOMAN_5) | (6,15) FACE_LEFT | 4 | ⛔ **MANDATORY on leg 1** — (9,14) is UNREACHABLE without entering her cone |
| **Edgar** (MAN_3) | (33,22) FACE_DOWN | 3 | ⛔ **MANDATORY on leg 2** — (39,5) is UNREACHABLE without entering his cone |
| Albert | (27,34) | 3 | avoidable, **+0 steps** |
| Katelynn | (29,17) | 2 | avoidable, +0 |
| Quincy | (32,17) | 2 | avoidable, +0 |

⇒ **§Ch23's total unavoidable sight battles: 2 on 1F (Hope, Edgar) + ≥5 in the basements + Wally.**

## §5. ⚠⚠ THE OPEN QUESTION — 61 vs 64, ON THE ONE LEG NOBODY HAS DRIVEN

The agent's BFS reproduces our planner **exactly** on three legs and on the unreachability verdict,
then **disagrees on the fourth**:

| leg | our `calculate_path` | the agent's BFS |
|---|---|---|
| (15,40)→(9,14) | 44 | **44** ✔ |
| (15,40)→(3,23) | 29 | **29** ✔ |
| (3,23)→(9,14) | 15 | **15** ✔ |
| (15,40)→(39,5) | UNREACHABLE | **UNREACHABLE** ✔ |
| **(21,32)→(39,5)** | **64** | ⚠ **61** |

‼ **Why it matters more than a 3-step tie-break:** leg 2 is **the only leg that crosses the
elevation-15 bridge at y=17-18** (through (31,17)/(31,18), between Katelynn and Quincy), and
elevation-15 handling is exactly the rule that moves the reachable set by hundreds of tiles. **If our
planner treats elevation-15 even slightly differently, this is the leg where it shows** — and it is
the leg the bot must walk to finish Victory Road.
⚠ A 3-step gap is small enough to be a tie-break between equal paths and large enough to be a
modelling error. **It is not currently distinguishable, and it should not be guessed.**

### ⭐ THE CHEAPEST LIVE CHECK — ONE TILE, ONE STEP, SETTLES THE WHOLE AUDIT
Observe-only, no state writes, no basement traversal:
1. From the Ever Grande entrance side, walk to **1F (29,28)** (region A, 3 tiles east of the y=27-28
   bridge). Print the carried elevation — **predict 3** — then attempt **one step EAST to (30,28)**
   — **predict it FAILS with an elevation mismatch.**
2. Confirming arm: arrive at (21,32), walk to **the same tile (29,28)**, print the elevation —
   **predict 4** — and step east — **predict it SUCCEEDS.**

⇒ That A/B on a single tile discriminates the entire region decomposition, and settles 61-vs-64 in
the same visit. ⛔ **If step 1 SUCCEEDS, this whole three-region model is wrong and the basement
detour is not actually forced** — which would change the chapter's shape completely.

## §6. HAZARDS — the census, and two rules proven VACUOUS rather than left ambiguous

Only **8 distinct behaviours** exist across all 2,070 tiles: `MB_CAVE` 1146 (632 walkable),
`MB_NORMAL` 700 (16), `MB_IMPASSABLE_NORTH` 204 (29), `MB_JUMP_WEST` 10, `MB_JUMP_SOUTH` 4,
`MB_LADDER` 3, `MB_SOUTH_ARROW_WARP` 2, `MB_JUMP_SOUTHWEST` 1. **682 walkable / 1388 wall.**
✅ **No cracked floors, no holes, no ice, no currents, no waterfalls, no warp pads, no tall grass.**

⭐ **`MB_IMPASSABLE_NORTH` IS 100% VACUOUS ON 1F — proven exhaustively.** Of all 204: **175 are
themselves walls** and the other **29 have a wall immediately north**. **Live passable↔passable
crossings blocked by the rule alone: 0.** *(Same verdict as B1F — see the B1F/B2F note §4. ⇒ stop
carrying the raw 178/181/204 counts as a hazard; they are behaviour totals, not live blockers.)*

⭐ **LEDGES: 15 tiles, and 10 are DEAD METATILE DATA.** **(17,38) `MB_JUMP_SOUTHWEST` is NEVER
jumpable** — `GetLedgeJumpDirection` (`event_object_movement.c:7666-7671`) tests only the four
CARDINAL `MB_JUMP_*` functions, so a diagonal ledge behaviour can never fire. Nine more are unusable
because their take-off tile is a wall. **Five are live** — (39-41,27) south and (19,39)/(19,40) west
— and **all five are benign**: every landing tile is already walk-reachable, every take-off tile is
walk-returnable, and none is on a mandatory leg. ⇒ **no one-way trap on 1F.**

**Encounters — and NOT on every tile:** `land_mons`, rate **10**, no water/fishing/rock-smash table.
Only `MB_CAVE` carries `TILE_FLAG_HAS_ENCOUNTERS` among the behaviours present, so **632 of 682
walkable tiles (92.7%) roll encounters and 50 are safe** (region A 449/479, B 175/185, C 16/20).
Species: Golbat / Hariyama / Lairon / Loudred @40, Golbat / Hariyama @38, Zubat / Makuhita / Aron /
Whismur @36.

## §7. WARPS — all five, both directions verified

| tile | elev | behaviour | destination | return lands at |
|---|---|---|---|---|
| **(15,40)** | 3 | `MB_SOUTH_ARROW_WARP` | Ever Grande warp 2 | EGC (18,41) |
| **(39,5)** | 3 | `MB_SOUTH_ARROW_WARP` | Ever Grande warp 3 | EGC (18,27) |
| **(21,32)** | 3 | `MB_LADDER` | B1F warp 5 | B1F **(20,21)** ✔ |
| **(42,38)** | 4 | `MB_LADDER` | B1F warp 2 | B1F **(42,25)** ✔ |
| **(9,14)** | 4 | `MB_LADDER` | B1F warp 4 | B1F **(8,3)** ✔ |

Every warp's `map.json` elevation matches its tile's elevation in `map.bin`. ⇒ **the route
1F(15,40) → (9,14) → B1F → B2F → B1F → 1F(21,32) → (39,5) is exactly what the reachability graph
forces**, not a preference.

## §8. ITEMS — all three OFF the mandatory route
**Max Elixir** ball (40,26), region A — a 66-step side trip vs 44 for the ladder ·
**PP Up** ball (37,39), region C · **hidden Ultra Ball** (30,39), region C **and gated behind
collecting the PP Up first**.

## §9. ⭐ THE FAULT-INJECTION TABLE — why the numbers above are worth anything
From (15,40) carrying elevation 3; baseline **479 tiles**, (9,14)=44, (39,5) unreachable:

| rule broken | tiles | (9,14) | (39,5) | verdict |
|---|---|---|---|---|
| collision | **2065** | 32 | **59** | ✅ live |
| elevation ENTRY | **648** | 44 | **71** | ✅ live |
| **elevation CARRY** | **297** | ⛔ **UNREACHABLE** | ✗ | ✅ **the load-bearing rule** |
| object blocking | 482 | 44 | ✗ | ✅ live (also 20→28 from (42,38)) |
| ledge directionality | 479 | 44 | ✗ | ⚠ no change — **proven redundant**, §6 |
| directional-impassable | 479 | 44 | ✗ | ⚠ no change — **proven vacuous**, §6 |

From (21,32) (baseline 185 / exit 61): elevation-entry off → 648; **elevation-carry off → 8 tiles**.
⇒ **elevation-carry is the rule the entire three-region model rests on**, on this floor as in the
basements — and the two rules that could not be broken were each chased to a proof of why, not left
as "verified".
