"""LIVE PROOF of AI-player build step 5: the AI plays the STORY itself (USER RULING 37: badge 1 in 4 chapters; an OFFICIAL
acceptance run starts from a REAL New Game, naming and clock included). Test side.

    py -3.12 ai_player/gates/live_step5.py [--arms CH1T,CH1C,CH1M,CH2] [--evidence-tag step5]
    exit 0 = every arm PASS and no leftover emulator process

Every arm runs the REAL package through the real launcher (`py -3.12 -m ai_player run`: the purity gate first, the
instrument, the verdict file), brain `play` (`mode.py` HandsBrain._play: the goal manager `brain/goals.py`, the personality
`personality.py`, the story skills `skills/story.py`), and is graded three ways, every check quoting both values:
  PURITY  CLEAN, every breach counter 0, `ai_presses` == 2 x the pad's presses, the pad's frames == `real_frames`,
          `ai_bot_calls` 0, and the run ENDED BY ITSELF with "play: done: <target> reached" within its PRE-REGISTERED frames;
  HANDS   every press has its gate; every A is a WAIT, a MENU confirm (the starter's bag included) or a TALK, by its look;
          no stretch standing still under the catch-all reason; the brain always had a goal with a reason;
  THE GAME by a SECOND PATH from the state the run left (`gates/play_harness.py truth`: the harness's own reads of save
          block 1's milestone flags and vars at the decomp-checked numbers, the game's own counters (steps, wild and trainer
          battles, captures, POKéMON CENTER uses), the item balls' flags, the party by PID with its OT id, the bag, the name
          and gender in save block 2), never the AI's eyes; the state asserted to be THIS run's.

THE ARMS
  CH1T, CH1C, CH1M   chapter 1 from a REAL NEW GAME (`--fresh`: the title screen, the AI names itself, sets the clock),
                     one per STARTER (TREECKO, TORCHIC, MUDKIP: `AI_PLAYER_STARTER`) and one per PERSONALITY (Story,
                     Catcher, Trainer), target `ch1_pokedex`. CLAIMS (pre-registered in `PREDICTED`): the POKéDEX flag set
                     (RECEIVED_POKEDEX_FROM_BIRCH, SYS_POKEDEX_GET, ADVENTURE_STARTED) and the rival's (DEFEATED_RIVAL_ROUTE103)
                     and the clock's (SET_WALL_CLOCK); the starter named is the party's first Pokemon, the player's own (OT);
                     the name and gender in the save are the intro's intent recomputed here from `personality.py`; TRAINED
                     BEFORE THE RIVAL: at least `T` training steps in its TRAINING roams for the rival before its rival
                     milestone (the roams a rest or an item ball stopped included) and at least `N` wild battles WON inside
                     them (the step-5 verifier's round 2: won anywhere between the starter and the rival, an arm that never
                     trains passed in 6 seeds of 10; the GAME's count inside the same windows is the sweep's, which has a
                     second path while it plays), and its told wild battles in all == the game's GAME_STAT_WILD_BATTLES (the
                     second path agrees with the AI's count); THE REST RULE: no training roam played on after a battle that
                     left the party under its personality's heal_below, and the three arms had at least one such occasion
                     together (not vacuous); ITS END LINE: its battles lost == its log's == the play loop's TOLD losses (round
                     2), and its training counts for the rival == its log's (the verifier found both false); at most
                     `SPINS_PER_RUN` back-and-forth spins in its roaming,
                     and the three arms' spins together under 2 % of their training steps (step 4.1 round 3's criterion: a
                     per-run "< 2 %" fails 2 spins in 100 steps); frames within the bound.
  CH2                chapter 2 (stretch) from the state the CH1C arm LEFT (the AI's own presses only) and its world memory
                     (`AI_PLAYER_WORLD`): target `ch2_wally`. CLAIMS: HIDE_PETALBURG_CITY_WALLYS_MOM set and
                     VAR_PETALBURG_GYM_STATE >= 2 (WALLY's tutorial played); at least 2 new species CAUGHT (the game's
                     GAME_STAT_POKEMON_CAPTURES and new PIDs with the player's OT); at least 1 nurse heal (the game's
                     GAME_STAT_USED_POKECENTER); at least 1 item ball picked up (its FLAG_ITEM_* set); POKé BALLS bought
                     (its told purchase, the money and the bag by the second path).
The fault arms (no training before the rival; no hints; the rest rule's fix removed; the MAX_LOSSES stop and the loop's
count removed) are the seed sweep's (`gates/rate_step5.py` NOTRAIN, NOHINTS, DEADREST, STOP, STOPDEAD): a win RATE and a
slowdown are frequency claims, which a sweep answers (CLAUDE.md rule 9).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.live_step2 import check_purity, classify_a, clean_env, run_json  # noqa: E402
from ai_player.gates.provenance import keep_earlier, provenance as tree_provenance  # noqa: E402
from ai_player.gates.rate_step5 import roam_breaches, training_windows  # noqa: E402
from ai_player.hands.dialogue import GENERIC_BUSY  # noqa: E402
from ai_player.host import launcher  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_CLOCK, ENV_PERSONALITY, ENV_SEED, ENV_STARTER, ENV_TARGET, ENV_WORLD,
)
from ai_player.personality import choose_gender, choose_name, pick_personality  # noqa: E402

GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
PROFILE = "ai-step5-play"
HARNESS = GATES / "play_harness.py"
FRAME_SLACK = 5
#: step 4.1 round 3's `ROAM_SPINS_PER_SEED` (`rate_step3.py`): the most back-and-forth spins one run's roaming may hold
SPINS_PER_RUN = 5
#: The wall clock the AI sets in its room (the cartridge's own clock reads the HOST's time in a launcher run).
WALL_CLOCK = "10:00"
#: PRE-REGISTERED (module docstring): the claims' numbers, set from development runs of this code BEFORE the graded run
#: (in-process, `gates/play_harness.py`; the README's step-5 section names them). `frames_max` bounds the run; `train_steps`
#: and `wild_before` are the T and N of "trained before the rival".
PREDICTED: dict[str, dict] = {
    # (the step-5 verifier's round, 2026-10-14) `wild_won`: wild battles WON (a battle FLED is not training); round 2: WON
    # INSIDE ITS TRAINING ROAMS for the rival (between the starter and the rival, an arm that never trains won >= 3 in 6
    # seeds of 10: walks win battles too). `train_steps`: the training roams' steps. Numbers carried over from round 1;
    # measured in round 1's three arms by the verifier, 11 / 6 / 11 won inside training
    "CH1T": {"frames_max": 300000, "train_steps": 60, "wild_won": 3},
    "CH1C": {"frames_max": 300000, "train_steps": 60, "wild_won": 3},
    "CH1M": {"frames_max": 300000, "train_steps": 60, "wild_won": 3},
    "CH2": {"frames_max": 300000, "caught": 2, "heals": 1, "items": 1},
}


@dataclass
class Arm:
    name: str
    title: str
    frames: int
    wall: float
    env: dict[str, str] = field(default_factory=dict)
    seed: int = 1
    fresh: bool = True
    state_from: str | None = None  # another arm whose end state (and world memory) this one starts from
    brain: str = "play"


@dataclass
class Run:
    arm: Arm
    command: list[str] = field(default_factory=list)
    exit_code: int = -1
    elapsed: float = 0.0
    started: float = 0.0
    stdout: str = ""
    run_dir: Path | None = None
    verdict: dict | None = None
    records: list[dict] = field(default_factory=list)
    ai_log: str = ""
    before: dict | None = None
    after: dict | None = None
    state_mtime: float | None = None
    start_state: Path | None = None
    checks: list[tuple[bool, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    measures: dict = field(default_factory=dict)

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)

    @property
    def presses(self) -> list[dict]:
        return [r for r in self.records if str(r.get("action", "")).startswith(("press ", "hold "))]

    @property
    def outcome(self) -> str:
        return ((self.verdict or {}).get("facts") or {}).get("exit_reason") or ""


def play_env(personality: str, starter: str | None, target: str, **extra: str) -> dict[str, str]:
    env = {ENV_PERSONALITY: personality, ENV_TARGET: target, ENV_CLOCK: WALL_CLOCK, **extra}
    if starter:
        env[ENV_STARTER] = starter
    return env


ARMS: list[Arm] = [
    Arm("CH1T", "chapter 1 from a real New Game, TREECKO, Story: the POKéDEX, having trained before the rival", 330000,
        3600.0, play_env("Story", "TREECKO", "ch1_pokedex"), seed=11),
    Arm("CH1C", "chapter 1 from a real New Game, TORCHIC, Catcher: the POKéDEX, having trained before the rival", 330000,
        3600.0, play_env("Catcher", "TORCHIC", "ch1_pokedex"), seed=12),
    Arm("CH1M", "chapter 1 from a real New Game, MUDKIP, Trainer: the POKéDEX, having trained before the rival", 330000,
        3600.0, play_env("Trainer", "MUDKIP", "ch1_pokedex"), seed=13),
    Arm("CH2", "chapter 2 (stretch) from the CH1C arm's own end: Oldale's balls, ROUTE 102, PETALBURG, DAD, WALLY's tutorial",
        330000, 3600.0, play_env("Catcher", None, "ch2_wally"), seed=12, fresh=False, state_from="CH1C"),
]


# ---------------------------------------------------------------------- running
def truth_of(state: Path) -> tuple[dict | None, str]:
    return run_json([sys.executable, str(HARNESS), "truth", str(state)], "TRUTH", clean_env({}), 600)


def run_arm(arm: Arm, build_root: Path, carried: dict[str, tuple[Path, Path]]) -> Run:
    run = Run(arm)
    profile_dir, _ = launcher.ensure_profile(build_root, PROFILE)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {PROFILE} is not ai_player-owned; refusing to touch it")
    launcher.force_http_off(profile_dir)
    cheats = profile_dir / "game_cheats.yml"
    if cheats.exists():
        cheats.unlink()
    run.run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    env_extra = {}
    start = ["--fresh"]
    if arm.state_from is not None:
        if arm.state_from not in carried:
            run.notes.append(f"the arm {arm.state_from} it starts from left no state: not run")
            return run
        state, world = carried[arm.state_from]
        run.start_state = state
        start = ["--state", str(state)]
        env_extra[ENV_WORLD] = str(world)
        run.before, raw = truth_of(state)
        if run.before is None:
            run.notes.append(f"truth of the start state failed: {raw[-1500:]}")
    run.command = [sys.executable, "-m", "ai_player", "run", "--profile", PROFILE, "--frames", str(arm.frames),
                   "--wall-seconds", f"{arm.wall:g}", "--build-root", str(build_root), "--run-dir", str(run.run_dir), *start]
    env = clean_env({ENV_BRAIN: "play", ENV_SEED: str(arm.seed), **arm.env, **env_extra})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    run.started = time.time()
    began = time.monotonic()
    proc = subprocess.Popen(run.command, cwd=str(REPO), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, creationflags=flags)
    try:
        raw_out, _ = proc.communicate(timeout=arm.wall + 300)
    except subprocess.TimeoutExpired:
        launcher.kill_tree(proc)
        raw_out, _ = proc.communicate()
        raw_out = (raw_out or b"") + b"\n[DRIVER] the run overran the driver's own wall clock; process tree killed\n"
    run.elapsed = time.monotonic() - began
    run.exit_code = proc.returncode if proc.returncode is not None else -9
    run.stdout = raw_out.decode("utf-8", errors="replace")
    run.verdict = launcher.read_verdict(run.run_dir)
    actions = run.run_dir / "actions.jsonl"
    if actions.is_file():
        for line in actions.read_text(encoding="utf-8").splitlines():
            try:
                run.records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    log = run.run_dir / "ai_player.log"
    if log.is_file():
        run.ai_log = log.read_text(encoding="utf-8", errors="replace")
    state = profile_dir / launcher.STATE_FILE
    if state.is_file():
        run.state_mtime = state.stat().st_mtime
        keep = run.run_dir / "end_state.ss1"
        shutil.copy2(state, keep)
        run.after, raw = truth_of(keep)
        if run.after is None:
            run.notes.append(f"truth of the state left behind failed: {raw[-1500:]}")
        world = run.run_dir / "world.jsonl"
        if world.is_file():
            carried[arm.name] = (keep, world)
    return run


# ---------------------------------------------------------------------- shared checks
def marks(truth: dict | None) -> dict:
    return ((truth or {}).get("story") or {}).get("marks") or {}


def stats(truth: dict | None) -> dict:
    return ((truth or {}).get("story") or {}).get("stats") or {}


def items(truth: dict | None) -> dict:
    return ((truth or {}).get("story") or {}).get("items") or {}


def check_after_is_this_run(run: Run) -> None:
    after = run.after or {}
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    start_frame = (run.before or {}).get("frame") or 0
    frame = after.get("frame")
    written = run.state_mtime is not None and run.state_mtime >= run.started - 1.0
    near = isinstance(frame, int) and frames > 0 and abs(frame - (start_frame + frames)) <= FRAME_SLACK
    before_md5 = (run.before or {}).get("state_md5")
    run.check(bool(after) and written and near and after.get("state_md5") != before_md5,
              f"the state graded is the one THIS run wrote: written "
              f"{'%.1fs after the run started' % (run.state_mtime - run.started) if run.state_mtime else 'NEVER'}; frame "
              f"{frame} == start {start_frame} + {frames} real frames (+-{FRAME_SLACK}); md5 {after.get('state_md5')} "
              f"(start {before_md5 or '-: a fresh boot'})")


def check_hands(run: Run) -> None:
    presses = run.presses
    no_gate = [p for p in presses if not p.get("reason")]
    run.check(bool(presses) and not no_gate, f"{len(presses)} presses in the action log, every one with its gate (without: {len(no_gate)})")
    kinds: dict[str, int] = {}
    menus: dict[str, int] = {}
    wrong = []
    for press in (p for p in presses if p["action"].startswith("press A ")):
        kind, ok = classify_a(press)
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind == "menu":
            name = str(press.get("reason")).split(" cursor on")[0]
            menus[name] = menus.get(name, 0) + 1
        if not ok:
            wrong.append((press["frame"], kind, str(press["reason"])[:60], (press.get("digest") or "")[:90]))
    run.check(not wrong, f"EVERY A press is a WAIT, a MENU confirm or a TALK by its look: {dict(sorted(kinds.items()))}, "
                         f"the menus {dict(sorted(menus.items()))}; any other: {wrong[:4] or 'none'}")
    blind = [p for p in presses if "NONE" in str(p.get("reason"))]
    run.check(not blind, f"no press without the eyes asked (a 'NONE' gate): {len(blind)}")
    idle = [r for r in run.records if r.get("decision") == "watch"]
    generic = [(r["frame"], r["reason"]) for r in idle if str(r.get("reason", "")).startswith(GENERIC_BUSY)]
    run.check(not generic, f"{len(idle)} stretches standing still, NONE under the catch-all {GENERIC_BUSY!r}: {generic[:3] or 'none'}")
    goals = [r for r in run.records if r.get("decision") == "goal"]
    empty = [r for r in goals if not str(r.get("reason", "")).strip()]
    run.check(bool(goals) and not empty, f"NEVER WITHOUT A GOAL: {len(goals)} goals chosen, each with its reason (without: "
                                         f"{len(empty)}); kinds {count(r['action'] for r in goals)}")


def count(values) -> dict:
    out: dict = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def tells(run: Run, text: str) -> list[dict]:
    return [r for r in run.records if r.get("decision") == "tell" and text in str(r.get("reason", ""))]


def milestone_frame(run: Run, milestone: str) -> int | None:
    hit = next((r for r in tells(run, f"MILESTONE {milestone} done at f")), None)
    return hit.get("frame") if hit else None


def roams(run: Run) -> list[dict]:
    return [r for r in run.records if r.get("decision") == "roam" and r.get("action") == "metrics"]


def wild_battles(run: Run) -> list[dict]:
    return tells(run, "battle: a wild battle against")


def is_battle(record: dict) -> bool:
    extra = record.get("extra") or {}
    return record.get("decision") == "world" and "kind" in extra and "outcome" in extra


def battle_records(run: Run) -> list[dict]:
    """The navigator's record of every battle its battler played (`brain/navigator.py` handle: its kind as the eyes showed
    it during the battle, its outcome, the party's HP at its start and end)."""
    return [r for r in run.records if is_battle(r)]


def end_note(run: Run) -> dict:
    """The play brain's own end record (`mode.py` _play_end): its fight preparation, losses, drift."""
    return next(((r.get("extra") or {}) for r in reversed(run.records)
                 if r.get("decision") == "end" and "fight_prep" in (r.get("extra") or {})), {})


def check_rest_rule(run: Run) -> None:
    """(the step-5 verifier's DEAD FIX, 2026-10-14) No training or catching roam played on after a battle that left the
    party under the personality's heal_below (`rate_step5.roam_breaches`); the occasions are reported, so a pass with none
    is seen to be vacuous."""
    breaches, occasions = roam_breaches(run.records)
    rests = [r for r in run.records if r.get("decision") == "roam" and "rest:" in str((r.get("extra") or {}).get("stopped"))]
    run.check(not breaches, f"THE REST RULE (its log): battles a roam played after one that ended under the personality's "
                            f"heal_below: {len(breaches)} {breaches[:3]} (bound 0), over {occasions} such ends; roams stopped "
                            f"by a rest {len(rests)}")
    run.measures.update({"rest_breaches": len(breaches), "rest_occasions": occasions, "rests": len(rests)})


def training_battles(run: Run, fight: str) -> tuple[int, int]:
    """The wild battles its log records inside its TRAINING roams for `fight` (`rate_step5.training_windows`: from a train
    goal's "roam N steps" record to that roam's metrics record): (met, won)."""
    windows = training_windows(run.records, fight)
    inside = [r for r in battle_records(run) if r["extra"].get("kind") == "wild"
              and any(start <= (r.get("frame") or -1) <= end for start, end in windows)]
    return len(inside), sum(1 for r in inside if r["extra"].get("outcome") == "won")


def check_own_report(run: Run, fight: str | None) -> None:
    """(the step-5 verifier's round) The AI's END LINE tells the truth of its own log: its battles lost == the battles
    its log records as lost (every one, inside a goal or not: `mode.py` MAX_LOSSES) == the play loop's TOLD losses (round
    2: the end line recounted, so it agreed even with the loop's count removed; only the loop's count tells them), and,
    before `fight`, its counts of the wild battles met and won while training == the battle records inside its training
    roams for that fight."""
    note = end_note(run)
    records = battle_records(run)
    lost = [r for r in records if r["extra"].get("outcome") == "lost"]
    told = [r for r in run.records if r.get("decision") == "tell" and str(r.get("reason", "")).startswith("a battle was LOST (")]
    run.check(bool(note) and note.get("losses") == len(lost) == len(told),
              f"ITS END LINE'S LOSSES ({note.get('losses')}) == the battles its log records as lost ({len(lost)}: "
              f"{[r.get('frame') for r in lost]}) == the play loop's told losses ({len(told)}: "
              f"{[str(r.get('reason'))[:40] for r in told]})")
    if fight is None:
        return
    prep = (note.get("fight_prep") or {}).get(fight) or {}
    wild, won = training_battles(run, fight)
    run.check(prep.get("wild") == wild and prep.get("won") == won and wild > 0,
              f"ITS END LINE'S TRAINING ({fight}: {prep}) == its log's wild battles in its training roams for it: met {wild}, "
              f"won {won} (and more than 0: the count the verifier found always 0)")


def intent_of(arm: Arm) -> tuple[str, str]:
    """The intro's gender and name for this arm, recomputed from `personality.py` (the brain's CHOICES stream: the
    personality the run names takes no draw)."""
    choices = random.Random(f"{arm.seed}:choices")
    personality = pick_personality(choices, arm.seed, arm.env.get(ENV_PERSONALITY))
    gender, _ = choose_gender(choices, personality)
    return gender, choose_name(choices, gender)


# ---------------------------------------------------------------------- graders
def grade_common(run: Run, target: str) -> None:
    check_purity(run, f"done: {target} reached")
    check_after_is_this_run(run)
    check_hands(run)
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames")
    bound = PREDICTED[run.arm.name]["frames_max"]
    run.check(isinstance(frames, int) and frames <= bound, f"BOUNDED: {frames} real frames <= the pre-registered {bound}")
    run.measures["frames"] = frames
    run.measures["goals"] = count(r["action"] for r in run.records if r.get("decision") == "goal")


def grade_CH1(run: Run) -> None:
    arm, after = run.arm, run.after
    grade_common(run, "ch1_pokedex")
    m = marks(after)
    proofs = {name: m.get(name) for name in ("RECEIVED_POKEDEX_FROM_BIRCH", "SYS_POKEDEX_GET", "ADVENTURE_STARTED",
                                             "DEFEATED_RIVAL_ROUTE103", "SET_WALL_CLOCK", "RESCUED_BIRCH", "SYS_POKEMON_GET")}
    run.check(all(proofs.values()), f"THE GAME (save block 1, the harness's own read): {proofs}")
    gender, name = intent_of(arm)
    run.check((after or {}).get("name") == name and (after or {}).get("gender_name") == gender,
              f"THE GAME (save block 2): name {(after or {}).get('name')!r} gender {(after or {}).get('gender_name')} == the intro's "
              f"intent {name!r} {gender} (recomputed from personality.py for seed {arm.seed})")
    party = (after or {}).get("party_exp") or []
    owner = {row[0]: row[1] for row in (after or {}).get("party_ot") or []}
    starter = arm.env[ENV_STARTER]
    first = party[0] if party else None
    run.check(first is not None and first[1].upper() == starter and owner.get(first[0]) == (after or {}).get("player_tid"),
              f"THE GAME (the framework's party decoder): the first Pokemon {first} is the {starter} the run named, its OT "
              f"{owner.get(first[0]) if first else None} == the player's {(after or {}).get('player_tid')}")
    balls = (after or {}).get("balls") or {}
    run.check(sum(balls.values()) >= 5, f"THE GAME (the bag): POKé BALLS {balls} (the rival's 5 after the POKéDEX)")
    rival = milestone_frame(run, "ch1_rival_route103")
    starter_done = milestone_frame(run, "ch1_starter")
    # (the step-5 verifier's round 2: "wild battles WON between the starter and the rival" is met by an arm that never
    # trains: walks win battles too) the TRAINING ROAMS for the rival (`rate_step5.training_windows`), before it: their
    # steps (the roam reports) and the wild battles won INSIDE them. The GAME's own count of both inside the same windows
    # is the sweep's (`rate_step5.py`: a live run has no second path while it plays); here the game agrees with the
    # AI's battle count over the whole run (below)
    windows = [w for w in training_windows(run.records) if rival is not None and w[0] <= rival]
    before = [r for r in roams(run) if any(start <= (r.get("frame") or -1) <= end for start, end in windows)]
    steps = sum((r.get("extra") or {}).get("steps", 0) for r in before)
    wild_before = [r for r in wild_battles(run) if rival is not None and (r.get("frame") or 0) <= rival]
    fought = [r for r in battle_records(run) if rival is not None and starter_done is not None
              and starter_done < (r.get("frame") or 0) <= rival and r["extra"].get("kind") == "wild"]
    met_training, won_training = training_battles(run, "ch1_rival_route103")
    want = PREDICTED[arm.name]
    run.check(rival is not None and steps >= want["train_steps"] and won_training >= want["wild_won"],
              f"TRAINED BEFORE THE RIVAL (its log: its {len(windows)} TRAINING roam(s) for the rival, before its rival "
              f"milestone at f{rival}): {steps} training steps in them, the stopped ones included (>= {want['train_steps']}), "
              f"and {won_training} wild battles WON inside them (>= {want['wild_won']}; of {met_training} met there). "
              f"Reported, not a training check: between its starter milestone at f{starter_done} and the rival, "
              f"{count(r['extra'].get('outcome') for r in fought)} of the {len(fought)} wild battles there; "
              f"{len(wild_before)} met before the rival in all")
    check_rest_rule(run)
    check_own_report(run, "ch1_rival_route103")
    told = len(wild_battles(run))
    game = stats(after).get("wild_battles")
    run.check(told == game, f"THE GAME AGREES WITH ITS COUNT: its told wild battles in all {told} == GAME_STAT_WILD_BATTLES "
                            f"{game} (the harness's own read of save block 1's counters)")
    all_steps = sum((r.get("extra") or {}).get("steps", 0) for r in roams(run))
    spins = sum((r.get("extra") or {}).get("spins", 0) for r in roams(run))
    ratio = spins / all_steps if all_steps else 1.0
    # step 4.1 round 3's criterion (`rate_step3.py` ROAM_SPINS_PER_SEED): at most 5 spins in one run, and the CH1 arms'
    # spins TOGETHER under 2 % of their training steps (`main`); a per-run "< 2 %" fails 2 spins in 100 steps
    run.check(all_steps > 0 and spins <= SPINS_PER_RUN, f"ROAMING, NOT SPINNING: {spins} spins over {all_steps} training "
                                                        f"steps = {ratio:.4f} (at most {SPINS_PER_RUN} spins in a run; the CH1 "
                                                        f"arms together under 2 %: the overall line)")
    run.measures.update({"rival_frame": rival, "train_steps_before": steps, "wild_before": len(wild_before),
                         "wild_won_training": won_training, "wild_met_training": met_training,
                         "wild_won_starter_to_rival": sum(1 for r in fought if r["extra"].get("outcome") == "won"),
                         "wild_total": told, "spin_ratio": round(ratio, 4), "spins": spins,
                         "roam_steps": all_steps, "game_stats": stats(after)})


def grade_CH2(run: Run) -> None:
    before, after = run.before, run.after
    grade_common(run, "ch2_wally")
    m = marks(after)
    run.check(m.get("HIDE_PETALBURG_CITY_WALLYS_MOM") == 1 and (m.get("VAR_PETALBURG_GYM_STATE") or 0) >= 2,
              f"THE GAME: WALLY's tutorial: HIDE_PETALBURG_CITY_WALLYS_MOM {m.get('HIDE_PETALBURG_CITY_WALLYS_MOM')}, "
              f"VAR_PETALBURG_GYM_STATE {m.get('VAR_PETALBURG_GYM_STATE')} (>= 2)")
    want = PREDICTED["CH2"]
    caught = stats(after).get("captures", 0) - stats(before).get("captures", 0)
    pids_before = {row[0] for row in (before or {}).get("party_exp") or []} | {row[0] for row in (before or {}).get("boxes") or []}
    tid = (after or {}).get("player_tid")
    new = [row for row in (after or {}).get("party_ot") or [] if row[0] not in pids_before and row[1] == tid]
    new += [row for row in (after or {}).get("boxes") or [] if row[0] not in pids_before and row[1] == tid]
    run.check(caught >= want["caught"] and len(new) >= want["caught"],
              f"CAUGHT: GAME_STAT_POKEMON_CAPTURES +{caught} and {len(new)} new PIDs with the player's OT {tid}: {new} "
              f"(>= {want['caught']})")
    heals = stats(after).get("used_pokecenter", 0) - stats(before).get("used_pokecenter", 0)
    run.check(heals >= want["heals"], f"HEALED: GAME_STAT_USED_POKECENTER +{heals} (>= {want['heals']})")
    picked = [name for name, value in items(after).items() if value and not items(before).get(name)]
    run.check(len(picked) >= want["items"], f"ITEMS: item-ball flags newly set {picked} (>= {want['items']})")
    check_rest_rule(run)
    check_own_report(run, None)
    bought = tells(run, "done; POKé BALL in the bag")
    run.check(bool(bought), f"SHOPPED (its told purchase): {[str(r['reason'])[:120] for r in bought[:2]]}; money "
                            f"{(before or {}).get('money')} -> {(after or {}).get('money')}, balls {(before or {}).get('balls')} -> "
                            f"{(after or {}).get('balls')}")
    run.measures.update({"caught": caught, "heals": heals, "items": picked, "game_stats": stats(after)})


GRADERS = {"CH1T": grade_CH1, "CH1C": grade_CH1, "CH1M": grade_CH1, "CH2": grade_CH2}


def write_evidence(run: Run, code: str, tag: str) -> Path:
    out = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{tag}-{run.arm.name}.txt"
    keep_earlier(out)
    lines = [f"AI PLAYER BUILD STEP 5 (THE STORY) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
             f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}",
             f"start: {'a real New Game (--fresh)' if run.arm.fresh else f'the end state of arm {run.arm.state_from}: {run.start_state}'}",
             f"command: {' '.join(run.command)}",
             f"env: {' '.join(f'{k}={v}' for k, v in sorted({ENV_BRAIN: 'play', ENV_SEED: str(run.arm.seed), **run.arm.env}.items()))}",
             f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
             f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
             "checks (pre-registered in ai_player/gates/live_step5.py's docstring and PREDICTED; each quotes both values):"]
    lines += [f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks]
    lines.append(f"measures: {json.dumps(run.measures, ensure_ascii=False)}")
    lines += [f"note: {note}" for note in run.notes]
    milestones = [str(r.get("reason")) for r in tells(run, "MILESTONE ")]
    lines.append("the AI's milestones (its told lines; the GAME's proofs are the checks above):")
    lines += [f"  {line[:300]}" for line in milestones]
    lines.append("the AI's goals (kind: reason), first 400:")
    lines += [f"  f{r.get('frame')} {r.get('action')}: {str(r.get('reason'))[:200]}" for r in run.records
              if r.get("decision") == "goal"][:400]
    lines.append("the end of the AI's log:")
    lines += [f"  {line[:400]}" for line in run.ai_log.splitlines()[-40:]]
    lines.append("verdict file: " + json.dumps(run.verdict, ensure_ascii=False)[:3000])
    lines.append("second path at the end: " + json.dumps({k: (run.after or {}).get(k) for k in
                                                         ("name", "gender_name", "party_exp", "party_ot", "balls", "money",
                                                          "map", "story")}, ensure_ascii=False)[:4000])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def leftover_processes() -> list[str]:
    """The emulator processes THIS driver could have left: the framework or the launcher on this driver's profile, or the
    harness's `truth` read. (Measured 2026-10-14: a check for any `pokebot.py` named 17 processes of OTHER projects on this
    machine, a 24/7 learner's lanes among them, which this driver never started and must never touch; and a check for
    any `play_harness` would name the seed sweep's runs, which may play beside this driver.)"""
    done = subprocess.run(["powershell", "-NoProfile", "-Command",
                           "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { ($_.CommandLine -like "
                           f"'*pokebot.py*{PROFILE}*') -or ($_.CommandLine -like '*ai_player run*{PROFILE}*') -or "
                           "($_.CommandLine -like '*play_harness.py* truth *') } | ForEach-Object { $_.ProcessId }"],
                          capture_output=True, timeout=60)
    return [line.strip() for line in done.stdout.decode(errors="replace").splitlines() if line.strip()]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--arms", default=",".join(arm.name for arm in ARMS))
    parser.add_argument("--evidence-tag", default="step5")
    parser.add_argument("--build-root", type=Path, default=launcher.resolve_build_root(None))
    args = parser.parse_args()
    wanted = [a.strip() for a in args.arms.split(",") if a.strip()]
    arms = [arm for arm in ARMS if arm.name in wanted]
    code = tree_provenance(REPO)
    print(f"[LIVE5] code: {code}", flush=True)
    carried: dict[str, tuple[Path, Path]] = {}
    results = []
    for arm in arms:
        print(f"[LIVE5] arm {arm.name}: {arm.title}", flush=True)
        run = run_arm(arm, args.build_root, carried)
        GRADERS[arm.name](run)
        path = write_evidence(run, code, args.evidence_tag)
        results.append(run)
        print(f"[LIVE5] arm {arm.name}: {'PASS' if run.passed else 'FAIL'} ({run.elapsed:.0f}s) -> {path}", flush=True)
        for ok, text in run.checks:
            if not ok:
                print(f"    [FAIL] {text[:400]}", flush=True)
    left = leftover_processes()
    print(f"[LIVE5] leftover emulator processes: {left or 'none'}", flush=True)
    chapter_1 = [r for r in results if r.arm.name.startswith("CH1")]
    spins = sum(r.measures.get("spins") or 0 for r in chapter_1)
    steps = sum(r.measures.get("roam_steps") or 0 for r in chapter_1)
    pooled_ok = not chapter_1 or (steps > 0 and spins / steps < 0.02)
    occasions = sum(r.measures.get("rest_occasions") or 0 for r in chapter_1)
    rest_ok = not chapter_1 or occasions >= 1
    if chapter_1:
        print(f"[LIVE5] the CH1 arms' spins together: {spins} over {steps} training steps = "
              f"{(spins / steps if steps else 1.0):.4f} (< 0.02): {'PASS' if pooled_ok else 'FAIL'}", flush=True)
        print(f"[LIVE5] the CH1 arms' occasions for the rest rule together (a battle in a roam that ended under the "
              f"personality's heal_below): {occasions} (>= 1, so the rule's check is not vacuous): "
              f"{'PASS' if rest_ok else 'FAIL'}; rests {[r.measures.get('rests') for r in chapter_1]}", flush=True)
    passed = all(run.passed for run in results) and not left and pooled_ok and rest_ok
    print(f"[LIVE5] OVERALL {'PASS' if passed else 'FAIL'}: " + ", ".join(f"{r.arm.name} {'PASS' if r.passed else 'FAIL'}"
                                                                            for r in results), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
