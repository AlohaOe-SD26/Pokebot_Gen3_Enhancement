"""TEST SIDE (the chapter-5 search fix, 2026-11-13): the REAL-MEMORY fixture of `test_goals.py` StandingThingsTests (E)
and EntryLeadTests (K1).

    py -3.12 ai_player/gates/make_ch5loop_fixture.py WORLD_LAST.jsonl

WORLD_LAST is the last line of the T capture's world.jsonl (`e0diag/runs/s3t_Tcap/world_last.jsonl`, 2026-11-13: the
merged tree c25d2c40 replayed from E0 T's L4 start, seed 6483, capped at frame 1036000, inside E0 T's ROUTE 104 <-> PETALBURG
WOODS loop; its moves equal E0 T's for all 17094 moves). The fixture keeps, of it, the four maps the loop and its way out
lie on: ROUTE 104 (0:19), PETALBURG WOODS (24:11), RUSTBORO CITY (0:3) and ROUTE 116 (0:31), every warp and connection
record (links to maps not kept are skipped by the searches that read them: a map with no memory is no part), and the
counters. Writes `fixtures/ch5loop_tcap.world.jsonl` and a `.build.json` beside it with the source's sha256.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "fixtures" / "ch5loop_tcap.world.jsonl"
KEEP = {"0:19": "ROUTE104", "24:11": "PETALBURG_WOODS", "0:3": "RUSTBORO_CITY", "0:31": "ROUTE116"}


def build(source: Path) -> dict:
    last = None
    with open(source, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    if last is None:
        raise SystemExit(f"{source} holds no snapshot")
    data = json.loads(last)
    for key, const in KEEP.items():
        if (data["maps"].get(key) or {}).get("const") != const:
            raise SystemExit(f"map {key} of the snapshot is not {const}")
    return {"maps": {key: data["maps"][key] for key in KEEP}, "warps": data["warps"], "connections": data["connections"],
            "tiles_learned": data.get("tiles_learned"), "news": data.get("news")}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    source = Path(argv[0])
    fixture = build(source)
    OUT.write_text(json.dumps(fixture, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    side = {"world": str(OUT.relative_to(HERE.parents[1])).replace("\\", "/"),
            "from": "the last line of the T capture's world.jsonl (s53 lab e0diag/runs/s3t_Tcap/world_last.jsonl: c25d2c40 "
                    "replayed from E0 T's L4 start, seed 6483, Trainer, capped at f1036000 inside the loop)",
            "from_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "kept": {"maps": KEEP, "warps": "all", "connections": "all"},
            "why": "the chapter-5 search fix: E (the woods' trees remembered off screen) and K1 (the entry-map lead toward "
                   "RUSTURF_TUNNEL) on the AI's real memory of the loop"}
    OUT.with_suffix("").with_suffix(".build.json").write_text(json.dumps(side, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes) from {source} (sha256 {side['from_sha256'][:16]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
