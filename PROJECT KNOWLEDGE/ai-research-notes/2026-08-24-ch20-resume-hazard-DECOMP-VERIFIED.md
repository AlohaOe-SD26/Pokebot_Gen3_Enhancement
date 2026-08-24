# §Ch20 RESUME HAZARD — VERIFIED AGAINST THE pret DECOMP (2026-08-24)

⛔ **THIS IS NOT A GEMINI NOTE.** Every claim below was read out of `pret/pokeemerald` via `gh api`
by a Claude subagent with real tool access, and the load-bearing ones are quoted verbatim. The
project rule that a research note is a NOTE still applies to the *interpretation*; the **quoted
script lines are primary source**.

## THE QUESTION
The §Ch20 build needs a crash-recovery branch. If the bot beats Archie but dies before
`ROUTE128_STATE` reaches 2, is the run PERMANENTLY unable to finish?

## THE ANSWER: RECOVERABLE. There is no soft-lock.

### 1. The Room 9 trigger IS permanently disarmed
`SeafloorCavern_Room9/map.json` — the coord event at `(17,42)` is gated `VAR_SEAFLOOR_CAVERN_STATE == 0`
(**and elevation 3** — a detail our code did not record). `scripts.inc:131` sets it to 1, and a
repo-wide search finds only **3** references to that var in the entire decomp (`vars.h`, this
`scripts.inc`, this `map.json`). **Nothing ever resets it.** Room 9 also has NO map scripts
(`SeafloorCavern_Room9_MapScripts:: .byte 0`), so there is no alternate re-entry.
⇒ Re-diving the cavern can NEVER re-fire the scene. Do not build a recovery that tries.

### 2. Route 128 RE-FIRES the scene, every time, on the next frame of field control
`data/maps/Route128/scripts.inc`:
    Route128_OnFrame:
        map_script_2 VAR_ROUTE128_STATE, 1, Route128_EventScript_KyogreAwakenedScene
`ON_FRAME_TABLE` semantics, from `include/constants/map_scripts.h`: *"Run every frame after the map
has faded in, before player input is processed."* The scene ends:
    clearflag FLAG_HIDE_MAP_NAME_POPUP
    setvar VAR_ROUTE128_STATE, 2
    releaseall
⇒ **RECOVERY = get back to Route 128.** Surf in from Route 127/129/Ever Grande or the underwater
dive; Route 128 has no warps and no coord events, so those are the only ways in and all need Surf.

### 3. ⛔⛔ THE SPEC'S PROPOSED BRANCH WAS DEAD CODE — CORRECTED HERE
The build spec proposed: *"if `KYOGRE_ESCAPED_SEAFLOOR_CAVERN` is set but `ROUTE128_STATE < 2`, do
not re-dive."* **That test cannot discriminate.** In `Room9/scripts.inc`:
    :115  setvar VAR_ROUTE128_STATE, 1      <- THIRTEEN LINES EARLIER
    :128  setflag FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN
⇒ **There is no reachable state with the flag set and the var at 0.** The flag half is redundant.
✅ **THE CORRECT CONDITION IS SIMPLY `ROUTE128_STATE == 1`** — meaning "the cavern scene ran; only
the Route 128 scene is outstanding".

### 4. A degenerate re-fire still COMPLETES — checked, not assumed
If the interruption landed after the scene's `removeobject` of Archie/Maxie, those hide flags are
persistent (`RemoveObjectEventByLocalIdAndMap` → `FlagSet`). The re-fired scene then runs with them
absent — and `ScriptMovement_StartObjectMovementScript` / `..._IsObjectMovementFinished` both RETURN
EARLY on a missing local id, so `applymovement`/`waitmovement` are no-ops rather than hangs. Steven
is re-added unconditionally (`addobject`), and the script reaches `setvar ..., 2`.
⇒ **No hang path exists in that script.** ⚠ Not observed live; the no-hang argument is from source.

### 5. A BACKSTOP nobody had noticed
`VAR_ROUTE128_STATE` has only **3** references repo-wide — **nothing else in the game gates on it.**
The next chapter is driven by `VAR_SOOTOPOLIS_CITY_STATE == 1` (SootopolisCity's own ON_FRAME), and
that var is set in the SAME Room 9 block (`:116`). ⇒ even a bot that never returns to Route 128 can
still enter the Rayquaza/Sootopolis chapter. The recovery is about not being ambushed later, not
about unblocking the game.
‼ **AND THAT AMBUSH IS REAL:** Route 128 is on the surf route to Ever Grande. A stale
`ROUTE128_STATE == 1` means the FIRST frame of field control there — possibly during the Elite Four
run — is seized by a ~1-minute cutscene. **Clear it deliberately.**

## 6. ⚠ A CORRECTION TO OUR OWN DOCS: THE LAGOON IS OFF BY ONE
Decoded from `Route128/map.bin` + the tileset attribute binaries:
| tile | behavior | note |
|---|---|---|
| `(38,22)` landing | `MB_SHALLOW_WATER` | walkable wading, **not surfable** |
| `(38,21)` north | `MB_SHALLOW_WATER` | **still sandbar** — Maxie's spawn tile |
| `(38,20)` two north | `MB_DEEP_WATER` | **the lagoon starts HERE** |
| `(38,23)` south | `MB_SHALLOW_WATER` | walkable |
| `(38,24)` two south | `MB_OCEAN_WATER` | the open ocean |
Our docs say *"north is a 41-tile closed lagoon"*. North is **sandbar**; the lagoon is two tiles
north. ✅ The operational rule is UNCHANGED and still correct: **step SOUTH to `(38,23)`, then Surf
onto `(38,24)`** — and "`(38,22)` has zero surfable neighbours" is also still true, because shallow
water is not surfable.
‼ Flood-fill measured: lagoon **41** tiles, ocean **1,766**, disjoint. Of the sandbar ring's surf
entry points, **28 lead INTO the lagoon and 46 into open ocean** — which is exactly why KI-72's rule
(hand-pick the tile, never let the planner choose) applies to the launch as well as the surfacing.
