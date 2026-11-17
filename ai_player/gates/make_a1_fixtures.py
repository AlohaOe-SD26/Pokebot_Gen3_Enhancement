"""TEST SIDE (A1, the frontier probe, spec `2026-11-11-A1-FRONTIER-PROBE-SPEC.md` 4.1 T31 and T35): the two REAL-DATA
fixtures of `test_frontier_probe.py`, cut by this script from the files kept for A1's build.

    py -3.12 -B ai_player/gates/make_a1_fixtures.py KEEP_DIR

KEEP_DIR is the folder the merge's lead kept for A1 (`_ai_lab/keep/2026-11-13-a1-sources`, this PC only, not git; every
source's sha256 is in its README.txt). It reads, never writes there:
  e0-L5/LC-{T-6483,C-6482,S-6481}_L5_{world_last.jsonl,row.json}  E0's three leg-5 legs (ledger #147, commit a90c8e8f):
        T looped PETALBURG_WOODS <-> ROUTE104 59 times each way and ran out of its 600,000 frames, C looped 37 times each
        way and stopped `stuck: no progress`, S reached `ch5_rival_meet` (the CONTROL). Each leg's transitions NEWER than
        its start truth's frame (the leg's own; the older ones are the carried memory), the consts of the maps they name,
        the leg's frames, exit, outcome and the end truth's map and marks are kept: T31's loop signature on the real data.
  c-fix/C_FIX_actions.jsonl  the chapter-5 fix round's C_FIX leg: its two K1 tells (`[AI-GOALS] RUSTURF_TUNNEL is somewhere
        it has not been: first to ROUTE116, a seasoned player's knowledge: ...`, the form `brain/goals.py` writes), kept
        as the action-log records they are: T35's K1 leads on the real data.
Writes `fixtures/a1_e0_loops.json` and `fixtures/a1_k1_tells.jsonl`, each with a `.build.json` beside it naming its
sources' sha256 and its own sha256 (of its bytes with every CRLF read as LF: this PC checks text files out with CRLF
(`core.autocrlf true`), so the working-tree bytes differ from the committed ones; the test hashes the same way).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOOPS = HERE / "fixtures" / "a1_e0_loops.json"
TELLS = HERE / "fixtures" / "a1_k1_tells.jsonl"
#: E0's three leg-5 chains, in the order the fixture keeps them
CHAINS = ("LC-T-6483", "LC-C-6482", "LC-S-6481")
#: the K1 tell's own words (`brain/goals.py` WAY_IN and the tell's form)
K1_WORDS = "a seasoned player's knowledge"
K1_FORM = " is somewhere it has not been: first to "


def lf_sha256(data: bytes) -> str:
    """The sha256 of `data` with every CRLF read as LF (the committed bytes of a text file on any checkout)."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def last_line(path: Path) -> str:
    last = None
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    if last is None:
        raise SystemExit(f"{path} holds no snapshot")
    return last


def loop_leg(keep: Path, chain: str) -> dict:
    row = json.loads((keep / "e0-L5" / f"{chain}_L5_row.json").read_text(encoding="utf-8"))
    world = json.loads(last_line(keep / "e0-L5" / f"{chain}_L5_world_last.jsonl"))
    before, after = row.get("truth_before") or {}, row.get("truth_after") or {}
    start = before.get("frame")
    if not isinstance(start, int):
        raise SystemExit(f"{chain}: its row has no start truth frame")
    transitions = [t for t in world.get("transitions") or [] if isinstance(t, list) and t and isinstance(t[0], int)
                   and t[0] > start]
    named = sorted({t[1] for t in transitions} | {t[2] for t in transitions})
    maps = world.get("maps") or {}
    stop = row.get("harness_stop") or {}
    return {"chain": chain, "leg": row.get("leg"), "target": row.get("target"), "frames": row.get("frames"),
            "exit": row.get("exit"), "outcome": row.get("outcome"), "reached": row.get("reached"),
            "real_frames": stop.get("real_frames"), "start_frame": start, "end_frame": after.get("frame"),
            "end_map": after.get("map"), "marks_after": after.get("marks"),
            "consts": {key: (maps.get(key) or {}).get("const") or key for key in named},
            "transitions": transitions, "transitions_carried": len(world.get("transitions") or []) - len(transitions)}


def k1_tells(path: Path) -> list[str]:
    out = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            reason = str(record.get("reason") or "") if isinstance(record, dict) else ""
            if record.get("decision") == "tell" and K1_WORDS in reason and K1_FORM in reason:
                out.append(line.rstrip("\r\n"))
    return out


def build(keep: Path) -> tuple[dict, list[str]]:
    loops = {"what": "E0's three leg-5 legs (ledger #147): each leg's own transitions (newer than its start truth's "
                     "frame), the consts of the maps they name, its frames, exit, outcome and end truth's map and marks",
             "legs": [loop_leg(keep, chain) for chain in CHAINS]}
    tells = k1_tells(keep / "c-fix" / "C_FIX_actions.jsonl")
    if len(tells) != 2:
        raise SystemExit(f"C_FIX_actions.jsonl holds {len(tells)} K1 tells, not the 2 the spec names (T35)")
    return loops, tells


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    keep = Path(argv[0])
    loops, tells = build(keep)
    LOOPS.write_bytes((json.dumps(loops, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8"))
    TELLS.write_bytes(("\n".join(tells) + "\n").encode("utf-8"))
    sources_loops = {f"e0-L5/{chain}_L5_{name}": file_sha256(keep / "e0-L5" / f"{chain}_L5_{name}")
                     for chain in CHAINS for name in ("world_last.jsonl", "row.json")}
    for fixture, sources, why in (
            (LOOPS, sources_loops, "T31: the LOOP key on E0's own leg-5 transitions (T 59 each way, C 37 each way, the "
                                   "same pair; S reached, the CONTROL)"),
            (TELLS, {"c-fix/C_FIX_actions.jsonl": file_sha256(keep / "c-fix" / "C_FIX_actions.jsonl")},
             "T35: the two real K1 tells of the fix round's C_FIX leg (lead ROUTE116)")):
        side = {"fixture": fixture.relative_to(HERE.parents[1]).as_posix(),
                "fixture_sha256_lf": lf_sha256(fixture.read_bytes()),
                "made_by": "ai_player/gates/make_a1_fixtures.py KEEP_DIR (KEEP_DIR = the merge lead's A1 keep folder "
                           "_ai_lab/keep/2026-11-13-a1-sources: this PC only, not git)",
                "sources_sha256": sources, "why": why}
        fixture.with_name(fixture.name.split(".")[0] + ".build.json").write_text(json.dumps(side, indent=1) + "\n",
                                                                                 encoding="utf-8")
        print(f"wrote {fixture.name} ({fixture.stat().st_size} bytes, LF sha256 {side['fixture_sha256_lf']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
