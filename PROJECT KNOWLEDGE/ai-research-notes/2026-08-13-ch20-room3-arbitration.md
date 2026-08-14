# §Ch20 Room 3 — arbitration (2026-08-13). ‼ IT INVERTS THE PREVIOUS PASS, AND OUR SPEC WAS RIGHT.

> ‼ **A NOTE, NOT TRUTH.** Decomp (`pret/pokeemerald@master`) **plus our own ROM reader** — the two
> independent authorities that made the Room 1 and Room 2 arbitrations decisive. Nothing here was
> driven live yet.

## ⛔ THE HEADLINE — AND IT IS A CORRECTION TO MY OWN HANDOFF

**`ROOM3 (4,15) → (8,1)` is reachable PUSH-FREE in 18 steps.** Our real planner returns
`OK, 18 waypoints`. **The 7-boulder puzzle is OPTIONAL — it exists solely to avoid the trainers.**

⇒ An earlier pass told me Room 3 *"is NOT the walk the spec calls it"* and that our build spec was
**REFUTED**. **That verdict was itself wrong, and I propagated it into `04-HANDOFF.md` and
`03-PUNCH-LIST.md` before this deeper pass ran.** The spec's *"Room 3 walk (+2 unavoidable
trainers)"* is an **operationally correct** route description. It is *incomplete* (it omits the
optional stealth puzzle) and it has **one real factual error** — the trainers, below.

‼ **The lesson is the one this project keeps paying for:** an agent's REFUTED is a claim like any
other. Room 1's refutation held up because it was checked against two independent authorities;
this one was not, and it was wrong.

## ‼ THE REAL ERROR IN THE SPEC: IT IS **ONE DOUBLE BATTLE**, NOT TWO SINGLES

`CheckForTrainersWantingBattle` (`src/trainer_see.c:191-218`) does **not** stop at the first
trainer:

```c
214:         if (gNoOfApproachingTrainers > 1)
215:             break;
216:         if (GetMonsStateToDoubles_2() != PLAYER_HAS_TWO_USABLE_MONS)
217:             break;
```

Both trainers' sight lines cover the **same** tiles, so with **≥2 usable Pokémon**
`gNoOfApproachingTrainers == 2` and `battle_setup.c:1272-1275` starts a **DOUBLE battle against
Shelly AND Grunt5 simultaneously**.

✅ **Our fork already supports this** — `battle_state.is_double_battle`,
`decide_turn_in_double_battle`, and `modules/story/mossdeep_gym.py:315-369` (the Tate & Liza driver)
rides one out behind a `MINIMUM_USABLE_POKEMON` precondition. **Reuse that precondition.**
⚠ With **fewer than 2 usable**, the engine fires **two sequential singles** instead — survivable,
but a different shape. The precondition is what makes the outcome predictable.

## THE MEASURED FACTS

Map **16 × 17**, 100 walkable tiles, **every walkable tile `elevation=3`** (a pure collision
problem). Decomp and our ROM agree on all 9 objects, all 3 warps, and every elevation.

| local_id | what | tile | note |
|---|---|---|---|
| 1-7 | `PUSHABLE_BOULDER` | `(13,10) (11,10) (12,9) (12,7) (11,8) (12,11) (13,8)` | the optional checkerboard, x=11-13 / y=6-11 |
| 8 | **Shelly** `AQUA_MEMBER_F` | `(9,5)` | `MOVEMENT_TYPE_FACE_LEFT`, sight **6** |
| 9 | **Grunt5** `AQUA_MEMBER_M` | `(5,5)` | `MOVEMENT_TYPE_FACE_RIGHT`, sight **4** |

Warps: `(8,1)` `Non-Animated Door` → `ROOM8 (5,12)`; `(9,13)` `South Arrow Warp` → `ROOM7 (5,1)`;
`(4,15)` `South Arrow Warp` → `ROOM6 (4,1)`. `coord_events`/`bg_events` empty;
`SeafloorCavern_Room3_MapScripts:: .byte 0` — **no map scripts, no `setmetatile`** ⇒ KI-74 N/A.

**Sight is a 1-TILE-WIDE LINE, not a cone.** `GetTrainerApproachDistanceWest/East`
(`trainer_see.c:349-368`) test `trainerObj->currentCoords.y == y` — exact equality, no tolerance.
`MOVEMENT_TYPE_FACE_LEFT/RIGHT` **never rotate** (`event_object_movement.c:3031-3055`), and
`movement_range` has **zero** effect on sight. ⇒ **the cones are permanently fixed.**
⇒ **The effective sight set for BOTH trainers is exactly `{(6,5), (7,5), (8,5)}`.**
It fires **every overworld frame** against the *destination* tile, so **you cannot walk through a
line — every tile entered is a trigger.**

⚠ **A defeated trainer still OCCUPIES its tile.** The trainer flag is separate from
`FLAG_HIDE_SEAFLOOR_CAVERN_AQUA_GRUNTS` (set only when Kyogre escapes,
`Room9/scripts.inc:136`). **Post-battle, Shelly WALKS to `(7,5)`** (`TrainerMoveToPlayer` moves each
trainer `approachDistance-1`), sandwiching the player. The continuation is still clear (6 steps to
`(8,1)`), but ⇒ **recompute anything positional from live `currentCoords`, never from `map.json`.**

⚠ **Two prior claims corrected:** the push-free route does **not** cross all of
`{(6,5),(7,5),(8,5)}` — it enters **exactly one** of them (our planner picks `(6,5)`), and `(8,5)`
is on no push-free route at all (`(8,6)` is `collision=1`).

## THE OPTIONAL STEALTH ROUTE — verified, zero-sight, 5 pushes

Upstream's Emerald branch (`puzzle_solver.py:427-436`) replays **step for step to `(8,1)`, all 5
pushes legal, and zero-sight** — and *every* shortest path on the final leg's DAG avoids the sight
tiles, so the result does not depend on which one our planner picks. Independent Dijkstra over
`(player × boulder-config)` with the sight tiles banned reproduces both prior searches exactly:
**push-optimal 5 pushes / 28 steps**, **step-optimal 26 steps / 6 pushes**. Upstream is
push-optimal. (Note: it is **5** pushes, not 4 — two of its `walk_one_tile("Up")` calls push the
same boulder twice.)

In our API — `strength_push(map, approach_tile, face)`, player ends on the boulder's old tile:

| stand | face | action |
|---|---|---|
| `(4,15)` | — | `navigate_to (13,11)` (13 steps) |
| `(13,11)` | Left | **push** b6 `(12,11)→(11,11)` |
| `(12,11)` | Up | walk → `(12,10)` |
| `(12,10)` | Up | **push** b3 `(12,9)→(12,8)` |
| `(12,9)` | Right | walk → `(13,9)` |
| `(13,9)` | Up | **push** b7 `(13,8)→(13,7)` |
| `(13,8)` | Up | **push** b7 `(13,7)→(13,6)` |
| `(13,7)` | Left | **push** b4 `(12,7)→(11,7)` |
| `(12,7)` | — | `navigate_to (8,1)` (10 steps, zero-sight) |

## ✅ RECOMMENDATION: TAKE THE WALK, NOT THE PUZZLE

**18 steps, 0 pushes, 1 double battle.** Operationally one call:
`navigate_to(SEAFLOOR_CAVERN_ROOM3, (8,1))` riding battles out.

**Why the walk, given we have Strength:** the pushes are **irreversible within a map visit**. Any
mid-sequence derail — a wild encounter (`has_encounters=True` on every non-warp route tile), a
re-navigate, a wrong-direction bump — can **wedge the room**, recoverable only by warping out and
back. The walk has nothing to wedge, and our party is L40-49 against their L35-37.
⇒ **Prefer the reversible route when the irreversible one only buys avoiding a fight we win.**

**Preconditions:** ≥2 usable Pokémon (the double-battle shape); no Strength needed.
**Discriminator for which route ran:** `FlagGet(TRAINER_FLAGS_START + TRAINER_SHELLY_SEAFLOOR_CAVERN)`
and `..._GRUNT_SEAFLOOR_CAVERN_5` — **True** after the walk, **False** after the stealth route.

## THE A/B FOR A ROOM-3 DRIVE — ‼ IT CANNOT BE A SINGLE TILE

**No tile becomes reachable "because the room was solved"** — `(8,1)` is push-free reachable and the
checkerboard's north end already is too. What the pushes buy is a **south↔north shortcut bypassing
row 5** — connectivity a single-tile test cannot see. So:

* **Walk route (recommended):** the A/B is not spatial. Assert
  `calculate_path((4,15) → (8,1))` returns 18 waypoints **containing `(6,5)`** (i.e. the route
  really does enter the sight line), and grade on **both trainer flags being SET** afterwards plus
  "and the bot can continue" out of `(8,1)`.
* **Stealth route (if ever built):** three-point A/B on **`(13,9)`** — `M1` from `(4,15)` NO-PATH;
  `M2` after push 1 **still** NO-PATH (the arm that attributes the opening to push 2); `M3` after
  push 2 OK. Plus: the final `navigate_to((12,7) → (8,1))` path must contain **none** of
  `{(6,5),(7,5),(8,5)}`.

## KI-77: **NONE.** Checked every player position across the whole stealth route against all five
pushed boulders — all stay inside the 20x17 window, the tightest being boulder 6 at `(11,11)` with
the player at `(8,2)` (`y ≤ 11`, exactly on the boundary). The single despawn happens at `(8,1)`,
the exit tile, when the route is already over. **The walk route makes zero pushes, so it cannot fire
at all.** ⚠ Carry forward: the reset means **any retreat after solving loses the pushes**, and every
`FLAG_TEMP_*` boulder respawns on map re-entry regardless.

## THE `(9,13)` HAZARD: real, but **incidental risk is ZERO**

`TryPushBoulder`'s guard (`field_player_avatar.c:763-764`) rejects only `MetatileBehavior_IsNonAnimDoor`,
so **arrow warps are unguarded** and `(9,13)` is a legal boulder destination. **CONFIRMED.** But the
minimal sequence to park one there is **6 pushes / 20 steps**, all southward/westward — the opposite
of every real route. None of upstream's, the push-optimal or the step-optimal routes ever place a
boulder on any of `(9,13)`'s three source tiles. Consequence if it ever happened: the Room 7 retreat
is lost; **forward progress is unaffected**.
✅ **`(8,1)` is PROVEN safe** — it is `MB_NON_ANIMATED_DOOR`, the one case the guard does reject.
✅ **`(4,15)` is structurally out of reach** — 9 pushes minimum just to block `(6,14)`, the sole
row13↔row14 gateway (`(2..5,13)` are `collision=1` `Jump South` ledges).

## RESIDUAL UNCERTAINTY, STATED
1. **The double battle is decomp-derived, not observed live.** ⇒ it is the top pre-registered
   prediction for the Room 3 drive.
2. The `(4,15)`/`(8,1)` hazard searches hit a 4M-state cap — but neither conclusion rests on it
   (`(8,1)` is proven by the guard; `(4,15)` by the 9-push gateway bound).
