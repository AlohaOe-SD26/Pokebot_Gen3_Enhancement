"""TEST SIDE (build step 5): the SEED SWEEP of the story player: how OFTEN chapter 1 is played through, and what each
fault arm costs. In-process (`gates/play_harness.py`), the cartridge's clock pinned, every run graded by the GAME's own
record (`play_harness.StoryRecorder`: save block 1's marks and the game's counters read by the harness's own code, never the
AI's eyes), the AI's told lines only cross-checked.

    py -3.12 ai_player/gates/rate_step5.py [--plans CH1,NOTRAIN,NOHINTS,DEADREST,STOP,STOPDEAD] [--seeds 12]
                                           [--first-seed 1] [--workers 8] [--frames 300000] [--evidence-tag step5]

THE PLANS (each seed: a personality and a starter drawn by the seed number, so every personality and starter is played):
  CH1      a real New Game to the POKéDEX (`ch1_pokedex`): reached? frames; the rival beaten at the FIRST try (by the game:
           the trainer-battle counter when the rival's flag went up); TRAINED BY THE GAME (the step-5 verifier's round 2):
           inside the windows the AI's log says it roamed to train before the rival's flag, the game's own step counter
           (`play_harness` THE STEPS) and the wild battles the game says were WON there (THE BATTLES), and the AI's
           training steps (its roam reports); the wild battles won anywhere before the rival (reported: walks win battles
           too); its spin ratio; any stretch standing still under the catch-all reason; THE REST RULE (no roam fought on
           after a battle that left the party under its personality's heal_below, `roam_breaches`, with its occasions
           counted); the AI's battles lost (its report) == its TOLD losses (the play loop's lines) == the game's
           (gBattleOutcome LOST) in every run of every plan
  NOTRAIN  FAULT `no_training`: the same seeds, no training before a known fight (the heal before the fight KEPT: the
           fault removes the training only): the wild battles won before the rival (the mechanism), the game-side TRAINED
           check failing in EVERY seed (it tells training from none), the party's strongest level and the share of its
           HP left when the rival's flag went up, PAIRED by seed (the effect, the framework's party decoder at that
           frame), and the first-try win rate (REPORTED, not bounded: below)
  NOHINTS  FAULT `no_hints`: the same seeds, no hint ever used: reached or not within the budget, the frames, the reason
  DEADREST the fix REMOVED: a copy of the package with `revert_step5.py`'s mutant G36 (the navigator asks the rest rule only
           with a battle limit set, as it did until the step-5 verifier's round): the rest check must find the battles
           played on under heal_below that the real code no longer plays (CLAUDE.md rule 8: an arm with the fix removed)
  STOP, STOPDEAD  PHASE 2 (`STOP_PLANS`): every run above that the GAME recorded a battle lost in, replayed with MAX_LOSSES
           1 in a copy: STOP must end at that loss with the loop's reason; STOPDEAD (the loop's count also removed,
           revert_step5 G46: the verifier's V6) must not, and its report says 0 losses where the game lost
The verdicts are PRE-REGISTERED in `BOUNDS` (machine-checked) from the DEVELOPMENT sweeps of 2026-10-14 (`step5dev1` to
`step5dev8`, seeds 1-9); the graded sweep plays HELD-OUT seeds. The first graded sweep played seeds 101-110 (the tree
59521c7ebf62dc70); the step-5 verifier's round (2026-10-14) re-graded on NEW held-out seeds, 201-210, since its fixes
were developed while seeds 101-110's results were known. The last development sweep (step5dev8, the tree of that round)
measured: CH1 9 of 9 reached, 9 of 9 first-try, wild battles WON before the rival 12-27 a seed, training steps 120-240,
spins 11 in 1566 steps (0.70 %), the catch-all 0, the rest rule 0 breaches over 20 occasions, whiteouts 0 (3 in 9 in
step5dev6 and step5dev7, before the way home was known); NOTRAIN won wild battles 47 vs 162, the strongest level at the
rival paired by seed +1.9 levels (every seed +1 to +3), first-try 8 of 9 vs 9 of 9; DEADREST 37 battles fought on under
heal_below over 46 occasions (the real code 0). (NOHINTS was not re-swept in development: its switch still makes
`hint_known` refuse every hint, before the new wordless rule is reached; its bound is unchanged.) The win-rate drop the design predicted for NOTRAIN is NOT measurable at this fight (the rival's L5 starter is
beaten untrained 8 times in 9), so it is reported, and the effect is graded on the fight's margin instead.
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

from ai_player.gates.provenance import keep_earlier, provenance  # noqa: E402

HARNESS = Path(__file__).resolve().parent / "play_harness.py"
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
GAME_CLOCK = "2026-10-14T10:00"
WALL_CLOCK = "10:00"
PERSONALITIES = ("Story", "Catcher", "Trainer")
STARTERS = ("TREECKO", "TORCHIC", "MUDKIP")
PLANS = {"CH1": "", "NOTRAIN": "no_training", "NOHINTS": "no_hints", "DEADREST": ""}
#: (the step-5 verifier's round, 2026-10-14) a plan played by a COPY of the package with mutants of
#: `gates/revert_step5.py` applied: DEADREST is G36, the navigator asking the rest rule only with a battle limit set (the
#: verifier's DEAD FIX, as it was): the arm with the fix REMOVED (CLAUDE.md rule 8), graded by the same rest check
MUTANT_PLANS = {"DEADREST": ["G36"]}
#: (the step-5 verifier's round 2, 2026-10-14: "no run reached the MAX_LOSSES stop", and the loop's count was unproven)
#: PHASE 2, the STOP plans: every run of the plans above whose GAME recorded a battle LOST is played again, the same seed,
#: faults and mutants, in a copy whose MAX_LOSSES is 1 (`CAP1`): STOP must end with "1 battles lost (MAX_LOSSES 1)" right
#: after that loss (within `STOP_WITHIN` frames of the game's record of it); STOPDEAD, the same with the loop's count
#: REMOVED too (revert_step5 G46, the verifier's V6), must NOT, and its report must say 0 losses where the game lost (the
#: ALL PLANS check's arm: it would catch the dead count). The plans are chosen by the game's own record, before they run.
STOP_PLANS = {"STOP": ["CAP1"], "STOPDEAD": ["CAP1", "G46"]}
EXTRA_EDITS = {"CAP1": [("mode.py", "MAX_LOSSES = 3\n",
                         "MAX_LOSSES = 1  # gates/rate_step5.py's STOP plans: the first battle lost ends the run\n")]}
STOP_REASON = "play: stuck: 1 battles lost (MAX_LOSSES 1)"
#: frames from the game's record of the loss (gBattleOutcome LOST) to the run's end: the whiteout's text and the warp home
#: (~1,500 frames), the goal under way unwinding, and the loop's next pass
STOP_WITHIN = 6000
GENERIC_BUSY = "watching: the game is busy"
#: PRE-REGISTERED (module docstring): set from the development sweeps (named in the README's step-5 section).
BOUNDS = {
    "CH1_REACHED_MIN": 0.8,  # at least this share of the CH1 seeds reach the POKéDEX within the budget
    "CH1_FIRST_TRY_MIN": 0.8,  # ... and beat the rival at the first try
    # (the step-5 verifier's round 2, 2026-10-14: "won >= 3 between the starter's mark and the rival's flag" was met by
    # NOTRAIN, which never trains, in 6 of 10 seeds: walks win battles too) every CH1 seed that beat the rival: inside the
    # windows its log says it ROAMED TO TRAIN before the rival's flag (`training_windows`), the GAME says at least this many
    # wild battles were WON (`play_harness` THE BATTLES) ...
    "CH1_WILD_WON_MIN": 3,
    # ... and the GAME's step counter rose at least this much there (`play_harness` THE STEPS); its roam reports must say
    # as much too. Both bounds are round 1's, carried over (not re-derived); measured on the kept action logs of the
    # development seeds 1-9 and the graded seeds 201-210 (the AI's log: the game's own counts in the windows are new),
    # 5-21 wild battles won and 110-279 training steps in the windows, NOTRAIN 0 and 0 in every seed
    "CH1_TRAIN_STEPS_MIN": 60,
    # (the step-5 verifier's round) the game's WHITEOUTS (battles LOST) over all the CH1 seeds together at most this: the
    # development sweeps measured 3 in 9 (step5dev6, step5dev7: every one a wild battle met at 2-5 HP, six of them on a walk
    # home that could not find the house) and 0 in 9 once the way home was known (step5dev8)
    "CH1_WHITEOUTS_MAX": 2,
    "CH1_SPIN_MAX": 0.02,  # the back-and-forth spins over all the seeds' training steps together
    "CH1_SPINS_PER_SEED": 5,  # ... and no seed over this many (step 4.1 round 3's `ROAM_SPINS_PER_SEED`)
    "NOTRAIN_WILD_LESS": True,  # NOTRAIN wins fewer wild battles before the rival than CH1, in total
    # NOTRAIN's effect, PAIRED by seed: the mean of (CH1's strongest level at the rival's flag - NOTRAIN's) at least this,
    # and no seed where NOTRAIN is 2 or more levels higher
    "NOTRAIN_LEVEL_PAIRED_MIN": 0.5,
    "NOHINTS_SLOWER": True,  # NOHINTS reaches the POKéDEX in fewer seeds, or later on average where both reach it
}


def plan_of(seed: int) -> tuple[str, str]:
    """The seed's personality and starter: every personality and every starter in turn (seed 1: Story, TREECKO; 2: Catcher,
    TORCHIC; 3: Trainer, MUDKIP; 4: Story, TORCHIC ...), so 9 consecutive seeds play each pair once."""
    index = seed - 1
    return PERSONALITIES[index % 3], STARTERS[(index + index // 3) % 3]


def copy_with(names: list[str]) -> Path:
    """The package copied with these edits applied (`revert_step5.make_copy`: every anchor must occur once): mutants of
    `revert_step5.MUTANTS` and this file's `EXTRA_EDITS`."""
    from ai_player.gates.revert_step5 import MUTANTS, make_copy

    edits: list[tuple[str, str, str]] = []
    for name in names:
        edits += EXTRA_EDITS[name] if name in EXTRA_EDITS else MUTANTS[name][2]
    return make_copy(edits)


def run_one(plan: str, seed: int, frames: int, target: str, root: Path = REPO, base: str | None = None) -> dict:
    """One run of `plan` (a phase-2 STOP plan replays the run of plan `base`: its faults, in the copy `root`)."""
    personality, starter = plan_of(seed)
    folder = Path(tempfile.mkdtemp(prefix=f"ai_step5_{plan}{'_' + base if base else ''}_{seed}_"))
    fault = PLANS[base or plan]
    harness = root / "ai_player" / "gates" / "play_harness.py"
    command = [sys.executable, str(harness), "--fresh", "--seed", str(seed), "--frames", str(frames), "--personality",
               personality, "--starter", starter, "--target", target, "--game-clock", GAME_CLOCK, "--clock", WALL_CLOCK,
               "--run-dir", str(folder)] + (["--fault", fault] if fault else [])
    began = time.monotonic()
    env = {**os.environ, "PYTHONUTF8": "1"}
    if root != REPO:
        from ai_player.host.launcher import ENV_BUILD_ROOT, resolve_build_root

        env.update({ENV_BUILD_ROOT: str(resolve_build_root(None)), "PYTHONDONTWRITEBYTECODE": "1"})
    result = subprocess.run(command, cwd=str(root), capture_output=True, timeout=7200, env=env)
    text = result.stdout.decode("utf-8", errors="replace")
    line = next((l for l in text.splitlines() if l.startswith("PLAY ")), None)
    if line is None:
        return {"plan": plan, "seed": seed, "base": base,
                "error": (text + result.stderr.decode("utf-8", errors="replace"))[-2000:]}
    data = json.loads(line[5:])
    actions = []
    path = folder / "actions.jsonl"
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            try:
                actions.append(json.loads(raw))
            except json.JSONDecodeError:
                pass
    row = grade_run(plan, seed, personality, starter, data, actions, time.monotonic() - began)
    return {**row, "base": base} if base else row


def trained_by_game(row: dict) -> bool:
    """THE TRAINED CHECK by the game (the step-5 verifier's round 2): inside the windows its log says it roamed to train
    before the rival's flag, the game's step counter rose at least `CH1_TRAIN_STEPS_MIN` and the game says at least
    `CH1_WILD_WON_MIN` wild battles were WON."""
    return (row.get("game_train_steps") or 0) >= BOUNDS["CH1_TRAIN_STEPS_MIN"] \
        and (row.get("game_train_won") or 0) >= BOUNDS["CH1_WILD_WON_MIN"]


def stop_verdicts(rows: dict[str, list[dict]]) -> list[tuple[bool, str]]:
    """PHASE 2 (`STOP_PLANS`): the MAX_LOSSES stop, end to end in the game, and the arm with the loop's count removed."""
    out: list[tuple[bool, str]] = []
    if "STOP" not in rows and "STOPDEAD" not in rows:
        return out
    bases = {(r["plan"], r["seed"]): r for plan, plan_rows in rows.items() if plan in PLANS for r in plan_rows
             if "error" not in r}
    lost = sorted(key for key, r in bases.items() if r["losses_game"])
    for plan in ("STOP", "STOPDEAD"):
        if plan not in rows:
            continue
        played = [r for r in rows[plan] if "error" not in r]
        bad, lines = [], []
        for r in played:
            base = bases.get((r.get("base"), r["seed"]))
            after = r["frames"] - r["first_loss_f"] if r["first_loss_f"] is not None else None
            same = base is not None and base["first_loss_f"] == r["first_loss_f"]
            if plan == "STOP":
                ok = (r["reason"] == STOP_REASON and r["losses_game"] == 1 and r["losses_told"] == 1 and r["losses_ai"] == 1
                      and after is not None and 0 <= after <= STOP_WITHIN)
            else:
                ok = (r["reason"] != STOP_REASON and r["losses_game"] >= 1 and r["losses_ai"] == 0 and r["losses_told"] == 0
                      and after is not None and after > STOP_WITHIN)
            lines.append((r.get("base"), r["seed"], r["reason"], f"first loss f{r['first_loss_f']} (the base run's "
                          f"f{base['first_loss_f'] if base else '?'}: {'the same' if same else 'NOT the same'})",
                          f"ended {after} frames after it", f"losses report/told/game {r['losses_ai']}/{r['losses_told']}/"
                          f"{r['losses_game']}"))
            if not ok:
                bad.append((r.get("base"), r["seed"]))
        if plan == "STOP":
            text = (f"STOP (MAX_LOSSES 1 in a copy; every run of phase 1 the GAME recorded a loss in, replayed): each must "
                    f"end '{STOP_REASON}' within {STOP_WITHIN} frames of the game's record of its loss, told once, the "
                    f"game's losses 1")
        else:
            text = (f"STOPDEAD (MAX_LOSSES 1 AND the loop's count removed, revert_step5 G46): each must NOT stop there, "
                    f"going on past {STOP_WITHIN} frames, its report and told losses 0 while the game lost (the ALL PLANS "
                    f"check would catch it)")
        out.append((bool(lost) and len(played) == len(lost) and not bad,
                    f"{text}: phase 1's runs with a loss {lost or 'NONE (not exercised)'}; played {len(played)}: {lines}; "
                    f"off: {bad or 'none'}"))
    return out


def first_change(changes: list[dict], mark: str, to: int = 1) -> dict | None:
    return next((c for c in changes if c["mark"] == mark and c["to"] >= to), None)


def training_windows(actions: list[dict], fight: str = "ch1_rival_route103") -> list[tuple[int, int]]:
    """(the step-5 verifier's round 2) Where the AI's log says it was ROAMING TO TRAIN for `fight`: (first frame, last
    frame) of every roam of a `train` goal for it, from the roam's start ("roam N steps", after the walk to the grass) to
    its metrics record (a roam that ran out, or one a rest or an item ball stopped), else to the goal's last record. The
    GAME's counts inside them (`training_by_game`) are what tells training from none."""
    windows: list[tuple[int, int]] = []
    goal, start, last = None, None, None
    for r in actions:
        frame = r.get("frame")
        if r.get("decision") == "goal":
            if start is not None:
                windows.append((start, last))
            goal, start = r, None
            continue
        if frame is not None:
            last = frame
        if goal is None or goal.get("action") != "train" or (goal.get("extra") or {}).get("milestone") != fight:
            continue
        if r.get("decision") == "decide" and str(r.get("action", "")).startswith("roam ") and frame is not None:
            start = frame
        elif start is not None and r.get("decision") == "roam" and r.get("action") == "metrics":
            windows.append((start, last))
            start = None
    if start is not None:
        windows.append((start, last))
    return windows


def training_by_game(windows: list[tuple[int, int]], story: dict, offset: int, until: int | None) -> dict:
    """THE GAME's counts inside the AI's training windows (`training_windows`, its log's frames less `offset`, the frame of
    its first look: the recorder counts from the run's first frame) that began before frame `until` (the rival's flag): the
    steps its own counter rose (`play_harness.steps_counted`) and the wild battles it says were WON (gBattleOutcome 1 with
    no trainer flag), each ended inside a window (the recorder samples every `every` frames: that much slack after it)."""
    from ai_player.gates.play_harness import steps_counted

    every = story.get("every") or 30
    timeline = story.get("steps") or []
    steps = refused = 0
    won = []
    for start, end in windows:
        start, end = start - offset, end - offset
        if until is not None and start > until:
            continue
        counted, bad = steps_counted(timeline, start, end)
        steps += counted
        refused += bad
        won += [b["f"] for b in story.get("battles") or [] if not b["trainer"] and b["outcome"] == 1
                and start <= b["f"] <= end + every]
    return {"windows": len([w for w in windows if until is None or w[0] - offset <= until]), "steps": steps,
            "won": len(won), "refused": refused}


def roam_breaches(actions: list[dict]) -> tuple[list[tuple], int]:
    """(the step-5 verifier's DEAD FIX, 2026-10-14) From the AI's action log: every battle a TRAINING or CATCHING roam
    played AFTER an earlier battle of the same roam had ended with the party under the active personality's `heal_below`
    (the rest rule says the roam stops there, to heal), and how many battles ended under it in a roam (the opportunities:
    a check with none is vacuous). A roam begins at its "roam N steps" record and ends at the next goal; the walk to the
    grass before it is travel (no rest is asked there)."""
    from ai_player.personality import ERRANDS

    breaches, low_ends = [], 0
    goal, roaming, low = None, False, None
    for r in actions:
        if r.get("decision") == "goal":
            goal, roaming, low = r, False, None
            continue
        if goal is None or goal.get("action") not in ("train", "catch"):
            continue
        if r.get("decision") == "decide" and str(r.get("action", "")).startswith("roam "):
            roaming = True
            continue
        extra = r.get("extra") or {}
        if not roaming or r.get("decision") != "world" or "kind" not in extra:
            continue
        if low is not None:
            breaches.append((r.get("frame"), low, extra.get("outcome")))
        hp = extra.get("party_hp_end") or [0, 0]
        active = (goal.get("extra") or {}).get("active") or "Story"
        heal_below = ERRANDS[active].heal_below
        if hp[1] and hp[0] / hp[1] < heal_below and extra.get("outcome") != "lost":
            low_ends += 1
            low = f"f{r.get('frame')} ended at {hp[0]}/{hp[1]} (under the {active}'s {heal_below:.0%})"
    return breaches, low_ends


def grade_run(plan: str, seed: int, personality: str, starter: str, data: dict, actions: list[dict], seconds: float) -> dict:
    """One run's numbers, each by the game (the recorder) unless named as the AI's."""
    changes = (data.get("story") or {}).get("changes") or []
    end = (data.get("story_truth") or {}).get("marks") or {}
    stats = (data.get("story_truth") or {}).get("stats") or {}
    dex = first_change(changes, "RECEIVED_POKEDEX_FROM_BIRCH")
    rival = first_change(changes, "DEFEATED_RIVAL_ROUTE103")
    # the trainer battles fought before the rival's flag went up, counted from the starter's first battle (the game's
    # counter): 1 = the rival beaten at the first try (Route 103 holds no other trainer the player can reach before it)
    starter_mark = first_change(changes, "VAR_BIRCH_LAB_STATE", 2)
    trainer_before = rival["stats"]["trainer_battles"] - (starter_mark["stats"]["trainer_battles"] if starter_mark else 0) \
        if rival else None
    wild_before = rival["stats"]["wild_battles"] - (starter_mark["stats"]["wild_battles"] if starter_mark else 0) \
        if rival else None
    rival_frame = rival["f"] if rival else None
    roams = [r for r in actions if r.get("decision") == "roam" and r.get("action") == "metrics"]
    roams_before = [r for r in roams if rival_frame is None or (r.get("frame") or 0) <= rival_frame]
    train_steps = sum((r.get("extra") or {}).get("steps", 0) for r in roams_before)
    spins = sum((r.get("extra") or {}).get("spins", 0) for r in roams)
    steps_all = sum((r.get("extra") or {}).get("steps", 0) for r in roams)
    generic = sum(1 for r in actions if r.get("decision") == "watch" and str(r.get("reason", "")).startswith(GENERIC_BUSY))
    party = (data.get("truth") or {}).get("party_exp") or []
    # the party when the rival's flag went up (the framework's decoder, `play_harness.party_now`): its strongest level and
    # the share of its HP the fight left (how hard the win was)
    at_rival = (rival or {}).get("party") or []
    level_at_rival = max((row[1] for row in at_rival), default=None)
    total = sum(row[3] for row in at_rival)
    hp_after_rival = round(sum(row[2] for row in at_rival) / total, 3) if total else None
    blips = len(((data.get("story") or {}).get("blips")) or [])
    # (the step-5 verifier's round) THE GAME's battles (the recorder's gBattleOutcome / gBattleTypeFlags): the wild battles
    # WON between the starter's mark (PROF. BIRCH's scripted battle is before it) and the rival's flag, and every battle
    # LOST in the run (a whiteout), against the AI's own count of its losses
    battles = (data.get("story") or {}).get("battles") or []
    since = starter_mark["f"] if starter_mark else 0
    won_before = [b for b in battles if not b["trainer"] and b["outcome"] == 1 and since < b["f"] <= (rival_frame or 0)] \
        if rival else []
    lost = [b for b in battles if b["outcome"] == 2]
    drew = [b for b in battles if b["outcome"] == 3]
    breaches, low_ends = roam_breaches(actions)
    # (the step-5 verifier's round 2) THE GAME inside the AI's training windows: the steps its counter rose there and the
    # wild battles it says were won there (an arm that never trains has no window: both 0); and the AI's TOLD losses (the
    # play loop's own lines, `mode.py` _count_losses), which only the loop's count writes
    offset = actions[0].get("frame") or 0 if actions else 0
    windows = training_windows(actions)
    by_game = training_by_game(windows, data.get("story") or {}, offset, rival_frame)
    told = sum(1 for r in actions if r.get("decision") == "tell" and str(r.get("reason", "")).startswith("a battle was LOST ("))
    return {
        "plan": plan, "seed": seed, "personality": personality, "starter": starter, "reason": data.get("reason"),
        "frames": data.get("frames"), "seconds": round(seconds, 1),
        "reached": bool(end.get("RECEIVED_POKEDEX_FROM_BIRCH")), "dex_frame": dex["f"] if dex else None,
        "rival_beaten": bool(end.get("DEFEATED_RIVAL_ROUTE103")), "rival_frame": rival_frame,
        "train_windows": by_game["windows"], "game_train_steps": by_game["steps"], "game_train_won": by_game["won"],
        "game_steps_refused": by_game["refused"], "train_steps_before_rival": train_steps,
        "losses_game": len(lost), "losses_ai": ((data.get("report") or {}).get("losses")), "losses_told": told,
        "first_loss_f": lost[0]["f"] if lost else None,
        "trainer_battles_to_rival": trainer_before, "wild_before_rival": wild_before,
        "wild_won_before_rival": len(won_before) if rival else None,
        "spins": spins, "roam_steps": steps_all,
        "spin_ratio": round(spins / steps_all, 4) if steps_all else 0.0, "generic_idle": generic,
        "level_at_rival": level_at_rival, "hp_after_rival": hp_after_rival, "recorder_blips": blips,
        "starter_in_party": [row[1] for row in party[:1]], "levels": [row[3] for row in party], "drew_game": len(drew),
        "battles_ended": len(battles), "rest_breaches": breaches, "roam_low_ends": low_ends, "game_stats": stats,
    }


def summarise(plan: str, rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    reached = [r for r in ok if r["reached"]]
    beaten = [r for r in ok if r["rival_beaten"]]
    first = [r for r in beaten if r["trainer_battles_to_rival"] == 1]
    return {"plan": plan, "runs": len(rows), "errors": len(rows) - len(ok), "reached": len(reached),
            "rival_beaten": len(beaten), "first_try": len(first),
            "wild_before_rival": [r["wild_before_rival"] for r in ok],
            "train_steps_before_rival": [r["train_steps_before_rival"] for r in ok],
            "dex_frames": [r["dex_frame"] for r in ok], "spin_ratios": [r["spin_ratio"] for r in ok],
            "generic_idle": sum(r["generic_idle"] for r in ok), "reasons": [r["reason"] for r in ok],
            "levels_at_rival": [r["level_at_rival"] for r in ok], "hp_after_rival": [r["hp_after_rival"] for r in ok],
            "wild_won_before_rival": [r["wild_won_before_rival"] for r in ok],
            "game_train_steps": [r["game_train_steps"] for r in ok], "game_train_won": [r["game_train_won"] for r in ok],
            "losses_game": [r["losses_game"] for r in ok], "losses_ai": [r["losses_ai"] for r in ok],
            "losses_told": [r["losses_told"] for r in ok],
            "rest_breaches": sum(len(r["rest_breaches"]) for r in ok), "roam_low_ends": sum(r["roam_low_ends"] for r in ok)}


def verdicts(summary: dict[str, dict], rows: dict[str, list[dict]]) -> list[tuple[bool, str]]:
    out = []
    ch1 = summary.get("CH1")
    if ch1:
        n = ch1["runs"]
        out.append((ch1["reached"] >= BOUNDS["CH1_REACHED_MIN"] * n,
                    f"CH1: the POKéDEX reached (by the game's flag) in {ch1['reached']} of {n} (bound >= {BOUNDS['CH1_REACHED_MIN']:.0%})"))
        out.append((ch1["first_try"] >= BOUNDS["CH1_FIRST_TRY_MIN"] * n,
                    f"CH1: the rival beaten at the FIRST try (the game's trainer-battle counter) in {ch1['first_try']} of {n} "
                    f"(bound >= {BOUNDS['CH1_FIRST_TRY_MIN']:.0%})"))
        beaten = [r for r in rows["CH1"] if r.get("rival_beaten")]
        low = [(r["seed"], r["game_train_won"], r["game_train_steps"], r["train_steps_before_rival"]) for r in beaten
               if not trained_by_game(r) or r["train_steps_before_rival"] < BOUNDS["CH1_TRAIN_STEPS_MIN"]]
        out.append((bool(beaten) and not low,
                    f"CH1: every seed that beat the rival TRAINED first, BY THE GAME inside the windows its log says it "
                    f"roamed to train before the rival's flag (the step-5 verifier's round 2): the game's step counter rose "
                    f">= {BOUNDS['CH1_TRAIN_STEPS_MIN']} there {[r['game_train_steps'] for r in beaten]} and the game says "
                    f">= {BOUNDS['CH1_WILD_WON_MIN']} wild battles were WON there {[r['game_train_won'] for r in beaten]} "
                    f"(windows {[r['train_windows'] for r in beaten]}); and its roam reports say >= "
                    f"{BOUNDS['CH1_TRAIN_STEPS_MIN']} training steps {[r['train_steps_before_rival'] for r in beaten]}; "
                    f"short: {low or 'none'}"))
        out.append((True, f"CH1 (reported): wild battles WON anywhere between the starter's mark and the rival's flag (the "
                          f"game's outcomes; NOT a training check: walks win battles too) "
                          f"{[r['wild_won_before_rival'] for r in beaten]}, met (the game's counter) "
                          f"{[r['wild_before_rival'] for r in beaten]}; the game's steps refused as impossible readings "
                          f"{[r['game_steps_refused'] for r in beaten]}"))
        # step 4.1 round 3's criterion (`rate_step3.py` ROAM_SPINS_PER_SEED): the spins over the seeds TOGETHER under 2 % of
        # their training steps, and no seed over 5 (a per-seed "< 2 %" failed 18 % of 10-seed samples of the same roaming:
        # 2 spins in 100 steps is 2 %; this sweep's seed 7 of 2026-10-14, step5dev3, was exactly that)
        graded = [r for r in rows["CH1"] if "error" not in r]
        spins = sum(r.get("spins") or 0 for r in graded)
        steps = sum(r.get("roam_steps") or 0 for r in graded)
        pooled = spins / steps if steps else 1.0
        heavy = [(r["seed"], r.get("spins")) for r in graded if (r.get("spins") or 0) > BOUNDS["CH1_SPINS_PER_SEED"]]
        out.append((pooled < BOUNDS["CH1_SPIN_MAX"] and not heavy,
                    f"CH1: the back-and-forth spins over the seeds together {spins} in {steps} training steps ({pooled:.2%}, "
                    f"bound under {BOUNDS['CH1_SPIN_MAX']:.0%}), per seed {[r.get('spins') for r in graded]} (bound "
                    f"{BOUNDS['CH1_SPINS_PER_SEED']} each; over it {heavy or 'none'})"))
        out.append((ch1["generic_idle"] == 0, f"CH1: no stretch standing still under the catch-all reason: {ch1['generic_idle']}"))
        out.append((sum(ch1["losses_game"]) <= BOUNDS["CH1_WHITEOUTS_MAX"],
                    f"CH1: the game's whiteouts (battles LOST, gBattleOutcome) over the seeds together {sum(ch1['losses_game'])} "
                    f"(bound <= {BOUNDS['CH1_WHITEOUTS_MAX']}), per seed {ch1['losses_game']}"))
        # (the step-5 verifier's DEAD FIX) the rest rule FIRES: no roam played on after a battle that left the party under
        # its personality's heal_below; and it had occasions to (a check with none is vacuous)
        out.append((ch1["rest_breaches"] == 0 and ch1["roam_low_ends"] >= 1,
                    f"CH1: THE REST RULE: battles a training or catching roam played after one that ended under the "
                    f"personality's heal_below {ch1['rest_breaches']} (bound 0), over {ch1['roam_low_ends']} such ends (the "
                    f"occasions; bound >= 1: not vacuous): "
                    f"{[(r['seed'], r['rest_breaches'][:2]) for r in graded if r['rest_breaches']] or 'none'}"))
        # the recorder saw every battle end (its count of ends == the game's battle counter, or one fewer if a battle was
        # under way when the run ended): the battle numbers above rest on it
        missed = [(r["seed"], r["battles_ended"], (r.get("game_stats") or {}).get("total_battles")) for r in graded
                  if (r.get("game_stats") or {}).get("total_battles") is None
                  or not 0 <= r["game_stats"]["total_battles"] - r["battles_ended"] <= 1]
        out.append((not missed, f"CH1: the recorder saw every battle end (ends == GAME_STAT_TOTAL_BATTLES, or one fewer): "
                                f"{[(r['seed'], r['battles_ended']) for r in graded]}; off: {missed or 'none'}"))
    # (the step-5 verifier's round: the AI's report said 0 losses after two whiteouts) every plan, every seed: the AI's
    # count of battles lost (its report, `mode.py` MAX_LOSSES) == the game's (battle outcomes LOST); and (round 2: the end
    # line recounted, so a loop that had stopped counting still agreed) its TOLD losses, which only the loop's count writes,
    # == the game's too. STOPDEAD is the arm with the loop's count REMOVED: graded below, never here.
    every = [r for plan, plan_rows in rows.items() if plan != "STOPDEAD" for r in plan_rows if "error" not in r]
    wrong = [(r["plan"], r["seed"], r["losses_ai"], r["losses_told"], r["losses_game"]) for r in every
             if not r["losses_ai"] == r["losses_told"] == r["losses_game"]]
    out.append((bool(every) and not wrong,
                f"ALL PLANS: the AI's battles lost (its report) == its TOLD losses (the loop's lines) == the game's "
                f"(gBattleOutcome LOST) in {len(every) - len(wrong)} of {len(every)} runs; the game's losses by plan "
                f"{ {plan: sum(r['losses_game'] for r in plan_rows if 'error' not in r) for plan, plan_rows in rows.items()} }; "
                f"off (plan, seed, report, told, game): {wrong or 'none'}"))
    if ch1 and summary.get("NOTRAIN"):
        no = summary["NOTRAIN"]
        a = sum(x or 0 for x in ch1["wild_won_before_rival"])
        b = sum(x or 0 for x in no["wild_won_before_rival"])
        out.append((b < a, f"NOTRAIN (the mechanism): wild battles WON before the rival (the game's outcomes) in all {a} "
                           f"(CH1) vs {b} (NOTRAIN)"))
        # (the step-5 verifier's round 2: "won >= 3 before the rival" was met by NOTRAIN in 6 of 10 seeds) the game-side
        # TRAINED check must tell the arms apart: it passes for every CH1 seed that beat the rival (above) and FAILS for
        # every NOTRAIN seed (no training window: the game counted nothing there)
        untrained = [r for r in rows["NOTRAIN"] if "error" not in r]
        passed = [(r["seed"], r["game_train_steps"], r["game_train_won"]) for r in untrained if trained_by_game(r)]
        trained = [r for r in rows["CH1"] if "error" not in r and r.get("rival_beaten")]
        out.append((bool(untrained) and not passed,
                    f"THE TRAINED CHECK TELLS TRAINING FROM NONE (by the game): it passes for "
                    f"{sum(1 for r in trained if trained_by_game(r))} of {len(trained)} CH1 seeds and for {len(passed)} of "
                    f"{len(untrained)} NOTRAIN seeds (bound 0): NOTRAIN's training windows "
                    f"{[r['train_windows'] for r in untrained]}, the game's steps there "
                    f"{[r['game_train_steps'] for r in untrained]}, wild battles won there "
                    f"{[r['game_train_won'] for r in untrained]} (while it WON {no['wild_won_before_rival']} wild battles "
                    f"before the rival elsewhere: the count the old check used)"))

        def mean(values: list) -> float | None:
            values = [v for v in values if v is not None]
            return round(sum(values) / len(values), 3) if values else None

        # (the step-5 verifier: the HP comparison was a bare comparison of means, confounded by the missing heal before
        # the fight) PAIRED BY SEED: the same seed, personality and starter in both arms
        by_no = {r["seed"]: r for r in rows["NOTRAIN"] if "error" not in r}
        pairs = [(r, by_no[r["seed"]]) for r in rows["CH1"] if "error" not in r and r["seed"] in by_no]
        levels = [a["level_at_rival"] - b["level_at_rival"] for a, b in pairs
                  if a["level_at_rival"] is not None and b["level_at_rival"] is not None]
        hps = [round(a["hp_after_rival"] - b["hp_after_rival"], 3) for a, b in pairs
               if a["hp_after_rival"] is not None and b["hp_after_rival"] is not None]
        level_mean = mean(levels)
        out.append((bool(levels) and level_mean is not None and level_mean >= BOUNDS["NOTRAIN_LEVEL_PAIRED_MIN"]
                    and not any(d <= -2 for d in levels),
                    f"NOTRAIN (the effect, by the game's party at the rival's flag, PAIRED by seed): the strongest level "
                    f"CH1 - NOTRAIN {levels}, mean {level_mean} (bound >= {BOUNDS['NOTRAIN_LEVEL_PAIRED_MIN']}, and no seed "
                    f"NOTRAIN 2 or more levels higher)"))
        out.append((True, f"NOTRAIN (reported, not bounded): the HP share the rival's fight left, CH1 - NOTRAIN paired by "
                          f"seed {hps}, mean {mean(hps)} (both arms now heal before the fight: the fault removes the training "
                          f"only)"))
        # the WIN RATE is REPORTED, not a pass condition: the development sweeps measured the rival (L5) beaten at the
        # first try 9 of 9 (CH1) and 8 of 9 (NOTRAIN) (step5dev4, seed 7's CH1 row a recorder phantom, fixed since), a
        # ceiling a 10-seed sample cannot resolve; the README's step-5 section says so
        out.append((True, f"NOTRAIN (reported, not bounded): the rival beaten at the first try {ch1['first_try']} of "
                          f"{ch1['runs']} (CH1) vs {no['first_try']} of {no['runs']} (NOTRAIN)"))
    if ch1 and summary.get("DEADREST"):
        dead = summary["DEADREST"]
        hit = [(r["seed"], len(r["rest_breaches"]), r["rest_breaches"][:1]) for r in rows["DEADREST"]
               if "error" not in r and r["rest_breaches"]]
        out.append((dead["rest_breaches"] > 0 and ch1["rest_breaches"] == 0,
                    f"DEADREST (the fix REMOVED: mutant G36, the rest asked only with a battle limit): the rest check finds "
                    f"{dead['rest_breaches']} battles played on under heal_below over {dead['roam_low_ends']} occasions "
                    f"(bound > 0: the check sees the dead fix) vs CH1 {ch1['rest_breaches']}; seeds {hit or 'none'}; the "
                    f"game's whiteouts {sum(dead['losses_game'])} vs CH1 {sum(ch1['losses_game'])} (reported)"))
    if ch1 and summary.get("NOHINTS"):
        nh = summary["NOHINTS"]
        both = [(c, h) for c, h in zip(ch1["dex_frames"], nh["dex_frames"]) if c and h]
        slower = nh["reached"] < ch1["reached"] or (both and sum(h for _, h in both) > sum(c for c, _ in both))
        out.append((bool(slower), f"NOHINTS: reached {nh['reached']} of {nh['runs']} (CH1 {ch1['reached']}); where both "
                                  f"reached, frames {sum(h for _, h in both) if both else '-'} vs CH1 "
                                  f"{sum(c for c, _ in both) if both else '-'}; its ends {nh['reasons']}"))
    out += stop_verdicts(rows)
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plans", default="CH1,NOTRAIN,NOHINTS,DEADREST,STOP,STOPDEAD")
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--first-seed", type=int, default=1)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--frames", type=int, default=300000)
    parser.add_argument("--target", default="ch1_pokedex")
    parser.add_argument("--evidence-tag", default="step5")
    args = parser.parse_args()
    plans = [p.strip() for p in args.plans.split(",") if p.strip()]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    lines: list[str] = []

    def say(line: str) -> None:
        print(line, flush=True)
        lines.append(line)

    say(f"AI PLAYER BUILD STEP 5 - THE SEED SWEEP: plans {plans}, seeds {seeds[0]}-{seeds[-1]}, frames {args.frames}, game "
        f"clock {GAME_CLOCK}, wall clock set {WALL_CLOCK}")
    say(f"code: {provenance(REPO)}")
    unknown = [p for p in plans if p not in PLANS and p not in STOP_PLANS]
    if unknown:
        parser.error(f"unknown plans {unknown}")
    jobs = [(plan, seed) for plan in plans if plan in PLANS for seed in seeds]
    rows: dict[str, list[dict]] = {plan: [] for plan in plans}
    copies: dict[tuple[str, str], Path] = {(plan, plan): copy_with(MUTANT_PLANS[plan]) for plan in plans if plan in MUTANT_PLANS}
    for (plan, _), root in copies.items():
        say(f"plan {plan}: a COPY of the package with mutants {MUTANT_PLANS[plan]} of revert_step5.py applied, at {root}")

    def play(jobs: list[tuple[str, str | None, int]]) -> None:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(run_one, plan, seed, args.frames, args.target,
                                   copies.get((plan, base or plan), REPO), base): (plan, seed)
                       for plan, base, seed in jobs}
            for future, (plan, seed) in futures.items():
                row = future.result()
                rows[plan].append(row)
                say(f"  {plan}{' (' + row['base'] + ')' if row.get('base') else ''} seed {seed}: "
                    f"{json.dumps(row, ensure_ascii=False)[:2400]}")

    try:
        play([(plan, None, seed) for plan, seed in jobs])
        # PHASE 2 (`STOP_PLANS`): the runs the GAME recorded a loss in, replayed with MAX_LOSSES 1 (and without the loop's
        # count): chosen by the game's own record of phase 1, before they run
        stops = [plan for plan in plans if plan in STOP_PLANS]
        lost = sorted((r["plan"], r["seed"]) for plan in plans if plan in PLANS for r in rows[plan]
                      if "error" not in r and r["losses_game"])
        if stops:
            say(f"PHASE 2: the runs of phase 1 the game recorded a battle LOST in: {lost or 'none'}; plans {stops}")
        for stop in stops:
            for base in sorted({base for base, _ in lost}):
                copies[(stop, base)] = copy_with(MUTANT_PLANS.get(base, []) + STOP_PLANS[stop])
                say(f"plan {stop} ({base}): a COPY with {MUTANT_PLANS.get(base, []) + STOP_PLANS[stop]} applied, at "
                    f"{copies[(stop, base)]}")
        play([(stop, base, seed) for stop in stops for base, seed in lost])
    finally:
        for root in copies.values():
            shutil.rmtree(root, ignore_errors=True)
    summary = {plan: summarise(plan, sorted(rows[plan], key=lambda r: r["seed"])) for plan in plans}
    for plan in plans:
        say(f"SUMMARY {plan}: {json.dumps(summary[plan], ensure_ascii=False)}")
    results = verdicts(summary, rows)
    for ok, text in results:
        say(f"  [{'PASS' if ok else 'FAIL'}] {text}")
    verdict = "PASS" if results and all(ok for ok, _ in results) else "FAIL"
    say(f"VERDICT: {verdict}")
    out = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{args.evidence_tag}-RATE.txt"
    keep_earlier(out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"evidence: {out}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
