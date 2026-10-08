"""THE SEED SWEEP of AI-player build step 3: how OFTEN each walk does what it should, over seeds (a FREQUENCY measurement,
CLAUDE.md rule 9), in-process (`gates/hands_harness.py`, each run in its own process and throwaway emulator), each run
graded by its SECOND-PATH truth (save block 1, read after the run, never the AI's eyes).

    py -3.12 ai_player/gates/rate_step3.py [--plans HOUSE,TOWN,...] [--seeds 10] [--workers 4]

THE PLANS: HOUSE, TOWN (Story), ROUTE, ROAM, STUCK, TOWN-Catcher, TOWN-Trainer as `live_step3.py`'s arms (the same
fixtures, goals and budgets), and CROP (TOWN with the crop FAULT on: `--no-crop`). Besides "as intended", each run
reports what the step-3 verifier asked about:
  * CHOICES (its weak proof 2: "seeds 3 and 7 chose the SAME seven targets"): every run's sequence of targets (the
    action log's `decide` records) and its first target's HEADING; per plan, how many different sequences 10 seeds
    chose, and whether seeds 3 and 7 chose the same.
  * CROP-SEP (its weak proof 1: "step count alone does not separate cropped from uncropped"): for every TOWN (Story)
    and CROP run, the two discriminators of `live_step3.py`'s CROP arm: how many known tiles lie OUTSIDE the window
    they were first seen from (the memory, `world.jsonl`), and whether the first target on LITTLEROOT_TOWN was in the
    window; and, for contrast, the walking steps on the town (the measure that does NOT separate them).
  * ROAM (its weak proof 5): training steps, presses, the presses a battle interrupted, spins, the ratio over steps.
Evidence: `ai_player/evidence/<date>-step3-RATE.txt`, with the code line of the tree (`provenance.py`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.provenance import provenance  # noqa: E402
from ai_player.world.memory import WorldMemory, in_window  # noqa: E402

GATES = Path(__file__).resolve().parent
FIXTURES = GATES / "fixtures"
HARNESS = GATES / "hands_harness.py"
DONE = REPO / "tools" / "story-dev" / "saves" / "pokedex_done.ss1"
EVIDENCE = REPO / "ai_player" / "evidence"
WALL = 1500  # seconds a single run may take (killed past it)


def _explore(state: Path, goal: str, frames: int, personality: str, *extra: str) -> list[str]:
    return ["explore", "--state", str(state), "--goal-map", goal, "--frames", str(frames), "--personality", personality, *extra]


#: name -> (harness arguments, intended(truth, reason)).
PLANS = {
    "HOUSE": (_explore(FIXTURES / "house_2f_clockset.ss1", "LITTLEROOT_TOWN", 12000, "Story"),
              lambda t, r: r.startswith("explore: done") and t["map"] == [0, 9]),
    "TOWN": (_explore(DONE, "ROUTE101", 20000, "Story"), lambda t, r: r.startswith("explore: done") and t["map"] == [0, 16]),
    "ROUTE": (_explore(FIXTURES / "route101_south.ss1", "OLDALE_TOWN", 24000, "Story", "--world-in",
                       str(FIXTURES / "route101_south.world.jsonl")),
              lambda t, r: r.startswith("explore: done") and t["map"] == [0, 10]),
    "ROAM": (["roam", "--state", str(FIXTURES / "route101_south.ss1"), "--roam-steps", "150", "--frames", "40000",
              "--personality", "Catcher"], lambda t, r: r.startswith("roam: roamed")),
    "STUCK": (_explore(FIXTURES / "clock_room.ss1", "LITTLEROOT_TOWN", 12000, "Story"),
              lambda t, r: r.startswith("explore: stuck: ping-pong")),
    "TOWN-Catcher": (_explore(DONE, "ROUTE101", 20000, "Catcher"),
                     lambda t, r: r.startswith("explore: done") and t["map"] == [0, 16]),
    "TOWN-Trainer": (_explore(DONE, "ROUTE101", 20000, "Trainer"),
                     lambda t, r: r.startswith("explore: done") and t["map"] == [0, 16]),
    "CROP": (_explore(DONE, "ROUTE101", 20000, "Story", "--no-crop"),
             lambda t, r: r.startswith("explore: done") and t["map"] == [0, 16]),
}


def run_one(name: str, seed: int) -> dict:
    args, intended = PLANS[name]
    run_dir = Path(tempfile.mkdtemp(prefix=f"ai_rate3_{name}_{seed}_"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env["PYTHONUTF8"] = "1"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    proc = subprocess.Popen([sys.executable, str(HARNESS), *args, "--seed", str(seed), "--run-dir", str(run_dir)], cwd=str(REPO),
                            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags)
    try:
        out, _ = proc.communicate(timeout=WALL)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        return {"name": name, "seed": seed, "ok": False, "line": f"seed {seed}: TIMEOUT after {WALL}s"}
    text = out.decode("utf-8", "replace")
    line = next((l for l in text.splitlines() if l.startswith("HANDS ")), None)
    if line is None:
        return {"name": name, "seed": seed, "ok": False, "line": f"seed {seed}: no HANDS line: {text[-400:]}"}
    data = json.loads(line[len("HANDS "):])
    truth = data["truth"]
    ok = bool(intended(truth, data["reason"]))
    records = [json.loads(l) for l in (run_dir / "actions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()] \
        if (run_dir / "actions.jsonl").is_file() else []
    decides = [r.get("extra") or {} for r in records if r.get("decision") == "decide" and (r.get("extra") or {}).get("target")]
    sequence = [(d.get("map"), d.get("kind"), tuple(d.get("target"))) for d in decides]
    result = {"name": name, "seed": seed, "ok": ok, "reason": data["reason"], "frames": data["frames"], "map": truth["map"],
              "sequence": sequence}
    exploring = [d for d in decides if d.get("kind") in ("frontier", "road", "grass", "wander") and d.get("player")]
    if exploring:
        # the HEADING of the first EXPLORING choice on each map (an exit chosen first, the lab's door, says nothing)
        result["headings"] = {}
        for d in exploring:
            if d.get("map") in result["headings"]:
                continue
            dx, dy = d["target"][0] - d["player"][0], d["target"][1] - d["player"][1]
            result["headings"][d.get("map")] = (("left" if dx < 0 else "right") if abs(dx) > abs(dy) else ("up" if dy < 0 else "down"))
        first = exploring[0]
        result["first_exploring"] = f"{first.get('map')} {first.get('kind')} {first.get('target')} from {first.get('player')}"
    town = next((d for d in decides if d.get("map") == "0:9"), None)
    if town is not None:
        # SEEN: a tile the memory knew, inside the window of the tile it was first seen from (the perception rule);
        # `in_window` is only "inside the window of where the player stands NOW" (a tile seen two steps ago is not)
        seen = bool(town.get("known") and town.get("seen_from") and in_window(tuple(town["seen_from"]), tuple(town["target"])))
        result["first_town_target"] = {"kind": town.get("kind"), "target": town.get("target"), "player": town.get("player"),
                                       "seen_from": town.get("seen_from"), "seen": seen, "in_window_now": town.get("in_window")}
    result["town_steps"] = sum(1 for r in records if str(r.get("reason", "")).startswith("walk ")
                               and re.search(r"\(0,9\) xy=", r.get("digest") or ""))
    world_file = run_dir / "world.jsonl"
    if world_file.is_file():
        lines = [l for l in world_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        world = WorldMemory.from_dict(json.loads(lines[-1])) if lines else None
        if world is not None:
            tiles = [(xy, fact.seen_from) for memory in world.maps.values() for xy, fact in memory.tiles.items()]
            result["known"] = len(tiles)
            result["outside"] = sum(1 for xy, frm in tiles if not in_window(frm, xy))
    if name == "ROAM":
        metrics = next((r.get("extra") or {} for r in records if r.get("decision") == "roam"), {})
        result["roam"] = {k: metrics.get(k) for k in ("steps", "attempts", "interrupted", "not_moved", "spins", "spin_ratio",
                                                      "spin_ratio_of_attempts", "distinct", "most_visited", "encounters", "fled")}
    result["line"] = (f"seed {seed}: {data['reason'][:120]!r} frames {data['frames']} map {truth['map']}"
                      + (f" | first exploring choice {result['first_exploring']}; headings by map {result['headings']}" if exploring else ""))
    return result


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="The step-3 seed sweep.")
    parser.add_argument("--plans", default=",".join(PLANS))
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    wanted = [p.strip() for p in args.plans.split(",") if p.strip()]
    seeds = list(range(1, args.seeds + 1))
    code = provenance(REPO)
    began = time.time()
    jobs = [(name, seed) for name in wanted for seed in seeds]
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(lambda job: run_one(*job), jobs))
    by_plan = {name: [r for r in results if r["name"] == name] for name in wanted}
    out = ["AI PLAYER BUILD STEP 3 - RATE SWEEP (gates/rate_step3.py; in-process gates/hands_harness.py, each run graded by its "
           "second-path truth)", f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}",
           "a FREQUENCY measurement (CLAUDE.md rule 9); the purity of the same code is live_step3.py's launcher arms", ""]
    total_ok = 0
    separated = True
    for name, rows in by_plan.items():
        good = sum(1 for r in rows if r["ok"])
        total_ok += good
        out.append(f"{name}: {good} of {len(rows)} seeds as intended")
        out += [f"    {'OK ' if r['ok'] else 'BAD'} {r['line']}" for r in rows]
    out += ["", "---- CHOICES (the verifier's weak proof 2): the targets each seed chose (map, kind, tile), from its action log ----"]
    for name, rows in by_plan.items():
        if name == "ROAM":
            continue
        sequences = [tuple(r.get("sequence") or ()) for r in rows]
        three = next((r for r in rows if r["seed"] == 3), None)
        seven = next((r for r in rows if r["seed"] == 7), None)
        same_37 = None if three is None or seven is None else three.get("sequence") == seven.get("sequence")
        by_map: dict[str, set] = {}
        for r in rows:
            for key, heading in (r.get("headings") or {}).items():
                by_map.setdefault(key, set()).add(heading)
        headings = {key: sorted(value) for key, value in sorted(by_map.items())}
        out.append(f"{name}: {len(set(sequences))} different target sequences in {len(rows)} seeds; the first exploring "
                   f"choice's headings, by map: {headings}; seeds 3 and 7 chose the same sequence: {same_37}")
        for r in rows:
            seq = "; ".join(f"{m} {k} {list(t)}" for m, k, t in r.get("sequence") or [])
            out.append(f"    seed {r['seed']}: {seq[:600]}")
    if "TOWN" in by_plan or "CROP" in by_plan:
        out += ["", "---- CROP-SEP (the verifier's weak proof 1): what separates a cropped walk (TOWN, Story) from an uncropped "
                    "one (CROP), seed by seed ----",
                "    columns: known tiles OUTSIDE the window they were first seen from / all known; the first target on "
                "LITTLEROOT_TOWN (kind, tile, from; SEEN = known and inside the window of the tile it was first seen from; "
                "in the window NOW, for the record); walking steps on the town (NOT a discriminator)"]
        for name in ("TOWN", "CROP"):
            for r in by_plan.get(name, []):
                first = r.get("first_town_target") or {}
                out.append(f"    {name:<4} seed {r['seed']:>2}: outside {r.get('outside')} / {r.get('known')}; first town target "
                           f"{first.get('kind')} {first.get('target')} from {first.get('player')}, seen from {first.get('seen_from')}: "
                           f"SEEN {first.get('seen')} (in the window now {first.get('in_window_now')}); town steps {r.get('town_steps')}")
        town_rows, crop_rows = by_plan.get("TOWN", []), by_plan.get("CROP", [])
        honest = all(r.get("outside") == 0 and (r.get("first_town_target") or {}).get("seen") is True for r in town_rows)
        faulty = all((r.get("outside") or 0) > 100 and (r.get("first_town_target") or {}).get("seen") is False for r in crop_rows)
        steps_t = sorted(r.get("town_steps") for r in town_rows)
        steps_c = sorted(r.get("town_steps") for r in crop_rows)
        overlap = bool(steps_t and steps_c and min(steps_t) <= max(steps_c))
        separated = honest and faulty
        out.append(f"CROP-SEP: every TOWN seed knows 0 tiles from outside a window and its first town target was SEEN: "
                   f"{honest}; every CROP seed knows > 100 from outside and its first town target was NOT seen: {faulty}; "
                   f"=> the two discriminators separate all {len(town_rows)} + {len(crop_rows)} runs: {honest and faulty}. "
                   f"The town steps (TOWN {steps_t}, CROP {steps_c}) overlap: {overlap} (the step count is not a check: the "
                   f"step-3 sweep before the whim had an honest TOWN seed of 26 steps, CROP's own total)")
    if "ROAM" in by_plan:
        out += ["", "---- ROAM (the verifier's weak proof 5): spins over TRAINING STEPS (the stricter ratio) ----"]
        for r in by_plan["ROAM"]:
            out.append(f"    seed {r['seed']:>2}: {json.dumps(r.get('roam'))}")
    out += ["", f"{total_ok} of {len(results)} runs as intended; {time.time() - began:.0f} s of wall clock with {args.workers} workers"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step3-RATE.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(line for line in out if not line.startswith("    ")))
    print(f"evidence: {path.relative_to(REPO)}")
    return 0 if total_ok == len(results) and separated else 1


if __name__ == "__main__":
    sys.exit(main())
