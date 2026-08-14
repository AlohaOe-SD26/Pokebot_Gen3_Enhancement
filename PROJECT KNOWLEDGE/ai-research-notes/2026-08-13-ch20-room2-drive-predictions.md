# §Ch20 Room 2 — PRE-REGISTERED predictions (written BEFORE the run, 2026-08-13)

> Driver: `--driver ch20room2`, anchor `post_dive.ss1`.
> `PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room2 --frames 2000000`
> Companion to `2026-08-13-ch20-room1-drive-predictions.md`, where the same method scored 6/7 and
> the single FAILED prediction is what produced **KI-77**. That is the point of writing these down.

## THE ARBITRATION THAT SET THIS ROUTE — and unlike Room 1's, it came out CLEAN

Room 1's arbitration **refuted** our build spec. Room 2's **confirms** everything: the decomp
(`data/maps/SeafloorCavern_Room2/map.json`) and our own ROM reader agree on all **8 object events**,
upstream `puzzle_solver.py:395-402` is correct **step for step**, and the spec's Room 2 line agrees
too. Two independent decomp passes also **both retracted** an earlier claim that `(9,3)` offered a
second east↔west link: smashing `(9,3)` alone leaves `(6,1)` unreachable, so **`(8,7)` really is the
sole crossing reachable from the arrival tile**.

Measured facts the run is built on:
* `id 4 PUSHABLE_BOULDER (4,5) FLAG_TEMP_15` needs **exactly three** pushes north. `(4,4)`, `(4,3)`,
  `(4,2)` are each `collision=0 elevation=3 'Cave'`; **`(4,1)` is `collision=1 elevation=0`, so a
  fourth push is illegal and would fail SILENTLY.** Door `(6,1)` reachability after each push:
  1 → NO, 2 → NO, **3 → YES**. Zero slack.
* `id 6 BREAKABLE_ROCK (8,7) FLAG_TEMP_18`. Rows 4-6 are walled at x=8,9.
* **Zero trainers and zero scripts** (`scripts.inc` is `.byte 0`; `coord_events`/`bg_events` empty).
* `(10,7)` — the arrival tile — is `MB_SOUTH_ARROW_WARP` back to Room 1. Arrow warps need
  stand-and-**hold**, not a step, so an accidental step will not bounce us out.

## THE PREDICTIONS

| # | prediction | why | if it FAILS |
|---|---|---|---|
| **Q1** | *(control)* Room 1 re-solves: `room1_ok=True`. | It has now passed twice. This driver re-solves it because `FLAG_TEMP_*` objects respawn on every map load. | Room 1 is flakier than two passes suggested, and every Room 2 number is void. Would take Room 1 from n=2 to a contested result. |
| **Q2** | ‼ **THE DISCRIMINATING ONE. `STRENGTH-FLAG after the ROOM1→ROOM2 warp` is `False`.** | Two sources in OUR OWN repo contradict each other. `modules/story/early_game.py:7638-7645`/`:7799` say `FLAG_SYS_USE_STRENGTH` is *"NEVER CLEARED … once per SAVE, not once per map"*, on the strength of a decomp-wide search for **`clearflag`**. An adversarial decomp pass says `ClearTempFieldEventData()` (`src/event_data.c:39-48`) calls **`FlagClear`**(FLAG_SYS_USE_STRENGTH) from `LoadMapFromWarp` (`src/overworld.c:848`) — on **every warp**. ⇒ I predict the adversarial pass is right: a search for the SCRIPT MACRO cannot find a C function call, so our search would have missed it **by construction**. Corroboration: upstream re-arms Strength in *every* room (`puzzle_solver.py:373, 399, 429, 440`), which is pointless if it persists. | If `True`, our comment is right and the adversarial pass invented a call chain — which would be a serious mark against everything else it reported, including the Route 128 atoll and the Rock Smash prompt. **Either way the production CODE is safe**: `strength_push` re-checks the flag on every call and re-activates. This measures a DOC claim, not a defect. |
| **Q3** | `M1` — `calculate_path((10,7) → (6,2))` NO-PATH. | Rock `(8,7)` and boulder `(4,5)` both seal it; the start component is 9 tiles. | The room is not sealed as measured and the whole Room 2 model is wrong. |
| **Q4** | ‼ `M2` — after the smash alone, `calculate_path((4,6) → (6,2))` **still** NO-PATH. | Smashing grows the reach 9 → 21 tiles, and `(6,2)` is not in it. | **This is the arm that attributes the opening to the PUSHES.** If M2 already has a path, the pushes are not what opens the room and the "3 pushes minimum" result is wrong. |
| **Q5** | Three `strength_push` calls succeed; boulder `local_id=4` reads `(4,4)`, then `(4,3)`, then `(4,2)`, verified by identity. | `strength_push` is proven (`#24-strength`) and pins the boulder by `local_id`. | A silent no-move means the destination was blocked — i.e. the tile data is wrong, or an earlier accidental step already moved it. |
| **Q6** | `M3` — from `(4,3)`, `calculate_path(→ (6,2))` returns OK. | Reach jumps to 31 tiles via `(4,3)→(5,3)→(6,3)→(6,2)`. | The planner cannot see a vacated boulder tile — which would be **KI-77 firing in Room 2**, not a route problem. |
| **Q7** | `LEG3` lands in `SEAFLOOR_CAVERN_ROOM6` at `(11,21)`. | `(6,1)` is a `Non-Animated Door`; our reader resolves the warp to `ROOM6 (11,21)`. | The warp table lies again — it already lied at both ends of the dive. |
| **Q8** | ‼ `calculate_path(ROOM6 (11,21) → (4,1))` returns a path, **measured from inside the room**. | `probe_ch20_currents.py` predicted this from OUTSIDE the cavern (its P1), and Rooms 6/7 have **zero objects**, so the `active_objects` artifact that invalidated the boulder rooms cannot apply. This converts that planner-level prediction into an in-room measurement. | The outside-the-cavern current predictions do not survive contact with the live room, and Rooms 6/7 need a solver after all. |
| **Q9** | *(reported, NOT graded)* The adjacent-step check in Room 6 does something **unpredictable** — a current may slide the avatar several tiles. | Stepping onto a current tile is a forced move. This is why the can-continue GATE is Q8's path, not this step. | Nothing — it is a measurement, deliberately outside the verdict. Its value is the endpoint it prints. |
| **Q10** | ≥0 wild encounters; if any fire the run survives them. | `gSeafloorCavern_Room2` land mons (Zubat L30+) are live on every route tile except the two warps, and a battle can fire **between two pushes**. | A stall here is a driver defect: every push must be idempotent and re-navigate rather than assume the avatar stayed put. |

---

# ✅ RESULT — `ACCEPTANCE: PASS` ON THE FIRST DRIVE (2026-08-13). **10 of 10 predictions held.**

```
[ch20room2] ROOM1 re-solved ok=True   (Room 1 is now n=3)
[ch20room2] STRENGTH-FLAG after the ROOM1->ROOM2 warp: False      <-- ‼ Q2
[ch20room2] M1 path_exists=False      (10,7) -> (6,2)
[ch20room2] SMASH ok=True  rock local_id=6 present=False
[ch20room2] M2 path_exists=False      <-- ‼ the smash ALONE does not open it
[ch20room2] PUSH1 ok boulder local_id=4 at=(4, 4)
[ch20room2] PUSH2 ok boulder local_id=4 at=(4, 3)
[ch20room2] PUSH3 ok boulder local_id=4 at=(4, 2)
[ch20room2] PUSHES 3/3
[ch20room2] STRENGTH-FLAG after the Room 2 pushes: True
[ch20room2] M3 path_exists=True
[ch20room2] LEG3 at=('SEAFLOOR_CAVERN_ROOM6', (11, 21)) in_room6=True
[ch20room2] ROOM6 arrival=(11, 21) tile_type='South Arrow Warp'
[ch20room2] CAN-CONTINUE (11, 21) -> (4, 1): OK len=13
[ch20room2] CAN-CONTINUE (ungraded) adjacent-step moved=True now at=(11, 20) tile_type='Cave'
[ch20room2] RESULT room1_ok=True m1=False m2=False m3=True pushes=3/3 in_room6=True
            can_continue=True
[ch20room2] ACCEPTANCE: PASS
```

## ‼ Q2 IS THE RESULT OF THE RUN: **OUR OWN PRODUCTION COMMENT WAS WRONG**

`FLAG_SYS_USE_STRENGTH` read **False** immediately after warping `ROOM1 → ROOM2`, with Strength
having just been activated in Room 1. ⇒ **the flag is cleared on every warp**, exactly as
`ClearTempFieldEventData()` (`src/event_data.c:39-48`) → `LoadMapFromWarp` (`src/overworld.c:848`)
says, and **not** "never cleared / once per SAVE" as `modules/story/early_game.py` claimed in two
places. Both comments are corrected in place.

**Why the wrong claim survived so long, and the rule that follows:** it rested on *"a decomp-wide
search for `clearflag`"* — the **script macro**. The clear is the **C function `FlagClear`**, so a
macro-only search could never have found it. ⇒ *A search proves absence only within the vocabulary
it searched.*

✅ **The code was always safe** — `strength_push` re-checks `_strength_active()` on every call and
re-activates — which is precisely why nothing caught it: **the bug was load-bearing documentation
sitting on top of correct code.** The danger was always the future author who reads "once per SAVE"
and removes the re-check as redundant; every room after the first would then walk into its boulder,
take a plain wall collision, and retry with no message and no error.

## THE THREE-POINT A/B DID ITS JOB

`M1 False → M2 False → M3 True` attributes the opening to the **pushes specifically**. A two-point
A/B would have been satisfied by "the rock was the only obstacle", which is false: the smash grows
the reachable set 9 → 21 tiles and `(6,2)` is in neither.

## Q8 — the current maze, now measured from INSIDE

`calculate_path(ROOM6 (11,21) → (4,1))` returned **`OK len=13`** — the same 13 waypoints
`probe_ch20_currents.py` predicted from *outside* the cavern for a 27-tile Manhattan trip (a count
only reachable via multi-tile slides). The outside-the-cavern current model therefore survives
contact with the live room. ⚠ **It is still a PLAN, not a walk** — crossing a current has never been
executed (KI-76), and the adjacent step that did run went to `(11,20)`, an ordinary `'Cave'` tile,
not onto a current.

## OTHER MEASURED FACTS WORTH KEEPING
* Room 6's arrival tile `(11,21)` is itself a **`South Arrow Warp`** (back to Room 2). Arrow warps
  need stand-and-**hold**, so a step will not bounce the bot out — but nothing may *hold* Down there.
* **Room 1 is now n=3** (`ch20room1` ×2, `ch20room2` ×1), each time re-solved from scratch.
* No wild encounter fired in Room 2 on this run (Q10 held vacuously — the encounter rate is 4, low).

## WHAT THIS RUN DOES NOT CLAIM
* **It does not prove the EXECUTOR can cross a current.** Q8 is a PLAN. Walking a current has never
  been executed in this project (KI-76), and a plan is not a walk.
* **It is not §Ch20.** No chapter module, nothing wired into `story_mode.py`, Dive still injected.
* **It does not test the retreat.** Every `FLAG_TEMP_*` object in both rooms respawns on map re-entry.
