"""§Ch21 — SOOTOPOLIS and RAYQUAZA. **LEG 1 ONLY so far: the dive into Sootopolis.**

⛔ THIS CHAPTER IS INCOMPLETE AND MUST NOT BE WIRED INTO `_play()` YET. Leg 1 (ROUTE128 → the
underwater route → surfacing inside the crater) is built and driven; legs 2-5 (Steven's escort, the
Cave of Origin, the Sky Pillar climb, HM07 from BOTH Maxie AND Archie) are NOT. Read the **§Ch21
ATLAS** in `PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md` before adding to this file — every coordinate
below came from there, and the atlas states its provenance per row.

‼ WHY LEG 1 IS ITS OWN THING. §Ch20's method (playbook §4c) is *incremental drivers that INHERIT*:
each leg is driven standalone, and the chapter is the ASSEMBLY of proven ingredients. Writing all
five legs before driving one is how §Ch20's orchestration glue accumulated four review blockers.

⛔⛔ THE TRAPS ON THIS LEG SPECIFICALLY.

 1. KI-72, AND IT IS SHARPER HERE THAN IN THE CAVERN. `UNDERWATER_SOOTOPOLIS_CITY` contains **ZERO**
    `Underwater Blocked Above` / `Seaweed No Surfacing` tiles, so `surface_from_dive()`'s own guard —
    which checks ONLY the underwater tile type — can never fire on this map. But of its 31 non-warp
    walkable tiles, **only SIX emerge onto non-blocked ground**: (7,5) (6,6) (7,6) (9,7) (14,7)
    (14,8). The other 25 sit under the crater wall. **The game will not stop a bad surface here.**
    Measured 2026-08-24 by decoding `data/layouts/{Underwater_SootopolisCity,
    SootopolisCity_LegendsBattle}/map.bin`; `Emerge` preserves (x,y), so the underwater tile IS the
    city tile. ⇒ the tile is HARD-CODED and asserted, never planned.

 2. THE ARRIVAL TILE WARPS STRAIGHT BACK. `UNDERWATER_SOOTOPOLIS_CITY (9,8)` — where the Route 126
    warp lands you — is `Water South Arrow Warp` back to `UNDERWATER_ROUTE126`, as is `(10,8)`.
    ✅ Stepping NORTH off it is safe: an arrow warp fires only while its own direction is HELD
    (`TryArrowWarp` is guarded on `input->heldDirection`), and this one points SOUTH. The emerge tile
    `(9,7)` is exactly one step north — the map is built so the two are adjacent.

 3. SOOTOPOLIS IS A TRUE ISLAND — region 1, ALONE, zero map connections (our own ROM-extracted
    `cache/warp_graph_BPEE0.json`). There is no walking or surfing in or out, and **no Fly either**:
    `VISITED_SOOTOPOLIS_CITY` is False (measured on both anchors,
    `evidence/2026-08-24-ch21-prereq-flags.txt`). Diving is the ONLY door, in both directions.

 4. ⛔ SOOTOPOLIS_CITY IS LAYOUT-SWAPPED AT RUNTIME. At `SOOTOPOLIS_CITY_STATE` 1-4 the map is
    `LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE`, not its header default. **Any static tile read of that
    city describes a map the bot never sees.** (Two of this chapter's other regions swap too —
    ROUTE131 unconditionally, and every Sky Pillar floor below `SKY_PILLAR_STATE` 2.)

‼ GRADING. The chapter's completion flag is `RECEIVED_HM_WATERFALL` (`chapters.py`), which is NOT
this leg. Leg 1's own acceptance is: standing on `SOOTOPOLIS_CITY`, controllable, having arrived by
Dive. ⛔ `SOOTOPOLIS_CITY_STATE` does NOT advance on arrival alone — the arrival CUTSCENE moves it
1 → 2, and it fires from `OnFrame` with no coordinate condition, so expect an immediate `lockall`.

⛔ NAMES ARE BARE. `SOOTOPOLIS_CITY_STATE`, never the decomp's `VAR_SOOTOPOLIS_CITY_STATE` —
`get_event_var` returns **−1** for an unknown name, so the prefixed spelling fails SILENTLY and reads
as "not done yet". (Playbook §4.2. This bit §Ch20 the day before this file was written.)
"""

from typing import Generator

from modules.context import context
from modules.map_data import MapRSE

# ‼ IMPORTED, NOT RE-IMPLEMENTED. `seafloor_cavern`'s transcription rule A says a hand-rolled map
# comparison is the bug: `_where()` returns a (group, number) TUPLE in this package and a NAME STRING
# in the harness, so `where[0] == "SOOTOPOLIS_CITY"` is silently ALWAYS FALSE. `_on_map()` also
# guards the case where `_where()` returns a reason string (indexing which yields a character that
# likewise compares unequal forever). Re-deriving these would re-earn that defect.
from modules.story.seafloor_cavern import _at, _on_map, _var, _where

# --- LEG 1 CONSTANTS — every one verified live from `saves/post_ch20.ss1` on 2026-08-24 -----------
# evidence: the §Ch21 ATLAS table + evidence/2026-08-24-ch21-topology-probe.stdout.txt
DIVE_TILE = (45, 66)          # ROUTE126, tile_type 'Deep Water' — 1 tile south of the warp column
SOOTOPOLIS_DOOR = (45, 65)    # UNDERWATER_ROUTE126: its ONLY warp, -> UNDERWATER_SOOTOPOLIS_CITY
UW_ARRIVAL = (9, 8)           # where that warp lands. ⛔ 'Water South Arrow Warp' — warps BACK
UW_EMERGE = (9, 7)            # the hand-picked surfacing tile (KI-72). 'Deep Water', collision 0.
# ⛔ THERE IS DELIBERATELY NO `CITY_ARRIVAL` CONSTANT. An earlier draft had `CITY_ARRIVAL = (9,7)`
# reasoning that `Emerge` preserves (x,y) -- which is TRUE of the emerge itself and IRRELEVANT to
# where the run ends up, because the ARRIVAL CUTSCENE then warps the player. The first drive landed
# on `(29,53)` mid-scene. ‼ THE GAME CHOOSES THIS TILE, SO WE MEASURE IT; hard-coding a predicted
# coordinate is how a fabricated constant gets shipped (see `ROOM8_PUSHES`, 08-MISTAKES 2026-08-24).


def sootopolis_reached() -> bool:
    """Leg 1's completion test: we are standing in Sootopolis City."""
    return _on_map(MapRSE.SOOTOPOLIS_CITY)


def ch21_done() -> bool:
    """The WHOLE chapter's grading flag — ⛔ not leg 1's."""
    from modules.memory import get_event_flag

    return bool(get_event_flag("RECEIVED_HM_WATERFALL"))


def assert_ch21_preflight() -> None:
    """Refuse loudly, BEFORE any travel, if this leg cannot possibly succeed.

    ‼ Each check below is a state that would otherwise fail deep in a dive with a confusing symptom.
    """
    from modules.modes import BotModeError
    from modules.player import AvatarFlags, get_player_avatar

    state = _var("SOOTOPOLIS_CITY_STATE")
    if not isinstance(state, int) or state < 1:
        raise BotModeError(
            f"Ch21 preflight: SOOTOPOLIS_CITY_STATE is {state!r}, expected >= 1. That var is set in "
            "the SAME Seafloor Cavern block as ROUTE128_STATE, so a value below 1 means §Ch20 has "
            "not run — Sootopolis's arrival scene would not fire and the chapter cannot start."
        )
    if AvatarFlags.Underwater in get_player_avatar().flags:
        raise BotModeError(
            f"Ch21 preflight: the run is already UNDERWATER at {_where()}. This leg dives from the "
            "surface and does not know how to recover from that — surface manually first."
        )


def _ride_arrival_scene(budget_frames: int = 30000) -> Generator:
    """Ride the Sootopolis ARRIVAL CUTSCENE out until it has actually finished.

    ⛔ WHY THIS EXISTS, MEASURED NOT GUESSED. Leg 1's first drive reported
    `reached=True at=SOOTOPOLIS_CITY(29,53) state=1 ACCEPTANCE: FAIL`, and the harness log showed
    `scripts=['SootopolisCity_EventScript_LegendariesSceneFromDive']` STILL RUNNING at f18014.
    `SootopolisCity_OnFrame` fires `map_script_2 VAR_SOOTOPOLIS_CITY_STATE, 1, ...StartLegendariesScene`
    the instant the map is live -- with NO coordinate condition -- and that scene sets the var to 2
    only at its END (`SootopolisCity/scripts.inc:243` / `:342`) after warping the player around.
    ⇒ "we are on the map" is NOT "we have arrived". Grade on the VAR, never on the map.

    ⛔ THE BUTTON IS GATED, NOT MASHED -- `A` only when a printer is waiting, else `B`. Copied from
    `seafloor_cavern._ride_until`, which earned that rule when a mashing version re-introduced the
    museum-greeter bug. (That helper could not be reused directly: its whiteout guard hard-codes
    Ch20's maps.)
    """
    from modules.modes import BotModeError
    from modules.story.early_game import _check_abort
    from modules.tasks import is_waiting_for_input

    frames = 0
    while frames < budget_frames:
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try (loop-head abort rule)
        state = _var("SOOTOPOLIS_CITY_STATE")
        if isinstance(state, int) and state >= 2:
            return
        where = _where()
        if isinstance(where, tuple) and where[0] != MapRSE.SOOTOPOLIS_CITY.value:
            raise BotModeError(
                f"Ch21: while riding the arrival scene the run LEFT Sootopolis and is at {where}. "
                "Sootopolis has zero map connections, so the only ways out are a Dive warp or a "
                "whiteout -- and the party arrives here with a fainted member."
            )
        context.emulator.press_button("A" if is_waiting_for_input() else "B")
        yield
        frames += 1

    raise BotModeError(
        f"Ch21: rode the arrival cutscene for its full budget of {budget_frames} frames without "
        f"SOOTOPOLIS_CITY_STATE reaching 2 -- it is {_var('SOOTOPOLIS_CITY_STATE')!r}, at {_where()}."
    )


def enter_sootopolis() -> Generator:
    """LEG 1 — ROUTE128 → surf to ROUTE126 → dive → warp → step off → surface INSIDE the crater.

    ⛔ The surf leg is a SINGLE `navigate_to`: Routes 126/127/128 are all one region, and
    `calculate_path` spans only DIRECTLY CONNECTED maps (playbook §4.6). Measured live from
    `post_ch20.ss1`: `ROUTE128 (38,24) -> ROUTE126 (45,66)` = 147 waypoints, OK.
    """
    from modules.map import get_map_data_for_current_position
    from modules.modes import BotModeError
    from modules.modes.util.higher_level_actions import dive, surface_from_dive
    from modules.modes.util.walking import navigate_to
    from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

    assert_ch21_preflight()
    yield from wait_until_truly_controllable()

    # --- 1. surf to the dive tile ----------------------------------------------------------------
    context.message = "Story: Ch21 — surfing to the Route 126 dive point."
    yield from _navigate_riding_out(MapRSE.ROUTE126, DIVE_TILE)
    if not _at(MapRSE.ROUTE126, DIVE_TILE):
        raise BotModeError(f"Ch21: could not reach the dive tile {DIVE_TILE} on Route 126 — at {_where()}.")

    # ⛔ Assert the tile is divable BEFORE calling dive(). `dive()` raises on a bad tile, but its
    # message is about the avatar; this one names the coordinate a future reader has to fix.
    tile_type = getattr(get_map_data_for_current_position(), "tile_type", None)
    if tile_type not in ("Deep Water", "Interior Deep Water", "Semi-Deep Water", "Sootopolis Deep Water"):
        raise BotModeError(
            f"Ch21: refusing to dive at ROUTE126 {DIVE_TILE} — its tile_type is {tile_type!r}, "
            "which `dive()` does not accept."
        )

    # --- 2. dive, and cross to the Sootopolis door -----------------------------------------------
    yield from dive()
    # ⛔ run=False underwater — the same choice §Ch20's dive leg made and drove.
    yield from navigate_to(MapRSE.UNDERWATER_ROUTE126, SOOTOPOLIS_DOOR, False)

    # --- 3. we should now be through the warp, inside the crater's underwater map ----------------
    if not _on_map(MapRSE.UNDERWATER_SOOTOPOLIS_CITY):
        raise BotModeError(
            f"Ch21: took the {SOOTOPOLIS_DOOR} warp but did not land in UNDERWATER_SOOTOPOLIS_CITY "
            f"— at {_where()}. That warp is the map's ONLY one, so this means the walk never "
            "reached it."
        )

    # --- 4. ⛔ STEP OFF THE ARRIVAL TILE BEFORE SURFACING ----------------------------------------
    # (9,8) and (10,8) are `Water South Arrow Warp` back to Route 126. Surfacing is fine here in
    # principle, but the tile ABOVE (9,8) in the city is the crater WALL — see KI-72 note above.
    yield from navigate_to(MapRSE.UNDERWATER_SOOTOPOLIS_CITY, UW_EMERGE, False)
    if not _at(MapRSE.UNDERWATER_SOOTOPOLIS_CITY, UW_EMERGE):
        raise BotModeError(
            f"Ch21: could not reach the surfacing tile {UW_EMERGE} — at {_where()}. It is ONE step "
            f"north of the arrival tile {UW_ARRIVAL}; failing that usually means the warp-back fired."
        )

    # --- 5. KI-72: assert the surfacing tile, because the GAME will not ---------------------------
    tile_type = getattr(get_map_data_for_current_position(), "tile_type", None)
    if tile_type != "Deep Water":
        raise BotModeError(
            f"Ch21 (KI-72): refusing to surface at {UW_EMERGE} — its tile_type is {tile_type!r}, "
            "not 'Deep Water'. ⛔ This map has ZERO 'Underwater Blocked Above' tiles, so "
            "`surface_from_dive()`'s own guard CANNOT fire here: 25 of its 31 walkable tiles emerge "
            "under the crater wall and nothing but this assertion stands between the run and one."
        )

    yield from surface_from_dive()
    if not _on_map(MapRSE.SOOTOPOLIS_CITY):
        raise BotModeError(f"Ch21: surfaced but did not arrive in SOOTOPOLIS_CITY — at {_where()}.")

    # --- 6. ⛔ RIDE THE ARRIVAL CUTSCENE OUT. Being on the map is NOT having arrived. ------------
    context.message = "Story: Ch21 — surfaced in Sootopolis; riding the legendaries arrival scene."
    yield from _ride_arrival_scene()

    state = _var("SOOTOPOLIS_CITY_STATE")
    if not isinstance(state, int) or state < 2:
        raise BotModeError(
            f"Ch21: the arrival scene returned but SOOTOPOLIS_CITY_STATE is {state!r}, not >= 2."
        )
    context.message = f"Story: Ch21 — arrived in Sootopolis (state {state}) at {_where()}."
