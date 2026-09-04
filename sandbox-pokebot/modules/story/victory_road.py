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
from modules.pokemon_party import get_party

# ‼ IMPORTED, NOT RE-IMPLEMENTED — this package's transcription rule: the same fact in two files is
# the P5 doc shape in code form, and it drifts.
from modules.story.seafloor_cavern import _at, _on_map, _where
from modules.story.early_game import (
    StoryAbort,
    _check_abort,
    _navigate_riding_out,
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


def _fault(arm: str) -> bool:
    """A fault arm is ON only when its env var is exactly '1'. ⛔ Never truthiness on the string."""
    import os

    return os.environ.get(f"POKEBOT_CH23_FAULT_{arm}") == "1"


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
            reraise_if_aborting(error)
            last_error = f"attempt {attempt}: {type(error).__name__}: {error}"
            report.setdefault("attempt_errors", []).append(last_error)
            context.message = f"Ch23 {last_error}"
            yield from wait_until_truly_controllable()

    report["failure"] = last_error or "exhausted attempts without reaching ROUTE126"
    raise BotModeError(f"Ch23: legs 2-3 failed after {attempts} attempts. Last: {last_error}")
