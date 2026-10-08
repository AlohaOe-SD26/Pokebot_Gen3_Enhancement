"""THE SEED SWEEP of AI-player build step 3: how OFTEN each walk does what it should, over seeds (a FREQUENCY measurement,
CLAUDE.md rule 9), in-process (`gates/hands_harness.py`, each run in its own process and throwaway emulator), each run
graded by its SECOND-PATH truth (save block 1, read after the run, never the AI's eyes).

    py -3.12 ai_player/gates/rate_step3.py [--plans HOUSE,TOWN,...] [--seeds 10] [--workers 4]

THE PLANS: HOUSE, TOWN (Story), ROUTE, ROAM, STUCK, TOWN-Catcher, TOWN-Trainer, SCENE as `live_step3.py`'s arms (the same
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
BUILD STEP 3.1 (the step-3 adversarial review) adds: the plan SCENE (errands past Littleroot's twin: given up after the
second scene, `live_step3.py` arm SCENE); REVERSALS per run on the AI's own steps (`live_step3.reversals`, finding 2),
bounded by `REVERSALS_PER_RUN` on the exploring plans; ROAM's BOTH ratios (finding 9: back-and-forth spins over training
steps, the criterion < 2%, and the strict non-moving-press ratio, reported); every window check on the gate's own
literal window (`gates/window.py`, finding 6). The CROP plan's first town target need no longer be a road (finding 1).
THE STEP-3.1 VERIFIER'S ROUND adds:
  * REVERSALS: the per-run bound is now `REVERSALS_PER_RUN` = 1 (the step-3.1 tree's own maximum) and each exploring plan
    is also bounded by `REVERSALS_PER_100` = 1 per 100 steps over its seeds (the verifier: with a bound of 2 a run, ROUTE
    with finding 2 reverted, 12 reversals in 451 steps, passed).
  * REVERT, the sweep's own FAULT ARM and the A/B the README quotes (the verifier: "the baseline ... is a scratch
    measurement ... it cannot be reproduced from the tree"): the same plans and seeds from a COPY of the package with a
    rule reverted (`live_step3.py` STALE_MUTATIONS: finding 2's two rules; SCENEX_MUTATION: the count per tile a scene
    began on), measured by the same metric; each revert must break the bound the real code meets (`REVERT_PREDICTIONS`).
  * SCENE-EXPLORE: the EXPLORER (its own targets, not an errand) from the twin's fixture toward Route 101: the twin stops
    it at most twice on each tile, a tile given up is never stepped on again (the verifier: "SCENE ... tests the scene
    rule on a scripted goto target ... 1 different target sequences in 10 seeds"). SCENE, the errand, is labelled as what
    it is: one scripted scenario whose seeds vary only the path noise and the pacing.
  * ROUTE's FLEE, seed by seed (the verifier: "ROUTE seed 3 no longer meets a wild battle"): the battles each seed met ==
    fled == the game's own wild-battle count, and how many seeds met one.
  * REPLAY, NOT REPLICATION (CLAUDE.md rule 8): every plan's seed 3 is `live_step3.py`'s arm of that name replayed (the
    harness and the launcher play one seed identically); the line says so, and compares the frames with the live
    evidence of the same tree when there is one. The other nine seeds are the frequency sample.
THE STEP-3.1 VERIFIER'S SECOND ROUND:
  * SCENE-EXPLORE runs to the explorer's OWN end (20,000 frames, as the live SCENEX, whose trajectory its seed 3 replays),
    so what happens after the twin is measured: per seed, her push-backs before any news and between news (`twin_ok`:
    at most `TWIN_SCENES_IN_ALL` before any news, every tile she began on then given up, at most once more after each
    news), and each seed's END (map, VAR_LITTLEROOT_TOWN_STATE, outcome; how many reach ROUTE101).
  * REVERTS: SCENE-WORDS (a scene not known by its words: replaces SCENE-TILE, whose count per tile no longer changes what
    the twin does to the explorer) and SCENE-NEWS (new words not progress: the explorer never tries the twin again).
  * THE GAME'S CLOCK IS PINNED for every run (`live_step3.GAME_CLOCK`, `hands_harness.py --game-clock`): the game reads its
    real-time clock at every map load (berry growth draws random numbers), so an unpinned sweep was a different sweep at
    another hour (measured: live_step3 arm CLOCKS). The REPLAY section says which live arms read a clock that can differ.
Evidence: `ai_player/evidence/<date>-step3-RATE.txt`, with the code line of the tree (`provenance.py`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.live_step2 import make_copy  # noqa: E402
from ai_player.gates.live_step3 import (  # noqa: E402
    ARMS, CLOCK_SENSITIVE, GAME_CLOCK, NEWS_MUTATION, REVERSALS_PER_RUN, SCENEWORDS_MUTATION, STALE_MUTATIONS,
    TWIN_SCENES_IN_ALL, TWIN_SCENES_PER_TILE, Run, map_name_of, path_reversals, stale_arrivals, twin_scenes,
)
from ai_player.gates.provenance import provenance  # noqa: E402
from ai_player.world.memory import WorldMemory  # noqa: E402
#: (build step 3.1, finding 6) the screen's window as the gate writes it (literals), never the eyes' VIEW_*
from ai_player.gates.window import on_screen_from as in_window  # noqa: E402

GATES = Path(__file__).resolve().parent
FIXTURES = GATES / "fixtures"
HARNESS = GATES / "hands_harness.py"
DONE = REPO / "tools" / "story-dev" / "saves" / "pokedex_done.ss1"
EVIDENCE = REPO / "ai_player" / "evidence"
WALL = 1500  # seconds a single run may take (killed past it)
#: (build step 3.1, finding 2) reversals an EXPLORING run may show: `live_step3.REVERSALS_PER_RUN` (1 since the step-3.1
#: verifier's round, was 2), and (that round) per plan at most this many per 100 steps over its seeds
REVERSALS_PER_100 = 1.0
EXPLORING = ("HOUSE", "TOWN", "ROUTE", "TOWN-Catcher", "TOWN-Trainer")
#: A plan whose live arm has another name (the REPLAY section). (The step-3.1 verifier's second round) SCENE-EXPLORE and
#: the live SCENEX now both run 20,000 frames, to the explorer's OWN end: seed 3 here is SCENEX replayed.
LIVE_ARM: dict[str, str] = {"SCENE-EXPLORE": "SCENEX"}
REPLAY_NOTES: dict[str, str] = {}
#: (the step-3.1 verifier's round) the REVERTS: name -> (the mutations of a COPY, the plans run from it, the PREDICTION,
#: pre-registered in `live_step3.py`'s docstring: what the revert must break). (Its second round) SCENE-WORDS replaces
#: SCENE-TILE: with the twin known by her words, the count per tile alone no longer changes what she does to the explorer
#: (the words close both tiles first), so the rule to revert is the words rule (`revert_step3.py` W44 keeps the per-tile
#: rule's own proof, on a scene with no words).
REVERT_PREDICTIONS = {
    "FINDING-2": (STALE_MUTATIONS, EXPLORING,
                  "every exploring plan breaks its reversal bound (a run over REVERSALS_PER_RUN, or the plan over "
                  "REVERSALS_PER_100), and frontier targets are walked onto with everything beside them seen"),
    "SCENE-WORDS": ((SCENEWORDS_MUTATION,), ("SCENE-EXPLORE",),
                    "at least 8 of the 10 seeds are sent back by the twin more than TWIN_SCENES_IN_ALL times before any news "
                    "(twice on each of her tiles), while the real code is at most that often on every seed"),
    "SCENE-NEWS": ((NEWS_MUTATION,), ("SCENE-EXPLORE",),
                   "the real code reaches ROUTE101 on at least 5 of the 10 seeds (development sweep: 6, seeds 2, 3, 4, 7, 9, "
                   "10: May's words are news, the twin is tried again and lets the player pass; the other four end by the "
                   "ping-pong rule at Brendan's house before meeting May), and on every one of those seeds the revert (new "
                   "words not progress) never tries her again and stays off Route 101"),
}
#: (the step-3.1 verifier's second round) the SCENE-NEWS prediction's floor: seeds of the 10 the real code takes to Route 101
SCENE_NEWS_REACHED = 5


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
    # build step 3.1 (the step-3 review's finding 3): errands past Littleroot's twin, given up after the second scene
    "SCENE": (["goto", "--state", str(FIXTURES / "littleroot_twin.ss1"), "--goto", "10,4;10,0", "--frames", "6000",
               "--personality", "Story"],
              lambda t, r: r.startswith("goto: stuck: the goto at (10, 0) cannot be reached (a scene stopped the way there 2 times")
              and t["map"] == [0, 9]),
    # the step-3.1 verifier's round: the EXPLORER's own targets behind the twin (graded with the twin's scenes: `twin_ok`);
    # (its second round) to the explorer's OWN end, as the live SCENEX (20,000 frames): what it does after the twin is
    # graded too, by its outcome and save block 1 (reported per seed; `twin_ok` is the rule's grade)
    "SCENE-EXPLORE": (_explore(FIXTURES / "littleroot_twin.ss1", "ROUTE101", 20000, "Story"),
                      lambda t, r: r.startswith("explore: ") and not r.startswith("explore: budget")),
}


def twin_report(records: list[dict]) -> dict:
    """(the step-3.1 verifier's round) The twin's scenes in one run, by the tile each began on (`live_step3.twin_scenes`),
    in all, the targets they stopped, the tiles given up, and any step onto a tile after it was given up."""
    t = twin_scenes(records)
    walls = t["walls"]
    later = [r["frame"] for frame, tile, key in walls for r in records
             if str(r.get("reason", "")).startswith("walk ") and str(r.get("action", "")).startswith("hold ")
             and (r.get("frame") or 0) > frame and f"-> ({tile[0]}, {tile[1]})" in str(r.get("reason")) and map_name_of(r) == key]
    counts = {f"{tile[0]},{tile[1]}": len(hits) for tile, hits in sorted(t["by_tile"].items())}
    lifts = t["lifts"]
    # a step onto a tile given up, BEFORE news made it worth a try again
    later = [f for f in later if not any(w < l <= f for w, _, _ in walls for l in lifts)]
    first_walls = sorted({f"{x},{y}" for frame, (x, y), _ in walls if frame < (lifts[0] if lifts else 10**12)})
    return {"per_tile": counts, "total": t["total"], "worst": t["worst"], "walls": [list(tile) for _, tile, _ in walls],
            "first_walls": first_walls, "targets": [list(x) for x in t["targets"]], "stepped_after": later, "words": t["words"],
            "segments": t["segments"], "lifts": lifts, "news": [w for _, w in t["news"]], "passed_her": len(t["passed_her"])}


def twin_ok(report: dict) -> bool:
    """The rule's grade on one run (the step-3.1 verifier's second round): before any news, the twin sends the player back
    at most `TWIN_SCENES_IN_ALL` times and every tile she began on is then given up; after each news at most once more; a
    tile given up is never stepped on until news lifts it."""
    segments = report.get("segments") or [0]
    walled = report["first_walls"] == sorted(report["per_tile"]) if segments[0] >= 2 else True
    return segments[0] <= TWIN_SCENES_IN_ALL and all(n <= 1 for n in segments[1:]) and walled and not report["stepped_after"]


def run_one(name: str, seed: int, root: Path | None = None, label: str = "") -> dict:
    """One run of plan `name` at `seed`, in-process, from this repo or (a REVERT) from the COPY at `root`."""
    args, intended = PLANS[name]
    run_dir = Path(tempfile.mkdtemp(prefix=f"ai_rate3_{label or 'real'}_{name}_{seed}_"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env["PYTHONUTF8"] = "1"
    harness = HARNESS
    if root is not None:
        harness = root / "ai_player" / "gates" / HARNESS.name
        env["AI_PLAYER_BUILD_ROOT"] = str(REPO / "sandbox-pokebot")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    # (the step-3.1 verifier's second round) the cartridge's clock pinned (`hands_harness.pin_game_clock`): the game reads it
    # at every map load, so an unpinned sweep is a different sweep at another hour (live_step3 arm CLOCKS)
    proc = subprocess.Popen([sys.executable, str(harness), *args, "--seed", str(seed), "--run-dir", str(run_dir),
                             "--game-clock", GAME_CLOCK], cwd=str(REPO),
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
              "var_town": truth.get("VAR_LITTLEROOT_TOWN_STATE"),
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
        result["roam"] = {k: metrics.get(k) for k in ("steps", "attempts", "interrupted", "not_moved", "spins", "reversals",
                                                      "in_place", "preempted", "spin_ratio", "strict_ratio",
                                                      "spin_ratio_of_attempts", "distinct", "most_visited", "encounters", "fled")}
    else:
        # (build step 3.1, the step-3 review's finding 2) reversals on the player's path as the looks showed it
        last = _last_line(world_file) if world_file.is_file() else None
        run = Run(ARMS[0], records=records, world=json.loads(last) if last else None)
        steps, found = path_reversals(run)
        result["walk"] = {"steps": steps, "reversals": len(found), "which": [(r["map"], r["kind"], r["tiles"]) for r in found]}
        result["stale"] = sum(1 for r in records if r.get("decision") == "world" and "is not worth going to any more" in str(r.get("reason")))
        result["scenes"] = sum(1 for r in records if r.get("decision") == "world" and str(r.get("reason", "")).startswith("a scene stopped the way"))
        # (the step-3.1 verifier's round) frontier targets WALKED ONTO with everything beside them seen (`stale_arrivals`)
        chosen, arrived = stale_arrivals(run)
        result["walked_stale"] = sum(1 for a in arrived if a["everything_beside_it_seen"])
    if name == "SCENE-EXPLORE":
        result["twin"] = twin_report(records)
        result["ok"] = ok = ok and twin_ok(result["twin"])
    # (the step-3.1 verifier's round) every wild battle met, fled, and the game's own count (ROUTE's flee, seed by seed)
    lines = data.get("lines") or []
    start = (data.get("start_truth") or {}).get("game_stats") or {}
    end = truth.get("game_stats") or {}
    result["battles"] = {"met": sum(1 for l in lines if l.startswith("[AI-WORLD] battle:")),
                         "fled": sum(1 for l in lines if l.startswith("[AI-WORLD] battle: fled")),
                         "game": (end.get("wild_battles") - start.get("wild_battles"))
                         if isinstance(end.get("wild_battles"), int) and isinstance(start.get("wild_battles"), int) else None}
    walk = result.get("walk")
    result["line"] = (f"seed {seed}: {data['reason'][:120]!r} frames {data['frames']} map {truth['map']}"
                      + (f" | reversals {walk['reversals']} in {walk['steps']} steps, {result['stale']} stale targets dropped, "
                         f"{result['walked_stale']} stale walked onto, {result['scenes']} scenes held against a target" if walk else "")
                      + (f" | the twin sent the player back {result['twin']['total']} times, by tile {result['twin']['per_tile']}, "
                         f"before any news and between news {result['twin']['segments']}, given up {result['twin']['walls']}, its "
                         f"targets {result['twin']['targets']}, stepped on while given up: {result['twin']['stepped_after'] or 'none'}; "
                         f"news {[w[:24] for w in result['twin']['news']]}; VAR_LITTLEROOT_TOWN_STATE {result.get('var_town')}"
                         if "twin" in result else "")
                      + (f" | first exploring choice {result['first_exploring']}; headings by map {result['headings']}" if exploring else ""))
    return result


def _last_line(path: Path) -> str | None:
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return lines[-1] if lines else None


def run_plans(jobs: list[tuple[str, int]], workers: int, root: Path | None = None, label: str = "") -> list[dict]:
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return list(pool.map(lambda job: run_one(job[0], job[1], root, label), jobs))


def live_frames(name: str, code: str) -> int | None:
    """The real frames of `live_step3.py`'s arm `name` in today's evidence, when that evidence is of THIS tree (its code
    line equal to this run's), else None: the seed-3 run here is that trajectory replayed."""
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step3-{name}.txt"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if f"code: {code}" not in text:
        return None
    match = re.search(r'"real_frames": (\d+)', text)
    return int(match.group(1)) if match else None


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="The step-3 seed sweep.")
    parser.add_argument("--plans", default=",".join(PLANS))
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--no-reverts", action="store_true", help="development only: skip the REVERT section")
    parser.add_argument("--tag", default="", help="development only: a suffix for the evidence file's name")
    args = parser.parse_args()
    wanted = [p.strip() for p in args.plans.split(",") if p.strip()]
    seeds = list(range(1, args.seeds + 1))
    code = provenance(REPO)
    began = time.time()
    jobs = [(name, seed) for name in wanted for seed in seeds]
    results = run_plans(jobs, args.workers)
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
    # (build step 3.1, the step-3 review's finding 2) REVERSALS on every walking plan, seed by seed: A -> B -> A or a
    # U-turn's third step, on the player's path as the looks showed it (`live_step3.reversals`); the bounds are the
    # pre-registered `REVERSALS_PER_RUN` a run and `REVERSALS_PER_100` a plan (a CROP run is a fault arm: reported, not
    # bounded); and (the step-3.1 verifier's round) the frontier targets walked onto with everything beside them seen
    walking = [name for name in by_plan if name != "ROAM"]
    reversal_ok = True
    if walking:
        out += ["", f"---- REVERSALS (finding 2): per run, on the AI's own steps as the looks confirmed them; bound "
                    f"{REVERSALS_PER_RUN} per run and {REVERSALS_PER_100} per 100 steps per plan on the EXPLORING plans "
                    f"{EXPLORING} (the others reported: CROP a fault arm, STUCK, SCENE and SCENE-EXPLORE a scene sending the "
                    f"player back, by design); 'stale walked onto': frontier targets the AI walked onto with everything beside "
                    f"them already seen (live_step3.stale_arrivals) ----"]
        for name in walking:
            line, ok = reversal_line(name, by_plan[name], name in EXPLORING)
            reversal_ok &= ok
            out.append(line)
            for r in by_plan[name]:
                if (r.get("walk") or {}).get("which"):
                    out.append(f"    seed {r['seed']}: {r['walk']['which']}")
    # (the step-3.1 verifier's round) THE REVERTS: the same plans and seeds from a COPY with a rule reverted, by the same
    # metric; each must break what the real code meets (the sweep's own fault arm, and the A/B the README quotes)
    revert_ok = True
    if not args.no_reverts:
        out += ["", "---- REVERTS (the step-3.1 verifier's round): the same plans and seeds from a COPY of the package with ONE "
                    "rule reverted, graded by the same metric; PREDICTED (pre-registered in live_step3.py's docstring) to break "
                    "what the real code meets ----"]
        for label, (mutations, plans, prediction) in REVERT_PREDICTIONS.items():
            plans = [p for p in plans if p in wanted]
            if not plans:
                continue
            root = make_copy(mutations)
            try:
                rows = run_plans([(name, seed) for name in plans for seed in seeds], args.workers, root, label)
            finally:
                shutil.rmtree(root, ignore_errors=True)
            out.append(f"{label}: {len(mutations)} edit(s) {[m[1].strip()[:60] for m in mutations]}; PREDICTED: {prediction}")
            if label == "FINDING-2":
                broken, totals = [], [0, 0, 0, 0]
                for name in plans:
                    mine = [r for r in rows if r["name"] == name]
                    line, ok = reversal_line(name, mine, True)
                    real_line, _ = reversal_line(name, by_plan.get(name, []), True)
                    out.append(f"    REVERTED {line}")
                    out.append(f"    REAL     {real_line}")
                    broken.append(not ok)
                    totals[0] += sum((r.get("walk") or {}).get("reversals") or 0 for r in mine)
                    totals[1] += sum((r.get("walk") or {}).get("steps") or 0 for r in mine)
                    totals[2] += sum((r.get("walk") or {}).get("reversals") or 0 for r in by_plan.get(name, []))
                    totals[3] += sum((r.get("walk") or {}).get("steps") or 0 for r in by_plan.get(name, []))
                walked = sum(r.get("walked_stale") or 0 for r in rows)
                real_walked = sum(r.get("walked_stale") or 0 for name in plans for r in by_plan.get(name, []))
                held = all(broken) and walked > 0 and real_walked == 0
                revert_ok &= held
                out.append(f"FINDING-2 A/B, the exploring plans, seeds {seeds[0]}-{seeds[-1]}: REVERTED {totals[0]} reversals in "
                           f"{totals[1]} steps, {walked} stale targets walked onto; REAL {totals[2]} in {totals[3]}, {real_walked} "
                           f"walked onto; plans over the bound when reverted: {sum(broken)} of {len(plans)} -> the prediction "
                           f"{'HELD' if held else 'FAILED'}")
            elif label == "SCENE-WORDS":
                first = [((r.get("twin") or {}).get("segments") or [0])[0] for r in rows]
                real_first = [((r.get("twin") or {}).get("segments") or [0])[0] for name in plans for r in by_plan.get(name, [])]
                over = sum(1 for w in first if w > TWIN_SCENES_IN_ALL)
                held = over >= 8 and all(w <= TWIN_SCENES_IN_ALL for w in real_first)
                revert_ok &= held
                for r in rows:
                    out.append(f"    REVERTED {'OK ' if r.get('ok') else 'BAD'} {r['line']}")
                out.append(f"SCENE-WORDS A/B, SCENE-EXPLORE, seeds {seeds[0]}-{seeds[-1]}: the twin's push-backs BEFORE ANY NEWS "
                           f"per seed REVERTED {first}, REAL {real_first}; seeds over {TWIN_SCENES_IN_ALL} when reverted: {over} of "
                           f"{len(rows)} (predicted >= 8) -> the prediction {'HELD' if held else 'FAILED'}")
            else:
                # SCENE-NEWS: new words not progress: the seeds the real code takes to Route 101 stay in Littleroot
                real_rows = {r["seed"]: r for name in plans for r in by_plan.get(name, [])}
                reached = sorted(s for s, r in real_rows.items() if r.get("map") == [0, 16])
                stayed = sorted(r["seed"] for r in rows if r.get("map") != [0, 16] and not (r.get("twin") or {}).get("lifts"))
                held = len(reached) >= SCENE_NEWS_REACHED and set(reached) <= set(stayed)
                revert_ok &= held
                for r in rows:
                    out.append(f"    REVERTED {'OK ' if r.get('ok') else 'BAD'} {r['line']}")
                out.append(f"SCENE-NEWS A/B, SCENE-EXPLORE, seeds {seeds[0]}-{seeds[-1]}: REAL reached ROUTE101 on seeds {reached}; "
                           f"REVERTED (new words not progress) stayed off it, the twin never tried again, on seeds {stayed} -> the "
                           f"prediction {'HELD' if held else 'FAILED'}")
    # (the step-3.1 verifier's round) the explorer's own targets behind the twin, and the errand labelled for what it is
    scene_ok = True
    if "SCENE-EXPLORE" in by_plan or "SCENE" in by_plan:
        out += ["", "---- SCENES (finding 3; the step-3.1 verifier's round) ----"]
        if "SCENE" in by_plan:
            rows = by_plan["SCENE"]
            out.append(f"SCENE (the errand (10,4) then (10,0)): ONE scripted scenario, the targets fixed by the errand list: its "
                       f"{len(rows)} seeds differ only by the path noise and the pacing (frames {sorted({r.get('frames') for r in rows})}); "
                       f"it is the rule on an errand, not on the explorer's choices (SCENE-EXPLORE)")
        if "SCENE-EXPLORE" in by_plan:
            rows = by_plan["SCENE-EXPLORE"]
            sequences = {tuple(r.get("sequence") or ()) for r in rows}
            targets = {tuple(t) for r in rows for t in (r.get("twin") or {}).get("targets", [])}
            scene_ok = all(r.get("twin") is not None and twin_ok(r["twin"]) for r in rows) \
                and all(len((r.get("twin") or {}).get("targets", [])) >= 2 for r in rows) \
                and all(((r.get("twin") or {}).get("segments") or [0])[0] >= 2 for r in rows)
            segments = [(r["seed"], (r.get("twin") or {}).get("segments")) for r in rows]
            ends = [(r["seed"], r.get("map"), r.get("var_town"), str(r.get("reason", ""))[:24]) for r in rows]
            reached = sum(1 for r in rows if r.get("map") == [0, 16])
            out.append(f"SCENE-EXPLORE (the EXPLORER's own targets, to its own end): {len(sequences)} different target sequences in "
                       f"{len(rows)} seeds; {len(targets)} different targets the twin stopped over the seeds ({sorted(targets)}); "
                       f"the twin's push-backs per seed, before any news and between news {segments}; every seed: sent back "
                       f"2..{TWIN_SCENES_IN_ALL} times before any news, every tile she began on then given up and not stepped on "
                       f"until news, at most once more after each news, and >= 2 different targets of its own stopped: {scene_ok}")
            out.append(f"SCENE-EXPLORE, AFTER THE TWIN (each seed's end: map, VAR_LITTLEROOT_TOWN_STATE, outcome): {ends}; reached "
                       f"ROUTE101 (May met, the twin tried again and passed): {reached} of {len(rows)}")
    # (the step-3.1 verifier's round: "ROUTE seed 3 no longer meets a wild battle") ROUTE's flee, seed by seed
    flee_ok = True
    if "ROUTE" in by_plan:
        rows = by_plan["ROUTE"]
        per = [(r["seed"], r.get("battles") or {}) for r in rows]
        flee_ok = all(b.get("met") == b.get("fled") == b.get("game") for _, b in per) and any((b.get("met") or 0) > 0 for _, b in per)
        out += ["", "---- ROUTE's FLEE (the step-3.1 verifier's round), seed by seed: battles met / fled / the game's own wild-battle "
                    "count rise ----",
                f"ROUTE: {[(s, b.get('met'), b.get('fled'), b.get('game')) for s, b in per]}; {sum(1 for _, b in per if b.get('met'))} "
                f"of {len(per)} seeds met a wild battle; every one met was fled and counted by the game: {flee_ok}"]
    # (the step-3.1 verifier's round, CLAUDE.md rule 8) seed 3 is the live arm's trajectory, replayed
    out += ["", "---- REPLAY, NOT REPLICATION: each plan's seed 3 is live_step3.py's arm of the same name, replayed in-process "
                "(the harness and the launcher play one seed identically): a determinism check, not another sample ----"]
    arms = {arm.name for arm in ARMS}
    for name, rows in by_plan.items():
        three = next((r for r in rows if r["seed"] == 3), None)
        arm = LIVE_ARM.get(name, name)
        if name in REPLAY_NOTES:
            out.append(f"{name}: seed 3 here {three.get('frames') if three else None} frames; {REPLAY_NOTES[name]}")
            continue
        if arm not in arms:
            out.append(f"{name}: no live arm plays it (its 10 seeds are all in-process samples)")
            continue
        live = live_frames(arm, code) if three is not None else None
        clock = (f" (the live arm reads the HOST's clock and {arm} is CLOCK-SENSITIVE, live_step3 arm CLOCKS: the same trajectory "
                 f"only when the host's clock gives what the pinned clock {GAME_CLOCK} gives)" if arm in CLOCK_SENSITIVE else "")
        out.append(f"{name}: seed 3 here {three.get('frames') if three else None} frames (the clock pinned at {GAME_CLOCK}); the "
                   f"live arm {arm} on this tree {live if live is not None else '(no evidence of this tree yet)'}"
                   f"{'' if live is None else ' -> the same trajectory: ' + str(live == three.get('frames'))}{clock}")
    if "ROAM" in by_plan:
        out += ["", "---- ROAM (the verifier's weak proof 5; build step 3.1 finding 9): BOTH ratios, the back-and-forth spin "
                    "ratio over TRAINING STEPS (the criterion, < 2%) and the strict non-moving-press ratio over every press "
                    "(reported: its pre-empted presses are battles rolled at the end of the step before) ----"]
        for r in by_plan["ROAM"]:
            m = r.get("roam") or {}
            out.append(f"    seed {r['seed']:>2}: back-and-forth {m.get('spin_ratio')} ({m.get('reversals')} reversals + "
                       f"{m.get('in_place')} in place / {m.get('steps')} steps); strict {m.get('strict_ratio')} ({m.get('in_place')} "
                       f"in place + {m.get('preempted')} pre-empted / {m.get('attempts')} presses); {json.dumps(m)}")
        spin_ok = all(isinstance((r.get("roam") or {}).get("spin_ratio"), (int, float)) and r["roam"]["spin_ratio"] < 0.02
                      for r in by_plan["ROAM"])
        out.append(f"ROAM: every seed's back-and-forth spin ratio < 2%: {spin_ok}")
        reversal_ok &= spin_ok
    verdict = total_ok == len(results) and separated and reversal_ok and revert_ok and scene_ok and flee_ok
    out += ["", f"{total_ok} of {len(results)} runs as intended; reversal bounds met: {reversal_ok}; reverts as predicted: "
                f"{revert_ok if not args.no_reverts else 'not run'}; scenes: {scene_ok}; ROUTE's flee: {flee_ok}; "
                f"{time.time() - began:.0f} s of wall clock with {args.workers} workers", f"OVERALL: {'PASS' if verdict else 'FAIL'}"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step3-RATE{args.tag}.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(line for line in out if not line.startswith("    ")))
    print(f"evidence: {path.relative_to(REPO)}")
    return 0 if verdict else 1


def reversal_line(name: str, rows: list[dict], bounded: bool) -> tuple[str, bool]:
    """One plan's reversals over its seeds against the bounds (`REVERSALS_PER_RUN` a run, `REVERSALS_PER_100` a plan)."""
    counts = [(r.get("walk") or {}).get("reversals") for r in rows]
    steps = sum((r.get("walk") or {}).get("steps") or 0 for r in rows)
    total = sum(c or 0 for c in counts)
    rate = 100.0 * total / steps if steps else 0.0
    walked = sum(r.get("walked_stale") or 0 for r in rows)
    ok = (not bounded) or (all(isinstance(c, int) and c <= REVERSALS_PER_RUN for c in counts) and rate <= REVERSALS_PER_100)
    return (f"{name}: {total} reversals in {steps} steps over {len(rows)} seeds ({rate:.2f} per 100 steps); per seed {counts}; "
            f"stale walked onto {walked}{'' if bounded else ' (reported, not bounded)'} -> {'OK' if ok else 'OVER THE BOUND'}", ok)


if __name__ == "__main__":
    sys.exit(main())
