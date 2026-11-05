"""THE GRADED NEW GAME CHAIN HELD-OUT (USER RULING 55: after practising from saves, the AI passes a NEW GAME test so that
what it learned connects). Build spec `PROJECT KNOWLEDGE/ai-research-notes/2026-11-05-LIVE-CHAIN-BUILD-SPEC.md` (written in
the session scratch as s53/chainheld/SPEC.md, with its adversarial critique CH-01..CH-18 and N1-N7 applied or rebutted in
the build report). TEST SIDE: the AI never imports this module (ImportTests).

    py -3.12 ai_player/gates/live_chain.py bounds (--run ch5 | --to ID [--chains 3|6] [--leg-frames L1=F,...])
        print the BOUNDS TEXT, the legs, the registered numbers (without the text) and both sha256s (read only)
    py -3.12 ai_player/gates/live_chain.py register --run ch5 [--note-file F]
        pre-register GRADED_RUNS["ch5"]'s seeds with registered_numbers()'s sha256 (BEFORE any run; commit and push it)
    py -3.12 ai_player/gates/live_chain.py run --purpose graded --run ch5 --out DIR
    py -3.12 ai_player/gates/live_chain.py run --purpose development --first-seed N --to ID --prediction-file F --out DIR
            [--chains 3|6] [--leg-frames L1=F[,L2=F...]] [--build-root DIR]
        exit 0 = PASS (graded) / ran (development), 1 = FAIL, 2 = refused before any leg, 3 = ABORTED by the harness (disk)
    py -3.12 ai_player/gates/live_chain.py grade DIR      offline re-grade of a batch's rows (no ledger write)
    py -3.12 ai_player/gates/live_chain.py read RUN_DIR [--truth]
        one leg folder, READ ONLY: its log counts, its memory line, its world.jsonl streamed (never kept, never deleted)
    `child JOB.json` is the internal entry of one chain's process.

WHAT IT IS. Chains of LEGS: each chain starts from a REAL New Game and plays one leg per chapter, each leg through the real
launcher (`live_step5.run_arm`: the purity gate on every launch), from the save state AND the world memory the previous leg
left. A leg targets its chapter's end milestone (`legs_of`, derived from `knowledge/milestones.json`); the last targets
`--to`. What a leg reached is read from the GAME (the harness's `truth` on the state it left, at the save-block numbers
the milestones name), freshness-checked by `L5.THIS_RUN`. A chain that misses STOPS: its later legs are NOT RUN, each with
a row that says why. Everything the batch is graded by (BOUNDS_TEXT, every constant, the legs and their proofs, the
milestones' sha256, the AI code's sha256 and the grader files' sha256) is hashed into the ledger registration, so
`ledger.begin` refuses a graded run on other numbers or code. The disk rule is live_ki128's section 6, per leg.

KNOWN LIMITS (said, not hidden; also in the evidence): each leg is its own launcher session, so the goal manager's in-run
memory starts again at every leg and the HARNESS names each leg's target (critic CH-18: this tests the game state and the
world memory carried across chapters, NOT the AI moving from one chapter to the next in one process; the rejected
alternative, one process to --to, would be about 2.76 M frames and 3 h a chain); the legs hand the game over by savestate,
not through the game's own save (USER RULING 51's saving is not part of this test); `live_step5.run_arm` reads the whole
action log into memory (the 2 GB-world churn runs of 2026-10-30, profiles ai-ch3-probe-1/2, had actions.jsonl of 12.97 MB
and 14.61 MB and logs under 1 MB, so this is megabytes, not gigabytes); the world cap is per leg, and later chapters'
snapshot lines are larger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import ledger  # noqa: E402
from ai_player.gates.grader_checks import (  # noqa: E402
    AI, GAME, GRADED, HARNESS, PASS, REPORTED, Check, status_of, verdict as typed_verdict,
)
# (spec D7) live_ki128's readers are imported, not copied: its 55 tests cover them, and it is in GRADER_FILES
from ai_player.gates.live_ki128 import (  # noqa: E402
    ai_code_sha256, file_sha256, free_gb, kill_descendants, measure_then_delete, text_sha256,
)
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_CLOCK, ENV_PERSONALITY, ENV_SEED, ENV_STARTER, ENV_TARGET, ENV_WORLD,
)

GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
FAMILY = "story"
DRIVER = "live_chain"
SPEC = "PROJECT KNOWLEDGE/ai-research-notes/2026-11-05-LIVE-CHAIN-BUILD-SPEC.md"

# ====================================================================== the registered constants (section 3 and 5)
#: (pair, personality, starter): one chain per pair and seed
PAIRS = (("S", "Story", "TREECKO"), ("C", "Catcher", "TORCHIC"), ("T", "Trainer", "MUDKIP"))
#: (pair, seed offset) in launch order: one chain of each pair in the first wave
JOB_ORDER = (("S", 0), ("C", 2), ("T", 4), ("S", 1), ("C", 3), ("T", 5))
#: development `--chains 3` only (its seed range is first..first+2, critic N3)
JOB_ORDER_3 = (("S", 0), ("C", 1), ("T", 2))
#: one row per graded registration (seeds 6201-6206 checked unused in every ledger on 2026-11-05)
GRADED_RUNS = {"ch5": {"seeds": (6201, 6206), "to": "ch5_rival_meet"}}
#: a chapter needs its OWN registered budget (adding one changes the grader hash, so a new registration)
FRAMES_BY_CHAPTER = {1: 330000, 2: 330000, 3: 600000, 4: 900000, 5: 600000}
WALL = 3600.0
PARALLEL = 3
STAGGER_SECONDS = 15
#: a pre-registered PRIOR (critic CH-16), not a measured rate: 0 unbroken New Game -> chapter 5 chains have run on one code
#: version, and the chains come in pairs (two seeds per personality and starter), so the binomial power of "at least 5 of 6"
#: (0.97 at p 0.95, 0.89 at 0.90, 0.66 at 0.80, 0.11 at 0.50) assumes independent chains it does not have
REACH_MIN = 5
#: every leg's world.jsonl UNDER this many bytes (decimal), measured before its deletion (the live_ki128 precedent)
WORLD_MAX_BYTES = 300_000_000
#: (critic CH-02) GRADED by the spec's D2; the known, unfixed Route 116 after-battle churn (774 MB in 200,000 frames) fails
#: it, so the lead rules on this ONE word before registering (REPORTED: the cap is printed and never counts, and a churn leg
#: no longer stops its chain)
WORLD_SIZE_KIND = GRADED
#: the disk guard during the batch (a leg past it has its launcher killed; free space under GUARD_FREE_GB ABORTS the batch)
GUARD_WORLD_BYTES = 1_500_000_000
GUARD_FREE_GB = 30.0
FREE_MIN_GB = 40.0
#: `live_step5.run_arm`'s own margin over the wall clock, and `truth_of`'s timeout (two truth reads a leg)
LEG_MARGIN_SECONDS = 300
TRUTH_SECONDS = 600
PROFILE_PREFIX = "ai-livechain-"
#: `live_step5.PROFILE`'s default: the profile `run_arm` writes when the global is not re-pointed
MAIN_PROFILE = "ai-step5-play"
#: the purity checks of `live_step2.check_purity` that COUNT (L5.PURITY_ENDED is reported only: a leg may end on its budget)
PURITY_IDS = ("L5.PURITY_GATE", "L5.PURITY_CLEAN", "L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PURITY_BREACHES",
              "L5.PURITY_PACKAGE")
#: the environment each leg gets (`live_step2.clean_env` strips the caller's AI_PLAYER_*); nothing else, no fault switch
ENV_KEYS_FIRST = tuple(sorted((ENV_BRAIN, ENV_SEED, ENV_PERSONALITY, ENV_TARGET, ENV_CLOCK, ENV_STARTER)))
ENV_KEYS_LATER = tuple(sorted((ENV_BRAIN, ENV_SEED, ENV_PERSONALITY, ENV_TARGET, ENV_CLOCK, ENV_WORLD)))
#: where the game sets a target's proof (pinned decomp 731ad5b), printed beside its leg (critic CH-09)
PROOF_NOTES = {
    "ch5_rival_meet": "the flag and VAR 8 are set together when the rival is met in Rustboro (RustboroCity/scripts.inc:740-741 "
                      "and :808-809); on Route 104 the flag is set at Route104/scripts.inc:99 and :184 and VAR 8 at :50; MR. "
                      "BRINEY's sail sets VAR 8 alone (Route104_MrBrineysHouse/scripts.inc:78), so the FLAG is what tells a "
                      "rival meeting: the proof means 'met the rival in Rustboro or on Route 104'",
}
#: the files that grade the batch, hashed into the registration (critic CH-08: the framework's party and memory decoders
#: decide LC.STARTER and every truth read, and the plugin is the hook the AI plays through)
GRADER_FILES = ("ai_player/gates/live_chain.py", "ai_player/gates/live_ki128.py", "ai_player/gates/live_step5.py",
                "ai_player/gates/live_step2.py", "ai_player/gates/grader_checks.py", "ai_player/gates/play_harness.py",
                "ai_player/gates/hands_harness.py", "ai_player/gates/probe_eyes.py", "ai_player/gates/probe_presses.py",
                "ai_player/gates/rate_step5.py", "ai_player/gates/provenance.py", "ai_player/gates/ledger.py",
                "ai_player/gates/fixtures/item_flags.json", "ai_player/gates/b1_debt.json",
                "ai_player/gates/grader_waivers.json", "sandbox-pokebot/modules/pokemon_party.py",
                "sandbox-pokebot/modules/memory.py", "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py")
MILESTONES = "ai_player/knowledge/milestones.json"
#: (critic CH-11) the graded check that reads an AI input, declared: the only record that the AI LOADED the carried memory
AI_INPUT_DEBT = {
    "LC.MEMORY": {"ai_input": "'[AI-WORLD] memory from ...' line in ai_player.log",
                  "plan": "critic CH-11: no game or harness record shows that the AI loaded the memory it was handed; its "
                          "own line names the file and five counts, and the counts are checked against the kept line the "
                          "HARNESS wrote, so an amnesiac leg or a wrong memory fails"},
}
STOP_FILE = "STOP.txt"
ABORT_FILE = "ABORT.txt"
RAN = ("RAN", "SALVAGED", "ERROR")  # a leg that was (or may have been) launched: every check samples it


class Refusal(Exception):
    """A batch, a leg list or a chain the driver refuses: the message says why."""


def repo_root() -> Path:
    """REPO, read at call time (the mutant tests load a mutated copy and rebind it)."""
    return REPO


def chain_watchdog_seconds(legs: list[dict]) -> int:
    """A chain child alive past this is killed and salvaged: each leg's wall plus run_arm's margin plus two truth reads,
    plus 300 s (5 legs of 3,600 s: 25,800 s)."""
    return int(sum(leg["wall"] + LEG_MARGIN_SECONDS + 2 * TRUTH_SECONDS for leg in legs) + 300)


def reach_min_of(chains: int) -> int:
    """At least REACH_MIN of 6 (graded); a development batch of 3 allows one miss (2 of 3)."""
    return REACH_MIN if chains == 6 else chains - 1


# ====================================================================== the legs (pure)
def load_milestones(repo: Path | None = None) -> dict:
    return json.loads(((repo or REPO) / MILESTONES).read_text(encoding="utf-8"))


def legs_of(to: str | None, data: dict, frames_by_chapter: dict[int, int] | None = None) -> list[dict]:
    """One leg per chapter up to `to`'s (spec section 2), RAISING `Refusal` for an unknown, optional or waypoint target, a
    chapter with no end milestone or no budget, an empty proof, or milestones whose chapters go backwards in file order.
    A chapter's leg ends at its LAST milestone in file order that is neither optional nor a waypoint; the last leg's is `to`."""
    budgets = FRAMES_BY_CHAPTER if frames_by_chapter is None else frames_by_chapter
    ms = list(data.get("milestones") or [])
    if any(not isinstance(m.get("chapter"), int) for m in ms):
        raise Refusal("a milestone of milestones.json has no chapter number")
    for a, b in zip(ms, ms[1:]):
        if b["chapter"] < a["chapter"]:
            raise Refusal(f"milestones.json's chapters go BACKWARDS in file order: {a['id']} (chapter {a['chapter']}) "
                          f"before {b['id']} (chapter {b['chapter']})")
    target = next((m for m in ms if m.get("id") == to), None)
    if target is None:
        raise Refusal(f"--to {to!r} is no milestone of milestones.json")
    if target.get("optional"):
        raise Refusal(f"--to {to} is OPTIONAL: a run may never need it, so no chain may end on it")
    if target.get("waypoint") is not None:
        raise Refusal(f"--to {to} is a WAYPOINT ({target['waypoint']}): its proof is a later milestone's, so the AI stops "
                      f"on its map while the game's proof is still false")
    legs = []
    for chapter in range(1, target["chapter"] + 1):
        if chapter == target["chapter"]:
            end = target
        else:
            ends = [m for m in ms if m["chapter"] == chapter and not m.get("optional") and m.get("waypoint") is None]
            if not ends:
                raise Refusal(f"chapter {chapter} has no milestone that is neither optional nor a waypoint: no leg ends it")
            end = ends[-1]
        if chapter not in budgets:
            raise Refusal(f"chapter {chapter} has no registered frame budget (FRAMES_BY_CHAPTER {sorted(budgets)}): a chapter "
                          f"needs its own, and adding one is a new registration")
        done = end.get("done") or {}
        proof = {"flags": {k: int(v) for k, v in (done.get("flags") or {}).items()},
                 "variables": {k: {"number": int(v["number"]), "at_least": int(v["at_least"])}
                               for k, v in (done.get("variables") or {}).items()},
                 "trainers": {k: int(v) for k, v in (done.get("trainers") or {}).items()}}
        if not (proof["flags"] or proof["variables"] or proof["trainers"]):
            raise Refusal(f"{end['id']}'s proof is EMPTY: an empty proof holds on any state")
        legs.append({"leg": f"L{chapter}", "chapter": chapter, "target": end["id"], "frames": int(budgets[chapter]),
                     "wall": WALL, "proof": proof})
    return legs


def parse_leg_frames(text: str | None, legs: list[dict]) -> dict[str, int]:
    """`L1=30000,L2=5000` -> {"L1": 30000, "L2": 5000}, RAISING `Refusal` on a leg not in `legs` or a budget under 1."""
    if not text:
        return {}
    names = {leg["leg"] for leg in legs}
    out: dict[str, int] = {}
    for part in text.split(","):
        name, _, value = part.strip().partition("=")
        if name not in names:
            raise Refusal(f"--leg-frames names {name!r}, not one of the legs {sorted(names)}")
        try:
            frames = int(value)
        except ValueError:
            raise Refusal(f"--leg-frames {part!r}: not a whole number of frames") from None
        if frames < 1:
            raise Refusal(f"--leg-frames {part!r}: a budget must be at least 1 frame")
        out[name] = frames
    return out


def proof_holds(marks: dict | None, proof: dict) -> dict:
    """Does the game's proof hold on a truth's marks? Every flag == 1, every `VAR_<name>` >= its at_least, every
    `TRAINER_<name>` == 1. A key the truth did NOT return is NOT held: it is listed as missing, never defaulted. An empty
    proof never holds."""
    marks = marks or {}
    values: dict[str, object] = {}
    missing: list[str] = []
    failing: list[str] = []

    def one(key: str, ok) -> None:
        value = marks.get(key)
        values[key] = value
        if value is None:
            missing.append(key)
        elif not ok(value):
            failing.append(key)

    for name in proof.get("flags") or {}:
        one(name, lambda v: v == 1)
    for name, info in (proof.get("variables") or {}).items():
        one(f"VAR_{name}", lambda v, need=info["at_least"]: isinstance(v, int) and v >= need)
    for name in proof.get("trainers") or {}:
        one(f"TRAINER_{name}", lambda v: v == 1)
    return {"held": bool(values) and not missing and not failing, "missing": missing, "failing": failing,
            "values": values}


def proof_text(proof: dict | None) -> str:
    if not proof:
        return "not read"
    if proof.get("unread"):
        return "UNREAD (no start truth)"
    return (f"{proof.get('values')}" + (f"; missing {proof['missing']}" if proof.get("missing") else "")
            + (f"; failing {proof['failing']}" if proof.get("failing") else ""))


def proof_line(leg: dict) -> str:
    """One leg's proof as the bounds text writes it: NAME (number) = 1 / VAR_NAME (number) >= n / TRAINER_NAME (number) = 1."""
    p = leg["proof"]
    parts = [f"{name} ({number}) = 1" for name, number in p["flags"].items()]
    parts += [f"VAR_{name} ({info['number']}) >= {info['at_least']}" for name, info in p["variables"].items()]
    parts += [f"TRAINER_{name} ({number}) = 1" for name, number in p["trainers"].items()]
    return ", ".join(parts)


# ====================================================================== chains, seeds, jobs
def jobs_of(first: int, chains: int = 6) -> list[dict]:
    order = JOB_ORDER if chains == 6 else JOB_ORDER_3 if chains == 3 else None
    if order is None:
        raise Refusal(f"--chains {chains}: 3 (development) or 6")
    pairs = {p[0]: p for p in PAIRS}
    return [{"chain": f"LC-{pair}-{first + off}", "pair": pair, "personality": pairs[pair][1], "starter": pairs[pair][2],
             "seed": first + off, "profile": f"{PROFILE_PREFIX}{first + off}"} for pair, off in order]


def seeds_of(first: int, chains: int) -> tuple[int, int]:
    return first, first + chains - 1


# ====================================================================== the bounds text (one generator)
def bounds_text(to: str, legs: list[dict], jobs: list[dict], reach_min: int) -> str:
    """BOUNDS_TEXT for these legs and jobs (graded and development use this one generator; hashed into the numbers)."""
    chains = len(jobs)
    first = min(j["seed"] for j in jobs)
    world_graded = WORLD_SIZE_KIND == GRADED
    leg_lines = []
    for leg in legs:
        note = PROOF_NOTES.get(leg["target"])
        leg_lines.append(f"  {leg['leg']} {leg['target']}, {leg['frames']} frames: {proof_line(leg)}"
                         + (f" ({note})" if note else ""))
    job_text = ", ".join(f"{j['personality']} {j['starter']} +{j['seed'] - first}" for j in jobs)
    world_rule = (f"LC.WORLD_SIZE: every leg that ran: its world.jsonl, measured before its deletion, is under {WORLD_MAX_BYTES} "
                  f"bytes (300 MB); if it grew between the first size and the deletion the larger is graded.")
    lines = [
        f"LIVE CHAIN GRADED HELD-OUT (USER RULING 55: the New Game test), build spec {SPEC} (with its critique CH-01..CH-18). "
        f"Driver ai_player/gates/live_chain.py.",
        "CODE: the AI's files (ai_player/ outside gates/ and evidence/, no *.md, no __pycache__; CRLF read as LF) are hashed "
        "into these numbers (ai_code_sha256), knowledge/milestones.json among them and also as milestones_sha256, as are the "
        "files that grade the batch (grader_files, the framework's party and memory decoders and the AI's plugin among them): "
        "a graded run on any other AI code, milestone data or grader is refused by ledger.begin. A graded run also needs HEAD "
        "to be origin/main after a fetch with no tracked file changed, and the build root to be the one the truth harness "
        "reads. The frozen-tree watch must see no change from the batch's start to its verdict.",
        f"TARGET {to}. LEGS, one per chapter, derived from milestones.json (each chapter before the target's: the LAST "
        f"milestone of the chapter in file order that is neither optional nor a waypoint; the target's chapter: the target), "
        f"each with its frame budget, a {WALL:g} s wall clock and the GAME's proof of its target (save block 1 at the numbers "
        f"named, read by the harness's truth on the state the leg left):",
        *leg_lines,
        f"CHAINS: {chains} on the registered seeds, one seed per chain for all its legs; in launch order (personality, starter, "
        f"seed offset): {job_text}; at most {PARALLEL} chains at once, {STAGGER_SECONDS} s apart; each chain in its own NEW "
        f"profile {PROFILE_PREFIX}<seed> under the build root (refused if it exists).",
        "EACH LEG: the real launcher through live_step5.run_arm, brain play, the chain's personality and seed, target the "
        "leg's; L1 from a REAL New Game (--fresh, the chain's starter); each later leg from the end state the previous leg "
        "left (--state) and the world memory it left (AI_PLAYER_WORLD = that leg's world.jsonl's LAST line, kept outside the "
        "repo; the AI reads only the last line), with the pages read in the earlier legs. The environment holds exactly "
        f"{', '.join(ENV_KEYS_FIRST)} (L1) or {', '.join(ENV_KEYS_LATER)} (later legs); no fault switch. Each leg is its own "
        "session: the game and the world memory are carried, the goal manager's in-run memory starts again, and the harness "
        "names each leg's target (the AI connecting one chapter to the next inside one process is NOT what this tests).",
        "A LEG REACHES its target iff its L5.THIS_RUN PASSES and every proof of its target holds on the state it left; a mark "
        "the truth did not return is not held. Every chain starts from a New Game, which holds none of the proofs, so the "
        "chain's claim is never vacuous; a leg whose target already held at its start (an earlier leg played past its own "
        "target) still REACHES and is marked ALREADY HELD. For a leg after the first, a start state the truth could not read "
        "is UNREAD, never 'not held' (its custody then fails).",
        f"A CHAIN CONTINUES after a leg iff (C1) the leg reached its target, (C2) every counting purity check of its launch "
        f"PASSED, (C3) its world.jsonl was measured{(' under ' + str(WORLD_MAX_BYTES) + ' bytes') if world_graded else ''} "
        f"and its last line parsed and was kept (a failed deletion is recorded and retried at the end, never a stop), (C4) "
        f"the disk guard did not kill it, (C5) its custody held, (C6) the frozen tree had not moved. Otherwise the chain "
        f"STOPS: it fails, and every later leg is NOT RUN (a row says so, with the reason) and is in no check's sample. A "
        f"CHAIN REACHES {to} iff every one of its legs ran and passed C1-C6, the last included.",
        f"DISK: refused under {FREE_MIN_GB:g} GB free on the build root's drive. During the batch a leg whose world.jsonl "
        f"(the newest run folder of its chain's profile) passes {GUARD_WORLD_BYTES} bytes has its launcher killed (recorded; "
        f"its chain stops); under {GUARD_FREE_GB:g} GB free the batch is ABORTED by the harness (every launcher killed, no "
        f"PASS or FAIL: a neighbour's disk use is not the AI's); a chain past its watchdog (each leg's wall + "
        f"{LEG_MARGIN_SECONDS} s + two {TRUTH_SECONDS} s truth reads, + 300 s) is killed and salvaged. After each leg, before "
        f"the next starts, its world.jsonl's size is recorded, it is streamed line by line (never a whole-file read), its "
        f"last line is written outside the repo, and it is DELETED.",
        "GRADED (every one must PASS; a VACUOUS check fails; no waivers):",
        f"LC.REACH: at least {reach_min} of the {chains} chains reach {to} (a pre-registered prior: it assumes independent "
        f"chains, and the chains come in pairs).",
        f"LC.PURITY: on every leg that ran, the counting purity checks of live_step2.check_purity ({', '.join(PURITY_IDS)}) "
        f"all PASS. L5.PURITY_ENDED is reported only.",
        "LC.THIS_RUN: every leg that ran: L5.THIS_RUN (live_step5.check_after_is_this_run) PASSES.",
        *([world_rule] if world_graded else []),
        "LC.CUSTODY: every registered chain's L1 ran, and every leg that ran started as above: L1 from --fresh with the "
        "chain's starter and no world memory or start state; each later leg from --state of the previous leg's end state, its "
        "start truth (frame, md5) equal to the previous leg's end truth, and an AI_PLAYER_WORLD file whose sha256 equals the "
        "previous leg's kept last line's; every leg's environment keys exactly the set above.",
        "LC.STARTER: every chain whose first leg left a party: its first Pokemon is the chain's registered starter, the "
        "player's own (OT).",
        "LC.MEMORY (reads the AI's log, declared as B1 debt): every leg that ran said '[AI-WORLD] memory from ...': L1 from "
        "nothing (a new memory); each later leg from the last snapshot of its AI_PLAYER_WORLD file, with its maps, tiles "
        "learned, warp links, connections and map changes equal to the counts of the kept last line.",
        "LC.FROZEN: the frozen-tree watch saw no change of the code under test from the batch's start to its verdict.",
        f"LC.LEFTOVER: no python process whose command line names {PROFILE_PREFIX} is left after the batch.",
        "REPORTED (information, never counted): LC.PROGRESS (per chain the legs reached; per leg real frames of the budget, "
        "seconds of the wall), LC.MULTICHOICE (per leg the LINES of ai_player.log saying 'an unexpected multichoice', by form, "
        "and every 'an unexpected <kind>' line by kind: lines, not events), LC.OUTCOME (the AI's exit claim beside the game's "
        "proof), LC.ENDED (who ended each leg, the harness's own record), LC.OPTIONAL (the optional milestones' proofs at "
        "each chain's last leg), LC.WORLD (bytes per leg and chain; deletions; leftovers), LC.PROFILES (each chain's run "
        "folders are its legs', and no run folder of this batch's arms anywhere else), LC.MAIN_PROFILE (ai-step5-play's run "
        "folders and its state file unchanged)"
        + ("" if world_graded else f", LC.WORLD_SIZE (the {WORLD_MAX_BYTES}-byte cap, information)") + ".",
        "VERDICT: PASS iff every GRADED check PASSES. Nothing is tuned to a grader (B1): a miss is reported, never re-run on "
        "new seeds.",
    ]
    return "\n".join(lines)


# ====================================================================== registration
def env_keys() -> dict:
    return {"L1": list(ENV_KEYS_FIRST), "later": list(ENV_KEYS_LATER)}


def registered_numbers(run: str | None, to: str, seeds: tuple[int, int], chains: int, legs: list[dict],
                       repo: Path | None = None, development: dict | None = None) -> dict:
    """Everything the batch is graded by (`ledger.numbers_sha256` of this is the registration's bounds field). A
    development batch adds {purpose, chains, leg_frames_override, prediction_sha256}: its ledger entry covers its
    prediction, registered before the runs."""
    repo = repo or REPO
    jobs = jobs_of(seeds[0], chains)
    reach_min = reach_min_of(chains)
    numbers = {"family": FAMILY, "driver": DRIVER, "run": run, "seeds": list(seeds), "to": to,
               "bounds_text": bounds_text(to, legs, jobs, reach_min),
               "legs": [{k: leg[k] for k in ("leg", "chapter", "target", "frames", "wall", "proof")} for leg in legs],
               "jobs": [{k: j[k] for k in ("chain", "pair", "personality", "starter", "seed")} for j in jobs],
               "parallel": PARALLEL, "stagger_seconds": STAGGER_SECONDS, "reach_min": reach_min, "chains": chains,
               "frames_by_chapter": {str(k): v for k, v in FRAMES_BY_CHAPTER.items()},
               "free_min_gb": FREE_MIN_GB, "world_max_bytes": WORLD_MAX_BYTES, "world_size_kind": WORLD_SIZE_KIND,
               "guard_world_bytes": GUARD_WORLD_BYTES, "guard_free_gb": GUARD_FREE_GB,
               "chain_watchdog_seconds": chain_watchdog_seconds(legs), "profile_prefix": PROFILE_PREFIX,
               "purity_ids": list(PURITY_IDS), "env_keys": env_keys(), "proof_notes": PROOF_NOTES,
               "milestones_sha256": text_sha256(repo / MILESTONES), "ai_code_sha256": ai_code_sha256(repo),
               "grader_files": {name: text_sha256(repo / name) for name in GRADER_FILES}}
    if development is not None:
        numbers.update({"purpose": "development", **development})
    return numbers


def register(seeds: tuple[int, int], numbers: dict, note: str = "", path: Path | None = None) -> dict:
    return ledger.register(FAMILY, DRIVER, seeds[0], seeds[1], ledger.numbers_sha256(numbers), note=note,
                           path=path or ledger.LEDGER)


def begin(purpose: str, seeds: tuple[int, int], numbers: dict, tree: str | None, note: str = "",
          path: Path | None = None) -> tuple[dict, list[str]]:
    return ledger.begin(FAMILY, DRIVER, purpose, seeds[0], seeds[1], ledger.numbers_sha256(numbers), tree, note=note,
                        path=path or ledger.LEDGER)


def seeds_named(first: int, last: int, path: Path | None = None) -> list[dict]:
    """Every ledger entry, of ANY family, whose range overlaps first..last."""
    return [e for e in ledger.load(path or ledger.LEDGER).get("entries", []) if e["first"] <= last and first <= e["last"]]


# ====================================================================== the readers (pure; unit-tested on planted files)
UNEXPECTED = re.compile(r"an unexpected (?P<kind>\S+)(?: (?P<form>on screen|while the person|in the battle))?")
MEMORY_LINE = re.compile(r"\[AI-WORLD\] memory from (?P<source>.+?): (?P<maps>\d+) maps \(")
MEMORY_COUNTS = re.compile(r", (?P<tiles>\d+) tiles learned, (?P<warps>\d+) warp links, (?P<connections>\d+) connections, "
                           r"(?P<transitions>\d+) map changes")
SNAPSHOT_SOURCE = "the last snapshot of "
NEW_MEMORY = "nothing (a new memory)"


def stream_world_tail(path: Path, keep: Path | None = None) -> dict:
    """ONE PASS over a world.jsonl, line by line, never a whole-file read: its size, its non-blank lines, the ones that do
    not parse, and its LAST non-blank line, byte for byte (written to `keep` when given): whether it parses, its sha256, its
    size and its counts (maps, tiles learned, warp links, connections, map changes: the five the AI says it loaded)."""
    size = path.stat().st_size
    lines = bad = 0
    last: bytes | None = None
    with open(path, "rb") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            lines += 1
            last = raw
            try:
                json.loads(raw)
            except ValueError:
                bad += 1
    out = {"bytes": size, "lines": lines, "bad_lines": bad, "last_ok": False, "last_sha256": None, "last_bytes": 0,
           "kept": None, "counts": None}
    if last is None:
        return out
    try:
        data = json.loads(last)
        ok = isinstance(data, dict)
    except ValueError:
        data, ok = None, False
    out.update({"last_ok": ok, "last_sha256": hashlib.sha256(last).hexdigest(), "last_bytes": len(last)})
    if ok:
        out["counts"] = {"maps": len(data.get("maps") or {}), "tiles": int(data.get("tiles_learned") or 0),
                         "warps": len(data.get("warps") or {}), "connections": len(data.get("connections") or []),
                         "transitions": len(data.get("transitions") or [])}
    if keep is not None:
        keep.parent.mkdir(parents=True, exist_ok=True)
        keep.write_bytes(last)
        out["kept"] = str(keep)
    return out


def parse_memory_line(line: str) -> dict | None:
    """The AI's '[AI-WORLD] memory from <source>: N maps (...), T tiles learned, W warp links, C connections, M map
    changes' -> {source, path (a snapshot's file, else None), counts}."""
    found = MEMORY_LINE.search(line)
    if not found:
        return None
    source = found["source"]
    counts = MEMORY_COUNTS.search(line, found.end())
    return {"source": source, "path": source[len(SNAPSHOT_SOURCE):] if source.startswith(SNAPSHOT_SOURCE) else None,
            "new": source == NEW_MEMORY,
            "counts": None if counts is None else {"maps": int(found["maps"]), "tiles": int(counts["tiles"]),
                                                   "warps": int(counts["warps"]),
                                                   "connections": int(counts["connections"]),
                                                   "transitions": int(counts["transitions"])},
            "line": line.strip()[:600]}


def log_counts(lines: Iterable[str]) -> dict:
    """The AI's log, line by line: every 'an unexpected <kind>' LINE by kind and by form (lines, not events: one stop may
    be said more than once), the multichoice lines, the first such line, and the FIRST memory line."""
    out: dict = {"lines": 0, "unexpected": {}, "forms": {}, "multichoice": 0, "first_unexpected": None, "memory": None}
    for line in lines:
        out["lines"] += 1
        found = UNEXPECTED.search(line)
        if found:
            kind = found["kind"]
            form = found["form"] or "other"
            out["unexpected"][kind] = out["unexpected"].get(kind, 0) + 1
            out["forms"][f"{kind} {form}"] = out["forms"].get(f"{kind} {form}", 0) + 1
            if kind == "multichoice":
                out["multichoice"] += 1
            if out["first_unexpected"] is None:
                out["first_unexpected"] = line.strip()[:300]
        if out["memory"] is None and "[AI-WORLD] memory from " in line:
            out["memory"] = parse_memory_line(line)
    return out


def read_log_counts(path: Path) -> dict | None:
    if not path.is_file():
        return None
    with open(path, encoding="utf-8", errors="replace") as handle:
        return log_counts(handle)


# ====================================================================== the rules (pure; unit-tested on planted rows)
def _status(row: dict, check_id: str) -> str | None:
    return next((c["status"] for c in row.get("checks") or [] if c["id"] == check_id), None)


def _norm(path) -> str | None:
    return None if path is None else os.path.normcase(os.path.abspath(str(path)))


def leg_reached(row: dict) -> tuple[bool, str]:
    """C1: L5.THIS_RUN PASS and the target's proof holds on the state the leg left."""
    this_run = _status(row, "L5.THIS_RUN")
    after = row.get("proof_after") or {}
    ok = this_run == PASS and bool(after.get("held"))
    return ok, (f"L5.THIS_RUN {this_run or 'MISSING'}; {row.get('target')}'s proof on the state it left "
                f"{'HOLDS' if after.get('held') else 'does NOT hold'} ({proof_text(after)})")


def custody_problems(row: dict, prev: dict | None, job: dict, index: int) -> list[str]:
    """Did this leg start from what the bounds say? (section 4, CUSTODY) Empty: it did."""
    problems: list[str] = []
    command = [str(c) for c in row.get("command") or []]
    env = row.get("env") or {}
    keys = tuple(sorted(row.get("env_keys") or []))
    if index == 0:
        if "--fresh" not in command:
            problems.append("L1 did not start with --fresh")
        if "--state" in command:
            problems.append("L1 started from --state")
        if row.get("world_in") is not None:
            problems.append(f"L1 was handed a world memory {row.get('world_in')}")
        if row.get("truth_before") is not None:
            problems.append("L1 has a start truth (a fresh boot has none)")
        if env.get(ENV_STARTER) != job.get("starter"):
            problems.append(f"L1's starter {env.get(ENV_STARTER)!r} is not the chain's {job.get('starter')!r}")
        if keys != ENV_KEYS_FIRST:
            problems.append(f"L1's environment keys {list(keys)} are not {list(ENV_KEYS_FIRST)}")
        return problems
    if prev is None:
        return [f"{row.get('leg')}: no row of the leg before it"]
    want = str(Path(prev["run_dir"]) / "end_state.ss1") if prev.get("run_dir") else None
    state = command[command.index("--state") + 1] if "--state" in command and command.index("--state") + 1 < len(command) \
        else None
    if "--fresh" in command:
        problems.append(f"{row['leg']} started with --fresh")
    if state is None or want is None or _norm(state) != _norm(want):
        problems.append(f"{row['leg']} started from --state {state}, not {prev.get('leg')}'s end state {want}")
    before, after = row.get("truth_before"), prev.get("truth_after") or {}
    if not before:
        problems.append(f"{row['leg']}'s start truth is UNREAD")
    elif after.get("state_md5") is None or (before.get("frame"), before.get("state_md5")) != (after.get("frame"),
                                                                                             after.get("state_md5")):
        problems.append(f"{row['leg']}'s start truth (frame {before.get('frame')}, md5 {before.get('state_md5')}) is not "
                        f"{prev.get('leg')}'s end truth (frame {after.get('frame')}, md5 {after.get('state_md5')})")
    if row.get("world_in_sha256") is None or row.get("world_in_sha256") != prev.get("kept_world_sha256"):
        problems.append(f"{row['leg']}'s AI_PLAYER_WORLD sha256 {row.get('world_in_sha256')} is not {prev.get('leg')}'s "
                        f"kept last line's {prev.get('kept_world_sha256')}")
    if _norm(row.get("world_in")) != _norm(prev.get("kept_world")):
        problems.append(f"{row['leg']}'s AI_PLAYER_WORLD {row.get('world_in')} is not {prev.get('leg')}'s kept last line "
                        f"{prev.get('kept_world')}")
    if keys != ENV_KEYS_LATER:
        problems.append(f"{row['leg']}'s environment keys {list(keys)} are not {list(ENV_KEYS_LATER)}")
    return problems


def continue_after(row: dict, stop_seen: bool) -> tuple[bool, str]:
    """THE CONTINUATION RULE (C1-C6, registered in the bounds text): (go on, why). The why names each failing condition
    with both values."""
    why: list[str] = []
    reached, reach_text = leg_reached(row)
    if not reached:
        why.append(f"C1 {row.get('target')} not reached: {reach_text}")
    statuses = {c["id"]: c["status"] for c in row.get("checks") or [] if c["id"] in PURITY_IDS}
    wrong = [f"{i} {statuses.get(i, 'MISSING')}" for i in PURITY_IDS if statuses.get(i) != PASS]
    if wrong:
        why.append(f"C2 purity not clean: {', '.join(wrong)}")
    size = (row.get("world_file") or {}).get("bytes")
    world = (row.get("measures") or {}).get("world") or {}
    if not isinstance(size, int):
        why.append("C3 its world.jsonl was not measured")
    elif WORLD_SIZE_KIND == GRADED and size >= WORLD_MAX_BYTES:
        why.append(f"C3 its world.jsonl was {size} bytes, not under {WORLD_MAX_BYTES}")
    if not world.get("last_ok"):
        why.append(f"C3 its world.jsonl's last line did not parse ({world.get('lines')} lines, {world.get('bad_lines')} bad)")
    elif not row.get("kept_world") or not Path(row["kept_world"]).is_file():
        why.append("C3 its last line was not kept")
    if row.get("guard_killed"):
        why.append(f"C4 the disk guard killed it ({(row.get('guard_killed') or {}).get('text')})")
    if row.get("custody"):
        why.append(f"C5 custody: {'; '.join(row['custody'])}")
    if stop_seen:
        why.append("C6 the code under test changed mid-batch (STOP.txt)")
    return not why, "; ".join(why) if why else "C1-C6 held"


def chain_reaches(chain: dict, legs_wanted: int) -> bool:
    """A chain REACHES --to iff every one of its legs RAN and passed C1-C6, the last included."""
    legs = chain.get("legs") or []
    return len(legs) == legs_wanted and legs_wanted > 0 and all(leg.get("status") == "RAN" and leg.get("continue")
                                                                for leg in legs)


def guard_decision(world_bytes: int | None, free: float | None) -> str | None:
    """The disk guard: "free" (under GUARD_FREE_GB free: the batch aborts), "world" (the leg's world.jsonl over
    GUARD_WORLD_BYTES: its launcher is killed), or None."""
    if free is not None and free < GUARD_FREE_GB:
        return "free"
    if world_bytes is not None and world_bytes > GUARD_WORLD_BYTES:
        return "world"
    return None


def newest_world(runs: Path) -> tuple[str | None, int | None]:
    """(the newest run folder's name, its world.jsonl's size): ONLY the newest folder (run_arm names them by time), so a
    world.jsonl whose deletion failed in an older folder cannot kill a healthy later leg. Every stat is OSError-safe: a file
    deleted between the listing and the stat reads None (critic CH-14)."""
    try:
        folders = sorted(p.name for p in runs.iterdir() if p.is_dir())
    except OSError:
        return None, None
    if not folders:
        return None, None
    try:
        return folders[-1], (runs / folders[-1] / "world.jsonl").stat().st_size
    except OSError:
        return folders[-1], None


def leg_of_folder(name: str | None, chain: str) -> str | None:
    """The leg ("L3") of a run folder named `<time>-<chain>-L3`, or None."""
    if not name or f"-{chain}-L" not in name:
        return None
    return name.rsplit("-", 1)[1]


# ====================================================================== the grader (pure; unit-tested on planted rows)
def _check(check_id: str, kind: str, ok: bool, n: int | None, floor: int | None, inputs: Iterable[str], text: str) -> Check:
    return Check(check_id, kind, status_of(ok, n, floor), n, floor, frozenset(inputs), f"{check_id}: {text}",
                 debt=AI_INPUT_DEBT)


def ran_legs(chains: list[dict]) -> list[tuple[dict, dict]]:
    return [(c, leg) for c in chains for leg in c.get("legs") or [] if leg.get("status") in RAN]


def _starter_ok(chain: dict) -> tuple[bool | None, str]:
    legs = chain.get("legs") or []
    first = legs[0] if legs else None
    after = (first or {}).get("truth_after") or {}
    party = after.get("party_exp") or []
    if not first or first.get("status") not in RAN or not party:
        return None, f"{chain.get('chain')}: no party"
    owner = {row[0]: row[1] for row in after.get("party_ot") or []}
    lead = party[0]
    ok = str(lead[1]).upper() == chain.get("starter") and owner.get(lead[0]) == after.get("player_tid") \
        and after.get("player_tid") is not None
    return ok, (f"{chain.get('chain')}: first {lead[1]} (PID {lead[0]}) OT {owner.get(lead[0])}, the player's "
                f"{after.get('player_tid')}; registered {chain.get('starter')}")


def memory_problems(chain: dict) -> tuple[int, list[str], list[str]]:
    """LC.MEMORY over one chain: (legs judged, problems, per-leg lines)."""
    judged, problems, lines = 0, [], []
    legs = chain.get("legs") or []
    for at, leg in enumerate(legs):
        if leg.get("status") not in RAN:
            continue
        said = ((leg.get("measures") or {}).get("log") or {}).get("memory")
        if not said:
            continue
        judged += 1
        name = f"{chain.get('chain')} {leg.get('leg')}"
        if at == 0:
            if not said.get("new"):
                problems.append(f"{name}: L1 said memory from {said.get('source')!r}, not {NEW_MEMORY!r}")
            lines.append(f"{name} from {said.get('source')}")
            continue
        prev = legs[at - 1]
        kept = ((prev.get("measures") or {}).get("world") or {}).get("counts")
        if _norm(said.get("path")) != _norm(leg.get("world_in")):
            problems.append(f"{name}: the memory said is from {said.get('source')!r}, not its AI_PLAYER_WORLD "
                            f"{leg.get('world_in')}")
        if kept is None or said.get("counts") != kept:
            problems.append(f"{name}: the AI's counts {said.get('counts')} are not the kept line's {kept}")
        lines.append(f"{name} {said.get('counts')} vs kept {kept}")
    return judged, problems, lines


def grade_batch(chains: list[dict], jobs: list[dict], legs_wanted: int, reach_min: int,
                frozen: tuple[bool, str] | None = None, leftover: list[str] | None = None,
                reported: dict | None = None) -> list[Check]:
    """THE GRADED BOUNDS of the bounds text over a batch's chain rows (each with every leg's row, NOT RUN ones included).
    `jobs` are the REGISTERED chains; `reported` carries the harness's own records for the reported checks (world files
    left after the sweep, the profiles' listings, the main profile, the most chains at once). Every check quotes both
    values."""
    reported = reported or {}
    checks: list[Check] = []
    expected = len(jobs)
    by_name = {c.get("chain"): c for c in chains}
    ran = ran_legs(chains)
    floor = max(len(ran), expected)
    # LC.REACH
    reached = [c["chain"] for c in chains if chain_reaches(c, legs_wanted)]
    stopped = [f"{c.get('chain')} at {c.get('stopped_at')}: {str(c.get('stop_reason'))[:200]}" for c in chains
               if not chain_reaches(c, legs_wanted)]
    present = [j["chain"] for j in jobs if j["chain"] in by_name]
    checks.append(_check("LC.REACH", GRADED, len(reached) >= reach_min, len(present), expected, (GAME, HARNESS),
                         f"chains reaching the target (every leg continued, the last reached by the game): {len(reached)} "
                         f"of {len(present)} (bound: at least {reach_min} of {expected}); reached {reached or 'none'}; "
                         f"not: {stopped or 'none'}"))
    # LC.PURITY
    judged, bad = 0, []
    for chain, leg in ran:
        statuses = {c["id"]: c["status"] for c in leg.get("checks") or [] if c["id"] in PURITY_IDS}
        if statuses:
            judged += 1
            wrong = [f"{i} {statuses.get(i, 'MISSING')}" for i in PURITY_IDS if statuses.get(i) != PASS]
            if wrong:
                bad.append(f"{chain.get('chain')} {leg.get('leg')}: {', '.join(wrong)}")
    checks.append(_check("LC.PURITY", GRADED, not bad and judged == len(ran), judged, floor, (HARNESS,),
                         f"purity CLEAN on every leg that ran: {judged - len(bad)} of {judged} judged legs with every "
                         f"counting purity check PASS, of {len(ran)} legs that ran (want every one; floor {floor}); "
                         f"failing: {bad or 'none'}"))
    # LC.THIS_RUN
    fresh = [(chain.get("chain"), leg.get("leg"), _status(leg, "L5.THIS_RUN")) for chain, leg in ran]
    read = [f for f in fresh if f[2] is not None]
    stale = [f"{c} {l} {s}" for c, l, s in read if s != PASS]
    checks.append(_check("LC.THIS_RUN", GRADED, not stale and len(read) == len(ran), len(read), floor, (HARNESS, GAME),
                         f"L5.THIS_RUN PASS on {len(read) - len(stale)} of {len(read)} legs read, of {len(ran)} that ran "
                         f"(want every one; floor {floor}); not: {stale or 'none'}"))
    # LC.WORLD_SIZE
    sizes = [(f"{chain.get('chain')} {leg.get('leg')}", (leg.get("world_file") or {}).get("bytes")) for chain, leg in ran]
    measured = [(name, size) for name, size in sizes if isinstance(size, int)]
    big = [f"{name} {size}" for name, size in measured if size >= WORLD_MAX_BYTES]
    checks.append(_check("LC.WORLD_SIZE", WORLD_SIZE_KIND, not big and len(measured) == len(ran), len(measured), floor,
                         (HARNESS,), f"{'(information, never counted) ' if WORLD_SIZE_KIND == REPORTED else ''}every leg's "
                                     f"world.jsonl, measured before its deletion, under {WORLD_MAX_BYTES} bytes: largest "
                                     f"{max((s for _, s in measured), default=None)}; at or over: {big or 'none'}; not "
                                     f"measured: {[n for n, s in sizes if not isinstance(s, int)] or 'none'}"))
    # LC.CUSTODY (critic CH-06: every registered chain's L1 ran)
    unlaunched = [j["chain"] for j in jobs
                  if not ((by_name.get(j["chain"]) or {}).get("legs") or [{}])[0].get("status") == "RAN"]
    custody_bad = [f"{chain.get('chain')} {leg.get('leg')}: {'; '.join(leg.get('custody') or ['not checked'])}"
                   for chain, leg in ran if leg.get("status") != "RAN" or leg.get("custody") is None or leg.get("custody")]
    custody_judged = sum(1 for _, leg in ran if leg.get("status") == "RAN" and leg.get("custody") is not None)
    checks.append(_check("LC.CUSTODY", GRADED, not unlaunched and not custody_bad, custody_judged, floor, (HARNESS, GAME),
                         f"every registered chain's L1 ran ({expected - len(unlaunched)} of {expected}; not: "
                         f"{unlaunched or 'none'}) and every leg that ran started from what the bounds say "
                         f"({custody_judged - sum(1 for _, leg in ran if leg.get('custody'))} of {len(ran)}); problems: "
                         f"{custody_bad or 'none'}"))
    # LC.STARTER
    starters = [_starter_ok(c) for c in chains]
    judged_starters = [(ok, text) for ok, text in starters if ok is not None]
    wrong_starters = [text for ok, text in judged_starters if not ok]
    checks.append(_check("LC.STARTER", GRADED, not wrong_starters, len(judged_starters), reach_min, (GAME,),
                         f"the registered starter, the player's own, leads the party L1 left: {len(judged_starters) - len(wrong_starters)} "
                         f"of {len(judged_starters)} chains (floor {reach_min}); wrong: {wrong_starters or 'none'}"))
    # LC.MEMORY (B1 debt, declared)
    memory_judged, memory_bad, memory_lines = 0, [], []
    for chain in chains:
        n, problems, lines = memory_problems(chain)
        memory_judged += n
        memory_bad += problems
        memory_lines += lines
    checks.append(_check("LC.MEMORY", GRADED, not memory_bad and memory_judged == len(ran), memory_judged, floor, (AI, HARNESS),
                         f"the AI's memory line on {memory_judged} of {len(ran)} legs that ran (want every one; floor "
                         f"{floor}): L1 from nothing, each later leg from its AI_PLAYER_WORLD with the kept line's counts; "
                         f"wrong: {memory_bad or 'none'}; per leg: {' | '.join(memory_lines) or 'none'}"))
    if frozen is not None:
        checks.append(_check("LC.FROZEN", GRADED, bool(frozen[0]), 1, 1, (HARNESS,), f"the frozen-tree watch: {frozen[1]}"))
    if leftover is not None:
        checks.append(_check("LC.LEFTOVER", GRADED, not leftover, 1, 1, (HARNESS,),
                             f"python processes naming {PROFILE_PREFIX} after the batch: {leftover or 'none'} (want none)"))
    checks += reported_checks(chains, legs_wanted, reported)
    return checks


def reported_checks(chains: list[dict], legs_wanted: int, reported: dict) -> list[Check]:
    """The REPORTED checks: information, never counted (each prints FAIL in its own line when its property did not hold)."""
    checks: list[Check] = []
    ran = ran_legs(chains)
    progress, shares = [], []
    for chain in chains:
        legs = chain.get("legs") or []
        reached = [leg["leg"] for leg in legs if leg.get("status") == "RAN" and leg_reached(leg)[0]]
        progress.append(f"{chain.get('chain')}: reached {reached or 'none'}"
                        + ("" if chain_reaches(chain, legs_wanted) else f", stopped at {chain.get('stopped_at')}"))
        for leg in legs:
            stop = leg.get("harness_stop") or {}
            if leg.get("status") in RAN and isinstance(stop.get("real_frames"), int):
                shares.append((stop["real_frames"] / max(1, leg.get("frames") or 1), f"{chain.get('chain')} {leg.get('leg')}",
                               stop["real_frames"], leg.get("frames"), leg.get("elapsed"), leg.get("wall")))
    top = max(shares, default=None)
    checks.append(_check("LC.PROGRESS", REPORTED, all(chain_reaches(c, legs_wanted) for c in chains), len(chains), None,
                         (GAME, HARNESS), f"(information) {'; '.join(progress) or 'none'}; per leg real frames / budget, "
                                          f"s / wall: " + "; ".join(f"{n} {f}/{b} {e}/{w:g}" for _, n, f, b, e, w in shares)
                         + (f"; the most of its budget a leg used: {top[1]} {top[0]:.0%}" if top else "")))
    multi = [(f"{c.get('chain')} {leg.get('leg')}", ((leg.get("measures") or {}).get("log") or {})) for c, leg in ran]
    flagged = [f"{n} {m.get('multichoice')} ({m.get('forms')}; first: {m.get('first_unexpected')})" for n, m in multi
               if m.get("multichoice")]
    checks.append(_check("LC.MULTICHOICE", REPORTED, not flagged, len(multi), None, (AI,),
                         f"(information) LINES of ai_player.log saying 'an unexpected multichoice' (lines, not events) per "
                         f"leg: " + "; ".join(f"{n} {m.get('multichoice')}" for n, m in multi)
                         + f"; legs over 0: {flagged or 'none'}; every 'an unexpected <kind>' by kind: "
                         + ("; ".join(f"{n} {m.get('unexpected')}" for n, m in multi if m.get("unexpected")) or "none")))
    outcomes, disagree = [], []
    for c, leg in ran:
        stop = leg.get("harness_stop") or {}
        claim = None
        if leg.get("outcome") and stop.get("by") == "ai":
            claim = leg["outcome"] == f"play: done: {leg.get('target')} reached"
        held = bool((leg.get("proof_after") or {}).get("held"))
        mark = "no claim" if claim is None else "agree" if claim == held else "DISAGREE"
        outcomes.append(f"{c.get('chain')} {leg.get('leg')} {leg.get('outcome')!r} vs game {'held' if held else 'not held'}: {mark}")
        if mark == "DISAGREE":
            disagree.append(outcomes[-1])
    checks.append(_check("LC.OUTCOME", REPORTED, not disagree, len(outcomes), None, (AI, GAME),
                         f"(information) the AI's exit claim beside the game's proof: {'; '.join(outcomes) or 'none'}"))
    ended = [f"{c.get('chain')} {leg.get('leg')} {(leg.get('harness_stop') or {}).get('by')} "
             f"({(leg.get('harness_stop') or {}).get('cause')})" for c, leg in ran]
    checks.append(_check("LC.ENDED", REPORTED, all((leg.get("harness_stop") or {}).get("by") == "ai" for _, leg in ran),
                         len(ran), None, (HARNESS,), f"(information) who ended each leg: {'; '.join(ended) or 'none'}"))
    optional = reported.get("optional") or {}
    checks.append(_check("LC.OPTIONAL", REPORTED, True, len(optional), None, (GAME,),
                         f"(information) the optional milestones' proofs at each chain's last leg that ran: "
                         + ("; ".join(f"{k}: {v}" for k, v in optional.items()) or "none")))
    worlds = [f"{c.get('chain')} {leg.get('leg')} {(leg.get('world_file') or {}).get('bytes')} B, "
              f"{((leg.get('measures') or {}).get('world') or {}).get('lines')} lines, deleted "
              f"{(leg.get('world_file') or {}).get('deleted')}" for c, leg in ran]
    totals = {c.get("chain"): sum((leg.get("world_file") or {}).get("bytes") or 0 for leg in c.get("legs") or [])
              for c in chains}
    left = reported.get("world_left") or []
    undeleted = [w for c, leg in ran for w in [f"{c.get('chain')} {leg.get('leg')}"]
                 if not (leg.get("world_file") or {}).get("deleted")]
    checks.append(_check("LC.WORLD", REPORTED, not left and not undeleted, len(ran), None, (HARNESS,),
                         f"(information) per leg: {'; '.join(worlds) or 'none'}; per chain total bytes {totals}; not deleted "
                         f"after its leg: {undeleted or 'none'}; still present after the end sweep: {left or 'none'}"))
    profiles = reported.get("profiles")
    checks.append(_check("LC.PROFILES", REPORTED, profiles is not None and not profiles.get("problems"), len(chains), None,
                         (HARNESS,), f"(information) {profiles.get('text') if profiles else 'not measured'}"))
    main = reported.get("main_profile")
    checks.append(_check("LC.MAIN_PROFILE", REPORTED, main is not None and main.get("unchanged"), 1, None, (HARNESS,),
                         f"(information) {MAIN_PROFILE}: {main.get('text') if main else 'not measured'}"))
    most = reported.get("most_running")
    checks.append(_check("LC.CONCURRENCY", REPORTED, most is not None and most <= PARALLEL, 1, None, (HARNESS,),
                         f"(information) the most chains running at once: {most} (bound {PARALLEL})"))
    return checks


def batch_verdict(checks: list[Check]) -> str:
    """PASS iff every GRADED check PASSES (no waivers: a VACUOUS check fails)."""
    return typed_verdict(checks, waivers={})


def check_lines(checks: list[Check]) -> list[str]:
    lines = [f"  [{c.status}] {c.id} {c.kind} n/floor {'-' if c.n is None else c.n}/{'-' if c.floor is None else c.floor} "
             f"inputs {'+'.join(sorted(c.inputs))}: {c.text}" for c in checks]
    debts = [c for c in checks if c.id in AI_INPUT_DEBT and c.kind == GRADED]
    for c in debts:
        lines.append(f"B1 DEBT {c.id} ({c.status}): reads the AI's {AI_INPUT_DEBT[c.id]['ai_input']}; why: "
                     f"{AI_INPUT_DEBT[c.id]['plan']}")
    if not debts:
        lines.append("B1 DEBT: none")
    return lines


def optional_report(chains: list[dict], data: dict, to_chapter: int) -> dict:
    """LC.OPTIONAL: at each chain's last leg that ran, every optional milestone's proof for chapters up to the target's."""
    optional = [m for m in data.get("milestones") or [] if m.get("optional") and m["chapter"] <= to_chapter]
    out = {}
    for chain in chains:
        last = next((leg for leg in reversed(chain.get("legs") or []) if leg.get("status") in RAN), None)
        marks = ((last or {}).get("truth_after") or {}).get("marks")
        out[chain.get("chain")] = {m["id"]: proof_holds(marks, {"flags": m["done"].get("flags") or {},
                                                                "variables": m["done"].get("variables") or {},
                                                                "trainers": m["done"].get("trainers") or {}})["held"]
                                   for m in optional} if marks else "no end truth"
    return out


# ====================================================================== one chain (the child process)
def _truth_subset(truth: dict | None) -> dict | None:
    if not truth:
        return None
    story = truth.get("story") or {}
    return {"frame": truth.get("frame"), "map": truth.get("map"), "state_md5": truth.get("state_md5"),
            "marks": story.get("marks"), "stats": story.get("stats"), "party_exp": truth.get("party_exp"),
            "party_ot": truth.get("party_ot"), "player_tid": truth.get("player_tid")}


def check_rows(checks) -> list[dict]:
    return [{"id": c.id, "kind": c.kind, "status": c.status, "n": c.n, "floor": c.floor, "text": c.text} for c in checks]


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(temp, path)


def not_run_row(job: dict, leg: dict, status: str, reason: str) -> dict:
    return {"chain": job["chain"], "leg": leg["leg"], "chapter": leg["chapter"], "target": leg["target"],
            "proof": leg["proof"], "frames": leg["frames"], "wall": leg["wall"], "status": status, "reason": reason,
            "checks": [], "continue": False}


def new_chain_row(job: dict) -> dict:
    return {**{k: job.get(k) for k in ("chain", "pair", "personality", "starter", "seed", "profile")},
            "to": job["legs"][-1]["target"] if job.get("legs") else None, "legs": [], "reached_to": False,
            "stopped_at": None, "stop_reason": None}


def write_chain(out: Path, chain: dict, legs_wanted: int) -> None:
    chain["reached_to"] = chain_reaches(chain, legs_wanted)
    _write_json(out / "rows" / f"{chain['chain']}.json", chain)


def stop_rest(job: dict, chain: dict, start: int, reason: str, status: str = "NOT RUN") -> None:
    """Every leg from `start` on gets a row that says why it was not run (and is in no check's sample)."""
    for leg in job["legs"][start:]:
        chain["legs"].append(not_run_row(job, leg, status, reason))


def child_refusal(job: dict, profile: str) -> str | None:
    """The child's profile guard: it plays only in its own chain's NEW profile, never in the main one."""
    if not str(job.get("profile", "")).startswith(PROFILE_PREFIX):
        return f"the chain's profile {job.get('profile')!r} does not start with {PROFILE_PREFIX!r}"
    if job.get("profile") == MAIN_PROFILE or profile == MAIN_PROFILE:
        return f"refusing to play in {MAIN_PROFILE}"
    if profile != job.get("profile"):
        return f"live_step5.PROFILE is {profile!r}, not this chain's {job.get('profile')!r}"
    return None


def finish_leg(row: dict, run_dir: Path | None, keep: Path) -> None:
    """Section 6.3 inside the child, BEFORE the next leg: the world.jsonl's size recorded, streamed once (its last line
    kept outside the repo), then DELETED; the log counted; the small files copied. Writes into `row`."""
    measures: dict = {"log": None, "world": None}
    world_file = {"bytes": None, "deleted": False, "present": False}
    if run_dir is not None and run_dir.is_dir():
        world_path = run_dir / "world.jsonl"
        try:
            size_first = world_path.stat().st_size
        except OSError:
            size_first = None
        if size_first is not None:
            measures["world"] = stream_world_tail(world_path, keep / "world_last.jsonl")
            world_file = measure_then_delete(world_path)
            sizes = [s for s in (size_first, world_file.get("bytes"), measures["world"]["bytes"]) if isinstance(s, int)]
            if world_file.get("bytes") != size_first:
                row["notes"].append(f"world.jsonl was {size_first} bytes at first and {world_file.get('bytes')} at its "
                                    f"deletion: the larger is graded")
            world_file["bytes"] = max(sizes)
            if not world_file.get("deleted"):
                row["notes"].append("world.jsonl could not be DELETED after 5 tries (recorded; the end sweep retries)")
        measures["log"] = read_log_counts(run_dir / "ai_player.log")
        for name in ("actions.jsonl", "ai_player.log", "purity.json", "end_state.ss1", "stdout.txt"):
            if (run_dir / name).is_file():
                keep.mkdir(parents=True, exist_ok=True)
                shutil.copy2(run_dir / name, keep / name)
    world = measures["world"] or {}
    row["measures"], row["world_file"] = measures, world_file
    row["kept_world"] = world.get("kept")
    row["kept_world_sha256"] = world.get("last_sha256")


def guard_mark(out: Path, chain: str, leg: str) -> dict | None:
    marker = out / chain / f"{leg}.KILLED.json"
    if not marker.is_file():
        return None
    try:
        return json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"cause": "unknown", "text": "an unreadable marker"}


def run_chain(job: dict, run_leg: Callable | None = None) -> dict:
    """ONE CHAIN (spec section 4): its legs one after another in this process, each through `run_leg` (live:
    `live_step5.run_arm`; the tests pass a stub). Writes each leg's row and the chain row after EVERY leg; a chain that
    misses stops, its later legs NOT RUN with the reason."""
    from ai_player.gates import live_step5 as L5
    from ai_player.gates.live_step2 import check_purity

    run_leg = run_leg or L5.run_arm
    out = Path(job["out"])
    build_root = Path(job["build_root"])
    legs = job["legs"]
    chain = new_chain_row(job)
    refusal = child_refusal(job, L5.PROFILE)
    if refusal is not None:
        stop_rest(job, chain, 0, f"REFUSED: {refusal}", status="REFUSED")
        chain.update({"stopped_at": "L1", "stop_reason": f"REFUSED: {refusal}"})
        write_chain(out, chain, len(legs))
        return chain
    carried: dict = {}
    prev: dict | None = None
    for index, leg in enumerate(legs):
        for name, why in ((STOP_FILE, "the code under test changed mid-batch (STOP.txt)"),
                          (ABORT_FILE, "the batch was ABORTED by the harness (disk: free space)")):
            if (out / name).is_file():
                stop_rest(job, chain, index, why)
                chain.update({"stopped_at": leg["leg"], "stop_reason": why})
                write_chain(out, chain, len(legs))
                return chain
        arm_name = f"{job['chain']}-{leg['leg']}"
        _write_json(out / job["chain"] / "current_leg.json", {"leg": leg["leg"], "arm": arm_name,
                                                              "started": time.strftime("%Y-%m-%d %H:%M:%S")})
        fresh = prev is None
        env = L5.play_env(job["personality"], job["starter"] if fresh else None, leg["target"])
        arm = L5.Arm(arm_name, f"{job['chain']} {leg['leg']}: chapter {leg['chapter']} to {leg['target']} "
                               f"({job['personality']}, {job['starter']}, seed {job['seed']})",
                     leg["frames"], leg["wall"], env, seed=job["seed"], fresh=fresh,
                     state_from=None if fresh else prev["arm"])
        keep = out / job["chain"] / leg["leg"]
        try:
            run = run_leg(arm, build_root, carried)
        except Exception as error:  # noqa: BLE001 - a crashed leg still has its world measured and deleted
            row = salvage_leg(job, leg, build_root, out, arm_name, f"ERROR: the leg raised {type(error).__name__}: "
                                                                    f"{str(error)[:400]}", status="ERROR")
            chain["legs"].append(row)
            stop_rest(job, chain, index + 1, f"the chain stopped at {leg['leg']}: it raised {type(error).__name__}")
            chain.update({"stopped_at": leg["leg"], "stop_reason": row["reason"]})
            write_chain(out, chain, len(legs))
            return chain
        check_purity(run, None)
        L5.check_after_is_this_run(run)
        sent = {ENV_BRAIN: "play", ENV_SEED: str(arm.seed), **arm.env}
        if run.world_in is not None:
            sent[ENV_WORLD] = str(run.world_in)
        before, after = _truth_subset(run.before), _truth_subset(run.after)
        proof_before = (proof_holds(before.get("marks"), leg["proof"]) if before
                        else None if fresh else {"unread": True, "held": None})
        row = {"chain": job["chain"], "leg": leg["leg"], "chapter": leg["chapter"], "target": leg["target"],
               "proof": leg["proof"], "frames": leg["frames"], "wall": leg["wall"], "arm": arm_name, "status": "RAN",
               "reason": None, "exit": run.exit_code, "elapsed": round(run.elapsed or 0, 1),
               "run_dir": str(run.run_dir) if run.run_dir else None, "command": [str(c) for c in run.command],
               "env": sent, "env_keys": sorted(sent), "world_in": str(run.world_in) if run.world_in else None,
               "world_in_sha256": file_sha256(run.world_in) if run.world_in and Path(run.world_in).is_file() else None,
               "start_state": str(run.start_state) if run.start_state else None,
               "truth_before": before, "truth_after": after, "proof_before": proof_before,
               "proof_after": proof_holds((after or {}).get("marks"), leg["proof"]) if after else
               {"held": False, "missing": ["(no end truth)"], "failing": [], "values": {}},
               "already_held": (proof_before or {}).get("held") if proof_before else (False if fresh else None),
               "checks": check_rows(run.checks), "harness_stop": run.measures.get("harness_stop"),
               "outcome": ((run.verdict or {}).get("facts") or {}).get("exit_reason"),
               "gate_line": next((ln for ln in run.stdout.splitlines() if ln.startswith("[AI-GATE]")), None),
               "notes": list(run.notes)}
        row["reached"] = leg_reached(row)[0]
        finish_leg(row, run.run_dir, keep)
        row["guard_killed"] = guard_mark(out, job["chain"], leg["leg"])
        end_state = (run.run_dir / "end_state.ss1") if run.run_dir else None
        # (spec section 4) the next leg gets the KEPT last line as its world memory, never the deleted original (F6/F8)
        carried.pop(arm_name, None)
        if end_state is not None and end_state.is_file() and row["kept_world"]:
            reads = [r for r in run.earlier + run.records if r.get("decision") == "read"]
            carried[arm_name] = (end_state, Path(row["kept_world"]), reads)
        row["custody"] = custody_problems(row, prev, job, index)
        go, why = continue_after(row, (out / STOP_FILE).is_file())
        row["continue"], row["why"] = go, why
        _write_json(keep / "row.json", row)
        chain["legs"].append(row)
        if not go:
            stop_rest(job, chain, index + 1, f"the chain stopped at {leg['leg']}: {why}")
            chain.update({"stopped_at": leg["leg"], "stop_reason": why})
            write_chain(out, chain, len(legs))
            return chain
        write_chain(out, chain, len(legs))
        prev = {**row, "arm": arm_name}
    write_chain(out, chain, len(legs))
    return chain


def salvage_leg(job: dict, leg: dict, build_root: Path, out: Path, arm_name: str, reason: str,
                status: str = "SALVAGED") -> dict:
    """A leg whose child died (or raised): the NEWEST run folder named for THIS leg's arm (critic CH-13: never the
    previous leg's folder) has its world.jsonl measured and DELETED and gets a row with NO checks (purity and THIS_RUN
    read it as not judged: VACUOUS, which fails). No such folder: NOT RUN (the process ended before the launch)."""
    runs = build_root / "profiles" / job["profile"] / "ai_player_runs"
    try:
        folders = sorted(p for p in runs.iterdir() if p.is_dir() and p.name.endswith(f"-{arm_name}"))
    except OSError:
        folders = []
    if not folders:
        return not_run_row(job, leg, "NOT RUN", f"{reason}; no run folder of {arm_name}: the process ended before its "
                                                f"launch")
    row = {**not_run_row(job, leg, status, reason), "arm": arm_name, "run_dir": str(folders[-1]), "notes": [],
           "truth_before": None, "truth_after": None, "harness_stop": None}
    finish_leg(row, folders[-1], out / job["chain"] / leg["leg"])
    row["notes"].append("NO CHILD ROW: salvaged by the orchestrator; its world.jsonl was measured and deleted; no check "
                        "was made, so purity and freshness read it as not judged")
    return row


def salvage_chain(job: dict, build_root: Path, out: Path, why: str) -> dict:
    """A chain whose child left no complete chain row: its done legs are kept, the leg it was playing is salvaged
    (`salvage_leg`), the later legs are NOT RUN with the reason."""
    path = out / "rows" / f"{job['chain']}.json"
    chain = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else new_chain_row(job)
    done = {leg["leg"] for leg in chain["legs"]}
    current = None
    marker = out / job["chain"] / "current_leg.json"
    if marker.is_file():
        try:
            current = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            current = None
    salvaged = False
    for index, leg in enumerate(job["legs"]):
        if leg["leg"] in done:
            continue
        if not salvaged and current and current.get("leg") == leg["leg"]:
            row = salvage_leg(job, leg, build_root, out, current["arm"], f"the chain's process ended during this leg ({why})")
            chain["legs"].append(row)
            salvaged = True
            chain.update({"stopped_at": leg["leg"], "stop_reason": row["reason"]})
            continue
        chain["legs"].append(not_run_row(job, leg, "NOT RUN", f"the chain's process ended ({why}; see "
                                                              f"out/{job['chain']}.child.log)"))
        if chain.get("stopped_at") is None:
            chain.update({"stopped_at": leg["leg"], "stop_reason": f"the chain's process ended ({why})"})
    write_chain(out, chain, len(job["legs"]))
    return chain


def child(job_path: Path) -> int:
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    from ai_player.gates import live_step5 as L5

    L5.PROFILE = job["profile"]
    chain = run_chain(job)
    print(f"[{job['chain']}] " + "; ".join(f"{leg['leg']} {leg['status']}"
                                           + (f" reached {leg.get('reached')}" if leg["status"] == "RAN" else "")
                                           for leg in chain["legs"]), flush=True)
    return 0


# ====================================================================== the batch (the orchestrator)
def leftover_processes(prefix: str | None = None) -> list[str]:
    """Python processes whose command line names this batch's profiles; never any other (the bot tuner runs beside)."""
    prefix = prefix or PROFILE_PREFIX
    try:
        done = subprocess.run(["powershell", "-NoProfile", "-Command",
                               "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine "
                               f"-like '*{prefix}*' }} | ForEach-Object {{ \"$($_.ProcessId) $($_.CommandLine)\" }}"],
                              capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        return [f"could not list the processes: {error}"]
    return [line.strip()[:200] for line in done.stdout.decode(errors="replace").splitlines() if line.strip()]


def safe_free(path: Path) -> float | None:
    try:
        return free_gb(path)
    except OSError:
        return None


def default_build_root() -> Path:
    """The build root the truth harness reads (`probe_eyes.boot` resolves it with no argument), so the only one a graded
    batch may play in (critic CH-08)."""
    from ai_player.host import launcher

    return (launcher.PACKAGE_ROOT / "sandbox-pokebot").resolve()


def git_state(repo: Path | None = None) -> dict:
    """R9's facts: HEAD and origin/main after a fetch, and every TRACKED file changed (critic CH-08: the whole tree)."""
    repo = repo or REPO

    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, timeout=120,
                              check=True).stdout.strip()
    try:
        git("fetch", "-q", "origin")
        return {"head": git("rev-parse", "HEAD"), "origin": git("rev-parse", "origin/main"),
                "dirty": [ln for ln in git("status", "--porcelain", "--untracked-files=no").splitlines() if ln.strip()]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"head": None, "origin": None, "dirty": [], "error": str(error)[:300]}


def g3_scan() -> list:
    from ai_player.gates.check_grader_imports import scan

    return scan(REPO, ("ai_player.gates.live_chain",))


def watch_tree():
    from ai_player.gates.provenance import watch

    return watch(REPO, explicit=True)


def code_line() -> str:
    from ai_player.gates.provenance import provenance

    return provenance(REPO)


def snapshot() -> object:
    from ai_player.gates.provenance import snapshot_tree

    return snapshot_tree(REPO)


class ChildProcess:
    """One chain's child: `py -B live_chain.py child JOB.json`, its output in `<chain>.child.log`."""

    def __init__(self, job_path: Path, log_path: Path) -> None:
        self.log = open(log_path, "w", encoding="utf-8")
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        self.proc = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "child", str(job_path)],
                                     cwd=str(REPO), env=env, stdout=self.log, stderr=subprocess.STDOUT, creationflags=flags)
        self.pid = self.proc.pid

    def poll(self) -> int | None:
        code = self.proc.poll()
        if code is not None and not self.log.closed:
            self.log.close()
        return code

    def kill_tree(self) -> None:
        kill_descendants(self.pid)
        try:
            self.proc.kill()
        except OSError:
            pass


def spawn_child(job: dict, job_path: Path, log_path: Path) -> ChildProcess:
    return ChildProcess(job_path, log_path)


@dataclass
class Deps:
    """The orchestrator's side effects, injected (the tests run a whole batch with stub launches, a temp ledger and a temp
    evidence folder; spec section 8)."""
    spawn: Callable = spawn_child
    free: Callable[[Path], float | None] = safe_free
    git_state: Callable[[], dict] = git_state
    leftover: Callable[[], list[str]] = leftover_processes
    g3: Callable[[], list] = g3_scan
    watch: Callable[[], object] = watch_tree
    snapshot: Callable[[], object] = snapshot
    code_line: Callable[[], str] = code_line
    default_build_root: Callable[[], Path] = default_build_root
    kill: Callable[[int], list] = kill_descendants
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    ledger_path: Path | None = None
    evidence_dir: Path | None = None
    #: the repository R1 and R8 measure --out and the build root against (None: this one; a test puts a temp tree here)
    repo: Path | None = None
    poll_seconds: float = 5.0
    stagger: float | None = None
    tree_every: float = 60.0
    events: list = field(default_factory=list)


def schedule(jobs: list[dict], spawn: Callable, tick: Callable, parallel: int, stagger: float, sleep: Callable,
             may_start: Callable, poll_seconds: float) -> dict:
    """At most `parallel` chains at once, `stagger` seconds apart, in the jobs' order; `tick(running)` after every pass (the
    disk guard, the watchdog, the frozen tree). Returns the most chains it ever had running, the start order and the chains
    it did not start (with why)."""
    pending = list(jobs)
    running: list[tuple[dict, object]] = []
    most = 0
    order: list[str] = []
    not_started: list[tuple[dict, str]] = []
    while pending or running:
        while pending and len(running) < parallel:
            job = pending.pop(0)
            ok, why = may_start(job)
            if not ok:
                not_started.append((job, why))
                continue
            running.append((job, spawn(job)))
            order.append(job["chain"])
            most = max(most, len(running))
            if pending:
                sleep(stagger)
        tick(running)
        for item in list(running):
            if item[1].poll() is not None:
                running.remove(item)
        if pending or running:
            sleep(poll_seconds)
    return {"most_running": most, "order": order, "not_started": not_started}


def run_refusal(args, facts: dict) -> str | None:
    """EVERY REFUSAL before `ledger.begin` (spec section 7, R1-R9 and the critique's additions), pure: `facts` are what
    the orchestrator measured (`gather_facts`). None: the batch may begin (the ledger, R10, may still refuse)."""
    repo = Path(facts["repo"])
    out, build_root = Path(facts["out"]), Path(facts["build_root"])
    graded = args.purpose == "graded"
    if out == repo or out.is_relative_to(repo):
        return f"R1: --out {out} is inside the repository; the summaries and kept lines live outside it (section 6)"
    learner = [p for p in (out, build_root) if "pokebot-learner" in (part.lower() for part in p.parts)]
    if learner:
        return f"R8: {learner[0]} lies in a folder named pokebot-learner: the learner clone is never touched"
    if not build_root.is_relative_to(repo):
        return f"R8: the build root {build_root} is not under this repository {repo}"
    if graded:
        given = [name for name in ("first_seed", "to", "chains", "leg_frames", "prediction_file")
                 if getattr(args, name, None) is not None]
        if given or args.run not in GRADED_RUNS:
            return (f"R2: a graded batch plays exactly a registered run ({sorted(GRADED_RUNS)}) and nothing else: "
                    f"--run {args.run!r}, given {['--' + g.replace('_', '-') for g in given] or 'nothing more'}")
        if Path(facts["default_build_root"]) != build_root:
            return (f"R2: a graded batch plays in the build root the truth harness reads ({facts['default_build_root']}), "
                    f"not {build_root}")
    else:
        missing = [name for name in ("first_seed", "to", "prediction_file") if getattr(args, name, None) is None]
        if missing:
            return f"R3: a development batch needs {['--' + m.replace('_', '-') for m in missing]} (registered and predicted)"
        if args.run is not None:
            return "R3: --run names a GRADED registration; a development batch gives --first-seed and --to"
        if facts.get("prediction_error"):
            return f"R3: {facts['prediction_error']}"
    if facts.get("legs_error"):
        return f"R4: {facts['legs_error']}"
    if facts.get("g3"):
        return f"R5: the G-3 walk of ai_player.gates.live_chain found an AI import: {facts['g3']}"
    if graded:
        git = facts.get("git") or {}
        if git.get("error") or not git.get("head") or git.get("head") != git.get("origin"):
            return (f"R9: a graded batch runs on a PUSHED commit: HEAD {git.get('head')} is not origin/main "
                    f"{git.get('origin')} {git.get('error') or ''}".rstrip())
        if git.get("dirty"):
            return f"R9: tracked files are changed: {git['dirty'][:8]}"
    else:
        named = facts.get("named") or []
        if named:
            return (f"R3: the development seeds {facts.get('seeds')} are named by ledger entries "
                    f"{[e['id'] for e in named]}: a rehearsal on them would replay their trajectories (critic CH-15)")
    free = facts.get("free")
    if free is None or free < FREE_MIN_GB:
        return f"R6: {free if free is None else round(free, 1)} GB free on the build root's drive, under the {FREE_MIN_GB:g} GB floor"
    if facts.get("profiles_exist"):
        return f"R7: the profiles {facts['profiles_exist']} exist under {build_root / 'profiles'}: each chain needs a NEW one"
    return None


def gather_facts(args, deps: Deps) -> dict:
    """What `run_refusal` judges, measured once (each piece robust to the arguments it has)."""
    repo = repo_root()
    facts: dict = {"repo": Path(deps.repo).resolve() if deps.repo else repo, "out": Path(args.out).resolve(),
                   "default_build_root": Path(deps.default_build_root())}
    facts["build_root"] = Path(args.build_root).resolve() if args.build_root else facts["default_build_root"]
    graded = args.purpose == "graded"
    run = GRADED_RUNS.get(args.run) if graded else None
    to = run["to"] if run else (None if graded else args.to)
    chains = 6 if graded else (args.chains or 3)
    first = run["seeds"][0] if run else args.first_seed
    facts.update({"to": to, "chains": chains, "first": first})
    try:
        legs = legs_of(to, load_milestones(repo))
        if not graded:
            override = parse_leg_frames(args.leg_frames, legs)
            facts["override"] = override
            legs = [{**leg, "frames": override.get(leg["leg"], leg["frames"])} for leg in legs]
        facts["legs"] = legs
        facts["jobs"] = jobs_of(first, chains) if first is not None else []
    except Refusal as error:
        facts["legs_error"] = str(error)
    if not graded and args.prediction_file is not None:
        try:
            facts["prediction"] = Path(args.prediction_file).read_text(encoding="utf-8").strip()
            if not facts["prediction"]:
                facts["prediction_error"] = f"the prediction file {args.prediction_file} is empty"
        except OSError as error:
            facts["prediction_error"] = f"the prediction file cannot be read: {error}"
    facts["g3"] = deps.g3()
    if first is not None:
        facts["seeds"] = run["seeds"] if run else seeds_of(first, chains)
    if graded:
        facts["git"] = deps.git_state()
    elif first is not None:
        facts["named"] = seeds_named(*facts["seeds"], path=deps.ledger_path)
    facts["free"] = deps.free(facts["build_root"])
    facts["profiles_exist"] = [j["profile"] for j in facts.get("jobs") or []
                               if (facts["build_root"] / "profiles" / j["profile"]).exists()]
    return facts


def run_folders(build_root: Path) -> dict[str, list[str]]:
    """Every profile's run folders (profile -> names), for LC.PROFILES."""
    out: dict[str, list[str]] = {}
    try:
        profiles = [p for p in (build_root / "profiles").iterdir() if p.is_dir()]
    except OSError:
        return out
    for profile in profiles:
        try:
            out[profile.name] = sorted(p.name for p in (profile / "ai_player_runs").iterdir() if p.is_dir())
        except OSError:
            continue
    return out


def profiles_report(before: dict, after: dict, chains: list[dict], jobs: list[dict]) -> dict:
    """LC.PROFILES (REPORTED, critic CH-10): each chain's profile holds one run folder per leg that ran, named for it, and
    no profile but the chain's own gained a folder named for one of this batch's arms."""
    problems, lines = [], []
    by_name = {c.get("chain"): c for c in chains}
    for job in jobs:
        arms = sorted(f"{job['chain']}-{leg['leg']}" for leg in (by_name.get(job["chain"]) or {}).get("legs") or []
                      if leg.get("status") in RAN and leg.get("run_dir"))
        folders = after.get(job["profile"], [])
        found = sorted(next((a for a in arms if name.endswith("-" + a)), name) for name in folders)
        if found != arms:
            problems.append(f"{job['profile']}: folders {folders} for the legs {arms}")
        lines.append(f"{job['profile']} {len(folders)} folders")
    ours = {j["profile"] for j in jobs}
    for profile, names in after.items():
        new = set(names) - set(before.get(profile, []))
        strays = [n for n in new if "-LC-" in n and profile not in ours]
        if strays:
            problems.append(f"{profile} gained {strays}")
    return {"problems": problems, "text": f"{'; '.join(lines)}; problems: {problems or 'none'}"}


def main_profile_state(build_root: Path) -> dict:
    profile = build_root / "profiles" / MAIN_PROFILE
    state = profile / "current_state.ss1"
    runs = profile / "ai_player_runs"
    try:
        folders = sorted(p.name for p in runs.iterdir()) if runs.is_dir() else []
    except OSError:
        folders = ["(unreadable)"]
    try:
        mark = [state.stat().st_mtime_ns, file_sha256(state)] if state.is_file() else None
    except OSError:
        mark = ["(unreadable)"]
    return {"present": profile.is_dir(), "folders": folders, "state": mark}


def end_sweep(jobs: list[dict], build_root: Path) -> list[str]:
    """After the batch: any world.jsonl still in the chains' profiles is deleted again; what could not be is reported."""
    left = []
    for job in jobs:
        runs = build_root / "profiles" / job["profile"] / "ai_player_runs"
        if not runs.is_dir():
            continue
        for world in runs.glob("*/world.jsonl"):
            record = measure_then_delete(world)
            if not record.get("deleted"):
                left.append(f"{world} {record.get('bytes')} bytes (could not be deleted)")
            else:
                left.append(f"{world} {record.get('bytes')} bytes (deleted by the end sweep)")
    return left


def evidence_path(evidence_dir: Path, graded: bool, to: str, first: int) -> Path:
    stamp = time.strftime("%Y-%m-%d")
    return evidence_dir / (f"{stamp}-chain-heldout.txt" if graded else f"{stamp}-chain-heldout-dev-{to}-{first}.txt")


def run_batch(args, deps: Deps | None = None) -> int:
    """THE BATCH: refusals, the ledger's begin, the chains (at most PARALLEL at once), salvage, the end sweep, the grade,
    one evidence file and the ledger's finish. Exit 0 PASS (graded) or ran (development), 1 FAIL, 2 refused, 3 ABORTED."""
    from ai_player.gates.provenance import keep_earlier, line_digest

    deps = deps or Deps()
    graded = args.purpose == "graded"
    facts = gather_facts(args, deps)
    refusal = run_refusal(args, facts)
    if refusal is not None:
        print(f"REFUSED: {refusal}", flush=True)
        return 2
    out, build_root = facts["out"], facts["build_root"]
    legs, jobs, seeds, to = facts["legs"], facts["jobs"], facts["seeds"], facts["to"]
    chains_n, reach_min = facts["chains"], reach_min_of(facts["chains"])
    prediction = facts.get("prediction")
    development = None if graded else {"chains": chains_n, "leg_frames_override": facts.get("override") or {},
                                       "prediction_sha256": hashlib.sha256(prediction.encode("utf-8")).hexdigest()}
    numbers = registered_numbers(args.run if graded else None, to, seeds, chains_n, legs, repo_root(), development)
    sha = ledger.numbers_sha256(numbers)
    code = deps.code_line()
    tree = deps.watch()
    kept = deps.snapshot()
    print(f"[LC] numbers sha256 {sha} (seeds {seeds[0]}-{seeds[1]}, {args.purpose}); code: {code}; tree kept: {kept}",
          flush=True)
    try:
        entry, ledger_lines = begin(args.purpose, seeds, numbers, line_digest(code),
                                    note=f"LIVE CHAIN held-out (USER RULING 55), {args.purpose}, to {to}, {chains_n} chains, "
                                         f"driver ai_player/gates/live_chain.py, numbers sha256 {sha[:16]}, free "
                                         f"{facts['free']:.1f} GB"
                                         + (f", prediction sha256 {development['prediction_sha256'][:16]}" if development
                                            else ""), path=deps.ledger_path)
    except ledger.Refused as error:
        print(f"REFUSED by the ledger (R10): {error}", flush=True)
        return 2
    for line in ledger_lines:
        print(f"[LC] {line}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    began = time.strftime("%Y-%m-%d %H:%M:%S")
    main_before = main_profile_state(build_root)
    folders_before = run_folders(build_root)
    events: list[str] = deps.events
    stagger = STAGGER_SECONDS if deps.stagger is None else deps.stagger
    paths: dict[str, tuple[Path, Path]] = {}
    watchdog = chain_watchdog_seconds(legs)
    for job in jobs:
        full = {**job, "legs": legs, "out": str(out), "build_root": str(build_root), "watchdog_seconds": watchdog}
        job_path = out / f"{job['chain']}.job.json"
        _write_json(job_path, full)
        paths[job["chain"]] = (job_path, out / f"{job['chain']}.child.log")
    started: dict[str, float] = {}
    state = {"last_tree": deps.clock(), "aborted": False}

    def may_start(job: dict) -> tuple[bool, str]:
        if state["aborted"] or (out / ABORT_FILE).is_file():
            return False, "the batch was ABORTED by the harness (disk: free space)"
        if tree.moved or not tree.check(f"before {job['chain']}"):
            if not (out / STOP_FILE).is_file():
                (out / STOP_FILE).write_text(f"the tree moved: {tree.moves[-1]}\n", encoding="utf-8")
            return False, "the code under test changed mid-batch"
        return True, ""

    def spawn(job: dict):
        job_path, log_path = paths[job["chain"]]
        started[job["chain"]] = deps.clock()
        print(f"[LC] {job['chain']} started ({time.strftime('%H:%M:%S')})", flush=True)
        return deps.spawn({**job, "legs": legs, "out": str(out), "build_root": str(build_root)}, job_path, log_path)

    def tick(running: list) -> None:
        now = deps.clock()
        if now - state["last_tree"] >= deps.tree_every:
            state["last_tree"] = now
            if not tree.check("during the batch") and not (out / STOP_FILE).is_file():
                (out / STOP_FILE).write_text(f"the tree moved: {tree.moves[-1]}\n", encoding="utf-8")
                events.append(f"the frozen tree moved: {tree.moves[-1]}")
        free = deps.free(build_root)
        for job, handle in running:
            if handle.poll() is not None:
                continue
            name, size = newest_world(build_root / "profiles" / job["profile"] / "ai_player_runs")
            leg = leg_of_folder(name, job["chain"])
            cause = guard_decision(size, free)
            if cause == "free" and not state["aborted"]:
                state["aborted"] = True
                (out / ABORT_FILE).write_text(f"under {GUARD_FREE_GB:g} GB free: {free}\n", encoding="utf-8")
                events.append(f"ABORT: {free} GB free, under {GUARD_FREE_GB:g}: every running launcher is killed")
            if cause is not None and leg is not None:
                marker = out / job["chain"] / f"{leg}.KILLED.json"
                if not marker.exists():
                    killed = deps.kill(handle.pid)
                    text = (f"{job['chain']} {leg}: the disk guard ({cause}) killed the launcher at "
                            f"{time.strftime('%H:%M:%S')}: world.jsonl {size} bytes, {free} GB free; pids {killed}")
                    _write_json(marker, {"cause": cause, "text": text})
                    events.append(text)
            if now - started.get(job["chain"], now) > watchdog and not (out / job["chain"] / "WATCHDOG.txt").exists():
                handle.kill_tree()
                (out / job["chain"]).mkdir(parents=True, exist_ok=True)
                (out / job["chain"] / "WATCHDOG.txt").write_text(f"past {watchdog} s\n", encoding="utf-8")
                events.append(f"{job['chain']}: the chain watchdog ({watchdog} s) killed its process tree")

    plan = schedule(jobs, spawn, tick, PARALLEL, stagger, deps.sleep, may_start, deps.poll_seconds)
    left_procs = deps.leftover()
    chains: list[dict] = []
    not_started = {job["chain"]: why for job, why in plan["not_started"]}
    for job in jobs:
        full = {**job, "legs": legs}
        if job["chain"] in not_started:
            chain = new_chain_row(full)
            stop_rest(full, chain, 0, not_started[job["chain"]])
            chain.update({"stopped_at": "L1", "stop_reason": not_started[job["chain"]]})
            write_chain(out, chain, len(legs))
            chains.append(chain)
            continue
        path = out / "rows" / f"{job['chain']}.json"
        chain = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        if chain is None or len(chain.get("legs") or []) != len(legs):
            why = ("killed by the chain watchdog" if (out / job["chain"] / "WATCHDOG.txt").is_file()
                   else "it ended without its chain row")
            chain = salvage_chain({**full, "out": str(out)}, build_root, out, why)
            events.append(f"{job['chain']}: salvaged ({why})")
        chains.append(chain)
    world_left = end_sweep(jobs, build_root)
    profiles = profiles_report(folders_before, run_folders(build_root), chains, jobs)
    main_after = main_profile_state(build_root)
    main = {"unchanged": main_before == main_after,
            "text": f"before {main_before}, after {main_after}: {'unchanged' if main_before == main_after else 'CHANGED'}"}
    held = tree.check("after the batch")
    _, frozen_line = tree.seal("PASS" if held else "FAIL")
    optional = optional_report(chains, load_milestones(repo_root()), legs[-1]["chapter"])
    checks = grade_batch(chains, jobs, len(legs), reach_min, (held and not tree.moves, frozen_line), left_procs,
                         {"world_left": [w for w in world_left if "could not" in w], "profiles": profiles,
                          "main_profile": main, "optional": optional, "most_running": plan["most_running"]})
    result = batch_verdict(checks)
    aborted = state["aborted"] or (out / ABORT_FILE).is_file()
    failing = [c.id for c in checks if c.kind == GRADED and c.status != PASS]
    label = ledger.label(args.purpose)
    shown = "ABORTED (harness: disk)" if aborted else result
    reach = next(c for c in checks if c.id == "LC.REACH")
    verdict_line = (f"{label}, {shown if graded else 'NO PASS (development: ' + shown + ' by the registered rules)'}"
                    f"{' (failing: ' + ', '.join(failing) + ')' if failing and not aborted else ''}: live chain held-out, "
                    f"to {to}, seeds {seeds[0]}-{seeds[1]}, numbers sha256 {sha[:16]}; {reach.text.split(': ', 1)[1][:400]}")
    evidence_dir = deps.evidence_dir or EVIDENCE_DIR
    evidence = evidence_path(evidence_dir, graded, to, seeds[0])
    evidence.parent.mkdir(parents=True, exist_ok=True)
    keep_earlier(evidence)
    head = (f"LIVE CHAIN HELD-OUT - {'GRADED' if graded else 'DEVELOPMENT, NOT GRADED, NO PASS'} - VERDICT {shown}"
            f"{' (failing: ' + ', '.join(failing) + ')' if failing and not aborted else ''} (to {to}; driver "
            f"ai_player/gates/live_chain.py; build spec {SPEC})")
    not_run = [f"{c['chain']} {leg['leg']}: {leg.get('reason')}" for c in chains for leg in c["legs"]
               if leg.get("status") in ("NOT RUN", "REFUSED")]
    flagged = [f"{c['chain']} {leg['leg']} {((leg.get('measures') or {}).get('log') or {}).get('multichoice')}"
               for c, leg in ran_legs(chains) if ((leg.get("measures") or {}).get("log") or {}).get("multichoice")]
    text = [head, f"date: {began} -> {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}", *ledger_lines,
            f"numbers sha256: {sha} (seeds {seeds[0]}-{seeds[1]}; {args.purpose}; {chains_n} chains; at least {reach_min} "
            f"to reach)"]
    if development:
        text += [f"PREDICTION (sha256 {development['prediction_sha256']}, in the numbers, registered before the runs): "
                 f"{prediction}", f"leg budgets overridden: {development['leg_frames_override'] or 'none'}"]
    text += [f"build root: {build_root}   out: {out}   free at start: {facts['free']:.1f} GB",
             f"frozen tree: {frozen_line}", f"leftover processes: {left_procs or 'none'}",
             f"the most chains running at once: {plan['most_running']} (launch order {plan['order']})",
             f"NOT RUN: {not_run or 'none'}", f"guard and watchdog events: {events or 'none'}",
             f"legs with an unexpected-multichoice line: {flagged or 'none'}",
             f"VERDICT: {shown}" + (" (the checks below are information: a harness abort is no PASS and no FAIL)"
                                     if aborted else ""),
             "checks (registered in the bounds text below; each quotes both values):", *check_lines(checks), "",
             "per chain and leg:"]
    for chain in chains:
        text.append(f"  {chain['chain']} ({chain.get('personality')}, {chain.get('starter')}, seed {chain.get('seed')}, "
                    f"profile {chain.get('profile')}): reached {to} {chain_reaches(chain, len(legs))}; stopped at "
                    f"{chain.get('stopped_at')}: {chain.get('stop_reason')}")
        for leg in chain["legs"]:
            text += leg_lines(leg)
    text += ["", "BOUNDS TEXT (hashed into the registration):", numbers["bounds_text"]]
    evidence.write_text("\n".join(text) + "\n", encoding="utf-8")
    _write_json(out / "results.json", {"began": began, "ended": time.strftime("%Y-%m-%d %H:%M:%S"),
                                       "purpose": args.purpose, "run": args.run if graded else None, "to": to,
                                       "chains": chains_n, "seeds": list(seeds), "numbers_sha256": sha,
                                       "ledger": entry["id"], "frozen": [held and not tree.moves, frozen_line],
                                       "leftover": left_procs, "not_run": not_run, "events": events,
                                       "most_running": plan["most_running"], "verdict": shown, "reach_min": reach_min,
                                       "legs": legs, "jobs": jobs, "world_left": world_left,
                                       "reported": {"profiles": profiles, "main_profile": main, "optional": optional},
                                       "checks": check_rows(checks), "evidence": str(evidence)})
    reference = (str(evidence.resolve().relative_to(REPO)).replace("\\", "/") if evidence.resolve().is_relative_to(REPO)
                 else str(evidence))
    ledger.finish(entry["id"], verdict_line, reference, path=deps.ledger_path or ledger.LEDGER)
    print(f"[LC] evidence: {evidence}", flush=True)
    for line in check_lines(checks):
        print(f"[LC] {line.strip()}", flush=True)
    print(f"[LC] OVERALL {shown} ({label}); ledger #{entry['id']} finished", flush=True)
    if aborted:
        return 3
    return 0 if (result == "PASS" or not graded) else 1


def leg_lines(leg: dict) -> list[str]:
    """One leg's evidence block."""
    if leg.get("status") in ("NOT RUN", "REFUSED"):
        return [f"    {leg['leg']} {leg['target']}: {leg['status']} - {leg.get('reason')}"]
    stop = leg.get("harness_stop") or {}
    m = leg.get("measures") or {}
    log, world = m.get("log") or {}, m.get("world") or {}
    statuses = {c["id"]: c["status"] for c in leg.get("checks") or []}
    purity = "CLEAN" if all(statuses.get(i) == PASS for i in PURITY_IDS) else \
        {i: statuses.get(i) for i in PURITY_IDS if statuses.get(i) != PASS}
    return [f"    {leg['leg']} {leg['target']} ({leg['status']}): proof before {proof_text(leg.get('proof_before'))} -> "
            f"after {proof_text(leg.get('proof_after'))}; reached {leg.get('reached')}"
            f"{' (ALREADY HELD at its start)' if leg.get('already_held') is True else ''}; real frames "
            f"{stop.get('real_frames')} of {leg.get('frames')}; {leg.get('elapsed')} s of {leg.get('wall')}; stop by "
            f"{stop.get('by')} ({stop.get('cause')})",
            f"      purity {purity}; THIS_RUN {statuses.get('L5.THIS_RUN')}; custody {leg.get('custody') or 'held'}; "
            f"continue {leg.get('continue')}: {leg.get('why')}",
            f"      world.jsonl {(leg.get('world_file') or {}).get('bytes')} B, {world.get('lines')} lines "
            f"({world.get('bad_lines')} bad), last line {world.get('last_bytes')} B ok {world.get('last_ok')}, deleted "
            f"{(leg.get('world_file') or {}).get('deleted')}; kept {leg.get('kept_world')}",
            f"      unexpected lines {log.get('unexpected')} (multichoice {log.get('multichoice')}, forms "
            f"{log.get('forms')}); first {log.get('first_unexpected')!r}",
            f"      the AI's outcome {leg.get('outcome')!r}; memory line {((log.get('memory') or {}).get('line') or '')[:300]!r}",
            f"      run dir {leg.get('run_dir')}; notes {leg.get('notes') or 'none'}"]


def grade_dir(out: Path) -> int:
    results = json.loads((out / "results.json").read_text(encoding="utf-8"))
    chains = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "rows").glob("*.json"))]
    legs, jobs = results["legs"], results["jobs"]
    rep = results.get("reported") or {}
    checks = grade_batch(chains, jobs, len(legs), results["reach_min"], tuple(results["frozen"]), results.get("leftover"),
                         {"world_left": [w for w in results.get("world_left") or [] if "could not" in w],
                          "profiles": rep.get("profiles"), "main_profile": rep.get("main_profile"),
                          "optional": rep.get("optional"), "most_running": results.get("most_running")})
    for line in check_lines(checks):
        print(line)
    print(f"OFFLINE RE-GRADE (no ledger write): {batch_verdict(checks)} over {len(chains)} chains")
    return 0


def read_leg(run_dir: Path, truth: bool = False) -> dict:
    """One leg folder, READ ONLY: its log counts, its world.jsonl streamed (no copy kept, nothing deleted), and with
    `truth` the harness's truth of its end_state.ss1 against every chapter end's proof."""
    out: dict = {"log": read_log_counts(run_dir / "ai_player.log"), "world": None, "proofs": None}
    world = run_dir / "world.jsonl"
    if world.is_file():
        out["world"] = stream_world_tail(world, None)
    if truth and (run_dir / "end_state.ss1").is_file():
        from ai_player.gates import live_step5 as L5

        found, raw = L5.truth_of(run_dir / "end_state.ss1")
        marks = ((found or {}).get("story") or {}).get("marks")
        data = load_milestones()
        ends = {}
        for m in data["milestones"]:
            if not m.get("optional") and m.get("waypoint") is None:
                ends[m["chapter"]] = m
        out["proofs"] = {m["id"]: proof_holds(marks, {"flags": m["done"].get("flags") or {},
                                                      "variables": m["done"].get("variables") or {},
                                                      "trainers": m["done"].get("trainers") or {}})
                         for m in ends.values()} if marks else f"no truth: {raw[-400:]}"
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("bounds")
    p.add_argument("--run")
    p.add_argument("--to")
    p.add_argument("--first-seed", type=int)
    p.add_argument("--chains", type=int, choices=(3, 6))
    p.add_argument("--leg-frames")
    p = sub.add_parser("register")
    p.add_argument("--run", required=True)
    p.add_argument("--note-file")
    p = sub.add_parser("run")
    p.add_argument("--purpose", choices=("graded", "development"), required=True)  # NO default (spec section 7)
    p.add_argument("--run")
    p.add_argument("--first-seed", type=int)
    p.add_argument("--to")
    p.add_argument("--chains", type=int, choices=(3, 6))
    p.add_argument("--leg-frames")
    p.add_argument("--prediction-file")
    p.add_argument("--out", required=True)
    p.add_argument("--build-root")
    p = sub.add_parser("grade")
    p.add_argument("dir")
    p = sub.add_parser("read")
    p.add_argument("run_dir")
    p.add_argument("--truth", action="store_true")
    p = sub.add_parser("child")
    p.add_argument("job")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    args = build_parser().parse_args(argv)
    if args.cmd == "child":
        return child(Path(args.job))
    if args.cmd == "bounds":
        if args.run:
            spec = GRADED_RUNS[args.run]
            to, first, chains, override = spec["to"], spec["seeds"][0], 6, {}
        else:
            to, first, chains = args.to, args.first_seed or 1, args.chains or 3
        legs = legs_of(to, load_milestones())
        if not args.run:
            override = parse_leg_frames(args.leg_frames, legs)
            legs = [{**leg, "frames": override.get(leg["leg"], leg["frames"])} for leg in legs]
        numbers = registered_numbers(args.run, to, seeds_of(first, chains), chains, legs)
        print(numbers["bounds_text"])
        print(json.dumps({k: v for k, v in numbers.items() if k != "bounds_text"}, indent=1))
        print(f"BOUNDS TEXT sha256 {hashlib.sha256(numbers['bounds_text'].encode('utf-8')).hexdigest()}")
        print(f"REGISTERED NUMBERS sha256 {ledger.numbers_sha256(numbers)}")
        return 0
    if args.cmd == "register":
        if args.run not in GRADED_RUNS:
            print(f"REFUSED: --run {args.run!r} is not one of {sorted(GRADED_RUNS)}")
            return 2
        spec = GRADED_RUNS[args.run]
        seeds = spec["seeds"]
        named = [e for e in seeds_named(*seeds) if not (e["driver"] == DRIVER and e["status"] == "registered")]
        if named:
            print(f"REFUSED: ledger entries already name seeds {seeds[0]}-{seeds[1]}: {[e['id'] for e in named]}")
            return 2
        legs = legs_of(spec["to"], load_milestones())
        numbers = registered_numbers(args.run, spec["to"], seeds, 6, legs)
        note = (Path(args.note_file).read_text(encoding="utf-8").strip() if args.note_file else
                f"LIVE CHAIN graded held-out (USER RULING 55), run {args.run}, to {spec['to']}, driver "
                f"ai_player/gates/live_chain.py: registered BEFORE any run; the bounds field is the sha256 of "
                f"registered_numbers() (the bounds text, the legs and proofs, every constant, the milestones', the AI "
                f"code's and the grader files' sha256)")
        print(numbers["bounds_text"])
        entry = register(seeds, numbers, note)
        print(f"REGISTERED numbers sha256 {ledger.numbers_sha256(numbers)}")
        print("ENTRY " + json.dumps(entry, ensure_ascii=False))
        return 0
    if args.cmd == "run":
        return run_batch(args)
    if args.cmd == "grade":
        return grade_dir(Path(args.dir))
    if args.cmd == "read":
        print(json.dumps(read_leg(Path(args.run_dir), args.truth), indent=1, default=str))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
