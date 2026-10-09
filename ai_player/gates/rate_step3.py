"""THE SEED SWEEP of AI-player build step 3: how OFTEN each walk does what it should, over seeds (a FREQUENCY measurement,
CLAUDE.md rule 9), in-process (`gates/hands_harness.py`, each run in its own process and throwaway emulator), each run
graded by its SECOND-PATH truth (save block 1, read after the run, never the AI's eyes).

    py -3.12 ai_player/gates/rate_step3.py [--plans HOUSE,TOWN,...] [--seeds 10] [--workers 4] [--first-seed 1]

(The step-4 verifier's second round: "determinism replays aren't replications".) Seeds 1..N are the seeds of the
development sweeps every bound below was registered from, so the graded run REPLAYS them (a determinism check of those
numbers); `--first-seed 101` plays HELD-OUT seeds no development run played, graded by the same bounds: a replication
(evidence `<date>-step3-RATE-SEEDS101-110.txt`).

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
BUILD STEP 3.2 (the step-3.1 adversarial review: "the reversal metric cannot see laps"):
  * LAPS AND THE SHORTEST WAY, per run (`live_step3.lap_report`): laps (back on a tile 4..12 steps later, nothing new between)
    and the steps walked to each target beyond the shortest way the memory knew; bounded per run on the exploring plans and
    SCENE-EXPLORE (`LAP_SWEEP_BOUNDS`, pre-registered from the development sweep named in live_step3.py's docstring, "AFTER
    STEP 3.2"); and the targets chosen ON THE MOVE: whether the walk kept its heading (`live_step3.choices_on_the_move`).
  * REVERTS: LAPS (finding 1 reverted: the turn-back cost on every replan, no plan followed: `live_step3.LAPS_MUTATION`) and
    WHIM (finding 4 reverted: a target chosen on the move picked on a whim: `WHIM_MUTATION`), each with its prediction.
  * REVERSALS: the per-100-steps bound is over the exploring plans TOGETHER (`REVERSALS_PER_100`): a target behind is now
    reached by turning back (laps were invisible to the reversal metric, and the step-3.1 code walked them instead), and
    HOUSE's walks are 10 to 18 steps, so one turn back at the end of the player's room in one seed is 6 per 100 for that
    plan alone. The per-run bound (`REVERSALS_PER_RUN`) is unchanged.
THE STEP-3.2 VERIFIER'S ROUND ("the new CYCLE check (`laps`) does not tell the fix from the revert ... 1 lap was found in
60 reverted runs"; "steps-vs-shortest is measured per DECISION"):
  * RINGS per run (`live_step3.rings`: back on a tile 4..12 steps later having walked ROUND, whatever was seen on the way),
    bounded at 1 a run on the lapped plans (`LAP_SWEEP_BOUNDS`) and `LAPS_REAL_RINGS` over them together; the LAPS revert
    must ring at least `LAPS_REVERT_RINGS` times in at least `LAPS_REVERT_RINGED` runs (pre-registered from this round's
    development sweep: the real code 2 rings in 60 runs, each across a target that vanished with every leg the shortest
    way to its own target; the revert 36 in 14).
  * JOURNEYS per run (`live_step3.journeys`), reported with the real and reverted totals, not bounded (an exploring walk
    ends where it stopped, not at a destination).
THE STEP-4 VERIFIER'S ROUND (its FAILURE: "Step 3.2 finding 4 ... is NOT fixed ... the churn is still there"; its weak
proofs "SCENE-EXPLORE has 2.91 reversals per 100 steps and its journey excess is not bounded", "laps cannot tell the fix
from the revert", the subset-evidence hazard of `revert_step3.py`):
  * CHURN per lapped plan (`live_step3.churn`): decisions on the move per 100 steps, the one-step walks' share, and the
    VISIBLE COST, every journey's share of steps beyond the shortest known way (detours included), bounded per plan
    (`CHURN_SWEEP_BOUNDS`); SCENE-EXPLORE's reversals per 100 steps and journeys bounded
    (`SCENE_EXPLORE_REVERSALS_PER_100`, `SCENE_EXPLORE_JOURNEY_SHARE`).
  * REVERT CHURN (`live_step3.CHURN_MUTATION`: the decision never carried on, the step-3.2 rule) on the lapped plans but
    HOUSE (no frontier there is ever carried on): PREDICTED more decisions and one-step walks, every plan over the bounds,
    and the real code's cost no dearer (`CHURN_*`).
  * the rings' bound is on LAP RINGS (`live_step3.lap_ring`); the LAPS revert's ring predictions are on them; the twin
    after news at most once on each tile (`live_step3.once_a_tile_after_news`).
  Every number re-registered from development sweeps of the final code (their files moved out of the evidence folder).
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
    ARMS, CHURN_MUTATION, CLOCK_SENSITIVE, GAME_CLOCK, LAP_STEPS, LAPS_MUTATION, NEWS_MUTATION, REVERSALS_PER_RUN, SCENEWORDS_MUTATION,
    STALE_MUTATIONS, TWIN_SCENES_IN_ALL, TWIN_SCENES_PER_TILE, WHIM_MUTATION, Run, choices_on_the_move, churn, lap_report,
    map_name_of, once_a_tile_after_news, path_reversals, stale_arrivals, twin_scenes,
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
                  "(since build step 3.2) at least FINDING2_PLANS_OVER of the exploring plans have a run over REVERSALS_PER_RUN, "
                  "the plans together are over REVERSALS_PER_100, and frontier targets are walked onto with everything beside "
                  "them seen (none with the rules)"),
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
#: (build step 3.2) the plans whose laps and walks are bounded per run (`LAP_SWEEP_BOUNDS`, pre-registered: live_step3.py's
#: docstring "AFTER STEP 3.2"): the exploring plans and the explorer behind the twin
LAPPED = EXPLORING + ("SCENE-EXPLORE",)
#: per run: no lap; at most 2 steps beyond the shortest known way on any one target (a step round someone standing in the
#: way: people move, so the memory's shortest way does not know them; measured, the development sweep's SCENE-EXPLORE
#: seeds 3, 7, 9: (14, 9) -> (11, 0) in 14 steps for 12, past the twin), at most 4 in all
#: (the step-3.2 verifier's round) and at most ONE ring per run: the development sweep of this round found the real code ring
#: twice in its 60 lapped runs (SCENE-EXPLORE seeds 1 and 6, once each), each across a TARGET that vanished (unreachable;
#: everything beside it seen), every leg the shortest known way to its own target ((12, 15) -> the door (7, 17) in 7, the
#: shortest; (5, 3) -> (7, 2) in 3, the shortest): a person comes back by a way as short as the one gone by. The reverted
#: code rang 36 times in 14 runs (SCENE-EXPLORE every seed, up to 4; ROUTE seed 9 six times with 0 steps beyond its targets)
#: (the step-4 verifier's round) the bound is on LAP RINGS (`live_step3.lap_ring`: a ring with a leg walked beyond the shortest
#: way to its own target); every ring is reported, an excursion (each leg the shortest way to its own target) included
LAP_SWEEP_BOUNDS = {"laps": 0, "excess": 4, "worst": 2, "lap_rings": 1}
#: (the step-3.2 verifier's round) rings over the lapped plans' runs together: the real code at most this many (development
#: sweep: 2), the LAPS revert at least `LAPS_REVERT_RINGS` (development sweep: 36); (the step-4 verifier's round) LAP rings
LAPS_REAL_RINGS = 4
LAPS_SPAN = f"{LAP_STEPS[0]}..{LAP_STEPS[1]}"
#: (build step 3.2) the LAPS revert's prediction: runs over `LAP_SWEEP_BOUNDS` with finding 1 reverted, at least (the
#: development sweep: SCENE-EXPLORE's 10 seeds, 12 to 48 steps beyond each; HOUSE and TOWN-Trainer one seed each)
LAPS_REVERT_OVER = 8
#: (the step-3.2 verifier's round) the LAPS revert's RINGS prediction: rings in the reverted copy's lapped runs together, at
#: least (the development sweep of this round: 36 in 14 runs; the real code 2), and runs with a ring, at least (14)
LAPS_REVERT_RINGS = 20
LAPS_REVERT_RINGED = 8
#: (build step 3.2) the WHIM revert's prediction: the share of targets chosen on the move after which the walk keeps its
#: heading falls by at least this much with the whim (the development sweep: 88% with the heading rule, 61% without)
WHIM_REVERT_DROP = 0.15
#: (build step 3.2) the FINDING-2 revert's prediction: exploring plans with a run over `REVERSALS_PER_RUN` (2 since step 3.2)
#: when reverted, at least (the development sweep: HOUSE 3, TOWN 4, TOWN-Catcher 3, TOWN-Trainer 4; ROUTE's worst 2)
FINDING2_PLANS_OVER = 4


def lap_run_ok(row: dict) -> bool:
    """(build step 3.2) One run within `LAP_SWEEP_BOUNDS` (laps, steps beyond the shortest known ways, the worst target),
    at least one walk graded."""
    laps = row.get("laps") or {}
    bound = LAP_SWEEP_BOUNDS
    return (isinstance(laps.get("laps"), int) and (laps.get("graded") or 0) > 0 and laps["laps"] <= bound["laps"]
            and laps["excess"] <= bound["excess"] and laps["worst"] <= bound["worst"]
            and isinstance(laps.get("lap_rings"), int) and laps["lap_rings"] <= bound["lap_rings"])
#: (the step-4 verifier's round, its FAILURE: "Step 3.2 finding 4 ... is NOT fixed ... the churn is still there") THE CHURN
#: per lapped plan over its seeds together (`live_step3.churn`), PRE-REGISTERED from this round's development sweep (20 seeds
#: of TOWN, ROUTE, SCENE-EXPLORE, TOWN-Catcher, TOWN-Trainer; the docstring "THE STEP-4 VERIFIER'S ROUND"): decisions made ON
#: THE MOVE per 100 steps walked, the share of walks to a decision that are ONE step, and THE VISIBLE COST, every journey's
#: steps beyond the shortest known way over the steps those journeys walked.
CHURN_SWEEP_BOUNDS = {"move_per_100": 30.0, "ones": 0.40, "journey_share": 0.50}
#: the CHURN revert (the decision never carried on: the step-3.2 rule) over the lapped plans together, PREDICTED: at least
#: `CHURN_REVERT_DECISIONS` times the real code's decisions and `CHURN_REVERT_ONES` times its one-step walks; and the real
#: code's VISIBLE COST no dearer: its steps at most `CHURN_COST_STEPS` times the revert's, its journeys' share beyond at
#: most the revert's + `CHURN_COST_SHARE` (a development sweep of the final code, 20 seeds of TOWN, ROUTE, SCENE-EXPLORE,
#: TOWN-Catcher, TOWN-Trainer: decisions 1,290 against 2,952, one-step walks 290 against 1,920, steps 5,965 against
#: 5,881, every journey 1,496 beyond of 5,387 walked (0.28) against 1,644 of 5,527 (0.30); this driver's own development
#: sweep of 10 seeds is in its docstring)
CHURN_REVERT_DECISIONS = 2.0
CHURN_REVERT_ONES = 3.0
CHURN_COST_STEPS = 1.10
CHURN_COST_SHARE = 0.05
#: (the step-4 verifier's weak proof: "SCENE-EXPLORE has 2.91 reversals per 100 steps and its journey excess is not
#: bounded. Both are reported, not graded") its bounds, pre-registered from this round's development sweeps (the final
#: code, 20 seeds: 79 reversals in 2,902 steps, 2.72 per 100; every journey 822 beyond of 2,324 walked, 0.35; the step-3.2
#: rule's 2.67 per 100 and 0.36)
SCENE_EXPLORE_REVERSALS_PER_100 = 3.5
SCENE_EXPLORE_JOURNEY_SHARE = 0.45
REVERT_PREDICTIONS.update({
    "LAPS": ((LAPS_MUTATION,), LAPPED,
             "the turn-back cost on every replan walks round where the real code turns back: over the lapped plans, more steps "
             "beyond the shortest known ways than the real code's, and at least 3 runs over `LAP_SWEEP_BOUNDS`"),
    "WHIM": ((WHIM_MUTATION,), ("TOWN", "TOWN-Catcher", "TOWN-Trainer"),
             "a target chosen on the move on a whim: on the TOWN plans the walk keeps its heading after such a choice less "
             "often than with the heading rule"),
    # (the step-4 verifier's round, its FAILURE) the decision never carried on: the step-3.2 rule. Not HOUSE: the player's
    # room and the house's 1F are smaller than the screen, so no frontier there is ever seen past and carried on (the
    # development sweep: 30 decisions, 0 carried on, the same with and without), so nothing there can tell the two apart
    "CHURN": ((CHURN_MUTATION,), tuple(p for p in LAPPED if p != "HOUSE"),
              "the decision never carried on: over the lapped plans at least CHURN_REVERT_DECISIONS times the decisions and "
              "CHURN_REVERT_ONES times the one-step walks of the real code, every plan over CHURN_SWEEP_BOUNDS; and the real "
              "code's visible cost no dearer (its steps at most CHURN_COST_STEPS times the revert's, its journeys' share beyond "
              "at most CHURN_COST_SHARE over)"),
})


def churn_cells(rows: list[dict]) -> dict:
    """(the step-4 verifier's round) The churn of `rows` together: decisions, on the move, carried on, the step-3.2 rule's
    counterfactual, steps, walks, one-step walks, every journey's walked and beyond, and the shares."""
    cells = {key: sum((r.get("churn") or {}).get(key) or 0 for r in rows)
             for key in ("decisions", "on_the_move", "carried", "would", "dropped", "refused_better", "steps", "walks", "ones")}
    cells["jall_walked"] = sum((r.get("laps") or {}).get("jall_walked") or 0 for r in rows)
    cells["jall_excess"] = sum((r.get("laps") or {}).get("jall_excess") or 0 for r in rows)
    cells["move_per_100"] = round(100.0 * cells["on_the_move"] / cells["steps"], 1) if cells["steps"] else 0.0
    cells["ones_share"] = round(cells["ones"] / cells["walks"], 2) if cells["walks"] else 0.0
    cells["journey_share"] = round(cells["jall_excess"] / cells["jall_walked"], 2) if cells["jall_walked"] else 0.0
    return cells


def churn_ok(cells: dict) -> bool:
    bound = CHURN_SWEEP_BOUNDS
    return (cells["walks"] > 0 and cells["move_per_100"] <= bound["move_per_100"] and cells["ones_share"] <= bound["ones"]
            and cells["journey_share"] <= bound["journey_share"])


def churn_text(cells: dict) -> str:
    return (f"{cells['decisions']} decisions in {cells['steps']} steps, {cells['on_the_move']} on the move ({cells['move_per_100']} "
            f"per 100 steps); {cells['carried']} places carried on (the step-3.2 rule would have gone elsewhere at {cells['would']}); "
            f"{cells['dropped']} stale targets dropped for a new decision ({cells['refused_better']} for something clearly better); "
            f"walks of ONE step {cells['ones']} of {cells['walks']} ({cells['ones_share']}); every journey {cells['jall_excess']} "
            f"steps beyond of {cells['jall_walked']} walked ({cells['journey_share']})")


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
            "segments": t["segments"], "segment_tiles": t["segment_tiles"], "lifts": lifts, "news": [w for _, w in t["news"]],
            "passed_her": len(t["passed_her"])}


def twin_ok(report: dict) -> bool:
    """The rule's grade on one run (the step-3.1 verifier's second round): before any news, the twin sends the player back
    at most `TWIN_SCENES_IN_ALL` times and every tile she began on is then given up; after each news at most once more; a
    tile given up is never stepped on until news lifts it."""
    segments = report.get("segments") or [0]
    walled = report["first_walls"] == sorted(report["per_tile"]) if segments[0] >= 2 else True
    # (the step-4 verifier's round) after each news at most once ON EACH TILE (`live_step3.once_a_tile_after_news`: the old
    # "at most once in all" failed the development sweep's seed 10, in which the rule did exactly what it says)
    return (segments[0] <= TWIN_SCENES_IN_ALL and once_a_tile_after_news(report.get("segment_tiles") or [{}]) and walled
            and not report["stepped_after"])


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
        # (build step 3.2) laps and the walks against the shortest known ways; the targets chosen on the move
        report = lap_report(run)
        worst = report["worst_walk"] or {}
        result["laps"] = {"laps": len(report["laps"]), "excess": report["excess"], "worst": report["worst"],
                          "graded": report["graded"], "walked": report["walked"], "shortest": report["shortest"],
                          "which": [(lap["map"], lap["tile"], lap["steps"]) for lap in report["laps"]],
                          "worst_walk": [worst.get("map"), worst.get("kind"), worst.get("from"), worst.get("to"),
                                         worst.get("walked"), worst.get("shortest")] if worst else None,
                          # (the step-3.2 verifier's round) rings, and journeys (reported); (the step-4 verifier's round)
                          # the LAP rings (a leg walked beyond its shortest way), and EVERY journey (detours included)
                          "rings": len(report["rings"]), "lap_rings": len(report["lap_rings"]),
                          "ring_which": [(ring["map"], ring["tile"], ring["steps"], "LAP" if ring["lap"] else "excursion")
                                         for ring in report["rings"]],
                          "jgraded": report["journeys_graded"], "jtargets": report["journey_targets"],
                          "jwalked": report["journey_walked"], "jshortest": report["journey_shortest"],
                          "jexcess": report["journey_excess"], "jworst": report["journey_worst"],
                          "jall_walked": report["journey_all_walked"], "jall_excess": report["journey_all_excess"]}
        moves = choices_on_the_move(run)
        result["moves"] = {key: moves[key] for key in ("chosen", "on", "aside", "back")}
        # (the step-4 verifier's round, its FAILURE: finding 4's churn) how often the AI decided (`live_step3.churn`)
        c = churn(run, report)
        result["churn"] = {key: c[key] for key in ("decisions", "on_the_move", "carried", "would", "dropped", "refused_better",
                                                   "steps", "walks", "ones")}
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
    laps, moves = result.get("laps") or {}, result.get("moves") or {}
    result["line"] = (f"seed {seed}: {data['reason'][:120]!r} frames {data['frames']} map {truth['map']}"
                      + (f" | reversals {walk['reversals']} in {walk['steps']} steps, {result['stale']} stale targets dropped, "
                         f"{result['walked_stale']} stale walked onto, {result['scenes']} scenes held against a target" if walk else "")
                      + (f" | laps {laps['laps']}, {laps['excess']} steps beyond the shortest known ways ({laps['walked']} walked "
                         f"to {laps['graded']} targets, {laps['shortest']} the shortest; the worst {laps['worst']}); chosen on the "
                         f"move {moves.get('chosen')}: kept the heading {moves.get('on')}, aside {moves.get('aside')}, back "
                         f"{moves.get('back')}" if laps else "")
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
    # (the step-4 verifier's second round: "determinism replays aren't replications") the graded sweep plays the SAME
    # seeds as the development sweeps its bounds came from, so it replays them; a sweep from another first seed is a
    # HELD-OUT replication (its evidence file named by its seeds), graded by the same pre-registered bounds
    parser.add_argument("--first-seed", type=int, default=1)
    args = parser.parse_args()
    wanted = [p.strip() for p in args.plans.split(",") if p.strip()]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    code = provenance(REPO)
    began = time.time()
    jobs = [(name, seed) for name in wanted for seed in seeds]
    results = run_plans(jobs, args.workers)
    by_plan = {name: [r for r in results if r["name"] == name] for name in wanted}
    out = ["AI PLAYER BUILD STEP 3 - RATE SWEEP (gates/rate_step3.py; in-process gates/hands_harness.py, each run graded by its "
           "second-path truth)", f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}",
           "a FREQUENCY measurement (CLAUDE.md rule 9); the purity of the same code is live_step3.py's launcher arms",
           f"seeds {seeds[0]}-{seeds[-1]}: " + ("the seeds of the development sweeps the bounds came from (this run REPLAYS "
           "them: a determinism check of those numbers, not another sample)" if args.first_seed == 1 else "HELD OUT (no "
           "development run played them): a REPLICATION, graded by the same pre-registered bounds"), ""]
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
                    f"{REVERSALS_PER_RUN} per run on the EXPLORING plans {EXPLORING} and (build step 3.2) "
                    f"{REVERSALS_PER_100} per 100 steps over those plans TOGETHER (the others reported: CROP a fault arm, "
                    f"STUCK, SCENE and SCENE-EXPLORE a scene sending the player back, by design); 'stale walked onto': frontier "
                    f"targets the AI walked onto with everything beside them already seen (live_step3.stale_arrivals) ----"]
        for name in walking:
            line, ok = reversal_line(name, by_plan[name], name in EXPLORING)
            reversal_ok &= ok
            out.append(line)
            for r in by_plan[name]:
                if (r.get("walk") or {}).get("which"):
                    out.append(f"    seed {r['seed']}: {r['walk']['which']}")
        together = [r for name in walking if name in EXPLORING for r in by_plan[name]]
        if together:
            total, steps, rate = pooled_reversals(together)
            pooled_ok = rate <= REVERSALS_PER_100
            reversal_ok &= pooled_ok
            out.append(f"THE EXPLORING PLANS TOGETHER (build step 3.2): {total} reversals in {steps} steps ({rate:.2f} per 100 "
                       f"steps; bound {REVERSALS_PER_100}) -> {'OK' if pooled_ok else 'OVER THE BOUND'}")
    # (build step 3.2, the step-3.1 review's finding 2: "the reversal metric cannot see laps") LAPS and the walks against
    # the shortest known ways, per run; and (its finding 4) what the walk did after a target chosen on the move
    lap_ok = True
    if walking:
        out += ["", f"---- LAPS AND THE SHORTEST WAY (build step 3.2): per run, laps (back on a tile {LAPS_SPAN} steps later, "
                    f"nothing new between) and the steps walked to each target beyond the shortest way the memory knew "
                    f"(live_step3.lap_report); bound {LAP_SWEEP_BOUNDS} per run on {LAPPED} (the others reported) ----"]
        for name in walking:
            line, ok = lap_line(name, by_plan[name], name in LAPPED)
            lap_ok &= ok
            out.append(line)
            for r in by_plan[name]:
                laps = r.get("laps") or {}
                if laps.get("which") or (laps.get("worst") or 0) > 0 or laps.get("ring_which"):
                    out.append(f"    seed {r['seed']}: laps {laps.get('which')}; rings {laps.get('ring_which')}; the worst walk "
                               f"(map, kind, from, to, walked, shortest) {laps.get('worst_walk')}")
        pooled_rings = sum((r.get("laps") or {}).get("lap_rings") or 0 for name in walking if name in LAPPED for r in by_plan[name])
        all_rings = sum((r.get("laps") or {}).get("rings") or 0 for name in walking if name in LAPPED for r in by_plan[name])
        rings_ok = pooled_rings <= LAPS_REAL_RINGS
        lap_ok &= rings_ok
        out.append(f"LAP RINGS OVER THE LAPPED PLANS TOGETHER (the step-4 verifier's round: a ring with a leg walked beyond the "
                   f"shortest way to its own target): {pooled_rings} (bound {LAPS_REAL_RINGS}; at most "
                   f"{LAP_SWEEP_BOUNDS['lap_rings']} a run); RINGS of any kind {all_rings} (an excursion, every leg the shortest "
                   f"way to its own target, reported) -> {'OK' if rings_ok else 'OVER THE BOUND'}")
        chosen, kept, back = kept_heading([r for name in walking if name in LAPPED for r in by_plan[name]])
        out.append(f"TARGETS CHOSEN ON THE MOVE (finding 4), the lapped plans: {chosen}; the walk kept its heading after {kept} "
                   f"({100.0 * kept / chosen if chosen else 0:.0f}%), turned straight back after {back} (a dead end: everything "
                   f"ahead seen, the way out behind); per plan "
                   + "; ".join(f"{name} {kept_heading(by_plan[name])}" for name in walking if name in LAPPED))
    # (the step-4 verifier's round, its FAILURE: "Step 3.2 finding 4 ... is NOT fixed") THE CHURN per lapped plan, bounded
    churn_all_ok = True
    if walking:
        out += ["", f"---- CHURN (the step-4 verifier's round, finding 4): per lapped plan over its seeds together "
                    f"(live_step3.churn); bound {CHURN_SWEEP_BOUNDS} per plan ----"]
        for name in walking:
            if name not in LAPPED:
                continue
            cells = churn_cells(by_plan[name])
            ok = churn_ok(cells)
            churn_all_ok &= ok
            out.append(f"{name}: {churn_text(cells)} -> {'OK' if ok else 'OVER THE BOUND'}")
        if "SCENE-EXPLORE" in by_plan:
            # (the step-4 verifier's weak proof) SCENE-EXPLORE's reversals and journeys, bounded now
            total, steps, rate = pooled_reversals(by_plan["SCENE-EXPLORE"])
            cells = churn_cells(by_plan["SCENE-EXPLORE"])
            ok = rate <= SCENE_EXPLORE_REVERSALS_PER_100 and cells["journey_share"] <= SCENE_EXPLORE_JOURNEY_SHARE
            churn_all_ok &= ok
            out.append(f"SCENE-EXPLORE (the step-4 verifier's weak proof: 'reported, not graded'): {total} reversals in {steps} "
                       f"steps ({rate:.2f} per 100; bound {SCENE_EXPLORE_REVERSALS_PER_100}), every journey {cells['jall_excess']} "
                       f"beyond of {cells['jall_walked']} ({cells['journey_share']}; bound {SCENE_EXPLORE_JOURNEY_SHARE}) -> "
                       f"{'OK' if ok else 'OVER THE BOUND'}")
        lap_ok &= churn_all_ok
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
                pooled = 100.0 * totals[0] / totals[1] if totals[1] else 0.0
                held = (sum(broken) >= min(FINDING2_PLANS_OVER, len(plans)) and pooled > REVERSALS_PER_100 and walked > 0
                        and real_walked == 0)
                revert_ok &= held
                out.append(f"FINDING-2 A/B, the exploring plans, seeds {seeds[0]}-{seeds[-1]}: REVERTED {totals[0]} reversals in "
                           f"{totals[1]} steps ({pooled:.2f} per 100, bound {REVERSALS_PER_100}), {walked} stale targets walked "
                           f"onto; REAL {totals[2]} in {totals[3]}, {real_walked} walked onto; plans with a run over "
                           f"{REVERSALS_PER_RUN} when reverted: {sum(broken)} of {len(plans)} (predicted >= {FINDING2_PLANS_OVER}) "
                           f"-> the prediction {'HELD' if held else 'FAILED'}")
            elif label == "LAPS":
                over = sum(1 for r in rows if not lap_run_ok(r))
                for name in plans:
                    mine = [r for r in rows if r["name"] == name]
                    out.append(f"    REVERTED {lap_line(name, mine, True)[0]}")
                    out.append(f"    REAL     {lap_line(name, by_plan.get(name, []), True)[0]}")
                beyond = sum((r.get("laps") or {}).get("excess") or 0 for r in rows)
                real_beyond = sum((r.get("laps") or {}).get("excess") or 0 for name in plans for r in by_plan.get(name, []))
                real_over = sum(1 for name in plans for r in by_plan.get(name, []) if not lap_run_ok(r))
                # (the step-3.2 verifier's round) RINGS: the lap check that sees a round walked whatever it showed; (the step-4
                # verifier's round) LAP rings: a ring with a leg walked beyond the shortest way to its own target
                ringed = sum(1 for r in rows if ((r.get("laps") or {}).get("lap_rings") or 0) > 0)
                ring_total = sum((r.get("laps") or {}).get("lap_rings") or 0 for r in rows)
                real_ringed = sum(1 for name in plans for r in by_plan.get(name, []) if ((r.get("laps") or {}).get("lap_rings") or 0) > 0)
                nothing_new = sum((r.get("laps") or {}).get("laps") or 0 for r in rows)
                jx = sum((r.get("laps") or {}).get("jall_excess") or 0 for r in rows)
                real_jx = sum((r.get("laps") or {}).get("jall_excess") or 0 for name in plans for r in by_plan.get(name, []))
                real_rings = sum((r.get("laps") or {}).get("lap_rings") or 0 for name in plans for r in by_plan.get(name, []))
                held = (beyond > real_beyond and over >= LAPS_REVERT_OVER and real_over == 0 and ring_total >= LAPS_REVERT_RINGS
                        and ringed >= LAPS_REVERT_RINGED and real_rings <= LAPS_REAL_RINGS and jx > real_jx)
                revert_ok &= held
                out.append(f"LAPS A/B, {list(plans)}, seeds {seeds[0]}-{seeds[-1]}: steps beyond the shortest known ways REVERTED "
                           f"{beyond}, REAL {real_beyond}; LAP RINGS (a ring with a leg walked beyond the shortest way to its own "
                           f"target) REVERTED {ring_total} in {ringed} runs (predicted >= {LAPS_REVERT_RINGS} in >= "
                           f"{LAPS_REVERT_RINGED} runs), REAL {real_rings} in {real_ringed} runs (predicted <= {LAPS_REAL_RINGS}); "
                           f"laps with nothing new between REVERTED {nothing_new} (reported: a round walked shows new tiles); EVERY "
                           f"JOURNEY's steps beyond REVERTED {jx}, REAL {real_jx} (predicted more reverted); runs over "
                           f"{LAP_SWEEP_BOUNDS} REVERTED {over} of {len(rows)} (predicted >= {LAPS_REVERT_OVER}), REAL {real_over} -> "
                           f"the prediction {'HELD' if held else 'FAILED'}")
            elif label == "CHURN":
                for name in plans:
                    out.append(f"    REVERTED {name}: {churn_text(churn_cells([r for r in rows if r['name'] == name]))}")
                    out.append(f"    REAL     {name}: {churn_text(churn_cells(by_plan.get(name, [])))}")
                rev = churn_cells(rows)
                real = churn_cells([r for name in plans for r in by_plan.get(name, [])])
                plans_over = sum(1 for name in plans if not churn_ok(churn_cells([r for r in rows if r["name"] == name])))
                held = (rev["decisions"] >= CHURN_REVERT_DECISIONS * real["decisions"] and rev["ones"] >= CHURN_REVERT_ONES * real["ones"]
                        and plans_over == len(plans) and real["steps"] <= CHURN_COST_STEPS * rev["steps"]
                        and real["journey_share"] <= rev["journey_share"] + CHURN_COST_SHARE)
                revert_ok &= held
                reach = sorted(r["seed"] for r in rows if r["name"] == "SCENE-EXPLORE" and r.get("map") == [0, 16])
                real_reach = sorted(r["seed"] for r in by_plan.get("SCENE-EXPLORE", []) if r.get("map") == [0, 16])
                out.append(f"    SCENE-EXPLORE reached ROUTE101 (reported): REVERTED on seeds {reach}, REAL on seeds {real_reach}")
                out.append(f"CHURN A/B, {list(plans)}, seeds {seeds[0]}-{seeds[-1]}: DECISIONS REVERTED {rev['decisions']} "
                           f"({rev['on_the_move']} on the move), REAL {real['decisions']} ({real['on_the_move']} on the move, "
                           f"{real['carried']} places carried on) (predicted >= {CHURN_REVERT_DECISIONS} x); ONE-STEP WALKS "
                           f"REVERTED {rev['ones']} of {rev['walks']}, REAL {real['ones']} of {real['walks']} (predicted >= "
                           f"{CHURN_REVERT_ONES} x); plans over the bounds when reverted {plans_over} of {len(plans)} (predicted "
                           f"all); THE VISIBLE COST: steps REVERTED {rev['steps']}, REAL {real['steps']} (predicted <= "
                           f"{CHURN_COST_STEPS} x); every journey's share beyond REVERTED {rev['journey_share']} ({rev['jall_excess']} "
                           f"of {rev['jall_walked']}), REAL {real['journey_share']} ({real['jall_excess']} of {real['jall_walked']}) "
                           f"(predicted <= + {CHURN_COST_SHARE}) -> the prediction {'HELD' if held else 'FAILED'}")
            elif label == "WHIM":
                mine, real = kept_heading(rows), kept_heading([r for name in plans for r in by_plan.get(name, [])])
                share, real_share = (mine[1] / mine[0] if mine[0] else 0.0), (real[1] / real[0] if real[0] else 0.0)
                rev_rev, real_rev = pooled_reversals(rows), pooled_reversals([r for name in plans for r in by_plan.get(name, [])])
                held = real_share - share >= WHIM_REVERT_DROP
                revert_ok &= held
                for name in plans:
                    out.append(f"    REVERTED {name}: chosen on the move, kept the heading, straight back "
                               f"{kept_heading([r for r in rows if r['name'] == name])}; REAL {kept_heading(by_plan.get(name, []))}")
                out.append(f"WHIM A/B, {list(plans)}, seeds {seeds[0]}-{seeds[-1]}: after a target chosen on the move the walk kept "
                           f"its heading REVERTED {mine[1]} of {mine[0]} ({100 * share:.0f}%), REAL {real[1]} of {real[0]} "
                           f"({100 * real_share:.0f}%; predicted at least {100 * WHIM_REVERT_DROP:.0f} points more); reversals "
                           f"REVERTED {rev_rev[0]} in {rev_rev[1]} steps, REAL {real_rev[0]} in {real_rev[1]} (reported) -> the "
                           f"prediction {'HELD' if held else 'FAILED'}")
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
            # (build step 3.2) a target chosen on the move now keeps its heading, so after the twin's first push-back the
            # explorer may go for the SAME target again (2 seeds of the development sweep: (10, -4) twice, given up by the
            # per-target rule, its tile walled): per seed at least one target of its own, over the seeds at least two
            scene_ok = all(r.get("twin") is not None and twin_ok(r["twin"]) for r in rows) \
                and all(len((r.get("twin") or {}).get("targets", [])) >= 1 for r in rows) and len(targets) >= 2 \
                and all(((r.get("twin") or {}).get("segments") or [0])[0] >= 2 for r in rows)
            segments = [(r["seed"], (r.get("twin") or {}).get("segments")) for r in rows]
            ends = [(r["seed"], r.get("map"), r.get("var_town"), str(r.get("reason", ""))[:24]) for r in rows]
            reached = sum(1 for r in rows if r.get("map") == [0, 16])
            out.append(f"SCENE-EXPLORE (the EXPLORER's own targets, to its own end): {len(sequences)} different target sequences in "
                       f"{len(rows)} seeds; {len(targets)} different targets the twin stopped over the seeds ({sorted(targets)}); "
                       f"the twin's push-backs per seed, before any news and between news {segments}; every seed: sent back "
                       f"2..{TWIN_SCENES_IN_ALL} times before any news, every tile she began on then given up and not stepped on "
                       f"until news, at most once more after each news, >= 1 target of its own stopped (>= 2 different over the "
                       f"seeds): {scene_ok}")
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
    verdict = total_ok == len(results) and separated and reversal_ok and revert_ok and scene_ok and flee_ok and lap_ok
    out += ["", f"{total_ok} of {len(results)} runs as intended; reversal bounds met: {reversal_ok}; lap bounds met: {lap_ok}; "
                f"reverts as predicted: "
                f"{revert_ok if not args.no_reverts else 'not run'}; scenes: {scene_ok}; ROUTE's flee: {flee_ok}; "
                f"{time.time() - began:.0f} s of wall clock with {args.workers} workers", f"OVERALL: {'PASS' if verdict else 'FAIL'}"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    held_out = "" if args.first_seed == 1 else f"-SEEDS{seeds[0]}-{seeds[-1]}"
    path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-step3-RATE{held_out}{args.tag}.txt"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(line for line in out if not line.startswith("    ")))
    print(f"evidence: {path.relative_to(REPO)}")
    return 0 if verdict else 1


def reversal_line(name: str, rows: list[dict], bounded: bool) -> tuple[str, bool]:
    """One plan's reversals over its seeds against the per-run bound (`REVERSALS_PER_RUN`); its rate per 100 steps is
    reported (build step 3.2: the per-100 bound is over the exploring plans together, `pooled_reversals`)."""
    counts = [(r.get("walk") or {}).get("reversals") for r in rows]
    steps = sum((r.get("walk") or {}).get("steps") or 0 for r in rows)
    total = sum(c or 0 for c in counts)
    rate = 100.0 * total / steps if steps else 0.0
    walked = sum(r.get("walked_stale") or 0 for r in rows)
    ok = (not bounded) or all(isinstance(c, int) and c <= REVERSALS_PER_RUN for c in counts)
    return (f"{name}: {total} reversals in {steps} steps over {len(rows)} seeds ({rate:.2f} per 100 steps); per seed {counts}; "
            f"stale walked onto {walked}{'' if bounded else ' (reported, not bounded)'} -> {'OK' if ok else 'OVER THE BOUND'}", ok)


def pooled_reversals(rows: list[dict]) -> tuple[int, int, float]:
    """(build step 3.2) Reversals and steps over every run of `rows` together, and the rate per 100 steps."""
    total = sum((r.get("walk") or {}).get("reversals") or 0 for r in rows)
    steps = sum((r.get("walk") or {}).get("steps") or 0 for r in rows)
    return total, steps, (100.0 * total / steps if steps else 0.0)


def lap_line(name: str, rows: list[dict], bounded: bool) -> tuple[str, bool]:
    """(build step 3.2) One plan's laps and walks against the shortest known ways, seed by seed, against
    `LAP_SWEEP_BOUNDS` per run (every run graded at least one walk) when `bounded`."""
    cells = [(r["seed"], (r.get("laps") or {}).get("laps"), (r.get("laps") or {}).get("excess"), (r.get("laps") or {}).get("worst"),
              (r.get("laps") or {}).get("rings"), (r.get("laps") or {}).get("lap_rings")) for r in rows]
    ok = (not bounded) or all(lap_run_ok(r) for r in rows)
    total = sum(c[2] or 0 for c in cells)
    walked = sum((r.get("laps") or {}).get("walked") or 0 for r in rows)
    jx = [((r.get("laps") or {}).get("jall_excess") or 0, (r.get("laps") or {}).get("jall_walked") or 0) for r in rows]
    return (f"{name}: laps {sum(c[1] or 0 for c in cells)}, RINGS {sum(c[4] or 0 for c in cells)} (LAP rings "
            f"{sum(c[5] or 0 for c in cells)}), {total} steps beyond the shortest known ways over {walked} walked (the worst "
            f"target {max((c[3] or 0 for c in cells), default=0)}); EVERY JOURNEY {sum(j[0] for j in jx)} steps beyond over "
            f"{sum(j[1] for j in jx)} walked (bounded per plan in CHURN); per seed (seed, laps, beyond, worst, rings, lap rings) "
            f"{cells}{'' if bounded else ' (reported, not bounded)'} -> {'OK' if ok else 'OVER THE BOUND'}", ok)


def kept_heading(rows: list[dict]) -> tuple[int, int, int]:
    """(build step 3.2) Over `rows`: targets chosen on the move, how many the walk followed in the same heading, how many
    straight back (`live_step3.choices_on_the_move`)."""
    moves = [r.get("moves") or {} for r in rows]
    return (sum(m.get("chosen") or 0 for m in moves), sum(m.get("on") or 0 for m in moves), sum(m.get("back") or 0 for m in moves))


if __name__ == "__main__":
    sys.exit(main())
