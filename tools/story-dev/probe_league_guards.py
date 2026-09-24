# -*- coding: utf-8 -*-
"""§Ch24 M2 — WHAT STANDS BETWEEN THE BOT AND THE LOBBY DOOR? OBSERVE-ONLY.

⛔⛔ THE GAP THIS CLOSES. M1 measured the lobby's north door: `(9,1)`/`(10,1)` are
`Non-Animated Door`, collision 0, and `(8,1)`/`(11,1)` are collision 1 — so the door is exactly two
tiles wide and the only approach tiles are `(9,2)`/`(10,2)`, which read collision 0 / `Normal`.
**That is a statement about TERRAIN, and terrain is not the whole story.** A recon pass reports that
`EverGrandeCity_PokemonLeague_1F`'s `OnTransition` calls `GuardsBlockDoor` while
`FLAG_ENTERED_ELITE_FOUR` is unset, parking two guard objects **onto `(9,2)`/`(10,2)`**.
⇒ ‼ **OBJECT OCCUPANCY IS NOT COLLISION.** M1's probe could not see this by construction, and said so.

⭐⭐ AND THE REASON IT MATTERS IS A SILENT HANG, NOT A REFUSAL.
`calculate_path` plans over **terrain**. It does not know an NPC is standing there. So if the guards
occupy the approach, the planner will happily return a route **through** them, the navigator will walk
into an object that never yields, and the run stalls with no error — the `KI-48` shape this tree has
already paid for. ⇒ a path returned here is **NOT** proof the bot can walk it, and this probe prints
that warning beside the number rather than leaving a reader to infer it.

────────────────────────────────────────────────────────────────────────────────────────────────────
⛔ THE CAMERA-RANGE TRAP, HANDLED EXPLICITLY
────────────────────────────────────────────────────────────────────────────────────────────────────
`get_map_objects()` is a **camera-range window**, not a map census (`.claude/skills/story-drive`).
The fixture stands at `(3,4)` and the guards would be at `(9,2)`/`(10,2)` — several tiles away.
⇒ **AN EMPTY LIST IS NOT EVIDENCE OF ABSENCE.** This probe therefore reports:
  * every object it CAN see, with coordinates, so presence is positive evidence; and
  * an explicit UNKNOWN verdict if the window does not appear to cover the door area at all,
    rather than reporting "no guards" and letting that read as "the way is clear".
The honest negative here is *"not visible from where we stand"*, and the probe says exactly that.

⛔ OBSERVE-ONLY: presses nothing, steps nowhere, cannot commit a run, cannot poison
`current_state.ss1` with an in-gauntlet position.
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
# ⛔ UNTHROTTLED (`probe_gate_unthrottled.py`).
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.map import get_map_data, get_map_objects
from modules.map_data import MapRSE
from modules.map_path import calculate_path
from modules.memory import get_event_flag
from modules.player import get_player_avatar

SAVES = REPO / "tools" / "story-dev" / "saves"
FIXTURE = "post_league_lobby.ss1"
BAR = "=" * 104

DOOR = [(9, 1), (10, 1)]
APPROACH = [(9, 2), (10, 2)]
#: Where `map.json` places the guards when they are NOT blocking (per the recon claim).
PARKED = [(8, 2), (11, 2)]
#: Flag 263 in `modules/data/event_flags/emerald.txt`.
FLAG = "ENTERED_ELITE_FOUR"


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
    except Exception:  # noqa: BLE001 — an unknown map id is a result; stop honestly.
        print(f"  ABORT — unknown map id {here}")
        return 1

    print(BAR)
    print("  §Ch24 M2 — WHAT STANDS BETWEEN THE BOT AND THE LOBBY DOOR?  ⛔ OBSERVE-ONLY.")
    print(f"  fixture: {FIXTURE}   standing: {map_enum.name} {tile}")
    print(BAR)

    # ---- THE FLAG ------------------------------------------------------------------------------
    try:
        flag = get_event_flag(FLAG)
        print(f"\n  FLAG {FLAG} = {flag}"
              f"   ({'guards should be PARKED aside' if flag else 'guards should be BLOCKING the door'})")
    except Exception as error:  # noqa: BLE001 — an unreadable flag is a RESULT worth printing; the
        # object census below is independent of it and must still run.
        flag = None
        print(f"\n  ⛔ FLAG {FLAG} could not be read: {type(error).__name__}: {str(error)[:70]}")

    # ---- THE OBJECT CENSUS ---------------------------------------------------------------------
    # ‼ VACUITY-GUARD THE FLAG NAME. `get_event_flag` returns False SILENTLY for a name that is not
    # in the table (`memory.py:336-338`), so a typo — or the `FLAG_` prefix, which NO row in
    # `event_flags/emerald.txt` carries — would print a hardcoded False that looks like a reading.
    from modules.memory import _event_flags
    if FLAG not in _event_flags:
        print(f"  ⛔ ABORT (instrument): {FLAG!r} is NOT in the event-flag table "
              f"({len(_event_flags)} entries). `get_event_flag` would return False SILENTLY.")
        return 1

    try:
        objects = list(get_map_objects())
    except Exception as error:  # noqa: BLE001 — same reasoning.
        print(f"  ⛔ get_map_objects() failed: {type(error).__name__}: {str(error)[:70]}")
        objects = []

    print(f"\n  OBJECTS VISIBLE FROM {tile} — ‼ this is a CAMERA-RANGE WINDOW, not a census:")
    seen = {}
    for ob in objects:
        try:
            # ‼ `current_coords`, NOT `local_coordinates`. `map.py` carries TWO classes with
            # overlapping names: the LIVE `ObjectEvent` (`:1107`, what `get_map_objects()` returns,
            # read out of `gObjectEvents`) and the STATIC `ObjectEventTemplate` (`:1588`, map data).
            # The template has `local_coordinates`/`kind`; the live one has `current_coords` and
            # neither of those. A first version of this probe read the TEMPLATE's API off the LIVE
            # object and every row came back `<unreadable object: AttributeError>` — which the
            # camera-range guard then correctly reported as UNKNOWN rather than "the way is clear".
            c = tuple(ob.current_coords)
            seen[c] = ob
            print(f"    local_id={ob.local_id:<3} gfx={ob.graphics_id:<4} "
                  f"move={str(ob.movement_type)[:18]:<18} at {c}")
        except Exception as error:  # noqa: BLE001 — one unreadable object must not hide the others.
            print(f"    <unreadable object: {type(error).__name__}: {str(error)[:50]}>")
    if not objects:
        print("    (none visible)")

    # ---- THE QUESTION --------------------------------------------------------------------------
    print("\n  IS THE APPROACH OCCUPIED?")
    occupied = [t for t in APPROACH if t in seen]
    parked = [t for t in PARKED if t in seen]
    for t in APPROACH:
        print(f"    approach {t}: {'OCCUPIED by local_id ' + str(seen[t].local_id) if t in seen else 'nothing visible'}")
    for t in PARKED:
        print(f"    parked   {t}: {'OCCUPIED by local_id ' + str(seen[t].local_id) if t in seen else 'nothing visible'}")

    # Did the camera window even reach the door area? If the nearest visible object is far from the
    # door and nothing at all is near it, we cannot tell absence from out-of-range.
    covered = bool(seen) and any(abs(x - 9) <= 3 and abs(y - 2) <= 3 for (x, y) in seen)

    # ---- THE PLANNER, AND THE WARNING THAT MUST TRAVEL WITH IT ---------------------------------
    print("\n  WHAT DOES THE PLANNER THINK? ‼ `calculate_path` plans over TERRAIN and is blind to NPCs.")
    planned, refused = [], []
    for t in DOOR:
        try:
            n = len(calculate_path((map_enum, tile), (map_enum, t)))
            planned.append((t, n))
            print(f"    path to door {t}: {n} waypoint(s)  NOT proof it is walkable - NPC-blind")
        except Exception as error:  # noqa: BLE001 - a refusal is the reading we came for.
            refused.append(t)
            print(f"    path to door {t}: REFUSED - {type(error).__name__}")

    # ---- VERDICT -------------------------------------------------------------------------------
    print()
    if occupied:
        print(f"  VERDICT: THE APPROACH IS BLOCKED BY OBJECT(S) at {occupied}.")
        print("     => A PRODUCTION LEG CANNOT SIMPLY NAVIGATE TO THE DOOR. Its FIRST act must")
        print("     be whatever clears the guards.")
        # REPORT WHICH FAILURE MODE ACTUALLY OCCURRED. They are NOT equivalent, and an earlier
        # version of this probe ASSERTED the dangerous one while its own output showed the safe
        # one - a verdict contradicted by its own log, which this tree has shipped before.
        if refused and not planned:
            print(f"     AND THE FAILURE IS LOUD, NOT SILENT: calculate_path REFUSED {refused}")
            print("     rather than routing through the guards. The KI-48 silent-stall hazard")
            print("     was PREDICTED here and DID NOT MATERIALISE on this fixture - a refusal")
            print("     is an exception the leg can catch, strictly better than a silent wait.")
            print("     Do NOT generalise: the planner is still NPC-blind by construction, so")
            print("     this is one fixture's behaviour, not a rule.")
        elif planned:
            print(f"     AND THE FAILURE WOULD BE SILENT: the planner RETURNED a route {planned}")
            print("     over tiles an NPC occupies - the KI-48 shape, with no error to catch.")
    elif not covered:
        print("  ⚠ VERDICT: UNKNOWN — NOT 'THE WAY IS CLEAR'.")
        print("     No object was visible near the door, but `get_map_objects()` is a camera-range")
        print("     window and nothing visible sits within 3 tiles of it. ⇒ this run cannot")
        print("     distinguish 'no guards' from 'guards out of range'. Re-read from a tile ADJACENT")
        print("     to the door before concluding anything.")
    else:
        print("  ✅ VERDICT: the camera window covers the door area and the approach tiles")
        print(f"     {APPROACH} are EMPTY of objects.")
        if flag:
            print(f"     Consistent with {FLAG}=True (guards parked aside).")
        else:
            print(f"     ‼ BUT {FLAG} is False, which the recon says should mean BLOCKING. Either the")
            print("     recon is wrong, or this fixture's guards are elsewhere. Do not build on this")
            print("     until the discrepancy is explained.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
