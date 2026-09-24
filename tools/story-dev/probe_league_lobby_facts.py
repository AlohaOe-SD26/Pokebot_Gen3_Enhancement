# -*- coding: utf-8 -*-
"""§Ch24 M1 (part 1) — WHAT IS TRUE IN THE LEAGUE LOBBY, BEFORE ANYTHING IS COMMITTED.

⛔⛔ THE QUESTION THIS EXISTS TO ANSWER, AND WHY IT GATES THE WHOLE GAUNTLET DESIGN.
`pokemon_league.py:5-8` asserts that *"the moment the bot steps on lobby tile (9,1) it is committed
to all five battles or a white-out"*, resting on an **`MB_NORMAL` inference that nobody in this tree
has ever confirmed by reading tile bytes.** The 2026-09-24 build spec repeats it.

⇒ **THAT ONE FACT DECIDES WHERE A READINESS CHECK CAN STILL ACT.** A guard that runs after the
commitment point can only report a problem it can no longer fix — and the lobby is the last place
where a **free nurse** (`victory_road.py:391`, `LEAGUE_NURSE_STAND = (3,4)`) and a **Mart** still
exist. Put the guard one tile too late and its only honest action is to stop the bot.

‼ **WHAT IS ALREADY MEASURED, AND MUST NOT BE RE-MEASURED:** `probe_e4_entry_seal.py`
(`#24-leg2spec` O5) is a LIVE confirmation that the six ENTRY tiles of an Elite Four room are set
impassable behind you and re-applied from `ON_LOAD`. ⇒ the seal *inside a room* is settled. What is
NOT settled is whether the **lobby's north door** is already a point of no return.

────────────────────────────────────────────────────────────────────────────────────────────────────
⛔ OBSERVE-ONLY, AND THAT IS A SAFETY PROPERTY, NOT A STYLE CHOICE
────────────────────────────────────────────────────────────────────────────────────────────────────
This probe **presses no buttons and takes no step.** It loads the fixture, reads memory, and prints.
Stepping through the lobby door is exactly the irreversible act under investigation, so part 1 must
not perform it. A follow-up arm may walk through *on a fixture* and try to walk back — that is the
reading that settles commitment — but it is deliberately a SEPARATE probe, so that this one can
never be the thing that seals a run.

WHAT IT PRINTS, and why each line matters to the design:
  * ROM collision vs **LIVE** collision for the lobby's north door tiles and their neighbours.
    ‼ The LIVE grid is the only oracle that can be trusted here: `KI-74`'s whole lesson is that ROM
    blockdata and the live `gBackupMapLayout` DISAGREE around League doors, in BOTH directions.
  * whether `calculate_path` can still route to the **nurse**, the **Mart** and the **way out** from
    where the bot stands. That is the concrete test of *"is the lobby still a place a guard can act
    from"* — and the answer is what the readiness check's failure branch depends on.
  * the tile the bot is actually standing on, so nothing downstream hardcodes a position.
"""
from __future__ import annotations

import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
# ⛔ UNTHROTTLED, OR THE SUITE PAYS FOR IT AT 1x REAL TIME (`probe_gate_unthrottled.py`).
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.player import get_player_avatar
from modules.map_path import calculate_path
from modules.story.sootopolis import _live_collision_grid

SAVES = REPO / "tools" / "story-dev" / "saves"
FIXTURE = "post_league_lobby.ss1"
BAR = "=" * 100

#: The lobby's north door, per the build spec's decomp read. UNVERIFIED — that is the point.
DOOR_TILES = [(9, 1), (10, 1)]
#: Neighbours, so a wrong door coordinate shows up as "the interesting tile is next door".
NEAR_DOOR = [(8, 1), (11, 1), (9, 2), (10, 2)]
#: Named landmarks the readiness check's failure branch would need.
LANDMARKS = {
    "nurse stand (victory_road.py:391)": (3, 4),
    "mart clerk approach": (16, 3),
    "lobby south exit (toward Ever Grande)": (9, 11),
}


def rom_collision(map_enum, tile):
    try:
        return get_map_data(map_enum, tile).collision
    except Exception as error:  # noqa: BLE001 — a failed read is a RESULT here, not a crash: this
        # probe's whole job is to report what the game says, including "it would not say".
        return f"ERR:{type(error).__name__}"


def tile_type(map_enum, tile):
    try:
        return str(get_map_data(map_enum, tile).tile_type)
    except Exception as error:  # noqa: BLE001 — same reasoning as rom_collision.
        return f"ERR:{type(error).__name__}"


def main() -> int:
    save = SAVES / FIXTURE
    if not save.is_file():
        print(f"  ABORT (instrument, not a result) — no fixture: {FIXTURE}")
        return 1
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    avatar = get_player_avatar()
    here, tile = avatar.map_group_and_number, avatar.local_coordinates
    try:
        map_enum = MapRSE(here)
    except Exception:  # noqa: BLE001 — an unknown map id is a result, and we stop honestly.
        print(f"  ABORT — unknown map id {here}")
        return 1

    print(BAR)
    print("  §Ch24 M1 (part 1) — LEAGUE LOBBY FACTS.  ⛔ OBSERVE-ONLY: no button is pressed,")
    print("  no step is taken. Stepping through the lobby door is the irreversible act under test.")
    print(f"  fixture: {FIXTURE}   standing: {map_enum.name} {tile}")
    print(BAR)

    live = _live_collision_grid(map_enum)

    print("\n  DOOR TILES — ROM vs LIVE. ‼ KI-74: these two DISAGREE around League doors, both ways,")
    print("  so a design that trusts ROM alone is already wrong.")
    print(f"    {'tile':>10}  {'ROM':>6}  {'LIVE':>6}   {'agree':<14} tile_type")
    for t in DOOR_TILES + NEAR_DOOR:
        r, l = rom_collision(map_enum, t), live.get(t)
        mark = "SAME" if r == l else "** DIVERGES **"
        star = "  <- claimed door" if t in DOOR_TILES else ""
        print(f"    {str(t):>10}  {str(r):>6}  {str(l):>6}   {mark:<14} {tile_type(map_enum, t)}{star}")

    print("\n  CAN THE BOT STILL ACT FROM HERE? — a readiness check's failure branch must be able to")
    print("  heal, buy, or leave. If any of these refuse, the guard cannot remedy and must not halt here.")
    for label, dest in LANDMARKS.items():
        try:
            path = calculate_path((map_enum, tile), (map_enum, dest))
            n = len(path)
            verdict = f"{n} waypoint(s)" + ("  (0 = already standing on it)" if n == 0 else "")
        except Exception as error:  # noqa: BLE001 — a refusal is the reading we came for.
            verdict = f"REFUSED — {type(error).__name__}: {str(error)[:60]}"
        print(f"    {label:<42} -> {verdict}")

    print("\n  ⛔ WHAT THIS PROBE DOES **NOT** SETTLE, STATED SO NOTHING OVER-READS IT:")
    print("     whether stepping onto a door tile COMMITS the run. Collision says what can be WALKED")
    print("     ON, never what happens after. The commitment question needs the walk-through arm —")
    print("     step through on a fixture, then try to walk BACK — and that is a separate probe on")
    print("     purpose, so this one can never be the thing that seals a run.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
