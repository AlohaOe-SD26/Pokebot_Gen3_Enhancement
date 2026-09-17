# `--driver e4exit` — PREDICTIONS, FILED BEFORE THE RUN (2026-09-16)

> ⛔ Written and committed **before** the driver was executed (`story-drive` §1). Anything the run
> contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Can the bot actually WALK out of Sidney's room after the victory — dismiss the msgbox, cross the
room, and warp into Hall 1?**

This is the last unknown standing in front of §Ch24 leg 1. Two things are already measured and are
NOT what this asks:
* `B` clears the post-victory msgbox and control returns in 297 frames, with a no-press CONTROL
  proving the box does not self-clear (`2026-09-16-e4dismiss-PREDICTIONS.md`).
* `calculate_path` returns a 6-waypoint route to `(6,2)` that goes around the standing trainer and
  lands on `HALL1 (5,12)`, with a positive control, a negative control and a discriminator.

⛔ **NEITHER IS PROOF THE BOT CAN WALK IT.** That is `KI-48`, a standing rule in this project: *a
`calculate_path` OK is not proof the driven navigator can execute it.* This drive is the arm that
tests the navigator, not the planner.

## FIXTURE AND METHOD

`saves/post_sidney_door_open.ss1`, md5 **`6231369647f8`** (PINNED; `verify_fixtures --assert` passes).
The driver reuses shipped helpers rather than writing new machinery — the whole point of the recon:
* dismiss: press `B` on the `script_running or printer-parked` gate (the same gate
  `_wait_until_cutscene_over` uses);
* exit: **`early_game._pass_through_door((6,2), from_map)`** — *"Robustly warp through a door/warp
  tile by making it a NAVIGATION target. A warp fires on a genuine step onto the tile."*
  ⛔ Not a hand-rolled press loop: this project measured that stopping short of a door and
  hand-stepping onto it is flaky (the Petalburg-Woods stall, ML-9).

## THE TWO ARMS

| arm | env | what it does |
|---|---|---|
| **TREATMENT** | *(none)* | dismiss, then walk out through `(6,2)` |
| **CONTROL** | `POKEBOT_E4EXIT_FAULT_NOWALK=1` | dismiss, then **skip the walk** |

The control exists so "we ended in Hall 1" cannot be satisfied by anything other than the walk —
e.g. by a script warping us out on its own.

## PREDICTIONS

| # | reading | TREATMENT | CONTROL | why |
|---|---|---|---|---|
| P1 | `start_map` / `start_tile` | `SIDNEYS_ROOM` `(6,6)` | same | the fixture |
| P2 | `controllable_after_dismiss` | `True` | `True` | already measured: 297 frames |
| P3 | **`end_map`** | **`EVER_GRANDE_CITY_HALL1`** | **`SIDNEYS_ROOM`** | the experiment |
| P4 | `end_tile` | `(5,12)` | `(6,6)` | the warp backbone's predicted landing tile |
| P5 | `walk_frames` | < 3000 | n/a | 6 waypoints across a 13×14 room |
| P6 | `battles` | 0 | 0 | the room has one trainer and he is beaten |
| P7 | `can_continue` | a real `calculate_path` from the Hall1 landing to the hall's north door `(5,2)` returns OK | n/a | ⛔ "arrived" is not "can continue" |

## FALSIFIERS

* **F1 — TREATMENT does not reach Hall 1.** Then `KI-48` bites at this door: the planner's route is
  not executable. Diagnose from the harness's no-progress dump (it names the generator, tile and
  script stack) — ⛔ do NOT respond by hand-rolling a press loop onto the door tile; that is the
  flaky pattern `_pass_through_door` exists to replace.
* **F2 — CONTROL also reaches Hall 1.** Then something other than our walk moves the bot, and the
  TREATMENT result attributes to the navigator something it did not do.
* **F3 — the bot arrives but `can_continue` REFUSES.** Then leg 1 lands somewhere it cannot leave —
  the §Ch15/§Ch18/§Ch19 "passed while stranded" shape this project has hit three times.
* **F4 — `battles > 0`.** Something re-triggered the defeated trainer. The dismiss would then be
  re-opening his script, i.e. pressing the wrong button or pressing it in the wrong state.

## WHAT THIS STILL DOES NOT ANSWER

1. Phoebe / Glacia / Drake. Their ROM layouts are byte-identical and the victory script is shared,
   but that is an INFERENCE. Glacia is additionally the first room whose in-battle lose-text carries
   `\p`, so it is the first that exercises our KI-93 in-battle dismiss at all.
2. The Champion's room, which has **no pre-battle window** and ends in a scripted warp, not a tile.
3. Whether the whole gauntlet is survivable — that is healing and party strength, not routing.

---

# RESULTS — GRADED AFTER THE RUN (2026-09-16)

**VERDICT: THE BOT WALKS OUT. `KI-48` DOES NOT BITE AT THIS DOOR.** Every prediction held; no
falsifier fired. Both arms `ACCEPTANCE: PASS`, graded by opposite expectations on `end_map`.

| reading | TREATMENT | CONTROL (`FAULT_NOWALK=1`) | predicted? |
|---|---|---|---|
| `start_map` / `start_tile` | `(16,0)` `(6,6)` | same | ✅ P1 |
| `controllable_after_dismiss` | `True` (297 frames) | `True` (297) | ✅ P2 |
| **`end_map`** | **`(16,5)` = `EVER_GRANDE_CITY_HALL1`** | **`(16,0)` = `SIDNEYS_ROOM`** | ✅ **P3** |
| **`end_tile`** | **`(5,12)`** | `(6,6)` | ✅ **P4** |
| `walk_frames` | **164** | 0 | ✅ P5 (< 3000) |
| `battles` | 0 | 0 | ✅ P6 |
| `can_continue_to_hall_door_5_2` | **OK 10 waypoint(s)** | REFUSED | ✅ P7 |
| `NEGCONTROL_path_to_0_0` | REFUSED | REFUSED | — (fires on both maps) |

⭐⭐ **`end_tile = (5,12)` IS THE TILE THE WARP BACKBONE PREDICTED**, independently derived from
`map.json` by the routing recon before any of this was run. Two different methods, same tile.

⭐ **THE DISMISS REPRODUCED FROM A SEPARATE DRIVER:** `dismiss_frames = 297`, identical to
`e4dismiss`'s `frames_to_control = 297`. ⚠ Same fixture and a deterministic emulator, so this is a
consistency check across two independent implementations of the same press loop — **not** an
independent replication of the phenomenon (rule 8).

⭐ **AND THE CONTINUATION CHECK EARNED ITS KEEP.** `can_continue` REFUSES in the CONTROL arm — i.e.
it is not a formality that passes wherever you stand. That is the §Ch15/§Ch18/§Ch19 "passed while
stranded" shape being actively excluded rather than assumed away.

## WHAT IS NOW ESTABLISHED FOR LEG 1 — AND WITH NO NEW MACHINERY

1. `B` clears the post-victory msgbox; control returns in 297 frames. (A/B'd: the box does not
   self-clear.)
2. `calculate_path` routes to the runtime-opened door, around the standing trainer, and follows the
   warp. (Positive control, negative control, and a `warps_to` discriminator.)
3. **The driven navigator executes that route** via the shipped `_pass_through_door()`, arriving at
   `HALL1 (5,12)` in 164 frames. (A/B'd against a no-walk arm.)
4. From there the bot can path to the hall's north door — the entrance to Phoebe's room.

⇒ **Leg 1 is a composition of helpers that already ship.** The BFS §G' specs should not be built.

## STILL NOT ESTABLISHED (unchanged by this run)

1. Phoebe / Glacia / Drake — byte-identical ROM layouts and a shared victory script make it very
   likely, but that is an INFERENCE. Glacia is also the first room whose in-battle lose-text carries
   `\p`, i.e. the first to exercise our KI-93 in-battle dismiss at all.
2. The Champion's room: **no pre-battle window**, and it ends in a scripted warp, not a tile.
3. Whether the gauntlet is SURVIVABLE. That is healing and party strength, not routing — and the
   bag is the only healing, because the gauntlet is one-way.
