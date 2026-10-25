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
                     the name and gender in the save are the intro's intent AS THE RUN TOLD IT (its intro line; build
                     step 5.3: a HONESTY check, no longer recomputed by calling the AI's own chooser); TRAINED
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
                     (its told purchase; the game's purchase counter GAME_STAT_SHOPPED by the second path).
  CH2T, CH2M         (build step 5.1) a second and (the step-5.1 verifier's round) a THIRD chapter 2: from CH1T's end (Story,
                     seed 11) and CH1M's (Trainer, seed 13), each from the save ITS OWN chapter-1 run made; CH2M's claims
                     were registered before any run of its trajectory (`PREDICTED`).
(Build step 5.1) EVERY arm also: THE STALL PROPERTY (no screen waited for a press `AWAIT_MAX` frames with none, by the AI's
record of every look); every go goal with a map after the page that told it; THE INTENT MIX (a floor) and, the step-5.1
verifier's round, the CURIOSITY THE STORY DID NOT NEED in this run (`rate_step5.intent_mix` free_share >= FREE_RUN_MIN;
both shares of frames REPORTED since build step 5.2, its P2, with the old bound's verdict beside them) and
A NEW PLACE IS NEW (every look-around draw names a map the world memory it started from had not stood on: CH2T had "looked
round a new place, LITTLEROOT_TOWN", its home town).
(The step-5.1 verifier's second round: CH2T FAILED the intent-mix floor) the INTENT MIX is HONEST (`rate_step5.intent_mix`:
a goal ends at its end record, so a goal dropped for a scene no longer counts the scene; a curiosity goal the story moved
on in is the story's); the share with the scenes between goals counted as the story's is reported beside it. Chapter 2's
screens are graded by the game's second path in the sweep (`rate_step5.py` CH2): a launcher run has none while it plays.
Every arm keeps the tree it ran on (`provenance.snapshot_tree`).
(Build step 5.2, the safety gates) THE FROZEN-TREE WATCH (`provenance.FrozenTree`, G1): checked before and after every
arm (an arm whose files moved FAILS its check "FROZEN TREE"; once moved, no further arm runs) and sealed at OVERALL. THE
DISK BUDGET (`disk_budget.prune_runs`, G5): after grading, the profile's run folders are pruned (this invocation's, the
failing, the cited by name and the newest 12 kept; `--keep-runs` keeps all).
(Build step 5.2, PRODUCTIVE CURIOSITY, the step-5.1 adversarial review: "it LOAFS") every arm plays a NEW trajectory: its
seed is `LIVE_SEEDS` (14, 15, 16 in 5.2's first graded round; 17, 18, 19 since its verifier's round: never a live arm's seed
before, nor in a development sweep the docs list), so a 5.2 arm is a new trajectory, never a replay of 5.1's (seeds 11-13). And EVERY arm also, by the AI's own record (the game's second path of each is the sweep's): NO
LOAFING (the frames of curiosity goals whose END record says they brought nothing, at most `LOAF_FRAMES_MAX`); CURIOSITY
SPACED (at most `SPACING_ROW_MAX` curiosity goals in a row; the streak's frames reported); THE PUSHING PROPERTY (the longest
free overworld stretch of pressing that brought no new tile or map, `hands/waiting.py` PushWatch, under `PUSH_MAX`); THE
ASK STEP never walks to its house with nothing said; A PLACE IT HAS LEFT IS NO NEW PLACE (a look-around draw on a map it
stood on earlier in the run); its detours reported (place, said reached). The bounds are `rate_step5.BOUNDS`, registered
in the seed ledger before the graded sweep.
The fault arms (no training before the rival; no hints; the rest rule's fix removed; the MAX_LOSSES stop and the loop's
count removed; and 5.2's LOAF, BLOCKED and GREEDY controls) are the seed sweep's (`gates/rate_step5.py` NOTRAIN, NOHINTS, DEADREST, STOP, STOPDEAD): a win RATE and a
slowdown are frequency claims, which a sweep answers (CLAUDE.md rule 9).
(Build step 5.3, stage A1: B1 and N8) EVERY check above is TYPED (`gates/grader_checks.py`: an id `L5.*`, a kind, a status,
its inputs). The arm's verdict is PASS iff every GRADED and HONESTY check passes. The name and gender and the told wild
battles are HONESTY (the AI's word against the game). The 5.2 checks by the AI's own record (NO LOAFING, CURIOSITY SPACED,
THE PUSHING PROPERTY, THE ASK STEP) and the CH1 arms' pooled spins and rest occasions are DIAGNOSTIC: printed, never
counted; the sweep grades the game's side of them. This driver imports no value from the AI's code (the G-3 rule,
`check_grader_imports.py`, checked before any arm is played).
(Build step 5.3, the RE-SOURCING build, the A2 decision addendum's rows 16-19 and 28-39) NO check of this driver that
counts reads the AI any more except as the claim half of a HONESTY check (USER RULING 35; `b1_debt.json` holds no L5 row):
the pad's press and frame counts are HONESTY against the instrument (the AMENDMENT to A1-1: a HONESTY truth half may be the
harness); the brain's outcome is HONESTY against the game's proof of the target, both ways (`check_outcome`); "it shopped"
is GRADED by the game's own purchase counter alone (L5.SHOPPED_GAME: GAME_STAT_SHOPPED rose; the fix round replaced the
money-and-bag form, which misjudged a run that threw more balls than it bought or won prize money) and the told purchases
are HONESTY against it (no claim is a waived VACUOUS); who ended the run is REPORTED from the harness's stop record (`ended_check`); and the checks of the AI's
own trace (its presses' gates, A kinds, blind presses, goals, waits, new places, training, rest rule, end line, spins) are
DIAGNOSTIC. So the purity line above is graded as: the pad's counts honest, the brain's claim honest, the run's end
recorded. The game-only achievement checks (CAUGHT, HEALED, ITEMS, SHOPPED_GAME) are GRADED with no sweep control under the
re-sourcing plan's rule (e): each has a known-answer fault test both ways and a caught mutant (`test_step53_rs.py`).
(Build step 5.3, stage A2) The purity checks of `live_step2.check_purity` carry a real sample count and floor
(`PURITY_SAMPLES`: a run that left nothing to judge reads VACUOUS, not merely FAIL), and every arm RECORDS who ended it from
the harness's own counters, never the brain's text (`harness_stop`: the driver's own kill, the launcher's wall clock, the
frame budget, or the AI's own exit; the evidence's HARNESS STOP line). Recorded, not graded.
"""

from __future__ import annotations

import argparse
import json
import os
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

from ai_player.gates.live_step2 import (  # noqa: E402
    BREACH_COUNTERS, check_purity, classify_a, clean_env, hands_line, run_json,
)
from ai_player.gates.disk_budget import prune_runs  # noqa: E402
from ai_player.gates.provenance import keep_earlier, provenance as tree_provenance, snapshot_tree, watch  # noqa: E402
from ai_player.gates.grader_checks import (  # noqa: E402
    Check, CheckError, as_check, evidence_lines, grade, verdict as typed_verdict,
)
# (build step 5.3, A1-2, G-3) GENERIC_BUSY is the grader-owned copy (`rate_step5`), no longer the AI's `hands.dialogue`;
# the intro's intent comes from the run's OWN record (`logged_intent`), no longer from calling the AI's chooser
from ai_player.gates.rate_step5 import (  # noqa: E402
    BOUNDS, GENERIC_BUSY, MAP_DATA, aside_streaks, await_stretches, curiosity_rows, curiosity_streaks, intent_mix,
    map_keys, push_ai, roam_breaches, told_before, train_steps_min, training_windows,
)
from ai_player.host import launcher  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_CLOCK, ENV_PERSONALITY, ENV_SEED, ENV_STARTER, ENV_TARGET, ENV_WORLD,
)

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
    # seeds of 10: walks win battles too). `train_steps`: the training roams' steps; (the step-5.1 verifier's round: "carried
    # over, not re-derived") now the personality's own minimum times 0.9 (`rate_step5.train_steps_min`: Story 72, Catcher
    # 90, Trainer 135; the derivation is at `rate_step5.BOUNDS` CH1_TRAIN_STEPS_SHARE), and 3 WON (measured 4-18 over the 20
    # graded sweep runs of seeds 301-310 and 401-410)
    "CH1T": {"frames_max": 300000, "train_steps": train_steps_min("Story"), "wild_won": 3},
    "CH1C": {"frames_max": 300000, "train_steps": train_steps_min("Catcher"), "wild_won": 3},
    "CH1M": {"frames_max": 300000, "train_steps": train_steps_min("Trainer"), "wild_won": 3},
    "CH2": {"frames_max": 300000, "caught": 2, "heals": 1, "items": 1},
    # (build step 5.1) the second, independent chapter 2 (Story, seed 11, from CH1T's end): measured in development (in
    # process, the Story seed 11 CH1 end state, 2026-10-14, the tree of step 5.1's first round): 1 capture, 1 POKéMON CENTER
    # heal, 0 item balls (a Story player walks past more), balls bought; so items are REPORTED here (>= 0), the other claims
    # bounded. (The verifier's round: that development run was the live arm's own trajectory replayed. On this round's tree
    # no in-process run of seed 11, 12 or 13 was made, so no live arm replays a development run.)
    "CH2T": {"frames_max": 300000, "caught": 1, "heals": 1, "items": 0},
    # (the step-5.1 verifier's round: "CH2T replays its development trajectory") a THIRD chapter 2, the Trainer's, from
    # CH1M's own end (seed 13): its claims PRE-REGISTERED here before ANY run of that trajectory, in process or live, from
    # what the other two showed of chapter 2 and the Trainer's taste (catch_seek 0.45, balls_low 5): WALLY's tutorial, at
    # least 1 new capture, at least 1 POKéMON CENTER heal, balls bought; item balls reported (>= 0)
    "CH2M": {"frames_max": 300000, "caught": 1, "heals": 1, "items": 0},
    # (the step-5.1 verifier's second round) every claim above is KEPT as registered: the round's AI changes (the gym by its
    # look, the nearest place to heal, the balance, the first POKé BALLS tried) make all six arms NEW trajectories, never a
    # replay of `a883634`'s; in the round's development sweeps every chapter-2 run caught at least 1 and healed at least
    # once (18 of 18 in step51wdev2 and dev3), so the claims are not loosened
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
    #: (build step 5.3, A1-1) TYPED checks (`grader_checks.Check`; each still reads as `(status is PASS, text)`)
    checks: list[Check] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    measures: dict = field(default_factory=dict)
    #: (build step 5.1) the `read` records of the run(s) this one continues (their pages are in its world memory)
    earlier: list[dict] = field(default_factory=list)
    #: (the step-5.1 verifier's round) the world memory this run started from (a continuing arm's), or None
    world_in: Path | None = None
    #: (build step 5.3, stage A2, read v) this DRIVER killed the run's process tree at its own wall clock (`run_arm`)
    driver_killed: bool = False

    def check(self, ok: bool, text: str, check_id: str | None = None, n: int = 1, floor: int = 1) -> None:
        """(Build step 5.3, A1-1) One check of this arm, TYPED: `check_id` from `grader_checks.CHECKS` (its kind and inputs
        come from there); `n` what it examined (one run, unless a count is given), `floor` the fewest it may examine. A call
        with no id (`live_step2.check_purity`, which this stage may not edit) is typed by its text's title, and refused
        when no title fits (`as_check`). (Build step 5.3, stage A2 carry-over 4) such a check then gets its REAL sample
        count and floor from `PURITY_SAMPLES` (what it judged in this run), so it CAN read VACUOUS; an untyped id with no
        sample rule there is refused (`purity_sample`): no counting check reaches the verdict with n/floor "-"."""
        if check_id is None:
            check_id = as_check((bool(ok), text), "L5").id
            if check_id == "L5.PURITY_ENDED":
                # (build step 5.3, the RE-SOURCING build, item 10) re-made from the HARNESS's own stop record: the
                # untyped check read the brain's `exit_reason`, which the AI writes
                self.checks.append(ended_check(self, text))
                return
            n, floor = purity_sample(self, check_id)
        self.checks.append(grade(check_id, bool(ok), text, n, floor))

    @property
    def passed(self) -> bool:
        """(Build step 5.3) THE VERDICT by kind: every GRADED and HONESTY check PASS; a DIAGNOSTIC one never counts."""
        return typed_verdict(self.checks) == "PASS"

    @property
    def presses(self) -> list[dict]:
        return [r for r in self.records if str(r.get("action", "")).startswith(("press ", "hold "))]

    @property
    def outcome(self) -> str:
        return ((self.verdict or {}).get("facts") or {}).get("exit_reason") or ""


def _counters(run: Run) -> dict:
    return (run.verdict or {}).get("counters") or {}


def _facts(run: Run) -> dict:
    return (run.verdict or {}).get("facts") or {}


def _pad_presses(run: Run) -> int:
    found = re.search(r"presses=(\d+)", hands_line(run, "[AI-HANDS] outcome="))
    return int(found.group(1)) if found else 0


#: (build step 5.3, stage A2 carry-over 4) THE PURITY CHECKS' SAMPLES. `live_step2.check_purity` (outside this stage's
#: files) gives its checks no count, so before A2 the eight L5.PURITY_* checks reached the verdict with n/floor "-" and could
#: never read VACUOUS: a run that left no verdict file, no gate line or no presses read FAIL at best, and a check with
#: nothing to judge could not say so. Each now carries what it JUDGED in this run, by the same inputs its text reads:
#: check id -> (run -> n, floor).
PURITY_SAMPLES = {
    # the launcher's gate lines found in the run's output
    "L5.PURITY_GATE": (lambda run: sum(1 for line in run.stdout.splitlines() if line.startswith("[AI-GATE] exit=")), 1),
    # the instrument's verdict files read (0 or 1)
    "L5.PURITY_CLEAN": (lambda run: int("verdict" in (run.verdict or {})), 1),
    # the AI pad's own presses compared with the instrument's door count
    "L5.PURITY_PRESSES": (_pad_presses, 1),
    # the frames the instrument counted in the main loop
    "L5.PURITY_FRAMES": (lambda run: int(_counters(run).get("real_frames") or 0), 1),
    # the breach counters the verdict file holds, of the ones the check reads (all of them must be there)
    "L5.PURITY_BREACHES": (lambda run: sum(1 for key in BREACH_COUNTERS if key in _counters(run)), len(BREACH_COUNTERS)),
    # (build step 5.3, the RE-SOURCING build, items 10 and 12) L5.PURITY_ENDED and L5.PURITY_OUTCOME have no rule here any
    # more: the first is re-made from the harness's stop record (`ended_check`), the second graded as HONESTY once the
    # game's proofs are read (`check_outcome`); an untyped check of either id reaching `purity_sample` is refused
    # the verdict file's package root read (0 or 1)
    "L5.PURITY_PACKAGE": (lambda run: int("package_root" in _facts(run)), 1),
}


def purity_sample(run: Run, check_id: str) -> tuple[int, int]:
    """(Build step 5.3, stage A2 carry-over 4) The sample count and floor of a check that came with no id (`Run.check`),
    from `PURITY_SAMPLES`. RAISES `CheckError` for an id with no rule: a new untyped check must say what it judges."""
    rule = PURITY_SAMPLES.get(check_id)
    if rule is None:
        raise CheckError(f"{check_id}: an untyped check with no sample rule (`live_step5.PURITY_SAMPLES`): it would reach "
                         f"the verdict with n/floor '-'")
    count, floor = rule
    return int(count(run)), int(floor)


#: (build step 5.3, stage A2, read v) the exit codes the LAUNCHER's side gives a run it stopped (never the brain's
#: reason text): `host/launcher.py` WALL_CLOCK_EXIT 124 (its hard kill at the wall clock; `host/session.py`'s guard uses
#: the same code at the soft deadline), and `host/lifecycle.py` EXIT_FRAME_BUDGET 4 (`host/session.py` _on_frame: more
#: frames passed than the budget). A grader-owned copy of the 4 (G-3: the grader imports `host.launcher` only), TIED to
#: lifecycle's value by `test_step53_a2.LiveStopTests.test_the_frame_budget_exit_is_lifecycles_own` (it reads lifecycle
#: as TEXT, importing nothing, and goes red the day the two differ: a stale copy would read a frame-budget stop as "other")
FRAME_BUDGET_EXIT = 4


def harness_stop(run: Run) -> dict:
    """(Build step 5.3, stage A2, read v; `06` 2026-10-23 D3) WHO ENDED THIS LAUNCHER RUN, from the harness's own counters,
    never the brain's text: this driver's own wall clock (it killed the process tree, `Run.driver_killed`), the launcher's
    wall clock (exit code `launcher.WALL_CLOCK_EXIT`), the frame budget (exit code `FRAME_BUDGET_EXIT`), or the AI's own
    exit (exit code 0: the run ended with its verdict written and no stop by the harness). Any other code (a crash, a purity
    breach, a park) is "other". The instrument's frame count and the elapsed time sit beside it. Recorded in the arm's
    measures and evidence, NOT graded (stage A2)."""
    code = run.exit_code
    if run.driver_killed:
        by, cause = "harness", "the driver's own wall clock (process tree killed)"
    elif code == launcher.WALL_CLOCK_EXIT:
        by, cause = "harness", f"the launcher's wall clock (exit code {code})"
    elif code == FRAME_BUDGET_EXIT:
        by, cause = "harness", f"the frame budget (exit code {code})"
    elif code == 0:
        by, cause = "ai", "the AI exited by itself (exit code 0)"
    else:
        by, cause = "other", f"exit code {code}"
    return {"by": by, "cause": cause, "exit_code": code, "real_frames": _counters(run).get("real_frames"),
            "frame_budget": run.arm.frames, "elapsed_seconds": round(run.elapsed, 1), "wall_clock_seconds": run.arm.wall}


def ended_check(run: Run, purity_text: str) -> Check:
    """(Build step 5.3, the RE-SOURCING build, item 10: the A2 decision addendum's row 28) L5.PURITY_ENDED, REPORTED: who
    ended the run by the HARNESS's own stop record (`harness_stop`: this driver's kill, the launcher's wall clock, the frame
    budget, the AI's own exit, or other), PASS iff `by: ai`. It replaces `live_step2.check_purity`'s check of the same id,
    which read the verdict file's `exit_reason`: for a clean exit that is the BRAIN's own reason, so the AI's text could flip
    it (06 2026-10-23 D3). WHY REPORTED and not GRADED: every one of ledger #39's 154 runs reads `by: ai`, so no control in
    a sweep fails the read (METHOD: no third rule rescues a binary harness record); it is printed and never counts. Its read
    is guarded by known-answer unit tests, one per stop cause (`test_step53_rs.PurityEndedTests`). The old check's text,
    the brain's reason included, stays in the line as diagnostic text only; n is 1 (the harness always knows its own exit)."""
    stop = harness_stop(run)
    return grade("L5.PURITY_ENDED", stop["by"] == "ai",
                 f"ended by itself (REPORTED, never counted: the HARNESS's own stop record) by {stop['by']}: {stop['cause']}; "
                 f"real_frames {stop['real_frames']} (budget {stop['frame_budget']}); (diagnostic, NOT read: "
                 f"`check_purity`'s line, the brain's own reason in it) {purity_text}", 1)


def outcome_claim(run: Run, target: str) -> bool | None:
    """(Re-sourcing build item 12) The brain's CLAIM about the game in its exit reason: True for "<brain>: done: <target>
    reached", False for any other reason (a stop: stuck, out of ideas, a reason naming another target), None when the AI
    made no claim: no reason in the verdict file, or the run was not ended by the AI (`harness_stop`: the reason of a run the
    harness stopped or that crashed is not the AI's word)."""
    reason = _facts(run).get("exit_reason") or ""
    if not reason or harness_stop(run)["by"] != "ai":
        return None
    return reason == f"{run.arm.brain}: done: {target} reached"


def check_outcome(run: Run, target: str, proof: bool, proof_text: str) -> None:
    """(Build step 5.3, the RE-SOURCING build, item 12: the A2 decision addendum's row 18) L5.PURITY_OUTCOME, HONESTY: the
    brain's exit reason is a claim about the game, judged BOTH WAYS against the game's proof of the target (`proof`:
    L5.CH1_PROOFS' save-block flags for chapter 1, L5.CH2_WALLY's for chapter 2, the harness's own reads). A claim of
    "reached" with no proof is a lie, and so is a proof under a stop reason ("stuck" while the game shows the target).
    Before 5.3 it compared the reason with the wanted string alone (the AI's text against a constant: B1 debt). n is the
    claims made (`outcome_claim`: 0 when the AI made none, which is VACUOUS and fails the verdict, unwaived)."""
    claim = outcome_claim(run, target)
    reason = _facts(run).get("exit_reason") or ""
    run.check(claim is not None and claim == proof,
              f"the brain's outcome {reason!r} claims the target {target} "
              f"{'REACHED' if claim else 'NOT reached' if claim is not None else '(no claim: no reason, or the AI did not end the run)'}"
              f"; THE GAME's proof of it (the harness's own reads) {'HOLDS' if proof else 'does NOT hold'} ({proof_text}): "
              f"{'they agree' if claim == proof else 'they DISAGREE (a lie)'}", "L5.PURITY_OUTCOME",
              0 if claim is None else 1, 1)


def balls_total(truth: dict | None) -> int | None:
    """The POKé BALLS of every kind in the bag by the game (`truth_of`'s `balls`), None when the read is missing."""
    balls = (truth or {}).get("balls")
    return sum(balls.values()) if isinstance(balls, dict) else None


def shop_count(truth: dict | None) -> int | None:
    """The game's own count of purchases, GAME_STAT_SHOPPED (`play_harness.STATS` "shopped", read from save block 1 by the
    harness), None when the read is missing (a truth made before the fix round read no such counter)."""
    value = stats(truth).get("shopped")
    return value if isinstance(value, int) else None


def game_shopped(before: dict | None, after: dict | None) -> dict:
    """(Build step 5.3, the RE-SOURCING build, item 13: the re-sourcing plan's (c), REDEFINED in the fix round) "IT SHOPPED"
    BY THE GAME alone: the game's own purchase counter GAME_STAT_SHOPPED ROSE from the run's start (`Run.before`, the truth
    of its start state) to its end (`Run.after`), both read by the harness (`truth_of`), no AI input. The game raises it
    once per purchase, as the money is taken (`src/shop.c` BuyMenuSubtractMoney, pinned decomp 731ad5b).
    WHY not the money and the bag (the first form: money fell AND POKé BALLS rose): it misjudged both ways. A run that buys
    5 balls and throws 7, or wins more prize money than it spends, read "did not shop"; a run that lost money at a whiteout
    and picked up an item-ball POKé BALL read "shopped". The money and the balls are still printed (text only).
    `read` is False when either counter read is missing (nothing to judge)."""
    count0, count1 = shop_count(before), shop_count(after)
    read = count0 is not None and count1 is not None
    return {"read": read, "count": (count0, count1), "money": ((before or {}).get("money"), (after or {}).get("money")),
            "balls": (balls_total(before), balls_total(after)), "bought": (count1 - count0) if read else None,
            "shopped": read and count1 > count0}


def play_env(personality: str, starter: str | None, target: str, **extra: str) -> dict[str, str]:
    env = {ENV_PERSONALITY: personality, ENV_TARGET: target, ENV_CLOCK: WALL_CLOCK, **extra}
    if starter:
        env[ENV_STARTER] = starter
    return env


#: (build step 5.2, the step-5.1 final verifier: "LIVE ARMS ARE REPLAYS, now proven by a log diff": five of 5.1's six arms
#: replayed, record for record, the trajectories of an earlier tree) the arms play NEW seeds, 14, 15 and 16 (never played
#: by any arm or sweep: the sweeps' development seeds were 1-9, 21-29, 31-39, 41-49, 51-59, 61-72, 81-92 and 1000-1099, the
#: earlier arms' 11, 12 and 13), each a NEW trajectory on the host's clock: a sample, not a replay. (Build step 5.2, the
#: verifier's round) 17, 18 and 19: the code changed after the arms on 14-16, and the round's evidence must be NEW
#: trajectories again (no sweep plays them: the round's development seeds are 1201 and up, its graded ones 921-940)
LIVE_SEEDS = {"Story": 17, "Catcher": 18, "Trainer": 19}

ARMS: list[Arm] = [
    Arm("CH1T", "chapter 1 from a real New Game, TREECKO, Story: the POKéDEX, having trained before the rival", 330000,
        3600.0, play_env("Story", "TREECKO", "ch1_pokedex"), seed=LIVE_SEEDS["Story"]),
    Arm("CH1C", "chapter 1 from a real New Game, TORCHIC, Catcher: the POKéDEX, having trained before the rival", 330000,
        3600.0, play_env("Catcher", "TORCHIC", "ch1_pokedex"), seed=LIVE_SEEDS["Catcher"]),
    Arm("CH1M", "chapter 1 from a real New Game, MUDKIP, Trainer: the POKéDEX, having trained before the rival", 330000,
        3600.0, play_env("Trainer", "MUDKIP", "ch1_pokedex"), seed=LIVE_SEEDS["Trainer"]),
    Arm("CH2", "chapter 2 (stretch) from the CH1C arm's own end: Oldale's balls, ROUTE 102, PETALBURG, DAD, WALLY's tutorial",
        330000, 3600.0, play_env("Catcher", None, "ch2_wally"), seed=LIVE_SEEDS["Catcher"], fresh=False, state_from="CH1C"),
    # (build step 5.1, the step-5 review's finding 6: "CH2 is one Catcher trajectory replayed") a SECOND, INDEPENDENT
    # chapter 2: another personality and seed, from the save ITS OWN chapter-1 run made
    Arm("CH2T", f"chapter 2 (stretch), a second trajectory: from the CH1T arm's own end, Story, seed {LIVE_SEEDS['Story']}",
        330000, 3600.0, play_env("Story", None, "ch2_wally"), seed=LIVE_SEEDS["Story"], fresh=False, state_from="CH1T"),
    # (the step-5.1 verifier's round) a THIRD chapter 2, never played before it is graded: the Trainer's, from CH1M's end
    Arm("CH2M", f"chapter 2 (stretch), a third trajectory, pre-registered unseen: from the CH1M arm's own end, Trainer, seed "
                f"{LIVE_SEEDS['Trainer']}", 330000, 3600.0, play_env("Trainer", None, "ch2_wally"), seed=LIVE_SEEDS["Trainer"],
        fresh=False, state_from="CH1M"),
]


# ---------------------------------------------------------------------- running
def truth_of(state: Path) -> tuple[dict | None, str]:
    return run_json([sys.executable, str(HARNESS), "truth", str(state)], "TRUTH", clean_env({}), 600)


def run_arm(arm: Arm, build_root: Path, carried: dict[str, tuple[Path, Path, list]]) -> Run:
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
        state, world, earlier = carried[arm.state_from]
        # (build step 5.1) the pages the AI READ in the run it continues (its world memory carries them): a go goal may
        # quote one of those
        run.earlier = [r for r in earlier if r.get("decision") == "read"]
        run.world_in = world
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
        run.driver_killed = True
    run.elapsed = time.monotonic() - began
    run.exit_code = proc.returncode if proc.returncode is not None else -9
    run.stdout = raw_out.decode("utf-8", errors="replace")
    run.verdict = launcher.read_verdict(run.run_dir)
    # (build step 5.3, stage A2, read v) who ended the run, by the harness's own counters: recorded, not graded
    run.measures["harness_stop"] = harness_stop(run)
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
            carried[arm.name] = (keep, world, run.earlier + run.records)
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
              f"(start {before_md5 or '-: a fresh boot'})", "L5.THIS_RUN")


def check_hands(run: Run) -> None:
    """The AI's hands and goals by its OWN record (a launcher run has no second path while it plays). (Build step 5.3,
    A1-1) Typed: each check reads the AI's action log, so the GRADED ones are B1 debt (`b1_debt.json`); loafing, spacing,
    pushing and the ask step (5.2's AI-only checks) are DIAGNOSTIC: the sweep grades the game's side of them. (A1 fix
    round, ruling F4) the catch-all, the go goals after their page and the asides coming back are DIAGNOSTIC like their
    sweep twins (R5.CH1_CATCH_ALL, R5.GO_AFTER_PAGE, R5.ASIDE_BACK): those properties have no game form, so no debt row
    for them could ever be paid; the evidence lists them as no longer graded."""
    presses = run.presses
    no_gate = [p for p in presses if not p.get("reason")]
    run.check(bool(presses) and not no_gate, f"THE PRESSES: {len(presses)} presses in the action log, every one with its gate "
                                             f"(without: {len(no_gate)})", "L5.PRESS_GATES", len(presses))
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
                         f"the menus {dict(sorted(menus.items()))}; any other: {wrong[:4] or 'none'}", "L5.A_KINDS")
    blind = [p for p in presses if "NONE" in str(p.get("reason"))]
    run.check(not blind, f"no press without the eyes asked (a 'NONE' gate): {len(blind)}", "L5.BLIND")
    idle = [r for r in run.records if r.get("decision") == "watch"]
    generic = [(r["frame"], r["reason"]) for r in idle if str(r.get("reason", "")).startswith(GENERIC_BUSY)]
    run.check(not generic, f"THE CATCH-ALL: {len(idle)} stretches standing still, NONE under the catch-all "
                           f"{GENERIC_BUSY!r}: {generic[:3] or 'none'}", "L5.CATCH_ALL")
    goals = [r for r in run.records if r.get("decision") == "goal"]
    empty = [r for r in goals if not str(r.get("reason", "")).strip()]
    run.check(bool(goals) and not empty, f"NEVER WITHOUT A GOAL: {len(goals)} goals chosen, each with its reason (without: "
                                         f"{len(empty)}); kinds {count(r['action'] for r in goals)}", "L5.HAS_GOAL",
              len(goals))
    # (build step 5.1, the step-5 verifier's FAILURE: a stall of 600-1,200 frames under a NAMED reason passed the check
    # above) THE STALL PROPERTY: no screen waited for a press `AWAIT_MAX` frames or more with none, by the AI's own record of
    # every look (`hands/waiting.py`), whatever reason it gave meanwhile
    awaits = await_stretches(run.records)
    longest = max((a["frames"] for a in awaits), default=0)
    over = [(a["first"], a["frames"], str(a["what"])[:40], str(a["doing"])[:60]) for a in awaits
            if a["frames"] >= BOUNDS["AWAIT_MAX"]]
    noted = [r for r in run.records if r.get("decision") == "end" and (r.get("extra") or {}).get("waits")]
    run.check(not over and bool(noted), f"THE STALL PROPERTY (its record of every look): the longest a screen waited for a "
                                        f"press with none {longest} frames (bound under {BOUNDS['AWAIT_MAX']}, whatever the "
                                        f"reason); {len(awaits)} stretches of 60 or more; over the bound: {over or 'none'}; "
                                        f"its end record {(noted[0].get('extra') or {}).get('waits') if noted else 'MISSING'}",
              "L5.STALL", len(noted))
    # (the pages of the run it continues count as read before its first frame: its world memory carries them)
    bad = told_before([{**r, "frame": -1} for r in run.earlier] + run.records)
    run.check(not bad, f"EVERY GO GOAL WITH A MAP CAME AFTER THE PAGE THAT TOLD IT (its read records, and the "
                       f"{len(run.earlier)} pages of the run it continues): off {bad or 'none'}", "L5.GO_AFTER_PAGE")
    # (build step 5.2, PRODUCTIVE CURIOSITY) a curiosity goal counts by what it BROUGHT: in a launcher run by the AI's own
    # record of it (its END record's yield: the tiles its memory learned, a map, an item, a catch, words, a talk); the
    # game's second path is the sweep's (`rate_step5.py` curiosity_rows)
    curious = curiosity_rows(run.records, {}, 0)
    idle = {row["frame"] for row in curious if not row["ai"]}
    mix = intent_mix(run.records, idle)
    loaf = sum(row["walking_ai"] for row in curious if not row["ai"])  # its own time, outside battles (step52dev4)
    made = sum(row["frames"] for row in curious if row["ai"])
    run.check(loaf <= BOUNDS["LOAF_FRAMES_MAX"],
              f"NO LOAFING (its record of what each curiosity goal brought): {loaf} frames of curiosity that brought "
              f"nothing, its own time outside battles (bound <= {BOUNDS['LOAF_FRAMES_MAX']}); {made} frames that brought "
              f"something; by goal (kind, frame, "
              f"frames, productive) {[(r['kind'], r['frame'], r['frames'], int(r['ai'])) for r in curious][:12]}",
              "L5.NO_LOAFING", len(curious), None)
    # (its own names: the stall property's `longest` above is its measures' await_max; the 5.2 live arms first reported
    # this streak's frames under that name)
    rows = curiosity_streaks(run.records)
    most = max((s[1] for s in rows), default=0)
    row_frames = max((s[2] for s in rows), default=0)
    run.check(most <= BOUNDS["SPACING_ROW_MAX"],
              f"CURIOSITY SPACED: at most {most} curiosity goals in a row (bound <= {BOUNDS['SPACING_ROW_MAX']}); (reported) "
              f"the longest streak {row_frames} frames; streaks of 2+ (first frame, goals, frames) "
              f"{[s for s in rows if s[1] >= 2][:6] or 'none'}", "L5.SPACED", len(rows), None)
    pushed = push_ai(run.records)
    run.check(pushed < BOUNDS["PUSH_MAX"], f"THE PUSHING PROPERTY (its record of every look, `hands/waiting.py` PushWatch): "
                                           f"the longest free stretch of pressing that brought nothing new {pushed} frames "
                                           f"(bound under {BOUNDS['PUSH_MAX']}); the game's second path is the sweep's",
              "L5.PUSHING", 1, None)
    detours = [(r["frame"], r.get("place"), r["said_reached"]) for r in curious if r["kind"] == "detour"]
    run.notes.append(f"(reported) its detours (frame, place, said reached): {detours or 'none'}; the GAME's word on them is the "
                     f"sweep's (a launcher run has no second path while it plays)")
    asked = [r.get("frame") for r in run.records if r.get("decision") == "goal" and "to ask at" in str(r.get("reason"))
             and "nothing was said" in str(r.get("reason"))]
    run.check(not asked, f"THE ASK STEP WALKS TO ITS HOUSE ONLY WHEN TOLD (no 'to ask at ... nothing was said'): off "
                         f"{asked or 'none'}", "L5.ASK_STEP", 1, None)
    run.measures.update({"loaf_frames": loaf, "productive_frames": made, "streak_goals": most, "streak_frames": row_frames,
                         "push_ai": pushed, "detours": detours})
    # (the step-5.1 verifier's second round) honest: a goal's frames end at its END record (a goal dropped for a scene no
    # longer counts the scene after it), and a curiosity goal the story moved on in is the story's; (build step 5.2) and
    # a curiosity goal that brought nothing is no errand
    # (build step 5.2, P2: "grade YIELD and SPACING, not share of frames"; `rate_step5.P2_REPORTED`) the two shares of
    # frames are REPORTED with the old bound's own verdict beside them
    run.notes.append(f"(reported, 5.2 P2: a share of frames is not graded; the old bound "
                     f"{'HELD' if mix['errand_share'] >= BOUNDS['MIX_MIN'] else 'did NOT hold'}) THE INTENT MIX: "
                     f"{mix['errand_share']:.1%} of the goals' frames on errands (old bound >= {BOUNDS['MIX_MIN']:.0%}), "
                     f"{mix['errand_goals']} of {mix['goals']} goals; frames by kind {mix['frames']}; the story's own "
                     f"curiosity goals (counted as the story's) {mix['story_own']}; between goals (no goal's: scenes) "
                     f"{mix['between_goals']} frames; {mix['errand_share_with_scenes']:.1%} with those counted as the story's")
    run.notes.append(f"(reported, 5.2 P2: a share of frames is not graded; the old bound "
                     f"{'HELD' if mix['free_share'] >= BOUNDS['FREE_RUN_MIN'] else 'did NOT hold'}) CURIOSITY THE STORY "
                     f"DID NOT NEED: {mix['free_share']:.1%} of the goals' frames ({mix['free_frames']} frames; old bound >= "
                     f"{BOUNDS['FREE_RUN_MIN']:.0%}), the story's own curiosity goals not counted {mix['story_own']}")
    check_new_places(run)
    # (the step-5.1 verifier's round: CH2's ten asides in a row, about 32,000 frames) a story goal put aside comes back
    streaks = aside_streaks(run.records)
    long_ = [s for s in streaks if s[2] > BOUNDS["ASIDE_STREAK_MAX"]]
    run.check(not long_, f"A STORY GOAL PUT ASIDE COMES BACK: its streaks of asides (goal, first frame, frames, asides) "
                         f"{streaks or 'none (not exercised in this run)'} (each <= {BOUNDS['ASIDE_STREAK_MAX']} frames); "
                         f"over it: {long_ or 'none'}", "L5.ASIDE_BACK")
    run.measures.update({"await_max": longest, "intent_mix": mix, "asides": streaks})


def known_at_start(run: Run) -> set[str]:
    """The maps (consts) the world memory this run started from had STOOD on (a continuing arm's carried memory); empty for
    a New Game."""
    if run.world_in is None or not Path(run.world_in).is_file():
        return set()
    lines = [line for line in Path(run.world_in).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return set()
    data = json.loads(lines[-1])
    return {memory.get("const") for memory in (data.get("maps") or {}).values() if memory.get("visits")}


def check_new_places(run: Run) -> None:
    """(the step-5.1 verifier's round: "CH2T logged 'explore a new place, LITTLEROOT_TOWN' (its home town, walked all
    through chapter 1)") Every look-around draw, made or not (the goal's reason and the told line "a new place, X: it goes
    on without looking round"), names a map the world memory it STARTED from had never stood on."""
    known = known_at_start(run)
    named = []
    for r in run.records:
        text = str(r.get("reason") or "")
        found = re.search(r"a new place, ([A-Z0-9_]+)", text)
        if found and ((r.get("decision") == "goal" and r.get("action") == "explore")
                      or (r.get("decision") == "tell" and "it goes on without looking round" in text)):
            named.append((r.get("frame"), found.group(1)))
    old = [(frame, const) for frame, const in named if const in known]
    # (build step 5.2, the step-5.1 review's finding 6: CH1M said "a new place, OLDALE_TOWN" after healing there twice) nor
    # a map it had LEFT earlier in this run (its own record of its map changes: the navigator's MAP records). (Build step
    # 5.3, A1-1) a const's key from the framework's `MapRSE` (`rate_step5.map_keys`), no longer from its world.jsonl
    keys = map_keys(MAP_DATA)
    left = [(t[0], t[1]) for t in (((r.get("extra") or {}).get("transition")) for r in run.records
                                   if r.get("decision") == "world") if t]
    again = [(frame, const) for frame, const in named
             if any(source == keys.get(const) and at < (frame or 0) for at, source in left)]
    run.check(not old and not again,
              f"A NEW PLACE IS NEW: every look-around draw ({len(named)}: {sorted({c for _, c in named})}) names a map the "
              f"world memory it started from had not stood on ({len(known)} known at the start"
              f"{': ' + str(sorted(known)[:8]) if known else ': a New Game'}) and that it had not LEFT earlier in the run "
              f"(its record of {len(left)} map changes); a known one called new: {old or 'none'}; one left before: "
              f"{again or 'none'}", "L5.NEW_PLACE")


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
                            f"by a rest {len(rests)}", "L5.REST_RULE")
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
              f"{[str(r.get('reason'))[:40] for r in told]})", "L5.OWN_LOSSES")
    if fight is None:
        return
    prep = (note.get("fight_prep") or {}).get(fight) or {}
    wild, won = training_battles(run, fight)
    run.check(prep.get("wild") == wild and prep.get("won") == won and wild > 0,
              f"ITS END LINE'S TRAINING ({fight}: {prep}) == its log's wild battles in its training roams for it: met {wild}, "
              f"won {won} (and more than 0: the count the verifier found always 0)", "L5.OWN_TRAINING")


#: the intro's own told line (`skills/intro.py` play_intro: "intro: personality P (...): gender G (...), name 'N' (...)")
INTRO_TELL = re.compile(r"^intro: personality \S+ .*?: gender (?P<gender>[A-Z]+) .*?, name (?P<q>['\"])(?P<name>.*?)(?P=q) ")


def logged_intent(run: Run) -> tuple[str | None, str | None]:
    """(Build step 5.3, A1-2: G-3, "L:566-573's intent from the launcher run's own record") The intro's gender and name as
    the run ITSELF told them (its action log's intro tell line), the AI's word that the HONESTY check `L5.NAME_GENDER`
    judges against the game's save block 2. Before 5.3 the grader RECOMPUTED them by calling the AI's own chooser
    (`personality.pick_personality` / `choose_gender` / `choose_name`): the expected value was the code under test.
    (None, None): the run told no intent (the check then fails: the AI's word is missing)."""
    for record in run.records:
        if record.get("decision") != "tell":
            continue
        found = INTRO_TELL.match(str(record.get("reason") or ""))
        if found:
            return found.group("gender"), found.group("name")
    return None, None


# ---------------------------------------------------------------------- graders
def grade_common(run: Run, target: str) -> None:
    # (build step 5.3, the RE-SOURCING build, item 12) no wanted outcome is passed: `check_purity` then makes no check of
    # the brain's outcome against a constant string, and each grader judges that claim against the GAME's proof once it has
    # read it (`check_outcome`)
    check_purity(run, None)
    check_after_is_this_run(run)
    check_hands(run)
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames")
    bound = PREDICTED[run.arm.name]["frames_max"]
    run.check(isinstance(frames, int) and frames <= bound, f"BOUNDED: {frames} real frames <= the pre-registered {bound}",
              "L5.BOUNDED")
    run.measures["frames"] = frames
    run.measures["goals"] = count(r["action"] for r in run.records if r.get("decision") == "goal")


def grade_CH1(run: Run) -> None:
    arm, after = run.arm, run.after
    grade_common(run, "ch1_pokedex")
    m = marks(after)
    proofs = {name: m.get(name) for name in ("RECEIVED_POKEDEX_FROM_BIRCH", "SYS_POKEDEX_GET", "ADVENTURE_STARTED",
                                             "DEFEATED_RIVAL_ROUTE103", "SET_WALL_CLOCK", "RESCUED_BIRCH", "SYS_POKEMON_GET")}
    run.check(all(proofs.values()), f"THE GAME (save block 1, the harness's own read): {proofs}", "L5.CH1_PROOFS")
    check_outcome(run, "ch1_pokedex", all(proofs.values()), "L5.CH1_PROOFS' flags")
    # (build step 5.3, A1-2) HONESTY: the AI's OWN told intent judged against the game's save block 2 (no longer the
    # intent recomputed by calling the AI's chooser)
    gender, name = logged_intent(run)
    run.check(name is not None and (after or {}).get("name") == name and (after or {}).get("gender_name") == gender,
              f"THE GAME (save block 2): name {(after or {}).get('name')!r} gender {(after or {}).get('gender_name')} == the intro's "
              f"intent {name!r} {gender} (as the run itself told it, its intro line; seed {arm.seed})", "L5.NAME_GENDER",
              1 if name is not None else 0)
    party = (after or {}).get("party_exp") or []
    owner = {row[0]: row[1] for row in (after or {}).get("party_ot") or []}
    starter = arm.env[ENV_STARTER]
    first = party[0] if party else None
    run.check(first is not None and first[1].upper() == starter and owner.get(first[0]) == (after or {}).get("player_tid"),
              f"THE GAME (the framework's party decoder): the first Pokemon {first} is the {starter} the run named, its OT "
              f"{owner.get(first[0]) if first else None} == the player's {(after or {}).get('player_tid')}", "L5.STARTER_OT")
    balls = (after or {}).get("balls") or {}
    run.check(sum(balls.values()) >= 5, f"THE GAME (the bag): POKé BALLS {balls} (the rival's 5 after the POKéDEX)",
              "L5.BALLS")
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
              f"{len(wild_before)} met before the rival in all", "L5.TRAINED")
    check_rest_rule(run)
    check_own_report(run, "ch1_rival_route103")
    told = len(wild_battles(run))
    game = stats(after).get("wild_battles")
    # (build step 5.3) HONESTY: the AI's told count judged against the game's counter
    run.check(told == game, f"THE GAME AGREES WITH ITS COUNT: its told wild battles in all {told} == GAME_STAT_WILD_BATTLES "
                            f"{game} (the harness's own read of save block 1's counters)", "L5.TOLD_WILD")
    all_steps = sum((r.get("extra") or {}).get("steps", 0) for r in roams(run))
    spins = sum((r.get("extra") or {}).get("spins", 0) for r in roams(run))
    ratio = spins / all_steps if all_steps else 1.0
    # step 4.1 round 3's criterion (`rate_step3.py` ROAM_SPINS_PER_SEED): at most 5 spins in one run, and the CH1 arms'
    # spins TOGETHER under 2 % of their training steps (`main`); a per-run "< 2 %" fails 2 spins in 100 steps
    run.check(all_steps > 0 and spins <= SPINS_PER_RUN, f"ROAMING, NOT SPINNING: {spins} spins over {all_steps} training "
                                                        f"steps = {ratio:.4f} (at most {SPINS_PER_RUN} spins in a run; the CH1 "
                                                        f"arms together under 2 %: the overall line)", "L5.SPINS")
    run.measures.update({"rival_frame": rival, "train_steps_before": steps, "wild_before": len(wild_before),
                         "wild_won_training": won_training, "wild_met_training": met_training,
                         "wild_won_starter_to_rival": sum(1 for r in fought if r["extra"].get("outcome") == "won"),
                         "wild_total": told, "spin_ratio": round(ratio, 4), "spins": spins,
                         "roam_steps": all_steps, "game_stats": stats(after)})


def grade_CH2(run: Run) -> None:
    before, after = run.before, run.after
    grade_common(run, "ch2_wally")
    m = marks(after)
    wally = m.get("HIDE_PETALBURG_CITY_WALLYS_MOM") == 1 and (m.get("VAR_PETALBURG_GYM_STATE") or 0) >= 2
    run.check(wally, f"THE GAME: WALLY's tutorial: HIDE_PETALBURG_CITY_WALLYS_MOM {m.get('HIDE_PETALBURG_CITY_WALLYS_MOM')}, "
                     f"VAR_PETALBURG_GYM_STATE {m.get('VAR_PETALBURG_GYM_STATE')} (>= 2)", "L5.CH2_WALLY")
    check_outcome(run, "ch2_wally", wally, "L5.CH2_WALLY's flag and var")
    want = PREDICTED[run.arm.name]
    caught = stats(after).get("captures", 0) - stats(before).get("captures", 0)
    pids_before = {row[0] for row in (before or {}).get("party_exp") or []} | {row[0] for row in (before or {}).get("boxes") or []}
    tid = (after or {}).get("player_tid")
    new = [row for row in (after or {}).get("party_ot") or [] if row[0] not in pids_before and row[1] == tid]
    new += [row for row in (after or {}).get("boxes") or [] if row[0] not in pids_before and row[1] == tid]
    run.check(caught >= want["caught"] and len(new) >= want["caught"],
              f"CAUGHT: GAME_STAT_POKEMON_CAPTURES +{caught} and {len(new)} new PIDs with the player's OT {tid}: {new} "
              f"(>= {want['caught']})", "L5.CAUGHT")
    heals = stats(after).get("used_pokecenter", 0) - stats(before).get("used_pokecenter", 0)
    run.check(heals >= want["heals"], f"HEALED: GAME_STAT_USED_POKECENTER +{heals} (>= {want['heals']})", "L5.HEALED")
    picked = [name for name, value in items(after).items() if value and not items(before).get(name)]
    run.check(len(picked) >= want["items"], f"ITEMS: item-ball flags newly set {picked} (>= {want['items']})", "L5.ITEMS")
    check_rest_rule(run)
    check_own_report(run, None)
    # (build step 5.3, the RE-SOURCING build, item 13: the re-sourcing plan's (c)) "IT SHOPPED" is GRADED BY THE GAME alone
    # (an ACHIEVEMENT check under the plan's rule (e): its null, a run in which nothing was bought, is built directly by its
    # known-answer fault test); n 0 (a missing purchase-counter read, before or after) is VACUOUS, unwaived
    shop = game_shopped(before, after)
    run.check(shop["shopped"], f"SHOPPED, BY THE GAME (its own purchase counter GAME_STAT_SHOPPED, read by the harness, no "
                               f"AI input): {shop['count'][0]} -> {shop['count'][1]} (must RISE); (text only) money "
                               f"{shop['money'][0]} -> {shop['money'][1]}, POKé BALLS {shop['balls'][0]} -> {shop['balls'][1]}",
              "L5.SHOPPED_GAME", int(shop["read"]), 1)
    # its TOLD purchases are HONESTY, each judged by that same game read; none told is VACUOUS (no claim, no lie), WAIVED
    # (`grader_waivers.json`): "it shopped" is graded above, never by the AI's word
    bought = tells(run, "done; POKé BALL in the bag")
    run.check(shop["shopped"], f"SHOPPED (its told purchase): {len(bought)} told {[str(r['reason'])[:120] for r in bought[:2]]}; "
                               f"each must be true by THE GAME (its purchase counter rose): {shop['count'][0]} -> "
                               f"{shop['count'][1]}: {'TRUE' if shop['shopped'] else 'NOT shown by the game'}",
              "L5.SHOPPED", len(bought), 1)
    run.measures.update({"caught": caught, "heals": heals, "items": picked, "game_stats": stats(after)})


GRADERS = {"CH1T": grade_CH1, "CH1C": grade_CH1, "CH1M": grade_CH1, "CH2": grade_CH2, "CH2T": grade_CH2,
           "CH2M": grade_CH2}


def write_evidence(run: Run, code: str, tag: str) -> Path:
    out = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{tag}-{run.arm.name}.txt"
    keep_earlier(out)
    lines = [f"AI PLAYER BUILD STEP 5.3 (TYPED CHECKS, stage A1) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title} "
             f"(seed {run.arm.seed}: a NEW trajectory, never played by an arm or a sweep; one sample on the host's clock)",
             f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}",
             f"start: {'a real New Game (--fresh)' if run.arm.fresh else f'the end state of arm {run.arm.state_from}: {run.start_state}'}",
             f"command: {' '.join(run.command)}",
             f"env: {' '.join(f'{k}={v}' for k, v in sorted({ENV_BRAIN: 'play', ENV_SEED: str(run.arm.seed), **run.arm.env}.items()))}",
             f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
             # (build step 5.3, stage A2, read v) RECORDED, not graded
             f"HARNESS STOP: {json.dumps(run.measures.get('harness_stop') or harness_stop(run), ensure_ascii=False)}",
             f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
             "checks (pre-registered in ai_player/gates/live_step5.py's docstring and PREDICTED; each quotes both values; "
             "build step 5.3: typed, id kind n/floor inputs, a DIAGNOSTIC one never counts):"]
    lines += evidence_lines(run.checks)
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
    parser.add_argument("--evidence-tag", default="step52")
    parser.add_argument("--build-root", type=Path, default=launcher.resolve_build_root(None))
    # (build step 5.2, G5) the profile's older run folders are pruned after grading unless this is given
    parser.add_argument("--keep-runs", action="store_true", help="keep every run folder of the profile")
    args = parser.parse_args()
    wanted = [a.strip() for a in args.arms.split(",") if a.strip()]
    arms = [arm for arm in ARMS if arm.name in wanted]
    # (build step 5.3, A1-2, G-3) no arm is played while a grader takes a value from the AI's code
    from ai_player.gates.rate_step5 import grader_imports_line
    import_line = grader_imports_line()
    print(f"[LIVE5] {import_line}", flush=True)
    if not import_line.startswith("GRADER IMPORTS: PASS"):
        return 2
    code = tree_provenance(REPO)
    print(f"[LIVE5] code: {code}", flush=True)
    # (build step 5.2, G1) the frozen-tree watch (started by the code line): checked around every arm, sealed at OVERALL
    tree = watch(REPO, explicit=True)
    print(f"[LIVE5] frozen-tree watch: {len(tree.stats)} files, files digest {tree.digest}", flush=True)
    # (the step-5.1 verifier's second round: "the dee96b tree was not kept") the tree these arms run on is kept
    print(f"[LIVE5] tree kept: {snapshot_tree(REPO)}", flush=True)
    carried: dict[str, tuple[Path, Path, list]] = {}
    results = []
    for arm in arms:
        if tree.moved or not tree.check(f"before arm {arm.name}"):
            print(f"[LIVE5] arm {arm.name}: NOT RUN, the tree changed mid-run: {tree.moves[0][:300]}", flush=True)
            continue
        print(f"[LIVE5] arm {arm.name}: {arm.title}", flush=True)
        run = run_arm(arm, args.build_root, carried)
        GRADERS[arm.name](run)
        run.check(tree.check(f"after arm {arm.name}"),
                  f"FROZEN TREE: the files of the code under test did not change while this arm played "
                  f"({tree.moves[-1][:300] if tree.moves else 'unchanged'})", "L5.FROZEN")
        path = write_evidence(run, code, args.evidence_tag)
        results.append(run)
        print(f"[LIVE5] arm {arm.name}: {'PASS' if run.passed else 'FAIL'} ({run.elapsed:.0f}s) -> {path}", flush=True)
        for check in run.checks:
            if check.status != "PASS":
                print(f"    [{check.status}] {check.id} {check.kind}"
                      f"{' (never counts)' if check.kind in ('DIAGNOSTIC', 'REPORTED') else ''}: {check.text[:400]}",
                      flush=True)
    left = leftover_processes()
    print(f"[LIVE5] leftover emulator processes: {left or 'none'}", flush=True)
    chapter_1 = [r for r in results if r.arm.name.startswith("CH1")]
    spins = sum(r.measures.get("spins") or 0 for r in chapter_1)
    steps = sum(r.measures.get("roam_steps") or 0 for r in chapter_1)
    occasions = sum(r.measures.get("rest_occasions") or 0 for r in chapter_1)
    if chapter_1:
        # (build step 5.3, A1-1) the CH1 arms' pooled spins and rest occasions are DIAGNOSTIC: printed, never counted (both
        # read the AI's own roam and battle records; the sweep grades the game's side)
        pooled = [grade("L5.POOLED_SPINS", steps > 0 and spins / steps < 0.02,
                        f"the CH1 arms' spins together: {spins} over {steps} training steps = "
                        f"{(spins / steps if steps else 1.0):.4f} (< 0.02)", steps, 1),
                  grade("L5.REST_OCCASIONS", occasions >= 1,
                        f"the CH1 arms' occasions for the rest rule together (a battle in a roam that ended under the "
                        f"personality's heal_below): {occasions} (>= 1, so the rule's check is not vacuous); rests "
                        f"{[r.measures.get('rests') for r in chapter_1]}", occasions)]
        for line in evidence_lines(pooled):
            print(f"[LIVE5] {line.strip()}", flush=True)
    passed = all(run.passed for run in results) and not left and len(results) == len(arms)
    # (build step 5.2, G1) the frozen-tree watch seals the overall verdict
    overall, frozen_line = tree.seal("PASS" if passed else "FAIL")
    print(f"[LIVE5] {frozen_line}", flush=True)
    passed = overall == "PASS"
    # (G5) the profile's run folders: this invocation's, the failing, the cited and the newest kept; the rest deleted
    folders = {r.run_dir.parent for r in results if r.run_dir is not None}
    for runs in sorted(folders):
        print(f"[LIVE5] {prune_runs(runs, keep=[r.run_dir for r in results if r.run_dir], apply=not args.keep_runs)[2]}",
              flush=True)
    print(f"[LIVE5] OVERALL {'PASS' if passed else 'FAIL'}: " + ", ".join(f"{r.arm.name} {'PASS' if r.passed else 'FAIL'}"
                                                                            for r in results), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
