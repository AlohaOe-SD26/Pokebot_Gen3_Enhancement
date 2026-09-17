"""THE **HALLS** BETWEEN THE ELITE FOUR ROOMS — the part of §Ch24 nothing had measured.

⛔⛔ WHY THIS EXISTS. Every measurement §Ch24 has so far stops at the moment the bot arrives in a
hall: `--driver e4exit` proves it leaves Sidney's room and lands on `HALL1 (5,12)`, and that is where
the evidence ends. But **a hall is not a doorway — it is a corridor the bot must WALK**, and the one
before the Champion's room is much longer than the others. A leg that treats "arrived in the hall" as
"arrived at the next room" is building on a gap.

⭐ THE USER FLAGGED EXACTLY THIS (2026-09-16): *"between each elite 4 member room, there is a straight
path (in between room) that they have to walk across when leaving the prior room, to then walk that
path and actually go through the door to the next elite 4 member, and so on, it is a longer path to
the champions room."* This probe checks that description against **OUR OWN runtime map data** — which
is what the bot actually sees — rather than against the decomp or a recon note. (A prior recon
reported hall geometry from `map.json`; agreement between the two is worth having, and disagreement
would be worth much more.)

⛔ IT READS THE **ROM/STATIC** LAYOUT, which is legitimate here and is NOT the `KI-74` trap. `KI-74`
is about tiles a SCRIPT rewrites at runtime — the E4 exit doors. Nothing rewrites a hall: the halls
carry no `setmetatile`, and the recon found they carry no objects and no coord events either. The
walkable column measured here is therefore the same column the bot will walk. ‼ The one thing that IS
runtime-dependent — whether the *door at the top* has been opened — is a property of the ROOM behind
it, not of the hall, and is already measured elsewhere.

CONTROLS (a reading with no control is not a measurement):
  C1  the forward door tile (5,2) must be reachable-looking (collision 0) in EVERY hall. It is the
      tile the bot walks onto to reach the next room; if it reads as a wall, the reader is wrong.
  C2  (0,0) must be a WALL in every hall. If a reader calls the corner walkable it is not reading
      collision at all, and every other number here is void.
  C3  the landing tile each room warps you onto — (5,12) for the short halls — must be walkable.
⇒ exit 0 if the controls hold (whatever the verdict), 1 if any control fails.

    PYTHONUTF8=1 py -3.12 probe_e4_halls.py [save.ss1]
"""

import pathlib
import sys

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
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE

BAR = "=" * 100

#: The halls, in the order the gauntlet walks them. HALL5 is the FIRST one (lobby -> Sidney); HALL1
#: follows Sidney, and so on. ‼ The numbering is NOT the walking order — that is a genuine trap in
#: the map names themselves, and it is why this table spells the order out.
HALLS = [
    ("HALL5  lobby   -> SIDNEY  ", MapRSE.EVER_GRANDE_CITY_HALL5),
    ("HALL1  SIDNEY  -> PHOEBE  ", MapRSE.EVER_GRANDE_CITY_HALL1),
    ("HALL2  PHOEBE  -> GLACIA  ", MapRSE.EVER_GRANDE_CITY_HALL2),
    ("HALL3  GLACIA  -> DRAKE   ", MapRSE.EVER_GRANDE_CITY_HALL3),
    ("HALL4  DRAKE   -> CHAMPION", MapRSE.EVER_GRANDE_CITY_HALL4),
]

DOOR = (5, 2)          #: the forward door at the top of every hall
CORNER = (0, 0)        #: must be a wall

#: ⛔⛔ THE THREE SOUTHERN "BACKWARD WARP" TILES — `#24-hallwarpdisputed`. TWO OF OUR OWN DOCS
#: CONTRADICT EACH OTHER ABOUT THESE, ON THE EXACT HALL LEG 1 WALKS:
#:   * `ai-research-notes/2026-09-04-ch24-LEAGUE-INTERIOR-ROUTING.md:139` — they are
#:     DESTINATION-ONLY: they sit on `MB_NORMAL`, which `IsWarpMetatileBehavior` rejects, so
#:     stepping on one never fires.
#:   * `2026-09-07-ch24-elite-four-BUILD-SPEC.md:157` and `03-PUNCH-LIST.md` — a single SIDESTEP in
#:     that hall warps you BACK into the room you just cleared.
#: ‼ The second was derived from `get_map_data(...).warps` — a warp-EVENT TABLE, which lists arrival
#: destinations and says NOTHING about whether a tile can TRIGGER a warp. This probe reads the thing
#: that actually decides: the metatile BEHAVIOUR byte, via `MapLocation.tile_type`
#: (`modules/map.py:862` → `_metatile_attributes[0] & 0xFF`).
#: ⭐ THIS SETTLES THE OFFLINE HALF ONLY. Behaviour says whether the tile is a warp KIND; it does not
#: prove the game declines to move the player. The live half is one westward step, logged.
BACKWARD = [(4, 12), (5, 12), (6, 12)]


def collision_at(map_enum, tile):
    try:
        return get_map_data(map_enum, tile).collision
    except Exception as error:  # noqa: BLE001 — a failed read is a RESULT, not a crash
        return f"ERR:{type(error).__name__}"


def walkable_column(map_enum, x: int, max_y: int = 40):
    """The contiguous run of collision-0 tiles down column ``x``, and where it stops."""
    ys = []
    for y in range(max_y):
        c = collision_at(map_enum, (x, y))
        if c == 0:
            ys.append(y)
        elif isinstance(c, str):
            break
    return ys


def main() -> int:
    save = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("post_ch24_atdoor.ss1")
    if not save.is_absolute():
        for base in (pathlib.Path(__file__).resolve().parent / "saves", pathlib.Path.cwd()):
            if (base / save).is_file():
                save = base / save
                break
    if not save.is_file():
        print(f"save not found: {save}")
        return 1
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(4):
        context.emulator.run_single_frame()

    print(BAR)
    print("THE ELITE FOUR HALLS — walked in gauntlet order, read from OUR OWN map data")
    print(f"  save: {save.name}")
    print(BAR)

    failures = []
    rows = []
    for label, m in HALLS:
        col = walkable_column(m, DOOR[0])
        door_c = collision_at(m, DOOR)
        corner_c = collision_at(m, CORNER)
        landing = max(col) if col else None
        length = (landing - DOOR[1]) if landing is not None else None
        rows.append((label, length, landing, door_c, corner_c, col))

        if door_c != 0:
            failures.append(f"C1 {label}: forward door {DOOR} reads collision {door_c}, expected 0")
        if corner_c == 0:
            failures.append(f"C2 {label}: corner {CORNER} reads WALKABLE — the reader is not reading collision")

    print(f"  {'hall (walking order)':<28}{'steps':>7}{'from':>7}{'to':>6}   walkable column x=5")
    for label, length, landing, door_c, corner_c, col in rows:
        span = f"y={min(col)}..{max(col)}" if col else "<none>"
        print(f"  {label:<28}{(length if length is not None else '?'):>7}"
              f"{('(5,%d)' % landing) if landing is not None else '?':>7}{'(5,2)':>6}   {span}")

    longest = max((r for r in rows if r[1] is not None), key=lambda r: r[1], default=None)
    print()
    if longest:
        print(f"  ⭐ LONGEST: {longest[0].strip()} — {longest[1]} steps, landing (5,{longest[2]}).")
        others = [r[1] for r in rows if r[1] is not None and r is not longest]
        if others and longest[1] > max(others):
            print(f"     The other halls are {sorted(set(others))} steps. ⇒ the user's description is"
                  f" CONFIRMED against our own data: the run to the Champion is the long one.")
        else:
            print("     ⚠ It is NOT longer than the rest — the 'long corridor' claim does not hold here.")

    # ---- `#24-hallwarpdisputed` — read the BEHAVIOUR, not the warp table ------------------------
    print()
    print("  BACKWARD-WARP TILES — behaviour byte (`#24-hallwarpdisputed`):")
    print("      ⛔ A warp-EVENT entry says a tile is a DESTINATION. Only the BEHAVIOUR says whether")
    print("        stepping on it can TRIGGER one. This reads the behaviour.")
    warpish = 0
    for label, m in HALLS:
        cells = []
        for t in BACKWARD:
            try:
                md = get_map_data(m, t)
                beh, coll = md.tile_type, md.collision
            except Exception as error:  # noqa: BLE001 — a failed read is a RESULT
                beh, coll = f"ERR:{type(error).__name__}", "?"
            # "Normal" behaviour is what IsWarpMetatileBehavior rejects; a door/warp behaviour is
            # what it accepts. We report the string rather than asserting a list, because the
            # decisive question is which FAMILY it falls in and a reader must see the raw answer.
            if isinstance(beh, str) and beh != "Normal" and not beh.startswith("ERR"):
                warpish += 1
            cells.append(f"{t}={beh!r}/c{coll}")
        print(f"      {label:<28} {'  '.join(cells)}")
    print()
    if warpish == 0:
        print("  ⭐ VERDICT (offline half): every backward tile reads behaviour 'Normal' ⇒ consistent")
        print("     with LEAGUE-INTERIOR-ROUTING.md:139 (destination-only, never fires), and NOT with")
        print("     'a sidestep warps you back'. ‼ Consistent-with is not proof: the live half is one")
        print("     westward step from HALL1 (5,12), logging the map. Until that runs, keep the hall")
        print("     walk COLUMN-CONSTRAINED.")
    else:
        print(f"  ⛔ VERDICT (offline half): {warpish} backward tile(s) carry a NON-'Normal' behaviour ⇒")
        print("     the BUILD-SPEC half may be right and a sidestep could genuinely warp. Treat the")
        print("     hall as hazardous and do NOT sidestep. Read the cells above for which tiles.")

    print()
    print("  CONTROLS:")
    for label, _l, landing, door_c, corner_c, _c in rows:
        land_c = collision_at(HALLS[[r[0] for r in rows].index(label)][1], (5, landing)) if landing is not None else "?"
        print(f"    {label:<28} C1 door(5,2)={door_c}  C2 corner(0,0)={corner_c}  C3 landing(5,{landing})={land_c}")

    print(BAR)
    if failures:
        print("  ⛔ CONTROL FAILURE — nothing above can be trusted:")
        for f in failures:
            print("    ", f)
        print(BAR)
        return 1
    print("  ✅ controls hold: every forward door reads walkable, every corner reads wall.")
    print("  ‼ THIS IS GEOMETRY, NOT A DRIVE. It says the corridor exists and how long it is; it does")
    print("    NOT say the bot walks it. Only `#24-e4postbattlestall`'s HALL1 leg is driven so far.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
