"""LIVE PROOF of AI-player build step 2 (the HANDS): the AI plays the intro, the nurse, the mart and the wall
clock ITSELF, through the real launcher, under the purity instrument.

    py -3.12 ai_player/gates/live_step2.py [--arms INTRO,XU,XBN,NURSE,MART,CLOCK,XBC,WBI,WBN,WBM,WBC,WBX,XTW,RATE]
                                           [--seed 3] [--evidence-tag step2]

Each arm runs the REAL launcher (`py -3.12 -m ai_player run`, which gates the real package first) with a hands
brain (`AI_PLAYER_BRAIN=intro|nurse|mart|clock`, `ai_player/mode.py` HandsBrain) and the pinned seed 3 (or
`--seed N`: the REPLICATION below), from a fresh boot or a pinned fixture. The grade has three parts, each
check quoting both values:
  1. PURITY: the gate passed on the real package; the instrument's verdict file says CLEAN; `ai_presses > 0`
     and EQUAL to twice the presses the AI's own pad counted (two counts: the instrument's at the emulator's
     door, where each press is a `hold_button` and a `release_button`, and the pad's in the AI's log); every
     breach counter 0 (`foreign_presses`, `foreign_writes`, `foreign_loads`,
     `ai_writes`, `ai_loads`, `ai_unrouted_presses`, `ai_bot_calls`, ...); the run ended by itself, code 0,
     within its frame budget.
  2. THE GAME, read by a SECOND PATH from the state the run LEFT (the framework writes `current_state.ss1` at
     shutdown; `gates/hands_harness.py truth` loads it in a throwaway emulator: save block 2's name and gender
     by the probe's own charmap, the party's HP by the framework's `get_party()`, money and the bag by the
     probe's own decoder (save block 1 XOR the key), the wall clock's flag and the intro's variable from save
     block 1's bits, the game's own local time `gLocalTime`, the ROM's Poke Ball price from `gItems`), never
     the AI's eyes. For the fixture arms the same truth is read on the fixture BEFORE the run. EVERY arm first
     asserts that the state graded is the one THIS run wrote (`check_after_is_this_run`): the file was written
     after the run started (a `--state` seed is copied with the fixture's old mtime, `shutil.copy2`; `--fresh`
     unlinks it), its frame counter is the start's plus the run's real frames (+-5), and a fixture arm's md5
     differs from the fixture's. (Added after the step-2 verifier found the fresh arms relied on the
     launcher's unlink without asserting it.)
  3. THE HANDS, from the AI's action log: every press names its gate; every A that advanced a text was pressed
     on a look that said the game WAITS (its record's digest says `waits=A/B(<the same reason>)`); the human
     pace (holds 3-7 frames, gaps 8-18, reading delays 18-150 frames, logged with the page read).

PRE-REGISTERED PREDICTIONS (2026-10-07, written before the graded runs, from the in-process harness
`gates/hands_harness.py` running the same code on the same starts; seed 3 = personality Catcher, P(GIRL)=0.6,
GIRL, name "Rosa", recomputed here from `ai_player/personality.py`):
INTRO  fresh boot -> the truck. PREDICT outcome "in the truck; intended Rosa (GIRL)"; truth: name "Rosa",
       gender 1 (GIRL), map (25,40) = MAP_INSIDE_OF_TRUCK (`data/maps/map_groups.json`); ~8,700 frames; ~55
       presses: ~21 A on text waits (printer 0 CLEAR / SCROLL_START), 1 A on the task wait before the keyboard,
       A on the main menu, the gender menu (after one Down) and the yes/no, the keyboard's keys and OK; "So it's
       Rosa?" read before YES.
XU     FAULT `AI_PLAYER_FAULT_UNGATED_A=1`, the same fresh boot and seed. PREDICT the same intent in the log
       (Rosa, GIRL) and the HARM in the game: the naive driver's A picks the gender menu's default and types the
       keyboard's top-left key until the name is full: truth name "AAAAAAA", gender 0 (BOY); every A gated NONE.
XBN    FAULT `AI_PLAYER_FAULT_BLIND_COUNT=1`, the same fresh boot and seed: the keyboard's cursor STARTS ON THE
       LAST KEY TYPED, not the top-left one. PREDICT a wrong name typed ("R" right, then wrong letters: "R.qq" in
       the harness), "So it's ...?" answered NO by the AI (it reads the name), retyped wrong again; the truck
       never reached within 12,000 frames; truth name != "Rosa".
NURSE  `tools/story-dev/saves/post_league_lobby.ss1` (the League lobby, the player at the nurse's counter
       facing LEFT; the party's Mightyena 202/227). PREDICT the AI turns up, talks, reads 2 pages, YES, reads,
       ends the conversation; outcome "healed"; truth: every party Pokemon at full HP after (Mightyena
       227/227), not before; ~7 presses, every A on a wait, the yes/no or the talk.
MART   `ai_player/gates/fixtures/mart_rustboro.ss1` (`make_mart_fixture.py`: inside the Rustboro Mart across
       the counter from the clerk, facing UP). PREDICT 5 Poke Balls bought: truth Poke Balls 5 -> 10, money
       6680 -> 5680 = 5 x the ROM's price 200; the quantity READ x1..x5; the list's "Here you go!" task wait.
CLOCK  `ai_player/gates/fixtures/clock_room.ss1` (`make_clock_fixture.py`: the AI's own intro, seed 7, then
       walked to the tile under the stopped clock; `VAR_LITTLEROOT_INTRO_STATE` 5). PREDICT the AI sets the
       computer's local time (logged), the hand held then stepped, A, the yes/no opened on NO and moved to YES,
       Mom's scene read to its end; truth: `FLAG_SET_WALL_CLOCK` set, the variable 6, `gLocalTime` = the time
       logged (or one minute later, if the seconds rolled over before the state was written).
XBC    FAULT `AI_PLAYER_FAULT_BLIND_COUNT=1` on the clock fixture. PREDICT "Is this the correct time?" answered
       NO (the count assumes the cursor starts on YES; it opens on NO): truth `FLAG_SET_WALL_CLOCK` clear and the
       variable still 5; the clock asked again and again.
Evidence: `ai_player/evidence/<date>-step2-<ARM>.txt`. Exit 0 only if every arm passed and no emulator is left.

REPLICATION, SEED 9 (pre-registered 2026-10-07, before its graded runs; added because the step-2 verifier
noted every arm was ONE trajectory per seed, and identical re-runs of seed 3 are a determinism check, not a
replication: CLAUDE.md rule 8). `--seed 9` draws another personality and other pacing (every hold, gap,
reading delay and think pause differs), so each arm is a SECOND trajectory with the same pass criteria. Seed 9
= personality Trainer, P(GIRL)=0.5, GIRL, name "Luna" (recomputed from `ai_player/personality.py`; GIRL keeps
XU's gender harm observable, "Luna" needs the page switch). The in-process harness (`hands_harness.py intro
--fresh --seed 9`, run first, development only) gave: INTRO "in the truck; intended Luna (GIRL)", 8,792 frames,
52 presses, truth "Luna" 1 (25,40); XU 4,530 frames, 247 presses, truth "AAAAAAA" 0; XBN not finished in 12,000
frames, truth "BELLA" 1 (0,0). PREDICT: INTRO in the truck, truth name "Luna", gender 1, map (25,40), ~8,792
frames; XU the same defaults as seed 3 (name "AAAAAAA", gender 0: the naive A's harm does not depend on the
seed); XBN the names asked about "L   " ("So it's L   ?": the counted presses typed spaces after the L), each
answered NO, and truth name "BELLA" != "Luna": the game's PRESET name, which Birch's speech writes before EVERY
keyboard opening (`src/main_menu.c` NewGameBirchSpeech_SetDefaultPlayerName(Random() % NUM_PRESET_NAMES); the
keyboard itself opens empty, `sPlayerNamingScreenTemplate.copyExistingString = FALSE`), left in the save because
the run ends during a retry; the truck never reached; NURSE, MART, CLOCK, XBC the same truths as seed 3 (healed
to 227/227; +5 balls, -1000 money; the flag set and the variable 6 at the computer's time; the flag clear and 5
under the fault).
Evidence: `ai_player/evidence/<date>-step2-seed9-<ARM>.txt`.

STEP 2.1 (pre-registered 2026-10-07, before the graded runs; the step-2 verifier's five weak proofs):
(1) THE GAME WAITED, not just the log: arms WBI, WBN, WBM, WBC run each real skill under `gates/probe_presses.py`,
    which, before EVERY A press, forks the frame and asks the game (module docstring there): no text printing,
    nothing moving in 300 frames with no input, A moves it, B instead does the same (a WAIT); the menu still and
    A doing something (a MENU); the player free and A starting a script (a TALK). Each also compares the forked run
    with an unforked `hands_harness.py` run (outcome, frames, presses equal: the forks touched nothing). PREDICT
    (from the in-process dev runs, seed 3): WBI 30 A presses (22 waits incl. ONE gated "task
    Task_NewGameBirchSpeech_WaitPressBeforeNameChoice (A or B)", 8 menus), every one proven, 8,664 frames 55 presses
    both ways, truth "Rosa" GIRL truck; WBN 6 A presses (1 talk, 3 text waits, 1 yes/no, 1 "script
    waitbuttonpress"); WBM 9 (1 talk, 1 text, 5 menus, ONE "task Task_ReturnToItemListAfterItemPurchase (A or B)",
    1 script wait), truth 10 balls, money 5680; WBC 10 (1 talk, 5 text, 2 script waits, the clock, the yes/no),
    the clock set to 13:37. CONTROL WBX: the ungated fault under the probe: >= 1 A on a text still printing and
    >= 1 on a screen moving by itself (dev: 118 printing, 90 more moving without printing, 35 still, of 243; the
    grader counts "moving" with the printing ones included: 208). FAULT XTW: a copy of the eyes whose TASK_WAITS
    lists the TIMER task Task_NewGameBirchSpeech_WaitToShowBirch: the AI presses A on it and the probe flags EVERY
    one (the timer moved on by itself), while the same run's other waits are all proven. (Written first as "dev: 5
    presses, f543-f693, 49-199 frames" from a TRUNCATED listing of the dev run; the dev run had 6, f543-f727, 15-199
    frames, and so did the graded run. Corrected after it; the prediction, every one flagged, is unchanged.)
(2) EVERY A press of a real launcher arm is classified from its look (`classify_a`: a wait, a menu confirm on that
    menu taking input, or a talk in the overworld) and none is anything else; still the log about itself, which is
    why (1) exists.
(3) No real launcher arm logs a stretch under the catch-all busy reason ("watching: the game is busy"): the eyes
    now report the fade and the scene (`ScreenState.fading`, `.scene`), and `busy_reason` names them. PREDICT 0.
(4) XBC's time is PINNED (`AI_PLAYER_CLOCK=13:37`): PREDICT "Is this the correct time?" answered with the cursor
    on NO 55 times (the in-process dev run), the same on every re-run. CLOCK keeps the computer's time (the default
    a person uses), so its numbers still move with the hour.
(5) RATE: each skill once per seed 1-20 in-process (`hands_harness.py`; the clock at `rate_clock(seed)`, spread over
    the day), each graded by its second-path truth. PREDICT 20 of 20 for each (CLAUDE.md rule 9: a frequency
    question takes a batch; with 0 failures of 20 the failure rate is below ~15% at 95%).
Evidence: `ai_player/evidence/<date>-step2-<ARM>.txt` (the new arms too). With `--seed 9` (the replication) every
arm but RATE runs again with the same pass criteria and no numbers predicted (RATE's seeds do not depend on --seed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.probe_presses import WAIT_GATE, gate_kind  # noqa: E402
from ai_player.hands.dialogue import GENERIC_BUSY, UNGATED_GATE  # noqa: E402
from ai_player.hands.menus import BLIND_GATE  # noqa: E402
from ai_player.host import launcher  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_CLOCK, ENV_FAULT_BLIND_COUNT, ENV_FAULT_UNGATED_A, ENV_MART_COUNT, ENV_SEED,
)
from ai_player.personality import choose_gender, choose_name, pick_personality  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
EVIDENCE_TAG = "step2"
HARNESS = GATES / "hands_harness.py"
PROFILE = "ai-step2-hands"
#: The pinned seed of the graded runs; `--seed` replaces it for a REPLICATION (main() sets it before any arm).
DEFAULT_SEED = 3
SEED = DEFAULT_SEED
#: How far the state's frame counter may be from the start's plus the run's real frames (measured: equal on the
#: fixture arms, +1 on a fresh boot).
FRAME_SLACK = 5
#: The fault-test of `check_after_is_this_run`, run by main() before any arm; quoted in every evidence file.
SELFTEST_LINE = "[SELFTEST] not run"
#: (path, md5) PINNED.
FIXTURES: dict[str, tuple[Path, str]] = {
    "post_league_lobby.ss1": (SAVES / "post_league_lobby.ss1", "5a75ea37ed5cc07ae8b0b0a75da5e909"),
    "mart_rustboro.ss1": (GATES / "fixtures" / "mart_rustboro.ss1", "830ed079b0a7d4f20be9160c2ac51de7"),
    "clock_room.ss1": (GATES / "fixtures" / "clock_room.ss1", "5d1d0ce0974470bf11040fc39f832041"),
}
BREACH_COUNTERS = (
    "foreign_presses", "foreign_writes", "foreign_loads", "ai_writes", "ai_loads", "ai_unrouted_presses", "ai_bot_calls",
    "extra_frames", "unattributed_inputs", "unattributed_state_changes", "instrument_tampered", "instrument_errors",
    "ran_after_finish", "isolation_lost",
)
INTRO_MAP = [25, 40]  # data/maps/map_groups.json: InsideOfTruck is group 25, number 40
#: STEP 2.1: the time XBC's clock is set to (pinned, so the fault arm reproduces exactly: with the computer's time
#: the hand travels a different distance at every hour, and the count of NO answers moved, 50 then 51 for seed 3).
#: The same pinned time for WBC (the behaviour of every press does not depend on the time).
PINNED_CLOCK = "13:37"
#: STEP 2.1: the press-behaviour probe (`gates/probe_presses.py`) and the in-process harness it is compared with.
PRESSES = GATES / "probe_presses.py"
#: STEP 2.1: arm RATE's seeds (each skill once per seed, in-process).
RATE_SEEDS = tuple(range(1, 21))
#: STEP 2.1: arm XTW's mutant: a TIMER task (src/main_menu.c Task_NewGameBirchSpeech_WaitToShowBirch counts tTimer
#: = 0xD8 down and moves on by itself; it polls no button) listed in the eyes' TASK_WAITS.
XTW_ANCHOR = '    "Task_NewGameBirchSpeech_WaitPressBeforeNameChoice": "A or B",  # src/main_menu.c, after "...your name?"\n'
XTW_MUTATION = ("eyes/screens.py", XTW_ANCHOR, XTW_ANCHOR + '    "Task_NewGameBirchSpeech_WaitToShowBirch": "A or B",  # MUTANT XTW\n')


@dataclass
class Arm:
    name: str
    title: str
    brain: str
    fixture: str | None  # None: --fresh (a New Game from the title screen)
    frames: int
    wall: float
    env: dict[str, str] = field(default_factory=dict)
    doc: str = ""
    #: STEP 2.1: "launcher" (the real launcher, under the purity instrument), "probe" (`gates/probe_presses.py`, every
    #: A press checked against the game's behaviour, in a throwaway emulator) or "rate" (the in-process harness, many
    #: seeds).
    kind: str = "launcher"
    args: tuple[str, ...] = ()  # extra arguments of the probe
    mutations: tuple[tuple[str, str, str], ...] = ()  # a probe arm run from a COPY of the package with these edits


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
    state_mtime: float | None = None  # when the state graded was last written (None: no state file)
    checks: list[tuple[bool, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    probe: dict | None = None  # STEP 2.1: a probe arm's PRESSES result (`gates/probe_presses.py`)
    harness: dict | None = None  # STEP 2.1: the unforked in-process run of the same start (`gates/hands_harness.py`)
    sweep: list[dict] = field(default_factory=list)  # STEP 2.1: arm RATE's runs

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)

    @property
    def outcome(self) -> str:
        return ((self.verdict or {}).get("facts") or {}).get("exit_reason") or ""

    @property
    def presses(self) -> list[dict]:
        return [r for r in self.records if str(r.get("action", "")).startswith(("press ", "hold "))]


ARMS: list[Arm] = [
    Arm("INTRO", "a New Game from the title screen to the truck, played by the AI (seed 3: Rosa, GIRL)", "intro", None, 16000, 900.0),
    Arm("XU", "FAULT ungated A: the same New Game with the naive driver (A on the cadence, no wait gate)", "intro", None, 16000,
        900.0, {ENV_FAULT_UNGATED_A: "1"}),
    Arm("XBN", "FAULT blind count: the same New Game, the keyboard moved by counts from the top-left key", "intro", None, 12000,
        900.0, {ENV_FAULT_BLIND_COUNT: "1"}),
    Arm("NURSE", "heal at the Pokemon League's nurse", "nurse", "post_league_lobby.ss1", 6000, 600.0,
        doc="FIXTURES.md5: EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (3,4) (LEAGUE_NURSE_STAND), the L75 party, 0 battles fought"),
    Arm("MART", "buy 5 Poke Balls at the Rustboro Mart", "mart", "mart_rustboro.ss1", 8000, 600.0, {ENV_MART_COUNT: "5"},
        doc="ai_player/gates/make_mart_fixture.py (its printout: gates/fixtures/mart_rustboro.build.json)"),
    Arm("CLOCK", "set the wall clock in the player's room to the computer's time", "clock", "clock_room.ss1", 10000, 600.0,
        doc="ai_player/gates/make_clock_fixture.py (its printout: gates/fixtures/clock_room.build.json)"),
    Arm("XBC", "FAULT blind count on the clock: 'Is this the correct time?' opens on NO", "clock", "clock_room.ss1", 6000, 600.0,
        {ENV_FAULT_BLIND_COUNT: "1", ENV_CLOCK: PINNED_CLOCK}, doc="as CLOCK; the time PINNED (step 2.1) so the arm reproduces"),
    # STEP 2.1: every A press against the GAME'S BEHAVIOUR (`gates/probe_presses.py`), in a throwaway emulator
    Arm("WBI", "BEHAVIOUR of every A press: the intro (incl. the task wait after 'your name?')", "intro", None, 16000, 900.0,
        kind="probe", doc="gates/probe_presses.py intro --fresh, and gates/hands_harness.py (unforked) for the determinism check"),
    Arm("WBN", "BEHAVIOUR of every A press: the nurse (incl. the script's waitbuttonpress)", "nurse", "post_league_lobby.ss1", 6000,
        600.0, kind="probe", doc="as NURSE"),
    Arm("WBM", "BEHAVIOUR of every A press: the mart (incl. the task wait after 'Here you go!')", "mart", "mart_rustboro.ss1", 8000,
        600.0, kind="probe", args=("--mart-count", "5"), doc="as MART"),
    Arm("WBC", "BEHAVIOUR of every A press: the wall clock", "clock", "clock_room.ss1", 10000, 600.0, kind="probe",
        args=("--clock", PINNED_CLOCK), doc="as CLOCK, the time pinned"),
    Arm("WBX", "CONTROL of the behaviour probe: the ungated fault's A presses (the probe must say 'not waiting')", "intro", None,
        16000, 900.0, kind="probe", args=("--fault", "ungated_a"), doc="as XU"),
    Arm("XTW", "FAULT: a timer task listed as a wait in a COPY of the eyes; the probe must catch the A pressed on it", "intro",
        None, 16000, 900.0, kind="probe", mutations=(XTW_MUTATION,), doc="gates/probe_presses.py from a copy of the package"),
    Arm("RATE", f"RATE: each skill once per seed {RATE_SEEDS[0]}-{RATE_SEEDS[-1]}, in-process (gates/hands_harness.py)", "all",
        None, 16000, 1800.0, kind="rate", doc="in-process: the skills' code; the purity of the same code is the launcher arms'"),
]


# ---------------------------------------------------------------------- running
def clean_env(extra: dict[str, str]) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env["PYTHONUTF8"] = "1"
    env.update(extra)
    return env


def truth_of(state: Path) -> tuple[dict | None, str]:
    done = subprocess.run([sys.executable, str(HARNESS), "truth", str(state)], cwd=str(REPO), env=clean_env({}),
                          capture_output=True, timeout=300)
    raw = done.stdout.decode("utf-8", errors="replace") + done.stderr.decode("utf-8", errors="replace")
    for line in raw.splitlines():
        if line.startswith("TRUTH "):
            return json.loads(line[len("TRUTH "):]), raw
    return None, raw


def run_arm(arm: Arm, build_root: Path) -> Run:
    run = Run(arm)
    profile_dir, _ = launcher.ensure_profile(build_root, PROFILE)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {PROFILE} is not ai_player-owned; refusing to touch it")
    launcher.force_http_off(profile_dir)
    cheats = profile_dir / "game_cheats.yml"
    if cheats.exists():
        cheats.unlink()
    if arm.fixture is not None:
        run.before, raw = truth_of(FIXTURES[arm.fixture][0])
        if run.before is None:
            run.notes.append(f"truth of the fixture failed: {raw[-1500:]}")
    run.run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    start = ["--fresh"] if arm.fixture is None else ["--state", str(FIXTURES[arm.fixture][0])]
    run.command = [sys.executable, "-m", "ai_player", "run", "--profile", PROFILE, "--frames", str(arm.frames),
                   "--wall-seconds", f"{arm.wall:g}", "--build-root", str(build_root), "--run-dir", str(run.run_dir), *start]
    env = clean_env({ENV_BRAIN: arm.brain, ENV_SEED: str(SEED), **arm.env})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    run.started = time.time()
    began = time.monotonic()
    proc = subprocess.Popen(run.command, cwd=str(REPO), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, creationflags=flags)
    try:
        raw_out, _ = proc.communicate(timeout=arm.wall + 240)
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
        run.records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
    log = run.run_dir / "ai_player.log"
    if log.is_file():
        run.ai_log = log.read_text(encoding="utf-8", errors="replace")
    state = profile_dir / launcher.STATE_FILE
    if state.is_file():
        run.state_mtime = state.stat().st_mtime
        run.after, raw = truth_of(state)
        if run.after is None:
            run.notes.append(f"truth of the state left behind failed: {raw[-1500:]}")
    return run


# ---------------------------------------------------------------------- step 2.1: the probe and the rate
def start_args(arm: Arm, fixture: str | None = None) -> list[str]:
    fixture = arm.fixture if fixture is None else fixture
    return ["--fresh"] if fixture is None else ["--state", str(FIXTURES[fixture][0])]


def run_json(command: list[str], prefix: str, env: dict[str, str], timeout: float) -> tuple[dict | None, str]:
    """A test-side script that prints one `<prefix> {json}` line; (that JSON or None, the raw output)."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    proc = subprocess.Popen(command, cwd=str(REPO), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, creationflags=flags)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        launcher.kill_tree(proc)
        out, _ = proc.communicate()
        out = (out or b"") + b"\n[DRIVER] the script overran the driver's own wall clock; process tree killed\n"
    raw = (out or b"").decode("utf-8", errors="replace")
    for line in raw.splitlines():
        if line.startswith(prefix + " "):
            return json.loads(line[len(prefix) + 1:]), raw
    return None, raw


def make_copy(mutations: tuple[tuple[str, str, str], ...]) -> Path:
    """A temporary copy of the real package with each (file, old, new) applied exactly once (as `revert_step2.py`)."""
    root = Path(tempfile.mkdtemp(prefix="ai_player_step21_"))
    shutil.copytree(REPO / "ai_player", root / "ai_player", ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
    for relative, old, new in mutations:
        path = root / "ai_player" / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"mutation anchor not unique in {relative} ({text.count(old)} hits): {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    return root


def run_probe_arm(arm: Arm) -> Run:
    """`gates/probe_presses.py` on the arm's start (from a COPY of the package when the arm has mutations), then,
    for a real arm, the unforked `gates/hands_harness.py` run of the same start for the determinism check."""
    run = Run(arm)
    common = [arm.brain, *start_args(arm), "--seed", str(SEED), "--frames", str(arm.frames), *arm.args]
    root = make_copy(arm.mutations) if arm.mutations else None
    script = PRESSES if root is None else root / "ai_player" / "gates" / PRESSES.name
    env = clean_env({} if root is None else {launcher.ENV_BUILD_ROOT: str(REPO / "sandbox-pokebot")})
    run.command = [sys.executable, str(script), *common]
    run.started = time.time()
    began = time.monotonic()
    try:
        run.probe, raw = run_json(run.command, "PRESSES", env, arm.wall)
    finally:
        if root is not None:
            shutil.rmtree(root, ignore_errors=True)
    if run.probe is None:
        run.notes.append(f"the probe printed no PRESSES line: {raw[-2000:]}")
    if not arm.mutations:
        harness_command = [sys.executable, str(HARNESS), *common, "--run-dir",
                           tempfile.mkdtemp(prefix=f"ai_step21_{arm.name}_")]
        run.harness, raw = run_json(harness_command, "HANDS", clean_env({}), arm.wall)
        if run.harness is None:
            run.notes.append(f"the unforked harness printed no HANDS line: {raw[-2000:]}")
    run.elapsed = time.monotonic() - began
    run.exit_code = 0 if run.probe is not None else 1
    return run


def rate_clock(seed: int) -> str:
    """Arm RATE's clock time for a seed: spread over the day, so the hand travels a different way each time."""
    return f"{(seed * 5) % 24}:{(seed * 13) % 60:02d}"


def run_rate_arm(arm: Arm) -> Run:
    """Every skill once per seed of RATE_SEEDS, in-process (`gates/hands_harness.py`), each graded by its own truth."""
    run = Run(arm)
    run.started = time.time()
    began = time.monotonic()
    plans = [("intro", None, ()), ("nurse", "post_league_lobby.ss1", ()), ("mart", "mart_rustboro.ss1", ("--mart-count", "5")),
             ("clock", "clock_room.ss1", None)]
    for seed in RATE_SEEDS:
        for brain, fixture, args in plans:
            extra = ("--clock", rate_clock(seed)) if args is None else args
            command = [sys.executable, str(HARNESS), brain, *start_args(arm, fixture), "--seed", str(seed), "--frames",
                       str(16000 if brain == "intro" else 10000), *extra, "--run-dir", tempfile.mkdtemp(prefix="ai_step21_rate_")]
            data, raw = run_json(command, "HANDS", clean_env({}), 600)
            entry = {"seed": seed, "brain": brain, "fixture": fixture, "args": list(extra), "data": data,
                     "raw": None if data is not None else raw[-1500:]}
            run.sweep.append(entry)
            print(f"  RATE seed {seed} {brain}: {(data or {}).get('reason')!r} frames {(data or {}).get('frames')}", flush=True)
            if time.monotonic() - began > arm.wall:
                run.notes.append(f"the sweep stopped at its wall clock ({arm.wall:g} s), after seed {seed} {brain}")
                break
        else:
            continue
        break
    run.elapsed = time.monotonic() - began
    run.exit_code = 0
    return run


# ---------------------------------------------------------------------- shared checks
def hands_line(run: Run, prefix: str) -> str:
    return next((line for line in run.ai_log.splitlines() if line.startswith(prefix)), "")


def check_purity(run: Run, want_outcome: str | None) -> None:
    gate = next((line for line in run.stdout.splitlines() if line.startswith("[AI-GATE] exit=")), "")
    run.check("verdict=PASS" in gate and gate.endswith(f"package={REPO / 'ai_player'}"), f"the launcher gated the real package: {gate or 'MISSING'}")
    verdict = run.verdict or {}
    counters = verdict.get("counters") or {}
    facts = verdict.get("facts") or {}
    run.check(verdict.get("verdict") == "CLEAN", f"verdict file: verdict={verdict.get('verdict')} (want CLEAN)")
    summary = hands_line(run, "[AI-HANDS] outcome=")
    pad = re.search(r"presses=(\d+)", summary)
    pad_presses = int(pad.group(1)) if pad else None
    # Every pad press is ONE `Controls.hold` (`hands/pad.py`): the controller calls `hold_button` and then
    # `release_button`, and the instrument counts every call of an input method at the emulator's door
    # (`host/attribution.py` EMULATOR_INPUT_METHODS): 2 per press.
    run.check((counters.get("ai_presses") or 0) > 0 and pad_presses is not None and counters.get("ai_presses") == 2 * pad_presses,
              f"ai_presses={counters.get('ai_presses')} (the instrument, at the emulator's door: hold_button + release_button) == "
              f"2 x the AI pad's own count {pad_presses} ({summary or 'no [AI-HANDS] outcome line'}), and > 0")
    nonzero = {k: counters.get(k) for k in BREACH_COUNTERS if counters.get(k) != 0}
    run.check(not nonzero, f"every breach counter 0, incl. foreign_presses={counters.get('foreign_presses')} foreign_writes="
                           f"{counters.get('foreign_writes')} foreign_loads={counters.get('foreign_loads')} ai_bot_calls="
                           f"{counters.get('ai_bot_calls')} (non-zero: {nonzero or 'none'})")
    reason = facts.get("exit_reason") or ""
    run.check(facts.get("exit_code") == 0 and run.exit_code == 0 and not reason.startswith(("frame-budget", "wall-clock")),
              f"ended by itself: exit_reason={reason!r} exit_code={facts.get('exit_code')} process={run.exit_code} "
              f"real_frames={counters.get('real_frames')} (budget {run.arm.frames})")
    if want_outcome is not None:
        run.check(reason == f"{run.arm.brain}: {want_outcome}", f"the brain's outcome: {reason!r} (want {run.arm.brain}: {want_outcome!r})")
    run.check(facts.get("package_root") == str(REPO), f"the verdict file names the package that ran: {facts.get('package_root')}")


def check_after_is_this_run(run: Run) -> None:
    """The state graded is the one THIS run wrote, asserted, not assumed: written after the run started (a `--state`
    seed keeps the fixture's old mtime, `shutil.copy2`; `--fresh` unlinks the old state, `host/launcher.py`
    seed_profile), its frame counter is the start's plus this run's real frames (+-FRAME_SLACK: a state left
    by a LONGER or SHORTER earlier run fails), and a fixture arm's state differs from the fixture."""
    after = run.after or {}
    before_md5 = FIXTURES[run.arm.fixture][1] if run.arm.fixture else None
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    start_frame = (run.before or {}).get("frame") or 0  # a fresh boot starts at frame 0
    frame = after.get("frame")
    written = run.state_mtime is not None and run.state_mtime >= run.started - 1.0
    near = isinstance(frame, int) and frames > 0 and abs(frame - (start_frame + frames)) <= FRAME_SLACK
    run.check(bool(after) and written and near and (before_md5 is None or after.get("state_md5") != before_md5),
              f"the state graded is the one THIS run wrote: written "
              f"{'%.1fs after the run started' % (run.state_mtime - run.started) if run.state_mtime else 'NEVER (no state file)'}; "
              f"frame {frame} == start {start_frame} + {frames} real frames (+-{FRAME_SLACK}); md5 {after.get('state_md5')} "
              f"(fixture {before_md5 or '-: a fresh boot'})")


def selftest_after_check() -> list[str]:
    """FAULT-TEST of `check_after_is_this_run` (CLAUDE.md rule 6), on synthetic runs, before any arm: it passes a
    state this run wrote and fails each way a graded state could be someone else's. Returns the failures."""
    fresh, fixture = ARMS[0], next(a for a in ARMS if a.fixture is not None)

    def verdict(arm: Arm, mtime: float | None, frame: int | None, md5: str, start_frame: int | None = None) -> bool:
        run = Run(arm, started=1000.0, state_mtime=mtime,
                  verdict={"counters": {"real_frames": 8664}},
                  before=None if start_frame is None else {"frame": start_frame},
                  after=None if frame is None else {"frame": frame, "state_md5": md5})
        check_after_is_this_run(run)
        return run.passed

    cases = [
        ("a fresh run's own state (+1 frame, written after the start)", verdict(fresh, 1500.0, 8665, "abc"), True),
        ("a STALE state from before the run (mtime before the start)", verdict(fresh, 900.0, 8665, "abc"), False),
        ("a state of a LONGER earlier run (frame +3000)", verdict(fresh, 1500.0, 11664, "abc"), False),
        ("a state of a SHORTER run (frame -3000)", verdict(fresh, 1500.0, 5664, "abc"), False),
        ("no state file at all", verdict(fresh, None, None, "abc"), False),
        ("a fixture arm's own state", verdict(fixture, 1500.0, 108664, "abc", 100000), True),
        ("a fixture arm's seed copy, never rewritten (the fixture's md5)",
         verdict(fixture, 1500.0, 108664, FIXTURES[fixture.fixture][1], 100000), False),
    ]
    return [f"{name}: passed={got}, want {want}" for name, got, want in cases if got != want]


def check_gates(run: Run, allow_faults: bool = False) -> dict:
    """Every press names a gate; every A that advanced a text was pressed on a look that WAITED; the pace."""
    presses = run.presses
    no_gate = [p for p in presses if not p.get("reason")]
    run.check(bool(presses) and not no_gate, f"{len(presses)} presses in the action log, every one with its gate (without: {len(no_gate)})")
    text_a = [p for p in presses if p["action"].startswith("press A ") and WAIT_GATE.match(p["reason"] or "")]
    mismatched = [p for p in text_a if f"waits=A/B({p['reason']})" not in (p.get("digest") or "")]
    run.check(allow_faults or (bool(text_a) and not mismatched),
              f"{len(text_a)} A presses advanced a text, each on a look whose digest says waits=A/B(<that reason>) "
              f"(mismatched: {[(p['frame'], p['reason']) for p in mismatched][:5] or 'none'})")
    faulty = [p for p in presses if p["reason"] in (UNGATED_GATE, BLIND_GATE)]
    if not allow_faults:
        run.check(not faulty, f"no press of a FAULT gate in a real run: {len(faulty)}")
        # STEP 2.1 (the step-2 verifier: only NURSE limited the OTHER A presses): EVERY A press is one of three
        # kinds, and its look says the screen took it. This is still the log agreeing with itself (the gate and
        # the digest are one look); that the GAME took each press is arms WBI, WBN, WBM, WBC (`probe_presses.py`).
        kinds: dict[str, int] = {}
        wrong = []
        for press in (p for p in presses if p["action"].startswith("press A ")):
            kind, ok = classify_a(press)
            kinds[kind] = kinds.get(kind, 0) + 1
            if not ok:
                wrong.append((press["frame"], kind, press["reason"][:60], (press.get("digest") or "")[:90]))
        run.check(bool(kinds) and not wrong,
                  f"EVERY A press is a WAIT (its look: waits=A/B(<that gate>), no menu), a MENU confirm (its look: that menu "
                  f"open and taking input, ui=<kind>[...], nothing waiting) or a TALK (its look: the overworld, nothing "
                  f"waiting, no menu): {dict(sorted(kinds.items()))}; any other: {wrong[:4] or 'none'}")
        # STEP 2.1 (the step-2 verifier: 530 frames of Birch's opening under the catch-all): every stretch the AI
        # stood still names what it watched (`hands/dialogue.py` busy_reason)
        idle = [r for r in run.records if r.get("decision") == "watch"]
        generic = [(r["frame"], r["action"], r["reason"]) for r in idle if str(r.get("reason", "")).startswith(GENERIC_BUSY)]
        run.check(bool(idle) and not generic,
                  f"{len(idle)} stretches standing still, NONE under the catch-all {GENERIC_BUSY!r}: {generic[:4] or 'none'}; "
                  f"the reasons: {sorted({re.sub(r'[0-9]+', '#', str(r['reason']))[:60] for r in idle})[:14]}")
    holds = [((p.get("extra") or {}).get("hold"), (p.get("extra") or {}).get("gap")) for p in presses if p["action"].startswith("press ")]
    turns = [h for h, g in holds if h is not None and h < 3]
    paced = [(h, g) for h, g in holds if h is not None and h >= 3]
    run.check(all(3 <= h <= 7 and 8 <= g <= 18 for h, g in paced) and len(paced) >= len(holds) - len(turns),
              f"human pace: {len(paced)} presses held 3-7 frames (seen {sorted({h for h, _ in paced})}) with gaps 8-18 "
              f"(seen {min((g for _, g in paced), default=None)}-{max((g for _, g in paced), default=None)}); {len(turns)} short taps "
              f"(a turn in place, or a single minute on the clock)")
    reads = [r for r in run.records if r.get("decision") == "idle" and str(r.get("reason", "")).startswith("reading ")]
    lengths = [int(r["action"].split()[1].rstrip("f")) for r in reads]
    run.check(allow_faults or (bool(reads) and all(18 <= n <= 150 for n in lengths)),
              f"{len(reads)} reading delays, {min(lengths, default=None)}-{max(lengths, default=None)} frames (bound 18-150), each "
              f"logged with the page it read")
    gates: dict[str, int] = {}
    for press in presses:
        key = f"{press['action'].split()[1]}: {re.sub(r'[0-9]+', '#', (press['reason'] or '').split(':')[0])[:48]}"
        gates[key] = gates.get(key, 0) + 1
    run.notes.append(f"presses by button and gate: {json.dumps(dict(sorted(gates.items())), ensure_ascii=False)}")
    return gates


def classify_a(press: dict) -> tuple[str, bool]:
    """STEP 2.1: what an A press's GATE claims (`probe_presses.gate_kind`), and whether the look of its record
    (the digest) agrees: a WAIT says `waits=A/B(<that gate>)` and shows no menu; a MENU confirm shows that menu
    taking input (`ui=<kind>[`, not `(busy)`) and nothing waiting; a TALK shows the overworld, nothing waiting, no
    menu. Anything else is ("other", False)."""
    gate = press.get("reason") or ""
    digest = press.get("digest") or ""
    kind, menu = gate_kind(gate)
    parts = digest.split()
    screen = parts[1] if len(parts) > 1 else ""
    if kind == "wait":
        return kind, f"waits=A/B({gate})" in digest and " ui=" not in digest
    if kind == "menu":
        return kind, re.search(rf" ui={re.escape(menu or '')}\[", digest) is not None and "waits=A/B" not in digest
    if kind == "talk":
        return kind, screen == "overworld" and "waits=A/B" not in digest and " ui=" not in digest
    return kind, False


def intent(seed: int) -> tuple[str, str, str]:
    choices = random.Random(f"{seed}:choices")
    personality = pick_personality(choices, seed)
    gender, _ = choose_gender(choices, personality)
    return personality.name, gender, choose_name(choices, gender)


def check_intent_logged(run: Run) -> tuple[str, str]:
    personality, gender, name = intent(SEED)
    line = hands_line(run, "[AI-HANDS] intro: personality")
    run.check(f"personality {personality} " in line and f"gender {gender} " in line and f"name {name!r}" in line,
              f"the AI's logged intent for seed {SEED} is the personality's draw, recomputed here from ai_player/personality.py "
              f"({personality}, {gender}, {name!r}): {line or 'MISSING'}")
    return gender, name


# ---------------------------------------------------------------------- graders
def grade_INTRO(run: Run) -> None:
    gender, name = check_intent_logged(run)
    check_purity(run, f"in the truck; intended {name} ({gender})")
    check_after_is_this_run(run)
    after = run.after or {}
    run.check(after.get("name") == name and after.get("gender") == (1 if gender == "GIRL" else 0) and after.get("map") == INTRO_MAP,
              f"TRUTH (save block 2 by the probe's charmap, save block 1's map): name {after.get('name')!r} gender "
              f"{after.get('gender')} ({after.get('gender_name')}) map {after.get('map')} == the intent {name!r} {gender} and the "
              f"truck {INTRO_MAP}")
    check_gates(run)
    question = next((r for r in run.records if r.get("decision") == "read" and str(r.get("reason", "")).startswith("So it")), None)
    run.check(question is not None and name in question["reason"] and (question.get("extra") or {}).get("names_the_typed_name") is True,
              f"the AI read the name question before answering it: {question and question['reason']!r}")
    choices = [p for p in run.presses if p["action"].startswith("press A ") and " cursor on " in (p["reason"] or "")]
    run.check(any(p["reason"].startswith(f"gender cursor on {1 if gender == 'GIRL' else 0} ({gender})") for p in choices)
              and any(p["reason"].startswith("main_menu cursor on 0 (NEW GAME)") for p in choices)
              and any(p["reason"].startswith("yes_no cursor on 0 (YES)") for p in choices),
              f"the choices were made on the cursor READ: {[p['reason'] for p in choices]}")


def grade_XU(run: Run) -> None:
    gender, name = check_intent_logged(run)
    check_purity(run, None)
    check_after_is_this_run(run)
    after = run.after or {}
    # NON-VACUITY: the naive A picks the gender menu's DEFAULT (BOY); a seed that intends BOY cannot show that harm
    run.check(gender == "GIRL", f"non-vacuous: the seed intends {gender}, not the gender menu's default (BOY), so taking the "
                                f"default is a visible harm")
    run.check(after.get("name") != name and after.get("gender") != (1 if gender == "GIRL" else 0),
              f"HARM, by the second path: name {after.get('name')!r} (intended {name!r}), gender {after.get('gender')} "
              f"({after.get('gender_name')}; intended {gender}): the naive A took the gender menu's default and typed the key under "
              f"the cursor")
    run.check(after.get("name") == "AAAAAAA" and after.get("gender") == 0,
              f"exactly the predicted defaults: name {after.get('name')!r} == 'AAAAAAA' (the top-left key until full), gender BOY")
    check_gates(run, allow_faults=True)
    a = [p for p in run.presses if p["action"].startswith("press A ")]
    run.check(bool(a) and all(p["reason"] == UNGATED_GATE for p in a), f"every A of the fault run was ungated: {len(a)} A presses, "
              f"gates {sorted({p['reason'] for p in a})}")


def grade_XBN(run: Run) -> None:
    gender, name = check_intent_logged(run)
    check_purity(run, None)
    check_after_is_this_run(run)
    after = run.after or {}
    run.check(after.get("name") != name, f"HARM, by the second path: the name in save block 2 is {after.get('name')!r}, not {name!r}")
    run.check(not run.outcome.startswith("intro: in the truck") and after.get("map") != INTRO_MAP,
              f"the truck was never reached: outcome {run.outcome!r}, map {after.get('map')}")
    check_gates(run, allow_faults=True)
    questions = [r["reason"] for r in run.records if r.get("decision") == "read" and str(r.get("reason", "")).startswith("So it")]
    run.check(bool(questions) and all(name not in q for q in questions),
              f"the names the game asked about (read by the AI, which then answered NO): {questions[:4]}")
    blind = [p for p in run.presses if p["reason"] == BLIND_GATE and p["action"].split()[1] in ("Right", "Down", "Select")]
    run.check(bool(blind), f"{len(blind)} keyboard moves by count (gate {BLIND_GATE!r})")


def grade_NURSE(run: Run) -> None:
    check_purity(run, "healed")
    check_after_is_this_run(run)
    before, after = run.before or {}, run.after or {}
    hurt = [p for p in before.get("party") or [] if p[1] != p[2]]
    run.check(bool(hurt), f"NON-VACUITY: before the run the party was NOT whole (the framework's get_party on the fixture): {hurt}")
    party = after.get("party") or []
    run.check(bool(party) and all(p[1] == p[2] for p in party) and len(party) == len(before.get("party") or []),
              f"TRUTH after (get_party on the state the run left): {party}: every Pokemon at full HP")
    check_gates(run)
    a = [p for p in run.presses if p["action"].startswith("press A ")]
    kinds = sorted({("wait" if WAIT_GATE.match(p["reason"]) else p["reason"].split(":")[0].split(" cursor")[0]) for p in a})
    run.check(set(kinds) <= {"wait", "talk", "yes_no"}, f"every A was a text wait, the talk or the yes/no: {kinds}")
    run.check(any(p["reason"].startswith("yes_no cursor on 0 (YES)") for p in a), "the nurse's yes/no answered YES on the cursor read")


def grade_MART(run: Run) -> None:
    check_purity(run, "bought")
    check_after_is_this_run(run)
    before, after = run.before or {}, run.after or {}
    ball = (after.get("rom_poke_ball") or {}).get("name", "POKé BALL")
    price = (after.get("rom_poke_ball") or {}).get("price")
    b0, b1 = (before.get("balls") or {}).get(ball), (after.get("balls") or {}).get(ball)
    m0, m1 = before.get("money"), after.get("money")
    run.check(isinstance(b0, int) and isinstance(b1, int) and b1 - b0 == 5,
              f"TRUTH (the probe's own bag decode): {ball} {b0} -> {b1}: +{None if b0 is None or b1 is None else b1 - b0} (want +5)")
    run.check(isinstance(m0, int) and isinstance(m1, int) and price and m0 - m1 == 5 * price,
              f"TRUTH: money {m0} -> {m1}: -{None if m0 is None or m1 is None else m0 - m1} (want 5 x the ROM's price {price})")
    check_gates(run)
    quantities = [p["reason"] for p in run.presses if p["reason"].startswith("mart_quantity reads")]
    run.check(any(q.startswith("mart_quantity reads x5, the number wanted") for q in quantities),
              f"the quantity was READ up to x5 before A: {quantities}")


def grade_CLOCK(run: Run) -> None:
    check_purity(run, None)
    check_after_is_this_run(run)
    line = hands_line(run, "[AI-HANDS] set the wall clock: the clock at")
    match = re.search(r"the time to set: (\d+):(\d+) \(the computer's local time\)", line)
    run.check(bool(match), f"the AI logged the time it would set, from the computer's clock: {line or 'MISSING'}")
    if not match:
        return
    hours, minutes = int(match.group(1)), int(match.group(2))
    window = [time.localtime(run.started), time.localtime(run.started + run.elapsed)]
    in_window = any((t.tm_hour, t.tm_min) == (hours, minutes) for t in window) or \
        (window[0].tm_hour * 60 + window[0].tm_min) <= hours * 60 + minutes <= (window[1].tm_hour * 60 + window[1].tm_min)
    run.check(in_window, f"that time {hours}:{minutes:02d} is the computer's local time during the run "
                         f"({window[0].tm_hour}:{window[0].tm_min:02d} to {window[1].tm_hour}:{window[1].tm_min:02d})")
    run.check(run.outcome == f"clock: clock set to {hours}:{minutes:02d}", f"the brain's outcome: {run.outcome!r}")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("FLAG_SET_WALL_CLOCK") is False and before.get("VAR_LITTLEROOT_INTRO_STATE") == 5,
              f"NON-VACUITY (the fixture): FLAG_SET_WALL_CLOCK={before.get('FLAG_SET_WALL_CLOCK')} "
              f"VAR_LITTLEROOT_INTRO_STATE={before.get('VAR_LITTLEROOT_INTRO_STATE')} (want False, 5)")
    local = after.get("gLocalTime") or [None, None, None, None]
    delta = None if local[1] is None else (local[1] * 60 + local[2] - (hours * 60 + minutes)) % 1440
    run.check(after.get("FLAG_SET_WALL_CLOCK") is True and after.get("VAR_LITTLEROOT_INTRO_STATE") == 6 and delta in (0, 1),
              f"TRUTH after: FLAG_SET_WALL_CLOCK={after.get('FLAG_SET_WALL_CLOCK')} VAR_LITTLEROOT_INTRO_STATE="
              f"{after.get('VAR_LITTLEROOT_INTRO_STATE')} gLocalTime {local} (days, h, m, s) vs {hours}:{minutes:02d}: +{delta} min")
    check_gates(run)
    yes = [p["reason"] for p in run.presses if p["reason"].startswith("yes_no cursor")]
    run.check(any(r.startswith("yes_no cursor on 1 (NO), wanted 0 (YES)") for r in yes) and any(r.startswith("yes_no cursor on 0 (YES)") for r in yes),
              f"the yes/no opened on NO and the cursor was READ and moved to YES: {yes}")


def grade_XBC(run: Run) -> None:
    check_purity(run, None)
    check_after_is_this_run(run)
    after = run.after or {}
    run.check(after.get("FLAG_SET_WALL_CLOCK") is False and after.get("VAR_LITTLEROOT_INTRO_STATE") == 5,
              f"HARM, by the second path: FLAG_SET_WALL_CLOCK={after.get('FLAG_SET_WALL_CLOCK')} VAR_LITTLEROOT_INTRO_STATE="
              f"{after.get('VAR_LITTLEROOT_INTRO_STATE')}: the clock was never confirmed (the CLOCK arm: True, 6)")
    run.check(not run.outcome.startswith("clock: clock set"), f"the brain did not claim it: {run.outcome!r}")
    told = hands_line(run, "[AI-HANDS] set the wall clock: the clock at")
    run.check(f"the time to set: {PINNED_CLOCK} (named by the run)" in told,
              f"STEP 2.1: the time is PINNED ({ENV_CLOCK}={PINNED_CLOCK}), so the arm reproduces: {told or 'MISSING'}")
    check_gates(run, allow_faults=True)
    blind_a = [p for p in run.presses if p["reason"] == BLIND_GATE and p["action"].startswith("press A ")]
    asked = [r for r in run.records if "ui=yes_no[NO]" in (r.get("digest") or "") and r.get("action", "").startswith("press A ")]
    run.check(len(asked) >= 2, f"A was pressed on 'Is this the correct time?' with the cursor on NO {len(asked)} times (the clock asked "
                               f"again each time): {[r['frame'] for r in asked][:6]}; blind A presses {len(blind_a)}")


# ---------------------------------------------------------------------- step 2.1: graders of the probe and the rate
def press_verdict(p: dict) -> tuple[bool, str]:
    """The GAME'S verdict on one A press (`probe_presses.py`), by the kind its gate claims. A WAIT: no text printing,
    nothing moved in the idle frames, A moved it, and B (instead) did the same (a continue, not a choice). A MENU:
    no text printing, the menu sat still waiting for input, A did something. A TALK: the player was free (no script,
    controls unlocked, no printer) and A started a script."""
    base = (f"f{p['frame']} {p['kind']} {p['gate'][:56]!r}: printing={p['printing']} still={p['still']}"
            f"{'' if p['still'] else ' (moved by itself at +%s: %s)' % (p['moved_by_itself_at'], p['moved_by_itself'])} "
            f"A moved it at +{p['moved_by_a_at']} {p['moved_by_a']} B-same={p['b_same']} free={p['free']} started={p['started']}")
    if not p.get("restored"):
        return False, base + " (the fork did NOT restore the frame)"
    if p["kind"] == "wait":
        return (not p["printing"] and p["still"] and p["moved_by_a_at"] is not None and p["b_same"]), base
    if p["kind"] == "menu":
        return (not p["printing"] and p["still"] and p["moved_by_a_at"] is not None), base
    if p["kind"] == "talk":
        return (p["free"] and p["started"] and p["moved_by_a_at"] is not None), base
    return False, base + " (a gate of no known kind)"


def check_probe_ran(run: Run) -> list[dict]:
    data = run.probe or {}
    presses = data.get("a_presses") or []
    run.check(bool(data) and bool(presses) and all(p.get("restored") for p in presses),
              f"the probe ran and tested {len(presses)} A presses, each in forks of its own frame, the frame restored after "
              f"each ({sum(1 for p in presses if p.get('restored'))} of {len(presses)}); IDLE/PRESS_WATCH/PRINT_WINDOW = "
              f"{data.get('constants')}")
    return presses


def check_forks_changed_nothing(run: Run) -> None:
    """The forks are reloaded before the real press: the forked run must be the unforked run (CLAUDE.md rule 8: one
    trajectory twice is a DETERMINISM check, which is exactly what this is)."""
    probe, harness = run.probe or {}, run.harness or {}
    keys = ("reason", "frames", "presses")
    run.check(bool(probe) and bool(harness) and all(probe.get(k) == harness.get(k) for k in keys),
              f"the forks changed nothing in the run: probe {[probe.get(k) for k in keys]} == unforked harness "
              f"{[harness.get(k) for k in keys]}")


def grade_probe(run: Run, outcome: str, need: dict[str, int], truth_check) -> None:
    """A real skill under the probe (WBI, WBN, WBM, WBC): every A press, by the game's behaviour."""
    presses = check_probe_ran(run)
    if not presses:
        return
    check_forks_changed_nothing(run)
    data = run.probe or {}
    run.check(data.get("reason") == outcome, f"the skill's outcome: {data.get('reason')!r} (want {outcome!r})")
    by_kind: dict[str, list] = {}
    for p in presses:
        by_kind.setdefault(p["kind"], []).append(p)
    bad = [press_verdict(p)[1] for p in presses if not press_verdict(p)[0]]
    run.check(not bad and "other" not in by_kind,
              f"EVERY A press, by the GAME'S behaviour: {', '.join(f'{len(v)} {k}' for k, v in sorted(by_kind.items()))}; each "
              f"WAIT: no text printing, {IDLE_TEXT}, A moved it, B did the same; each MENU: no text printing, the menu sat "
              f"still for input, A did something; each TALK: the player free, A started a script. Wrong: {bad[:4] or 'none'}")
    printing = [p["frame"] for p in presses if p["printing"]]
    run.check(not printing, f"no A press landed while a text was PRINTING (an active printer advancing in the next "
                            f"{(data.get('constants') or {}).get('PRINT_WINDOW')} frames, no input): {printing or 'none'}")
    gates = [p["gate"] for p in presses]
    for gate, minimum in need.items():
        hits = [p for p in presses if p["gate"] == gate or (gate.endswith("*") and p["gate"].startswith(gate[:-1]))]
        good = [p for p in hits if press_verdict(p)[0]]
        run.check(len(good) >= minimum and len(good) == len(hits),
                  f"NON-VACUITY (pre-registered >= {minimum}): {len(hits)} A presses gated {gate!r}, {len(good)} of them "
                  f"proven by the game: {[press_verdict(p)[1] for p in hits][:2]}")
    run.notes.append("every A press, the probe's verdict:\n    " + "\n    ".join(
        f"{'OK ' if press_verdict(p)[0] else 'BAD'} {press_verdict(p)[1]}" for p in presses))
    truth_check(run, data.get("truth") or {})
    run.notes.append(f"gates seen: {sorted(set(gates))}")


IDLE_TEXT = "nothing moved in 300 frames with no input"


def truth_intro(run: Run, truth: dict) -> None:
    _, gender, name = intent(SEED)
    run.check(truth.get("name") == name and truth.get("gender") == (1 if gender == "GIRL" else 0) and truth.get("map") == INTRO_MAP,
              f"TRUTH at the end (save block 2, the map): {truth.get('name')!r} {truth.get('gender')} {truth.get('map')} == "
              f"{name!r} {gender} {INTRO_MAP}")


def truth_nurse(run: Run, truth: dict) -> None:
    party = truth.get("party") or []
    run.check(bool(party) and all(p[1] == p[2] for p in party), f"TRUTH at the end (get_party): {party}: every Pokemon at full HP")


def truth_mart(run: Run, truth: dict) -> None:
    ball = (truth.get("rom_poke_ball") or {}).get("name", "POKé BALL")
    run.check((truth.get("balls") or {}).get(ball) == 10 and truth.get("money") == 5680,
              f"TRUTH at the end (the probe's bag and money decode): {ball} {(truth.get('balls') or {}).get(ball)} (want 10, from 5), "
              f"money {truth.get('money')} (want 5680, from 6680)")


def truth_clock(run: Run, truth: dict) -> None:
    hours, minutes = (int(x) for x in PINNED_CLOCK.split(":"))
    local = truth.get("gLocalTime") or [None, None, None, None]
    run.check(truth.get("FLAG_SET_WALL_CLOCK") is True and truth.get("VAR_LITTLEROOT_INTRO_STATE") == 6
              and local[1:3] in ([hours, minutes], list(divmod(hours * 60 + minutes + 1, 60))),
              f"TRUTH at the end: FLAG_SET_WALL_CLOCK={truth.get('FLAG_SET_WALL_CLOCK')} VAR_LITTLEROOT_INTRO_STATE="
              f"{truth.get('VAR_LITTLEROOT_INTRO_STATE')} gLocalTime {local} (want {PINNED_CLOCK})")


def grade_WBI(run: Run) -> None:
    _, gender, name = intent(SEED)
    grade_probe(run, f"intro: in the truck; intended {name} ({gender})",
                {"task Task_NewGameBirchSpeech_WaitPressBeforeNameChoice (A or B)": 1, "text printer 0 *": 15}, truth_intro)


def grade_WBN(run: Run) -> None:
    grade_probe(run, "nurse: healed", {"script waitbuttonpress": 1, "text printer 0 *": 2, "talk: facing *": 1}, truth_nurse)


def grade_WBM(run: Run) -> None:
    grade_probe(run, "mart: bought", {"task Task_ReturnToItemListAfterItemPurchase (A or B)": 1, "script waitbuttonpress": 1,
                                      "talk: facing *": 1}, truth_mart)


def grade_WBC(run: Run) -> None:
    grade_probe(run, f"clock: clock set to {PINNED_CLOCK}", {"script waitbuttonpress": 1, "text printer 0 *": 4,
                                                             "talk: facing *": 1, "clock reads *": 1}, truth_clock)


def grade_WBX(run: Run) -> None:
    """CONTROL: the probe CAN say "the game was not waiting": the naive driver's A presses, on its cadence."""
    presses = check_probe_ran(run)
    if not presses:
        return
    check_forks_changed_nothing(run)
    printing = [p for p in presses if p["printing"]]
    moving = [p for p in presses if not p["still"]]
    still = [p for p in presses if p["still"]]
    run.check(all(p["gate"] == UNGATED_GATE for p in presses), f"every A of the control was ungated: {len(presses)} presses")
    run.check(len(printing) >= 1 and len(moving) >= 1,
              f"the probe says NOT WAITING where the game was not: {len(printing)} of {len(presses)} ungated A presses landed on a "
              f"text still PRINTING, {len(moving)} on a screen that moved by itself within 300 frames, {len(still)} on a still "
              f"screen (pre-registered: >= 1 printing and >= 1 moving; the dev run: 118, 208 (the 118 included), 35 of 243). "
              f"Examples: "
              f"{[press_verdict(p)[1] for p in (printing[:1] + [m for m in moving if not m['printing']][:1])]}")
    truth = (run.probe or {}).get("truth") or {}
    run.check(truth.get("name") == "AAAAAAA" and truth.get("gender") == 0,
              f"the same harm as arm XU, read at the end: {truth.get('name')!r} gender {truth.get('gender')}")


def grade_XTW(run: Run) -> None:
    """FAULT: TASK_WAITS lists a timer task in a COPY of the eyes; the AI presses A on it; the probe must flag it."""
    presses = check_probe_ran(run)
    data = run.probe or {}
    code = data.get("eyes_code") or {}
    ran_copy = "ai_player_step21_" in str(code.get("screens")) and "Task_NewGameBirchSpeech_WaitToShowBirch" in (code.get("task_waits") or [])
    run.check(ran_copy, f"the COPY's eyes ran, its TASK_WAITS holding the timer task: {code.get('screens')}")
    fake = [p for p in presses if p["gate"] == "task Task_NewGameBirchSpeech_WaitToShowBirch (A or B)"]
    flagged = [p for p in fake if not press_verdict(p)[0]]
    run.check(bool(fake) and len(flagged) == len(fake),
              f"CAUGHT: {len(fake)} A presses gated on the fake wait, {len(flagged)} flagged by the game's behaviour (the timer "
              f"moved on by itself; the press did not move it): {[press_verdict(p)[1] for p in flagged][:3]}")
    real = [p for p in presses if p["kind"] == "wait" and p not in fake]
    run.check(bool(real) and all(press_verdict(p)[0] for p in real),
              f"CONTROL inside the arm: the {len(real)} other wait-gated presses of the same run are all proven by the game")


def grade_RATE(run: Run) -> None:
    """A RATE (CLAUDE.md rule 9: a frequency question): each skill once per seed, graded by its own truth."""
    per: dict[str, list] = {}
    for entry in run.sweep:
        data = entry["data"] or {}
        truth = data.get("truth") or {}
        seed, brain = entry["seed"], entry["brain"]
        if brain == "intro":
            _, gender, name = intent(seed)
            ok = (data.get("reason") == f"intro: in the truck; intended {name} ({gender})" and truth.get("name") == name
                  and truth.get("gender") == (1 if gender == "GIRL" else 0) and truth.get("map") == INTRO_MAP)
            what = f"{truth.get('name')!r} {truth.get('gender')} {truth.get('map')}"
        elif brain == "nurse":
            party = truth.get("party") or []
            ok = data.get("reason") == "nurse: healed" and bool(party) and all(p[1] == p[2] for p in party)
            what = f"{party[:1]}"
        elif brain == "mart":
            start = data.get("start_truth") or {}
            ball = (truth.get("rom_poke_ball") or {}).get("name", "POKé BALL")
            price = (truth.get("rom_poke_ball") or {}).get("price") or 0
            gained = (truth.get("balls") or {}).get(ball, 0) - (start.get("balls") or {}).get(ball, 0)
            spent = (start.get("money") or 0) - (truth.get("money") or 0)
            ok = data.get("reason") == "mart: bought" and gained == 5 and spent == 5 * price
            what = f"+{gained} balls, -{spent} money"
        else:
            hours, minutes = (int(x) for x in entry["args"][1].split(":"))
            local = truth.get("gLocalTime") or [None, None, None, None]
            later = divmod((hours * 60 + minutes + 1) % 1440, 60)
            ok = (data.get("reason") == f"clock: clock set to {hours}:{minutes:02d}" and truth.get("FLAG_SET_WALL_CLOCK") is True
                  and truth.get("VAR_LITTLEROOT_INTRO_STATE") == 6 and local[1:3] in ([hours, minutes], list(later)))
            what = f"set {hours}:{minutes:02d}, gLocalTime {local[1:3]}"
        per.setdefault(brain, []).append((seed, ok, f"seed {seed}: {data.get('reason')!r} frames {data.get('frames')} {what}"))
    for brain in ("intro", "nurse", "mart", "clock"):
        rows = per.get(brain, [])
        failed = [r[2] for r in rows if not r[1]]
        frames = [((e["data"] or {}).get("frames") or 0) for e in run.sweep if e["brain"] == brain]
        run.check(len(rows) == len(RATE_SEEDS) and not failed,
                  f"{brain}: {sum(1 for r in rows if r[1])} of {len(rows)} seeds succeeded by the second-path truth (want all "
                  f"{len(RATE_SEEDS)}; with 0 failures in {len(RATE_SEEDS)} the failure rate is below ~{300 // len(RATE_SEEDS)}% at 95% "
                  f"confidence, the rule of three); frames {min(frames, default=0)}-{max(frames, default=0)}; failed: {failed[:3] or 'none'}")
        run.notes.append(f"{brain}:\n    " + "\n    ".join(r[2] for r in rows))


GRADERS = {"INTRO": grade_INTRO, "XU": grade_XU, "XBN": grade_XBN, "NURSE": grade_NURSE, "MART": grade_MART,
           "CLOCK": grade_CLOCK, "XBC": grade_XBC, "WBI": grade_WBI, "WBN": grade_WBN, "WBM": grade_WBM, "WBC": grade_WBC,
           "WBX": grade_WBX, "XTW": grade_XTW, "RATE": grade_RATE}


# ---------------------------------------------------------------------- evidence
def provenance() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO), capture_output=True, text=True, timeout=30).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", "ai_player"], cwd=str(REPO),
                               capture_output=True, text=True, timeout=30).stdout.strip()
        return f"HEAD {head}; " + ("ai_player/ has UNCOMMITTED changes (the code under test is the working tree)" if dirty else "ai_player/ clean at HEAD")
    except Exception as error:  # noqa: BLE001
        return f"unknown ({error})"


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def write_evidence(run: Run, code_ref: str, tag: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{tag}-{run.arm.name}.txt"
    fixture = run.arm.fixture
    env = " ".join(f"{k}={v}" for k, v in {ENV_BRAIN: run.arm.brain, ENV_SEED: str(SEED), **run.arm.env}.items())
    if run.arm.kind != "launcher":
        env = f"none (a test-side script in its own throwaway emulator; its arguments are in the command; seed {SEED})"
    if run.arm.kind == "rate":
        start = (f"each skill from its own start, seeds {RATE_SEEDS[0]}-{RATE_SEEDS[-1]}: intro --fresh; nurse "
                 f"{FIXTURES['post_league_lobby.ss1'][0].name}; mart {FIXTURES['mart_rustboro.ss1'][0].name} (5 balls); clock "
                 f"{FIXTURES['clock_room.ss1'][0].name} (the time per seed: rate_clock)")
    elif fixture:
        start = f"fixture: {FIXTURES[fixture][0].relative_to(REPO).as_posix()} md5={md5_of(FIXTURES[fixture][0])}"
    else:
        start = "start: --fresh (no state, no cartridge save: the title screen and a New Game)"
    out = [
        f"AI PLAYER BUILD STEP 2 (THE HANDS) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"code: {code_ref}",
        start,
        f"fixture documentation: {run.arm.doc or '-'}",
        f"command: {' '.join(run.command)}",
        f"env: {env}",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        SELFTEST_LINE,
        "checks (pre-registered in ai_player/gates/live_step2.py's docstring; each quotes both values):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
    ]
    if run.notes:
        out += ["", "---- notes ----", *run.notes]
    if run.verdict is not None:
        out += ["", "---- the instrument's verdict file (purity.json) ----", json.dumps(run.verdict, indent=2, sort_keys=True)]
    if run.before is not None:
        out += ["", "---- TRUTH of the fixture BEFORE the run (gates/hands_harness.py truth) ----", json.dumps(run.before, sort_keys=True, ensure_ascii=False)]
    if run.after is not None:
        out += ["", "---- TRUTH of the state the run LEFT (gates/hands_harness.py truth) ----", json.dumps(run.after, sort_keys=True, ensure_ascii=False)]
    if run.records:
        out += ["", f"---- the action log: {len(run.records)} records (frame | decision | action | gate or reason | digest) ----"]
        for r in run.records:
            if r.get("decision") in ("start", "end"):
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {r.get('reason')} | {r.get('digest')}")
            else:
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {r.get('reason')} | {r.get('digest')}")
    if run.stdout:
        keep = [line for line in run.stdout.splitlines() if line.startswith(("[AI-", "[DRIVER]"))]
        out += ["", "---- evidence lines from stdout ([AI-*]) ----", *keep]
    if run.probe is not None:
        probe = {k: v for k, v in run.probe.items() if k not in ("a_presses", "lines", "truth")}
        out += ["", "---- STEP 2.1: the probe (gates/probe_presses.py) ----", json.dumps(probe, ensure_ascii=False, sort_keys=True),
                "the brain's lines:", *[f"  {line}" for line in run.probe.get("lines") or []],
                "TRUTH at the end (gates/hands_harness.py truth, in the probe's emulator):",
                json.dumps(run.probe.get("truth"), ensure_ascii=False, sort_keys=True),
                "every A press, raw (frame, gate, kind, printing, still, moved_by_itself_at, moved_by_a_at, b_same, free, started, "
                "the probe's task list):"]
        for p in run.probe.get("a_presses") or []:
            out.append(f"  f{p['frame']} | {p['gate']} | {p['kind']} {p.get('menu') or ''} | printing={p['printing']} still={p['still']} "
                       f"by-itself={p['moved_by_itself_at']} {p['moved_by_itself']} | A={p['moved_by_a_at']} {p['moved_by_a']} | "
                       f"B-same={p['b_same']} {p.get('b_differs_at', '')} | free={p['free']} started={p['started']} | tasks {p['tasks']}")
    if run.harness is not None:
        harness = {k: run.harness.get(k) for k in ("brain", "seed", "fault", "reason", "frames", "presses", "seconds")}
        out += ["", "---- STEP 2.1: the unforked run of the same start (gates/hands_harness.py) ----", json.dumps(harness, ensure_ascii=False)]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def leftover_processes() -> list[str]:
    try:
        import psutil
    except ImportError:
        return []
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except Exception:  # noqa: BLE001
            continue
        if ("pokebot.py" in cmd and PROFILE in cmd) or "hands_harness.py" in cmd or "probe_presses.py" in cmd:
            found.append(f"pid {proc.info['pid']}: {cmd[:160]}")
    return found


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build step 2 (the hands).")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="the run's seed (default 3, the pinned one); another seed is a REPLICATION (docstring)")
    parser.add_argument("--evidence-tag", default=None, help=f"default {EVIDENCE_TAG}, or {EVIDENCE_TAG}-seedN for another seed")
    args = parser.parse_args()
    global SEED
    SEED = args.seed
    if args.evidence_tag is None:
        args.evidence_tag = EVIDENCE_TAG if SEED == DEFAULT_SEED else f"{EVIDENCE_TAG}-seed{SEED}"
    print(f"seed {SEED}; evidence tag {args.evidence_tag}")
    broken = selftest_after_check()
    global SELFTEST_LINE
    SELFTEST_LINE = (f"[SELFTEST] check_after_is_this_run on 7 synthetic runs (2 its own: pass; 5 someone else's: stale "
                     f"mtime, frame +3000, frame -3000, no file, the fixture's md5: fail): {'PASS' if not broken else 'FAIL ' + str(broken)}")
    print(SELFTEST_LINE)
    if broken:
        return 2
    wanted = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in wanted if name not in GRADERS]
    if unknown:
        print(f"unknown arms: {unknown}")
        return 2
    for name, (path, md5) in FIXTURES.items():
        actual = md5_of(path) if path.is_file() else "MISSING"
        if actual != md5:
            print(f"ABORT: fixture {name} has md5 {actual}, pinned {md5}: different bytes, results would not compare")
            return 2
    build_root = launcher.resolve_build_root()
    code_ref = provenance()
    results: list[Run] = []
    for arm in [a for a in ARMS if a.name in wanted]:
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        run = {"probe": run_probe_arm, "rate": run_rate_arm}[arm.kind](arm) if arm.kind != "launcher" else run_arm(arm, build_root)
        GRADERS[arm.name](run)
        evidence = write_evidence(run, code_ref, args.evidence_tag)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text}")
    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<5} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
