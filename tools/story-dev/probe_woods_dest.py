r"""GATE (ROM) — the Chapter-12 Petalburg Woods leg aims at a tile it can REACH (`#26-destreachability`, 2026-09-26).

WHY: `travel_lavaridge_to_petalburg` aimed at PETALBURG_WOODS (26, 5) — a solid tree. MEASURED in the live batch: 67 of 67
legs derailed there (recovering only through a re-run from inside the Woods). The fix aims at (14, 6), the first tile
inside the north door, and the leg's own south-east exit block does the rest.

  D1  the default path in `travel_lavaridge_to_petalburg` aims at (14, 6); (26, 5) appears only under the arm
      `POKEBOT_WOODS_FAULT_OLDTILE`, which is registered in 29.
  D2  THE GEOMETRY (the bot's own planner on the ROM's map data, from the pinned `norman_done.ss1`): (14, 6) is walkable,
      `calculate_path` reaches it from the north landing (14, 5), and reaches the south-east exit (36, 38) from it.
  D3  CONTROL — the old target must be unreachable here (else this gate could not have caught the bug): `calculate_path`
      from (14, 5) to (26, 5) FAILS.
FAULT ARM (built in): the default reverted to (26, 5) FAILS D1.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_woods_dest.py
"""
import ast
import io
import pathlib
import sys
import tokenize

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

EGSRC = REPO / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
REGISTRY = REPO / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _strip(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def d1(src: str, sink=None):
    fn = next((n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)
               and n.name == "travel_lavaridge_to_petalburg"), None)
    body = _strip(ast.get_source_segment(src, fn) or "") if fn else ""
    arm = "POKEBOT_WOODS_FAULT_OLDTILE"
    check('_woods_tile = (26, 5) if os.environ.get("POKEBOT_WOODS_FAULT_OLDTILE") == "1" else (14, 6)' in body
          and "_navigate_riding_out(MapRSE.PETALBURG_WOODS, _woods_tile, tries=8)" in body
          and "_navigate_riding_out(MapRSE.PETALBURG_WOODS, (26, 5)" not in body,
          "D1 the default aims at (14, 6); (26, 5) only under the arm", sink)
    check(f"`{arm}`" in REGISTRY.read_text(encoding="utf-8"), f"D1 {arm} is registered in 29", sink)


def main() -> int:
    print("=" * 92)
    print("GATE (ROM) — the Petalburg Woods leg aims at a reachable tile (#26-destreachability)")
    print("=" * 92)
    src = EGSRC.read_text(encoding="utf-8")
    d1(src)

    from modules.context import context
    from modules.game import set_rom
    from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists
    from modules.roms import list_available_roms

    profile_name = "woodsgate"
    if not profile_directory_exists(profile_name):
        create_profile(profile_name, list_available_roms()[0])
    profile = load_profile_by_name(profile_name)
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)
    from modules.libmgba import LibmgbaEmulator

    context.emulator = LibmgbaEmulator(profile, lambda: None)
    context.emulation_speed = 0
    context.audio = False
    context.video = False
    context.emulator.load_save_state((REPO / "tools" / "story-dev" / "saves" / "norman_done.ss1").read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    from modules.map import get_map_data
    from modules.map_data import MapRSE
    from modules.map_path import PathFindingError, calculate_path

    woods = MapRSE.PETALBURG_WOODS

    def path_ok(a, b) -> bool:
        try:
            calculate_path(get_map_data(woods, a), (woods, b))
            return True
        except PathFindingError:
            return False

    check(get_map_data(woods, (14, 6)).collision == 0, "D2 (14, 6) is walkable (collision 0)")
    check(path_ok((14, 5), (14, 6)), "D2 the planner reaches (14, 6) from the north landing (14, 5)")
    check(path_ok((14, 6), (36, 38)), "D2 … and the south-east exit (36, 38) from (14, 6)")
    check(not path_ok((14, 5), (26, 5)), "D3 CONTROL: (26, 5) — the old target — is unreachable from (14, 5)")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    d1(src.replace('else (14, 6)', 'else (26, 5)', 1), sink)
    check(bool(sink), f"FAULT the default reverted to (26, 5) FAILS D1 ({len(sink)})")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
