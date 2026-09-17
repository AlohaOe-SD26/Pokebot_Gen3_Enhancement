# -*- coding: utf-8 -*-
"""`#24-leg2spec` O5 — IS THE ELITE FOUR ROOM SEALED BEHIND YOU, AND IS THE SEAL INVISIBLE TO US?

⛔⛔ THE CLAIM UNDER TEST, AND WHY IT NEEDED A LIVE RUN. A decomp recon found that
`PokemonLeague_EliteFour_EventScript_WalkInCloseDoor` (`data/scripts/elite_four.inc`) sets the SIX
entry tiles — (5,12) (6,12) (7,12) (5,13) (6,13) (7,13) — to `EliteFour_EntryDoor_Closed*` with the
`impassable` argument **TRUE**, the moment you walk into the room, and re-applies it from `ON_LOAD`
so it survives a save/load. Its own report flagged this as the one thing that *"deserves one live
confirmation before leg 2 depends on it"*, because every number in it was decoded from decomp DATA
FILES rather than observed in RAM. This is that confirmation.

⭐⭐ IT MATTERS BECAUSE THE DIVERGENCE RUNS THE **OPPOSITE WAY** TO `KI-74`, AND THAT IS THE WHOLE
POINT. `KI-74` is: the EXIT door reads BLOCKED in ROM and is OPEN live, so the planner refuses a route
that exists. The entry seal is the mirror image: the ENTRY tiles read PASSABLE in ROM and are SEALED
live, so **the planner will confidently plan a retreat that the game refuses** — a jam at a threshold
it believes is open, which is the exact shape that has already cost this project one live incident.

‼‼ SO THE TWO DOORS ARE EACH OTHER'S CONTROL, AND THAT IS WHY THEY ARE MEASURED TOGETHER. One
mechanism (`setmetatile` into `gBackupMapLayout`) must produce a divergence in BOTH directions on the
SAME map at the SAME instant:

    EXIT  (6,1) (6,2)            ROM says BLOCKED (1)   live must say OPEN   (0)   <- KI-74
    ENTRY (5..7,12) (5..7,13)    ROM says OPEN    (0)   live says SEALED    (3)   <- this claim

A probe that showed only one direction could be explained away as "our ROM reader is just wrong about
this map". Two divergences in opposite directions cannot: they prove the ROM reader and the live grid
are describing genuinely different state, and they pin which one the game walks on.

⛔ PLUS TWO ORDINARY CONTROLS that must AGREE in both grids, so "everything diverges" is excluded:
a floor tile the player is standing next to, and a wall. If those disagree too, the comparison is
noise and the probe says so instead of printing a confident table.

FIXTURE: `post_sidney_door_open.ss1` — pinned, and the only state we hold that is INSIDE an Elite
Four room after the victory script has run. ⛔ The live grid is only valid for the map the avatar is
actually standing on (`gBackupMapLayout` describes the loaded map), so this cannot be answered from
anywhere else — unlike the ROM view, which `probe_e4_door_rom_view.py` can take from any save.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_e4_entry_seal.py
Exit 0 if the two ordinary controls agree (whatever the doors say); 1 if they do not, because then
nothing here can be trusted.
"""
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
# ⛔ UNTHROTTLED, OR THE SUITE PAYS FOR IT AT 1x REAL TIME — enforced by
# `probe_gate_unthrottled.py`, which caught this file missing the line.
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.player import get_player_avatar
from modules.story.sootopolis import _live_collision_grid

SAVES = REPO / "tools" / "story-dev" / "saves"
FIXTURE = "post_sidney_door_open.ss1"
BAR = "=" * 100

ENTRY_TILES = [(5, 12), (6, 12), (7, 12), (5, 13), (6, 13), (7, 13)]
EXIT_TILES = [(6, 1), (6, 2)]


def rom_collision(map_enum, tile):
    try:
        return get_map_data(map_enum, tile).collision
    except Exception as error:  # noqa: BLE001 — a failed read is a RESULT, not a crash
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
    except Exception:  # noqa: BLE001
        print(f"  ABORT — unknown map id {here}")
        return 1

    print(BAR)
    print("  #24-leg2spec O5 — does the Elite Four room SEAL behind you, invisibly to our planner?")
    print(f"  fixture: {FIXTURE}   standing: {map_enum.name} {tile}")
    print(BAR)

    live = _live_collision_grid(map_enum)

    def row(label, t, expect_rom, expect_live):
        r, l = rom_collision(map_enum, t), live.get(t)
        agree = "SAME" if r == l else "** DIVERGES **"
        if expect_rom is None:
            ok = r == l
        elif expect_live is None:
            # "any BLOCKED value" — see the note at the ENTRY caller.
            ok = r == expect_rom and isinstance(l, int) and l != 0
        else:
            ok = r == expect_rom and l == expect_live
        print(f"    {label:<22} {str(t):<9} ROM={r}  LIVE={l}   {agree:<16} "
              f"{'as predicted' if ok else 'NOT as predicted'}")
        return r, l, ok

    # ‼‼ "SEALED" IS `collision != 0`, **NOT** `collision == 1`, AND THE FIRST VERSION OF
    # THIS PROBE ASSERTED 1 AND PRINTED "THE DECOMP CLAIM IS NOT CONFIRMED" OVER A
    # CONFIRMATION. Gen-3 collision is a 2-bit field and these tiles come back as **3**;
    # our planner blocks on `tile.collision != 0` (`map_path.py:137`) and the live-grid
    # consumer uses the same test (`sootopolis.py:997`, `grid.get(tile, 1) != 0`). ⇒ 3 is
    # SEALED. Asserting the exact value tested a detail the codebase does not care about,
    # and scored a TRUE claim as refuted. *Read the failing line before touching the
    # thing under test.*
    print()
    print('  ' + 'ENTRY tiles — the claimed RUNTIME SEAL (ROM open, live SEALED = collision != 0):')
    entry = [row("entry", t, 0, None) for t in ENTRY_TILES]
    print("\n  EXIT tiles — KI-74, the SAME mechanism running the OTHER way (ROM blocked, live open):")
    exit_ = [row("exit", t, 1, 0) for t in EXIT_TILES]

    # ---- the two ordinary controls ---------------------------------------------------------------
    print("\n  CONTROLS — tiles with no script on them; these MUST agree in both grids:")
    floor = (tile[0], tile[1])            # the tile the avatar is standing on: walkable by definition
    wall = (0, 0)                         # a corner; solid in this room's layout
    c1_r, c1_l, _ = row("control FLOOR", floor, None, None)
    c2_r, c2_l, _ = row("control WALL", wall, None, None)
    controls_ok = (c1_r == c1_l) and (c2_r == c2_l)

    print(f"\n{BAR}")
    if not controls_ok:
        print("  ⛔⛔ THE CONTROLS DIVERGE TOO — the two grids disagree about ordinary tiles, so a")
        print("     divergence at a door proves nothing. Nothing above can be trusted.")
        print(BAR)
        return 1
    print("  ✅ controls agree in both grids ⇒ a divergence at a door is about the DOOR.")

    sealed = [t for (r, l, ok), t in zip(entry, ENTRY_TILES)
              if r == 0 and isinstance(l, int) and l != 0]
    opened = [t for (r, l, ok), t in zip(exit_, EXIT_TILES) if l == 0 and r == 1]
    print(f"\n  ENTRY tiles ROM-open but LIVE-SEALED : {sealed}")
    print(f"  EXIT  tiles ROM-blocked but LIVE-OPEN : {opened}")
    # ⛔⛔ THIS IS A GATE NOW, NOT A ONE-SHOT MEASUREMENT (#62, 2026-09-17). The result above is
    # pinned, so a run that no longer reproduces BOTH divergences is not "an interesting reading" —
    # it means `_live_collision_grid` has stopped seeing runtime `setmetatile` writes, which is the
    # single reader standing between us and `KI-74` in both of its directions. That regression would
    # otherwise surface as a jammed bot in the Elite Four, hours into a run.
    # ‼ The CONTROLS still gate separately and FIRST: if they diverge, the comparison is noise and
    # the failure is the instrument, not the subject — two different verdicts that must not be
    # collapsed into one red line.
    if not (sealed and opened):
        print("\n  ⛔⛔ A DIVERGENCE THAT WAS MEASURED ON 2026-09-17 HAS VANISHED.")
        print(f"     entry sealed: {len(sealed)}/6 expected 6   exit opened: {len(opened)}/2 expected 2")
        print("     ⇒ suspect `_live_collision_grid` / `gBackupMapLayout` reading, NOT the map.")
        print(BAR)
        return 1
    if sealed and opened:
        print("\n  ⭐⭐ BOTH DIVERGENCES CONFIRMED LIVE, IN OPPOSITE DIRECTIONS, ON ONE MAP AT ONE")
        print("     INSTANT. ⇒ the ROM layout and the grid the game walks on are genuinely different")
        print("     state, and `KI-74` is only HALF the hazard: the planner will also plan a RETREAT")
        print("     through the entry door that the game refuses.")
        print("  ⇒ LEG 2 MUST READ `_live_collision_grid` FOR ANY LEAGUE-INTERIOR REACHABILITY CHECK,")
        print("     and must never offer a 'walk back to the nurse' fallback.")
    elif sealed:
        print("\n  ⚠ The entry seal is confirmed; the exit divergence did not reproduce here.")
    elif opened:
        print("\n  ⛔ THE ENTRY SEAL DID NOT REPRODUCE — the decomp claim is NOT confirmed live.")
        print("     Do not build leg 2's retreat logic on it; re-measure before relying on either.")
    else:
        print("\n  ⛔ NEITHER divergence reproduced — re-check the fixture and the live-grid reader.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
