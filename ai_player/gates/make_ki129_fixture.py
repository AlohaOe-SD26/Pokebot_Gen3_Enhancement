"""TEST SIDE (KI-129 Part A, 2026-10-31): the REAL-MEMORY fixture of `test_goals.py` KI129PartATests (P-F1).

    py -3.12 ai_player/gates/make_ki129_fixture.py SNAPSHOT.json

SNAPSHOT is the LAST line of the A0-1 run's world.jsonl (the AI's world memory at the end of that run, ledger #68), saved
as a one-line file (the full world.jsonl is about 2 GB: never read it whole). The fixture keeps, of it, ROUTE 104's map
memory (key 0:19) and ONLY the links the map's `promise` reads: its three warp records (the doors it used: (10, 38) and
(11, 38) into the woods, (17, 50) into MR. BRINEY's house) and ONE connection record across its right edge to PETALBURG
(so the right side's roads are a known way, not "left to see"). Without those, the used doors and all 34 road tiles count
as promise (the critic's F8, reproduced). Writes `fixtures/route104_a01.world.jsonl` and a `.build.json` beside it with the
source's sha256.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "fixtures" / "route104_a01.world.jsonl"
ROUTE104 = "0:19"
WARPS = ("0:19|10,38", "0:19|11,38", "0:19|17,50")


def build(snapshot: Path) -> dict:
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    memory = data["maps"][ROUTE104]
    if memory.get("const") != "ROUTE104":
        raise SystemExit(f"map {ROUTE104} of the snapshot is {memory.get('const')}, not ROUTE104")
    warps = {name: data["warps"][name] for name in WARPS}
    across = [c for c in data["connections"] if c.get("source") == ROUTE104 and c.get("direction") == "right"]
    if not across:
        raise SystemExit("no connection across ROUTE104's right edge in the snapshot")
    return {"maps": {ROUTE104: memory}, "warps": warps, "connections": [across[0]],
            "tiles_learned": data.get("tiles_learned"), "news": data.get("news")}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    snapshot = Path(argv[0])
    fixture = build(snapshot)
    OUT.write_text(json.dumps(fixture, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    side = {"world": str(OUT.relative_to(HERE.parents[1])).replace("\\", "/"),
            "from": "the last line of the A0-1 run's world.jsonl (ledger #68, seed 5901; sandbox-pokebot/profiles/"
                    "ai-ch3-probe-1/ai_player_runs/20261030-172705-A0-1/world.jsonl)",
            "from_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            "kept": {"maps": [ROUTE104], "warps": list(WARPS), "connections": "the first record across ROUTE104's right "
                                                                              "edge (to PETALBURG_CITY, 0:0)"},
            "why": "KI-129 Part A, P-F1: Navigator.cut_off on the AI's real ROUTE 104 memory, from (39, 63)"}
    OUT.with_suffix("").with_suffix(".build.json").write_text(json.dumps(side, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes) from {snapshot} (sha256 {side['from_sha256'][:16]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
