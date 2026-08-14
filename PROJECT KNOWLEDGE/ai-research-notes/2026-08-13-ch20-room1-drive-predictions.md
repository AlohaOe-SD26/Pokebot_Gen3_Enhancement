# §Ch20 Room 1 — PRE-REGISTERED predictions for the first drive INSIDE the Seafloor Cavern

> ‼ **WRITTEN BEFORE THE RUN, ON PURPOSE.** §Ch19's hazard checks pre-registered 3 predictions,
> 3/3 held, and two traps got *designed out* instead of debugged. The roster drive did not, and
> **0 of 6** of its after-the-fact predictions fired while the real bug went unnamed by both
> passes. This file is the control on my own reasoning: whatever the run prints, these are the
> claims I was willing to commit to first.
>
> Driver: `--driver ch20room1` (`tools/story-dev/story_harness.py`), anchor `post_dive.ss1`.
> Run it with: `PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room1 --frames 1500000`

---

## WHAT THE RUN IS FOR

`probe_ch20_interior.py` built the cavern Area Atlas from **outside** (the avatar was in Mossdeep).
`get_map_objects()` returns nothing for an unloaded map, so `is_tile_accessible` blocked every
object-template tile and **every NO-PATH it reported is a LOWER BOUND, not a map fact** — the probe
says so itself in its section 3b. This run takes the same measurement from **inside the room**, and
pairs it with an A/B so that a pass cannot be explained by "the corridor was open all along".

---

## THE ARBITRATION THAT SET THE ROUTE (done BEFORE this run, 2026-08-13)

Two sources disagreed about Room 1 and both were in our own repo:

| source | claim |
|---|---|
| upstream `40cakes repo/pokebot-gen3/modules/modes/puzzle_solver.py:370-376` (shipped; their wiki marks Seafloor ✅ for Emerald) | Rock Smash `(5,10)` from `(4,10)`; **push boulder `(5,11)` DOWN** from `(5,10)`; then push `(12,11)` EAST from `(11,11)`; then `(6,2)` |
| our build spec `2026-08-13-ch20-seafloor-cavern-build-spec.md` (lines ~17-24, ~83-84) | an **exhaustive** Sokoban search proves *"the only route into the row-11 corridor requires pushing boulder `(5,11)` **north**"* |

**RULING: UPSTREAM IS CORRECT, and the spec's uniqueness claim is REFUTED.** Read from the decomp
(`data/maps/SeafloorCavern_Room1/map.json`) and independently from our own ROM: `(5,10)` and
`(5,12)` are **both** `collision=0 elevation=3 'Cave'`, so the boulder is legally pushable in
**either** direction and both leave the player on `(5,11)` with the corridor open. The spec's search
was **not exhaustive** — it never evaluated the south push. Its *tile* facts are right
(`(7..10,12)` really are `Impassable North` with `collision=1`; row 11 really is a one-tile corridor
whose only west entrance is `(5,11)→(6,11)`), and its **east** analysis is right (pushing east jams
the boulder against boulder 2 and strands the player at `(10,11)`). It is the **"every alternative
was searched"** sentence that is false.

⇒ **Consequence beyond Room 1, and it is the more important half:** the same document asserts
"exhaustive search" sequences for **Room 2** and **Room 8** (9 pushes). Those are now
**unaudited claims from a source with a demonstrated false-uniqueness result**. Arbitrate each one
the same way before driving it.

**The object table both sources' data agree on** (decomp `map.json` + our ROM reader):

| local_id | graphics | tile | flag | note |
|---|---|---|---|---|
| 1 | `PUSHABLE_BOULDER` | `(5,11)` | `FLAG_TEMP_11` | the corridor plug |
| 2 | `PUSHABLE_BOULDER` | `(12,11)` | `FLAG_TEMP_12` | blocks the climb up x=12 |
| 3 | `BREAKABLE_ROCK` | `(5,10)` | `FLAG_TEMP_13` | Rock Smash — mandatory |
| 4 | `AQUA_MEMBER_M` | `(8,6)` | `FLAG_HIDE_SEAFLOOR_CAVERN_AQUA_GRUNTS` | Grunt1, sight 2, rotates — on the row-7 walk |
| 5 | `AQUA_MEMBER_M` | `(15,10)` | same | Grunt2 — off-path |

---

## THE PREDICTIONS

| # | prediction | why | if it FAILS, what that means |
|---|---|---|---|
| **P1** | *(control)* The reused ingress reproduces: `legs=5/5`, surfacing in `SEAFLOOR_CAVERN_ENTRANCE (10,17)`. | It is the proven `--driver ch20dive` path, now called through `_ingress()` instead of inline. | Either the extraction broke it (checked separately by re-running `ch20dive` to `6/6`) or the dive route is not as stable as one PASS suggested. **Everything below is void.** |
| **P2** | Navigating `ENTRANCE (10,1)` lands the bot in `SEAFLOOR_CAVERN_ROOM1`, arriving at **`(5,18)`**. | `(5,18)` is ROOM1's `South Arrow Warp` back to the entrance, so it is the natural destination of the entrance's north warp. **Derived, not measured** — this is the weakest link in the chain. | The warp geometry is not what the static table implies. That would be the *third* time the cavern's warps lied (both dive edges were runtime `setdivewarp`s), and it would make "arrival tile" a thing every leg must measure rather than assume. |
| **P3** | `get_map_objects()` inside ROOM1 returns the **five** objects above, at their template coordinates. | Decomp + our ROM agree, and no `setmetatile`/map script exists on this map (`SeafloorCavern_Room1_MapScripts:: .byte 0`). | ‼ Most interesting failure: **the two grunts are absent.** They are hidden by `FLAG_HIDE_SEAFLOOR_CAVERN_AQUA_GRUNTS`, and the *entrance* grunt is already known to be permanently hidden by a flag set in the same script that hands over HM Dive. If these are hidden too, the spec's "unavoidable trainers" table is dead content and P6 is void. |
| **P4** | ‼ **THE DISCRIMINATING ONE.** `calculate_path(arrival → (11,11))` is **NO-PATH before** the smash+push and **OK after**, with live objects on both arms. | The corridor's only west entrance is `(5,11)`, plugged by boulder 1, and its approach `(5,10)` is plugged by the rock. `(6,10)` and `(6,12)` are `collision=1`. | If **before** already returns a path, the puzzle story is wrong and `probe_ch20_interior`'s lower bound was loose in the other direction. If **after** still fails, our planner cannot see a pushed boulder's vacated tile — a pathfinder defect, not a route problem. |
| **P5** | Both pushes succeed through `strength_push`, and the boulders end at **`(5,12)`** and **`(13,11)`**, verified by `local_id`. | `strength_push` is driven and proven (`#24-strength`, Magma Hideout) and judges the world by identity. Strength is already active after the first push (`FLAG_SYS_USE_STRENGTH` is never cleared). | A silent no-move means the destination was blocked — most likely the boulder was pushed by an *earlier accidental step* rather than by the call, which is precisely why the check is by `local_id` and destination, not "the old tile is empty". |
| **P6** | ≥1 trainer battle fires, from Grunt1 at `(8,6)` during the row-7 walk, and `_navigate_riding_out` rides it out. | Sight radius 2, rotating, standing 1 tile off the row-7 corridor. | Void if P3's grunts are hidden. Otherwise a hang here is KI-38's family and the run should be read as a navigation defect, not a route defect. |
| **P7** | The run ends in `SEAFLOOR_CAVERN_ROOM2` at **`(10,7)`**, controllable, and takes a real step. | The spec's leg-3 completion condition. | If `(10,7)` is wrong, that is the spec's *second* coordinate error (it already corrected `(16,42)`→`(17,42)`), and every arrival coordinate in it becomes suspect. |

---

# ✅ RESULT — `ACCEPTANCE: PASS` ON THE FIRST DRIVE (2026-08-13). 6 of 7 predictions held.

```
[ch20room1] INGRESS OK at=('SEAFLOOR_CAVERN_ENTRANCE', (10, 17)) (ch20dive legs 5/5)
[ch20room1] LEGA at=('SEAFLOOR_CAVERN_ROOM1', (5, 18)) in_room1=True
[ch20room1] A/B BEFORE (5,18) -> (11,11): PathFindingError: Could not find a path ... (source collision=0)
[ch20room1] SMASH ok=True  rock local_id=3 present=False
[ch20room1] PUSH1 ok=True  boulder local_id=1 at=(5, 12)
[ch20room1] A/B AFTER  (5,11) -> (11,11): OK len=6 (source collision=0)
[ch20room1] PUSH2 ok=True  boulder local_id=2 at=(13, 11)
[ch20room1] LEGC at=('SEAFLOOR_CAVERN_ROOM2', (10, 7)) in_room2=True
[ch20room1] CAN-CONTINUE stepping (10,7) -> (10,6) tile_type='Cave' ... moved=True manual=False
[ch20room1] RESULT in_room1=True ab_before=False ab_after=True smashed=True pushed1=True
            pushed2=True in_room2=True can_continue=True
[ch20room1] ACCEPTANCE: PASS
```

| # | verdict | evidence |
|---|---|---|
| P1 | ✅ HELD | `legs 5/5`, surfaced at `SEAFLOOR_CAVERN_ENTRANCE (10,17)`. The extraction into `_ingress()` was separately proven neutral: `--driver ch20dive` re-ran to `legs=6/6 at_entrance=True got_out=True can_continue=True ACCEPTANCE: PASS`, matching its documented prior result. |
| P2 | ✅ HELD, exactly | `SEAFLOOR_CAVERN_ROOM1 (5,18)` — the derived arrival tile was right. |
| P3 | ⛔ **REFUTED — and it is the most useful thing in this run.** | On arrival the dump showed **2 of 5** objects: `local_id=1 (5,11)` and `local_id=2 (12,11)`, both boulders. The **rock (id 3) and both grunts (ids 4, 5) were ABSENT** — yet the rock was demonstrably there (the smash removed it) and both grunts appeared in later dumps and one of them battled. ⇒ **`get_map_objects()` is a CAMERA-RANGE WINDOW, not a map inventory.** From `(5,18)` the objects at `y=10` and `y=6` are simply outside the spawn range. See **KI-77**. |
| P4 | ✅ **HELD — the discriminating one** | Same call, same target, live objects on both arms: **BEFORE `PathFindingError`** from `(5,18)`, **AFTER `OK len=6`** from `(5,11)`. This converts `probe_ch20_interior.py`'s Room 1 NO-PATH from a **lower bound** into a **measured fact**, and rules out "the corridor was open all along". |
| P5 | ✅ HELD | Boulder `local_id=1` moved `(5,11) → (5,12)`; boulder `local_id=2` moved `(12,11) → (13,11)`. Both verified **by identity**, both through `strength_push`, not `walk_one_tile`. ⇒ **The upstream/south arbitration is confirmed live**, not just on paper. |
| P6 | ✅ HELD | Two `TrainerApproachListener.handle_trainer_approach` engagements; `NICK got $720 for winning!`. `_navigate_riding_out` rode them out and the route continued. |
| P7 | ✅ HELD, exactly | `SEAFLOOR_CAVERN_ROOM2 (10,7)`, then a real step to `(10,6)` (`'Cave'`, non-warp), `manual=False`. |

## ‼ WHAT P3's FAILURE MEANS FOR EVERYTHING ELSE

`map_path.calculate_path` builds `active_objects` from the very same `get_map_objects()`
(`modules/map_path.py:811-818`), and then:
* `:844-853` — a tile whose object is **not** in `active_objects` is **BLOCKED at its TEMPLATE
  position**, and
* `:861` — an object that **is** active blocks its **live** `current`/`previous` coordinates.

So the planner's picture of a pushed boulder **flips with the camera**: while the boulder is on
screen its real tile is blocked and its old tile is free; once it scrolls out of range, its **old
tile is blocked again and its real tile becomes free**. Room 1 never exercised this (the route
after the pushes goes up x=12 and west along row 7, nowhere near `(5,11)`), which is exactly why it
had to be *measured* rather than inferred from a green run. **Room 8's nine pushes in a 48-tile
room are where this is armed.** Filed as **KI-77**.

## WHAT THIS RUN DELIBERATELY DOES **NOT** CLAIM

* **It is not §Ch20.** No chapter module is written, nothing is wired into `story_mode.py`, and the
  run injects Dive with a debug write (KI-63's acquisition is proven separately by
  `--driver divelearner`, not here).
* **It does not prove the way back out of Room 1.** Puzzle state resets on map re-entry
  (`FLAG_TEMP_*`), so a retreat costs the puzzle again. The acceptance proves the bot can *move* in
  Room 2, not that it can get home.
* **It says nothing about Rooms 3-9.** In particular the current mazes (Rooms 6/7) are still
  **planner-level only** — proven routable by `calculate_path`, never walked (KI-76).
