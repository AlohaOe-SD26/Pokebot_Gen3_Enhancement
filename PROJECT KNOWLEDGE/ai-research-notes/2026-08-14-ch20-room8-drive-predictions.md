# §Ch20 Room 8 drive — PRE-REGISTERED predictions (2026-08-14)

> ‼ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. Written BEFORE the first
> `--driver ch20room8` run, per the house rule: *write the predicted failure down before the run.*
> The raw transcript of the run(s) will be appended below the predictions, and each prediction
> graded against it. Sources: `2026-08-13-ch20-decomp-blockers-and-room8.md` (the adjudicated
> 9-push table), KI-77's corrected despawn-window entry, and the live results of
> `--driver ch20room1/2/6/3` (2026-08-13).

## The thing under test

`--driver ch20room8` (NEW): re-prove Rooms 1 → 2 → 6 → 3 from scratch, then execute the
**adjudicated 9-push sequence** in Room 8 (OURS, 9 pushes — not upstream's 10), take the `(5,2)`
door into **ROOM 9**, and prove "the bot can continue" with a real step there.
⛔ Step 9 faces **LEFT, never UP** — `(5,4)` pushed north lands on `(5,3)` and permanently seals
the room. ✅ A jam IS recoverable (exit to Room 3 via `(5,12)`, re-enter, all twelve boulders
respawn) — the driver wires that as its failure handler and retries ONCE.

An independent adversarial agent was dispatched BEFORE the drive to refute the 9-push table
offline (per-step legality + approach reachability + final connectivity).
✅ **ITS VERDICT (landed before the drive): SURVIVES.** Two independent sources — our own ROM
reader (`get_map_data`, anchored on `post_dive.ss1`) and the decomp's
`SeafloorCavern_Room8/map.json` — agree exactly on all twelve boulder templates:
`FLAG_TEMP_11 (4,7)`, `12 (5,7)`, `13 (6,7)`, `14 (3,6)`, `15 (7,6)`, `16 (4,5)`, `17 (5,5)`,
`18 (6,5)`, `19 (3,4)`, `1A (4,4)`, `1B (6,4)`, `1C (7,4)`. A programmatic simulation of the
9-push sequence (boulder+1/player+1 rule, occupancy + collision + one-way `Jump South` ledge
honored, BFS approach-reachability per step) passes every step; after push 9 `(5,3)` is
untouched and `(5,2)` is BFS-reachable from `(5,4)`. ‼ **The checker was itself fault-tested**:
a deliberately reordered variant (push onto `(4,4)` before it is vacated) is correctly REFUSED —
so the PASS is not a rubber stamp. **Limits, stated by the agent:** offline reader-level proof,
not a live emulator A/B; the engine push rule itself was taken as given (it is measured live in
Rooms 1/2). Push 6 vacating `(4,4)` before push 9 reuses it is load-bearing and correctly
sequenced.

## Pre-registered predictions

| # | prediction | source |
|---|---|---|
| P1 | Rooms 1, 2, 6, 3 re-solve cleanly (they are `FLAG_TEMP_*` rooms and reset on every load), taking the re-proof counts to R1 n=8, R2 n=5, R6 n=4, R3 n=3. | 4 prior drives |
| P2 | Arrival `SEAFLOOR_CAVERN_ROOM8 (5,12)`, tile `'South Arrow Warp'`, and it does NOT warp on arrival (arrow warps need a HELD direction). | decomp + live R2/R6 arrivals |
| P3 | ‼ The object dump AT ARRIVAL shows **exactly 8** boulders: the despawn window is `y ∈ [py-7, py+9]`, so from `(5,12)` rows `y ≤ 4` are out of range — and the template table (measured, below) puts exactly four boulders on `y=4` (`(3,4)`, `(4,4)`, `(6,4)`, `(7,4)`). They are INVISIBLE there, not absent. From `(5,8)` (step 0's end) all 12 are in range. A "12 at arrival" assertion would be a false alarm; the driver asserts the count from `(5,8)` instead. | KI-77's window + the measured templates |
| P4 | The step-0 walk `(5,12) → (5,8)` routes around the `Jump South` ledge `(4,10)-(6,10)` via `x=3` or `x=7` (northbound cannot jump it). | ROM ledge confirm |
| P5 | All 9 pushes succeed through `strength_push`, each boulder verified by `local_id` on its destination. Only push 1 pays the Strength prompt (the flag was cleared by the warp into the room — measured in Room 2). | Blocker-1 measurement |
| P6 | After push 9: `calculate_path((5,4) → (5,2))` is OK and no object sits on `(5,3)`. | the adjudicated table |
| P7 | Navigating onto `(5,2)` (Non-Animated Door) fires the warp; arrival in `SEAFLOOR_CAVERN_ROOM9`, predicted `(5,4)`, whose own `South Arrow Warp` does NOT bounce us back. | decomp warp table |
| P8 | Wild encounters (Zubat, rate 4) may fire mid-sequence; `strength_push`'s re-navigate + idempotency rides them out (already proven between two pushes in Room 2). | live R2 result |
| P9 | Can-continue: a real step onto a live-derived non-warp neighbour in Room 9 succeeds. | standing rule |

## Pre-registered failure modes (what a FAIL will look like, written first)

* **A refused push** = `strength_push` raises `BotModeError` naming the tiles (never a silent
  hang — that is upstream's `walk_one_tile` failure shape, not ours). The driver's response is
  the RECOVERY HANDLER (exit `(5,12)` holding Down → Room 3 → re-enter → verify respawn → retry
  once), never improvisation near `(5,3)`.
* **A planner mis-route on step 0** (tries to jump the ledge northward) = `PathFindingError` or
  arrival somewhere ≠ `(5,8)`. That would be a REAL pathfinder finding, filed, not patched over.
* **KI-77 shape**: if a push fails because the boulder "is not there" while the player stands
  adjacent, that refutes the window model (adjacent objects are always in range) — file it.
* **Fault injection** (`POKEBOT_CH20_FAULT=room8`): attempt 1 aborts the sequence after push 4,
  so the recovery handler + retry path is EXERCISED, not just written. A fault-mode run must
  still end with an honest RESULT line (`recovered=True attempts=2`) and never derail.

## Run transcript & grading

### Run 1 — FAULT-INJECTED (`POKEBOT_CH20_FAULT=room8`), 2026-08-14 → `ACCEPTANCE: PASS`

The recovery handler was the thing under test, and it was EXERCISED, not just written:

    [ch20room8] ARRIVAL at=(5, 12) tile_type='South Arrow Warp' boulders_visible=8
    [ch20room8] STAGED ok=True boulders_visible=12
    [ch20room8] PUSH1..PUSH4 ok (boulders on destination, verified by local_id)
    [ch20room8] ‼ FAULT: abandoning the sequence before push 5 on purpose
    [ch20room8] ATTEMPT 1 FAILED after 4 pushes: fault-injected stop before push 5
    [ch20room8] RECOVERY (attempt 1): exiting via (5, 12), re-entering through ROOM3 (8, 1)
    [ch20room8] RECOVERY back_in_room8=True boulders_visible=8 recovered=True
    [ch20room8] STAGED ok=True boulders_visible=12
    [ch20room8] PUSH1..PUSH9 ok  (attempt 2, from respawned templates)
    [ch20room8] EXIT-PATH (5, 4) -> (5, 2): OK len=2   boulder_on_(5,3)=False
    [ch20room8] ROOM9 at=('SEAFLOOR_CAVERN_ROOM9', (5, 4)) in_room9=True
    [ch20room8] CAN-CONTINUE stepping (5, 4) -> (5, 3) tile_type='Cave'  moved=True
    [ch20room8] RESULT room3_ok=True pushes=9/9 attempts=2 recovered=True exit_path=True
                in_room9=True can_continue=True
    [ch20room8] ACCEPTANCE: PASS

Notable beyond the predictions:
* ‼ **The recovery's derived-direction branch never executed** — the walk ONTO `(5,12)` fired
  the arrow warp by itself (the walker holds the direction through the step, and `TryArrowWarp`
  fires on a held direction). The map-check-first structure handled it cleanly. The originally
  hardcoded `_walk_through_warp("Down")` (removed after adversarial review) would have blindly
  pressed Down while ALREADY standing in Room 3.
* **Mid-sequence boulder state after 4 real pushes did NOT survive the recovery** — attempt 2's
  pushes 1-4 found every boulder back on its template tile and re-pushed them, which is the
  respawn claim proven by pushes rather than by a dump.
* Battles this run: the Route 127 wild, the Room 1 grunt, a Room 2 wild, and the Room 3
  DOUBLE at `(6,5)` — `saw_double=True` again (n=4 for the double-battle claim, counting
  ch20room3 runs).

### Run 2 — CLEAN, 2026-08-14 → `ACCEPTANCE: PASS`, first attempt

    [ch20room8] ROOMS 1+2+6+3 re-proven; standing in ('SEAFLOOR_CAVERN_ROOM8', (5, 12))
    [ch20room8] ARRIVAL at=(5, 12) tile_type='South Arrow Warp' boulders_visible=8
    [ch20room8] STAGED ok=True boulders_visible=12
    [ch20room8] PUSH1 ok stand=(5, 8) face=Up    boulder (5, 7)->(5, 6) on_destination=True
    [ch20room8] PUSH2 ok stand=(5, 7) face=Left  boulder (4, 7)->(3, 7) on_destination=True
    [ch20room8] PUSH3 ok stand=(4, 6) face=Right boulder (5, 6)->(6, 6) on_destination=True
    [ch20room8] PUSH4 ok stand=(5, 6) face=Up    boulder (5, 5)->(5, 4) on_destination=True
    [ch20room8] PUSH5 ok stand=(5, 5) face=Left  boulder (4, 5)->(3, 5) on_destination=True
    [ch20room8] PUSH6 ok stand=(4, 5) face=Up    boulder (4, 4)->(4, 3) on_destination=True
    [ch20room8] PUSH7 ok stand=(5, 5) face=Right boulder (6, 5)->(7, 5) on_destination=True
    [ch20room8] PUSH8 ok stand=(6, 5) face=Up    boulder (6, 4)->(6, 3) on_destination=True
    [ch20room8] PUSH9 ok stand=(6, 4) face=Left  boulder (5, 4)->(4, 4) on_destination=True
    [ch20room8] EXIT-PATH (5, 4) -> (5, 2): OK len=2   boulder_on_(5,3)=False
    [ch20room8] ROOM9 at=('SEAFLOOR_CAVERN_ROOM9', (5, 4)) in_room9=True
    [ch20room8] CAN-CONTINUE stepping (5, 4) -> (5, 3) tile_type='Cave'  moved=True
    [ch20room8] RESULT room3_ok=True pushes=9/9 attempts=1 recovered=False exit_path=True
                in_room9=True can_continue=True
    [ch20room8] ACCEPTANCE: PASS

## Grading — 9 of 9 pre-registered predictions HELD

| # | verdict | evidence |
|---|---|---|
| P1 | ✅ HELD | Rooms 1+2+6+3 re-proven in all three of this session's runs (neutrality + fault + clean). Counts now: R1 n=10, R2 n=7, R6 n=6, R3 n=5, R8 n=2. |
| P2 | ✅ HELD | `ARRIVAL at=(5,12) tile_type='South Arrow Warp'`, no bounce, both runs. |
| P3 | ✅ HELD **exactly** | `boulders_visible=8` at arrival, `12` from `(5,8)` — the KI-77 window predicted the split to the boulder. |
| P4 | ✅ HELD | staging arrivals `ok=True` every attempt (3 stagings across two runs); no ledge bounce. |
| P5 | ✅ HELD | 9/9 pushes, every boulder `on_destination=True` by `local_id`, both runs (22 pushes total incl. the fault run's attempt 1). |
| P6 | ✅ HELD | `EXIT-PATH (5,4) -> (5,2): OK len=2`, `boulder_on_(5,3)=False`, both runs. |
| P7 | ✅ HELD | `ROOM9 (5,4)` exactly, arrow warp did not bounce, both runs. |
| P8 | ✅ HELD (weakly exercised) | wild battles fired en route (Route 127, Room 2) but none landed BETWEEN two Room 8 pushes this session — the between-push case remains proven only by Room 2's earlier run. |
| P9 | ✅ HELD | `CAN-CONTINUE moved=True (5,4)->(5,3)` both runs. |
| (fault) | ✅ AS DESIGNED | attempt 1 aborted before push 5, recovery `recovered=True`, attempt 2 clean 9/9, honest `RESULT attempts=2`. |

⇒ **The queue's next increment is ROOM 9**: the 62-step walk to the trigger `(17,42)` (⛔ not
`(16,42)` — plain floor), Archie, Kyogre, `VAR_ROUTE128_STATE == 2` grading, and the atoll exit
(step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`). See the decomp-blockers note.
