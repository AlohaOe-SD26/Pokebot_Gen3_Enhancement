"""§Ch21 — SOOTOPOLIS and RAYQUAZA. **LEGS 1 and 2a so far: the dive in, and Steven's escort.**

⛔ THIS CHAPTER IS INCOMPLETE AND MUST NOT BE WIRED INTO `_play()` YET. Leg 1 (ROUTE128 → the
underwater route → surfacing inside the crater) and leg 2a (heal → Steven → the escort into the
Cave of Origin Entrance) are built; legs 2b-5 (the Cave of Origin descent + Wallace, the Sky
Pillar climb, HM07 from BOTH Maxie AND Archie) are NOT. Read the **§Ch21 ATLAS** in
`PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md` AND the leg-2 build spec + its probe addendum
(`ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md`) before adding to this file — every
coordinate below came from there, and both state their provenance per row.

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


# --- LEG 2a CONSTANTS — every one LIVE-VERIFIED 2026-08-27 by `--driver ch21leg2probe` -----------
# (spec: ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md §1 + its probe ADDENDUM)
STEVEN_TILE = (20, 36)      # object_event 7 of 18 in the ROM template; local_id 7 MEASURED live
#: ⛔ These two are the ONLY escort-handled facings — `SootopolisCity/scripts.inc:903-904` has a
#: DIR_WEST arm and a DIR_NORTH arm and NOTHING else (no east, no south, no default). Both tiles
#: pathed live from the arrival tile (27 wp) AND from the post-heal tile (30 wp).
STEVEN_APPROACHES = (((21, 36), "Left"), ((20, 37), "Up"))


def steven_escort_done() -> bool:
    """Leg 2a's completion flag — the game's OWN record that the escort ran.

    ‼ ONE writer repo-wide (`setflag` at `SootopolisCity/scripts.inc:918`, inside the escort
    itself — whole-decomp-grep verified in the leg-2 spec). ⛔ A misspelled name here would read
    False FOREVER (`memory.py:336`), which is exactly the input a retry loop keys on — the name
    below is verified against `modules/data/event_flags/emerald.txt:255` and the standing
    `audit_flag_names` gate covers this file.
    """
    from modules.memory import get_event_flag

    return bool(get_event_flag("STEVEN_GUIDES_TO_CAVE_OF_ORIGIN"))


def _ride_steven_escort(approach_tile: tuple[int, int], budget_frames: int = 30000) -> Generator:
    """Ride Steven's escort cutscene to its warp. Returns True on arrival, False if the A-press
    MISSED (nothing engaged — the caller retries the next approach), raises on a real stall.

    Success = the flag AND the Entrance map AND controllable — ALL THREE. The `setflag` sits at
    `scripts.inc:918`, three lines BEFORE the `warp` (`:921`), so the flag alone is true for a
    stretch while the cutscene still runs; and this module already owns the general lesson
    ("we are on the map" is NOT "we have arrived", `_ride_arrival_scene` above).

    ⛔⛔ THE MISSED-PRESS BAIL IS SCRIPT-STACK-BASED, AND THE FIRST VERSION COST A DRIVE (2026-08-27).
    v1 bailed on `controllable at frame 400` — which read True MID-ESCORT, returned False while the
    scene was RUNNING, and the caller's `_navigate_riding_out` then rode the rest of the escort as
    an "interruption" and PATHED BACK from the Entrance into the city (through the (9,20) return
    warp — the pocket is open post-escort), un-doing the story warp. The honest "nothing engaged"
    discriminator is: flag clear AND the global script stack EMPTY AND still standing on the
    approach tile — held for 60 CONSECUTIVE frames inside the first 600.

    ⛔ The A/B gating below is SAFE **for this scene specifically**: the escort is msgbox +
    applymovement only — no menu anywhere (`scripts.inc:900-923`, all four recon angles agree) —
    so a B cannot cancel anything. ⛔ Do NOT copy this rider to the Wallace multichoice in leg 2b:
    there, B cancels into a no-escape re-arm loop (spec §3.2) and the word "B" must not appear.
    """
    from modules.modes import BotModeError
    from modules.player import player_avatar_is_controllable
    from modules.story.early_game import _check_abort
    from modules.tasks import get_global_script_context, is_waiting_for_input

    frames = 0
    idle_streak = 0
    while frames < budget_frames:
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try (loop-head abort rule)
        if (
            steven_escort_done()
            and _on_map(MapRSE.CAVE_OF_ORIGIN_ENTRANCE)
            and player_avatar_is_controllable()
        ):
            context.message = f"Story: Ch21 — Steven's escort done in ~{frames} frames."
            return True
        if frames < 600 and not steven_escort_done():
            # ⛔⛔ `.is_active`, NEVER `bool(.stack)` — v2 of this bail used the latter and was
            # DEAD CODE: `ScriptContext.stack_pointers` unconditionally appends the bytecode
            # pointer (`tasks.py:147`), so `.stack` is NEVER empty and the bail could never fire
            # (an adversarial review caught it; every other call site in the tree gates on
            # `.is_active` first — `main.py:83` is the idiom).
            try:
                ctx = get_global_script_context()
                script_running = ctx is not None and ctx.is_active
            except Exception:  # noqa: BLE001 - an unreadable context must not kill the ride
                script_running = True  # assume engaged; the budget still bounds us
            if not script_running and _at(MapRSE.SOOTOPOLIS_CITY, approach_tile):
                idle_streak += 1
                if idle_streak >= 60:
                    # ‼ PRINTED, not only context.message — the harness does not echo message
                    # assignments, and this branch's firing IS the evidence the fault arm exists
                    # to capture (instrument the ACTION, never only the outcome).
                    from modules.console import console

                    console.print(
                        f"[yellow]Story: Ch21 — the A-press at {approach_tile} MISSED "
                        f"(no script for {idle_streak} consecutive frames, frame {frames}); "
                        f"retrying the next approach.[/]"
                    )
                    return False  # nothing engaged for a full second — the A-press missed
            else:
                idle_streak = 0
        context.emulator.press_button("A" if is_waiting_for_input() else "B")
        yield
        frames += 1

    raise BotModeError(
        f"Ch21 leg 2a: rode the escort for {budget_frames} frames without arriving — "
        f"flag={steven_escort_done()} at={_where()} state={_var('SOOTOPOLIS_CITY_STATE')!r}. "
        "The escort is one msgbox/applymovement chain, so a stall here is a real wedge, not slowness."
    )


def steven_escort() -> Generator:
    """LEG 2a — heal, find Steven, take his escort into the Cave of Origin Entrance.

    End state (the spec §2 predicate, all three conjuncts):
    `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` set AND on `CAVE_OF_ORIGIN_ENTRANCE` AND controllable.
    The decomp lands the player on Entrance (9,20) — REPORTED by the caller/driver, not asserted
    here (the warp coord is script-fixed, but this module's own rule is that the game owns the
    landing tile).

    ⛔ THE ESCORT FIRES EXACTLY ONCE, EVER (spec §3.1): its gate is `call_if_unset` on the flag,
    and after it the same A-press yields three frames of dialogue. So: flag already set = the leg
    is SPENT — return immediately, never re-approach; and a retry loop must never cross this
    function's success.
    """
    from modules.map_data import PokemonCenter
    from modules.memory import get_event_flag
    from modules.modes import BotModeError
    from modules.modes.util.higher_level_actions import heal_in_pokemon_center
    from modules.modes.util.walking import ensure_facing_direction
    from modules.pokemon_party import get_party
    from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable
    from modules.story.space_center import _npc_is_on

    yield from wait_until_truly_controllable()

    # --- 0. PREFLIGHT — refuse loudly here, not deep in a cutscene -------------------------------
    if steven_escort_done():
        context.message = "Story: Ch21 — Steven's escort already ran (flag set); leg 2a is done."
        return
    if not _on_map(MapRSE.SOOTOPOLIS_CITY):
        raise BotModeError(f"Ch21 leg 2a: not in Sootopolis — at {_where()}.")
    state = _var("SOOTOPOLIS_CITY_STATE")
    if state != 2:
        raise BotModeError(
            f"Ch21 leg 2a: SOOTOPOLIS_CITY_STATE is {state!r}, expected exactly 2 (arrival scene "
            "finished, escort not yet run). State 1 = the arrival cutscene is still running; "
            "state >= 3 with the flag clear should be impossible and needs eyes."
        )
    if get_event_flag("HIDE_SOOTOPOLIS_CITY_STEVEN"):
        raise BotModeError(
            "Ch21 leg 2a: HIDE_SOOTOPOLIS_CITY_STEVEN is SET — Steven is not spawned, the escort "
            "cannot be started. This is not a state the walkthrough reaches; investigate the save."
        )
    before = [(m.personality_value, m.current_hp, m.total_hp) for m in get_party() if m is not None]

    # --- 1. HEAL — the fixture's own inventory says a fainted member + a 2-HP lead is the honest
    # post-arrival state, and both cave maps ahead carry live encounters. PROVEN on this exact PC
    # by the probe: exits at (43,32), every PID full, (21,36) still paths (30 wp). ----------------
    context.message = "Story: Ch21 — healing at the Sootopolis Poke Center before finding Steven."
    # ⚠ FORWARD NOTE (review 2026-08-27): the heal's three PC piggybacks are no-ops here today
    # (rotation pinned 0; no `_needs_party_slot`/`_hunted_counter_pids` on this path) — but if a
    # future chapter wiring reuses a mode instance carrying `_needs_party_slot=True`, the heal
    # could LEGITIMATELY deposit a member and the by-PID assert below would raise on every retry.
    # If that assert ever fires with a "missing" PID, check those piggybacks before this code.
    yield from heal_in_pokemon_center(PokemonCenter.SootopolisCity)
    after = {m.personality_value: (m.current_hp, m.total_hp) for m in get_party() if m is not None}
    not_full = [pid for pid, _, _ in before if pid in after and after[pid][0] != after[pid][1]]
    missing = [pid for pid, _, _ in before if pid not in after]
    if not_full or missing:
        raise BotModeError(
            f"Ch21 leg 2a: the heal returned but the party is not whole — not_full={not_full} "
            f"missing={missing}. `heal_in_pokemon_center` asserts nothing itself; this check is "
            "the acceptance, by PID, never by slot or count."
        )

    # --- 2. APPROACH AND TALK — explicit approach list, NOT `talk_to_npc` (the spec's reasoned
    # choice: no inferred local_id dependency, auditable tile+facing in the log). ----------------
    import os as _os_fault

    fault_miss = _os_fault.environ.get("POKEBOT_CH21_FAULT_MISS", "").strip() == "1"
    for index, (approach, facing) in enumerate(STEVEN_APPROACHES):
        context.message = f"Story: Ch21 — approaching Steven via {approach} facing {facing}."
        yield from _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, approach, tries=6)
        yield from wait_until_truly_controllable()
        if not _npc_is_on(MapRSE.SOOTOPOLIS_CITY, STEVEN_TILE):
            raise BotModeError(
                f"Ch21 leg 2a: standing at {approach} but NO live object is on {STEVEN_TILE}. "
                "The preflight said he is spawned, so either the walk drifted out of camera range "
                "of his tile (unlikely from an adjacent tile) or the map state changed under us."
            )
        if fault_miss and index == 0:
            # ‼ FAULT INJECTION (POKEBOT_CH21_FAULT_MISS=1, driver-proof only): face AWAY so the
            # A lands on nothing — the arm that proves the missed-press bail returns False fast
            # and the loop recovers via approach 2. An adversarial review required this arm: the
            # happy path cannot exercise the bail, and v2's bail shipped dead without it.
            yield from ensure_facing_direction("Down")
        else:
            yield from ensure_facing_direction(facing)
        context.emulator.press_button("A")
        yield
        if (yield from _ride_steven_escort(approach)):
            break
        # ride returned False = the A-press missed; loop to the other handled approach.
        # ⛔ DEFENSE-IN-DEPTH (the v1 drive's exact cascade): if the flag SET while the bail said
        # "missed", the bail lied and the scene ran — navigating now would let
        # `_navigate_riding_out` walk BACK through the (9,20) return warp and un-do the story
        # warp. Refuse loudly instead of compounding.
        if steven_escort_done():
            raise BotModeError(
                f"Ch21 leg 2a: the ride reported a missed press but the escort flag IS SET — "
                f"at {_where()}. The scene ran (or is running) behind the bail's back; do not "
                "navigate. Reload the fixture and investigate the bail discriminator."
            )
    else:
        raise BotModeError(
            "Ch21 leg 2a: both handled approaches ((21,36) Left, (20,37) Up) pressed A without "
            "engaging the escort. The script only dispatches DIR_WEST/DIR_NORTH, so if this "
            "raises, verify facing actually latched (log the avatar facing) before re-driving."
        )

    context.message = f"Story: Ch21 — Steven's escort complete; at {_where()} (leg 2a done)."
