# §Ch20 Room 6 — PRE-REGISTERED predictions for THE FIRST EXECUTED CURRENT CROSSING (2026-08-13)

> Driver: `--driver ch20room6`, anchor `post_dive.ss1`.
> `PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room6 --frames 2500000`
> Third in the series after Room 1 (6/7 held) and Room 2 (10/10 held). The Room 1 run's single
> FAILED prediction is what produced KI-77, which is the entire reason these get written first.

## WHY THIS IS ITS OWN INCREMENT

Everything known about Rooms 6/7 is **planner-level only**. `probe_ch20_currents.py` put 4
pre-registered predictions to `calculate_path` and got 4/4 from *outside* the cavern;
`--driver ch20room2` reproduced one from *inside* (`(11,21) → (4,1)` = `OK len=13`).
**A PLAN IS NOT A WALK.** No current has ever been executed in this project, and KI-76's
correctness half is open. Bundling this with Room 3 would have made a failure unattributable.

## THE PREDICTIONS

| # | prediction | why | if it FAILS |
|---|---|---|---|
| **R1** | *(control)* Rooms 1 **and** 2 re-solve: `room2_ok=True`, `pushes=3/3`. | Both are `FLAG_TEMP_*` rooms that reset on every map load, so this driver redoes them from scratch — Room 1 reaches **n=5**, Room 2 **n=2**. Also proves the `_solve_room2()` extraction neutral. | Everything below is void, and the extraction broke something two green runs did not catch. |
| **R2** | Room 6 entry is `(11,21)`. | Room 2's `(6,1)` door resolves there; measured live in the Room 2 drive. | The warp table lies again — it already lied at both ends of the dive. |
| **R3** | The PLAN exists: `calculate_path((11,21) → (4,1))` returns `OK len≈13`. | Already measured from inside the room. Restated so the plan/walk comparison has both halves in one transcript. | The planner is not stable across runs, which would be a bigger finding than the crossing. |
| **R4** | ‼ **THE DISCRIMINATING ONE: `crossed=True` — the avatar actually WALKS to `(4,1)`.** | The decomp says `DoForcedMovement` returns `FALSE` on collision and `PlayerStep` hands control back **on that tile, the same frame** — swept over all 108 Room-6 current tiles, zero infinite loops. So the terrain cannot trap the bot. Whether **our executor** agrees is exactly what is unmeasured. | **KI-76's "a plan is not a walk" becomes a MEASURED defect**, and Rooms 6/7 need a solver after all — reversing the "no solver needed" conclusion in `03-PUNCH-LIST.md`. This is the single most valuable outcome either way. |
| **R5** | The `(4,1)` transition fires and we land in `SEAFLOOR_CAVERN_ROOM3 (4,15)`. | Room 3's `(4,15)` is a `South Arrow Warp` back to `ROOM6 (4,1)`; warps are normally paired. ‼ **Arrow warps need a HELD direction**, not a step — `TryArrowWarp` (`field_control_avatar.c:688-700`) fires only while `heldDirection` matches facing. The driver therefore **derives the hold direction from the tile's own name** rather than guessing, so it is correct whichever kind `(4,1)` is. | If `(4,1)` is neither an arrow warp nor a door, the room graph is wrong. |
| **R6** | ‼ **A LIVE CROSS-CHECK OF THE ROOM 3 ARBITRATION, FOR FREE:** `calculate_path((4,15) → (8,1))` returns **≈18 waypoints** *and* the path **contains `(6,5)`**. | The Room 3 note claims (a) Room 3 is crossable **push-free**, so its 7-boulder puzzle is optional, and (b) the push-free line **unavoidably** enters a trainer sight tile. **Neither has been checked live.** One call settles both. | ⛔ A `PathFindingError` **REFUTES the Room 3 arbitration** and makes the 7-boulder puzzle mandatory. A path that does **not** contain `(6,5)` means the double battle is avoidable without Strength — also a correction, in the opposite direction. |
| **R7** | `can_continue=True` — a real step in Room 3. | The standing rule; three chapters have shipped stranded. | Room 3's arrival pocket is more constrained than the grid suggests. |
| **R8** | ≥0 water encounters in Room 6; if any fire the run survives them. | `gSeafloorCavern_Room6` has a full `water_mons` table — ‼ **the build spec's "encounters are on land in Rooms 1-8" is wrong.** A battle can interrupt a slide. | A stall mid-slide is a driver defect: nothing may assume the avatar stayed where a plan put it. |

## THE HAZARD THIS RUN DELIBERATELY DOES NOT TAKE

‼ **ROOM 6 IS ONE-WAY.** `(11,21) → (4,1)` works; the reverse does not. Once across, the bot
**cannot** return the way it came — the retreat is Room 6's *other* warp `(14,8)`.
‼ **KI-76's OPEN half is armed in precisely this room:** a slide that ENDS ON A WARP is never
penalised, A* is ~9× biased toward long slides under `avoid_encounters`, and `(14,8)` is a
water-level door that **9 of the room's 108 chains end on**. Our route is one of the four already
asserted trap-free by `probe_ch20_currents.py` section 3b — but **that assertion is per ROUTE**, so
it is re-checked live here rather than assumed. ⇒ **Re-run that assertion for any NEW Room 6 route.**

---

# ✅ RESULT — `ACCEPTANCE: PASS` ON THE FIRST DRIVE (2026-08-13). **8 of 8 predictions held.**

```
[ch20room2] RESULT room1_ok=True m1=False m2=False m3=True pushes=3/3 in_room6=True
            can_continue=True                                   <- R1 control: the extraction is neutral
[ch20room2] ACCEPTANCE: PASS
[ch20room6] ROOMS 1+2 re-solved ok=True (both reset on every map load)
[ch20room6] ROOM6 entry=(11, 21) tile_type='South Arrow Warp'
[ch20room6] PLAN (11, 21) -> (4, 1): OK len=13
[ch20room6] CROSSING at=('SEAFLOOR_CAVERN_ROOM3', (4, 15)) crossed=True
[ch20room6] ROOM3 at=('SEAFLOOR_CAVERN_ROOM3', (4, 15)) in_room3=True
[ch20room6] ROOM3-WALK (4, 15) -> (8, 1): OK len=18 contains (6, 5)
[ch20room6] RESULT room2_ok=True crossed=True in_room3=True room3_walk=True can_continue=True
[ch20room6] ACCEPTANCE: PASS
```

## ‼ R4 — THE EXECUTOR CROSSES A CURRENT. KI-76's "a plan is not a walk" DOES NOT BITE HERE.

The avatar went from `ROOM6 (11,21)` to `SEAFLOOR_CAVERN_ROOM3 (4,15)`. **The only route between
them is across the current maze**, so the endpoint proves the crossing.
⚠ **State it precisely:** what is proven is the ENDPOINT, not the intermediate slide behaviour —
no per-slide telemetry was captured, and the planner's 13 waypoints were not compared step-by-step
against the executor's actual path. "The executor can cross THIS current maze on THIS route" is the
claim; "our `forced_movement_to` model matches the game tile-for-tile" is **not**.

✅ **The `03-PUNCH-LIST.md` conclusion that Rooms 6/7 "need no solver" now rests on a WALK, not a
plan.** It was previously planner-level only.

## ‼ THE CROSSING CARRIED STRAIGHT THROUGH THE WARP — and a design decision saved the run

The walk did not stop on `ROOM6 (4,1)`; it ended **already inside Room 3**. Twenty minutes before
the run I widened the `crossed` test to accept "or we are now in ROOM3", reasoning that this driver
measures the CROSSING and that reaching Room 3 is a strictly stronger proof of it. A strict
`where == (ROOM6, (4,1))` test would have printed **FAIL over a crossing that worked perfectly** —
the project's own rule: *assert the outcome, not the position you expected.*
⚠ **Consequence for coverage:** the arrow-warp branch (derive the hold direction from the tile's
own name, then `_walk_through_warp`) **never executed** and is therefore **UNTESTED**. It is
correct-by-construction and harmless, but do not describe it as proven.

## ✅ R6 — THE ROOM 3 ARBITRATION IS CONFIRMED LIVE, IN THE SAME RUN, FOR FREE

`calculate_path((4,15) → (8,1))` returned **`OK len=18`** and the path **contains `(6,5)`** —
exactly what the arbitration predicted. Both of its load-bearing claims are now measured:

1. **Room 3 is crossable PUSH-FREE** ⇒ its **7-boulder puzzle really is OPTIONAL**. The earlier
   pass that called our build spec "REFUTED" was itself wrong, and this is the live proof.
2. **The push-free line unavoidably enters a trainer sight tile** ⇒ the walk route **must** take
   the battle. (Decomp says that battle is a single **DOUBLE** battle — still unobserved live.)

## THE OTHER PREDICTIONS
* **R1 ✅** — Rooms 1 and 2 re-solved from scratch. **Room 1 is now n=5, Room 2 n=2**, and the
  `_solve_room2()` extraction is proven behaviour-neutral by the `ch20room2` arm.
* **R2 ✅** — entry `(11,21)`, `'South Arrow Warp'`. **R3 ✅** — `OK len=13`, stable across runs.
* **R5 ✅** — landed `ROOM3 (4,15)`. **R7 ✅** — real step taken, not Manual.
* **R8 — vacuously held:** no water encounter fired on this pass. The `water_mons` table is real,
  so this is luck, not safety; a battle mid-slide remains untested.

## WHAT THIS RUN DOES NOT CLAIM
* **It does not build Room 3.** R6 is a *plan*, not a walk; Room 3 gets its own driver.
* **It is not §Ch20.** No chapter module, nothing wired, Dive still injected.
* **It does not test the retreat** through `(14,8)`, and it cannot: the room is one-way.
