# PRE-REGISTERED PREDICTIONS — the first driven DIVE, Mossdeep → SEAFLOOR_CAVERN_ENTRANCE (2026-08-13)

> Written **BEFORE** the run. Last time this project pre-registered predictions (the roster drive,
> earlier today) **0 of 6 fired and the real defect was one nobody predicted** — so the value here
> is not the hit rate, it is that a miss is visible instead of re-narrated afterwards.

## THE ROUTE, AS MEASURED (not recalled) — `probe_ch21_topology.py`

```
ROUTE128 (38,27) Deep Water
  -> dive()                 -> UNDERWATER_ROUTE128 (38,27)   [same x,y — decomp-confirmed]
  -> navigate 1 waypoint    -> UNDERWATER_ROUTE128 (38,26)   'Water Door'
  -> warp                   -> UNDERWATER_SEAFLOOR_CAVERN (6,7)
  -> swim into the pool     -> one of 18 open Deep Water tiles (4-9,5) (3-9,6) (4-9,7)
  -> surface_from_dive()    -> SEAFLOOR_CAVERN_ENTRANCE (10,17)
  -> navigate               -> (10,1) 'Non-Animated Door' -> SEAFLOOR_CAVERN_ROOM1 (5,18)
```
491 of 4800 ROUTE128 tiles are dive-capable; **(38,27) is one tile south of the cavern door.**
419 of 491 landing tiles route to (38,26); the 72 failures are two walled-off basins.

## ‼ THE FINDING THAT CHANGES THE DESIGN — the last leg is not in the map data

`UNDERWATER_SEAFLOOR_CAVERN` has **no connection and no warp** into `SEAFLOOR_CAVERN_ENTRANCE`.
The edge is created at RUNTIME:
`data/maps/Underwater_SeafloorCavern/scripts.inc` → `Underwater_SeafloorCavern_OnResume:
setdivewarp MAP_SEAFLOOR_CAVERN_ENTRANCE, 10, 17`, consumed by `overworld.c` `SetDiveWarp()`'s
`RunOnDiveWarpMapScript()` fallback when there is no EMERGE connection.

⇒ **No warp-graph or path scan will ever see this edge.** The chapter must EMERGE inside the pool.
This is why KI-68's "the planner cannot route a dive" is only half the story: even the *destination*
of the surface is invisible to static analysis.

## Ranked predictions

| # | Prediction | Why | What I expect to SEE |
|---|---|---|---|
| **P1** | The **Mossdeep → Route 128 sea journey** is the riskiest leg, not the dive | KI-48 measured that direct navigation cannot make trips story mode makes; this is ~2 maps of open ocean | `_navigate_riding_out` burns its 10 tries, or a whiteout. **Most likely single point of failure.** |
| **P2** | `dive()` SUCCEEDS at (38,27) | its precondition is exactly `tile_type in (Deep Water, …)` and we measured (38,27) as Deep Water | `AvatarFlags.Underwater` set, map `UNDERWATER_ROUTE128`, coords unchanged at (38,27) |
| **P3** | `navigate_to((38,26))` **follows the warp automatically** | `calculate_path`'s docstring: a warp tile as destination leads to the map it connects to | we end on `UNDERWATER_SEAFLOOR_CAVERN (6,7)` without an explicit warp step |
| **P4** | ‼ **KI-72 is ARMED at the surfacing step** | `calculate_path` has never heard of `Underwater Blocked Above` / `Seaweed No Surfacing`, so it can route us to a tile we cannot surface from | if I let the planner pick, `BotModeError: This tile does not allow surfacing from a dive.` ⇒ **I pick the pool tile explicitly and assert its tile_type first.** |
| **P5** | The emerge lands at `SEAFLOOR_CAVERN_ENTRANCE (10,17)` — **but only if `OnResume` has run** | the divewarp is set by a map script, not by data | if the script has not run, surfacing goes somewhere unexpected or the last-set divewarp (a *different* map) fires. **This is the one I am least sure of.** |
| **P6** | Wild encounters underwater are unavoidable, only minimised | `avoid_encounters` adds +1000 cost but nearly every underwater tile has encounters | battles mid-leg; the party must be able to win them |
| **P7** | KI-59 does **not** bite this leg but arms one map later | measured: 0 `Impassable *` on UNDERWATER_ROUTE128, **27 `Impassable North`** in SEAFLOOR_CAVERN_ROOM1 | clean run to the entrance; trouble only if the probe continues into Room 1 |

## What makes this a PASS

Every leg lands on the measured map+tile, **and** the run is not stranded: a real `calculate_path`
off the end tile, an actual position change, **and** the exit proven — `SEAFLOOR_CAVERN_ENTRANCE`
`(10,18)` is Deep Water and warps back out to `UNDERWATER_ROUTE128 (38,26)`.
‼ §Ch15 ended four floors underground, §Ch18 on an eleven-tile island, §Ch19 in a living room.
**An underwater cavern is the best place yet to strand a run — so prove the way out, in the same run.**

---

# 🔻 OUTCOME — `ACCEPTANCE: PASS`, `legs=6/6`. THE FIRST DRIVEN DIVE IN THIS PROJECT.

```
[ch21dive] LEG1 at=('ROUTE128', (38, 27)) tile_type='Deep Water' arrived=True
[ch21dive] LEG2 at=('UNDERWATER_ROUTE128', (38, 27)) underwater=True ok=True
[ch21dive] LEG3 at=('UNDERWATER_SEAFLOOR_CAVERN', (6, 7)) in_cavern=True
[ch21dive] LEG4 at=('UNDERWATER_SEAFLOOR_CAVERN', (6, 6)) tile_type='Deep Water' surfaceable=True ok=True
[ch21dive] LEG5 at=('SEAFLOOR_CAVERN_ENTRANCE', (10, 17)) underwater=False at_entrance=True
[ch21dive] LEG6 on the exit water tile: ('SEAFLOOR_CAVERN_ENTRANCE', (10, 18)) tile_type='Deep Water'
[ch21dive] LEG6 dived back down to ('UNDERWATER_SEAFLOOR_CAVERN', (6, 5))
[ch21dive] LEG6 at=('UNDERWATER_ROUTE128', (38, 27)) got_out=True
[ch21dive] CAN-CONTINUE surfaced to ('ROUTE128', (38, 27)) ok=True
[ch21dive] CAN-CONTINUE surfaced=True moved=True (38, 27)->(37, 27) at=('ROUTE128', (37, 27))
[ch21dive] RESULT legs=6/6 at_entrance=True got_out=True can_continue=True
[ch21dive] ACCEPTANCE: PASS
```

## Adjudication

| # | Predicted | Fired? | Evidence |
|---|---|---|---|
| P1 | the ocean journey is the riskiest leg | **NO** | sailed Mossdeep → ROUTE128 (38,27) cleanly, first attempt, every run |
| P2 | `dive()` succeeds at (38,27) | ✅ **CONFIRMED** | underwater, same (x,y) — the decomp behaviour reproduced live |
| P3 | `navigate_to` follows the warp automatically | ✅ **CONFIRMED** | landed `UNDERWATER_SEAFLOOR_CAVERN (6,7)` with no explicit warp step |
| P4 | KI-72 armed at the surfacing step | **NO** — but the guard cost nothing | the chosen pool tile (6,6) is `Deep Water`; **the hazard is still real** — the planner was simply never given the chance to pick |
| P5 | emerge lands at (10,17) via the RUNTIME `setdivewarp` — *"the one I am least sure of"* | ✅ **CONFIRMED EXACTLY** | `SEAFLOOR_CAVERN_ENTRANCE (10, 17)`, on the nose, from a prediction made off a map script no static scan can see |
| P6 | wild encounters underwater are unavoidable | ✅ **FIRED, and was survivable** | battles occurred (`SCEPTILE gained 135 EXP`); the healed party won them |
| P7 | KI-59 does not bite this leg | ✅ **CONFIRMED** | clean throughout; it arms one map later in `SEAFLOOR_CAVERN_ROOM1` |

## ‼ THE WAY OUT IS THREE HOPS, AND THE STATIC TABLE IS MISLEADING ABOUT IT

The warp table says `SEAFLOOR_CAVERN_ENTRANCE (10,18) -> UNDERWATER_ROUTE128 (38,26)`.
**Live, it does not.** Diving at (10,18) drops you into `UNDERWATER_SEAFLOOR_CAVERN (6,5)` — the
pool — because the live dive warp is the runtime one again. The real exit is:

```
(10,18) dive -> UNDERWATER_SEAFLOOR_CAVERN (6,5)
             -> navigate (6,7) 'Water South Arrow Warp'
             -> UNDERWATER_ROUTE128 (38,27)   [not (38,26)]
             -> surface_from_dive()           -> ROUTE128 (38,27), open ocean
```

⇒ **A second instance of the same lesson**: around the Seafloor Cavern, the static warp data does
not describe what actually happens. Both the way in *and* the way out are runtime dive warps.
**Drive it; do not read it.**

## ‼ ALL THREE FAILURES ACROSS THE THREE RUNS WERE IN MY CHECK, NOT THE ROUTE

The route was correct from run 1. Runs 1 and 2 reported `FAIL` because the CAN-CONTINUE check was
wrong — first a hardcoded off-map coordinate (`IndexError` on a 14×9 map), then a target identical
to the tile it was standing on. Written up in `08-MISTAKES.md`, including the uncomfortable part:
the prevention rule against exactly this was written **the same day, into the same file**, and did
not fire because it had been filed as a story about the roster driver rather than as a property
every liveness check must have.

## What I will NOT claim

This probe injects Dive with a debug write. It measures **the ROUTE**, not the acquisition of a
Dive learner. "The dive leg works" must not be written up as "§Ch21 is unblocked".
