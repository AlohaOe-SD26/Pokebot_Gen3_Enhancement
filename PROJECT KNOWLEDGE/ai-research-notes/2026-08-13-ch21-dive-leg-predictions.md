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

## What I will NOT claim

This probe injects Dive with a debug write. It measures **the ROUTE**, not the acquisition of a
Dive learner. "The dive leg works" must not be written up as "§Ch21 is unblocked".
