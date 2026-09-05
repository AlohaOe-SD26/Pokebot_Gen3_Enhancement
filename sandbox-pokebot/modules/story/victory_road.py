"""§Ch23 — VICTORY ROAD. **LEGS 2 AND 3 ONLY: prepare to depart Sootopolis, and leave the crater.**

⛔⛔ THIS CHAPTER IS INCOMPLETE AND MUST NOT BE WIRED INTO `_play()` YET. Legs 4-8 (the ocean route,
Ever Grande, the waterfall, Victory Road itself) do not exist. `story_mode.py`'s END-OF-BUILT-CONTENT
banner is retargeted by leg 8, not by this file.

The full contract this module is built against — including the four BLOCKERS an adversarial review
found in the design *before any code existed* — is
`PROJECT KNOWLEDGE/ai-research-notes/2026-09-03-ch23-CHAPTER-BUILD-SPEC.md` §4b.

⛔⛔ THE FIVE TRAPS. Each was measured, and each one has already cost someone something.

1. **NO NAVIGATION PRIMITIVE IN THIS TREE CAN DIVE OR EMERGE.** `WaypointAction.Dive` / `.Emerge`
   are DECLARED at `map_path.py:692-693` and **assigned nowhere**; `follow_waypoints` handles only
   `Surf` and `Waterfall`. Corroborated structurally: the warp graph gives `SOOTOPOLIS_CITY` 13 warp
   edges and **ZERO** connections to `UNDERWATER_SOOTOPOLIS_CITY` — the scripted `setdivewarp` is in
   neither structure. ⇒ **leg 3's hand-sequencing is FORCED, not stylistic**, and
   `navigate_to_anywhere(ROUTE126, ...)` from inside the crater is structurally impossible.

2. **THE (9,8) WARP IS TAKEN BY `navigate_to` ITSELF — never hand-walk onto it.** The plan's last
   waypoint is already `UNDERWATER_ROUTE126 (45,65)` with `is_warp=True`, and `navigate_to`
   overrides its own destination when the last waypoint is a warp. Measured across three passing
   §Ch21 drives. ⛔ And never target `(10,8)`: it is plain Deep Water whose header warp cannot fire.

3. **THE WARP RESTS ON (45,66), NOT ON ITS TARGET (45,65) — READ, NEVER BLIND-STEP.**
   `sootopolis.py:729` records this MEASURED-LIVE. ‼ A literal reading of the older build-spec
   sentence *"step south to (45,66)"* lands you on **(45,67)**.

4. **STEPPING NORTH ONTO (45,65) UNDOES THE LEG.** It is a walk-on warp back into the crater, and
   §Ch21 leg 1 uses exactly that edge. The hazard here is not "emerging from a water door" — it is
   **a retry loop that walks the leg backwards and re-runs it forever.** ⇒ (45,65) is never a
   navigation target, and every step on `UW126` is a `_bounded_step` expecting a SOUTHWARD result.

5. **`dive()`, `surface_from_dive()` AND `heal_in_pokemon_center()` ALL END IN UNBOUNDED,
   ABORT-BLIND LOOPS** — `tasks_scripts.py` is 8 such loops with ZERO frame caps and ZERO
   `_check_abort()` (**KI-83**). It is byte-identical to the pristine upstream mirror, so it is NOT
   patched; every call from here goes through `_budgeted(...)`, which bounds it and closes the
   generator in a `finally`. ‼ A never-hang audit must enumerate the loops a call **reaches**, not
   the loops near it: the design's own audit cleared the heal by checking its *exit* loops while the
   nurse interaction three lines earlier was unbounded.
"""

from typing import Generator

from modules.context import context
from modules.map_data import MapRSE, PokemonCenter
from modules.modes import BotModeError
from modules.modes.util.higher_level_actions import (
    dive,
    heal_in_pokemon_center,
    surface_from_dive,
)
from modules.modes.util.walking import navigate_to
from modules.player import get_player_avatar
from modules.pokemon_party import get_party

# ‼ IMPORTED, NOT RE-IMPLEMENTED — this package's transcription rule: the same fact in two files is
# the P5 doc shape in code form, and it drifts.
from modules.story.seafloor_cavern import _at, _flag, _on_map, _var, _where
from modules.story.early_game import (
    StoryAbort,
    _check_abort,
    _navigate_riding_out,
    _walk_through_warp,
    reraise_if_aborting,
    wait_until_truly_controllable,
)

# ‼ IMPORTED, NOT RE-TYPED — §Ch21 leg 3 DROVE these three tiles. Re-typing them here would create a
# second copy of a fact that has already been corrected once.
from modules.story.sootopolis import (
    DIVE_OUT_TILE,
    R126_SURFACE_TILE,
    UW_EXIT_WARP,
    _bounded_step,
    _here_tile,
    _pin_planner_to_live_layout,
    _take,
)

CITY = MapRSE.SOOTOPOLIS_CITY
UWS = MapRSE.UNDERWATER_SOOTOPOLIS_CITY
UW126 = MapRSE.UNDERWATER_ROUTE126
R126 = MapRSE.ROUTE126
PC_1F = MapRSE.SOOTOPOLIS_CITY_POKEMON_CENTER_1F
PC_2F = MapRSE.SOOTOPOLIS_CITY_POKEMON_CENTER_2F

#: ⛔ THE DOOR AND THE APRON ARE DIFFERENT TILES AND CONFLATING THEM IS A REAL BUG.
#: (43,31) is the DOOR WARP; (43,32) is the APRON in front of it **and the whiteout respawn tile**.
PC_DOOR = PokemonCenter.SootopolisCity.value[1]
PC_APRON = (PC_DOOR[0], PC_DOOR[1] + 1)

#: ⛔ A resume can land the bot INSIDE the building — `heal_in_pokemon_center` was itself forked to
#: use `navigate_to_anywhere` because "a post-derail resume can call this from INSIDE a building".
#: A leg-2 gate that only knows about `CITY` strands the run two tiles from the exit.
_ISLAND_SIDE_MAPS = (CITY, PC_1F, PC_2F)

#: ⛔ EVERY MAP THIS CHAPTER CAN LEGITIMATELY BE ON WHEN IT STARTS OR RESUMES. The preflight gate
#: uses THIS, never `_ISLAND_SIDE_MAPS` — those two sets answer different questions, and conflating
#: them made a mid-leg-3 resume raise before the phase selector built to handle it ever ran.
_RESUMABLE_MAPS = (CITY, PC_1F, PC_2F, UWS, UW126, R126)

UW126_ARRIVAL_PREDICTION = (45, 65)  # the warp TARGET — REPORTED, never asserted (trap 3)
EMERGE_TILE = R126_SURFACE_TILE      # (45,66) — the MEASURED-LIVE resting tile

#: ⭐ MEASURED-PROD: `ch23route` R9f = 55 wp from (45,66), and leg 3's first drive reproduced 55.
#: The ROUTE126 east-edge seam toward ROUTE127 — i.e. the tile leg 4 departs through.
R126_EAST_PROBE = (79, 45)

# ============================== LEG 4 — THE OCEAN CROSSING ====================================
R127 = MapRSE.ROUTE127
R128 = MapRSE.ROUTE128
EG = MapRSE.EVER_GRANDE_CITY

#: ⭐ MEASURED-PROD 2026-09-04 (`ch23route` R10/R11): the planner crosses these CONNECTED maps and
#: plans ROUTE126 (45,66) -> EVER_GRANDE (18,68) in **273 waypoints**.
#: ‼ The rule is "the planner crosses CONNECTIONS, never WARPS" — the crater refuses only because
#: Sootopolis has ZERO connections. Do not carry leg 3's "hand-sequencing is forced" here.
WATERFALL_BASE = (18, 68)   # stand here SURFING, face NORTH, press A
WATERFALL_TOP = (18, 59)    # where the climb ends — same x, still surfing
EG_LANDING = (18, 55)       # the only surf->land exits are (18..22,56) stepping NORTH

#: ⛔⛔ (18,41) IS THE VICTORY ROAD DOOR **WARP**, AND AIMING AT IT ENDS LEG 4 INSIDE THE CAVE.
#: MEASURED (`ch23route` R11b): `calculate_path(EG (18,55) -> EG (18,41))` returns 16 wp whose LAST
#: waypoint is **`map=VICTORY_ROAD_1F coords=(15,40) is_warp=True`** — because `navigate_to`
#: overrides its own destination when the final waypoint is a warp. Leg 4 would then silently do
#: leg 5's job, and an honest `_at(EG, (18,41))` grade would FAIL a perfect run.
#: ✅ R11c: aiming at the APRON (18,42) returns 15 wp, LAST `map=EVER_GRANDE (18,42) is_warp=False`.
VR_DOOR = (18, 41)
VR_APRON = (18, 42)

#: ⛔ STAGE THE CROSSING HERE, and ⛔ NEVER at (101,29)/(101,22) — those are Carlee's and Harrison's
#: own tiles, and the planner REFUSES a path to an occupied tile (measured: both refuse, while
#: (101,26) and (100,29) beside them return 32 and 34 wp). A refusal to an occupied tile means
#: "something is standing there", not "you cannot get there".
CHANNEL_STAGE = (101, 26)

EG_PC_DOOR = PokemonCenter.EvergrandeCity.value[1]     # (27,48)
EG_PC_APRON = (EG_PC_DOOR[0], EG_PC_DOOR[1] + 1)

CROSSING_BUDGET = 400_000   # the crossing is ~273 wp of surfing plus two forced trainer battles
CLIMB_BUDGET = 3_000

LEG4_READINGS = ("R4-LEAD", "R4-STAGE", "R4-BASE", "R4-CLIMB", "R4-LAND", "R4-HEAL4", "R4-ARM4",
                 "R4-APRON", "R4-CONTINUE4")

# ============================== LEG 5 — VICTORY ROAD 1F =======================================
VR1F = MapRSE.VICTORY_ROAD_1F

#: Where the Ever Grande door warp lands, and the two tiles leg 5 turns on.
VR_ENTRANCE = (15, 40)

#: ⛔ WALLY'S TRIGGER IS *MANDATORY*, AND THE PLANNER ACTIVELY DISLIKES IT.
#: `map_path.py:1034-1037` adds **+10000** to any tile with an armed `on_enter_event_triggers`, and
#: (2,23)/(3,23) are exactly that — so the planner routes AROUND this battle wherever it can.
#: ✅ It cannot here: blocking both triggers makes the B1F ladder UNREACHABLE (477 → 429 tiles), and
#: MEASURED (`ch23route` R12) the entrance→ladder plan is **44 wp = 29 (to the trigger) + 15 (from
#: it)** — i.e. the only path runs straight through it. ⇒ the penalty costs nothing and the battle
#: that sets this chapter's GRADING FLAG cannot be skipped.
WALLY_TRIGGER = (3, 23)

#: ⭐ The OTHER armed trigger, same elevation, one tile west. **LOAD-BEARING**: walking between
#: the two is what actually fires the battle — an A/B measured `battles=5` with that walk and
#: `battles=0` without it, at an identical step-count delta.
WALLY_TRIGGER_WEST = (2, 23)

#: ⛔⛔ (9,14) IS A LADDER **WARP** AND MUST NEVER BE A NAVIGATION TARGET.
#: MEASURED (`ch23route` R12a): `calculate_path(1F (15,40) -> 1F (9,14))` returns 44 wp whose LAST
#: waypoint is **`map=VICTORY_ROAD_B1F coords=(8,3) is_warp=True`** — because `navigate_to` overrides
#: its own destination when the final waypoint is a warp. Aiming leg 5 there would drop the bot into
#: B1F's **sealed 23-tile arrival chamber**, doing leg 6's job, and an honest
#: `_at(VICTORY_ROAD_1F, (9,14))` grade would FAIL a perfect run.
#: ✅ R12b: the APRON (9,15) returns 45 wp, LAST `map=VICTORY_ROAD_1F (9,15) is_warp=False`.
#: ‼ This is the THIRD warp-as-destination trap in this chapter (the Poké Center door, the Victory
#: Road door, now the ladder). ⇒ **ask the planner before aiming at any tile adjacent to a warp.**
B1F_LADDER = (9, 14)
B1F_LADDER_APRON = (9, 15)

LEG5_READINGS = ("R5-WARP", "R5-WALLY", "R5-FLAG", "R5-LADDER", "R5-CONTINUE5")

# ============================== LEG 6 — VICTORY ROAD B1F: THE BOULDER PUZZLE ====================
#: ⭐⭐ EVERY VALUE BELOW WAS DRIVEN LIVE ON 2026-09-04 (`--driver ch23push`, all three arms PASS),
#: not taken from a model. Three research agents solved this puzzle with their own reimplementations
#: of pokeemerald's collision rules; one of them found and corrected a bug in its OWN elevation model
#: mid-run. ⇒ the agents told us WHAT TO LOOK FOR; the harness told us what is TRUE.
#: Evidence: `tools/story-dev/evidence/2026-09-04-ch23-push-arms-AB.txt`.
B1F = MapRSE.VICTORY_ROAD_B1F

#: Where the 1F (9,14) ladder drops us. MEASURED: `arrived_on = ((24,44), (8,3))`.
B1F_ARRIVAL = (8, 3)

#: ⛔⛔ THE B2F LADDER IS A **WARP** AND MUST NEVER BE A NAVIGATION TARGET — this is the FOURTH
#: warp-as-destination trap in this chapter (the Poké Center door, the Victory Road door, the 1F
#: ladder, now this). `navigate_to` overrides its own destination when the final waypoint is a warp
#: (`walking.py:446-448`), so aiming here would silently do LEG 7's job and an honest end-position
#: grade would FAIL a perfect run. Aim at the APRON; step onto the ladder with `_walk_through_warp`.
B1F_B2F_LADDER = (30, 25)
#: ⛔ THERE IS DELIBERATELY NO HARDCODED APRON CONSTANT HERE. `b1f_ladder_apron()` MEASURES which
#: neighbour of the ladder our planner can actually reach, because "hardcode no coordinates — derive
#: the target from the state the run ACTUALLY reached" is this project's rule, and a guessed apron is
#: precisely the kind of value that looks right in review and strands a run in practice.

#: ⭐ THE THREE OBSTACLES, EACH KEYED BY ITS LIVE `local_id` — never by "is something on that tile".
#: `strength_push` and `_smash_rock` both track by `local_id`, and an NPC standing on a tile would
#: fool a positional check.
#: ‼ THE ORDER IS FORCED AND IT IS NOT OBVIOUS: (9,10) can only be pushed EAST, which requires
#: standing at (8,10) — and **(8,10) is unreachable until (4,7) moves**. MEASURED: before the first
#: push `calculate_path (8,3)->(8,10)` REFUSES; after it, 7 waypoints. ⇒ a "delete the boulder and
#: re-path" model finds only (9,10) and misses (4,7) entirely.
B1F_PUSH_WEST = {"local_id": 3, "tile": (4, 7), "approach": (5, 7), "face": "Left", "to": (3, 7)}
B1F_PUSH_EAST = {"local_id": 4, "tile": (9, 10), "approach": (8, 10), "face": "Right", "to": (10, 10)}
B1F_SMASH = {"local_id": 10, "tile": (18, 12), "approach": (17, 12), "face": "Right"}

#: ⛔⛔ PUSHING EITHER BOULDER **SOUTH** BRICKS THE ROUTE — and SOUTH is exactly what a greedy
#: "push toward the goal" router chooses. MEASURED 2026-09-04: pushing (4,7) south moves it to (4,8)
#: and leaves BOTH (8,10) and (30,25) sealed. ‼ Recovery is to leave B1F and re-enter (see
#: `B1F_PUZZLE_RESETS_ON_WARP`), which is what makes that experiment safe to run at all.
B1F_TRAP_DIRECTION = "Down"

#: ⭐⭐ EVERY WARP RESETS THE ENTIRE PUZZLE. `LoadMapFromWarp` re-copies the object templates from
#: ROM and `ClearTempFieldEventData()` wipes `FLAG_TEMP_*`, so boulders revert and smashed rocks
#: respawn on EVERY entry to B1F. CONFIRMED LIVE, for free: the `trap` run's first reading showed
#: `local_id 3` back at (4,7) after the `correct` run had left it at (3,7).
#: ⛔ ⇒ **NEVER CACHE "THE PUZZLE IS SOLVED" ACROSS A WARP.** Re-solve on every entry.
B1F_PUZZLE_RESETS_ON_WARP = True

#: The whole B1F descent, generously bounded. The measured solve ran well inside this.
B1F_BUDGET_FRAMES = 120_000

#: ⛔⛔ 1F (15,40) IS AN **ARROW WARP** (`MB_SOUTH_ARROW_WARP`), NOT A STEP-ON WARP. `TryArrowWarp`
#: fires only when the player STANDS on the tile, FACES South and HOLDS Down. ⇒ walking onto it does
#: nothing; `_walk_through_warp("Down", ...)` works because it keeps pressing Down.
#: ‼ AND THE COROLLARY BITES INWARD: arriving from Ever Grande leaves the bot STANDING ON this tile,
#: so any stray Down press warps it straight back out of Victory Road.
VR_EXIT_ARROW = VR_ENTRANCE          # (15,40) — the same tile, used in the outward direction
VR_EXIT_APRON = (15, 39)             # one north; MEASURED walkable (leg 5 and the training leg both
                                     # stood here). ⛔ Never navigate to (15,40) itself — warp trap.

#: ⚠ Heal when ANY battler is fainted, or the party is below this fraction of total HP. Measured
#: degradation without a heal: 95%/0 fainted → 67%/2 → **32%/3** across three legs.
HEAL_HP_FRACTION = 0.70

LEG6_READINGS = ("R6-HEAL", "R6-ENTER", "R6-PUSH1", "R6-PUSH2", "R6-SMASH", "R6-LADDERPATH", "R6-B2F")

# ============================== LEG 7 — VICTORY ROAD B2F: SURF AND DESCEND =====================
#: ⭐⭐ THIS LEG IS ONE `navigate_to`, AND THAT IS A MEASURED DECISION, NOT LAZINESS.
#: A 19-agent recon produced a 13-phase hand-built crossing (two Surf mounts, a forced descent,
#: three elevation layers). ⛔ **THAT ROUTE WAS REFUTED AND WOULD HAVE STRANDED THE BOT** — its first
#: mount at (33,17) enters a 43-tile DEAD-END POND that cannot reach the exit ladder.
#: ✅ Meanwhile `--driver ch23b2fprobe` measured our own planner solving the whole thing:
#:     `calculate_path (30,25) -> (18,12)` = **63 wp, actions {Surf: 1, Waterfall: 1}**
#: ⇒ the planner MOUNTS SURF AND RIDES THE DESCENT ITSELF. Leg 4 had to hand-drive its waterfall
#: **CLIMB** because the planner will not plan one; a **DESCENT** it plans fine.
#: ‼ So the lesson is not "trust agents less" — their TILE reads were all correct — it is that a
#: hand-built route is a SYNTHESIS, and the planner is the authority on what our bot can walk.
B2F = MapRSE.VICTORY_ROAD_B2F

#: Where leg 6's ladder drops us. MEASURED: `b2f_arrival = ((24,45), (30,25))`.
B2F_ARRIVAL = (30, 25)

#: ⛔⛔ THE EXIT LADDER IS A **WARP** — NEVER A NAVIGATION TARGET. This is the FIFTH warp-as-
#: destination trap in this chapter, and it is MEASURED here, not assumed: `calculate_path (30,25) ->
#: (19,12)` returns **64 wp whose LAST waypoint is `map=(24,44) coords=(17,16) is_warp=True`** — i.e.
#: aiming at it silently ends on **B1F**, doing leg 8's job, and an honest end-position grade would
#: FAIL a perfect run. Aim at an apron; step onto the ladder explicitly.
B2F_EXIT_LADDER = (19, 12)

#: ⭐ MEASURED: the ladder sits on a 6-tile island, and **(19,11) is a WALL** — a north approach is
#: impossible. THREE neighbours work: (18,12)→E, (20,12)→W, (19,13)→N; our planner reaches (18,12)
#: and (19,13) in **63 wp each**. ⇒ `_ladder_apron()` picks whichever it can actually reach rather
#: than hardcoding one, because two independent agents disagreed about this and BOTH were right.
#: ⚠ MEASURED AND NON-DISCRIMINATING: `avoid_encounters` True vs False both give **63 wp with the
#: same actions** on this crossing. ⇒ the default stands; **do not spend time tuning that knob here**
#: (it is the `POKEBOT_CH21_POCKET_ARM` shape — an arm whose two sides produce identical output).
B2F_BUDGET_FRAMES = 150_000

LEG7_READINGS = ("R7-ENTER", "R7-APRON", "R7-CROSS", "R7-B1F")

# ============================== LEG 8 — THE RETURN: B1F's 2x2 PLUG -> 1F =======================
#: ⛔⛔ **URGENT, NOT OPTIONAL: THE BOT IS TRAPPED UNTIL THIS SHIPS.** MEASURED
#: (`--driver ch23retprobe`, observe-only) from the B2F landing **B1F (17,16)**: `(8,3)` (leg 6's
#: ladder to 1F) **UNREACHABLE**, `(30,25)` (back to B2F) **UNREACHABLE**, `(20,21)` (the 1F ladder)
#: **UNREACHABLE behind the plug**. ⇒ **the only exit from this island is through the plug**, so the
#: party cannot leave Victory Road to heal, train or shop until leg 8 works.
#: ‼ I documented the dependency BACKWARDS for one commit (as "attrition blocks leg 8"). It is the
#: reverse. ⇒ **measure the dependency before pricing the remedy.**
B1F_RETURN_LANDING = (17, 16)          # where leg 7's ladder drops us

#: ⛔⛔ THE 1F LADDER IS A **WARP** — never a navigation target. SIXTH trap of this shape in §Ch23.
B1F_1F_LADDER = (20, 21)

#: ⭐ THE 2x2 PLUG, each keyed by its LIVE `local_id`. MEASURED present from (17,16):
#: rock `11` @ (20,25) and boulder `6` @ (21,25). ⚠ Boulder `5` @ (20,26) and rock `12` @ (21,26)
#: sit ~10 tiles out, at the edge of the CAMERA WINDOW — **absent from the visible list is NOT
#: evidence they are gone**; confirm them from an adjacent standpoint, which the leg does.
#: ⛔⛔ **THE TRAP, AND IT IS AVOIDED BY CONSTRUCTION RATHER THAN GUARDED AGAINST.** Boulder `6` at
#: (21,25) has a SINGLE legal push — **EAST** — and it **BRICKS THE ROUTE** (its target (22,25) is
#: already the base of the only column to the ladder; MEASURED unreachable from here). ⇒ **push
#: boulder `5` at (20,26) NORTH instead, which makes boulder 6's trap physically unreachable.**
#: ‼ That is why the order below is not interchangeable: it is chosen so the wrong move cannot be
#: made, not so that a guard catches it afterwards.
B1F_SMASH_A = {"local_id": 11, "tile": (20, 25), "approach": (19, 25), "face": "Right"}
B1F_PUSH_N = {"local_id": 5, "tile": (20, 26), "approach": (20, 27), "face": "Up", "to": (20, 25)}
B1F_SMASH_B = {"local_id": 12, "tile": (21, 26), "approach": (20, 26), "face": "Right"}

#: ⛔ THE TRAP BOULDER. Leg 8 NEVER pushes it — the step order makes its only legal push (EAST)
#: physically unreachable — but it is WATCHED, because "the leg never touches it" is a claim and an
#: obstacle report that cannot see it cannot support that claim.
B1F_TRAP_BOULDER_ID = 6

#: MEASURED approach distances from (17,16): (19,25) = 15 wp, (20,27) = 18 wp.
B1F_RETURN_BUDGET = 120_000

#: 1F's exit is an ARROW WARP — see `VR_EXIT_ARROW`. From (21,32) the bot must reach (39,5), stand
#: on it facing South, and HOLD Down. ⚠ MODELED at 61 steps by an agent; not yet driven.
F1_LADDER_LANDING = (21, 32)
F1_EXIT_ARROW = (39, 5)

LEG8_READINGS = ("R8-ENTER", "R8-SMASHA", "R8-PUSHN", "R8-SMASHB", "R8-LADDERPATH", "R8-1F")

# ============================== LEG 9 — OUT OF VICTORY ROAD ====================================
#: ⛔⛔ (39,5) IS AN **ARROW WARP** (`MB_SOUTH_ARROW_WARP`), NOT A STEP-ON WARP: it fires only when
#: the player STANDS on it, FACES South and HOLDS Down. ⚠ We have driven the OTHER arrow warp
#: (15,40) OUTWARD (leg 6's heal), so the mechanic is proven — **this tile is not.**
#: ⭐ MEASURED (leg 8's continuation check): the apron **(38,5)** is reachable from (21,32) in
#: **62 wp**. ⛔ (39,6), the tile SOUTH of the arrow, is a WALL — never aim there.
F1_EXIT_APRON = (38, 5)

#: Where the arrow warp lands. ⚠ MODELED by an agent as EVER_GRANDE (18,27); **not yet observed.**
EG_EXIT_LANDING = (18, 27)

#: ⛔⛔ THE OPEN QUESTION THIS LEG EXISTS TO SETTLE. A research pass DERIVED (its own flood-fill, not
#: the decomp) that (18,27) sits on a **closed plateau containing the League door (18,5) but NOT the
#: Ever Grande Poké Center**. If that holds, "exit and heal" is WRONG and the only heal is the
#: **League's own Poké Center on `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F`** — which also has a Mart.
#: ‼ That agent flagged its own elevation model as a reimplementation and asked for a live probe.
#: ⇒ this leg walks out and then ASKS OUR PLANNER, rather than inheriting the claim.
EG_LEAGUE_DOOR = (18, 5)

LEG9_READINGS = ("R9-APRON", "R9-ARROW", "R9-OUT", "R9-WHERECANWEHEAL")

# ============================== LEG 10 — THE LEAGUE HEAL ======================================
#: ⭐⭐ THE ONLY HEAL REACHABLE FROM THE VICTORY ROAD EXIT. MEASURED (leg 9): Ever Grande's own Poké
#: Center (27,49) is **UNREACHABLE** from the landing — the exit sits on a closed plateau — while the
#: League door is **37 wp** away. An adversarial decomp pass then confirmed *why*: EVER_GRANDE_CITY
#: is split into a north plateau and a south beach connected only THROUGH Victory Road.
LEAGUE_1F = MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F

#: ⛔⛔ THE ENTRY IS A **DOOR**, NOT A STEP-ON WARP AND NOT AN ARROW WARP — a THIRD warp kind in this
#: chapter, each needing different handling:
#:     step-on warp (ladders) -> stand BESIDE, press TOWARD          (legs 6, 7, 8)
#:     arrow warp   (39,5)    -> stand **ON**, press its OWN direction (leg 9)
#:     door        (18,5)     -> stand BESIDE at (18,6), FACE north, HOLD Up
#: `(18,5)` is `MB_ANIMATED_DOOR` with **collision 1** — you never stand on it. VERIFIED in our own
#: data: `get_map_data` reports `'Door Warp', coll 1, elev 0`.
LEAGUE_DOOR = (18, 5)
LEAGUE_DOOR_APRON = (18, 6)

#: ⛔⛔⛔ **THE TRAP NOBODY ASKED ABOUT, AND IT IS ONE TILE FROM WHERE LEG 9 LANDS.**
#: `(18,27)` is `MB_NON_ANIMATED_DOOR` with **collision 0 — WALKABLE** — and it warps straight back
#: into VICTORY_ROAD_1F. `IsWarpMetatileBehavior` includes non-animated doors, so **completing a
#: single step onto it warps instantly: no facing requirement, no button, no confirmation.**
#: ⇒ from the landing (18,28), **NORTH IS A ONE-STEP TRAP BACK INTO VICTORY ROAD** with a 4% party.
#: ✅ Our planner already routes around it (`map_path.py:971` costs a non-destination warp tile at
#: 1,000,000) and the optimal route runs EAST first — but ⛔ **any "nudge north" or "unstick" recovery
#: heuristic at (18,28) undoes the entire trip.** This constant exists so that guard is nameable.
EG_VICTORY_ROAD_RETURN_TRAP = (18, 27)

#: ⛔ THE NURSE HAS NO WALKABLE NEIGHBOUR. (3,2) is behind a counter: (2,2), (4,2), (3,1) and (3,3)
#: are all collision 1, and **(3,3) is `MB_COUNTER`**. `GetInteractedObjectEventScript` looks ONE
#: TILE FURTHER across a counter, so the bot must stand at **(3,4)** facing NORTH and press A.
#: ‼ A naive "navigate adjacent to the NPC then talk" router FAILS here — which is exactly why
#: `heal_in_pokemon_center` cannot be reused: it walks to (7,4), the standard Centre nurse tile.
LEAGUE_NURSE_STAND = (3, 4)

#: Where the door drops us inside, and the tile to stand on to leave. ⛔ The EXIT is an ARROW warp
#: (`MB_SOUTH_ARROW_WARP`), so it does NOT fire on a step — the bot cannot fall out by accident, and
#: must stand ON it and press Down.
LEAGUE_ENTRY_LANDING = (9, 11)
LEAGUE_EXIT_TILE = (9, 11)

#: ⛔⛔ **DO NOT PRESS A NEAR THE GUARDS.** They sit at (9,2)/(10,2) while `FLAG_ENTERED_ELITE_FOUR`
#: is unset, blocking the north doors positionally — they are `TRAINER_TYPE_NONE`, so bumping them
#: does nothing and no script runs without an A-press. ‼ Talking to one sets that flag
#: **PERMANENTLY** (nothing in the decomp ever clears it), which parks the guards aside and leaves
#: (9,1)/(10,1) — **step-on** doors to Hall5 — open forever. ⇒ that is how a bot wanders into the
#: Elite Four by accident. The heal never goes near them.
#: ‼ AND `map.json` LISTS THE GUARDS AT (8,2)/(11,2) — those are the POST-flag positions, applied by
#: `copyobjectxytoperm`. The blocking positions exist only because `OnTransition` re-applies
#: `setobjectxyperm` on every entry. ⇒ **read LIVE object positions, never the template.**
LEAGUE_GUARD_TILES = ((9, 2), (10, 2))

#: ⚠ `(1,7)` is `MB_UP_ESCALATOR`, collision 0 — an accidental step-on warp to League 2F (the Cable
#: Club). Benign (2F warps straight back) but pointless; the heal route never touches it.
LEAGUE_ESCALATOR = (1, 7)

LEAGUE_HEAL_BUDGET = 100_000

LEG10_READINGS = ("R10-APRON", "R10-INSIDE", "R10-HEALED", "R10-OUT")

# ============================== LEG 11 — STOCK THE LEAGUE MART ================================
#: ⛔⛔ **THE BAG IS THE ELITE FOUR'S ENTIRE HEALING SYSTEM** (user directive 2026-09-04): five
#: consecutive fights, ~25 opposing Pokémon, every room sealing its own exit, and **no nurse past
#: the front door**. Items are fully legal in those battles — VERIFIED at `battle_main.c:4221-4239`,
#: where the only conditions that produce "Items can't be used here!" are LINK / FRONTIER / E-READER
#: / RECORDED, and an Elite Four fight is a plain `BATTLE_TYPE_TRAINER`.
#: ⇒ this leg is not housekeeping; it is the gauntlet's survivability.
LEAGUE_MART_STAND = (16, 4)          # the clerk is at (16,2) behind a `MB_COUNTER` at (16,3)

#: ⭐⭐ THE BASKET, AND THE ONE COUNTER-INTUITIVE CHOICE IN IT.
#: **Max Potion (₽2,500) is STRICTLY DOMINATED by Hyper Potion (₽1,200) FOR THIS PARTY.** Hyper
#: Potion heals a **flat 200 HP** (`item_effects.h:39`), and our whole party's max HP runs ~115-231
#: (Sceptile ~153, Swellow ~130, Mightyena ~140, Wailord ~231). ⇒ 200 full-heals every member,
#: Wailord included from 16 HP up, so a Max Potion buys **nothing** for ₽1,300 more. Skipping it is
#: what turns ₽36,000 into THIRTY heals instead of fourteen.
#: ⛔ Also deliberately NOT bought: **Ultra Ball** (every ball is BLOCKED in trainer battles —
#: `battle_script_commands.c:9915-9920`, the first branch, nothing overrides it) and **Max Repel**
#: (there is no wild-encounter table for ANY map past the League's front door).
#: ‼ ORDER IS LOAD-BEARING: the shop's quantity selector caps at `min(money / price, 99)` recomputed
#: from CURRENT money each transaction (`src/shop.c:1046-1051`), so **the largest line must be bought
#: FIRST** or the selector silently caps it low.
LEAGUE_BASKET = (
    ("Hyper Potion", 30),     # ₽36,000 — the basket; flat 200 HP full-heals anything we own
    ("Full Restore", 3),      # ₽9,000  — the one-turn emergency: low HP *and* status together
    ("Full Heal", 8),         # ₽4,800  — cheapest item on the board; Gen-3 freeze is permanent
    ("Revive", 3),            # ₽4,500  — anti-wipe insurance only (returns at HALF HP into L53-58)
)                             # ₽54,300 total against a MEASURED ₽56,041

#: ⚠ Money is not safe sitting still: `DoWhiteOut` (`overworld.c:358`) does `SetMoney(money / 2)`.
#: ⇒ unspent cash is cash at risk, and the gauntlet itself pays ~₽32,400 back on the way through.
LEAGUE_MIN_MONEY = 54_300

LEAGUE_SHOP_BUDGET = 80_000

LEG11_READINGS = ("R11-INSIDE", "R11-MENU", "R11-BOUGHT", "R11-VERIFIED", "R11-OUT")

# ============================== TRAINING — BEFORE WALLY ========================================
#: ⛔⛔ TRAIN ON **1F**, NOT B1F, AND THAT IS NOT A PREFERENCE — IT IS FORCED.
#: B1F is the better ground (950.8 EXP/battle vs 1F's 775.6, because B1F swaps 1F's low-level
#: Zubat/Whismur slots for more Hariyama at 184 base EXP). **But B1F is BEHIND WALLY.** The only
#: path to the ladder is 44 wp = 29 to Wally's trigger + 15 onward (MEASURED, `ch23route` R12), and
#: his triggers are a collision-geometry articulation pair — seal them and the ladder is
#: unreachable. ⇒ **the best training ground is gated behind the fight the training is FOR.**
#: ‼ A research pass recommended B1F without noticing that. Grinding 18% slower on 1F is the whole
#: cost of the mistake not being made.
#: ⭐ MEASURED 'Cave' (`ch23route` R15) — and that check is not pedantry: only `MB_CAVE` rolls
#: encounters on 1F, 16 walkable tiles are `MB_NORMAL`, and a spin parked on one of those generates
#: ZERO battles while looking perfectly healthy. That is `#24-grindconverge`'s exact shape.
TRAIN_SPOT_1F = (VR1F, (15, 39))     # 1 step from the entrance warp, elevation 3

#: ⭐⭐ THE TARGET, DERIVED FROM THE OPPOSITION *AND THEN PRICED* — 50 was the first answer and the
#: measurement overruled it. Max level faced is **58** (Champion Wallace's Milotic); the Elite Four
#: runs 49 / 51 / 53 / 55 and Wally's ace is 45.
#: ⛔ BUT L50 IS NOT AFFORDABLE ON 1F. Measured 2026-09-04 (`POKEBOT_CH23_ESTIMATE_ONLY=1`), worst
#: SINGLE mon against the 250,000 per-call ceiling:
#:     L46 → 339,621 total · L47 → 438,498 (worst Wailmer 217,816 ✅) · L48 → 556,004
#:     L50 → 793,882 (worst **Wailmer 359,683** ⛔ — 1.4x over the ceiling on its own)
#: ⇒ **47 is the highest target that fits, and it is ALSO `CRUNCH_LEVEL`.** The move constraint and
#: the budget constraint landing on the same number is a coincidence worth stating out loud, because
#: it means neither can be relaxed to buy room for the other.
#: ‼ 47 clears Wally's ace (45) outright and sits 2 under Sidney. It does NOT clear Wallace's 58 —
#: the remaining gap is meant to be closed on **B1F after Wally** (950.8 EXP/battle vs 1F's 775.6),
#: which is the only better ground and is gated behind exactly the fight this training is for.
TRAIN_TARGET = 47

#: ⛔ THE BINDING CONSTRAINT IS A MOVE, NOT A LEVEL. Mightyena learns **Crunch at L47** and has NO
#: Dark TM available at all — below 47 there is no answer to Phoebe's all-Ghost team.
CRUNCH_LEVEL = 47

#: ⚠ NOT BATTLERS FOR THIS ARC — training them costs 3.7x the work and fixes nothing, because the
#: problem is TYPING, not levels. ⛔ "Bench" here means **do not train and do not lead** — it does
#: NOT mean deposit: a PC deposit is the hazard `assert_carriers_survived` exists to catch.
#: ⭐ And benching is safe only because a FULL-HP party makes the faint-replacement ranking fall
#: through `hp_fraction` (all tie at 1.0) to `-level`, which then picks the STRONGEST.
BENCH_SPECIES = ("Zigzagoon", "Linoone", "Castform")

#: The frame ceiling every existing `train_team` caller gates on before calling
#: (`story_mode.py:1034`). ⛔ `train_team` itself has NO frame budget — only a 500-ROUND guard — and
#: KI-28 burned 19.9M frames on a target the local grass could not deliver.
MAX_TRAINING_FRAMES = 250_000

TRAIN_READINGS = ("R-TRAINPRE", "R-ESTIMATE", "R-TRAINED", "R-READY", "R-TRAINCONTINUE")

#: ⛔ A NAMED-BAD DENYLIST, NOT AN ALLOWLIST. The tile type at UW126 (45,66) has NEVER been read;
#: two independent designs predicted DIFFERENT values, and §Ch21 emerged there three times with no
#: tile guard at all. An allowlist can only LOSE here: it cannot make a correct run more correct and
#: it can refuse one. Drive 1 REPORTS the real string; tighten in a follow-up, not before.
EMERGE_REFUSED_TILE_TYPES = ("Water Door", "Underwater Blocked Above", "Seaweed No Surfacing")

#: §Ch22's own bar on this exact fixture. ⚠ Leg 4 wants 3 (Carlee + Harrison at x=101 are
#: unavoidable) but that is REPORTED, not enforced — refusing here would block a leg that can finish.
MIN_PARTY_TO_DEPART = 2

#: ⛔ ONLY these tick on the overworld. Field poison is the one non-battle party-wipe and it ticks
#: while surfing; burn/paralysis/sleep do not.
FIELD_TICKING_STATUSES = ("Poison", "BadPoison")

#: ⛔ THESE ARE THE KI-83 MITIGATION, NOT TUNING KNOBS. Each bounds an UPSTREAM helper that has
#: no bound of its own; raising one to make a failure go away restores the silent-forever it
#: exists to prevent. If a budget trips, read the raise — it names which call reached its cap.
HEAL_BUDGET = 30_000
DIVE_TASK_BUDGET = 3_000

#: ⛔ THE LEG OWNS ITS LABEL VOCABULARY AND THE DRIVER **IMPORTS** IT. A private driver copy fails in
#: the worst direction: a rename makes a PERFECT run report `missing=[...]`, and the obvious repair
#: is to delete a required reading.
LEG23_READINGS = (
    "R-PRE", "R-HEAL", "R-ARM", "R-DEPART",
    "R-PIN", "R-DIVE", "R-UWWARP", "R-EMERGETILE", "R-SURFACE", "R-CONTINUE",
)


def _os_environ_flag(name: str) -> bool:
    """A plain env-var switch, read as an exact '1'. ⛔ Never truthiness on the string — "0" is
    truthy in Python and would turn every guard permanently ON."""
    import os

    return os.environ.get(name) == "1"


#: ⭐ The fault arms this chapter honours, mapped to their **FULL env names as literals**.
#: ‼ The literal spelling is the point, twice over: `lint_docs` R6 cross-checks the registry against
#: names that appear in CODE (a mention in a comment deliberately does not count — see
#: `#24-advisorydocstring`), and a human grepping for the flag finds nothing if it only ever exists
#: as an f-string fragment. Add an arm here and it is registered, validated and findable at once.
FAULT_ARMS = {
    #: leg 2 — skip the pre-departure heal, so `departure_ready()`'s failure branch is exercisable
    "NOHEAL": "POKEBOT_CH23_FAULT_NOHEAL",
    #: leg 2 — skip the Sootopolis layout pin
    "NOPIN": "POKEBOT_CH23_FAULT_NOPIN",
    #: leg 3 — step the WRONG way off the dive tile ("Up" instead of "Down")
    "BADSTEP": "POKEBOT_CH23_FAULT_BADSTEP",
    #: leg 3 — do not lead the strongest battler across the 273-tile crossing
    "NOLEAD": "POKEBOT_CH23_FAULT_NOLEAD",
    #: leg 4 — do not drive the waterfall climb the planner refuses to plan
    "NOCLIMB": "POKEBOT_CH23_FAULT_NOCLIMB",
    #: leg 4 — skip the Ever Grande heal that resets every `hp_fraction` to 1.0
    "NOHEAL4": "POKEBOT_CH23_FAULT_NOHEAL4",
    #: leg 5 — do not lead the strongest battler into the Wally fight
    "NOLEAD5": "POKEBOT_CH23_FAULT_NOLEAD5",
    #: leg 6 — skip the FIRST boulder push, so the ordering guard must catch the sealed corridor
    "NOPUSH1": "POKEBOT_CH23_FAULT_NOPUSH1",
    #: leg 6 — skip the Rock Smash, so the ladder-reachability guard must catch the blocked route
    "NOSMASH": "POKEBOT_CH23_FAULT_NOSMASH",
    #: leg 6 — skip the pre-descent heal, to reproduce the degraded-party descent on demand
    "NOHEAL6": "POKEBOT_CH23_FAULT_NOHEAL6",
    #: leg 7 — aim navigation AT the exit ladder instead of an apron, so the warp-override trap
    #: fires on demand and the apron guard must catch it
    "LADDERAIM": "POKEBOT_CH23_FAULT_LADDERAIM",
    #: leg 8 — skip the NORTH push, so the ladder-reachability guard must catch the still-sealed plug
    "NOPUSHN": "POKEBOT_CH23_FAULT_NOPUSHN",
    #: leg 8 — take the TRAP: push boulder 6 at (21,25) EAST, which bricks the route. ⛔ The leg must
    #: refuse to do this on its own; the arm exists to prove the trap is real, as leg 6's did.
    "TRAPPUSH": "POKEBOT_CH23_FAULT_TRAPPUSH",
    #: leg 9 — aim the exit navigation AT the arrow tile (39,5) instead of its apron (38,5), so the
    #: apron guard must catch it (arrow warps are not step-on, so this should simply strand us there)
    "ARROWAIM": "POKEBOT_CH23_FAULT_ARROWAIM",
    #: leg 10 — skip the nurse interaction, so the "did the party actually heal?" guard must fire
    "NOHEAL10": "POKEBOT_CH23_FAULT_NOHEAL10",
    #: leg 11 — skip the purchase, so the "is the basket actually IN the bag?" guard must fire
    "NOBUY": "POKEBOT_CH23_FAULT_NOBUY",
}


def _fault(arm: str) -> bool:
    """A fault arm is ON only when its env var is exactly '1'. ⛔ Never truthiness on the string."""
    import os

    # ⛔⛔ VALIDATE THE ARM NAME. The flag is BUILT with an f-string, so a typo'd arm reads an
    # env var nobody sets and returns False forever — a fault hook that cannot fire, which is the
    # "control that cannot fail" shape this project has paid for repeatedly (see the
    # `POKEBOT_CH21PROBE_FAULT` row: a probe assertion that passed because it COULD NOT fail).
    # ‼ It also keeps the full literal names greppable, which is what `lint_docs` R6 checks and what
    # a human needs to find them at all.
    if arm not in FAULT_ARMS:
        raise BotModeError(
            f"Ch23: unknown fault arm {arm!r}. Known arms: {sorted(FAULT_ARMS)}. ⛔ Raising rather "
            f"than returning False, because a mistyped arm would silently disable the fault it "
            f"names — a fault hook that cannot fire is worse than none, since it reads as tested."
        )
    return os.environ.get(FAULT_ARMS[arm]) == "1"


def _budgeted(gen: Generator, budget_frames: int, label: str) -> Generator:
    """Frame-cap an UNBOUNDED upstream helper, and close it on the way out.

    ⛔⛔ THIS IS THE MITIGATION FOR **KI-83**, AND IT IS THE ONLY ONE AVAILABLE.
    `tasks_scripts.py` contains 8 wait loops with no frame cap and no `_check_abort()` — including a
    bare `while True:` — and `heal_in_pokemon_center`, `dive()` and `surface_from_dive()` all reach
    them. That file is **byte-identical to the pristine upstream mirror**, so patching it is a
    DIVERGENCE decision with the widest blast radius in the codebase. ⇒ bound it HERE, at the call
    site, and leave upstream alone.

    ‼ `finally: gen.close()` matters as much as the cap: without it the inner generator is left
    suspended holding whatever buttons it had pressed, and the next leg inherits them.
    """
    frames = 0
    try:
        for _ in gen:
            frames += 1
            if frames > budget_frames:
                raise BotModeError(
                    f"Ch23: '{label}' exceeded its {budget_frames}-frame budget. This is the KI-83 "
                    f"shape: the upstream helper waits on a task that never started (a whiteout "
                    f"inside the call kills the menus), and nothing in `tasks_scripts.py` checks "
                    f"the abort latch. The budget is what turns a silent forever into a named "
                    f"failure — do not raise it without reading KI-83 first."
                )
            _check_abort()
            yield
    finally:
        gen.close()
        context.emulator.reset_held_buttons()


def _tile_type_here():
    """The live tile behaviour under the avatar, or None.

    ⛔ `getattr(..., None)` on purpose: this is REPORTED and used only against a named-bad denylist,
    so a missing attribute must degrade to "unknown, proceed", never to a crash or to a False that
    silently passes a guard.
    """
    from modules.map import get_map_data_for_current_position

    return getattr(get_map_data_for_current_position(), "tile_type", None)


# --------------------------------------------------------------------------------------------
# READINGS — every one is a fact about the WORLD, read fresh. None is cached across a yield.
# --------------------------------------------------------------------------------------------
def respawn_reading():
    """The saved whiteout respawn as `(map_group, map_number)`, or a REASON STRING.

    ⛔ NEVER `None`: a `None` compares unequal to everything and reads as "not armed", which is the
    right answer for the wrong reason and hides a broken read forever.
    """
    try:
        from modules.save_data import get_last_heal_location

        return get_last_heal_location()
    except Exception as error:  # noqa: BLE001 - a refusal IS the reading
        return f"unreadable: {type(error).__name__}: {error}"


def respawn_is_armed(map_enum=CITY) -> bool:
    """Is the whiteout respawn armed to `map_enum`?

    ⛔ COMPARE AGAINST `.value`, NEVER THE ENUM. `get_last_heal_location()` returns a plain
    `(group, number)` tuple; comparing a tuple to an enum member is False forever, which would make
    this guard silently unarmable.
    ⛔ FAILS CLOSED: a reason string is not armed.

    ‼ WHY THIS MATTERS AT ALL — it is the expensive failure on this leg. The respawn is set by
    `setrespawn` in the Poké Center's **ON_TRANSITION**, i.e. by merely WALKING IN; healing is not
    required. If the bot has never entered the Sootopolis Center, a whiteout anywhere on the ocean
    leg dumps it at whatever far earlier Center is still saved — hours away, with no Center between
    Sootopolis and the Pokémon League.
    """
    reading = respawn_reading()
    return isinstance(reading, tuple) and reading == map_enum.value


def field_move_carriers() -> dict:
    """`{move_name: (pid, species) | None}` for the moves this chapter cannot proceed without.

    ⛔ IDENTITY, NEVER A SLOT INDEX — and `(pid, species)`, never a bare PID: a Ninjask/Shedinja pair
    shares a personality value (KI-78, observed live in a fixture), so a PID alone is not a key.
    ⛔ AND NEVER FILTER BY HP. Field moves ignore HP entirely — decomp-verified: there is no HP check
    in `CursorCb_FieldMove`, `SetUpFieldMove_Surf/Dive/Waterfall`, or `ScrCmd_checkpartymove`, which
    skips only `SPECIES_NONE` and eggs. **Our sole Dive carrier starts this chapter FAINTED and
    Dives normally.** A liveness filter here would refuse a move the game permits.
    ‼ Lowest-numbered slot wins, matching `checkpartymove` — the prompt path picks that one, not the
    one a caller might prefer.
    """
    out = {"Surf": None, "Dive": None, "Waterfall": None}
    for mon in get_party():
        if mon is None or mon.is_egg:
            continue
        for learned in mon.moves:
            if learned is None:
                continue
            name = learned.move.name
            if name in out and out[name] is None:
                out[name] = (mon.personality_value, mon.species.name)
    return out


def party_identities() -> dict:
    """`{(pid, species): (hp, total, status)}` — the roster as identities, never as a count.

    ‼ Six alive and six-with-one-down both report `party=6`. A count cannot answer "is the mon we
    cannot lose still here?", which is the question this chapter actually has.
    """
    out = {}
    for mon in get_party():
        if mon is None or mon.is_egg:
            continue
        status = getattr(getattr(mon, "status_condition", None), "name", None) or "None"
        out[(mon.personality_value, mon.species.name)] = (mon.current_hp, mon.total_hp, status)
    return out


def poisoned_members() -> list:
    """Members carrying a status that ticks on the OVERWORLD.

    ⚠ Field poison is the only non-battle way to lose the party, it ticks while SURFING, and the
    ocean leg has no Poké Center for its entire length. Curing before departure is cheap insurance.
    """
    return [
        f"{species}#{pid:08X}"
        for (pid, species), (_hp, _total, status) in party_identities().items()
        if status in FIELD_TICKING_STATUSES
    ]


def assert_carriers_survived(where: str) -> None:
    """⛔⛔ REFUSE TO CONTINUE IF A HEAL ATE A FIELD-MOVE CARRIER. Call after EVERY heal.

    ‼ WHY THIS EXISTS, AND IT IS NOT PARANOIA. `heal_in_pokemon_center` does not only heal — it
    piggybacks TWO PC-deposit paths while it is already inside the centre
    (`higher_level_actions.py:353-355` and `:370-381`), and `team_policy.py:36` defines dead weight
    as **`DEAD_WEIGHT_LEVEL_GAP = 8` levels behind the lead**.
    ⇒ with Sceptile L51 leading, THIS PARTY IS MOSTLY "DEAD WEIGHT" BY THAT MEASURE: Zigzagoon is
    32 levels behind, Castform 15, **Wailmer 11**, Swellow 9.
    ⛔ **AND WAILMER IS THE SOLE CARRIER OF DIVE *AND* WATERFALL** — depositing it strands the
    chapter with no way back through the crater and no way up the waterfall.

    ✅ THREE INDEPENDENT REASONS IT IS INERT TODAY — all verified by reading, none assumed:
      1. the rotation deposit bails at `pc_trip.py:83` unless `POKEBOT_PC_ROTATION` is 1 (default "0");
      2. the KI-63 slot-freeing deposit fires only when a caller sets `_needs_party_slot`, which no
         §Ch23 driver does; and
      3. ⭐ **Wailmer is explicitly EXEMPT**: `team_policy.py:147-149` never deposits a SOLE HM
         carrier (`_only_hm_carrier`, `:119-128`), and `HM_MOVES` (`:64`) includes both `Dive` and
         `Waterfall`.
    ⛔⛔ **BUT EXEMPTION 3 IS COMPUTED FROM THE LIVE MOVEPOOL AND IS ONE MOVE AWAY FROM EVAPORATING.**
    A SHARED HM protects NEITHER mon — the precedent is in this very chapter's neighbour:
    `sootopolis_gym.py:951` records that Zigzagoon was **not** HM-exempt precisely *"because Wailmer
    shares its Surf"*. ⇒ the moment anything else learns Dive or Waterfall, Wailmer becomes
    deposit-eligible like everything else — and it is 11 levels behind the lead, well past the
    8-level threshold.
    ⇒ **that is exactly why this guard is cheap and permanent rather than redundant:** it costs one
    party read after a heal, and it converts a silent chapter-stranding into a named refusal.
    ‼ Assert by IDENTITY, never by party count — a deposit plus a catch nets to six.
    """
    carriers = field_move_carriers()
    lost = [move for move in ("Surf", "Dive", "Waterfall") if carriers[move] is None]
    if lost:
        raise BotModeError(
            f"Ch23: after {where}, the party no longer carries {lost}. Roster now: "
            f"{sorted(party_identities())}. ⛔ The most likely cause is a PC deposit piggybacked on "
            f"the heal (`higher_level_actions.py:353` / `:370`), which treats anything "
            f"{8} levels behind the lead as dead weight — and this party is mostly that. "
            f"Dive is the only exit from the Sootopolis crater and Waterfall the only way up to "
            f"Victory Road, so continuing would strand the run."
        )


def departure_ready() -> bool:
    """Is leg 2's work already done? ONE copy, consumed by the leg gate AND the driver.

    ⛔ Two copies of this predicate would drift, and the half that drifts is the one that decides
    whether a leg self-skips.
    """
    if not respawn_is_armed():
        return False
    identities = party_identities()
    if len(identities) < MIN_PARTY_TO_DEPART:
        return False
    if any(hp < total for hp, total, _ in identities.values()):
        return False
    if poisoned_members():
        return False
    return all(field_move_carriers()[move] is not None for move in ("Surf", "Dive", "Waterfall"))


def crater_left() -> bool:
    """Leg 3's completion predicate — a POSITIVE WHITELIST of "outside the crater".

    ⛔ NOT `not _on_map(CITY)`. A negative predicate calls the Poké Center interior, a battle
    transition and any mid-warp frame "left the crater", and the leg would then self-skip from
    inside a building.
    """
    return _on_map(R126)


def departed_sootopolis() -> bool:
    """The one name the driver and any future chapter share."""
    return crater_left()


# --------------------------------------------------------------------------------------------
# PREFLIGHT
# --------------------------------------------------------------------------------------------
def assert_ch23_preflight(report=None) -> None:
    """Refuse to start on a premise this chapter cannot recover from. Called ONCE, before the loop.

    ⛔ `report=None` is a real caller shape, so the prologue below is not defensive noise: without
    it `_take(None, ...)` is a `TypeError` for every caller that is not the orchestrator.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())

    where = _where()
    if isinstance(where, str):
        raise BotModeError(f"Ch23 preflight: cannot read the avatar's position — {where}")
    map_value, tile = where
    # ⛔⛔ THIS SET MUST COVER EVERY MAP `leave_the_crater` CAN RESUME FROM, NOT JUST THE START.
    # An earlier version listed only the island side and ROUTE126 — so a fresh run from a savestate
    # taken mid-leg-3 (on either underwater map) raised HERE, before the phase selector that exists
    # precisely to resume it. ‼ THAT IS THE SAME BUG I HAD ALREADY FIXED TODAY IN THE ORCHESTRATOR
    # (see `depart_sootopolis`): I widened one gate and left its SIBLING narrow. ⇒ **fixing an
    # instance is not fixing the class — when a precondition is wrong, grep for its siblings.**
    if map_value not in [m.value for m in _RESUMABLE_MAPS]:
        raise BotModeError(
            f"Ch23 preflight: starting on map {map_value} at {tile}, which is none of "
            f"{[m.name for m in _RESUMABLE_MAPS]}. This chapter starts inside the Sootopolis crater "
            f"(or its Poké Center), resumes from either underwater map mid-leg-3, and is already "
            f"done on ROUTE126."
        )

    carriers = field_move_carriers()
    missing = [m for m in ("Surf", "Dive", "Waterfall") if carriers[m] is None]
    if missing:
        raise BotModeError(
            f"Ch23 preflight: no party member knows {missing}. Dive is the ONLY exit from the "
            f"Sootopolis crater and Waterfall is the ONLY way up to Victory Road, so this is a "
            f"hard stop, not a degraded run. Carriers seen: {carriers}"
        )

    identities = party_identities()
    if len(identities) < MIN_PARTY_TO_DEPART:
        raise BotModeError(
            f"Ch23 preflight: {len(identities)} usable party member(s), need >= "
            f"{MIN_PARTY_TO_DEPART}. Roster: {sorted(identities)}"
        )

    report["carriers_at_preflight"] = carriers
    report["identities_at_preflight"] = identities
    _take(report, "R-PRE")


def assert_departure_ready() -> None:
    """Leg 3's own precondition, re-read FRESH — the same facts as leg 2's gate, as named raises.

    ‼ Re-read rather than trusting leg 2's report: between the two, a whiteout may have happened,
    and the whole point of the respawn check is the case where something went wrong.
    """
    if not respawn_is_armed():
        raise BotModeError(
            f"Ch23: refusing to leave the crater with the whiteout respawn UNARMED "
            f"(reads {respawn_reading()!r}, want {CITY.value}). A whiteout on the ocean leg would "
            f"warp the bot to a far earlier Poké Center, and there is no Center between Sootopolis "
            f"and the Pokémon League."
        )
    carriers = field_move_carriers()
    if carriers["Dive"] is None:
        raise BotModeError(
            f"Ch23: no Dive carrier at departure. Dive is the only exit from the crater. "
            f"Carriers: {carriers}"
        )


# --------------------------------------------------------------------------------------------
# LEG 2 — PREPARE TO DEPART
# --------------------------------------------------------------------------------------------
def _re_enter_pokemon_center_once(report) -> Generator:
    """Walk into the Poké Center to arm `setrespawn`, ONCE. ⛔ Bound = 1 PER ATTEMPT, never a loop.

    ‼ The respawn is armed by the Center's **ON_TRANSITION** — walking in is enough; healing is not
    required. That is why this exists separately from the heal.
    ⚠ THE BOUND IS PER ATTEMPT, NOT PER CHAPTER. The orchestrator retries up to 3 times, so a
    chapter call permits 3 of these. That is finite and intended — but *"a bounded loop re-entered
    by its dispatcher is still infinite"* is this project's most expensive lesson (KI-34 burned
    23.9M frames exactly that way), so the arithmetic is stated rather than left to be discovered.
    """
    yield from _navigate_riding_out(CITY, PC_APRON)
    yield from _budgeted(
        heal_in_pokemon_center(PokemonCenter.SootopolisCity), HEAL_BUDGET, "re-enter Poké Center"
    )
    report["pc_map_seen"] = True
    yield from wait_until_truly_controllable()
    assert_carriers_survived("the Sootopolis re-entry heal")


def prepare_to_depart(report=None) -> Generator:
    """LEG 2 — heal, arm the whiteout respawn, and prove both.

    ⛔ ORDER IS LOAD-BEARING: THE RESPAWN CHECK COMES **BEFORE** THE HP-RISE CHECK.
    An adversarial review found the reverse ordering fatal: on a genuine respawn fault the leg
    retries, the party is already at full HP from the first attempt's heal, and an HP-rise assertion
    placed first then raises *"HP total did not rise"* — **the wrong diagnosis** — and the re-arm
    retry this function exists for is never reached.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())

    hp_before = {k: v[0] for k, v in party_identities().items()}
    total_max = {k: v[1] for k, v in party_identities().items()}
    report["respawn_before"] = respawn_reading()
    report["poisoned_before"] = poisoned_members()

    # ---- heal ----------------------------------------------------------------------------------
    if _fault("NOHEAL"):
        context.message = "Ch23 FAULT NOHEAL: skipping the heal"
    else:
        yield from _budgeted(
            heal_in_pokemon_center(PokemonCenter.SootopolisCity), HEAL_BUDGET, "heal at Sootopolis"
        )
        report["pc_map_seen"] = True
        yield from wait_until_truly_controllable()
        assert_carriers_survived("the Sootopolis heal")

    after = party_identities()
    report["identities_after"] = after
    report["hp_after"] = {k: v[0] for k, v in after.items()}
    report["poisoned_after"] = poisoned_members()
    report["carriers_after"] = field_move_carriers()
    _take(report, "R-HEAL")

    # ---- arm the respawn — FIRST, for the reason in the docstring ------------------------------
    if not respawn_is_armed():
        yield from _re_enter_pokemon_center_once(report)
    report["respawn_after"] = respawn_reading()
    if not respawn_is_armed():
        raise BotModeError(
            f"Ch23 leg 2: the whiteout respawn is still not armed to Sootopolis after a re-entry "
            f"(reads {report['respawn_after']!r}, want {CITY.value}). Refusing to depart: a "
            f"whiteout on the ocean leg would strand the run at a far earlier Poké Center."
        )
    _take(report, "R-ARM")

    # ---- only NOW grade the heal, and only where a rise was actually possible -------------------
    # ⛔ GATED ON `hp_before < max`, NOT ON AN ATTEMPT NUMBER. That is the property that makes the
    # check meaningful, and it is readable from the state the run actually reached — an attempt
    # counter is not, and the design that used one could not implement it.
    # ⛔⛔ THIS CHECK IS **NOT** GATED ON THE FAULT FLAG, AND THAT IS THE WHOLE POINT.
    # An earlier version read `if could_rise and not _fault("NOHEAL")` — i.e. the fault arm switched
    # OFF the only check that could notice the fault. Since nothing else in leg 2, leg 3 or the
    # driver inspects HP before departure, `POKEBOT_CH23_FAULT_NOHEAL=1` would have printed
    # `ACCEPTANCE: PASS` with the party still at 61% and Wailmer fainted. ‼ **An arm that disables
    # its own detector is the purest form of "a sentence that says PASS"** — and it is the exact
    # defect I had just written prevention rules about, committed inside the fix for it.
    # ⇒ the arm now FAILS the run, loudly, naming itself. That is what proves the guard is real.
    could_rise = [k for k in hp_before if hp_before[k] < total_max[k]]
    if could_rise:
        risen = [k for k in could_rise if report["hp_after"].get(k, 0) > hp_before[k]]
        if not risen:
            raise BotModeError(
                f"Ch23 leg 2: {len(could_rise)} member(s) were below full HP and NONE rose after the "
                f"heal. before={hp_before} after={report['hp_after']}"
                + (" — EXPECTED: POKEBOT_CH23_FAULT_NOHEAL=1 is set, so this raise IS the arm "
                   "firing correctly." if _fault("NOHEAL") else "")
            )
    if report["poisoned_after"]:
        raise BotModeError(
            f"Ch23 leg 2: still carrying overworld-ticking status after the heal: "
            f"{report['poisoned_after']}. Field poison ticks while surfing and is the only "
            f"non-battle party wipe; the ocean leg has no Poké Center."
        )
    _take(report, "R-DEPART")


# --------------------------------------------------------------------------------------------
# LEG 3 — LEAVE THE CRATER
# --------------------------------------------------------------------------------------------
def leave_the_crater(report=None) -> Generator:
    """LEG 3 — dive out of Sootopolis and surface on ROUTE126.

    ⛔⛔ THE LAYOUT PIN LIVES **HERE**, NOT IN LEG 2, AND THAT IS A BLOCKER-GRADE DISTINCTION.
    `_pin_planner_to_live_layout` mutates a PROCESS-GLOBAL cache keyed by (rom, map) with no unpin,
    and §Ch21 leaves `SOOTOPOLIS_CITY` pinned to its LEGENDS_BATTLE layout. If the pin sat in leg 2:
    a whiteout on a later leg respawns in the crater with `departure_ready()` already True (a
    whiteout heals fully and the respawn is armed), so **leg 2 self-skips, the pin never runs**, and
    the walk below plans on the stale layout — which §Ch21 measured as *"37 waypoints, walks into
    live rock"* against 35 correct. ⇒ **a guard placed in a leg that self-skips is a guard that is
    not there.** It belongs in the leg whose walk it protects.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    # ---- phase 0: where are we? A resume may enter mid-leg. -------------------------------------
    if crater_left():
        report["leg3_entry"] = "already on ROUTE126"
        return

    # ⛔ RECORD WHICH PHASE THIS RUN ACTUALLY ENTERED. The driver's presence conjunct used to be
    # `crater_exits > 0`, which is incremented ONLY in the CITY branch — so a legitimate resume from
    # either underwater map would reach ROUTE126 and still be graded FAIL. A presence witness has to
    # witness the work the run DID, not the work a different entry path would have done.
    report["leg3_entry"] = next(
        (name for name, m in (("CITY", CITY), ("UWS", UWS), ("UW126", UW126)) if _on_map(m)),
        f"unknown:{_where()}",
    )

    if _on_map(CITY):
        assert_departure_ready()
        if not _fault("NOPIN"):
            report["pin"] = _pin_planner_to_live_layout(CITY)
            _take(report, "R-PIN")

        # ---- phase 1: ride out to the dive tile -------------------------------------------------
        yield from _navigate_riding_out(CITY, DIVE_OUT_TILE)
        if not _at(CITY, DIVE_OUT_TILE):
            raise BotModeError(
                f"Ch23 leg 3: aimed at the dive tile {DIVE_OUT_TILE} and ended on {_here_tile()}."
            )

        # ---- phase 2: dive -----------------------------------------------------------------------
        tile_type = _tile_type_here()
        report["dive_tile_type"] = tile_type
        yield from _budgeted(dive(), DIVE_TASK_BUDGET, "dive out of Sootopolis")
        yield from wait_until_truly_controllable()
        if not _on_map(UWS):
            raise BotModeError(
                f"Ch23 leg 3: dived from {DIVE_OUT_TILE} (tile_type={tile_type!r}) and did NOT "
                f"arrive on UNDERWATER_SOOTOPOLIS_CITY — now at {_where()}."
            )
        report["uw_arrival"] = _here_tile()   # ⚠ REPORTED against (9,6); never asserted.
        report["crater_exits"] = report.get("crater_exits", 0) + 1
        _take(report, "R-DIVE")

    # ---- phase 3: cross to the walk-on warp ------------------------------------------------------
    if _on_map(UWS):
        # ⛔ `navigate_to` is `while not player_is_at(...)` with an early `return` on an empty plan,
        # so if the dive already landed ON the warp tile it presses NOTHING, the held-SOUTH warp
        # never fires, and the assert below would blame the warp. §Ch21's leg-5 PART C measured an
        # arrival of exactly (9,8) on this map, so this is a real arrival, not arithmetic.
        if _here_tile() == UW_EXIT_WARP:
            yield from _bounded_step("Up", expect=(UW_EXIT_WARP[0], UW_EXIT_WARP[1] - 1),
                                     map_enum=UWS)
        # ⛔ `run=False` IS A SAFETY ARGUMENT, NOT A STYLE CHOICE — §Ch21's homologous call says so
        # in those words. It is *currently* redundant because `follow_waypoints` independently
        # suppresses B-holding while the Underwater avatar flag is set, but that is an UNSTATED
        # dependency on someone else's implementation detail. State it here rather than inherit it.
        yield from navigate_to(UWS, UW_EXIT_WARP, run=False)
        yield from wait_until_truly_controllable()
        if not _on_map(UW126):
            raise BotModeError(
                f"Ch23 leg 3: navigated to the {UW_EXIT_WARP} arrow warp on "
                f"UNDERWATER_SOOTOPOLIS_CITY and did not arrive on UNDERWATER_ROUTE126 — "
                f"now at {_where()}."
            )
        _take(report, "R-UWWARP")

    # ---- phase 4: emerge ------------------------------------------------------------------------
    if _on_map(UW126):
        rest = _here_tile()
        report["uw126_rest"] = rest
        # ⛔ READ AND BRANCH — trap 3. §Ch21 measured the resting tile as (45,66), already the safe
        # emerge tile; the older spec sentence "step south to (45,66)" would land on (45,67).
        if rest != EMERGE_TILE:
            if rest != UW126_ARRIVAL_PREDICTION:
                raise BotModeError(
                    f"Ch23 leg 3: rested on {rest} after the arrow warp — neither the measured "
                    f"{EMERGE_TILE} nor the warp target {UW126_ARRIVAL_PREDICTION}. Refusing to "
                    f"guess a direction from here."
                )
            direction = "Up" if _fault("BADSTEP") else "Down"
            yield from _bounded_step(direction, expect=EMERGE_TILE, map_enum=UW126)

        tile_type = _tile_type_here()
        report["emerge_tile"] = _here_tile()
        report["emerge_tile_type"] = tile_type
        _take(report, "R-EMERGETILE")
        # ⛔ DENYLIST, NOT ALLOWLIST — this string has never been read on this tile.
        if tile_type in EMERGE_REFUSED_TILE_TYPES:
            raise BotModeError(
                f"Ch23 leg 3: refusing to surface from {_here_tile()} — tile_type is "
                f"{tile_type!r}, which is in the named-bad set {EMERGE_REFUSED_TILE_TYPES}."
            )

        yield from _budgeted(surface_from_dive(), DIVE_TASK_BUDGET, "surface onto ROUTE126")
        yield from wait_until_truly_controllable()
        if not _on_map(R126):
            raise BotModeError(
                f"Ch23 leg 3: surfaced from {report['emerge_tile']} "
                f"(tile_type={report['emerge_tile_type']!r}) and did not arrive on ROUTE126 — "
                f"now at {_where()}."
            )
        report["surface_tile"] = _here_tile()
        _take(report, "R-SURFACE")

    if not crater_left():
        raise BotModeError(
            f"Ch23 leg 3: finished without reaching ROUTE126 — now at {_where()}. This is the "
            f"un-owned-strand case: the phase selector matched no known map."
        )

    # ---- can the bot CONTINUE? A leg that lands stranded has not succeeded. ---------------------
    from modules.map_path import calculate_path

    try:
        # ⭐ (79,45) is MEASURED-PROD, not a guess: `ch23route` R9f asked production for
        # ROUTE126 (45,66) -> (79,45) and got **55 waypoints**, and this leg reproduced exactly 55
        # on its first drive. It is the east-edge seam toward ROUTE127, i.e. the tile leg 4 needs.
        path = calculate_path((R126, _here_tile()), (R126, R126_EAST_PROBE))
        report["continue_wp"] = len(path)
    except Exception as error:  # noqa: BLE001 - a refusal IS the reading
        report["continue_wp"] = f"{type(error).__name__}: {str(error)[:120]}"
    _take(report, "R-CONTINUE")


# --------------------------------------------------------------------------------------------
# ORCHESTRATOR
# --------------------------------------------------------------------------------------------
def depart_sootopolis(report=None, *, attempts: int = 3) -> Generator:
    """LEGS 2 + 3, bounded.

    ⛔ NOT named `do_victory_road_chapter`. A name claiming eight legs that delivers two is exactly
    the rot this project keeps paying for — a later reader wires it into `_play()` and the chapter
    silently ends in the ocean.

    ⛔⛔ READINGS ACCUMULATE ACROSS ATTEMPTS; THEY ARE NEVER RESET.
    An adversarial review found that archiving-and-resetting the readings per attempt makes a
    **perfect single-attempt run FAIL** — the preflight reading lands in `previous_attempts` and the
    grade cannot see it. Only the per-attempt COUNTERS are archived. This mirrors §Ch22, which grades
    its ice total by SUMMING across attempts precisely because *"grading the last attempt's figure
    would FAIL a healthy run"*.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    report.setdefault("trace", [])
    report.setdefault("crater_exits", 0)
    report.setdefault("attempts_used", 0)
    # ⛔ Every graded key gets a sentinel HERE, because leg 2 is the only writer of most of them and
    # it SELF-SKIPS whenever `departure_ready()` is true — the whiteout-resume case. Without these,
    # the driver's acceptance block raises `KeyError` after the run, with no verdict line printed.
    for key in ("respawn_before", "respawn_after", "identities_after", "hp_after",
                "poisoned_before", "poisoned_after", "carriers_after", "uw_arrival",
                "uw126_rest", "emerge_tile", "emerge_tile_type", "surface_tile",
                "dive_tile_type", "continue_wp", "pin", "leg3_entry"):
        report.setdefault(key, None)
    report.setdefault("pc_map_seen", False)

    assert_ch23_preflight(report)

    last_error = None
    for attempt in range(1, attempts + 1):
        report["attempts_used"] = attempt
        try:
            _check_abort()
            # ⛔ LEG 2 RUNS ONLY IF THE BOT IS ACTUALLY ON THE ISLAND SIDE. It is NOT an error to
            # be elsewhere — leg 3 owns every other map, and its phase selector ends in a NAMED
            # strand raise if it recognises none of them.
            # ‼ AN EARLIER VERSION RAISED "neither the island side nor ROUTE126" HERE, and that was
            # a real bug I caught by tracing the resume matrix rather than by running it: a wild
            # battle UNDERWATER chips the party, so `departure_ready()` goes False; the bot is on
            # UNDERWATER_SOOTOPOLIS_CITY, which is not the island side; and the run would then die
            # with a message about leg 2 while leg 3 was half-finished and perfectly resumable.
            # ⇒ a precondition for leg 2 must not be able to fail leg 3.
            if not crater_left() and not departure_ready() and any(
                _on_map(m) for m in _ISLAND_SIDE_MAPS
            ):
                yield from prepare_to_depart(report)
            yield from leave_the_crater(report)
            if crater_left():
                report["failure"] = None
                return
        except StoryAbort:
            raise
        except BotModeError as error:
            # ⛔ THIS HANDLER SWALLOWS ON PURPOSE, AND HERE IS WHY IT IS SAFE TO — the four
            # properties that make a retry legitimate rather than a silent derail:
            #   1. ABORTS ARE NOT SWALLOWED. `StoryAbort` is re-raised by the clause above, and
            #      `reraise_if_aborting` re-raises any abort wearing a `BotModeError` costume.
            #   2. THE ERROR IS KEPT, NOT DISCARDED — appended to `report["attempt_errors"]`, which
            #      the driver prints line by line, and surfaced live via `context.message`.
            #   3. THE LOOP IS BOUNDED (`attempts=3`) and its exhaustion RAISES, naming the last
            #      error, so "we retried and gave up" can never be mistaken for "we succeeded".
            #   4. EVERY LEG IS IDEMPOTENT and self-skips on state the game holds, so a retry
            #      resumes rather than redoing work.
            # ‼ Without all four this would be the `#26-manualderails` shape: 44 of 50 runs ended in
            # a Manual hand-off whose budget was exhausted rather than whose situation was hopeless.
            reraise_if_aborting(error)
            last_error = f"attempt {attempt}: {type(error).__name__}: {error}"
            report.setdefault("attempt_errors", []).append(last_error)
            context.message = f"Ch23 {last_error}"
            yield from wait_until_truly_controllable()

    report["failure"] = last_error or "exhausted attempts without reaching ROUTE126"
    raise BotModeError(f"Ch23: legs 2-3 failed after {attempts} attempts. Last: {last_error}")


# --------------------------------------------------------------------------------------------
# LEG 4 — CROSS THE OCEAN TO EVER GRANDE AND CLIMB THE WATERFALL
# --------------------------------------------------------------------------------------------
def _sampling(gen: Generator, report: dict) -> Generator:
    """Run a navigation generator while SAMPLING the map every frame.

    ⛔⛔ TWO REASONS THIS WRAPPER EXISTS, AND NEITHER IS COSMETIC.
    1. **THE PRESENCE WITNESS CANNOT BE COLLECTED ANY OTHER WAY.** `yield from navigate_to(...)`
       gives the leg no frames of its own, so it can never observe that ROUTE127 and ROUTE128 were
       actually crossed. Without that, a run that never left ROUTE126 could satisfy a
       position-plus-path grade — the house rule is *a presence conjunct before every absence one*.
    2. ⛔ **`navigate_to` NEVER CALLS `_check_abort()`**, so a `StoryAbort` latched by a whiteout is
       unobserved for the whole crossing. This is where the latch gets read.
    """
    for _ in gen:
        _check_abort()
        where = _where()
        if not isinstance(where, str):
            report.setdefault("maps_seen", set()).add(where[0])
        yield


def at_ever_grande_top() -> bool:
    """Leg 4's completion predicate — ⛔ a POSITIVE whitelist, never `not _on_map(R126)`."""
    return _on_map(EG) and _here_tile()[1] <= EG_LANDING[1]


def cross_to_ever_grande(report=None) -> Generator:
    """LEG 4 — ROUTE126 → 127 → 128 → Ever Grande, climb the waterfall, heal, reach the VR apron.

    ⛔⛔ WHY `_navigate_riding_out` AND NOT A RAW `navigate_to`. A trainer's sight line ABORTS a raw
    `navigate_to`: the intro msgbox runs while the game state is still OVERWORLD, so the waypoint
    countdown keeps ticking and `walking.py:479-485` raises `BotModeError`. **This crossing is
    GUARANTEED to hit two** — Carlee (101,29) and Harrison (101,22) patrol the only channel through
    Route 128's basin A, and an enumeration of all 48 configurations × 8 rows found **no safe row**.
    ⛔ And NEVER pass `expecting_script=True` to dodge it: that path `return`s, silently ending the
    crossing mid-ocean and reporting success.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    if at_ever_grande_top():
        report["leg4_entry"] = "already above the falls"
        return

    # ---- phase 0: a whiteout respawns INSIDE THE CRATER, where this leg cannot plan at all ------
    # ⛔ `SOOTOPOLIS_CITY` has zero map connections, so a crossing planned from there raises
    # `PathFindingError` on every attempt and reports "could not reach (18,68)" — the WRONG
    # diagnosis for "we are behind the dive". Leg 3 is idempotent and self-skips, so calling it is
    # free when we are already out.
    if any(_on_map(m) for m in (CITY, PC_1F, PC_2F, UWS, UW126)):
        report["leg4_entry"] = f"behind the dive on {_where()[0]} — re-running leg 3"
        yield from leave_the_crater(report)
        yield from wait_until_truly_controllable()
    report.setdefault("leg4_entry", "ROUTE126" if _on_map(R126) else str(_where()))

    # ---- phase 1: put the STRONGEST battler in slot 0 before the forced fights ------------------
    # ⛔⛔ THE STORY OVERRIDE'S FAINT-REPLACEMENT RANKING IS `(incoming, -outgoing, -hp_fraction,
    # -level)` (`story_mode.py:210`) and its only filter is `current_hp > 0` (`:185`) — it drops the
    # parent's `pokemon_can_battle` and ranks HP **FRACTION above LEVEL**. ⇒ once the type terms tie,
    # an untouched 100% L19 HM mule outranks a chipped L44.
    # ‼ VERIFIED FOR THIS PARTY against Water STAB: Sceptile (Grass) is picked first — incoming 0.5,
    # outgoing 2.0 — and Wailmer second. **The Zigzagoon only leads if BOTH are out**, which is
    # narrower than the review claimed but still reachable after a 273-tile crossing where every
    # tile rolls an encounter. Leading the strongest is cheap insurance either way.
    if not _fault("NOLEAD"):
        try:
            from modules.story.early_game import _lead_strongest_battler

            yield from _lead_strongest_battler()
        except Exception as error:  # noqa: BLE001 - a refusal IS the reading, and this is optional
            # ⛔⛔ THE ABORT LATCH IS RE-RAISED FIRST, AND THAT ORDER IS NOT OPTIONAL.
            # `_lead_strongest_battler` walks and opens menus, so a whiteout inside it latches
            # `StoryAbort` — and a bare `except Exception` would SWALLOW it and carry on crossing an
            # ocean on a run the harness has already given up on. The abort-swallowing ratchet
            # caught this within minutes of the commit (24 > 23, gate #27); it is a real defect, not
            # a ratchet nit. ‼ "Deliberately non-fatal" must never mean "deliberately deaf".
            reraise_if_aborting(error)
            # ⛔ DELIBERATELY NON-FATAL *for ordinary failures*: leading the strongest is INSURANCE,
            # not a precondition. The crossing is winnable without it, and refusing to depart
            # because a nicety failed would trade a small risk for a certain stop.
            report["lead_error"] = f"{type(error).__name__}: {error}"
    report["lead_after"] = next(iter(party_identities()), None)
    _take(report, "R4-LEAD")

    # ---- phase 2: stage the crossing at the channel mouth ---------------------------------------
    # ⛔ TWO REASONS TO STAGE RATHER THAN ASK FOR THE WHOLE 273 WAYPOINTS IN ONE CALL:
    #   (a) `_navigate_riding_out`'s fail-fast assumes "nothing can differ between attempts", which
    #       is false against a WALKING NPC — its effective tries collapse from 10 to ~2 in the
    #       channel; and
    #   (b) `navigate_to`'s no-progress window holds SIX positions against an EIGHT-tile channel, so
    #       it can keep resetting the window while making no real progress.
    # ⇒ get to the channel mouth first, then cross, so a failure names WHICH half failed.
    # ⚠ `avoid_encounters=False` on the ocean: it adds +1000 per WATER tile, which on an all-water
    # crossing avoids nothing and only inflates the search.
    if not _on_map(EG):
        yield from _sampling(
            _navigate_riding_out(R128, CHANNEL_STAGE, avoid_encounters=False), report)
        if not _at(R128, CHANNEL_STAGE):
            raise BotModeError(
                f"Ch23 leg 4: aimed at the ROUTE128 channel mouth {CHANNEL_STAGE} and ended on "
                f"{_where()}. maps_seen={sorted(report.get('maps_seen', ()))}"
            )
        _take(report, "R4-STAGE")

        # ---- phase 3: through the channel and across the seam into Ever Grande -----------------
        yield from _sampling(
            _navigate_riding_out(EG, WATERFALL_BASE, avoid_encounters=False), report)

    if not _at(EG, WATERFALL_BASE):
        raise BotModeError(
            f"Ch23 leg 4: aimed at the waterfall base {WATERFALL_BASE} and ended on {_where()}."
        )
    report["base_tile_type"] = _tile_type_here()
    _take(report, "R4-BASE")

    # ---- phase 4: the climb — HAND-ROLLED ON PURPOSE -------------------------------------------
    # ⛔⛔ DO NOT ASK `navigate_to` FOR THE TOP. `follow_waypoints`' waterfall branch computes its
    # timeout from the MAP NUMBER instead of the player's y (`walking.py:226-227`): for
    # EVER_GRANDE_CITY that is `195 + (8-59)*42 = -1947`, a NEGATIVE budget that trips on frame 1
    # and burns eight no-progress re-paths into `NavigationStuckError`. Upstream-origin and never
    # exercised — filed rather than patched (see KI-83's ruling on upstream-identical files).
    # ✅ MEASURED SAFE: `ch23route` R11a dumped the 273-wp crossing plan — its only actions are four
    # `WaypointAction.Surf`, **no `Waterfall` waypoint at all** — so aiming at the BASE never enters
    # that branch. The climb below is what the planner deliberately does not do.
    if not _fault("NOCLIMB"):
        from modules.modes.util.tasks_scripts import wait_for_task_to_start_and_finish
        from modules.modes.util.walking import ensure_facing_direction

        yield from ensure_facing_direction("Up")
        yield from _budgeted(
            wait_for_task_to_start_and_finish("Task_UseWaterfall", "A"),
            CLIMB_BUDGET, "climb the Ever Grande waterfall")
        yield from wait_until_truly_controllable()

    here = _here_tile()
    if not _on_map(EG) or here[1] > WATERFALL_TOP[1]:
        raise BotModeError(
            f"Ch23 leg 4: the waterfall climb did not lift the avatar — now at {_where()}, "
            f"expected to be at or above y={WATERFALL_TOP[1]}. Climbing needs BADGE08, the SURFING "
            f"state and a NORTH facing; descending is un-gated, so a failure here reads as 'stayed "
            f"at the bottom', never as 'fell'."
        )
    report["climb_end"] = here
    _take(report, "R4-CLIMB")

    # ---- phase 5: step off the water onto land --------------------------------------------------
    yield from _sampling(_navigate_riding_out(EG, EG_LANDING), report)
    if not _at(EG, EG_LANDING):
        raise BotModeError(f"Ch23 leg 4: aimed at the landing {EG_LANDING}, ended on {_where()}.")
    _take(report, "R4-LAND")

    # ---- phase 6: heal, and RE-ARM THE RESPAWN ABOVE THE FALLS ----------------------------------
    # ⛔⛔ THIS IS LOAD-BEARING, NOT HOUSEKEEPING. Until the bot walks into the Ever Grande Poké
    # Center, `lastHealLocation` is still SOOTOPOLIS — so any whiteout inside Victory Road drops it
    # back **inside the crater, below the falls**, forcing a full re-run of legs 3 AND 4.
    # ⭐ It is also the mitigation for the faint-replacement ranking above: healing resets every
    # `hp_fraction` to 1.0, so the ranking cannot prefer a fresh low-level mule over a chipped
    # veteran on the next fight.
    if not _fault("NOHEAL4"):
        yield from _budgeted(
            heal_in_pokemon_center(PokemonCenter.EvergrandeCity), HEAL_BUDGET,
            "heal at Ever Grande")
        yield from wait_until_truly_controllable()
        assert_carriers_survived("the Ever Grande heal")
    report["hp_after4"] = {k: v[0] for k, v in party_identities().items()}
    _take(report, "R4-HEAL4")

    report["respawn_after4"] = respawn_reading()
    if not respawn_is_armed(EG):
        raise BotModeError(
            f"Ch23 leg 4: the whiteout respawn is still not armed to EVER_GRANDE "
            f"(reads {report['respawn_after4']!r}, want {EG.value}). Refusing to hand leg 5 a run "
            f"whose whiteout lands BELOW the waterfall, inside the crater."
        )
    _take(report, "R4-ARM4")

    # ---- phase 7: park on the Victory Road APRON, never on the door ------------------------------
    yield from _sampling(_navigate_riding_out(EG, VR_APRON), report)
    if not _at(EG, VR_APRON):
        raise BotModeError(f"Ch23 leg 4: aimed at the VR apron {VR_APRON}, ended on {_where()}.")
    _take(report, "R4-APRON")

    # ---- can the bot CONTINUE? ⛔ off the END tile, and it must be NON-ZERO ---------------------
    from modules.map_path import calculate_path

    try:
        path = calculate_path((EG, _here_tile()), (EG, EG_PC_APRON))
        report["continue_wp4"] = len(path)
    except Exception as error:  # noqa: BLE001 - a refusal IS the reading
        report["continue_wp4"] = f"{type(error).__name__}: {str(error)[:120]}"
    _take(report, "R4-CONTINUE4")


# --------------------------------------------------------------------------------------------
# LEG 5 — ENTER VICTORY ROAD 1F, BEAT WALLY, REACH THE B1F LADDER
# --------------------------------------------------------------------------------------------
def wally_beaten() -> bool:
    """The chapter's GRADING FLAG. ⛔ Read the flag, never "we walked past his tile".

    ‼ The name is verified to resolve: `DEFEATED_WALLY_VICTORY_ROAD` is flag **126** in
    `modules/data/event_flags/emerald.txt`, and `chapters.py:281` already grades §Ch23 on it.
    That check matters because `get_event_flag` returns **False for any unknown name** — a typo
    would produce a guard that can never be True and would fail a perfect run forever.
    """
    return bool(_flag("DEFEATED_WALLY_VICTORY_ROAD"))


def at_b1f_doorstep() -> bool:
    """Leg 5's completion predicate — ⛔ a POSITIVE whitelist on the APRON, never the ladder."""
    return _on_map(VR1F) and _at(VR1F, B1F_LADDER_APRON)


def enter_victory_road(report=None) -> Generator:
    """LEG 5 — warp into Victory Road 1F, fight through to Wally, and park at the B1F ladder.

    ⛔ 1F NEEDS NO FIELD MOVES AND CANNOT BE BRICKED: it has ZERO pushable boulders and ZERO
    breakable rocks, and `requires_flash: false`. The boulder-seal hazard is a **B1F** property and
    belongs to leg 6. Nothing this leg does can make the floor unwinnable.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    if at_b1f_doorstep():
        report["leg5_entry"] = "already at the B1F doorstep"
        return

    # ---- phase 1: through the Victory Road door ------------------------------------------------
    # ⛔ `_walk_through_warp` and NOT `navigate_to(VR1F, ...)`: leg 4 deliberately parks on the
    # APRON (18,42) precisely so that taking the warp is leg 5's explicit act rather than a side
    # effect of a path whose last waypoint happens to be a door.
    if _on_map(EG):
        report["leg5_entry"] = "EVER_GRANDE apron"
        if not _at(EG, VR_APRON):
            yield from _sampling(_navigate_riding_out(EG, VR_APRON), report)
        yield from _walk_through_warp("Up", EG.value)
        yield from wait_until_truly_controllable()
        if not _on_map(VR1F):
            raise BotModeError(
                f"Ch23 leg 5: stepped NORTH off the Ever Grande apron {VR_APRON} and did not arrive "
                f"on VICTORY_ROAD_1F — now at {_where()}."
            )
        report["vr_arrival"] = _here_tile()
        # ⛔ DIAGNOSTIC ADDED AFTER DRIVE 1 FAILED WITH `battles=0` AND THE FLAG CLEAR.
        # Neither Hope's sight line nor Wally's coord event fired, and BOTH are elevation-gated in
        # the same way: a land trainer cannot see a SURFING player (the elevation mismatch is checked
        # before the object-event case), and a coord event only matches when
        # `coordEvent.elevation == playerElevation`. ⇒ one shared cause explains both, so measure the
        # avatar's state at arrival rather than guessing which of the two mechanics broke.
        # ⛔ `is_in_water`, NOT `is_surfing` — the latter does not exist and my first diagnostic
        # died on it. Reading an attribute I had not verified is the same class of error as the
        # `pathlib`/`_pathlib` trap: **check the name against the class before using it.**
        av = get_player_avatar()
        report["avatar_flags"] = str(av.flags)          # MEASURED drive 2: 33 = OnFoot|Controllable
        report["on_foot"] = not av.is_in_water          # ⇒ the "still surfing" theory is REFUTED
        # ⇒ so the cause is upstream of the avatar: is the coord event even ARMED, and does the
        # player's elevation match the event's? Both are read, never assumed.
        from modules.map import get_map_data_for_current_position

        # ⭐ `GAME_STAT_STEPS` IS THE PERFECT PROXY FOR "DID THE COORD-EVENT GATE OPEN".
        # `field_control_avatar.c:157` increments it INSIDE the same `if (input->tookStep)`
        # block, TWO LINES above the `TryStartStepBasedScript` call that runs coord events —
        # and nothing else in the game increments it. ⇒ a step-count DELTA of 29 across a
        # 29-waypoint walk proves the gate opened on every step, including the last one.
        from modules.game_stats import GameStat, get_game_stat

        report["steps_at_arrival"] = get_game_stat(GameStat.STEPS)
        report["vr1f_state"] = _var("VICTORY_ROAD_1F_STATE")
        try:
            report["arrival_elevation"] = getattr(
                get_map_data_for_current_position(), "elevation", None)
        except Exception as error:  # noqa: BLE001 - a refusal IS the reading
            report["arrival_elevation"] = f"{type(error).__name__}: {error}"
        _take(report, "R5-WARP")
    report.setdefault("leg5_entry", str(_where()))

    # ---- phase 1b: PUT THE STRONGEST BATTLER IN FRONT — measured necessary, not insurance -------
    # ⛔⛔ LEG 5 ORIGINALLY SKIPPED THIS AND TOOK **2 WHITEOUTS IN ONE DRIVE.**
    # The story override's faint-replacement ranking is `(incoming, -outgoing, -hp_fraction,
    # -level)` (`story_mode.py:210`), i.e. HP **fraction** outranks LEVEL. On the OCEAN that was
    # nearly harmless — Sceptile resists Water and carries a super-effective move, so it wins the
    # first two key terms outright, which is why I recorded the risk as NARROW.
    # ‼ **THAT NARROWING WAS TRUE OF WATER FOES AND FALSE HERE.** Victory Road's wilds are Golbat /
    # Hariyama / Lairon / Loudred at L36-40: nothing in this party resists them and nothing carries a
    # super-effective move, so `incoming` and `outgoing` TIE ACROSS THE WHOLE PARTY and the tiebreak
    # falls to `hp_fraction` — handing the lead to the freshest mon, which is the **L19 Zigzagoon**.
    # It is then one-shot by a L40, and `battle_items.py` declines to heal a mon that never gets an
    # intermediate turn. ⇒ measured: 5 battles, 2 whiteouts.
    # ⇒ **an environment-specific computation does not generalise to a different environment.**
    if not _fault("NOLEAD5"):
        try:
            from modules.story.early_game import _lead_strongest_battler

            yield from _lead_strongest_battler()
        except Exception as error:  # noqa: BLE001 - a refusal IS the reading
            reraise_if_aborting(error)   # ⛔ non-fatal must never mean deaf to an abort
            report["lead5_error"] = f"{type(error).__name__}: {error}"
    report["lead5_after"] = next(iter(party_identities()), None)

    # ---- phase 2: walk to Wally's trigger ------------------------------------------------------
    # ‼ Two sight battles are UNAVOIDABLE on this floor and both are expected, not faults: **Hope**
    # (6,15) on the way in — (9,14) is provably unreachable without entering her cone — and Edgar
    # (33,22) on the way OUT, which belongs to leg 7. A battle here is NORMAL.
    if not wally_beaten():
        yield from _sampling(_navigate_riding_out(VR1F, WALLY_TRIGGER), report)
        yield from wait_until_truly_controllable()
        report["after_wally_tile"] = _here_tile()
        # ⛔⛔ MEASURE AT THE TRIGGER, NOT AT ARRIVAL — my first diagnostic read the elevation on the
        # ENTRANCE tile (15,40) and answered a question I had not asked. Wally's coord events are
        # declared **elevation 4**, and `GetCoordEventScriptAtPosition` fires only when
        # `coordEvent.elevation == playerElevation || == 0`. So the load-bearing number is the
        # elevation the avatar carries **standing on (3,23)** — read it here, where it decides.
        from modules.map import get_map_data_for_current_position

        _md = get_map_data_for_current_position()
        report["trigger_elevation"] = getattr(_md, "elevation", None)
        report["trigger_tile_type"] = getattr(_md, "tile_type", None)
        from modules.game_stats import GameStat, get_game_stat
        from modules.map import get_map_objects

        report["steps_at_trigger"] = get_game_stat(GameStat.STEPS)
        # ⛔⛔ THE VALUE THAT ACTUALLY DECIDES, AND I HAD NEVER READ IT.
        # `GetCoordEventScriptAtPosition` compares the event's elevation against
        # `PlayerGetElevation()` = `gObjectEvents[player].previousElevation` — NOT the tile's
        # grid elevation. What I measured earlier as "elevation 4" was `MapLocation.elevation`,
        # a DIFFERENT NUMBER that merely happens to agree. ‼ Measuring a value adjacent to the
        # load-bearing one and calling the question settled is the same class of error as
        # reading `tail`'s exit code for the gate suite's.
        # ⚠ R-CAMWINDOW REVIEWED AND INAPPLICABLE HERE: `get_map_objects()` is a CAMERA-RANGE
        # window, so an object outside ~7-9 tiles is absent WHETHER OR NOT IT EXISTS — three
        # paid instances in this tree. ✅ The object being read is **the PLAYER**, which is by
        # definition at the centre of that window and can never be culled. ⛔ Do not copy this
        # pattern to read an NPC from across the map.
        try:
            _po = next((o for o in get_map_objects() if o.local_id == 255 or o.is_player),
                       None)
            report["prev_elevation_at_trigger"] = getattr(_po, "previous_elevation", None)
        except Exception as error:  # noqa: BLE001 - a refusal IS the reading
            report["prev_elevation_at_trigger"] = f"{type(error).__name__}: {error}"
        report["vr1f_state_at_trigger"] = _var("VICTORY_ROAD_1F_STATE")

        # ---- ⭐⭐ THE RE-ENTRY IS *REQUIRED*, AND AN ACCIDENTAL A/B PROVED IT ------------------
        # ⛔ I DELETED THIS ONCE, ON AN INFERENCE, AND THE NEXT DRIVE REFUTED ME. The reasoning was:
        # `GAME_STAT_STEPS` is incremented inside the same `if (input->tookStep)` block that runs
        # coord events, so a delta of 29 across a 29-waypoint walk "proves" the gate opened on the
        # arrival step and a re-entry cannot matter. ‼ **THE DIRECT COMPARISON SAYS OTHERWISE:**
        #     with this block    -> battles=5, whiteouts=2, `WallyEntranceBattle` RUNS
        #     without this block -> battles=0, whiteouts=0, nothing fires
        #     (steps_delta = 29 in BOTH — so the proxy cannot tell them apart)
        # ⇒ **A PROXY THAT SAYS "THIS SHOULD NOT BE NECESSARY" DOES NOT OUTRANK AN A/B SHOWING THAT
        # IT IS.** The step counter measures that a step COMPLETED, not that the coord-event lookup
        # ran with the arrival position on that frame — those are different claims, and I treated the
        # cheap one as settling the expensive one.
        # ⇒ walking between the two trigger tiles is what actually arms the battle. Both (2,23) and
        # (3,23) carry the same event, so either arrival re-enters it.
        # ‼ BOUNDED AT 2 AND IT FALLS THROUGH TO A NAMED RAISE — a re-entry that never works must
        # fail loudly rather than spin, and this loop is why a failing run shows battles at all.
        for attempt in range(1, 3):
            if wally_beaten():
                break
            report["retrigger_attempts"] = attempt
            target = WALLY_TRIGGER_WEST if _here_tile() != WALLY_TRIGGER_WEST else WALLY_TRIGGER
            try:
                yield from _navigate_riding_out(VR1F, target)
            except BotModeError as error:
                # ⛔ Aborts are re-raised FIRST — "non-fatal" must never mean "deaf" (the ratchet
                # caught exactly this shape in leg 4). The rest is recorded, not swallowed: a failed
                # re-entry attempt is a READING that the next attempt and the final raise both use.
                reraise_if_aborting(error)
                report.setdefault("retrigger_errors", []).append(f"{type(error).__name__}: {error}")
            yield from wait_until_truly_controllable()
        report["retrigger_end_tile"] = _here_tile()
        _take(report, "R5-WALLY")

    # ---- phase 3: the grading flag, read from the WORLD -----------------------------------------
    if not wally_beaten():
        # ⛔⛔ THIS MESSAGE ONCE ASSERTED WHAT THE FAILURE *WASN'T*, AND COST SIX DIAGNOSTIC DRIVES.
        # It read: "a clear flag here means the trigger was never stepped on — NOT that the battle
        # was lost (a loss whites out instead)." Every clause is wrong in the case that actually
        # happened: the coord event fired, `WallyEntranceBattle` ran, and the bot LOST — twice, with
        # `BattleScript_LocalBattleLostEnd` and two whiteouts printed in the SAME log I was reading.
        # ‼ **A DIAGNOSTIC THAT RULES A CAUSE OUT IS A CLAIM, AND A WRONG ONE SENDS THE READER AWAY
        # FROM THE ANSWER.** State what was OBSERVED; let the reader weigh it.
        _delta = (report.get("steps_at_trigger") or 0) - (report.get("steps_at_arrival") or 0)
        raise BotModeError(
            f"Ch23 leg 5: standing on {_here_tile()} but `DEFEATED_WALLY_VICTORY_ROAD` is CLEAR. "
            f"⇒ READ THE DRIVER'S `whiteouts` AND `battles` LINES BEFORE CONCLUDING ANYTHING: the "
            f"flag is set only at the END of `WallyEntranceBattle`, so it stays clear whether the "
            f"trigger never fired OR the battle fired and was LOST. Those two look IDENTICAL from "
            f"here. Diagnostics on hand: "
            f"var={_var('VICTORY_ROAD_1F_STATE')} (0 = armed); "
            f"steps_delta={_delta} (steps COMPLETED; ⚠ this does NOT prove the coord-event "
            f"lookup ran with the arrival position — an A/B measured battles=5 WITH the re-entry walk and battles=0 WITHOUT it at this SAME delta, so the counter cannot tell those "
            f"two apart); "
            f"prev_elevation={report.get('prev_elevation_at_trigger')} (must equal the event's 4). "
            f"If all three are good, the trigger fired and the BATTLE WAS LOST."
        )
    _take(report, "R5-FLAG")

    # ---- phase 4: park on the LADDER APRON, never on the ladder ---------------------------------
    yield from _sampling(_navigate_riding_out(VR1F, B1F_LADDER_APRON), report)
    if not _at(VR1F, B1F_LADDER_APRON):
        raise BotModeError(
            f"Ch23 leg 5: aimed at the B1F ladder apron {B1F_LADDER_APRON} and ended on "
            f"{_where()}. ⛔ Never retry this by aiming at the ladder {B1F_LADDER} itself — that is "
            f"a WARP, and the plan's last waypoint becomes B1F (8,3)."
        )
    _take(report, "R5-LADDER")

    # ---- can the bot CONTINUE? ⛔ off the END tile, NON-ZERO ------------------------------------
    # ⚠ The target is the ladder itself: leg 6's first act is to step onto it, so "can I still reach
    # the warp from where I stopped?" is exactly the question that matters — and it is 1 wp, which
    # is non-zero, so the check cannot be satisfied by standing on the answer.
    from modules.map_path import calculate_path

    try:
        path = calculate_path((VR1F, _here_tile()), (VR1F, B1F_LADDER))
        report["continue_wp5"] = len(path)
    except Exception as error:  # noqa: BLE001 - a refusal IS the reading
        report["continue_wp5"] = f"{type(error).__name__}: {str(error)[:120]}"
    _take(report, "R5-CONTINUE5")


# --------------------------------------------------------------------------------------------
# TRAINING — raise the battlers before Wally
# --------------------------------------------------------------------------------------------
def battler_identities() -> dict:
    """`{(pid, species): (slot, level)}` for the mons this arc actually fights with.

    ⛔ Returns IDENTITIES with their CURRENT slot, never a bare slot list: `train_team` physically
    rotates the party (`_rotate_lead_safely`), so a slot index resolved before a call is not the
    same mon afterwards. Resolve immediately before use, and re-verify by PID after.
    """
    out = {}
    for slot, mon in enumerate(get_party()):
        if mon is None or mon.is_egg:
            continue
        if mon.species.name in BENCH_SPECIES:
            continue
        out[(mon.personality_value, mon.species.name)] = (slot, mon.level)
    return out


def team_is_ready(target: int = None) -> tuple[bool, list]:
    """Is the party ready for Wally and the Elite Four? Returns `(ready, reasons)`.

    ⛔ ASSERTS ON SPECIES + MOVE IDENTITY, NEVER ON SLOT INDEX — benching reshuffles every slot, and
    a slot-index assert would happily read TRUE against the wrong Pokémon.
    ‼ The level is not the only gate: **Mightyena below L47 has no Crunch and therefore no answer to
    Phoebe's all-Ghost team**, so a party that is "all L50" but reached it without that level-up is
    still not ready. A readiness check that only counts levels would pass it.
    """
    # ⛔⛔ THE TARGET IS A PARAMETER, NOT A CONSTANT — FIXED 2026-09-04.
    # It used to read `TRAIN_TARGET` directly while `train_for_victory_road` accepted a `target`
    # argument, so a caller asking for a HIGHER target was checked against 47 anyway: the readiness
    # gate returned "already ready", the leg returned early, and **no estimate was ever produced**.
    # ‼ MEASURED: `POKEBOT_CH23_TRAIN_TARGET=53` printed `PRE reasons=[]` and
    # `train_estimate_total = None` — a flag that silently did nothing, which is the same defect
    # shape as the six dead fault arms (#34's gate exists for that class).
    # ⇒ **A PARAMETER THAT ONLY REACHES HALF THE FUNCTION IS NOT A PARAMETER.**
    target = TRAIN_TARGET if target is None else target
    reasons = []
    for (pid, species), (_slot, level) in battler_identities().items():
        if level < target:
            reasons.append(f"{species}#{pid:08X} is L{level} < {target}")
    for mon in get_party():
        if mon is None or mon.species.name != "Mightyena":
            continue
        moves = [l.move.name for l in mon.moves if l is not None]
        # ⛔⛔ ASSERT THE MOVE, NEVER THE LEVEL THAT USUALLY GRANTS IT. The first version of this
        # check read `if "Crunch" not in moves AND mon.level < CRUNCH_LEVEL` — so at exactly L47 it
        # stopped asking, and a Mightyena that reached 47 with FULL MOVE SLOTS and declined the
        # learn would have graded READY while carrying no Dark move at all. The level is a PROXY;
        # the move is the requirement. ‼ (It passed honestly on 2026-09-04 — the log shows
        # "MIGHTYENA learned CRUNCH!" — but it would have passed either way, which is the defect.)
        if "Crunch" not in moves:
            if mon.level < CRUNCH_LEVEL:
                reasons.append(
                    f"Mightyena L{mon.level} has no Crunch (learns it at L{CRUNCH_LEVEL})")
            else:
                reasons.append(
                    f"⛔ Mightyena is L{mon.level} ≥ {CRUNCH_LEVEL} but does NOT know Crunch — the "
                    f"level-up learn was missed or declined, and there is NO Dark TM in Emerald to "
                    f"recover with. Moves: {moves}."
                )
    return (not reasons), reasons


def training_continue_reading(report) -> None:
    """⛔⛔ LIVENESS: "the team is ready" is NOT "the bot can continue" — prove a REAL path out.

    ‼ WHY THIS IS NOT DECORATION. §Ch15 ended four floors underground, §Ch18 on an eleven-tile
    island and §Ch19 in a living room, and **all three PASSED their own acceptance tests**, because
    every one of those tests graded the goal and never asked whether the bot could leave. A grind
    ends wherever the last heal left it, so this leg is squarely in that family.

    ⛔ THE TARGET IS DERIVED FROM THE MAP THE RUN ACTUALLY ENDED ON, never hardcoded — and when the
    bot is already standing on the natural target, the check re-aims at a DIFFERENT tile, because a
    path from a tile to itself is vacuous and would grade PASS while proving nothing.
    ⛔ It aims at APRONS, never at the ladder (9,14) or the door (18,41): both are WARPS, and
    `navigate_to` overrides its own destination when the final waypoint is a warp — the trap this
    chapter has now hit three times.
    """
    from modules.map_path import calculate_path

    here = _here_tile()
    if _on_map(VR1F):
        target = B1F_LADDER_APRON if here != B1F_LADDER_APRON else VR_ENTRANCE
        target_map = VR1F
    elif _on_map(EG):
        target = VR_APRON if here != VR_APRON else EG_PC_APRON
        target_map = EG
    else:
        # ‼ An unexpected end map is itself the finding — record it, do not invent a target.
        report["continue_after_training"] = f"UNEXPECTED MAP {_where()} — no continuation target"
        _take(report, "R-TRAINCONTINUE")
        return

    try:
        path = calculate_path((target_map, here), (target_map, target))
        report["continue_after_training"] = {"from": here, "to": target, "wp": len(path)}
    except Exception as error:  # noqa: BLE001 - a refusal IS the reading
        # ⛔ Aborts first: "deliberately non-fatal" must never mean "deliberately deaf".
        reraise_if_aborting(error)
        report["continue_after_training"] = f"{type(error).__name__}: {str(error)[:120]}"
    _take(report, "R-TRAINCONTINUE")


def train_for_victory_road(report=None, *, target: int = TRAIN_TARGET) -> Generator:
    """Raise the battlers on VICTORY_ROAD_1F before attempting Wally.

    ⛔⛔ THREE GUARDS, EACH FROM A MEASURED FAILURE — none is optional:
    1. **PRE-ESTIMATE AND REFUSE.** `train_team` has no frame budget of its own, only a 500-round
       guard, and KI-28 burned **19.9M frames** grinding toward a level the local grass could not
       deliver. This estimates first and raises rather than spinning. ‼ An estimate of `None` means
       "cannot tell" and is treated as EXPENSIVE, never as cheap.
    2. **RESTORE THE LEAD OURSELVES, IN A `finally`.** `train_team`'s own
       `_lead_strongest_battler()` sits AFTER its loop, not inside its `finally`
       (`early_game.py:2091-2094`), so any abort or whiteout mid-grind exits with the WEAKEST
       trainee in slot 0. Measured cost of not doing this: 19 losses and 44 whiteouts at one tile.
    3. **CHECK THE CARRIERS SURVIVED.** `train_team` heals on every HP *or* PP dip, and each heal is
       another PC-deposit roll — see `assert_carriers_survived`.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    ready, reasons = team_is_ready(target)
    report["train_pre"] = {f"{s}#{p:08X}": lv for (p, s), (_sl, lv) in battler_identities().items()}
    report["train_reasons"] = reasons
    _take(report, "R-TRAINPRE")
    if ready:
        report["trained"] = "already ready"
        _take(report, "R-ESTIMATE")
        _take(report, "R-TRAINED")
        _take(report, "R-READY")
        return

    # ---- guard 1: estimate BEFORE committing frames -------------------------------------------
    from modules.story.training_areas import estimate_frames_to_level

    WILD_MAX = 40      # MEASURED: VICTORY_ROAD_1F's strongest land encounter is L40
    estimates, total = {}, 0
    for (pid, species), (slot, level) in battler_identities().items():
        if level >= target:
            continue
        mon = get_party()[slot]
        est = estimate_frames_to_level(mon, target, WILD_MAX)
        estimates[f"{species}#{pid:08X}"] = est
        if est is None:
            raise BotModeError(
                f"Ch23 training: cannot estimate the cost of taking {species}#{pid:08X} from "
                f"L{level} to L{target} on L{WILD_MAX} wilds. ⛔ An unknown estimate is treated as "
                f"EXPENSIVE, never as cheap — that is the KI-28 shape, which burned 19.9M frames."
            )
        total += est
    report["train_estimates"] = estimates
    report["train_estimate_total"] = total
    _take(report, "R-ESTIMATE")
    # ⭐ ESTIMATE-ONLY MODE. The whole point of estimating first is to be able to REPORT the cost
    # before spending it — a grind is the one kind of work where "just run it and see" is the
    # expensive option. `POKEBOT_CH23_ESTIMATE_ONLY=1` stops here with the numbers taken.
    if _os_environ_flag("POKEBOT_CH23_ESTIMATE_ONLY"):
        report["trained"] = "ESTIMATE ONLY — no frames spent"
        return
    # ⛔⛔ THE CEILING IS PER-CALL, NOT PER-TOTAL, AND THE DISTINCTION IS THE WHOLE POINT.
    # KI-28's 19.9M-frame livelock was ONE `train_team` call chasing a level the local grass could
    # never deliver — an unbounded call, not a large sum of bounded ones. This leg makes a SEPARATE
    # `train_team` call per mon, each of which converges on its own, so summing them and refusing
    # would be measuring the wrong quantity: it would block a plan that is merely LONG in favour of
    # one that is merely SHORT, while doing nothing about the failure mode the ceiling exists for.
    # ⇒ refuse any SINGLE mon whose grind is unaffordable; REPORT the total, because the total is
    # the user's time and that is a decision for them, not a safety property.
    worst = max(estimates.items(), key=lambda kv: kv[1], default=(None, 0))
    if worst[1] > MAX_TRAINING_FRAMES:
        raise BotModeError(
            f"Ch23 training: {worst[0]} alone needs {worst[1]:,} frames, over the "
            f"{MAX_TRAINING_FRAMES:,} per-call ceiling every other caller respects. "
            f"Per-mon: {estimates}. ⇒ lower the target for that mon, or train on B1F AFTER Wally "
            f"(950.8 EXP/battle vs 1F's 775.6) — do NOT raise the ceiling to make the run start."
        )

    # ---- guard 2: we restore the lead, because `train_team` will not on an abort ---------------
    from modules.story.early_game import (
        _lead_strongest_battler, _rotate_lead_safely, train_team)

    try:
        for (pid, species), (_slot, level) in sorted(
            battler_identities().items(), key=lambda kv: kv[1][1]
        ):
            if level >= target:
                continue
            _check_abort()
            # ⛔ RE-RESOLVE THE SLOT IMMEDIATELY BEFORE THE CALL. A previous round's rotation has
            # already moved this mon; the index captured above is stale by construction.
            here = battler_identities().get((pid, species))
            if here is None:
                raise BotModeError(
                    f"Ch23 training: {species}#{pid:08X} vanished from the battler set mid-grind. "
                    f"Roster now: {sorted(party_identities())}."
                )
            slot_now, level_now = here
            if level_now >= target:
                continue

            # ---- ⛔⛔ ROTATE TO SLOT 0 OURSELVES, THEN TRAIN `slots={0}` ------------------------
            # ‼ MEASURED 2026-09-04: `train_team(slots={i})` with i != 0 does exactly ONE spin-batch
            # and then RETURNS AS IF FINISHED. A 900k-frame run produced **8 battles** and moved
            # Wailmer 40->41, Mightyena 44->45, Swellow **+0**, against an estimate of 306 battles.
            # ⇒ WHY: `early_game.py:2021` computes `need` from `party[i]` BY INDEX; `:2034` then
            # calls `_rotate_lead_safely(target_slot)`, which drives the party menu's SWITCH option
            # (`higher_level_actions.py:500`) — a **SWAP**. On the next iteration `party[i]` is the
            # OLD LEAD (Sceptile L51 >= target), so `need` is empty and the loop breaks.
            # ⇒ This is THIS PROJECT'S OWN RULE #3 — "assert IDENTITY, never position" — violated
            # inside shared code. Filed separately; NOT fixed here, because `train_team(slots=...)`
            # is also the gym-prep path and changing it would move every gym's levels at once.
            # ⭐ THE COROLLARY IS THE FIX: with the mon ALREADY at slot 0, `target_slot == 0`, no
            # rotation happens, `party[0]` stays the same mon, and the loop converges correctly.
            # So we do the rotation, and hand `train_team` only the case it gets right.
            if slot_now != 0:
                yield from _rotate_lead_safely(slot_now)
                # ⛔ VERIFY BY PID THAT IT LANDED. `_rotate_lead_safely` "gives up gracefully" after
                # 3 attempts (its own docstring: "the rotation is an optimization") — and a silent
                # give-up here is NOT cosmetic: it would grind whatever else is in slot 0, burning
                # the entire budget on the wrong Pokémon while every level readout looked plausible.
                lead = get_party()[0]
                if lead is None or lead.personality_value != pid:
                    # ⛔ BUILD THE DESCRIPTION FIRST. A ternary at the end of an implicit string
                    # concatenation binds to the WHOLE concatenation, not the last fragment — the
                    # same fused-literal trap that silently produced "ch23roadch23train" from a
                    # missing comma earlier in this chapter. Keep the conditional out of the f-string.
                    holder = "nothing"
                    if lead is not None:
                        holder = f"{lead.species.name}#{lead.personality_value:08X}"
                    raise BotModeError(
                        f"Ch23 training: tried to rotate {species}#{pid:08X} from slot {slot_now} "
                        f"to the lead, but slot 0 holds {holder}. ⛔ `_rotate_lead_safely` gives up "
                        f"gracefully after 3 attempts, and training the wrong Pokémon would burn "
                        f"the whole budget while every level readout still looked plausible."
                    )
            yield from train_team(
                target, slots={0}, grass=TRAIN_SPOT_1F,
                heal_center=PokemonCenter.EvergrandeCity,
            )
            assert_carriers_survived(f"training {species}#{pid:08X}")

            # ⛔ AND PROVE THE CALL ACTUALLY MOVED THE MON. `train_team` returning is not evidence
            # it trained — that is exactly how the index bug above stayed invisible. Re-resolve by
            # PID and refuse to spin on a call that achieved nothing.
            after = battler_identities().get((pid, species))
            if after is not None and after[1] <= level_now and after[1] < target:
                raise BotModeError(
                    f"Ch23 training: `train_team` returned without raising {species}#{pid:08X} "
                    f"past L{level_now} (still L{after[1]}, target L{target}). ⛔ Refusing to loop "
                    f"— a call that trains nothing would spin the budget away silently."
                )
    finally:
        # ⛔ IN A `finally` ON PURPOSE — this is the guard `train_team` does not give us.
        yield from _lead_strongest_battler()

    report["train_post"] = {f"{s}#{p:08X}": lv for (p, s), (_sl, lv) in battler_identities().items()}
    _take(report, "R-TRAINED")

    # ⛔ TAKE THE LIVENESS READING BEFORE THE READINESS RAISE. If it went after, a not-ready run
    # would raise first and the one reading that says whether the bot is STRANDED would never be
    # taken — exactly when it matters most.
    training_continue_reading(report)

    ready, reasons = team_is_ready(target)
    report["train_reasons_after"] = reasons
    if not ready:
        raise BotModeError(
            f"Ch23 training: finished the grind but the team is still not ready: {reasons}. "
            f"Levels now: {report['train_post']}."
        )
    _take(report, "R-READY")


# --------------------------------------------------------------------------------------------
# LEG 6 — B1F: solve the boulder puzzle and descend to B2F
# --------------------------------------------------------------------------------------------
def b1f_obstacle_positions() -> dict:
    """`{local_id: (x, y)}` for the three obstacles this leg moves, as the GAME currently sees them.

    ⛔⛔ `get_map_objects()` IS A CAMERA-RANGE WINDOW, NOT A CENSUS. An object further than roughly a
    screen away is absent from the list **whether or not it exists** — this project has paid for that
    read three times (the §Ch21 "ZERO NPCs loaded" misread, the (31,18) Expert claim, and leg 2b's
    Wallace check from (9,3)). ⇒ **an id MISSING from this dict means "not visible from here", NEVER
    "gone"**, and no caller may treat absence as proof.
    ‼ `MapLocation.objects` is the ROM TEMPLATE (original positions) — never mix it with this.
    """
    from modules.map import get_map_objects

    # ⛔⛔ TRACK **EVERY** B1F OBSTACLE THIS CHAPTER TOUCHES, not just leg 6's three.
    # ‼ MEASURED 2026-09-04: leg 8's first run logged `plug_after_smash_a = {}`,
    # `plug_after_push = {}`, `plug_after_smash_b = {}` — which READS as "no obstacles left" and
    # actually meant "this function was not looking at leg 8's ids at all". The run PASSED with three
    # vacuous readings in its own report.
    # ⇒ **AN INSTRUMENT SCOPED TO YESTERDAY'S QUESTION RETURNS A CONFIDENT EMPTY ANSWER TO TODAY'S.**
    # Same family as `#24-waterfalltimeout` and the six dead fault arms: silent, plausible, wrong.
    watched = (
        B1F_PUSH_WEST["local_id"], B1F_PUSH_EAST["local_id"], B1F_SMASH["local_id"],   # leg 6
        B1F_SMASH_A["local_id"], B1F_PUSH_N["local_id"], B1F_SMASH_B["local_id"],       # leg 8
        B1F_TRAP_BOULDER_ID,                                                            # the trap
    )
    out = {}
    for obj in get_map_objects():
        local_id = getattr(obj, "local_id", None)
        if local_id in watched:
            out[local_id] = tuple(obj.current_coords)
    return out


def _can_reach(map_enum, target: tuple) -> bool:
    """Can our planner reach `target` on `map_enum` from where we stand *right now*?

    ⛔ THE WORLD IS THE JUDGE, NOT THE SCRIPT. This is how each step is verified: not "did the routine
    return without raising" but "did the map actually open up". `strength_push` already judges its own
    success by object identity; this judges the *consequence*.
    """
    from modules.map_path import calculate_path

    try:
        calculate_path((map_enum, _here_tile()), (map_enum, target))
        return True
    except Exception as error:  # noqa: BLE001 - a refusal IS the reading
        reraise_if_aborting(error)
        return False


def b1f_can_reach(target: tuple) -> bool:
    """Leg 6's B1F-scoped wrapper. ‼ ONE implementation, not two — the same fact in two functions is
    the P5 doc shape in code form, and it drifts."""
    return _can_reach(B1F, target)


def _ladder_apron(map_enum, ladder: tuple, label: str) -> tuple:
    """MEASURE which neighbour of a ladder we can actually stand on. Returns `(tile, step)`.

    ⛔⛔ DERIVED, NEVER HARDCODED — *"a liveness check must derive its target from the state the run
    ACTUALLY reached; hardcode no coordinates"*. A guessed coordinate looks perfectly reasonable in
    review and strands the run in practice.
    ⭐ AND IT IS NOT A HYPOTHETICAL SAFEGUARD HERE: two independent agents named DIFFERENT aprons for
    B2F's exit ladder ((18,12) and (19,13)) and the framing "at most one can be right" turned out to
    be wrong — both work, and so does (20,12), while (19,11) is a wall. Deriving sidesteps the whole
    argument.

    ‼ The returned `step` is the direction to press to move FROM the apron ONTO the ladder, which is
    the OPPOSITE of the offset that produced the apron — getting that backwards walks the bot away
    from the warp. (Three index/direction inversions have shipped in this codebase.)
    """
    lx, ly = ladder
    for (dx, dy), step in (((1, 0), "Left"), ((-1, 0), "Right"),
                           ((0, 1), "Up"), ((0, -1), "Down")):
        candidate = (lx + dx, ly + dy)
        if _can_reach(map_enum, candidate):
            return candidate, step
    raise BotModeError(
        f"Ch23 {label}: the ladder {ladder} on {map_enum} has no reachable neighbour, so there is "
        f"nowhere to stand to step onto it. We are at {_here_tile()}."
    )


def b1f_ladder_apron() -> tuple:
    """MEASURE which neighbour of the B2F ladder we can actually stand on. Returns `(tile, step)`.

    ⛔⛔ DERIVED, NEVER HARDCODED. The rule this obeys — *"a liveness check must derive its target
    from the state the run ACTUALLY reached; hardcode no coordinates"* — exists because a guessed
    coordinate looks perfectly reasonable in review and strands the run in practice. The solve drive
    measured the ladder reachable in 50 waypoints but never recorded WHICH tile it stood on, so
    inventing one here would be exactly the guess the rule forbids.

    ‼ The returned `step` is the direction to press to move FROM the apron ONTO the ladder, which is
    the OPPOSITE of the offset that produced the apron — getting that backwards walks the bot away
    from the warp. (Three index/direction inversions have shipped in this codebase; this comment is
    cheaper than a fourth.)
    """
    try:
        return _ladder_apron(B1F, B1F_B2F_LADDER, "leg 6")
    except BotModeError as error:
        # ⛔ Aborts first — "deliberately non-fatal" must never mean "deliberately deaf".
        reraise_if_aborting(error)
        raise BotModeError(
            f"{error} Obstacles: {b1f_obstacle_positions()}. ⇒ the puzzle solved but the approach "
            f"did not open — re-enter B1F (which resets it) and re-solve."
        ) from error


def party_needs_heal() -> tuple[bool, dict]:
    """`(needs_heal, reading)` — judged on FAINTS and HP FRACTION, never on a single mon.

    ⛔ ASSERT ON IDENTITY, NEVER ON COUNT. The reading names the fainted mons by PID, because a party
    count nets to zero when one faints and another is healed, and "6 Pokémon" reads TRUE either way.
    """
    total = live = 0
    fainted = []
    for mon in get_party():
        if mon is None or mon.is_egg:
            continue
        total += mon.total_hp
        live += mon.current_hp
        if mon.current_hp == 0:
            fainted.append(f"{mon.species.name}#{mon.personality_value:08X}")
    frac = (live / total) if total else 1.0
    reading = {"hp": f"{live}/{total}", "fraction": round(frac, 3), "fainted": fainted}
    return (bool(fainted) or frac < HEAL_HP_FRACTION), reading


def heal_before_descent(report=None) -> Generator:
    """Heal at the Ever Grande Poké Center BEFORE dropping into B1F, then come back to the ladder.

    ⛔⛔ WHY THIS EXISTS, MEASURED NOT FEARED. Without it the party degrades every leg:
    `post_training` 95% / 0 fainted → `post_wally` 67% / 2 → `post_b1f` **32% / 3**. Leg 7 would
    start from the worst of those, and `probe_anchor_inventory` already refuses to call it usable.

    ⛔ IT HEALS FROM **1F**, NOT FROM B1F, AND THAT IS THE WHOLE POINT OF ITS PLACEMENT: on 1F the
    bot is ONE warp from the exit, whereas from B1F it would have to re-cross the puzzle — and the
    puzzle RESETS on every warp, so a round trip from below costs the entire solve twice.

    ‼ THE ROUTE OUT USES AN **ARROW WARP** (`VR_EXIT_ARROW`), which fires only on standing + facing
    South + holding Down. We had only ever crossed it INWARD before this leg, so the attempt is
    bounded and raises with the tile named rather than pressing Down forever.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    needs, before = party_needs_heal()
    report["heal_before"] = before
    if not needs:
        report["healed"] = f"not needed ({before['hp']}, no faints)"
        _take(report, "R6-HEAL")
        return
    if _fault("NOHEAL6"):
        context.message = "Ch23 FAULT NOHEAL6: skipping the pre-descent heal"
        report["healed"] = "SKIPPED (fault arm)"
        _take(report, "R6-HEAL")
        return

    if not _on_map(VR1F):
        raise BotModeError(
            f"Ch23 leg 6: the pre-descent heal must run from VICTORY_ROAD_1F (one warp from the "
            f"exit) but we are at {_where()}. ⛔ Healing from B1F would cost the whole boulder solve "
            f"twice, because every warp resets the puzzle."
        )

    # ---- out through the arrow warp ------------------------------------------------------------
    if _here_tile() != VR_EXIT_APRON:
        yield from _navigate_riding_out(VR1F, VR_EXIT_APRON)
        yield from wait_until_truly_controllable()
    yield from _walk_through_warp("Down", VR1F.value)
    yield from wait_until_truly_controllable()
    report["exited_to"] = _where()
    if not _on_map(EG):
        raise BotModeError(
            f"Ch23 leg 6: held Down on the arrow warp {VR_EXIT_ARROW} from {VR_EXIT_APRON} and did "
            f"not arrive in EVER_GRANDE_CITY — we are at {_where()}. ⛔ `MB_SOUTH_ARROW_WARP` needs "
            f"the player STANDING on the tile, FACING South and HOLDING Down; a single step onto it "
            f"does nothing."
        )

    # ---- heal ------------------------------------------------------------------------------------
    yield from _budgeted(
        heal_in_pokemon_center(PokemonCenter.EvergrandeCity), HEAL_BUDGET,
        "heal before the B1F descent",
    )
    yield from wait_until_truly_controllable()
    # ⛔ THE HEAL PIGGYBACKS TWO PC-DEPOSIT PATHS, and this party is mostly "dead weight" behind an
    # L52 lead by `DEAD_WEIGHT_LEVEL_GAP = 8`. Losing Wailord here strands the chapter.
    assert_carriers_survived("the pre-descent heal")

    _, after = party_needs_heal()
    report["heal_after"] = after
    # ⛔ ASSERT THE CONSEQUENCE. "heal_in_pokemon_center returned" is not "the party is healed" —
    # the same rule that caught KI-84. A heal that leaves anyone fainted has not worked.
    if after["fainted"]:
        raise BotModeError(
            f"Ch23 leg 6: after the Ever Grande heal the party STILL has fainted members "
            f"{after['fainted']} ({after['hp']}). ⛔ Refusing to descend — B1F carries a trainer and "
            f"wild encounters, and this is how a run whites out underground."
        )

    # ---- back in, and back to the ladder apron ---------------------------------------------------
    if _here_tile() != VR_APRON:
        yield from _navigate_riding_out(EG, VR_APRON)
        yield from wait_until_truly_controllable()
    yield from _walk_through_warp("Up", EG.value)
    yield from wait_until_truly_controllable()
    if not _on_map(VR1F):
        raise BotModeError(
            f"Ch23 leg 6: stepped north off the Ever Grande apron {VR_APRON} after healing and did "
            f"not re-enter VICTORY_ROAD_1F — we are at {_where()}."
        )
    yield from _navigate_riding_out(VR1F, B1F_LADDER_APRON)
    yield from wait_until_truly_controllable()
    report["healed"] = {"before": before, "after": after, "back_at": _here_tile()}
    _take(report, "R6-HEAL")


def enter_b1f(report=None) -> Generator:
    """Step from the 1F ladder apron (9,15) onto the ladder (9,14), landing on B1F (8,3)."""
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    if _on_map(B1F):
        report["b1f_entry"] = f"already on B1F at {_here_tile()}"
        _take(report, "R6-ENTER")
        return

    if not _on_map(VR1F):
        raise BotModeError(
            f"Ch23 leg 6: expected to start on VICTORY_ROAD_1F (or already on B1F) but we are at "
            f"{_where()}. Leg 5 ends on the ladder apron {B1F_LADDER_APRON}; start this leg from "
            f"`post_wally.ss1`."
        )
    if _here_tile() != B1F_LADDER_APRON:
        yield from _navigate_riding_out(VR1F, B1F_LADDER_APRON)
        yield from wait_until_truly_controllable()

    # ⛔ `_walk_through_warp` and NOT `navigate_to(B1F_LADDER)`: (9,14) is a WARP, and aiming a
    # navigation at it makes `navigate_to` override its own destination (the trap this chapter has
    # now hit four times). ‼ AND THE SECOND ARGUMENT IS THE MAP WE ARE **LEAVING**, NOT THE
    # DESTINATION — passing the destination makes its `while` loop exit immediately, so it presses
    # nothing, raises nothing, and returns "successfully" while the bot stands still. That exact
    # no-op produced three confident-but-vacuous readings on 2026-09-04.
    yield from _walk_through_warp("Up", VR1F.value)
    yield from wait_until_truly_controllable()

    if not _on_map(B1F):
        raise BotModeError(
            f"Ch23 leg 6: stepped onto the ladder {B1F_LADDER} from {B1F_LADDER_APRON} and did not "
            f"arrive on VICTORY_ROAD_B1F — we are at {_where()}."
        )
    report["b1f_entry"] = _here_tile()
    _take(report, "R6-ENTER")


def solve_b1f_puzzle(report=None) -> Generator:
    """Push both boulders and smash the rock, verifying the WORLD after every step.

    ⛔⛔ RE-SOLVED ON EVERY ENTRY, NEVER CACHED. Every warp resets the puzzle
    (`B1F_PUZZLE_RESETS_ON_WARP`), so a "we already did this" flag would be wrong the moment the bot
    takes any ladder — including the one it is about to take. There is deliberately no such flag.

    THE ORDER IS FORCED: (9,10) can only be pushed EAST from (8,10), and (8,10) is unreachable until
    (4,7) has moved WEST. Each step below asserts the CONSEQUENCE it is supposed to produce, so a
    silent no-op cannot pass for success.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    from modules.story.early_game import _smash_rock, strength_push

    report["puzzle_before"] = b1f_obstacle_positions()
    report["ladder_before"] = b1f_can_reach(B1F_B2F_LADDER)

    # ⛔ ANTI-VACUITY. If the ladder is ALREADY reachable this leg has nothing to prove, and a PASS
    # would be meaningless. That should be impossible (every warp resets the puzzle), so it means the
    # start state is not what we think it is — which is worth a loud stop, not a quiet success.
    if report["ladder_before"]:
        raise BotModeError(
            f"Ch23 leg 6: the B2F ladder {B1F_B2F_LADDER} is reachable BEFORE any push — the puzzle "
            f"is supposed to start blocked on every entry. Obstacles now: {report['puzzle_before']}. "
            f"⇒ the start state is wrong, or the reset assumption is."
        )

    # ---- step 1: the WEST push that unlocks everything else ------------------------------------
    if not _fault("NOPUSH1"):
        yield from strength_push(
            B1F, B1F_PUSH_WEST["approach"], B1F_PUSH_WEST["face"]
        )
        yield from wait_until_truly_controllable()
    else:
        context.message = "Ch23 FAULT NOPUSH1: skipping the first boulder push"

    # ⛔ ASSERT THE CONSEQUENCE, NOT THE CALL. MEASURED: (8,10) refuses before this push and returns
    # 7 waypoints after it. That flip is the whole ordering constraint, so it is what we check —
    # `strength_push` returning is not evidence the corridor opened.
    report["opened_east_approach"] = b1f_can_reach(B1F_PUSH_EAST["approach"])
    report["puzzle_after_push1"] = b1f_obstacle_positions()
    _take(report, "R6-PUSH1")
    if not report["opened_east_approach"]:
        raise BotModeError(
            f"Ch23 leg 6: after pushing {B1F_PUSH_WEST['tile']} WEST, the approach tile "
            f"{B1F_PUSH_EAST['approach']} is STILL unreachable, so the second boulder cannot be "
            f"pushed. Obstacles: {report['puzzle_after_push1']}. ⛔ The likeliest cause is a push in "
            f"the wrong DIRECTION: south bricks the route (measured), and recovery is to leave B1F "
            f"and re-enter, which resets the puzzle."
        )

    # ---- step 2: the EAST push ------------------------------------------------------------------
    yield from strength_push(B1F, B1F_PUSH_EAST["approach"], B1F_PUSH_EAST["face"])
    yield from wait_until_truly_controllable()
    report["puzzle_after_push2"] = b1f_obstacle_positions()
    report["ladder_after_push2"] = b1f_can_reach(B1F_B2F_LADDER)
    _take(report, "R6-PUSH2")

    # ‼ AND THIS IS THE READING THAT PROVES THE ROCK IS LOAD-BEARING. MEASURED: after BOTH pushes the
    # ladder is STILL unreachable. A leg that only checked the endpoints would never learn that, and
    # would not know which of its three steps it could drop.
    if report["ladder_after_push2"]:
        report["surprise"] = (
            "the B2F ladder became reachable after two pushes and BEFORE the Rock Smash — that "
            "contradicts the 2026-09-04 measurement, where it stayed blocked until (18,12) was "
            "smashed. Not fatal, but the route model is wrong somewhere."
        )

    # ---- step 3: the rock ------------------------------------------------------------------------
    # ⚠ Rock Smash rolls a WILD ENCOUNTER (B1F has a `rock_smash_mons` table: Geodude/Graveler
    # 30-40). The battle listener fights it; the measured solve took 2 battles this way.
    if not _fault("NOSMASH"):
        yield from _smash_rock(B1F, B1F_SMASH["approach"], B1F_SMASH["face"])
        yield from wait_until_truly_controllable()
    else:
        context.message = "Ch23 FAULT NOSMASH: skipping the Rock Smash"
    report["puzzle_after_smash"] = b1f_obstacle_positions()
    _take(report, "R6-SMASH")

    # ---- the verdict: can we actually reach the ladder now? --------------------------------------
    report["ladder_reachable"] = b1f_can_reach(B1F_B2F_LADDER)
    _take(report, "R6-LADDERPATH")
    if not report["ladder_reachable"]:
        raise BotModeError(
            f"Ch23 leg 6: the puzzle steps all ran but the B2F ladder {B1F_B2F_LADDER} is still "
            f"unreachable. Obstacles: {report['puzzle_after_smash']}. Before: "
            f"{report['puzzle_before']}. ⛔ Do NOT retry blindly — every warp resets the puzzle, so "
            f"the recovery is to leave B1F and re-enter, then re-solve from the top."
        )


def descend_to_b2f(report=None) -> Generator:
    """§Ch23 LEG 6 — enter B1F, solve the puzzle, and take the ladder down to B2F.

    ⛔ BOUNDED END TO END (`B1F_BUDGET_FRAMES`). KI-83's shape is a leg that cannot finish and cannot
    stop; the measured solve ran far inside this budget, so a run that exhausts it is stuck, not slow.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())

    # ⛔ HEAL FIRST, FROM 1F. See `heal_before_descent` for why placement matters.
    yield from _budgeted(heal_before_descent(report), B1F_BUDGET_FRAMES, "heal before descending")
    yield from _budgeted(enter_b1f(report), B1F_BUDGET_FRAMES // 4, "enter B1F")
    yield from _budgeted(solve_b1f_puzzle(report), B1F_BUDGET_FRAMES, "solve the B1F puzzle")

    # ---- walk to the ladder's APRON, never to the ladder ----------------------------------------
    # ⛔ THE APRON IS MEASURED, NOT GUESSED. See `b1f_ladder_apron`.
    apron, step_dir = b1f_ladder_apron()
    report["ladder_apron"] = {"tile": apron, "step": step_dir}
    yield from _navigate_riding_out(B1F, apron)
    yield from wait_until_truly_controllable()
    report["at_ladder_apron"] = _here_tile()
    if _here_tile() != apron:
        raise BotModeError(
            f"Ch23 leg 6: navigated toward the B2F ladder apron {apron} but ended on "
            f"{_here_tile()}. ⛔ Refusing to press {step_dir} from the wrong tile — that is how a "
            f"leg walks into a wall and calls it a warp failure."
        )

    # ⛔ THE SECOND ARG IS THE MAP WE ARE LEAVING. See `enter_b1f` for what passing the destination
    # silently does.
    yield from _walk_through_warp(step_dir, B1F.value)
    yield from wait_until_truly_controllable()
    report["b2f_arrival"] = _where()
    report["on_b2f"] = _on_map(MapRSE.VICTORY_ROAD_B2F)
    _take(report, "R6-B2F")
    if not report["on_b2f"]:
        raise BotModeError(
            f"Ch23 leg 6: stepped onto the B2F ladder {B1F_B2F_LADDER} from {apron} and did "
            f"not arrive on VICTORY_ROAD_B2F — we are at {_where()}."
        )

# --------------------------------------------------------------------------------------------
# LEG 7 — B2F: cross the water and take the ladder back up to B1F
# --------------------------------------------------------------------------------------------
def cross_b2f(report=None) -> Generator:
    """§Ch23 LEG 7 — cross VICTORY_ROAD_B2F from (30,25) to the exit ladder, landing on B1F (17,16).

    ⭐ ONE `navigate_to` DOES THE CROSSING. Measured: our planner returns 63 waypoints with
    `{Surf: 1, Waterfall: 1}`, mounting and riding the descent by itself. The hand-built 13-phase
    route a recon produced was REFUTED — its first mount enters a dead-end pond.

    ⛔ EXPECT EXACTLY ONE FORCED TRAINER FIGHT. Measured against the decomp's own LOS algorithm:
    with Surf **and Waterfall** the only unavoidable trainer is **Julie** (Sandslash/Ninetales/Tropius,
    all L42); with Surf alone it is four. ✅ Wailord carries Waterfall, so we are on the one-fight
    route. ‼ **NEVER HARDCODE "four unavoidable"** — that figure was an artefact of a pathfinder that
    could not climb.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    # ⛔ ANTI-VACUITY: a run that starts on B1F has already crossed and would prove nothing.
    if _on_map(B1F):
        raise BotModeError(
            f"Ch23 leg 7: we are already on VICTORY_ROAD_B1F at {_here_tile()} — the crossing this "
            f"leg exists to perform has already happened, so a PASS here would be meaningless. "
            f"Start from `post_b1f_healed.ss1` (B2F (30,25))."
        )
    if not _on_map(B2F):
        raise BotModeError(
            f"Ch23 leg 7: must start on VICTORY_ROAD_B2F but we are at {_where()}. Leg 6 ends there; "
            f"use `post_b1f_healed.ss1`."
        )
    report["b2f_entry"] = _here_tile()
    _take(report, "R7-ENTER")

    # ⛔ THE CARRIERS MATTER MORE HERE THAN ANYWHERE ELSE IN THE CHAPTER. Wailord carries **Surf AND
    # Waterfall AND Dive** — and B2F cannot be crossed without the first two. Losing it to a PC
    # deposit mid-chapter would strand the run on an island of water.
    assert_carriers_survived("entering B2F")

    # ---- derive the apron, never hardcode it ----------------------------------------------------
    apron, step_dir = _ladder_apron(B2F, B2F_EXIT_LADDER, "leg 7")
    report["exit_apron"] = {"tile": apron, "step": step_dir}
    _take(report, "R7-APRON")

    if _fault("LADDERAIM"):
        # ‼ THE FAULT ARM AIMS AT THE LADDER ITSELF, which is what this leg exists NOT to do.
        # `navigate_to` overrides its destination when the last waypoint is a warp, so this ends on
        # B1F at (17,16) WITHOUT the explicit step — and the apron assert below must catch it.
        context.message = "Ch23 FAULT LADDERAIM: navigating AT the ladder, not the apron"
        target = B2F_EXIT_LADDER
    else:
        target = apron

    # ⛔⛔ BOUNDED. `B2F_BUDGET_FRAMES` was declared with commentary implying it bounded this leg and
    # then referenced NOWHERE — a Tier 1 reviewer caught it. A safety constant wired to nothing is
    # the same defect as a fault arm that cannot fire: it reads as protection while providing none,
    # and the next maintainer trusts it. ⇒ it is now actually applied.
    yield from _budgeted(
        _navigate_riding_out(B2F, target), B2F_BUDGET_FRAMES, "cross B2F")
    yield from wait_until_truly_controllable()
    report["after_crossing"] = _where()
    _take(report, "R7-CROSS")

    # ⛔ ASSERT WE ARE ON THE APRON BEFORE PRESSING ANYTHING. Under the fault arm we will already be
    # on B1F here, which is exactly the silent-success this guard exists to refuse.
    if not _on_map(B2F) or _here_tile() != apron:
        raise BotModeError(
            f"Ch23 leg 7: expected to be standing on the exit apron {apron} on B2F, but we are at "
            f"{_where()}. ⛔ If this says VICTORY_ROAD_B1F, the navigation was aimed at the LADDER "
            f"and `navigate_to` overrode its own destination — the warp-as-target trap. Aim at the "
            f"apron and step onto the ladder explicitly."
        )
    assert_carriers_survived("crossing B2F")

    # ⛔ `_walk_through_warp`, and the second arg is the map we are **LEAVING**.
    yield from _walk_through_warp(step_dir, B2F.value)
    yield from wait_until_truly_controllable()
    report["b1f_arrival"] = _where()
    report["on_b1f"] = _on_map(B1F)
    _take(report, "R7-B1F")
    if not report["on_b1f"]:
        raise BotModeError(
            f"Ch23 leg 7: pressed {step_dir} from the apron {apron} onto the ladder "
            f"{B2F_EXIT_LADDER} and did not arrive on VICTORY_ROAD_B1F — we are at {_where()}."
        )


# --------------------------------------------------------------------------------------------
# LEG 8 — THE RETURN: solve B1F's 2x2 plug and climb back to 1F
# --------------------------------------------------------------------------------------------
def return_through_b1f(report=None) -> Generator:
    """§Ch23 LEG 8 — clear the 2x2 plug on B1F and take the ladder up to 1F (21,32).

    ⛔⛔ **THE BOT IS TRAPPED UNTIL THIS WORKS.** From the B2F landing (17,16) every other exit is
    unreachable (MEASURED), so this is the only way out of Victory Road — including the only way to
    reach a Poké Center.

    ⭐ **THE ORDER IS CHOSEN SO THE TRAP BECOMES UNTAKEABLE — and here is the exact mechanism, so
    nobody has to take the claim on trust.** Boulder `local_id 6` at (21,25) has exactly one legal
    push (EAST), which bricks the route; **pushing it EAST requires STANDING ON (20,25)**. Step 2
    pushes boulder `5` from (20,26) **NORTH onto (20,25)** — i.e. **it parks a boulder on the trap's
    only standpoint.** ⇒ from step 2 onward the trap is *physically* impossible, not merely avoided.
    ‼ **BE PRECISE ABOUT WHEN:** that protection engages AT step 2, not before it. Between step 1 and
    step 2 the standpoint is clear and the trap IS takeable — which is exactly the window
    `POKEBOT_CH23_FAULT_TRAPPUSH` exploits, and why that arm can move boulder 6 to (22,25) at all.
    ⇒ correctness by construction beats correctness by assertion, but only over the interval where
    the construction actually holds; the assertions cover the rest.

    ‼ RE-SOLVED ON EVERY ENTRY, NEVER CACHED: every warp resets the puzzle, confirmed THREE times
    now (most recently arriving here from B2F, with leg 6's obstacles restored).
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    from modules.story.early_game import _smash_rock, strength_push

    yield from wait_until_truly_controllable()
    if not _on_map(B1F):
        raise BotModeError(
            f"Ch23 leg 8: must start on VICTORY_ROAD_B1F (leg 7 lands at {B1F_RETURN_LANDING}) but "
            f"we are at {_where()}. Use `post_b2f.ss1`."
        )
    report["b1f_return_entry"] = _here_tile()
    report["plug_before"] = b1f_obstacle_positions()
    report["ladder_before"] = _can_reach(B1F, B1F_1F_LADDER)
    _take(report, "R8-ENTER")

    # ⛔ ANTI-VACUITY: the plug is supposed to seal the ladder on every entry. If it is already open,
    # this run cannot demonstrate anything and the start state is not what we think it is.
    if report["ladder_before"]:
        raise BotModeError(
            f"Ch23 leg 8: the 1F ladder {B1F_1F_LADDER} is reachable BEFORE any work — the plug is "
            f"supposed to seal it on every entry (the warp reset). Obstacles: "
            f"{report['plug_before']}. ⇒ the start state is wrong, or the reset assumption is."
        )
    assert_carriers_survived("entering the return leg")

    # ---- step 1: smash rock 11 at (20,25), standing west at (19,25) -----------------------------
    yield from _smash_rock(B1F, B1F_SMASH_A["approach"], B1F_SMASH_A["face"])
    yield from wait_until_truly_controllable()
    report["plug_after_smash_a"] = b1f_obstacle_positions()
    _take(report, "R8-SMASHA")

    # ---- step 2: the NORTH push that makes the trap unreachable ---------------------------------
    if not _fault("NOPUSHN"):
        if _fault("TRAPPUSH"):
            # ‼ THE TRAP ARM: push boulder 6 EAST instead. Its target (22,25) is the base of the only
            # column to the ladder, so this seals the route. The guard below must catch it.
            context.message = "Ch23 FAULT TRAPPUSH: taking the route-bricking EAST push"
            yield from strength_push(B1F, (20, 25), "Right")
        else:
            yield from strength_push(B1F, B1F_PUSH_N["approach"], B1F_PUSH_N["face"])
        yield from wait_until_truly_controllable()
    else:
        context.message = "Ch23 FAULT NOPUSHN: skipping the north push"
    report["plug_after_push"] = b1f_obstacle_positions()
    _take(report, "R8-PUSHN")

    # ---- step 3: smash rock 12 at (21,26) --------------------------------------------------------
    # ⚠ Rock Smash rolls a wild encounter; the battle listener handles it.
    yield from _smash_rock(B1F, B1F_SMASH_B["approach"], B1F_SMASH_B["face"])
    yield from wait_until_truly_controllable()
    report["plug_after_smash_b"] = b1f_obstacle_positions()
    _take(report, "R8-SMASHB")

    # ---- the verdict: is the ladder open? --------------------------------------------------------
    report["ladder_reachable"] = _can_reach(B1F, B1F_1F_LADDER)
    _take(report, "R8-LADDERPATH")
    if not report["ladder_reachable"]:
        raise BotModeError(
            f"Ch23 leg 8: the plug steps ran but the 1F ladder {B1F_1F_LADDER} is still unreachable. "
            f"Obstacles: {report['plug_after_smash_b']}. Before: {report['plug_before']}. "
            f"⛔ Do NOT retry blindly — if boulder {B1F_PUSH_N['local_id']} went EAST instead of "
            f"NORTH the route is BRICKED, and the only recovery is to leave B1F and re-enter, which "
            f"resets the puzzle. ‼ From here the bot is TRAPPED, so that recovery means a whiteout "
            f"(respawn EVER_GRANDE, outside and healed) — survivable, but not free."
        )

    # ---- up to 1F, apron-first ---------------------------------------------------------------------
    apron, step_dir = _ladder_apron(B1F, B1F_1F_LADDER, "leg 8")
    report["ladder_apron"] = {"tile": apron, "step": step_dir}
    yield from _budgeted(_navigate_riding_out(B1F, apron), B1F_RETURN_BUDGET, "reach the 1F ladder")
    yield from wait_until_truly_controllable()
    if _here_tile() != apron:
        raise BotModeError(
            f"Ch23 leg 8: navigated toward the 1F ladder apron {apron} but ended on {_here_tile()}."
        )
    yield from _walk_through_warp(step_dir, B1F.value)
    yield from wait_until_truly_controllable()
    report["f1_arrival"] = _where()
    report["on_1f"] = _on_map(VR1F)
    _take(report, "R8-1F")
    if not report["on_1f"]:
        raise BotModeError(
            f"Ch23 leg 8: pressed {step_dir} onto the ladder {B1F_1F_LADDER} from {apron} and did "
            f"not arrive on VICTORY_ROAD_1F — we are at {_where()}."
        )
    assert_carriers_survived("returning to 1F")


# --------------------------------------------------------------------------------------------
# LEG 9 — out through the 1F arrow warp, and measure what is reachable on the far side
# --------------------------------------------------------------------------------------------
def exit_victory_road(report=None) -> Generator:
    """§Ch23 LEG 9 — leave Victory Road via the 1F arrow warp at (39,5).

    ⛔ THE ARROW WARP IS NOT A STEP-ON WARP. `TryArrowWarp` fires only on STAND + FACE South + HOLD
    Down, so the leg navigates to the APRON (38,5) and then holds the direction; aiming navigation at
    (39,5) itself would simply park the bot on the tile without warping.

    ⭐⭐ AND IT ANSWERS AN OPEN QUESTION RATHER THAN INHERITING IT. A research pass DERIVED that the
    landing (18,27) sits on a plateau **without** the Ever Grande Poké Center, which would make
    "exit and heal" wrong and force the League's own Centre instead. That agent flagged its own
    elevation model as a reimplementation. ⇒ once outside, this leg **asks our planner what is
    actually reachable** and records it, so `#24-ch23attrition` gets a measured answer.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    # ⛔ ANTI-VACUITY: starting outside Victory Road proves nothing about leaving it.
    if not _on_map(VR1F):
        raise BotModeError(
            f"Ch23 leg 9: must start on VICTORY_ROAD_1F (leg 8 lands at {F1_LADDER_LANDING}) but we "
            f"are at {_where()}. Use `post_return.ss1`."
        )

    target = F1_EXIT_ARROW if _fault("ARROWAIM") else F1_EXIT_APRON
    if _fault("ARROWAIM"):
        context.message = "Ch23 FAULT ARROWAIM: aiming at the arrow tile, not its apron"
    yield from _budgeted(
        _navigate_riding_out(VR1F, target), B1F_RETURN_BUDGET, "reach the exit apron")
    yield from wait_until_truly_controllable()
    report["at_exit_apron"] = _here_tile()
    _take(report, "R9-APRON")
    if _here_tile() != F1_EXIT_APRON:
        raise BotModeError(
            f"Ch23 leg 9: expected to stand on the exit apron {F1_EXIT_APRON} but we are at "
            f"{_here_tile()}. ⛔ If this is {F1_EXIT_ARROW}, the navigation was aimed at the ARROW "
            f"TILE itself — arrow warps do not fire on a step, so the bot would sit there forever."
        )

    # ---- ⛔⛔ STEP **ONTO** THE ARROW TILE FIRST — THIS IS WHERE MY FIRST DRIVE FAILED ------------
    # An ARROW warp is not a normal warp and the two need OPPOSITE handling:
    #   normal warp  -> stand BESIDE it and press TOWARD it (legs 6, 7, 8 all do this)
    #   arrow warp   -> stand **ON** it and press the ARROW'S OWN direction (South, here)
    # ‼ MEASURED 2026-09-04: with the apron (38,5) WEST of the arrow (39,5), pressing Down from the
    # apron walks the bot SOUTH, away from the tile, and `_walk_through_warp` then exhausts its
    # budget — *"Did not pass through the Down warp from map (24,43)"* with the bot parked on (38,5).
    # ⇒ the recon said this outright (*"issue ONE explicit step EAST onto (39,5); (39,5) MUST be the
    # standing tile"*) and I read it through the shape of the previous three legs instead.
    # ⇒ **WHEN A MECHANIC IS NAMED AS DIFFERENT, DO NOT REUSE THE PREVIOUS LEG'S PATTERN FOR IT.**
    yield from _bounded_step("Right", F1_EXIT_ARROW, map_enum=VR1F)
    yield from wait_until_truly_controllable()
    if _here_tile() != F1_EXIT_ARROW:
        raise BotModeError(
            f"Ch23 leg 9: stepped EAST from {F1_EXIT_APRON} but landed on {_here_tile()} instead of "
            f"the arrow tile {F1_EXIT_ARROW}. ⛔ The warp cannot fire unless we are STANDING on it."
        )
    report["on_arrow_tile"] = _here_tile()

    # ---- now hold Down until the map changes -----------------------------------------------------
    # ⛔ `_walk_through_warp` presses the direction repeatedly, which IS the arrow-warp semantic once
    # we are on the tile (`TryArrowWarp` wants stand + face South + HOLD Down). Second arg = the map
    # we are LEAVING.
    yield from _walk_through_warp("Down", VR1F.value)
    yield from wait_until_truly_controllable()
    report["exit_landing"] = _where()
    report["out_of_vr"] = not _on_map(VR1F)
    _take(report, "R9-ARROW")
    if not report["out_of_vr"]:
        raise BotModeError(
            f"Ch23 leg 9: held Down on the arrow warp {F1_EXIT_ARROW} from {F1_EXIT_APRON} and never "
            f"left VICTORY_ROAD_1F — we are at {_where()}. ⛔ `MB_SOUTH_ARROW_WARP` needs the player "
            f"STANDING on the tile FACING South while Down is held; a single step does nothing."
        )
    _take(report, "R9-OUT")

    # ---- ⭐ THE MEASUREMENT THIS LEG EXISTS FOR: where can we actually heal? ---------------------
    from modules.map_path import calculate_path

    here = _here_tile()
    reach = {}
    for label, tile in (("ever_grande_pc_apron", EG_PC_APRON), ("league_door", EG_LEAGUE_DOOR),
                        ("victory_road_door_apron", VR_APRON)):
        try:
            reach[label] = {"to": tile, "wp": len(calculate_path((EG, here), (EG, tile)))}
        except Exception as error:  # noqa: BLE001 - a refusal IS the reading
            reraise_if_aborting(error)
            reach[label] = {"to": tile, "reachable": False, "why": type(error).__name__}
    report["heal_options"] = reach
    _take(report, "R9-WHERECANWEHEAL")


# --------------------------------------------------------------------------------------------
# LEG 10 — walk to the Pokémon League and heal
# --------------------------------------------------------------------------------------------
def party_is_healthy() -> tuple[bool, dict]:
    """`(healthy, reading)` — every battler at full HP and nobody fainted, BY IDENTITY."""
    fainted, hurt, statused, live, total = [], [], [], 0, 0
    for mon in get_party():
        if mon is None or mon.is_egg:
            continue
        total += mon.total_hp
        live += mon.current_hp
        who = f"{mon.species.name}#{mon.personality_value:08X}"
        if mon.current_hp == 0:
            fainted.append(who)
        elif mon.current_hp < mon.total_hp:
            hurt.append(who)
        # ⛔ RECORD STATUS, NOT JUST HP. MEASURED 2026-09-04: the party lost 12 HP across a
        # 36-step walk with `battles=0` — which HP alone cannot explain and POISON can. A reading
        # that only counts HP would have left that as a mystery, and poison on the LAST conscious
        # Pokémon is a whiteout waiting to happen.
        status = getattr(mon, "status_condition", None)
        if status is not None and str(status) not in ("StatusCondition.Healthy", "Healthy", "None"):
            statused.append(f"{who}:{status}")
    reading = {"hp": f"{live}/{total}", "fainted": fainted, "hurt": hurt, "status": statused}
    return (not fainted and not hurt), reading


def heal_at_league(report=None) -> Generator:
    """§Ch23 LEG 10 — walk from the Victory Road exit to the League and heal at its Poké Center.

    ⭐ THIS IS THE ANSWER TO `#24-ch23attrition`, and it replaces a much more expensive one. I had
    priced up to ~5 hours of training as the fix for a party that kept degrading; the actual fix is a
    **37-waypoint walk**, because the League's Poké Center is the only one reachable from the exit.

    ⛔⛔ THREE THINGS THIS LEG MUST NOT DO, each verified against the decomp:
    1. **Never step NORTH from the landing.** `(18,27)` is a WALKABLE non-animated door that warps
       instantly back into Victory Road — one completed step, no button. See
       `EG_VICTORY_ROAD_RETURN_TRAP`.
    2. **Never press A near the guards** at (9,2)/(10,2): it sets `FLAG_ENTERED_ELITE_FOUR`
       permanently and opens step-on doors to the Elite Four.
    3. **Never walk adjacent to the nurse and talk** — she is behind a counter with no walkable
       neighbour. Stand at (3,4) and talk ACROSS it.

    ✅ And what makes it safe to drive with one conscious Pokémon: EVER_GRANDE_CITY has **no
    `land_mons` table at all** and **zero NPCs**, so land encounters and trainers are impossible;
    our own probe measured all 37 waypoints as `Normal` tiles.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    yield from wait_until_truly_controllable()

    healthy_before, before = party_is_healthy()
    report["heal_before"] = before
    # ⛔ ANTI-VACUITY: healing an already-healthy party proves nothing.
    if healthy_before:
        raise BotModeError(
            f"Ch23 leg 10: the party is ALREADY at full health ({before['hp']}) — this leg would "
            f"prove nothing. Start from `post_vr_exit.ss1`."
        )
    if not _on_map(EG):
        raise BotModeError(
            f"Ch23 leg 10: must start in EVER_GRANDE_CITY (leg 9 lands at (18,28)) but we are at "
            f"{_where()}."
        )

    # ---- ⛔ THE TRAP GUARD, ASSERTED NOT ASSUMED --------------------------------------------------
    # Our planner routes around warp tiles (cost 1,000,000), so the plan SHOULD avoid (18,27) —
    # but "should" is not "does", and the cost of being wrong is the whole trip. Check the plan.
    from modules.map_path import calculate_path

    plan = calculate_path((EG, _here_tile()), (EG, LEAGUE_DOOR_APRON))
    crossed = [tuple(getattr(wp, "coordinates", ())) for wp in plan]
    report["plan_wp"] = len(crossed)
    if EG_VICTORY_ROAD_RETURN_TRAP in crossed:
        raise BotModeError(
            f"Ch23 leg 10: the planned route to {LEAGUE_DOOR_APRON} passes through "
            f"{EG_VICTORY_ROAD_RETURN_TRAP}, which is a WALKABLE door back into VICTORY_ROAD_1F — "
            f"stepping on it warps instantly, with a party at {before['hp']}. ⛔ Refusing to walk it."
        )

    yield from _budgeted(
        _navigate_riding_out(EG, LEAGUE_DOOR_APRON), LEAGUE_HEAL_BUDGET, "reach the League door")
    yield from wait_until_truly_controllable()
    report["at_league_apron"] = _here_tile()
    _take(report, "R10-APRON")
    if _here_tile() != LEAGUE_DOOR_APRON:
        raise BotModeError(
            f"Ch23 leg 10: expected to stand on the League door apron {LEAGUE_DOOR_APRON} but we are "
            f"at {_here_tile()}."
        )

    # ---- in through the DOOR: stand beside, face north, HOLD Up ---------------------------------
    yield from _walk_through_warp("Up", EG.value)
    yield from wait_until_truly_controllable()
    report["inside"] = _where()
    _take(report, "R10-INSIDE")
    if not _on_map(LEAGUE_1F):
        raise BotModeError(
            f"Ch23 leg 10: held Up into the League door {LEAGUE_DOOR} from {LEAGUE_DOOR_APRON} and "
            f"did not arrive on LEAGUE_1F — we are at {_where()}. ⛔ `MB_ANIMATED_DOOR` needs a HELD "
            f"north input while FACING north; it has collision 1 and is never stood on."
        )

    # ---- heal ACROSS the counter -----------------------------------------------------------------
    if not _fault("NOHEAL10"):
        # ‼ LOCAL IMPORT: `ensure_facing_direction` is NOT bound at this module's scope — the one
        # other user of it in this file imports it inside its own function too. A module-level
        # reference here would be a NameError on a path only a real drive reaches.
        from modules.modes.util.walking import ensure_facing_direction

        from modules.modes.util import (
            wait_for_no_script_to_run,
            wait_for_player_avatar_to_be_standing_still,
            wait_for_yes_no_question,
        )

        yield from _navigate_riding_out(LEAGUE_1F, LEAGUE_NURSE_STAND)
        yield from wait_until_truly_controllable()
        yield from ensure_facing_direction("Up")
        report["nurse_stand"] = _here_tile()

        # ⛔⛔ THE NURSE ASKS A YES/NO QUESTION, AND MASHING A IS THE WRONG ANSWER TO IT.
        # ‼ MEASURED 2026-09-04: my first version pressed A every other frame for up to 240 tries,
        # polling `party_is_healthy()` between presses. The bot reached (3,4) correctly, faced north
        # correctly, and **healed nothing** — the mash drives the prompt open and shut faster than
        # the heal can run. `heal_in_pokemon_center` has always done it properly
        # (`higher_level_actions.py:337-341`): ONE A, then answer the prompt, then ride the script
        # out. ⇒ **when a proven helper exists for an interaction, copy its SHAPE, not just its
        # intent** — the shape is where the timing knowledge lives.
        yield
        context.emulator.press_button("A")
        yield from wait_for_yes_no_question("Yes")
        yield from wait_for_no_script_to_run("B")
        yield from wait_for_player_avatar_to_be_standing_still("B")
        yield from wait_until_truly_controllable()
    else:
        context.message = "Ch23 FAULT NOHEAL10: skipping the nurse"

    healthy_after, after = party_is_healthy()
    report["heal_after"] = after
    _take(report, "R10-HEALED")
    # ⛔ ASSERT THE CONSEQUENCE, NOT THE INTERACTION. "We pressed A at the nurse" is not "the party
    # is healed" — the same rule that caught KI-84 and the leg-6 heal.
    if not healthy_after:
        raise BotModeError(
            f"Ch23 leg 10: after the League nurse the party is STILL not whole — {after}. "
            f"⛔ Check the bot stood on {LEAGUE_NURSE_STAND} facing NORTH: the nurse is behind a "
            f"counter at (3,2) with no walkable neighbour, and the interaction only works ACROSS it."
        )
    assert_carriers_survived("the League heal")

    # ---- back out: the exit is an ARROW warp — stand ON it and press Down -------------------------
    yield from _navigate_riding_out(LEAGUE_1F, LEAGUE_EXIT_TILE)
    yield from wait_until_truly_controllable()
    yield from _walk_through_warp("Down", LEAGUE_1F.value)
    yield from wait_until_truly_controllable()
    report["back_outside"] = _where()
    report["out"] = _on_map(EG)
    _take(report, "R10-OUT")
    if not report["out"]:
        raise BotModeError(
            f"Ch23 leg 10: pressed Down on the League exit {LEAGUE_EXIT_TILE} and did not return to "
            f"EVER_GRANDE_CITY — we are at {_where()}."
        )


# --------------------------------------------------------------------------------------------
# LEG 11 — stock the League Mart for the Elite Four
# --------------------------------------------------------------------------------------------
def bag_healing_stock() -> dict:
    """What the Items pocket actually holds, by NAME. ⛔ Read the bag, never assume a purchase."""
    from modules.items import get_item_bag

    return {slot.item.name: slot.quantity for slot in get_item_bag().items}


def stock_for_the_elite_four(report=None) -> Generator:
    """§Ch23 LEG 11 — buy the Elite Four's healing at the League Mart.

    ⛔ THE BAG IS THE GAUNTLET'S ONLY HEALING. Five fights, no nurse, sealed doors. Items are legal
    in those battles (verified in the decomp), so what goes in the bag here is what the party has to
    survive on.

    ⭐ The basket deliberately skips **Max Potion**: Hyper Potion's flat 200 HP full-heals every
    member of this party for less than half the price. It also skips Ultra Balls (balls are blocked
    in trainer battles) and Max Repel (no wild encounters past the front door).

    ‼ AND IT BUYS THE LARGEST LINE FIRST, because the shop's quantity cap is recomputed from current
    money on every transaction — buy the small lines first and the big one silently caps low.
    """
    report = report if report is not None else {}
    report.setdefault("readings", set())
    from modules.items import get_item_by_name
    from modules.modes.util.higher_level_actions import buy_in_shop
    from modules.player import get_player

    yield from wait_until_truly_controllable()
    report["money_before"] = getattr(get_player(), "money", None)
    report["bag_before"] = bag_healing_stock()

    # ⛔ REFUSE RATHER THAN UNDER-BUY. The basket is sized to the gauntlet, not to the wallet; if we
    # cannot afford it the right move is to say so loudly, not to quietly buy a thinner one that
    # looks like success. ‼ And the figure is MEASURED at run time — an earlier plan was written
    # against ₽38,893, which was the pre-Victory-Road number and ₽17,148 short of the truth.
    if report["money_before"] is None or report["money_before"] < LEAGUE_MIN_MONEY:
        raise BotModeError(
            f"Ch23 leg 11: the basket costs ₽{LEAGUE_MIN_MONEY:,} but we hold "
            f"₽{report['money_before']}. ⛔ Refusing to buy a thinner basket silently — the Elite "
            f"Four has no other healing, so an under-stocked bag is a run that fails five fights "
            f"later for a reason nobody will connect to this moment."
        )

    if not _on_map(LEAGUE_1F):
        if not _on_map(EG):
            raise BotModeError(
                f"Ch23 leg 11: must start in EVER_GRANDE_CITY or the League but we are at {_where()}."
            )
        if _here_tile() != LEAGUE_DOOR_APRON:
            yield from _budgeted(_navigate_riding_out(EG, LEAGUE_DOOR_APRON),
                                 LEAGUE_SHOP_BUDGET, "reach the League door")
            yield from wait_until_truly_controllable()
        yield from _walk_through_warp("Up", EG.value)
        yield from wait_until_truly_controllable()
    if not _on_map(LEAGUE_1F):
        raise BotModeError(f"Ch23 leg 11: failed to enter the League — we are at {_where()}.")
    _take(report, "R11-INSIDE")

    # ---- talk to the clerk ACROSS the counter, exactly as with the nurse -------------------------
    # ‼ BOTH IMPORTS ARE FUNCTION-LOCAL ON PURPOSE, and forgetting the second one cost a drive:
    # `wait_for_no_script_to_run` is imported inside leg 10, NOT at module scope, so referencing it
    # here raised `NameError` on the first run. ⇒ **a helper another function imported locally is
    # NOT available to yours** — this is the third time that shape has bitten in this file
    # (`os as _os`, `pathlib`, and now this).
    from modules.modes.util import wait_for_n_frames
    from modules.modes.util.walking import ensure_facing_direction

    yield from _navigate_riding_out(LEAGUE_1F, LEAGUE_MART_STAND)
    yield from wait_until_truly_controllable()
    yield from ensure_facing_direction("Up")
    report["clerk_stand"] = _here_tile()
    if _fault("NOBUY"):
        context.message = "Ch23 FAULT NOBUY: skipping the purchase"
        _take(report, "R11-MENU")
        _take(report, "R11-BOUGHT")
    else:
        # ⛔⛔ OPENING A SHOP IS NOT ONE A-PRESS, AND IT IS NOT THE NURSE'S SHAPE EITHER.
        # ‼ MEASURED 2026-09-04: a single A followed by `wait_for_no_script_to_run` reached the
        # clerk and then died on *"Cannot buy things in mart because `Task_ShopMenu` is not active"*.
        # The clerk has intro dialogue that needs SEVERAL presses, and the thing to wait on is a
        # TASK, not the absence of a script.
        # ⭐ `buy_poke_balls` (`early_game.py:2179-2199`) supplies the SHAPE: press A on a cadence
        # until the menu task is up, bounded. ⛔ But NOT its target task — see the comment on the
        # wait below. ⇒ **THIS IS THE SECOND TIME TODAY THE FIX WAS "COPY THE PROVEN HELPER'S
        # SHAPE"** — the nurse taught it, and I still hand-rolled the next menu.
        # ⇒ *when an interaction already has a working caller in this repo, read that caller FIRST.*
        from modules.modes.util.tasks_scripts import task_is_active

        context.emulator.press_button("Up")
        yield
        yield from wait_for_n_frames(6)
        opened = False
        for _ in range(60):
            _check_abort()
            # ⛔ WAIT FOR **`Task_ShopMenu`** — the task `buy_in_shop` ACTUALLY checks
            # (`higher_level_actions.py:607,613`). ‼ My first fix copied `buy_poke_balls`'s target
            # tasks (`Task_GoToBuyOrSellMenu`/`Task_BuyMenu`) and still failed, because that helper
            # DRIVES THE MENU BY HAND and never calls `buy_in_shop` — so its shape is right for
            # advancing the clerk's dialogue and wrong for the task to wait on.
            # ⇒ **COPY THE SHAPE FROM A SIBLING, BUT TAKE THE CONTRACT FROM THE CALLEE.**
            if task_is_active("Task_ShopMenu"):
                opened = True
                break
            context.emulator.press_button("A")
            yield from wait_for_n_frames(10)
        report["shop_menu_open"] = opened
        if not opened:
            raise BotModeError(
                # ⛔⛔ THE MESSAGE MUST NAME THE TASK THE LOOP ACTUALLY WAITED FOR. It said
                # `Task_GoToBuyOrSellMenu` — a task this code never watches — for one commit, left
                # behind when the wait was corrected to `Task_ShopMenu`. ⇒ a debugger would have
                # grepped for the wrong symbol and concluded the check was absent.
                # ‼ THE FAILURE MESSAGE IS PART OF THE FIX, NOT COMMENTARY ON IT: when you change
                # what a guard checks, change what its refusal SAYS in the same edit.
                f"Ch23 leg 11: stood at {LEAGUE_MART_STAND} facing north and pressed A 60 times "
                f"without `Task_ShopMenu` ever becoming active — that is the task `buy_in_shop` "
                f"requires (`higher_level_actions.py:607`). ⛔ The clerk is at (16,2) behind a "
                f"counter at (16,3) — check we are on the right tile and facing NORTH."
            )
        _take(report, "R11-MENU")

        yield from _budgeted(
            buy_in_shop([(get_item_by_name(name), qty) for name, qty in LEAGUE_BASKET]),
            LEAGUE_SHOP_BUDGET, "buy the Elite Four basket",
        )
        yield from wait_until_truly_controllable()
        _take(report, "R11-BOUGHT")

    # ---- ⛔ ASSERT THE CONSEQUENCE: is the basket actually IN THE BAG? ---------------------------
    after = bag_healing_stock()
    report["bag_after"] = after
    report["money_after"] = getattr(get_player(), "money", None)
    missing = {name: qty for name, qty in LEAGUE_BASKET if after.get(name, 0) < qty}
    report["basket_shortfall"] = missing
    _take(report, "R11-VERIFIED")
    if missing:
        raise BotModeError(
            f"Ch23 leg 11: the purchase did not land. Short: {missing}. Bag now: {after}. "
            f"Money {report['money_before']} → {report['money_after']}. ⛔ 'buy_in_shop returned' is "
            f"not 'the items are in the bag' — and the Elite Four has no second chance to notice."
        )

    # ---- back out ---------------------------------------------------------------------------------
    yield from _navigate_riding_out(LEAGUE_1F, LEAGUE_EXIT_TILE)
    yield from wait_until_truly_controllable()
    yield from _walk_through_warp("Down", LEAGUE_1F.value)
    yield from wait_until_truly_controllable()
    report["back_outside"] = _where()
    report["out"] = _on_map(EG)
    _take(report, "R11-OUT")
    if not report["out"]:
        raise BotModeError(
            f"Ch23 leg 11: pressed Down on the League exit and did not return to EVER_GRANDE_CITY — "
            f"we are at {_where()}."
        )
