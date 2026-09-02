"""§Ch21 — SOOTOPOLIS and RAYQUAZA. **LEGS 1, 2 (2a+2b) AND 3: dive in, escort, Wallace, approach.**

⛔ THIS CHAPTER IS INCOMPLETE AND MUST NOT BE WIRED INTO `_play()` YET. Leg 1 (the dive in),
leg 2a (heal → Steven → the escort), leg 2b (the Cave of Origin descent → Wallace →
SOOTOPOLIS_CITY_STATE=3) and leg 3 (`approach_sky_pillar` — the cave return, the pocket, the heal,
the dive out, the six-map swim and the hand-walked approach to the Sky Pillar door) are built;
legs 4-5 (the Sky Pillar CLIMB, Rayquaza, HM07 from BOTH Maxie AND Archie) are NOT.
‼ THE POCKET EXIT IS NO LONGER THE OPEN RISK — it was MEASURED on 2026-08-27 (`--driver
ch21pocket`) and leg 3 now owns it. The remaining UNPROVEN mechanic in this file is the SURF
DISMOUNT inside leg 3's hand-walked tail, and `DOOR_APPROACH_FALLBACK` exists for it.
Read the **§Ch21 ATLAS** in
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
    `cache/warp_graph_BPEE0.json`). There is no walking or surfing in or out, and **no Fly either** —
    ⛔ BUT NOT FOR THE REASON THIS TRAP USED TO GIVE. It said "`VISITED_SOOTOPOLIS_CITY` is False";
    that reading was CORRECT FOR THE ANCHOR IT WAS TAKEN ON and is now out of era. Measured
    2026-09-01 across all four §Ch21 anchors: `post_ch20` (pre-arrival) False, and
    `post_sootopolis_arrival` / `post_steven_escort` / `post_wallace` all **True** —
    `SootopolisCity_OnTransition` sets it on first arrival. ⇒ from leg 1 onward the flag does NOT
    rule Fly out. What rules it out is that **no party member knows Fly** (measured False on
    `post_wallace.ss1`). Diving is still the ONLY door in both directions, but leg 5's return
    planning must not inherit the old reason.

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


# --- LEG 2b CONSTANTS — spec §1 steps 5-10, coordinates SURVIVED adversarial verification --------
ENTRANCE_TO_1F = (9, 5)       # Entrance: straight 5-wide shaft up x=9; warp -> 1F, land (11,17)
ONEF_TO_B1F = (14, 5)         # 1F: warp -> B1F, land (9,3)
WALLACE_TILE = (9, 13)        # B1F's ONLY object_event; MOVEMENT_TYPE_FACE_UP; never respawns (§3.6)
#: ⛔ (9,12) — directly north of Wallace — is a COLLISION WALL (metatile 816 coll 1), never an
#: approach. The three below are measured 21/19/19 steps from the (9,3) arrival.
WALLACE_APPROACHES = (((9, 14), "Up"), ((8, 13), "Right"), ((10, 13), "Left"))
MULTI_WHERES_RAYQUAZA = 110   # include/constants/script_menu.h:121 — the menu identity to assert


def wallace_sent_to_sky_pillar() -> bool:
    """Leg 2b's corroborating flag — single writer repo-wide (the AtSkyPillar branch)."""
    from modules.memory import get_event_flag

    return bool(get_event_flag("WALLACE_GOES_TO_SKY_PILLAR"))


def _answer_wallace_multichoice(budget_frames: int = 12000) -> Generator:
    """Drive Wallace's WHERES_RAYQUAZA menu to index 2 ("SKY PILLAR"). Returns the attempt count.

    ⛔⛔ BESPOKE ON PURPOSE — `wait_for_multiple_choice_question` is unbounded, never checks WHICH
    menu it answers, and verifies no outcome (spec §3.2; a wrong answer also drops the task,
    because every wrong branch re-arms the prompt with a FRESH `multichoice` — cursor RESET to 0).
    ⛔ THE LETTER "B" IS DELIBERATELY ABSENT FROM THIS FUNCTION: `multichoice … FALSE` means B
    cancels into `MULTI_B_PRESSED` (127) → the bare `goto DontRemember` → the same prompt again,
    forever. Every press here is A or Down.
    ‼ The ONLY honest success is `SOOTOPOLIS_CITY_STATE == 3` — the task dropping proves nothing.
    """
    from modules.modes import BotModeError
    from modules.story.early_game import _check_abort
    from modules.tasks import get_task, task_is_active

    import os as _os_fault

    fault_wrong = _os_fault.environ.get("POKEBOT_CH21_FAULT_WRONGANSWER", "").strip() == "1"
    attempts = 0
    frames = 0

    def _tick(n: int = 1) -> Generator:
        nonlocal frames
        for _ in range(n):
            yield
            frames += 1

    while frames < budget_frames:
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try (loop-head abort rule)
        if _var("SOOTOPOLIS_CITY_STATE") == 3:
            return attempts
        if task_is_active("Task_HandleMultichoiceInput"):
            task = get_task("Task_HandleMultichoiceInput")
            menu_id = task.data_value(7) if task is not None else None
            if menu_id != MULTI_WHERES_RAYQUAZA:
                raise BotModeError(
                    f"Ch21 leg 2b: a multichoice is open but its id is {menu_id!r}, not "
                    f"{MULTI_WHERES_RAYQUAZA} (MULTI_WHERES_RAYQUAZA) — refusing to answer a "
                    "menu this handler was not built for."
                )
            attempts += 1
            if attempts > 3:
                raise BotModeError(
                    "Ch21 leg 2b: the WHERES_RAYQUAZA prompt re-armed more than 3 times — the "
                    "answer is not landing on index 2 (SKY PILLAR). The cursor RESETS to 0 on "
                    "every re-arm, so a drift here means the Down presses are being eaten."
                )
            if attempts > 1:
                from modules.console import console

                console.print(
                    f"[yellow]Story: Ch21 — the WHERES_RAYQUAZA prompt RE-ARMED "
                    f"(attempt {attempts}, menu id {menu_id}, state still "
                    f"{_var('SOOTOPOLIS_CITY_STATE')!r}); answering again.[/]"
                )
            yield from _tick(4)  # let the menu settle before moving the cursor
            if fault_wrong and attempts == 1:
                # ‼ FAULT INJECTION (POKEBOT_CH21_FAULT_WRONGANSWER=1, driver-proof only):
                # answer index 0 once — the spec §4.9 arm. Proves the wrong-answer re-arm is
                # DETECTED (attempt 2 with the same menu id, state still 2) and RECOVERED.
                from modules.console import console

                console.print(
                    "[yellow]Story: Ch21 — FAULT ARM: deliberately answering index 0 "
                    "(CAVE OF ORIGIN) on attempt 1.[/]"
                )
            else:
                for _ in range(2):  # index 2 = Down x2 from the reset cursor (wrap is on; 2 < 4)
                    context.emulator.press_button("Down")
                    yield from _tick(3)
            inner = 0
            while task_is_active("Task_HandleMultichoiceInput"):
                context.emulator.press_button("A")
                yield from _tick(3)
                inner += 1
                if inner > 200:
                    raise BotModeError(
                        "Ch21 leg 2b: the multichoice task did not drop after 200 A-presses — "
                        "the menu is not accepting input; a real wedge, not slowness."
                    )
            continue
        # ‼ THE UNGATED A IS SAFE *HERE SPECIFICALLY*, and the museum-greeter rule demands the
        # proof be stated: Wallace's monologue → multichoice → payoff is ONE continuous script
        # (`CaveOfOrigin_B1F_EventScript_Wallace`) that NEVER releases control before
        # `SOOTOPOLIS_CITY_STATE` is written to 3 — measured in BOTH arm transcripts
        # (`evidence/2026-08-27-ch21cave-wronganswer-armB-clean.txt:224`: the script stack never
        # empties until state 3), so a stray A cannot land on the overworld and re-open him;
        # and the loop's own `state == 3` early-return exits before any post-payoff press.
        # ⛔ Do NOT copy this press into overworld-adjacent loops — there the gate is mandatory.
        context.emulator.press_button("A")  # advance the story msgbox toward/after the menu
        yield from _tick(1)

    raise BotModeError(
        f"Ch21 leg 2b: {budget_frames} frames of Wallace dialogue without "
        f"SOOTOPOLIS_CITY_STATE reaching 3 — it is {_var('SOOTOPOLIS_CITY_STATE')!r}, "
        f"attempts={attempts}, at {_where()}."
    )


def cave_of_origin() -> Generator:
    """LEG 2b — Entrance (9,20) → 1F → B1F → Wallace → SOOTOPOLIS_CITY_STATE == 3.

    Preconditions: leg 2a is DONE (escort flag set) and we are standing in the Cave of Origin
    Entrance. End state (spec §2): `SOOTOPOLIS_CITY_STATE == 3` AND `WALLACE_GOES_TO_SKY_PILLAR`
    — ⛔ NEVER graded on Wallace's absence (three worlds return False) and NEVER on
    `ch21_done()` (that is the whole chapter's flag, three legs away).
    ⛔ THE WALK BACK OUT IS NOT THIS LEG'S JOB, deliberately: the Sootopolis pocket re-plan trap
    belongs to LEG 3, which OWNS the cave return and is BUILT AND DRIVEN as of 2026-09-01
    (`approach_sky_pillar`). This leg ENDS on B1F with state 3, and that is exactly where the
    pinned fixture `post_wallace.ss1` sits.
    """
    from modules.modes import BotModeError
    from modules.modes.util.walking import ensure_facing_direction, navigate_to
    from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable
    from modules.story.space_center import _npc_is_on
    from modules.tasks import get_global_script_context

    yield from wait_until_truly_controllable()

    # --- 0. PREFLIGHT ---------------------------------------------------------------------------
    if not steven_escort_done():
        raise BotModeError(
            f"Ch21 leg 2b: the escort flag is CLEAR — leg 2a has not run (at {_where()}). "
            "2b starts from the Entrance the escort warps into; run leg 2a first."
        )
    state = _var("SOOTOPOLIS_CITY_STATE")
    if state == 3:
        context.message = "Story: Ch21 — Wallace already sent to Sky Pillar (state 3); leg 2b is done."
        return
    if state != 2:
        raise BotModeError(f"Ch21 leg 2b: SOOTOPOLIS_CITY_STATE is {state!r}, expected 2 (or 3=done).")
    if not _on_map(MapRSE.CAVE_OF_ORIGIN_ENTRANCE):
        raise BotModeError(
            f"Ch21 leg 2b: not in the Cave of Origin Entrance — at {_where()}. "
            "⛔ This leg does not travel to the cave; the escort (leg 2a) is the only way in."
        )

    # --- 1. ENTRANCE → 1F. ⛔ We are STANDING ON the warp back to Sootopolis ((9,20) → city
    # (31,16)); the path up x=9 moves NORTH away from it by construction. Encounters are LIVE
    # on Entrance and 1F (rate 4) — ride them out. --------------------------------------------
    context.message = "Story: Ch21 — descending the Cave of Origin (Entrance → 1F)."
    yield from _navigate_riding_out(MapRSE.CAVE_OF_ORIGIN_ENTRANCE, ENTRANCE_TO_1F, tries=6)
    if not _on_map(MapRSE.CAVE_OF_ORIGIN_1F):
        raise BotModeError(
            f"Ch21 leg 2b: took the Entrance shaft to {ENTRANCE_TO_1F} but did not land on 1F — "
            f"at {_where()} (expected CAVE_OF_ORIGIN_1F, arrival tile (11,17))."
        )

    # --- 2. 1F → B1F ----------------------------------------------------------------------------
    context.message = "Story: Ch21 — descending the Cave of Origin (1F → B1F)."
    yield from _navigate_riding_out(MapRSE.CAVE_OF_ORIGIN_1F, ONEF_TO_B1F, tries=6)
    if not _on_map(MapRSE.CAVE_OF_ORIGIN_B1F):
        raise BotModeError(
            f"Ch21 leg 2b: took the 1F warp at {ONEF_TO_B1F} but did not land on B1F — "
            f"at {_where()} (expected CAVE_OF_ORIGIN_B1F, arrival tile (9,3))."
        )

    # --- 3. WALLACE. B1F has NO wild encounters (whole-file grep, spec §Step 8) and no map
    # scripts; he is the map's only object. ⛔ He NEVER respawns (removeobject sets his hide
    # flag permanently, §3.6). ⛔⛔ The presence check runs INSIDE the approach loop, from the
    # ADJACENT tile — the first smoke run checked from the (9,3) arrival, 10 tiles away, and
    # `get_map_objects()` is a CAMERA-RANGE WINDOW: Wallace was "absent" whether or not he
    # existed. The exact mistake the §4.2 flip lesson documents, re-made and caught in-smoke. --
    from modules.story.early_game import _check_abort

    for approach, facing in WALLACE_APPROACHES:
        _check_abort()  # loop-head abort rule — consistent with every rider in this module
        context.message = f"Story: Ch21 — approaching Wallace via {approach} facing {facing}."
        yield from navigate_to(MapRSE.CAVE_OF_ORIGIN_B1F, approach)
        yield from wait_until_truly_controllable()
        if not _npc_is_on(MapRSE.CAVE_OF_ORIGIN_B1F, WALLACE_TILE):
            if _var("SOOTOPOLIS_CITY_STATE") == 3:
                context.message = "Story: Ch21 — Wallace already gone (state 3); leg 2b is done."
                return
            raise BotModeError(
                f"Ch21 leg 2b: standing ADJACENT at {approach} (in camera range) and no live "
                f"object is on {WALLACE_TILE}, state {_var('SOOTOPOLIS_CITY_STATE')!r} (not 3) — "
                "Wallace should be here and is not. ⛔ Do not wait: he never respawns."
            )
        yield from ensure_facing_direction(facing)
        context.emulator.press_button("A")
        yield
        # bounded ENGAGEMENT check (the leg-2a lesson, `.is_active` idiom): give the talk ~300
        # frames to start a script; a miss falls through to the next approach instead of
        # feeding 12,000 frames of A into empty air.
        engaged = False
        for _ in range(300):
            _check_abort()  # loop-head abort rule
            try:
                ctx = get_global_script_context()
                if ctx is not None and ctx.is_active:
                    engaged = True
                    break
            except Exception:  # noqa: BLE001 - unreadable context: keep waiting, budget bounds us
                pass
            yield
        if engaged:
            attempts = yield from _answer_wallace_multichoice()
            context.message = (
                f"Story: Ch21 — Wallace sent to Sky Pillar (state 3, menu attempts={attempts})."
            )
            break
        from modules.console import console

        console.print(
            f"[yellow]Story: Ch21 — the A-press at {approach} did not engage Wallace "
            f"(no script in 300 frames); retrying the next approach.[/]"
        )
    else:
        raise BotModeError(
            "Ch21 leg 2b: all three Wallace approaches pressed A without engaging his script. "
            "He was verified present before the loop, so check facing latching in the log."
        )

    # --- 4. ACCEPTANCE (spec §2, both observables) ----------------------------------------------
    state = _var("SOOTOPOLIS_CITY_STATE")
    if state != 3 or not wallace_sent_to_sky_pillar():
        raise BotModeError(
            f"Ch21 leg 2b: the dialogue ended but the end state is wrong — state={state!r}, "
            f"WALLACE_GOES_TO_SKY_PILLAR={wallace_sent_to_sky_pillar()}. The two are written by "
            "the same seven-line script block, so disagreement means a misread, not a half-run."
        )
    context.message = f"Story: Ch21 — leg 2b done: Wallace is off to Sky Pillar (at {_where()})."


# --- LEG 3 CONSTANTS — THE APPROACH: cave return -> pocket -> heal -> dive -> swim -> the door ----
# ⛔ EVERY ROW IS TAGGED WITH HOW IT WAS OBTAINED, AND NOTHING IS HARDCODED THAT THE RUN CAN READ
# BACK FROM THE STATE IT REACHED. Provenance, in order of strength:
#   MEASURED-LIVE  — read off a real drive (`--driver ch21pocket`, 2026-08-27).
#   MEASURED-PROD  — re-asked of production's own `calculate_path` / tile reader from the PINNED
#                    fixture by `tools/story-dev/probe_ch21_leg3_constants.py` (2026-09-01);
#                    evidence/2026-09-01-ch21-leg3-CONSTANTS.stdout.txt. 6/6 graded rows agreed
#                    with the BUILD SPEC, so these are corroborated, not merely transcribed.
#   MEASURED-ROM   — decoded from OUR OWN ROM's layout bytes by
#                    `tools/story-dev/probe_ch21_route131_tail.py` (2026-09-01), four controls PASS.
POCKET_RELOAD_TILE = (31, 17)   # MEASURED-LIVE: the RESTING tile of CAVE_OF_ORIGIN_ENTRANCE (9,20).
#                               # ⛔ NOT (31,16) — that is the warp EVENT tile, and it is a
#                               # 'Non-Animated Door' (MEASURED-PROD), so standing on it is a warp.
POCKET_EXIT_TARGET = (43, 32)   # MEASURED-LIVE: 121 wp from the reload tile, 1,624 frames. It is
#                               # the tile IN FRONT OF the Poke Center; ⛔ (43,31) is the DOOR
#                               # itself (it is literally `PokemonCenter.SootopolisCity`).
DIVE_OUT_TILE = (29, 53)        # MEASURED-PROD: 'Sootopolis Deep Water', collision 0, elevation 1.
UW_EXIT_WARP = (9, 8)           # MEASURED-PROD: 'Water South Arrow Warp'. ⛔ (10,8) is plain
#                               # 'Deep Water' (MEASURED-PROD) and its header warp can never fire.
R126_SURFACE_TILE = (45, 66)    # ⛔ MEASURED-LIVE 2026-09-01 (drive 3), AND IT CORRECTS BOTH
#                               # BUILD-SPEC CRITICS AND THE ATLAS ROW THEY READ. They both said
#                               # (45,65) and both hard-asserted it. (45,65) is the warp TARGET;
#                               # the avatar RESTS one tile SOUTH, on (45,66) — the resting-tile
#                               # rule, which this project has paid for before. Surfacing is
#                               # (x,y)-preserving, so the run surfaces on (45,66) too.
#                               # ‼ (45,66) is not a new tile: it is leg 1's own `DIVE_TILE`, whose
#                               # comment already called it "1 tile south of the warp column". The
#                               # two halves of this file disagreed and the drive settled it.
#                               # ⛔ This constant is a PREDICTION used for reporting. The actual
#                               # assertion below is the (x,y)-PRESERVING INVARIANT, not this literal.
R131_SWIM_TARGET = (40, 20)     # MEASURED-PROD: 322 wp in ONE call, split
#                               # ROUTE126:51 127:51 128:57 129:60 130:80 131:23.
R131_BLIND_STEP = (40, 19)      # MEASURED-PROD 'Normal' collision 1 to our planner;
#                               # MEASURED-ROM collision 0 in the layout the game runs. See below.
R131_STAGING = (28, 15)         # MEASURED-PROD: 16 wp from (40,19) — and 35 wp AND FATAL from
#                               # (40,20); see `_LEG3_FALLBACK_IS_FATAL`.
SKY_PILLAR_DOOR = (36, 6)       # MEASURED-ROM 'Non-Animated Door' in the live layout;
#                               # MEASURED-PROD 'Deep Water' to our planner ⇒ invisible to it.
ENTRANCE_CONTINUE = (14, 3)     # MEASURED-PROD: 21 wp, is_warp=False. ⛔ NEVER (14,4) — see
#                               # `approach_sky_pillar`'s continuation proof.
ENTRANCE_REST_PREDICTION = (6, 16)  # ⛔ A PREDICTION, REPORTED AND NEVER ASSERTED. There is
#                               # deliberately no `ENTRANCE_REST` constant: the resting tile is READ
#                               # from the state the run reaches. (MEASURED-PROD: (6,16) is a
#                               # 'South Arrow Warp', which is neither IsDoor nor IsNonAnimDoor, so
#                               # the +1-south resting rule should NOT apply — but that rule has
#                               # been blind-tested 3/3 only on Non-Animated Door and Ladder
#                               # targets and NEVER on an arrow-warp target. This run is its first
#                               # negative control, and a mismatch is a FINDING, not a failure.)

#: ⛔⛔ THE 16 HAND-WALKED STEPS FROM THE STAGING TILE TO THE DOOR APRON, AND WHY THEY EXIST.
#: ROUTE131 runs `setmaplayoutindex LAYOUT_ROUTE131_SKY_PILLAR` unconditionally in OnTransition,
#: while `calculate_path` plans on the ROM header's DEFAULT layout. So on this map the planner and
#: the avatar are looking at two different maps, and `(28,15) -> the door` is NO ROUTE to the
#: planner (MEASURED-PROD) while being 17 steps in the layout the game runs (MEASURED-ROM).
#:
#: ‼ THE BUILD SPEC SHIPPED **TWO DIFFERENT** TAILS, ONE PER CRITIC, EACH CLAIMING PRODUCTION
#: PROVENANCE. `probe_ch21_route131_tail.py` adjudicated them against our own ROM's bytes on
#: 2026-09-01 and found BOTH walkable, contiguous, and ending on (36,7). So this is a CHOICE, and
#: it is recorded in `06-DECISIONS-LOG.md` rather than presented as the only option:
#:   * the x=36 column (below) dismounts at step 14 of 16, leaving ONE step after the dismount;
#:   * the x=34 column (`DOOR_APPROACH_FALLBACK`) dismounts at step 12, leaving THREE.
#: The surf dismount is the single least-proven mechanic in the tail (no arm of any recon pass has
#: ever driven a BLIND step across one), so the tail that spends the fewest steps downstream of it
#: wins. Both are kept, because if the dismount stalls the alternative is a one-line swap.
#:
#: ✅ AND ONLY **TWO** OF THESE STEPS ARE ACTUALLY BLIND (MEASURED-ROM): (29,15) and (30,15) are
#: the only two tiles our planner calls walls. The other 14 are collision-0 in BOTH layouts — they
#: are unreachable to the planner only because they sit in a disconnected component. ⇒ IF THE
#: LAYOUT PREMISE IS WRONG, THIS SEQUENCE FAILS ON STEP 0 OR 1 — immediately, loudly, and two
#: steps from a re-plannable tile — NOT fourteen steps deep. That is a measured safety property,
#: and it is the reason this leg is drivable at all.
DOOR_APPROACH = (
    ("Right", (29, 15)),   # ⛔ BLIND: collision 1 to our planner, collision 0 in the live layout
    ("Right", (30, 15)),   # ⛔ BLIND: ditto. These two are the ONLY blind steps in the tail.
    ("Right", (31, 15)),
    ("Right", (32, 15)),
    ("Right", (33, 15)),
    ("Right", (34, 15)),
    ("Up", (34, 14)),
    ("Right", (35, 14)),
    ("Right", (36, 14)),
    ("Up", (36, 13)),
    ("Up", (36, 12)),
    ("Up", (36, 11)),
    ("Up", (36, 10)),
    ("Up", (36, 9)),
    ("Up", (36, 8)),       # ‼ THE SURF DISMOUNT: elevation 1 ('Ocean Water') -> 3 ('Sand').
    ("Up", (36, 7)),       # the door apron. The door itself is one more step Up, and it WARPS.
)

#: The pre-vetted alternate tail, MEASURED-ROM equally walkable (same 16 steps, same end tile).
#: ⛔ Swap to this ONLY if the dismount stalls at (36,8); it is not an error-recovery path the code
#: takes by itself, because a bot that silently tries a second route hides the finding.
DOOR_APPROACH_FALLBACK = (
    ("Right", (29, 15)), ("Right", (30, 15)), ("Right", (31, 15)), ("Right", (32, 15)),
    ("Right", (33, 15)), ("Right", (34, 15)),
    ("Up", (34, 14)), ("Up", (34, 13)), ("Up", (34, 12)), ("Up", (34, 11)), ("Up", (34, 10)),
    ("Up", (34, 9)),
    ("Up", (34, 8)),       # ‼ the dismount, four steps from the end instead of two
    ("Up", (34, 7)), ("Right", (35, 7)), ("Right", (36, 7)),
)

#: The tile the door apron sits on. Asserted after the tail and before the warp step.
DOOR_APRON = (36, 7)

#: ⛔ THE LEG OWNS ITS OWN LABEL VOCABULARY AND THE DRIVER IMPORTS IT. A driver holding a private
#: copy is the P5 shape — the same fact in two places — and it fails in the worst possible
#: direction: rename a label here and the driver reports `missing=['R-BLIND']` on a PERFECT run,
#: whose obvious repair is to edit the driver's list, which SILENTLY DELETES A REQUIRED READING.
#: (The two build-spec critics already disagreed: one wrote `R-BLIND`, the other `R-BLIND1`.)
LEG3_READINGS = (
    "R-CAVE",      # out of the Cave of Origin, standing on the measured resting tile
    "R-POCKET",    # the sealed-pocket crossing, planned once and followed blind
    "R-HEAL",      # party healed, asserted BY PID, and both HMs still present afterwards
    "R-DIVE",      # dived out of Sootopolis and landed underwater
    "R-SURFACE",   # through the arrow warp and back on the surface on Route 126
    "R-SWIM",      # the 322-waypoint six-map swim
    "R-LAYOUT",    # ROUTE131's live grid checked against every tile this leg will step on
    "R-BLIND",     # the blind step onto a tile our own planner calls a wall
    "R-STAGING",   # the last planner call permitted on Route 131
    "R-TAIL",      # all 16 hand-walked steps confirmed, one assert each
    "R-DOOR",      # through the Sky Pillar door
    "R-REST",      # the arrival tile READ (never asserted) against its prediction
    "R-CONTINUE",  # the bot can CONTINUE: a real path to (14,3)
    "R-CONTROL",   # ⛔ and the planner can still REFUSE: the same call to (6,17) must raise
)

#: ⛔ WHY THERE IS NO FALLBACK FROM (40,20). Production's own plan from the swim's end tile to the
#: staging tile is 35 waypoints and it is FATAL, not merely slow: three of its tiles — (23,19),
#: (23,18), (24,18) — are collision 0 to our planner and collision 1 in the layout the game runs
#: (MEASURED-PROD + MEASURED-ROM, 2026-09-01). The bot would walk into a wall it believes is water
#: and re-plan the identical path until `NavigationStuckError`. ⇒ the blind step at (40,19) is a
#: HARD PRECONDITION of everything after it. The atlas called this "35 wp and a detour"; it is a
#: wall collision, and that sentence is corrected in `12-STORYMODE-DESIGN.md`.
_LEG3_FALLBACK_IS_FATAL = True


def at_sky_pillar_door() -> bool:
    """Leg 3's completion test: standing inside the Sky Pillar's entrance hall."""
    return _on_map(MapRSE.SKY_PILLAR_ENTRANCE)


def _here_tile() -> tuple[int, int]:
    """The avatar's LIVE local (x, y), or a loud failure.

    ‼ WHY THIS EXISTS RATHER THAN `_where()[1]`. `_where()` returns `((group, number), (x, y))`
    **or a reason string** (seafloor_cavern.py:178-189), and indexing a string yields a CHARACTER
    — which would then be passed to `calculate_path` as a source tile and compared unequal to every
    real coordinate forever. That is the same shape as this package's transcription rule A. Every
    caller here plans or asserts from the tile the run ACTUALLY reached, so an unreadable position
    must stop the leg, never silently degrade it.
    """
    from modules.modes import BotModeError

    where = _where()
    if not isinstance(where, tuple):
        raise BotModeError(f"Ch21 leg 3: the player position is unreadable ({where!r}).")
    return tuple(where[1])


def _live_collision_grid(map_enum) -> dict[tuple[int, int], int]:
    """Collision per LOCAL tile, read from `gBackupMapLayout` — THE GRID THE GAME ITSELF WALKS ON.

    ⛔⛔ WHY THIS EXISTS, AND WHY NOTHING ELSE IN THE TREE COULD ANSWER THE QUESTION. Every tile
    reader we own ultimately dereferences a LAYOUT's blockdata pointer, which lives in **ROM**
    (`map.py:769-771`). The game walks on `sBackupMapData` in **RAM**. Those diverge whenever a map
    runs `setmaplayoutindex` (a whole different layout) or `setmetatile` (individual tiles), and a
    ROM read can never observe either.

    ‼ MEASURED, NOT ARGUED — this function exists because the FIRST leg-3 drive (2026-09-01) walked
    out of the Sootopolis Poke Center and jammed at (31,42) with `UnreachableDestinationError: the
    field is idle and we are still at (31,42), so retrying cannot change the result`. Reading this
    grid explained it in one shot: a solid 9x3 block, x=27..35 by y=43..45, is **collision 0 to our
    planner and collision 1 to the game**, and the planned route's very first waypoint (31,43) was
    inside it. SOOTOPOLIS_CITY swaps to `LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE` at
    SOOTOPOLIS_CITY_STATE 1-4 — the exact state leg 3 runs in.

    ⇒ USE THIS AS THE ORACLE FOR "CAN THE BOT ACTUALLY STEP THERE", never a `get_map_data` read.

    ⛔ ONLY VALID FOR THE MAP THE AVATAR IS CURRENTLY STANDING ON: `gBackupMapLayout` describes the
    loaded map, so asking it about any other map is meaningless. The caller passes `map_enum` so
    that mistake raises instead of returning confident nonsense.
    """
    from modules.memory import read_symbol, unpack_uint32
    from modules.modes import BotModeError

    if not _on_map(map_enum):
        raise BotModeError(
            f"Ch21: _live_collision_grid({map_enum.name}) was called while standing at {_where()}. "
            "`gBackupMapLayout` only ever describes the LOADED map."
        )

    header = read_symbol("gBackupMapLayout", 0, 12)
    width = unpack_uint32(header[0:4])
    height = unpack_uint32(header[4:8])
    pointer = unpack_uint32(header[8:12])

    from modules.map import get_map_data

    map_width, map_height = get_map_data(map_enum, (0, 0)).map_size
    # The backup grid carries a border margin of MAP_OFFSET (7) tiles on every side.
    # ⛔ THE MARGIN IS **NOT** SYMMETRIC IN THE TWO AXES, AND ASSUMING IT WAS IS A REAL BUG THIS
    # FUNCTION ALREADY SHIPPED ONCE (2026-09-01, caught by its own guard on the first call): the
    # decomp allocates `width = mapWidth + 15` but `height = mapHeight + 14`, so a
    # `(width - map_width) // 2` derivation reads 7 while `(width - map_width) % 2` is 1 — and a
    # derivation that "looks symmetric" would have silently shifted every x by half a tile on some
    # other map. ⇒ use the decomp's constant and VALIDATE the dimensions against it.
    # ‼ Calibrated independently by `probe_live_mapgrid.py`, which searches offsets 0-8 against
    # `get_map_data` and scores 7 at 99.6% while every other candidate lands between 46% and 74% —
    # so this constant is measured, not merely quoted.
    offset = 7  # MAP_OFFSET, include/constants/global.h
    if width < map_width + 2 * offset or height < map_height + 2 * offset:
        raise BotModeError(
            f"Ch21: the live grid for {map_enum.name} is {width}x{height}, too small for a "
            f"{map_width}x{map_height} map with a {offset}-tile border. Either the map is not "
            "loaded or `gBackupMapLayout` is not what this function thinks it is."
        )

    raw = context.emulator.read_bytes(pointer, width * height * 2)
    grid: dict[tuple[int, int], int] = {}
    for y in range(map_height):
        for x in range(map_width):
            index = ((y + offset) * width + (x + offset)) * 2
            block = raw[index] | (raw[index + 1] << 8)
            grid[(x, y)] = (block & 0x0C00) >> 10
    return grid


def _live_wall_tiles(map_enum, tiles) -> list[tuple[int, int]]:
    """Which of `tiles` does the GAME consider a wall, whatever our planner believes?"""
    grid = _live_collision_grid(map_enum)
    return [tuple(tile) for tile in tiles if grid.get(tuple(tile), 1) != 0]


def _pin_planner_to_live_layout(map_enum) -> str:
    """Make `calculate_path` plan on the layout THE GAME IS RUNNING for this map.

    ⛔⛔ THIS MUTATES A PROCESS-GLOBAL AND THAT IS DELIBERATE, BOUNDED AND MEASURED.
    `modules.map._map_layout_cache` (map.py:735) is keyed by **(rom id, map) ALONE** — it does not
    record whether the 24 layout bytes came from the LIVE `gMapHeader` or from the STATIC ROM
    `gMapGroups` table. So whichever reader touches a map first wins for the whole process, and
    `calculate_path` silently inherits that choice. MEASURED 2026-09-01 on this very fixture:
    static-seeded, `(43,32)->(29,53)` is **37 waypoints and walks into live rock**; live-seeded it
    is **35 waypoints and is correct**. The first leg-3 drive got the 37 and jammed.

    ⇒ Rather than hope the right reader went first, this SETS the entry from the live header and
    drops the `map_path` PathMap so the graph is rebuilt from it.

    ⛔ SCOPE, because a never-cleared global deserves an explicit blast radius (KI-73): this touches
    exactly ONE map key and only while the avatar is standing on that map. It is correct for as
    long as the map's layout does not change again — true for leg 3, whose whole run happens at
    SOOTOPOLIS_CITY_STATE 3. ⛔ A future caller that pins a map and then advances the var that
    swaps it back would be left with a stale entry, which is why this returns a description that
    the caller is expected to LOG.
    """
    import modules.map as _map_module
    import modules.map_path as _map_path_module
    from modules.memory import read_symbol, unpack_uint32
    from modules.modes import BotModeError

    if not _on_map(map_enum):
        raise BotModeError(
            f"Ch21: _pin_planner_to_live_layout({map_enum.name}) called while at {_where()}; the "
            "live header only describes the loaded map."
        )

    live_layout_pointer = unpack_uint32(read_symbol("gMapHeader")[:4])
    live_layout = context.emulator.read_bytes(live_layout_pointer, 24)

    per_rom = _map_module._map_layout_cache.setdefault(context.rom.id, {})
    before = per_rom.get(map_enum.value)
    per_rom[map_enum.value] = live_layout
    # ⛔⛔ THE WHOLE GAME KEY IS DROPPED, NOT JUST THIS MAP'S ENTRY, AND THAT IS NOT OVER-CAUTION —
    # A PER-MAP `pop()` IS A **BUG**, AND IT SHIPPED HERE FOR ONE DRIVE. `_get_all_maps_metadata`
    # (map_path.py:499-505) populates the collection for EVERY map, but only when the game key is
    # ABSENT: `if game_key in _maps: return _maps[game_key]`. So removing a single map's entry
    # leaves the collection permanently missing it, and the very next lookup raises. Drive 2
    # (2026-09-01) failed with exactly `KeyError: (0, 7)` — SOOTOPOLIS_CITY's own map value —
    # immediately after this function popped it.
    # ⇒ evicting the key forces a full rebuild, which re-reads `get_map_data` for every map and
    # therefore picks up the layout we just pinned. It costs one synchronous rebuild; a partially
    # populated cache costs the run.
    _map_path_module._maps.pop(context.rom.id, None)

    def _blockdata(struct) -> str:
        return "unseeded" if struct is None else f"0x{unpack_uint32(struct[12:16]):08X}"

    return (f"{map_enum.name}: planner blockdata {_blockdata(before)} -> "
            f"{_blockdata(live_layout)} (pinned to the LIVE header)")


def _route131_layout_reading() -> tuple[str, bool]:
    """Which map is `calculate_path` PLANNING ON for ROUTE131 right now, versus the one the game RUNS?

    ⛔⛔ THIS IS THE PREMISE THE WHOLE HAND-WALKED TAIL RESTS ON, AND UNTIL 2026-09-01 NOTHING IN
    THE TREE COULD READ IT. The mechanism is now pinned to a line: `modules/map.py:735-755` caches
    each map's 24-byte layout struct in `_map_layout_cache` keyed by **(map_group, map_number)
    ALONE** — not by which header it came from. `get_map_data()` builds its `MapLocation` from the
    STATIC ROM header (`gMapGroups`, map.py:1774-1789) while `get_map_data_for_current_position()`
    builds it from the LIVE `gMapHeader` (map.py:1742-1751). Both then populate THE SAME cache
    entry, so **whichever reader touches a map first wins for the rest of the process** — and
    `calculate_path` silently inherits that choice.

    ‼ MEASURED, NOT ARGUED (2026-09-01, a two-armed A/B on `post_sootopolis_arrival.ss1`): seeding
    SOOTOPOLIS_CITY from the static header gives blockdata 0x083E6A04 and `(43,32)->(29,53)` = 37
    waypoints; seeding it from the live header first gives blockdata 0x084675E0 and **35**. The
    seeding ORDER changes production's own answers. That is KI-73's blast radius, made concrete.

    For leg 3 this cuts both ways and must therefore be READ rather than assumed:
      * the swim is planned from ROUTE126 while the bot is still off ROUTE131, so that
        `calculate_path` seeds ROUTE131 with the STATIC layout before the bot ever arrives — which
        is exactly why the planner is blind on arrival, and why the tail is hand-walked;
      * but if anything read ROUTE131's LIVE header first, `calculate_path` would plan on the
        live layout, the door would become visible, and hand-walking would be unnecessary.

    :return: (a human-readable reading, whether the planner and the game agree)
    """
    import modules.map as _map_module
    from modules.memory import read_symbol, unpack_uint32

    cached = _map_module._map_layout_cache.get(context.rom.id, {}).get(MapRSE.ROUTE131.value)
    planner_blockdata = None if cached is None else unpack_uint32(cached[12:16])

    live_layout_pointer = unpack_uint32(read_symbol("gMapHeader")[:4])
    live_blockdata = unpack_uint32(context.emulator.read_bytes(live_layout_pointer + 12, 4))

    agree = planner_blockdata is not None and planner_blockdata == live_blockdata
    if planner_blockdata is None:
        reading = f"planner=UNSEEDED live=0x{live_blockdata:08X}"
    else:
        reading = f"planner=0x{planner_blockdata:08X} live=0x{live_blockdata:08X} agree={agree}"
    return reading, agree


def _bounded_step(direction: str, expect: tuple[int, int], *, map_enum, max_frames: int = 900,
                  tries: int = 3) -> Generator:
    """Take ONE tile step and PROVE it landed, with a frame bound and a named failure.

    ⛔⛔ THE WRAPPER IS MANDATORY AND ITS SHAPE IS NOT NEGOTIABLE. `walking.walk_one_tile` is
    `while get_player_avatar().local_coordinates == starting_position: yield` with NO frame cap, no
    `_check_abort()` and no controllable gate (walking.py:537-561); its own docstring says "It will
    create an endless loop if trying to run into a wall". Every step this leg takes on ROUTE131 is
    aimed at a tile our own pathfinder calls unreachable, so "running into a wall" is precisely the
    failure mode that must be bounded rather than trusted away.

    ⛔ `run=False` IS A SAFETY ARGUMENT, NOT A STYLE CHOICE, AND IT IS VERIFIED IN CODE. The
    signature is `walk_one_tile(direction, run: bool = True)` and `run=True` HOLDS B. Every blind
    step here is taken while SURFING, and `follow_waypoints` deliberately refuses to hold B on
    water — the guard is `run and not waypoint.is_water_tile and ... not AvatarFlags.Underwater`
    at walking.py:355-362, and walking.py:183-185 says why: "pressing B can cause the game to try
    and dive/emerge which we don't want". Inheriting the default here would ask the game to dive in
    the middle of a blind approach. (`_fortree_walk_one_tile`, the shape this copies, calls
    `walk_one_tile(direction)` and so inherits run=True — correct on dry land, wrong here.)

    ⚠ A BATTLE SHOULD NOT CONSUME THE BUDGET — REASONED FROM THE ARCHITECTURE, **NOT MEASURED**,
    and an adversarial review was right to flag the distinction. The mode generator receives no
    frames while a battle runs, so `frames` should count only frames this step actually got; what a
    battle DOES break is the held direction, which is why a stalled attempt is retried whole
    (bounded by `tries`) rather than resumed. ⛔ NEITHER FAULT ARM EXERCISES A BATTLE MID-BLIND-STEP
    on the ROUTE131 tail — both substitute a direction instead. If that reasoning is wrong the
    failure mode is benign (the budget expires early and the step is retried, `tries` times, then
    raises loudly) — which is why this ships as a documented assumption rather than a blocker.
    """
    from modules.modes import BotModeError
    from modules.modes.util.walking import walk_one_tile
    from modules.story.early_game import _check_abort

    for attempt in range(tries):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try (loop-head abort rule)
        if _at(map_enum, expect):
            return  # a retry after a stall that actually landed: nothing left to do
        stepper = walk_one_tile(direction, run=False)
        frames = 0
        stalled = False
        # ⛔⛔ THE `finally` IS LOAD-BEARING, NOT TIDINESS. `walk_one_tile` HOLDS the direction (and
        # B, when run=True) and only releases it once the tile changes — so abandoning it early, by
        # a frame-bound break OR by a `StoryAbort` raised at the loop head, leaves a D-pad key STUCK
        # DOWN. `early_game.py:8029-8035` earned that lesson in `strength_push` and says so: "it is
        # what makes the retry loop mean anything". ‼ It matters twice as much on THIS leg: a held
        # direction survives into the derail path (`plugins/custom_modes/story_mode.py` has no
        # `reset_held_buttons` at all), and leg 3 ends one tile from a SOUTH arrow warp that fires on
        # a held direction and drops the run back into a re-sealed pocket.
        try:
            while True:
                _check_abort()  # loop head; the inner try wraps ONLY `next()`, so it cannot swallow this
                try:
                    next(stepper)
                except StopIteration:
                    # Not an error: StopIteration is how a generator says the step COMPLETED. The
                    # `_at(...)` assertion below is what decides whether it completed CORRECTLY.
                    break
                frames += 1
                if frames > max_frames:
                    stalled = True
                    break
                yield
        finally:
            context.emulator.reset_held_buttons()
        if not stalled and _at(map_enum, expect):
            return
        from modules.console import console

        console.print(
            f"[yellow]Ch21 leg 3: step '{direction}' toward {expect} did not land on attempt "
            f"{attempt + 1}/{tries} (stalled={stalled}, frames={frames}, now at {_where()}); "
            f"retrying the SAME step.[/]"
        )
        for _ in range(30):  # let a battle aftermath / script settle before re-issuing the step
            yield

    raise BotModeError(
        f"Ch21 leg 3: could not step '{direction}' onto {expect} on {map_enum.name} after {tries} "
        f"attempts of up to {max_frames} frames each; the run is at {_where()}. These tiles come "
        "from OUR OWN ROM's Route131_SkyPillar layout bytes and our planner sees open water where "
        "the island is, so there is NO fallback route to fall back ON. A mismatch means the live "
        "layout differs from that blob — RE-MEASURE it with probe_ch21_route131_tail.py; do not "
        "nudge the constant to make this pass."
    )


def _assert_pocket_is_open(target: tuple[int, int]):
    """Prove the pocket crossing can be PLANNED before committing to it, and log the evidence.

    ⛔ WHAT IS MEASURED AND WHAT IS NOT — stated separately, because conflating them is how a
    correlation gets shipped as a mechanism. MEASURED (2026-08-27 `--driver ch21pocket`, and
    reproduced offline 2026-09-01 by `probe_ch21_leg3_constants.py` CONTROL 3): from
    CAVE_OF_ORIGIN_B1F with nothing but the player loaded, BOTH `(31,17)->(43,32)` and
    `(31,17)->(29,53)` raise `PathFindingError`; standing at (31,17) after the warp, with objects
    `[(255,(31,17)), (1,(30,18)), (7,(32,18))]` loaded, the same calls return 121 and 118
    waypoints. NOT MEASURED: that Steven (local_id 7) is the CAUSE. Two other things also changed
    (the bot is on the map, and it is standing on a different tile), and a 2026-09-01 A/B showed
    that merely standing on SOOTOPOLIS_CITY does not open the pocket either.

    ⇒ therefore this gate asserts THE THING THE LEG ACTUALLY NEEDS — that a path exists right now —
    and REPORTS the object list as evidence rather than asserting a causal story. A failure here is
    loud, immediate, and carries the diagnostic either way.
    """
    from modules.console import console
    from modules.map import get_map_objects
    from modules.map_path import PathFindingError, calculate_path
    from modules.modes import BotModeError

    objects = [(o.local_id, tuple(o.current_coords)) for o in get_map_objects()]
    console.print(f"[cyan]Ch21 leg 3: objects loaded at {_where()}: {objects}[/]")
    steven_loaded = any(local_id == 7 for local_id, _ in objects)

    here = tuple(_here_tile())
    try:
        path = calculate_path((MapRSE.SOOTOPOLIS_CITY, here), (MapRSE.SOOTOPOLIS_CITY, target))
    except PathFindingError as error:
        raise BotModeError(
            f"Ch21 leg 3: no route from {here} to {target} in Sootopolis ({error}). Objects loaded: "
            f"{objects} (Steven, local_id 7, present={steven_loaded}). This is the POCKET: the same "
            "call refuses from off-map and succeeds standing here with the escort NPCs loaded. "
            "⛔ Do NOT retry blindly — the pocket allows ONE crossing per visit, so a refusal here "
            "means the run must walk back to the resting tile before anything else."
        ) from error
    console.print(
        f"[cyan]Ch21 leg 3: pocket is OPEN — {len(path)} waypoints {here} -> {target} "
        f"(steven_loaded={steven_loaded}).[/]"
    )
    return path


def _cross_the_pocket(target: tuple[int, int], *, tries: int = 3) -> Generator:
    """Cross Sootopolis's sealed pocket: PLAN ONCE AT THE RESTING TILE, THEN FOLLOW BLIND.

    ⛔⛔ NEVER `navigate_to` AND NEVER `_navigate_riding_out` HERE, AND THIS IS VERIFIED IN CODE,
    not inferred. `navigate_to` wraps `follow_waypoints` in `while True: except
    TimedOutTryingToReachWaypointError` and RE-ENTERS the waypoint generator, which recomputes the
    path from the new location (walking.py:~458-470; its own comment says so). `_navigate_riding_out`
    calls `navigate_to_anywhere` afresh on every retry (early_game.py:236-270). A re-plan from
    inside the pocket REFUSES — measured: 89 of this route's ~121 waypoints cannot plan an escape
    once the escort objects unload — so a helper that re-plans on timeout converts a recoverable
    stall into a stranded run.

    ‼ THE RECOVERY BELOW IS A DESIGN, NOT A RESULT. Its walk-back half IS measured (from all 89
    danger-zone waypoints a path back to the resting tile exists). What has NEVER been observed is
    (i) that arriving at the resting tile a SECOND time re-opens the pocket live, and (ii) that the
    retry loop terminates rather than oscillating. ⛔ That is why `POKEBOT_CH21_FAULT_POCKETSTALL=1`
    is mandatory and must not be dropped because the happy path passed — leg 2a shipped a bail that
    was dead code for exactly that reason, and it cost a drive.

    :return: the number of crossing attempts that were made (1 when nothing went wrong).
    """
    import os as _os_fault

    from modules.console import console
    from modules.modes import BotModeError
    from modules.modes.util.walking import TimedOutTryingToReachWaypointError, follow_waypoints
    from modules.map_path import PathFindingError, calculate_path
    from modules.story.early_game import _check_abort

    fault_stall = _os_fault.environ.get("POKEBOT_CH21_FAULT_POCKETSTALL", "").strip() == "1"
    fault_walkback = _os_fault.environ.get("POKEBOT_CH21_FAULT_POCKETWALKBACK", "").strip() == "1"

    for attempt in range(tries):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try
        path = _assert_pocket_is_open(target)
        try:
            if fault_stall and attempt == 0:
                # ‼ FAULT INJECTION (driver-proof only). Truncating at index 40 of ~121 puts the
                # simulated stall INSIDE the danger zone, where a fresh plan would refuse and the
                # walk-back is ~45 waypoints — i.e. it exercises the recovery for real rather than
                # from a tile that could have re-planned anyway.
                console.print("[magenta]Ch21 leg 3 FAULT POCKETSTALL: truncating the pocket path "
                              "at waypoint 40 and raising a waypoint timeout.[/]")
                yield from follow_waypoints(path[:40])
                raise TimedOutTryingToReachWaypointError(path[40])
            yield from follow_waypoints(path)
        except TimedOutTryingToReachWaypointError as error:
            # ⛔ This except MUST come before any `except BotModeError` — the timeout is a SUBCLASS
            # of BotModeError (walking.py:103), so the broader clause would swallow it silently.
            here = _here_tile()
            console.print(
                f"[yellow]Ch21 leg 3: the pocket crossing stalled at {here} on attempt "
                f"{attempt + 1}/{tries} ({error}). Walking BACK to {POCKET_RELOAD_TILE} to re-open "
                f"the pocket before re-planning — a fresh plan from here would refuse.[/]"
            )
            try:
                back = calculate_path(
                    (MapRSE.SOOTOPOLIS_CITY, here), (MapRSE.SOOTOPOLIS_CITY, POCKET_RELOAD_TILE)
                )
            except PathFindingError as inner:
                raise BotModeError(
                    f"Ch21 leg 3: stalled at {here} inside the pocket AND cannot path back to "
                    f"{POCKET_RELOAD_TILE} ({inner}). This is the stranded case the plan-once rule "
                    "exists to prevent; it has never been observed and needs eyes."
                ) from inner
            # ⛔⛔ THE WALK BACK IS GUARDED AGAINST THE **SAME** EXCEPTION IT IS RECOVERING FROM,
            # AND IT WAS NOT UNTIL AN ADVERSARIAL REVIEW CAUGHT IT (2026-09-01). Unguarded, a second
            # timeout — here, on the ~45-waypoint return leg — would propagate straight out of this
            # `for attempt in range(tries)` loop, skipping the remaining attempts AND replacing the
            # purpose-written "stranded" message with a raw `TimedOutTryingToReachWaypointError`.
            # ‼ It is not a contrived case: the walk back crosses the very tiles whose live NPCs
            # DEFINE the pocket — `_assert_pocket_is_open` logs Steven (local_id 7) and at least one
            # other escort object standing on them — so "the recovery's own walk gets interrupted"
            # is the single most plausible way this leg fails on a rerun.
            try:
                if fault_walkback and attempt == 0:
                    # ‼ FAULT INJECTION (driver-proof only): the ONLY way to execute this branch.
                    # The happy path cannot reach it, and neither can POCKETSTALL, which always lets
                    # the walk-back succeed.
                    console.print("[magenta]Ch21 leg 3 FAULT POCKETWALKBACK: truncating the walk-back "
                                  "and raising a second waypoint timeout.[/]")
                    yield from follow_waypoints(back[:5])
                    raise TimedOutTryingToReachWaypointError(back[5] if len(back) > 5 else back[-1])
                yield from follow_waypoints(back)
            except TimedOutTryingToReachWaypointError as second:
                raise BotModeError(
                    f"Ch21 leg 3: the pocket crossing stalled at {here}, and the walk BACK to "
                    f"{POCKET_RELOAD_TILE} then stalled too ({second}). The run is inside a 347-tile "
                    "pocket it cannot re-plan out of — this is the stranded case the plan-once rule "
                    "exists to prevent. ⛔ Do not retry from here: a fresh plan from an unknown tile "
                    "inside the pocket REFUSES, which is the whole reason the recovery walks back to "
                    "a known tile first."
                ) from second
            if not _at(MapRSE.SOOTOPOLIS_CITY, POCKET_RELOAD_TILE):
                raise BotModeError(
                    f"Ch21 leg 3: walked back toward {POCKET_RELOAD_TILE} but ended at {_where()}. "
                    "⛔ Never re-plan the pocket from an unknown tile."
                )
            continue
        if not _at(MapRSE.SOOTOPOLIS_CITY, target):
            raise BotModeError(
                f"Ch21 leg 3: followed the pocket path without a timeout but ended at {_where()}, "
                f"not {target}."
            )
        return attempt + 1

    raise BotModeError(
        f"Ch21 leg 3: could not cross the pocket to {target} in {tries} attempts. The pocket allows "
        "ONE crossing per visit, so each attempt costs a full walk back to "
        f"{POCKET_RELOAD_TILE}; a third failure means the crossing premise itself is wrong."
    )


def approach_sky_pillar(report: dict | None = None) -> Generator:
    """LEG 3 — THE APPROACH: out of the Cave of Origin, across Sootopolis, and to the Sky Pillar door.

    ⛔⛔ WHERE THIS LEG STARTS AND STOPS, because both ends were got wrong at least once.
    START: the PINNED fixture `post_wallace.ss1` stands on **CAVE_OF_ORIGIN_B1F (9,14)**, not on
    SOOTOPOLIS_CITY (31,17). (31,17) is where the ROUTE starts; the FIXTURE is three warps behind
    it. So leg 3 OWNS the cave return, or it is not independently drivable from the thing it is
    handed.
    STOP: standing on **SKY_PILLAR_ENTRANCE**, having PROVED it can continue. ⛔ It must never take
    SKY_PILLAR_ENTRANCE (14,4): that warp leads to SKY_PILLAR_OUTSIDE, whose ON_FRAME Wallace scene
    fires at `SOOTOPOLIS_CITY_STATE == 3` with NO coordinate condition and drives the player ~12
    tiles under `lockall`. Riding that is LEG 4's first job, and a `calculate_path` aimed at (14,4)
    crosses the seam SILENTLY — MEASURED-PROD 2026-09-01: the same call that returns 21 waypoints
    and `is_warp=False` for (14,3) returns 21 waypoints and `is_warp=True` ENDING ON
    SKY_PILLAR_OUTSIDE (17,13) for (14,4).

    ⛔ WHAT THIS LEG MUST NOT DO. It must not advance `SOOTOPOLIS_CITY_STATE` past 3 or touch
    `SKY_PILLAR_STATE` (state 4 is written by the Wallace door scene, i.e. by leg 4). It must not
    touch SKY_PILLAR_1F..TOP, must not implement either deliberate fall, and must not contain
    `mount_bike` in any form — the bot is bikeless here (MEASURED-PROD: `RECEIVED_BIKE` False) and
    `puzzle_solver.py:39-42` is `while not is_on_bike: press Select`, an infinite hang for a
    bikeless bot.

    ‼ GRADING (house rule 8). §Ch15, §Ch18 and §Ch19 each PASSED their own acceptance test while
    leaving the bot STRANDED, so "the walk finished" is not the grade. This returns a readings dict
    and the driver grades on DID EVERY READING ACTUALLY HAPPEN **and can the bot CONTINUE** — the
    latter being a real `calculate_path` off the tile the run reached, not a `controllable` flag.

    :param report: an OPTIONAL dict OWNED BY THE CALLER, filled in as the leg progresses.
        ⛔⛔ IT IS AN ARGUMENT, NOT JUST A RETURN VALUE, AND THAT IS THE WHOLE POINT. The first
        leg-3 drive (2026-09-01) failed partway and its driver printed `readings=[]` with all
        thirteen labels `missing` (thirteen AT THE TIME — the set is 14 now, R-CONTROL joined later) — while the console above it showed R-CAVE, R-POCKET and R-HEAL
        had all been taken. The readings lived in a local that the raising generator never
        returned, so the ONE artefact a future agent reads said the leg had measured nothing. A
        run that dies is exactly the run whose partial readings matter most.
    :return: the same dict, for callers that would rather have it as a return value.
    """
    import os as _os_fault

    from modules.console import console
    from modules.map import get_map_data_for_current_position
    from modules.map_data import PokemonCenter
    from modules.map_path import PathFindingError, calculate_path
    from modules.memory import get_event_flag
    from modules.modes import BotModeError
    from modules.modes.util.higher_level_actions import dive, heal_in_pokemon_center, surface_from_dive
    from modules.modes.util.walking import navigate_to
    from modules.player import AvatarFlags, get_player_avatar
    from modules.pokemon_party import get_party
    from modules.story.early_game import (
        _check_abort,
        _navigate_riding_out,
        _walk_through_warp,
        wait_until_truly_controllable,
    )

    fault_blindwall = _os_fault.environ.get("POKEBOT_CH21_FAULT_BLINDWALL", "").strip() == "1"

    #: ⛔ READINGS ARE ADDED **AT THE POINT THE READING IS TAKEN**, never by appending step labels
    #: as the code walks past them. That is the exact defect `Ch21PocketExitMode` v1 shipped: it
    #: counted `legs_done`, which appended its last label unconditionally, so the acceptance line
    #: reported a reading that had not happened.
    if report is None:
        report = {}
    readings: set[str] = report.setdefault("readings", set())
    report.setdefault("pocket_attempts", 0)
    # ⛔ ANYTHING WITH MULTIPLICITY IS A COUNTER, NEVER A LABEL. `readings` is a set and `.add()` is
    # idempotent, so a label added once before a loop is indistinguishable from one added after
    # sixteen confirmed tiles — which is exactly the defect `Ch21PocketExitMode` v1 shipped. These
    # count the ACTION, and the driver re-checks them itself rather than trusting the labels.
    report.setdefault("tail_tiles_confirmed", 0)
    report.setdefault("tail_tiles_expected", len(DOOR_APPROACH))
    report.setdefault("blind_steps_taken", 0)
    # ⛔ AND THIS ONE GRADES THE METHOD, NOT THE DESTINATION. Exactly TWO planner calls are
    # permitted on ROUTE131 — the swim and the staging walk. A third means something re-planned
    # north of y=14, where our planner returns a confident route through solid rock.
    report.setdefault("planner_calls_on_route131", 0)

    yield from wait_until_truly_controllable()

    # --- 0. PREFLIGHT — refuse loudly HERE, not 300 waypoints out in an ocean --------------------
    if at_sky_pillar_door():
        context.message = "Story: Ch21 — already at the Sky Pillar door; leg 3 is done."
        report["resumed"] = True
        return report

    state = _var("SOOTOPOLIS_CITY_STATE")
    pillar_state = _var("SKY_PILLAR_STATE")
    if state != 3:
        raise BotModeError(
            f"Ch21 leg 3: SOOTOPOLIS_CITY_STATE is {state!r}, expected exactly 3. Below 3 means leg "
            "2b has not run (Wallace has not been told where Rayquaza is); above 3 means the Sky "
            "Pillar door scene already played and this leg is SPENT."
        )
    if not wallace_sent_to_sky_pillar():
        raise BotModeError(
            "Ch21 leg 3: SOOTOPOLIS_CITY_STATE is 3 but WALLACE_GOES_TO_SKY_PILLAR is CLEAR. Those "
            "two are written by the SAME seven-line script block, so disagreement is a MISREAD, "
            "not a half-run."
        )
    if pillar_state != 0:
        raise BotModeError(
            f"Ch21 leg 3: SKY_PILLAR_STATE is {pillar_state!r}, expected 0. This leg must not run "
            "after the tower has been entered — it does not know how to resume a climb."
        )
    if AvatarFlags.Underwater in get_player_avatar().flags:
        raise BotModeError(
            f"Ch21 leg 3: the run is already UNDERWATER at {_where()}. This leg dives from the "
            "surface and cannot recover from that — surface manually first."
        )
    # ‼ These are literally `map_path.py`'s own can_surf / can_dive conditions. A missing HM here
    # would otherwise kill the run ~300 waypoints out with a PathFindingError that names nothing,
    # and a missing DIVE user would turn `dive()` — an unbounded A-mash — into a silent forever-loop.
    party = get_party()
    for move, badge in (("Surf", "BADGE05_GET"), ("Dive", "BADGE07_GET")):
        if not get_event_flag(badge):
            raise BotModeError(f"Ch21 leg 3: {badge} is not set, so {move} cannot be used in the field.")
        if not party.has_pokemon_with_move(move, True):
            raise BotModeError(
                f"Ch21 leg 3: no party member knows {move} with PP to spare. Sootopolis is a TRUE "
                "ISLAND with zero map connections and no Fly user on this fixture, so both Surf "
                "and Dive are required to leave it at all."
            )

    # --- 1. THE CAVE RETURN — leg 3 owns it (the fixture is three warps behind the route) --------
    # ✅ `_navigate_riding_out` is CORRECT here and re-planning is SAFE: there is no pocket inside
    # the cave, and 1F carries live encounters that abort a path — which is exactly what that
    # helper exists for (a drive measured 2 encounters on the way out).
    for source_map, warp_tile, expect_map in (
        (MapRSE.CAVE_OF_ORIGIN_B1F, (9, 3), MapRSE.CAVE_OF_ORIGIN_1F),
        (MapRSE.CAVE_OF_ORIGIN_1F, (11, 17), MapRSE.CAVE_OF_ORIGIN_ENTRANCE),
        (MapRSE.CAVE_OF_ORIGIN_ENTRANCE, (9, 20), MapRSE.SOOTOPOLIS_CITY),
    ):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try
        if not _on_map(source_map):
            continue  # skip-if-already-past, so a resumed run does not walk backwards
        context.message = f"Story: Ch21 leg 3 — leaving {source_map.name} via {warp_tile}."
        yield from _navigate_riding_out(source_map, warp_tile, tries=6)
        yield from wait_until_truly_controllable()
        if not _on_map(expect_map):
            raise BotModeError(
                f"Ch21 leg 3: stepped the {source_map.name} warp at {warp_tile} but landed on "
                f"{_where()} instead of {expect_map.name} — a warp mis-fired."
            )

    if not _at(MapRSE.SOOTOPOLIS_CITY, POCKET_RELOAD_TILE):
        raise BotModeError(
            f"Ch21 leg 3: out of the cave but standing at {_where()}, not the MEASURED resting "
            f"tile {POCKET_RELOAD_TILE}. ⛔ (31,16) is the warp EVENT tile, so a reading of (31,16) "
            "means the door-exit step did not happen and the ATLAS ROW must be corrected — not "
            "this constant."
        )
    readings.add("R-CAVE")
    console.print(f"[cyan]Ch21 leg 3 R-CAVE: out of the cave, standing at {_where()}.[/]")

    # --- 2. THE POCKET — plan ONCE at the resting tile, then follow BLIND ------------------------
    report["pocket_attempts"] = yield from _cross_the_pocket(POCKET_EXIT_TARGET)
    readings.add("R-POCKET")
    console.print(
        f"[cyan]Ch21 leg 3 R-POCKET: crossed to {_where()} in "
        f"{report['pocket_attempts']} attempt(s).[/]"
    )

    # --- 3. HEAL, ASSERTED BY PID ---------------------------------------------------------------
    # ⛔ UNCONDITIONAL ON PURPOSE, and this is a deliberate divergence from the BUILD SPEC's
    # "heal only if somebody is hurt" (recorded in 06-DECISIONS-LOG.md). Two reasons, both safety:
    #   (1) healing PINS THE WHITEOUT RESPAWN to Sootopolis immediately before the longest unbroken
    #       stretch in the chapter — ~392 water waypoints across six routes with 39 undefeated
    #       trainers and NO Poke Center en route. A whiteout out there without this costs the swim
    #       AND lands the run somewhere it did not choose.
    #   (2) a conditional heal is DEAD CODE on the pinned fixture (party is 687/687), and the spec
    #       had to invent a `FORCEHEAL` fault arm purely to reach it. Making it unconditional means
    #       the by-PID assertion below is exercised on EVERY run — which is strictly better than a
    #       branch kept alive by an environment variable.
    before = [(m.personality_value, m.current_hp, m.total_hp) for m in get_party() if m is not None]
    context.message = "Story: Ch21 leg 3 — healing at the Sootopolis Poke Center."
    yield from heal_in_pokemon_center(PokemonCenter.SootopolisCity)
    yield from wait_until_truly_controllable()
    after = {m.personality_value: (m.current_hp, m.total_hp) for m in get_party() if m is not None}
    # ⛔ BY PID, NEVER BY SLOT OR COUNT. A count that nets to zero (one deposited, one caught) reads
    # TRUE when nothing happened, and `heal_in_pokemon_center` asserts nothing about the outcome
    # itself. A MISSING pid means the PC piggybacked a deposit — and if it took the Dive user, the
    # dive below becomes an unbounded A-mash.
    # ‼ BE HONEST ABOUT WHICH HALF OF THIS CHECK DISCRIMINATES. The **PID-presence** half is
    # load-bearing on every run — it is the only thing standing between a silent deposit and an
    # unbounded A-mash. The **full-HP** half only discriminates when the party actually arrived
    # damaged; on a fixture that starts 687/687 and takes no damage in the cave it is satisfied
    # before the heal is even called, and it must NOT be read as evidence that the heal worked.
    for personality_value, _hp, _total in before:
        if personality_value not in after:
            raise BotModeError(
                f"Ch21 leg 3: the party member with PID {personality_value} is GONE after the heal "
                f"(before={len(before)} members, after={len(after)}). The Poke Center trip "
                "piggybacked a deposit; if that was the Surf or Dive user the run cannot leave "
                "Sootopolis at all."
            )
        current, total = after[personality_value]
        if current != total:
            raise BotModeError(
                f"Ch21 leg 3: PID {personality_value} is {current}/{total} after healing, not full. "
                "The heal did not complete."
            )
    if not _on_map(MapRSE.SOOTOPOLIS_CITY):
        raise BotModeError(f"Ch21 leg 3: after healing the run is at {_where()}, not in Sootopolis.")
    # ⛔ RE-CHECK THE TWO HMs **AFTER** THE HEAL, because the Poke Center trip can legitimately
    # change the party. `heal_in_pokemon_center` calls `deposit_dead_weight_if_worth_it()`
    # (higher_level_actions.py:352-356), which self-gates on a rotation plan and reads NOTHING off
    # the bot mode — so a brand-new driver inherits it. The PID loop above already catches a
    # deposit; this names the CONSEQUENCE precisely, and it is the difference between failing here,
    # in a Poke Center, and failing at the dive tile inside `dive()`'s unbounded A-mash.
    after_party = get_party()
    for move in ("Surf", "Dive"):
        if not after_party.has_pokemon_with_move(move, True):
            raise BotModeError(
                f"Ch21 leg 3: after the Poke Center trip no party member knows {move} with PP. The "
                "heal piggybacked a party change and took the HM user; Sootopolis is a true island "
                "and the run cannot leave it."
            )
    readings.add("R-HEAL")
    console.print(f"[cyan]Ch21 leg 3 R-HEAL: {len(after)} party members at full HP, asserted by PID.[/]")

    # --- 4. TO THE DIVE TILE --------------------------------------------------------------------
    # ✅ Re-planning is CORRECT here and ONLY here in the city: the pocket is BEHIND us and
    # (43,32)->(29,53) is 37 waypoints with NOTHING loaded (MEASURED-PROD), so a fresh plan cannot
    # refuse. ⚠ Known but off-route: `SootopolisCity_OnLoad` `setmetatile`s ten doors CLOSED at
    # state 3 and our planner cannot see that (KI-74); none of the ten is on this path.
    # ⛔⛔ PIN THE PLANNER TO THE LAYOUT THE GAME IS RUNNING **BEFORE** THIS WALK. This is the fix
    # for the FIRST leg-3 drive's only failure (2026-09-01): it walked out of the Poke Center and
    # jammed at (31,42) because `calculate_path` was planning on Sootopolis's STATIC layout, whose
    # x=27..35 / y=43..45 block is open water — while the LEGENDS_BATTLE layout the game runs at
    # state 3 makes all 27 of those tiles solid. The planned route's FIRST waypoint (31,43) was
    # inside the block. MEASURED both ways on the drive's own stall state: static-seeded the walk is
    # 37 waypoints through rock, live-seeded it is 35 and correct.
    # ‼ IT IS DONE **HERE** AND NOT EARLIER ON PURPOSE. The pocket crossing above is DRIVEN and
    # PROVEN as it stands, and re-seeding the layout under it would change a step that already
    # works — so the pin happens once the pocket is behind us and only affects the walk that failed.
    console.print(f"[cyan]Ch21 leg 3: {_pin_planner_to_live_layout(MapRSE.SOOTOPOLIS_CITY)}[/]")
    context.message = "Story: Ch21 leg 3 — walking to the dive tile."
    yield from _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, DIVE_OUT_TILE, tries=6)
    if not _at(MapRSE.SOOTOPOLIS_CITY, DIVE_OUT_TILE):
        raise BotModeError(f"Ch21 leg 3: aimed at the dive tile {DIVE_OUT_TILE} but am at {_where()}.")

    # --- 5. DIVE, GUARDED -----------------------------------------------------------------------
    # ⛔ THE TILE GUARD IS A TUPLE, NEVER A SINGLE LITERAL. Our STATIC reader calls this tile
    # 'Sootopolis Deep Water' while the LIVE LEGENDS_BATTLE layout calls it 'Deep Water', and which
    # one we get depends on which reader seeded `_map_layout_cache` first (see
    # `_route131_layout_reading`). A single-literal guard would REFUSE A CORRECT RUN.
    tile_type = getattr(get_map_data_for_current_position(), "tile_type", None)
    if tile_type not in ("Deep Water", "Interior Deep Water", "Semi-Deep Water", "Sootopolis Deep Water"):
        raise BotModeError(
            f"Ch21 leg 3: standing on {DIVE_OUT_TILE} but it reads {tile_type!r}, which is not a "
            "divable water tile. Diving here would A-mash forever."
        )
    context.message = "Story: Ch21 leg 3 — diving out of Sootopolis."
    yield from dive()
    yield from wait_until_truly_controllable()
    if not _on_map(MapRSE.UNDERWATER_SOOTOPOLIS_CITY):
        raise BotModeError(f"Ch21 leg 3: dived at {DIVE_OUT_TILE} but ended at {_where()}.")
    readings.add("R-DIVE")
    # ⛔ REPORTED, NOT ASSERTED: the decomp fixes this at `SootopolisCity_OnResume: setdivewarp
    # MAP_UNDERWATER_SOOTOPOLIS_CITY, 9, 6`, but a mismatch corrects the atlas rather than killing
    # a run that is otherwise going fine.
    console.print(f"[cyan]Ch21 leg 3 R-DIVE: underwater at {_where()} (decomp predicts (9,6)).[/]")

    # --- 6. UNDERWATER, THEN SURFACE ------------------------------------------------------------
    # ‼ NO NEW PRIMITIVE, AND NO HAND-WRITTEN WALK. Targeting (9,8) returns a short path whose LAST
    # waypoint is already UNDERWATER_ROUTE126 (45,65) with is_warp=True and the held SOUTH direction
    # attached (MEASURED-PROD: 3 wp, ends (45,65), is_warp=True) — `navigate_to` overrides its own
    # destination when `waypoints[-1].is_warp`. That warp fires ONLY while SOUTH is HELD, which is
    # why a hand-written walk onto the tile stalls forever. ⛔ Do NOT target (10,8): it is plain
    # 'Deep Water' (MEASURED-PROD) and its header warp can never fire.
    context.message = "Story: Ch21 leg 3 — swimming to the Route 126 underwater exit."
    yield from navigate_to(MapRSE.UNDERWATER_SOOTOPOLIS_CITY, UW_EXIT_WARP, False)
    yield from wait_until_truly_controllable()
    # ⛔ ASSERT THE MAP, REPORT THE TILE. (45,65) is the warp's TARGET; where the avatar RESTS
    # after an arrow warp has never been measured on this map. Hard-asserting a warp TARGET is the
    # exact defect this project already paid for once — `story_harness.py` records it against its
    # own v1: "LANDING = (31,17) ⛔ where the avatar RESTS — MEASURED. v1 graded on WARP_TARGET and
    # therefore printed landing_ok=False on a perfectly CORRECT run". The map change is the
    # load-bearing half; the tile is checked one step later by the ROUTE126 assertion, where a
    # mismatch can be named precisely because surfacing is (x,y)-preserving.
    if not _on_map(MapRSE.UNDERWATER_ROUTE126):
        raise BotModeError(
            f"Ch21 leg 3: aimed at the {UW_EXIT_WARP} arrow warp but am at {_where()}, not on "
            "UNDERWATER_ROUTE126. That warp fires ONLY while SOUTH is HELD; if this raises, check "
            "that the path's final held-direction waypoint survived."
        )
    underwater_rest = _here_tile()
    report["uw_rest"] = underwater_rest
    console.print(
        f"[cyan]Ch21 leg 3: surfaced-side warp landed on UNDERWATER_ROUTE126 {underwater_rest} "
        f"(the warp TARGET is {R126_SURFACE_TILE}; a difference is a resting-tile FINDING, not a "
        "failure).[/]"
    )
    yield from surface_from_dive()
    yield from wait_until_truly_controllable()
    # ⛔ ASSERT THE MECHANIC, NOT A COORDINATE. Emerging preserves (x, y), so the tile we surface on
    # MUST equal the underwater tile we left from — and that is an invariant the run can check
    # against the state it actually reached, rather than against a literal somebody transcribed
    # from an atlas row. Drive 3 (2026-09-01) is why: both build-spec critics hard-asserted the warp
    # TARGET (45,65), the avatar actually rests on (45,66), and a correct run failed on a constant.
    # The literal below is used only to REPORT whether reality matched the prediction.
    surface_tile = _here_tile()
    report["surface_tile"] = surface_tile
    report["surface_matches_prediction"] = surface_tile == R126_SURFACE_TILE
    if not _on_map(MapRSE.ROUTE126):
        raise BotModeError(f"Ch21 leg 3: surfaced onto {_where()}, which is not ROUTE126.")
    if surface_tile != underwater_rest:
        raise BotModeError(
            f"Ch21 leg 3: surfaced onto ROUTE126 {surface_tile} but submerged from "
            f"{underwater_rest}. Emerging is (x,y)-preserving, so a coordinate CHANGE is itself the "
            "finding — the emerge did not happen where it was supposed to."
        )
    console.print(
        f"[cyan]Ch21 leg 3: surfaced on ROUTE126 {surface_tile} (prediction {R126_SURFACE_TILE}, "
        f"match={report['surface_matches_prediction']}); (x,y) preserved from {underwater_rest}.[/]"
    )
    if AvatarFlags.Underwater in get_player_avatar().flags:
        raise BotModeError("Ch21 leg 3: surfaced but the Underwater flag is still set.")
    readings.add("R-SURFACE")
    console.print(f"[cyan]Ch21 leg 3 R-SURFACE: on the surface at {_where()}.[/]")

    # --- 7. THE SWIM: ONE CALL, ~322 WAYPOINTS, SIX MAPS ----------------------------------------
    # ✅ Re-planning is SAFE here (no pocket) and NECESSARY: 39 undefeated trainers sit across the
    # six maps and the planner models sight lines NOT AT ALL, so a path is aborted often. `tries` is
    # deliberately far above the default — budget one per interruption. ✅ AUDITED (MEASURED-ROM):
    # the plan's 23 ROUTE131 waypoints run along y=23 and NONE of them is in the 116-tile
    # open-to-us / wall-in-the-live-layout set.
    context.message = "Story: Ch21 leg 3 — the long swim to Route 131 (six maps)."
    report["planner_calls_on_route131"] += 1
    yield from _navigate_riding_out(MapRSE.ROUTE131, R131_SWIM_TARGET, tries=30)
    if not _at(MapRSE.ROUTE131, R131_SWIM_TARGET):
        raise BotModeError(
            f"Ch21 leg 3: the swim ended at {_where()}, not ROUTE131 {R131_SWIM_TARGET}. The plan "
            "crosses ROUTE126:51 127:51 128:57 129:60 130:80 131:23 waypoints, so the map named "
            "above says WHERE it died."
        )
    readings.add("R-SWIM")
    console.print(f"[cyan]Ch21 leg 3 R-SWIM: at {_where()} after the six-map swim.[/]")

    # --- 8. THE LAYOUT READING — free, and it settles the premise the rest of the leg rests on ---
    layout_reading, planner_agrees_with_game = _route131_layout_reading()
    report["r131_layout"] = layout_reading
    report["r131_planner_agrees"] = planner_agrees_with_game

    # ⛔⛔ AND NOW THE READING THAT ACTUALLY DECIDES WHETHER THE REST OF THIS LEG IS WALKABLE.
    # Comparing layout POINTERS says which map the planner is on; it does not say whether the 17
    # tiles we are about to step on are open. `gBackupMapLayout` is the grid THE GAME WALKS ON, so
    # asking it about those exact tiles turns the leg's single biggest assumption — 16 hand-walked
    # steps with no planner, no refusal and no fallback — into a MEASUREMENT taken while the bot is
    # still standing safely on the swim's end tile.
    # ‼ This check exists because the first drive (2026-09-01) proved the failure mode is real on a
    # DIFFERENT map: in Sootopolis the planner was on the static layout and walked into a 9x3 block
    # of live walls. Route 131 swaps its layout too, so the same class of error was one drive away.
    planned_tiles = [R131_BLIND_STEP] + [tile for _direction, tile in DOOR_APPROACH] + [SKY_PILLAR_DOOR]
    live_walls = _live_wall_tiles(MapRSE.ROUTE131, planned_tiles)
    report["r131_live_walls"] = live_walls
    readings.add("R-LAYOUT")
    console.print(f"[cyan]Ch21 leg 3 R-LAYOUT: ROUTE131 {layout_reading}[/]")
    console.print(
        f"[cyan]Ch21 leg 3 R-LAYOUT: of the {len(planned_tiles)} tiles this leg will step on, "
        f"the GAME calls {len(live_walls)} of them WALLS: {live_walls or 'NONE'}[/]"
    )
    if live_walls:
        raise BotModeError(
            f"Ch21 leg 3: the live map grid says {len(live_walls)} of the tiles this leg is about "
            f"to walk are WALLS: {live_walls}. The hand-walked tail has no planner, no refusal and "
            "no fallback, so continuing would jam the run at the end of a one-shot swim. The tail "
            "was adjudicated against our ROM's Route131_SkyPillar layout by "
            "`probe_ch21_route131_tail.py`; if the game disagrees, RE-MEASURE with that probe — do "
            "not nudge the constants. ⛔ The alternate tail `DOOR_APPROACH_FALLBACK` is the other "
            "ROM-verified column and is a one-line swap if only the x=36 column is blocked."
        )
    if planner_agrees_with_game:
        # ⛔ NOT A FAILURE — A FINDING, AND A LOUD ONE. If the planner is already on the live layout
        # then the door is visible to it and the 16 hand-walked steps are unnecessary (though still
        # harmless: every one of their tiles is walkable in that layout too). Say so rather than
        # silently continuing, because it would mean the blindness premise has changed.
        console.print(
            "[magenta]‼ Ch21 leg 3: the planner and the game agree on ROUTE131's layout. The "
            "hand-walked tail was designed for the case where they DISAGREE. The steps below are "
            "still valid, but this reading contradicts the premise and belongs in the docs.[/]"
        )

    # --- 9. BLIND STEP 1 — the hard precondition ------------------------------------------------
    # ⛔ ON FAILURE, ABORT THE CHAPTER; DO NOT FALL BACK TO STEP 10 FROM (40,20). See
    # `_LEG3_FALLBACK_IS_FATAL`: the 35-waypoint plan from (40,20) is forced through live rock.
    context.message = "Story: Ch21 leg 3 — the blind step onto (40,19)."
    yield from _bounded_step("Up", expect=R131_BLIND_STEP, map_enum=MapRSE.ROUTE131)
    report["blind_steps_taken"] += 1
    readings.add("R-BLIND")
    console.print(
        f"[cyan]Ch21 leg 3 R-BLIND: standing on {_where()} — a tile our own planner calls a WALL. "
        "This is the first time this project has executed a blind step onto a static-wall tile.[/]"
    )

    # --- 10. TO THE STAGING TILE — the LAST planner call permitted on ROUTE131 -------------------
    report["planner_calls_on_route131"] += 1
    yield from _navigate_riding_out(MapRSE.ROUTE131, R131_STAGING, tries=6)
    if not _at(MapRSE.ROUTE131, R131_STAGING):
        raise BotModeError(
            f"Ch21 leg 3: aimed at the staging tile {R131_STAGING} but am at {_where()}. It is 16 "
            "waypoints from (40,19) and 35 waypoints THROUGH LIVE ROCK from (40,20), so if this "
            "took the long way the blind step silently did not happen."
        )
    readings.add("R-STAGING")
    console.print(f"[cyan]Ch21 leg 3 R-STAGING: at {_where()}. ⛔ No planner call from here on.[/]")

    # --- 11. THE 16 HAND-WALKED STEPS -----------------------------------------------------------
    # ⛔⛔ NO PLANNER CALL IS PERMITTED FROM HERE TO THE DOOR. Once the bot stands north of y=14 the
    # two components of the map our planner sees are bridged THROUGH IT, and a call to the door
    # returns a CONFIDENT plan whose tiles are solid rock in the layout the game runs. A refusal
    # would have been survivable; that would be a silent derail.
    for index, (direction, expect) in enumerate(DOOR_APPROACH):
        _check_abort()  # ⛔ FIRST statement of the loop body, OUTSIDE any try
        if fault_blindwall and index == 0:
            # ‼ FAULT INJECTION (driver-proof only): substitute the OPPOSITE direction on step 0.
            # The per-step assertion must fire NAMING THE STEP INDEX, and the frame bound must fire
            # rather than hang. This is the only way to prove the blind sequence fails LOUDLY.
            console.print("[magenta]Ch21 leg 3 FAULT BLINDWALL: substituting 'Left' at step 0.[/]")
            yield from _bounded_step("Left", expect=expect, map_enum=MapRSE.ROUTE131, max_frames=120)
        else:
            yield from _bounded_step(direction, expect=expect, map_enum=MapRSE.ROUTE131)
        if not _at(MapRSE.ROUTE131, expect):
            raise BotModeError(
                f"Ch21 leg 3: door-approach step {index} ('{direction}') should have landed on "
                f"{expect} but the run is at {_where()}."
            )
        if expect == (36, 8) and AvatarFlags.Surfing in get_player_avatar().flags:
            # The sequence's single state change: elevation 1 water -> elevation 3 'Sand'. It is
            # free to check and it is the least-proven mechanic in the tail.
            raise BotModeError(
                "Ch21 leg 3: stepped onto the (36,8) 'Sand' tile but the avatar is still SURFING — "
                "the dismount did not happen. The pre-vetted alternate tail "
                "`DOOR_APPROACH_FALLBACK` dismounts at (34,8) instead and is equally live-valid."
            )
        report["tail_tiles_confirmed"] += 1
    if not _at(MapRSE.ROUTE131, DOOR_APRON):
        raise BotModeError(f"Ch21 leg 3: the tail ended at {_where()}, not the door apron {DOOR_APRON}.")
    # ⛔ THE LABEL IS GATED ON THE COUNT, not on reaching the end of the loop: a `break` or a
    # short-circuited iteration would otherwise leave the label indistinguishable from 16 confirmed
    # tiles.
    if report["tail_tiles_confirmed"] != report["tail_tiles_expected"]:
        raise BotModeError(
            f"Ch21 leg 3: the tail loop finished having confirmed only "
            f"{report['tail_tiles_confirmed']} of {report['tail_tiles_expected']} tiles."
        )
    readings.add("R-TAIL")
    console.print(f"[cyan]Ch21 leg 3 R-TAIL: all {len(DOOR_APPROACH)} steps landed; at {_where()}.[/]")

    # --- 12. THE DOOR STEP ----------------------------------------------------------------------
    # ⛔ ASSERT THE MAP CHANGED, NEVER THE COORDINATES. (36,6) is a step-on warp ('Non-Animated
    # Door' in the live layout), so no held direction is needed; a 240-frame timeout is the RIGHT
    # failure if it turns out to be event-gated in some way the decomp does not show.
    context.message = "Story: Ch21 leg 3 — stepping through the Sky Pillar door."
    yield from _walk_through_warp("Up", MapRSE.ROUTE131.value, timeout_frames=240)
    if not at_sky_pillar_door():
        raise BotModeError(f"Ch21 leg 3: stepped through the door but am at {_where()}.")
    readings.add("R-DOOR")

    # --- 13. LAND, SETTLE, READ THE RESTING TILE (report it; never assert it) --------------------
    context.emulator.reset_held_buttons()
    yield from wait_until_truly_controllable()
    rest = _here_tile()
    report["rest"] = rest
    report["rest_matches_prediction"] = rest == ENTRANCE_REST_PREDICTION
    readings.add("R-REST")
    console.print(
        f"[cyan]Ch21 leg 3 R-REST: landed on SKY_PILLAR_ENTRANCE {rest}; the prediction was "
        f"{ENTRANCE_REST_PREDICTION} (match={report['rest_matches_prediction']}). ⛔ A MISMATCH IS "
        "A FINDING, not a failure: this is the resting-tile rule's FIRST arrow-warp target.[/]"
    )
    # ⛔ AND NEVER PRESS OR HOLD 'Down' FROM HERE ON: the arrival tile is a SOUTH arrow warp straight
    # back to Route 131, where the pocket has already re-sealed behind the run.

    # --- 14. THE CONTINUATION PROOF — the leg is GRADED on this ---------------------------------
    try:
        continue_path = calculate_path(
            (MapRSE.SKY_PILLAR_ENTRANCE, rest), (MapRSE.SKY_PILLAR_ENTRANCE, ENTRANCE_CONTINUE)
        )
    except PathFindingError:
        # ⛔ SWALLOWED DELIBERATELY: "there is no path" IS the measurement this block exists to take,
        # not an error in taking it. A refusal here means the bot is STRANDED, and that is graded
        # below as `continue_ok = False` — re-raising would turn a legitimate FAIL verdict into a
        # crash with no ACCEPTANCE line, which is strictly less informative.
        continue_path = None
    # ⛔ WHAT EACH CONJUNCT IS ACTUALLY FOR — stated precisely, because over-reading a PASS is its
    # own defect. `bool(path)` is the LIVE check: it is the one that can fail today, and it is the
    # whole "can the bot CONTINUE" question. The other two CANNOT fail while the target is (14,3),
    # because (14,3) is an ordinary Cave tile on this map and a non-warp destination forces both.
    # They are a REGRESSION GUARD, and a measured one: aiming at (14,4) instead returns a path of
    # the SAME LENGTH with `is_warp=True` ending on SKY_PILLAR_OUTSIDE (17,13) — leg 4's Wallace
    # cutscene. ⇒ keep all three, and do not claim the run "proved" three things when it proved one.
    # ⛔ AND TWO MORE CONJUNCTS THE BUILD SPEC DID NOT HAVE, because the three above inspect ONLY
    # `path[-1]`. A route that stepped out through the (14,4) arrow warp to SKY_PILLAR_OUTSIDE and
    # came back would END on this map with a non-warp final waypoint — satisfying all three — while
    # walking straight through leg 4's Wallace cutscene on the way. So: no waypoint may leave this
    # map, and the path must end exactly where it was aimed.
    # MEASURED-PROD 2026-09-01: the real path is 21 wp and every waypoint's map is (24,77).
    off_map = (
        sorted({tuple(w.map) for w in continue_path} - {MapRSE.SKY_PILLAR_ENTRANCE.value})
        if continue_path else []
    )
    continue_ok = (
        bool(continue_path)
        and tuple(continue_path[-1].map) == MapRSE.SKY_PILLAR_ENTRANCE.value
        and not continue_path[-1].is_warp
        and not off_map
        and tuple(continue_path[-1].coordinates) == ENTRANCE_CONTINUE
    )
    report["continue_wp"] = 0 if continue_path is None else len(continue_path)
    report["continue_is_warp"] = None if continue_path is None else continue_path[-1].is_warp
    report["continue_off_map"] = off_map
    report["continue_ok"] = continue_ok
    if continue_ok:
        readings.add("R-CONTINUE")

    # --- 14b. ⛔⛔ THE CONTROL: THE PLANNER MUST STILL BE ABLE TO **REFUSE** ---------------------
    # A reachability assertion with no matching refusal is a coin that only has heads. Every path
    # reading on this leg is taken through `modules.map._map_layout_cache` / `modules.map_path._maps`
    # — process globals that this very leg writes to (it pins Sootopolis to the live layout, and
    # KI-73 is the standing issue). A cache left in an over-permissive state would make the
    # continuation proof succeed unconditionally, and nothing above would notice.
    # ⇒ ask the SAME function, from the SAME tile, for a tile that MUST be unreachable.
    # MEASURED-PROD 2026-09-01: SKY_PILLAR_ENTRANCE (6,17) is 'Normal', collision 1, and
    # `calculate_path((ENTRANCE, (6,16)), (ENTRANCE, (6,17)))` RAISES. It is directly south of the
    # arrival tile, so it is also the cheapest possible negative control to reason about.
    control_target = (6, 17)
    try:
        control_path = calculate_path(
            (MapRSE.SKY_PILLAR_ENTRANCE, rest), (MapRSE.SKY_PILLAR_ENTRANCE, control_target)
        )
    except PathFindingError:
        # ⛔ SWALLOWED DELIBERATELY, AND HERE THE EXCEPTION IS THE **PASS** CONDITION: this is the
        # negative control, and a refusal is exactly what it must produce. Raising would invert the
        # check into "the control failed" when the control in fact SUCCEEDED.
        control_path = None
    control_refused = control_path is None
    report["control_refused"] = control_refused
    if control_refused:
        readings.add("R-CONTROL")
    # ‼ TWO INSTRUMENTS ON THE CONTROL, so the control is a control and not a second guess.
    try:
        from modules.map import get_map_data as _get_map_data

        control_collision = _get_map_data(MapRSE.SKY_PILLAR_ENTRANCE, control_target).collision
    except Exception:  # noqa: BLE001 - a diagnostic must never end the leg
        control_collision = "?"
    console.print(
        f"[cyan]Ch21 leg 3 R-CONTROL: the same planner asked for {control_target} "
        f"{'REFUSED (correct)' if control_refused else '‼ RETURNED A PATH'}; that tile reads "
        f"collision={control_collision} (expected 1). ⛔ If the control does NOT refuse, "
        "R-CONTINUE proves nothing and this run must not be read as a PASS.[/]"
    )
    console.print(
        f"[cyan]Ch21 leg 3 R-CONTINUE: {report['continue_wp']} wp from {rest} to "
        f"{ENTRANCE_CONTINUE}, is_warp={report['continue_is_warp']}, ok={continue_ok} "
        "(measured expectation: 21 wp, is_warp=False).[/]"
    )

    # --- 15. END STATE — leg 3 must NOT advance either var --------------------------------------
    end_state = _var("SOOTOPOLIS_CITY_STATE")
    end_pillar = _var("SKY_PILLAR_STATE")
    if end_state != 3 or end_pillar != 0:
        raise BotModeError(
            f"Ch21 leg 3: end state is SOOTOPOLIS_CITY_STATE={end_state!r}, "
            f"SKY_PILLAR_STATE={end_pillar!r}; both must be unchanged (3 and 0). State 4 is written "
            "by the Wallace DOOR scene — if it moved, this leg crossed into leg 4."
        )
    report["state"] = end_state
    report["pillar_state"] = end_pillar
    context.message = f"Story: Ch21 — leg 3 done: at the Sky Pillar door ({_where()})."
    return report
