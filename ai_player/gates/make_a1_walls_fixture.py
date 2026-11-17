"""TEST SIDE (A1, the frontier probe, spec `2026-11-11-A1-FRONTIER-PROBE-SPEC.md` 4.3 P1, build plan step 5): the REAL-DATA
fixture of `test_frontier_probe.py` T39 (the planted wall WALL-OLDALE, `frontier_probe.MUTANTS["oldale"]`), cut by this script
from the C1 start's own memory kept for A1's build.

    py -3.12 -B ai_player/gates/make_a1_walls_fixture.py KEEP_DIR

KEEP_DIR is the folder the merge's lead kept for A1 (`_ai_lab/keep/2026-11-13-a1-sources`, this PC only, not git; every
source's sha256 is in its README.txt). It reads, never writes there:
  ch5stops/out/probe/probe-C1/world.jsonl   the C1 start's world memory (A1's start C1, `frontier_probe.STARTS`): its LAST
        line, as `world/memory.py` read_world takes it. Kept: OLDALE TOWN and the three maps that border it (`MAPS`), each
        map's record UNCHANGED, every warp FROM one of them, and every connection BETWEEN two of them (both its ends kept,
        so `WorldMemory.from_dict` learns their edges again, as it does for the whole memory). Nothing else (the
        transitions, the news, what was heard are not read by the planner T39 drives).
Writes `fixtures/a1_walls_oldale.world.jsonl` (one line) and its `.build.json` beside it naming the source's sha256 and the
fixture's own (of its bytes with every CRLF read as LF, as `make_a1_fixtures.py`: this PC checks text out with CRLF).
WALL-BRINEY's T40 needs no new fixture: `fixtures/probe7_c1_island.world.jsonl` (a C1 memory, committed) holds ROUTE 104,
the cottage and the warp between them.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "a1_walls_oldale.world.jsonl"
SOURCE = Path("ch5stops") / "out" / "probe" / "probe-C1" / "world.jsonl"
#: OLDALE TOWN and the maps that border it (maps.json: its connections, up ROUTE103, down ROUTE101, left ROUTE102), by the
#: memory's keys ("group:number"); the script checks each key's const in the source
MAPS = {"0:10": "OLDALE_TOWN", "0:16": "ROUTE101", "0:17": "ROUTE102", "0:18": "ROUTE103"}


def lf_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def last_line(path: Path) -> str:
    last = None
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    if last is None:
        raise SystemExit(f"{path} holds no snapshot")
    return last


def build(keep: Path) -> dict:
    world = json.loads(last_line(keep / SOURCE))
    maps = world.get("maps") or {}
    for key, const in MAPS.items():
        if (maps.get(key) or {}).get("const") != const:
            raise SystemExit(f"{SOURCE}: map {key} is {(maps.get(key) or {}).get('const')!r}, not {const}")
    return {"maps": {key: maps[key] for key in MAPS},
            "warps": {name: link for name, link in (world.get("warps") or {}).items() if name.split("|")[0] in MAPS},
            "connections": [c for c in world.get("connections") or []
                            if c.get("source") in MAPS and c.get("target") in MAPS]}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    keep = Path(argv[0])
    cut = build(keep)
    FIXTURE.write_bytes((json.dumps(cut, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8"))
    side = {"fixture": FIXTURE.relative_to(HERE.parents[1]).as_posix(),
            "fixture_sha256_lf": lf_sha256(FIXTURE.read_bytes()),
            "made_by": "ai_player/gates/make_a1_walls_fixture.py KEEP_DIR (KEEP_DIR = the merge lead's A1 keep folder "
                       "_ai_lab/keep/2026-11-13-a1-sources: this PC only, not git)",
            "sources_sha256": {SOURCE.as_posix(): hashlib.sha256((keep / SOURCE).read_bytes()).hexdigest()},
            "kept": {"maps": MAPS, "warps": "every warp from a kept map",
                     "connections": "every connection between two kept maps"},
            "why": "T39: WALL-OLDALE's planner test on the C1 start's own memory of OLDALE TOWN and its three neighbours"}
    FIXTURE.with_name("a1_walls_oldale.build.json").write_text(json.dumps(side, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {FIXTURE.name} ({FIXTURE.stat().st_size} bytes, LF sha256 {side['fixture_sha256_lf']}; "
          f"{len(cut['maps'])} maps, {len(cut['warps'])} warps, {len(cut['connections'])} connections)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
