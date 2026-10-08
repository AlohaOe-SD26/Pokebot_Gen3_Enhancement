"""TEST SIDE: does the AI read the ROM's WARP TABLE, by ANY route? (AI-player build step 3.1; the step-3.1 verifier's second
round, its first weak proof: "FINDING 5's guard only checks syntax".)

    py -3.12 ai_player/gates/warp_reads.py               prints one line: WARPREADS {json}  (the real package and 3 plants)
    py -3.12 ai_player/gates/warp_reads.py --scan        prints one line: SCAN {json}       (THIS package only)

WHY: since step 3.1 a tile is an exit by how it LOOKS (`eyes/view.py` EXIT_BEHAVIORS) and the eyes no longer read a map's
warp events (`host/eyes.py`). The guard against that read coming back was SYNTAX: `test_world.py` looked for an attribute
spelled `.warps`. The verifier planted `getattr(location, 'warps')` in `host/eyes.py` `_map_facts` and it passed; a RAW read
of the warp array, followed from `gMapHeader`'s events pointer, would pass any syntax check. So the guard is now two:

  1. STATIC (`warp_table_reads`, run by `test_world.py` on every host file): an attribute OR a string constant naming the
     warp table (`warps`, `warp_events`, `warp_count`, `warpCount`), or the framework's `MapWarp` class. A string constant
     catches `getattr(x, 'warps')`, `hasattr`, a dict key; a docstring or a comment that MENTIONS `location.warps` does
     not fire (it is a longer string, or no node at all). It cannot see a raw read: that is what 2 is for.
  2. BEHAVIOURAL (`scan`, this file): the REAL eyes (`host/eyes.py` FrameworkEyes) look at the game, in a throwaway
     emulator, on every start the live arms use, and EVERY `context.emulator.read_bytes(address, length)` call is
     recorded. That one function is the funnel of every read the eyes can make: their own `_rom_bytes`/`_ewram_bytes`, the
     framework's `read_symbol` (`modules/memory.py`) and `MapLocation` (`modules/map.py`), all end in it
     (`modules/libmgba.py` LibmgbaEmulator.read_bytes), and the purity gate gives `host/eyes.py` no other read door.
     Then, test side, the ROM address range of EVERY map's warp-event array (`gMapGroups` -> the map's header ->
     `MapEvents` @+4 -> `warps` @+8, `warpCount` @+1, 8 bytes each: `include/global.fieldmap.h`). A recorded read that
     overlaps any of them read the warp table, whatever the code that asked for it looked like.

NON-VACUITY: the starts' own maps have warps (their arrays are not empty); the recorder SEES the eyes read the ROM right
next to them (the current map's `MapEvents` struct, which the framework's `bg_events` reads for the signs: the same
region, one pointer away); and the FAULT-TESTS: three plants in COPIES of the package, each in `host/eyes.py` `_map_facts`,
each of which the scan must catch:
  * `attribute`: `location.warps` (the read step 3.1 removed; the static check also catches it);
  * `getattr`: `getattr(location, 'warps')` (the verifier's plant; the static check now catches it too);
  * `raw`: the warp array read with the eyes' own `_rom_bytes`, its address followed from `gMapHeader`'s events pointer
    (NO name of the table anywhere: the static check cannot see it, and says so; the scan must).
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROFILE = "ai-step0-fixture"
#: The names of the ROM's warp table: the framework's `MapLocation.warps`, the decomp's `warpCount`, and the names a
#: reader would give them (`include/global.fieldmap.h` struct MapEvents: warpCount, warps).
WARP_NAMES = frozenset({"warps", "warp_events", "warp_count", "warpCount"})
#: The framework's class of one warp event (`modules/map.py` MapWarp).
WARP_CLASSES = frozenset({"MapWarp"})
#: The starts the scan looks from (every fixture the live arms use that stands on a map; the trainer battle has no view).
STARTS = ("house_2f_clockset.ss1", "clock_room.ss1", "pokedex_done.ss1", "littleroot_twin.ss1", "route101_south.ss1",
          "route101_xp.ss1", "mart_rustboro.ss1")
#: Looks per start, one frame apart.
LOOKS = 20
#: `include/global.fieldmap.h` struct MapHeader: events @4; struct MapEvents: warpCount @1, warps @8; struct WarpEvent: 8.
HEADER_EVENTS, EVENTS_WARP_COUNT, EVENTS_WARPS, WARP_EVENT_SIZE, MAP_EVENTS_SIZE = 4, 1, 8, 8, 20
#: The anchor every plant is put before (`host/eyes.py` `_map_facts`, right after the framework's `location` is made).
PLANT_ANCHOR = "            signs = tuple(\n"
PLANTS: dict[str, str] = {
    "attribute": "            _planted = frozenset(w.local_coordinates for w in location.warps)  # PLANT attribute\n",
    "getattr": "            _planted = frozenset(w.local_coordinates for w in getattr(location, 'warps'))  # PLANT getattr\n",
    "raw": ("            _events = _rom_bytes(_u32(live, 4), 20)  # PLANT raw: the warp array from gMapHeader's events pointer\n"
            "            _planted = _rom_bytes(_u32(_events, 8), 8 * _events[1]) if _events[1] else b''  # PLANT raw\n"),
}


def warp_table_reads(source: str) -> list[str]:
    """STATIC: every place a source NAMES the warp table: an attribute `.warps` (etc.), a string constant that is exactly
    such a name (`getattr(location, 'warps')`, `hasattr`, a dict key), or the framework's `MapWarp` class. A docstring or
    a comment that mentions `location.warps` is not a hit (a longer string; a comment is no node). A RAW read of the
    warp array names nothing: `scan` is the guard for that."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and (node.attr in WARP_NAMES or node.attr in WARP_CLASSES):
            found.append(f"line {node.lineno}: .{node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in WARP_NAMES:
            found.append(f"line {node.lineno}: the string {node.value!r}")
        elif isinstance(node, ast.Name) and node.id in WARP_CLASSES:
            found.append(f"line {node.lineno}: {node.id}")
        elif isinstance(node, ast.alias) and node.name.split(".")[-1] in WARP_CLASSES:
            found.append(f"an import of {node.name}")
    return found


def overlapping(reads: list[tuple[int, int]], ranges: dict[str, tuple[int, int]]) -> list[dict]:
    """The recorded reads (address, length) that touch any warp array (name -> (start, end exclusive))."""
    out = []
    for address, length in reads:
        for name, (start, end) in ranges.items():
            if address < end and start < address + max(length, 1):
                out.append({"read": [hex(address), length], "warp_array_of": name, "array": [hex(start), end - start]})
    return out


def warp_arrays(emulator) -> tuple[dict[str, tuple[int, int]], dict[tuple[int, int], tuple[int, int]]]:
    """Test side, from the ROM: every map's warp array (name -> (start, end)) and MapEvents struct ((group, number) ->
    (start, end)), walked from `gMapGroups` by THIS file (no framework reader of warps)."""
    from modules.game import get_symbol
    from modules.map_data import MapRSE

    groups = get_symbol("gMapGroups")[0]
    u32 = lambda data, at: int.from_bytes(bytes(data[at:at + 4]), "little")  # noqa: E731
    arrays, events = {}, {}
    for member in MapRSE:
        group, number = member.value
        try:
            table = u32(emulator.read_bytes(groups + 4 * group, 4), 0)
            header = emulator.read_bytes(u32(emulator.read_bytes(table + 4 * number, 4), 0), 0x1C)
            pointer = u32(header, HEADER_EVENTS)
            if not 0x08000000 <= pointer < 0x09000000:
                continue
            raw = emulator.read_bytes(pointer, MAP_EVENTS_SIZE)
        except Exception:  # noqa: BLE001 - a map the table does not hold
            continue
        events[(group, number)] = (pointer, pointer + MAP_EVENTS_SIZE)
        count, warps = raw[EVENTS_WARP_COUNT], u32(raw, EVENTS_WARPS)
        if count and 0x08000000 <= warps < 0x09000000:
            arrays[member.name] = (warps, warps + WARP_EVENT_SIZE * count)
    return arrays, events


def scan(starts: list[Path], looks: int = LOOKS) -> dict:
    """THIS package's eyes on every start, every read recorded (module docstring, 2)."""
    from ai_player.gates.probe_eyes import boot

    context = boot(PROFILE)
    emulator = context.emulator
    arrays, events = warp_arrays(emulator)
    from ai_player.host.eyes import FrameworkEyes

    original = emulator.read_bytes
    recorded: list[tuple[int, int]] = []

    def recording(address: int, length: int = 1):
        recorded.append((int(address), int(length)))
        return original(address, length)

    out = {"package": str(Path(sys.modules[FrameworkEyes.__module__].__file__).resolve()), "starts": [], "warp_arrays": len(arrays)}
    for start in starts:
        emulator.load_save_state(start.read_bytes())
        emulator.run_single_frame()
        eyes = FrameworkEyes(crop=True)
        recorded.clear()
        emulator.read_bytes = recording  # an INSTANCE attribute: every caller of `context.emulator.read_bytes` meets it
        maps, problems = set(), []
        try:
            for _ in range(looks):
                look = eyes.look()
                if look.player is not None:
                    maps.add((look.player.map_group, look.player.map_number))
                problems += [p for p in look.problems if "warp" in p.lower() or "Error" in p]
                emulator.read_bytes = original
                emulator.run_single_frame()
                emulator.read_bytes = recording
        finally:
            emulator.read_bytes = original
        reads = list(recorded)
        hits = overlapping(reads, arrays)
        own = {f"{g}:{n}": arrays_of(arrays, (g, n)) for g, n in sorted(maps)}
        near = [list(map(hex, events[key])) for key in sorted(maps) if key in events
                and any(a < events[key][1] and events[key][0] < a + max(n, 1) for a, n in reads)]
        out["starts"].append({"start": start.name, "maps": sorted(f"{g}:{n}" for g, n in maps), "reads": len(reads),
                              "rom_reads": sum(1 for a, _ in reads if a >= 0x08000000),
                              "own_warp_arrays": own, "map_events_read": near, "warp_table_reads": hits[:6],
                              "warp_table_read_count": len(hits), "problems": problems[:4]})
    return out


def arrays_of(arrays: dict[str, tuple[int, int]], key: tuple[int, int]) -> list:
    from modules.map_data import MapRSE

    try:
        name = MapRSE(key).name
    except ValueError:
        return []
    span = arrays.get(name)
    return [] if span is None else [name, hex(span[0]), (span[1] - span[0]) // WARP_EVENT_SIZE]


def fixtures() -> list[Path]:
    gates = Path(__file__).resolve().parent
    found = []
    for name in STARTS:
        for folder in (gates / "fixtures", REPO / "tools" / "story-dev" / "saves",
                       Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO) / "ai_player" / "gates" / "fixtures",
                       Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO) / "tools" / "story-dev" / "saves"):
            if (folder / name).is_file():
                found.append(folder / name)
                break
    return found


def run_scan(root: Path | None, starts: list[Path], timeout: float = 900) -> tuple[dict | None, str]:
    """`--scan` in its own process, from this package (root None) or a COPY at `root`."""
    script = Path(__file__).resolve() if root is None else root / "ai_player" / "gates" / Path(__file__).name
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": str(REPO), "AI_PLAYER_BUILD_ROOT": str(REPO / "sandbox-pokebot")})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        done = subprocess.run([sys.executable, str(script), "--scan", *map(str, starts)], cwd=str(REPO), env=env,
                              capture_output=True, timeout=timeout, creationflags=flags)
    except subprocess.TimeoutExpired as error:
        return None, f"TIMEOUT: {error}"
    raw = done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("SCAN "):
            return json.loads(line[len("SCAN "):]), raw
    return None, raw


def planted_copy(plant: str) -> Path:
    root = Path(tempfile.mkdtemp(prefix=f"ai_player_warp_plant_{plant}_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    path = root / "ai_player" / "host" / "eyes.py"
    text = path.read_text(encoding="utf-8")
    if text.count(PLANT_ANCHOR) != 1:
        raise SystemExit(f"plant anchor not unique in host/eyes.py ({text.count(PLANT_ANCHOR)} hits)")
    path.write_text(text.replace(PLANT_ANCHOR, PLANTS[plant] + PLANT_ANCHOR), encoding="utf-8")
    return root


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scan", nargs="*", help="internal: scan THIS package's eyes on these starts")
    args = parser.parse_args()
    if args.scan is not None:
        print("SCAN " + json.dumps(scan([Path(p) for p in args.scan] or fixtures()), ensure_ascii=False), flush=True)
        return 0
    starts = fixtures()
    out: dict = {"starts": [p.name for p in starts]}
    real, raw = run_scan(None, starts)
    out["real"] = real if real is not None else {"error": raw[-2000:]}
    out["static_real"] = {p.name: warp_table_reads(p.read_text(encoding="utf-8")) for p in sorted((REPO / "ai_player" / "host").glob("*.py"))}
    out["plants"] = {}
    for plant in PLANTS:
        root = planted_copy(plant)
        try:
            data, raw = run_scan(root, starts)
            static = warp_table_reads((root / "ai_player" / "host" / "eyes.py").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(root, ignore_errors=True)
        out["plants"][plant] = {"scan": data if data is not None else {"error": raw[-2000:]}, "static": static,
                                "code": PLANTS[plant].strip()}
    print("WARPREADS " + json.dumps(out, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
