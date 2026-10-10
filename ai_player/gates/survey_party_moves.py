"""TEST SIDE: a SURVEY of every save and fixture's party moves (step 4.1 round 3), by the framework's decoder
(`hands_harness.py truth`, one throwaway emulator per state, read only).

    py -3.12 ai_player/gates/survey_party_moves.py [--workers 4] [--evidence PATH]

WHY (the step-4.1 verifier's second round: "Paralysis to help a catch is unit-tested only"; "no Disabled, Taunted or
Tormented move is played"): before a limit is written down as "no fixture has it", the saves are READ for it. For every
state in `tools/story-dev/saves/` and `ai_player/gates/fixtures/`, each party Pokemon's moves; then which hold a move whose
effect is SLEEP or PARALYZE (`knowledge/moves.json`: a catch's status move, `brain/battle.py` CATCH_STATUS_EFFECTS), and
which hold DISABLE, TAUNT, TORMENT or IMPRISON (the causes of a refused move other than PP). A foe's moves are not in a
save; this surveys the player's side only."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.provenance import keep_earlier, provenance  # noqa: E402
from ai_player.knowledge.facts import move_fact  # noqa: E402

HARNESS = Path(__file__).resolve().parent / "hands_harness.py"
STATUS_EFFECTS = {"SLEEP", "PARALYZE"}
REFUSAL_EFFECTS = {"DISABLE", "TAUNT", "TORMENT", "IMPRISON"}


def states() -> list[Path]:
    return (sorted((REPO / "tools" / "story-dev" / "saves").glob("*.ss1"))
            + sorted((REPO / "ai_player" / "gates" / "fixtures").glob("*.ss1")))


def party_of(path: Path) -> tuple[str, dict | None]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env["PYTHONUTF8"] = "1"
    try:
        done = subprocess.run([sys.executable, str(HARNESS), "truth", str(path)], cwd=str(REPO), env=env,
                              capture_output=True, timeout=240)
    except subprocess.TimeoutExpired:
        return path.name, None
    line = next((l for l in done.stdout.decode("utf-8", "replace").splitlines() if l.startswith("TRUTH ")), None)
    if line is None:
        return path.name, None
    truth = json.loads(line[len("TRUTH "):])
    return path.name, {"party": truth.get("party"), "moves": truth.get("party_moves")}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    paths = states()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(party_of, paths))
    unread = [name for name, data in results if not data or not isinstance(data.get("moves"), list)]
    status, refusal = [], []
    for name, data in results:
        if name in unread:
            continue
        for _pid, species, moves in data["moves"]:
            effects = {m: (move_fact(m).effect if move_fact(m) else None) for m in moves}
            hits = [m for m, e in effects.items() if e in STATUS_EFFECTS]
            if hits:
                status.append((name, species, hits))
            blocks = [m for m, e in effects.items() if e in REFUSAL_EFFECTS]
            if blocks:
                refusal.append((name, species, blocks))
    out = ["AI PLAYER BUILD STEP 4.1 ROUND 3 - A SURVEY OF THE PARTIES' MOVES (gates/survey_party_moves.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {provenance(REPO)}",
           f"{len(paths)} states (tools/story-dev/saves/*.ss1 and ai_player/gates/fixtures/*.ss1), {len(paths) - len(unread)} "
           f"read by the framework's decoder (hands_harness.py truth); unread: {unread or 'none'}",
           f"a SLEEP or PARALYSIS move (a catch's status move) in a party: {len(status)} Pokemon; the moves "
           f"{sorted({m for _, _, hits in status for m in hits})}; the species {sorted({s for _, s, _ in status})}",
           *[f"    {name}: {species} {hits}" for name, species, hits in status],
           f"a DISABLE, TAUNT, TORMENT or IMPRISON move in a party: {len(refusal)} Pokemon",
           *[f"    {name}: {species} {hits}" for name, species, hits in refusal]]
    print("\n".join(out))
    if args.evidence is not None:
        keep_earlier(args.evidence)
        args.evidence.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0 if not unread else 1


if __name__ == "__main__":
    sys.exit(main())
