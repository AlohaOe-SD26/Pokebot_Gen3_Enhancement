"""LIVE PROOF of AI-player build step 4: the AI's OWN BATTLES (HUMAN-PLAY-DESIGN pillar 3). Test side.

    py -3.12 ai_player/gates/live_step4.py [--arms WILD,CATCH,...] [--evidence-tag step4]
    exit 0 = every arm PASS and no leftover emulator process

Every launcher arm runs the REAL package through the real launcher (`py -3.12 -m ai_player run`: the purity gate first,
the instrument, the verdict file), brain `battle` (`mode.py` HandsBrain._battles: the decider `brain/battle.py`, the skill
`skills/battle.py`), and is graded three ways, every check quoting both values:
  PURITY  CLEAN, every breach counter 0, `ai_presses` == 2 x the pad's presses, the pad's frames == `real_frames`,
          `ai_bot_calls` 0 (the bot's battle code never ran), the run ended by itself;
  HANDS   every press has its gate; every A is a WAIT, a MENU confirm (that menu, taking input, on its look) or a TALK;
          no stretch standing still under the catch-all reason;
  THE GAME by a SECOND PATH from the state the run left (`hands_harness.py truth`: the framework's party decoder by PID
          with each Pokemon's experience, level, moves and OT id; the PC boxes' PIDs and OT ids; `gBattleOutcome`; the
          trainers' DEFEATED flags and the story flags in save block 1; the game's own battle counters), never the AI's
          eyes; the state asserted to be THIS run's.

THE ARMS (fixtures: `gates/make_step4_fixtures.py`, every one made by button presses; md5s pinned in `FIXTURES`)
  WILD       `route101_south.ss1` (Route 101, Mudkip L8 19/28, 5 Poke Balls, only Mudkip owned), Story, 4 battles: it roams the
             grass and fights what comes (a species it has not caught may be caught: Story wants one 60 % of the time, a
             seeded draw); CLAIM: at least one wild battle WON by fighting, and the Mudkip's experience (by PID) rose.
  CATCH      the same start, Catcher (it wants every species it has not caught), 1 battle; CLAIM: the battle ends CAUGHT
             (`gBattleOutcome` 7), a NEW PID is in the party or a box with the PLAYER's visible OT id, the balls in the bag
             fell by exactly the balls the AI threw, and a weakening move came first while the foe's bar was above half.
  TRAINER    `trainer_battle_r116.ss1` (YOUNGSTER JOEY's battle just begun: Grovyle L16 against his Machop), Story;
             CLAIM: won, Joey's DEFEATED flag (322) clear -> set, Grovyle's experience rose.
  RIVAL      `rival_r103.ss1` (MAY's battle on Route 103 just begun, after the AI's OWN walk up to her and talk: Mudkip L6
             13/23 against her Treecko), Story, seed 5; CLAIM: won, DEFEATED_RIVAL_ROUTE103 and May's trainer flag (529)
             clear -> set. ‼ At 13/23 HP the battle is close: 1 of 8 seeds won in development, 2 of 10 in the seed sweep
             (`rate_step4.py` RIVAL); seed 5 is a won one, CHOSEN FOR IT and SAID so: this arm proves the battle can be played
             to a win and the game agrees, not how often. A person would heal first (step 5 chains a heal).
  CHALLENGE  `route103.ss1` (Route 103 BEFORE the rival: DEFEATED_RIVAL_ROUTE103 clear), Story, `AI_PLAYER_TALK_TO` 10,3:
             the AI walks up to May by its own navigator and talks to her; CLAIM: the rival's battle BEGAN after the AI's
             talk A (the game's trainer-battle count +1), was played by the decider to its end, and the game's result and
             the rival flag agree (won <-> set). The outcome itself is the RIVAL rate's business.
  TYPE       `geodude_grovyle.ss1` (a DOUBLE battle: HIKER CLARK's Geodude and YOUNGSTER JOHNSON's Shroomish, Grovyle L17
             and Nincada out), Story; CLAIM: every move Grovyle chose while the Geodude stood is ABSORB aimed at the
             Geodude (Grass x4: worth 120 against Pursuit 40 and Quick Attack 20).
  TYPEX      FAULT of TYPE (`AI_PLAYER_FAULT_IGNORE_TYPES=1`: the decider values every matchup as neutral, no STAB):
             CLAIM: Absorb is NEVER chosen against the Geodude (Pursuit and Quick Attack are), and purity still CLEAN.
  FAINT      `faint_r116.ss1` (SCHOOL KID KAREN's battle just begun, Mudkip L14 29/42 against her Shroomish), Story,
             seed 1; CLAIM: the lead Mudkip (PID 550a9be6) FAINTS (HP 0 by the second path), the AI chooses who goes in
             by PID through the party menu and SEND OUT, and the battle goes on to its end: won, Karen's flag (280) set.
             (The step-4 verifier's round: "the README says ... best matched against the foe ... the live party menu has
             no battle view, so `replacement` ranks by level x HP share only".) CLAIM since: the choice is made AGAINST the
             foe the decider REMEMBERS ("Taillow L6 (11/21 HP) is the best left against Shroomish (the field REMEMBERED
             ...)": Flying against Grass, where step 4 sent the full-HP Nincada), and the GAME (the replay) shows that
             Taillow come onto battler 0.
  DFAINT     (the step-4 verifier's FAILURE: "in a DOUBLE battle, when the partner faints, the AI sends in the Pokemon that
             is already on the field, and the battle gets stuck") `geodude_grovyle.ss1`, seed 6 with
             `AI_PLAYER_FAULT_IGNORE_TYPES=1` (the verifier's own reproduction: the types fault only makes the partner
             Nincada fall; the replacement rule under test is the real one). CLAIM: the decider names a Pokemon that is
             NOT the Grovyle standing on the field ("not Grovyle on the field ... REMEMBERED"), the game refuses nothing,
             the battle is WON (Clark's 631 and Johnson's 754 set), and the GAME (the replay) shows Nincada's HP 0 at
             position 2, then the named Pokemon come onto position 2 while the Grovyle stands at 0.
  DFAINTX    FAULT of DFAINT: the step-4 code (`AI_PLAYER_FAULT_FORGET_FIELD=1`: the party menu's look alone;
             `AI_PLAYER_FAULT_IGNORE_REFUSAL=1`: the refusal watched): CLAIM: "who goes in: Grovyle", and the run ends
             "stuck: the battle: no Pokemon could be sent in" (the verifier's bug, through the real launcher); purity CLEAN.
  REFUSE     `ki17_partymenu_wedge.ss1` (a story-bot save stopped ON the battle party menu's "SKITTY is already in
             battle!", Mauville's gym), Story, seed 1: the backstop of the fix, from a state the AI did not make. CLAIM: the
             AI reads the words and presses A on their WAIT (gate `text printer 6 WAIT`, a busy party list), the decider is
             told Skitty was refused, Mightyena goes in (the GAME, by the replay: its PID onto the field), and the battle is
             WON (`gBattleOutcome` 1). Its fault half is `rate_step4.py` REFUSE-FAULT (5 of 5 stuck).
THE REPLAY (the step-4 verifier's round: "live_step4 makes no game read of the move or its target"): every arm that starts
IN a battle (TYPE, TYPEX, FAINT, DFAINT, DFAINTX, REFUSE) is replayed in-process from the same fixture, seed, personality
and faults (`hands_harness.py --battle-log`, the cartridge's clock pinned), reading the GAME's battle after every frame
(`BattleRecorder`: each battler's chosen move, each HP change with its user, move and target, each Pokemon that came
onto a position). It counts only if its frames and presses EQUAL the launcher's: then it is the launcher's trajectory,
replayed (one trajectory, CLAUDE.md rule 8), and its game record is the second path for the moves and the send-ins.
  LEARN      `learn_r116.ss1` (a wild battle on Route 116 begun with the Mudkip at 1,978 experience, 57 short of level
             15, where it learns BIDE), Story, seed 1; CLAIM: the Mudkip (PID) reaches level 15, BIDE is in its moves and
             GROWL is not (the decider's reason logged: Bide worth 40, Growl a status move worth 4), forgotten on the
             summary screen by reading its cursor.
The RECOIL proof is a RECORDED case (`test_battle.py` RecordedRecoilTests, on `fixtures/recoil_r102.look.json`, the AI's own
look in a real battle: Take Down never chosen at 3 HP, where its recoil would knock the Marshtomp out) with the unit tests
(a sturdy Taillow: never at 20 % HP), and the seed sweep's live A/B (`rate_step4.py` RECOIL: the same battle, the recoil
charged on what the hit can take, against the step-4 rule; the game's own recoil read).

PRE-REGISTERED (`PREDICTED`, machine-checked): each arm's claims above, and, for the arms that start IN a battle (where the
game reads no clock), its frames and presses from a development run of the same code in-process with the cartridge's clock
pinned (`hands_harness.py --game-clock`), written BEFORE the graded runs. The roaming arms (WILD, CATCH, CHALLENGE) walk the
overworld, where the game reads the HOST's clock (the step-3.1 finding): their claims are registered, not their frames.

THE STEP-4 VERIFIER'S SECOND ROUND (2026-10-09): no arm and no number changes. Two things moved under them: each told fight
line now ends with the battler position and what the type chart changed in the choice (`brain/battle.py` TypeSay: the
sweep's TYPE-DECISIONS reads it; TYPE's and TYPEX's checks read the move and the values before it, unchanged), and the
explorer that WILD, CATCH and CHALLENGE walk with carries its decisions on (`brain/explore.py` carry_on, the doormat, the
way back to a map seen all of): those three register claims, not trajectories, as before.
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
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.live_step2 import check_purity, classify_a, clean_env, truth_of  # noqa: E402
from ai_player.gates.provenance import provenance as tree_provenance  # noqa: E402
from ai_player.hands.dialogue import GENERIC_BUSY  # noqa: E402
from ai_player.host import launcher  # noqa: E402
from ai_player.gates.live_step2 import run_json  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BATTLES, ENV_BRAIN, ENV_FAULT_FORGET_FIELD, ENV_FAULT_IGNORE_REFUSAL, ENV_FAULT_IGNORE_TYPES, ENV_FAULT_UNCAPPED_RECOIL,
    ENV_PERSONALITY, ENV_SEED, ENV_TALK_TO,
)

GATES = Path(__file__).resolve().parent
SAVES = REPO / "tools" / "story-dev" / "saves"
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
EVIDENCE_TAG = "step4"
PROFILE = "ai-step4-battle"
FRAME_SLACK = 5
SELFTEST_LINE = "[SELFTEST] not run"
FIXTURES: dict[str, tuple[Path, str]] = {
    "route101_south.ss1": (GATES / "fixtures" / "route101_south.ss1", "81bf318a1532c5364f60064530f9984b"),
    "trainer_battle_r116.ss1": (GATES / "fixtures" / "trainer_battle_r116.ss1", "f55f3c2ec6efb9fb20363e8ca92b73ba"),
    "route103.ss1": (SAVES / "route103.ss1", "0d951fe21be35a6eafade207ddff5961"),
    "rival_r103.ss1": (GATES / "fixtures" / "rival_r103.ss1", "a5a1624d7cf617ed731070a7569ff986"),
    "geodude_grovyle.ss1": (GATES / "fixtures" / "geodude_grovyle.ss1", "0e22cfda06a8bcf7f53b21aacc51a94d"),
    "faint_r116.ss1": (GATES / "fixtures" / "faint_r116.ss1", "14c714d4e2a34633a577a132f85665fb"),
    "learn_r116.ss1": (GATES / "fixtures" / "learn_r116.ss1", "d9f9c6dfdcdec46b08243df38828e98b"),
    # (the step-4 verifier's round) a story-bot save stopped on the battle party menu's refusal (KI-17's wedge)
    "ki17_partymenu_wedge.ss1": (SAVES / "ki17_partymenu_wedge.ss1", "0103bfe9881ba83eb8919a06a952938f"),
}
HARNESS = GATES / "hands_harness.py"
#: The replay's cartridge clock (the in-battle arms read none; pinned so the replay is the same whenever it is played).
REPLAY_CLOCK = "2026-10-08T06:00"
#: The fault switches of an arm's env, as the harness names them.
FAULT_NAMES = {ENV_FAULT_IGNORE_TYPES: "ignore_types", ENV_FAULT_UNCAPPED_RECOIL: "uncapped_recoil",
               ENV_FAULT_FORGET_FIELD: "forget_field", ENV_FAULT_IGNORE_REFUSAL: "ignore_refusal"}
#: The arms replayed in-process for the game's own battle record (the module docstring, THE REPLAY).
REPLAYED = ("TYPE", "TYPEX", "FAINT", "DFAINT", "DFAINTX", "REFUSE")
MUDKIP = "550a9be6"  # the starter's PID in every Route 101-116 fixture (the same playthrough)
GROVYLE = "550a9be6"  # trainer_battle_r116 / geodude_grovyle: the same Pokemon, evolved in another playthrough
#: Trainers (`include/constants/opponents.h`): TRAINER_JOEY, TRAINER_KAREN_1, TRAINER_MAY_ROUTE_103_MUDKIP.
JOEY, KAREN, MAY = "322", "280", "529"
#: The PRE-REGISTERED numbers (module docstring), written from the development runs (2026-10-08, in-process, this code,
#: `hands_harness.py battle ... --game-clock 2026-10-08T06:00`) BEFORE the graded runs. The arms that start IN a battle
#: register their frames and presses (the game reads no clock in a battle); the roaming arms only their claims (checks).
PREDICTED: dict[str, dict] = {
    "TRAINER": {"outcomes": ["won"], "frames": 3811, "presses": 14},
    "RIVAL": {"outcomes": ["won"], "frames": 6103, "presses": 21},
    "TYPE": {"outcomes": ["won"], "frames": 11458, "presses": 48, "first": ["Absorb", "Geodude"]},
    "TYPEX": {"outcomes": ["won"], "frames": 9468, "presses": 49, "first": ["Quick Attack", "Shroomish"]},
    # (the step-4 verifier's round, development runs in-process with this round's code, 2026-10-08) FAINT's replacement is
    # now chosen against the remembered Shroomish: Taillow, where step 4 sent the Nincada (11113 frames, 28 presses then)
    "FAINT": {"outcomes": ["won"], "frames": 9503, "presses": 30, "sent": ["Taillow"]},
    "DFAINT": {"outcomes": ["won"], "frames": 17536, "presses": 95, "sent": ["Skitty"]},
    "DFAINTX": {"outcomes": ["the battle: no Pokemon could be sent in"], "frames": 8200, "presses": 39, "sent": ["Grovyle"]},
    "REFUSE": {"outcomes": ["won"], "frames": 10182, "presses": 52, "sent": ["Mightyena"]},
    "LEARN": {"outcomes": ["won"], "frames": 3918, "presses": 19},
    "CATCH": {"outcomes": ["caught"]},
}


@dataclass
class Arm:
    name: str
    title: str
    fixture: str
    frames: int
    wall: float
    env: dict[str, str] = field(default_factory=dict)
    seed: int = 3
    doc: str = ""


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
    checks: list[tuple[bool, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    measures: dict = field(default_factory=dict)
    predictions: list = field(default_factory=list)
    #: (the step-4 verifier's round) the in-process replay with the game's battle read each frame (THE REPLAY)
    replay: dict | None = None

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    def measure(self, name: str, value) -> None:
        self.measures[name] = value

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)

    @property
    def presses(self) -> list[dict]:
        return [r for r in self.records if str(r.get("action", "")).startswith(("press ", "hold "))]

    @property
    def outcome(self) -> str:
        return ((self.verdict or {}).get("facts") or {}).get("exit_reason") or ""


def story(battles: int = 1, **extra: str) -> dict[str, str]:
    return {ENV_PERSONALITY: "Story", ENV_BATTLES: str(battles), **extra}


ARMS: list[Arm] = [
    Arm("WILD", "roam Route 101's grass and fight what comes: a wild battle WON by fighting, experience gained",
        "route101_south.ss1", 40000, 1500.0, story(4), doc="gates/make_step3_fixtures.py (route101_south.build.json)"),
    Arm("CATCH", "a species it has not caught, weakened then caught: a NEW PID with the player's OT id, balls spent",
        "route101_south.ss1", 20000, 900.0, {ENV_PERSONALITY: "Catcher", ENV_BATTLES: "1"}, doc="as WILD"),
    Arm("TRAINER", "YOUNGSTER JOEY's battle on Route 116 fought to the end: won, his defeated flag set", "trainer_battle_r116.ss1",
        12000, 600.0, story(), doc="gates/make_trainer_fixture.py: Joey's battle just begun"),
    Arm("RIVAL", "MAY's battle on Route 103 (after the AI's own walk up to her and talk): won, the rival flag set",
        "rival_r103.ss1", 12000, 600.0, story(), seed=5,
        doc="gates/make_step4_fixtures.py --only rival (rival_r103.build.json): route103.ss1 played on by the AI's own battle "
            "brain, talk to (10,3), seed 1; saved on the battle's first frame"),
    Arm("CHALLENGE", "Route 103 before the rival: the AI walks up to May, talks, and the rival's battle is played to its end",
        "route103.ss1", 20000, 900.0, story(1, **{ENV_TALK_TO: "10,3"}), seed=1,
        doc="tools/story-dev/saves/route103.ss1: Route 103, DEFEATED_RIVAL_ROUTE103 clear, May at (10,3)"),
    Arm("TYPE", "a double battle against a hiker's GEODUDE: Grovyle's every move against it is ABSORB (Grass x4)",
        "geodude_grovyle.ss1", 30000, 1200.0, story(),
        doc="gates/make_step4_fixtures.py --only type (geodude_grovyle.build.json): trainer_battle_r116.ss1 played on by the "
            "AI's own battle brain (Story, seed 3) until a trainer's Geodude engaged it"),
    Arm("TYPEX", "FAULT of TYPE: type effectiveness ignored (AI_PLAYER_FAULT_IGNORE_TYPES=1): Absorb never chosen",
        "geodude_grovyle.ss1", 30000, 1200.0, story(**{ENV_FAULT_IGNORE_TYPES: "1"}), doc="as TYPE"),
    Arm("FAINT", "KAREN's battle on Route 116: the lead Mudkip FAINTS, the AI sends in the next by PID, and wins",
        "faint_r116.ss1", 20000, 900.0, story(), seed=1,
        doc="gates/make_step4_fixtures.py --only faint (faint_r116.build.json): route116team.ss1 played on by the AI's own "
            "battle brain (Story, seed 2) until a trainer engaged it with the Mudkip below 85 % HP"),
    Arm("LEARN", "a wild battle that takes the Mudkip to level 15: BIDE learned, GROWL forgotten, the reason logged",
        "learn_r116.ss1", 12000, 600.0, story(), seed=1,
        doc="gates/make_step4_fixtures.py --only learn (learn_r116.build.json): route116team.ss1 played on by the AI's own "
            "battle brain (Story, seed 5) until a wild battle began with the Mudkip one battle short of level 15"),
    # (the step-4 verifier's round)
    Arm("DFAINT", "a double battle's PARTNER faints: the one sent in is not the Grovyle still on the field, and it wins",
        "geodude_grovyle.ss1", 30000, 1200.0, story(**{ENV_FAULT_IGNORE_TYPES: "1"}), seed=6,
        doc="as TYPE; seed 6 with the types fault is the verifier's own reproduction (rate_step4 TYPE-FAULT seed 6)"),
    Arm("DFAINTX", "FAULT of DFAINT, the step-4 code (field forgotten, refusal watched): the battle STUCK, as the verifier found",
        "geodude_grovyle.ss1", 30000, 1200.0,
        story(**{ENV_FAULT_IGNORE_TYPES: "1", ENV_FAULT_FORGET_FIELD: "1", ENV_FAULT_IGNORE_REFUSAL: "1"}), seed=6,
        doc="as DFAINT"),
    Arm("REFUSE", "resumed ON the party menu's 'SKITTY is already in battle!': read, A on its wait, Mightyena in, won",
        "ki17_partymenu_wedge.ss1", 30000, 1200.0, story(), seed=1,
        doc="tools/story-dev/saves/ki17_partymenu_wedge.ss1: the story bot's KI-17 wedge, saved on the battle party "
            "menu's refusal (Mauville gym)"),
]


# ---------------------------------------------------------------------- running
def run_arm(arm: Arm, build_root: Path) -> Run:
    run = Run(arm)
    profile_dir, _ = launcher.ensure_profile(build_root, PROFILE)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {PROFILE} is not ai_player-owned; refusing to touch it")
    launcher.force_http_off(profile_dir)
    cheats = profile_dir / "game_cheats.yml"
    if cheats.exists():
        cheats.unlink()
    run.before, raw = truth_of(FIXTURES[arm.fixture][0])
    if run.before is None:
        run.notes.append(f"truth of the fixture failed: {raw[-1500:]}")
    run.run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    run.command = [sys.executable, "-m", "ai_player", "run", "--profile", PROFILE, "--frames", str(arm.frames),
                   "--wall-seconds", f"{arm.wall:g}", "--build-root", str(build_root), "--run-dir", str(run.run_dir),
                   "--state", str(FIXTURES[arm.fixture][0])]
    env = clean_env({ENV_BRAIN: "battle", ENV_SEED: str(arm.seed), **arm.env})
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


def replay_arm(run: Run) -> None:
    """THE REPLAY (module docstring): the arm in-process from the same fixture, seed, personality and faults, the game's
    battle read after every frame (`hands_harness.py --battle-log`)."""
    arm = run.arm
    faults = ",".join(name for env, name in FAULT_NAMES.items() if arm.env.get(env) == "1")
    folder = Path(tempfile.mkdtemp(prefix=f"ai_step4_replay_{arm.name}_"))
    command = [sys.executable, str(HARNESS), "battle", "--state", str(FIXTURES[arm.fixture][0]), "--seed", str(arm.seed),
               "--frames", str(arm.frames), "--personality", arm.env.get(ENV_PERSONALITY, "Story"),
               "--battles", arm.env.get(ENV_BATTLES, "1"), "--run-dir", str(folder), "--game-clock", REPLAY_CLOCK,
               "--battle-log", *(["--fault", faults] if faults else [])]
    try:
        data, raw = run_json(command, "HANDS", clean_env({}), arm.wall + 240)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    run.replay = data
    if data is None:
        run.notes.append(f"the replay gave no result: {raw[-1500:]}")


def check_replay(run: Run) -> dict | None:
    """The replay counts only as THIS run's trajectory: its frames and presses equal the launcher's. Returns its game
    record (`BattleRecorder.result`), or None (the check failed)."""
    data = run.replay or {}
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames")
    presses = run.measures.get("presses")
    same = bool(data) and data.get("frames") == frames and data.get("presses") == presses
    run.check(same, f"THE REPLAY is this run's trajectory: in-process (`hands_harness.py --battle-log`, the same fixture, seed "
                    f"{run.arm.seed} and faults) {data.get('frames')} frames and {data.get('presses')} presses == the launcher's "
                    f"{frames} and {presses} (one trajectory replayed, not a second sample); its outcome {data.get('reason')!r}")
    return (data.get("game_battle") or {}) if same else None


def game_hits(game: dict, attacker: int | None = None) -> list[tuple[str, str, str]]:
    """(the user's species, the move, the species hit) of every HP change one battler's move made on ANOTHER battler, in
    order, by the GAME (`gBattleMons`, `gBattlerAttacker`, `gCurrentMove`, `gBattlerTarget`)."""
    return [(e["attacker_species"], e["move"], e["species"]) for e in game.get("events") or []
            if e["kind"] == "hp" and e["battler"] != e["attacker"] and (attacker is None or e["attacker"] == attacker)
            and e["hp"][1] < e["hp"][0]]


def game_replacements(game: dict) -> list[dict]:
    """Every Pokemon that came onto a PLAYER's position (0, 2) where the one before it had fainted (HP 0), by the GAME,
    with the PID and HP standing on the player's other position at that frame (`rate_step4.game_sent_in`'s rule)."""
    here = {s["battler"]: (s["pid"], s["hp"][0], s.get("species")) for s in game.get("start") or []}
    out = []
    for event in game.get("events") or []:
        if event["kind"] == "in" and event["battler"] in (0, 2):
            before = here.get(event["battler"])
            if before is not None and before[0] != "00000000" and before[1] == 0:
                out.append({**event, "replaced": before, "beside": here.get(2 - event["battler"])})
        if event["kind"] in ("in", "hp"):
            hp = event["hp"][0] if event["kind"] == "in" else event["hp"][1]
            here[event["battler"]] = (event["pid"], hp, event["species"])
    return out


def told_sent(run: Run) -> list[str]:
    """The species the decider named at each party menu ("who goes in: Taillow L6 ...")."""
    return re.findall(r"who goes in: (.+?) L\d+ ", "\n".join(battle_lines(run)))


# ---------------------------------------------------------------------- shared checks
def check_after_is_this_run(run: Run) -> None:
    """The state graded is the one THIS run wrote: written after the run started, its frame the start's plus the run's
    real frames (+-FRAME_SLACK), not the fixture's bytes (as `live_step3.check_after_is_this_run`)."""
    after = run.after or {}
    before_md5 = FIXTURES[run.arm.fixture][1]
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    start_frame = (run.before or {}).get("frame") or 0
    frame = after.get("frame")
    written = run.state_mtime is not None and run.state_mtime >= run.started - 1.0
    near = isinstance(frame, int) and frames > 0 and abs(frame - (start_frame + frames)) <= FRAME_SLACK
    run.check(bool(after) and written and near and after.get("state_md5") != before_md5,
              f"the state graded is the one THIS run wrote: written "
              f"{'%.1fs after the run started' % (run.state_mtime - run.started) if run.state_mtime else 'NEVER'}; frame {frame} "
              f"== start {start_frame} + {frames} real frames (+-{FRAME_SLACK}); md5 {after.get('state_md5')} (fixture {before_md5})")


def selftest_after_check() -> list[str]:
    """FAULT-TEST of `check_after_is_this_run` (CLAUDE.md rule 6): its own state passes; a stale one, a frame off by
    3000, no file and the fixture's own bytes fail."""
    arm = ARMS[0]
    md5 = FIXTURES[arm.fixture][1]

    def verdict(mtime, frame, state_md5) -> bool:
        run = Run(arm, started=1000.0, state_mtime=mtime, verdict={"counters": {"real_frames": 3344}},
                  before={"frame": 15268}, after=None if frame is None else {"frame": frame, "state_md5": state_md5})
        check_after_is_this_run(run)
        return run.passed

    cases = [("its own state", verdict(1500.0, 18612, "abc"), True),
             ("a stale state (mtime before the start)", verdict(900.0, 18612, "abc"), False),
             ("a frame +3000", verdict(1500.0, 21612, "abc"), False),
             ("no state file", verdict(None, None, "abc"), False),
             ("the fixture's own bytes", verdict(1500.0, 18612, md5), False)]
    return [f"{name}: passed={got}, want {want}" for name, got, want in cases if got != want]


def check_hands(run: Run, walking: bool) -> None:
    """Every press has its gate; every A is a WAIT, a MENU confirm (the battle's menus included: the action menu, the
    move grid, the target, the battle's yes/no, the bag and its USE, the party and its SHIFT / SEND OUT, the forget-a-move
    list) or a TALK, by its look; walking holds only in the arms that walk; no catch-all idle."""
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
            wrong.append((press["frame"], kind, press["reason"][:60], (press.get("digest") or "")[:90]))
    run.check(not wrong, f"EVERY A press is a WAIT, a MENU confirm or a TALK by its look: {dict(sorted(kinds.items()))}, "
                         f"the menus {dict(sorted(menus.items()))}; any other: {wrong[:4] or 'none'}")
    blind = [p for p in presses if "NONE" in str(p.get("reason"))]
    run.check(not blind, f"no press without the eyes asked (a 'NONE' gate): {len(blind)}")
    walks = [p for p in presses if str(p.get("reason", "")).startswith(("walk ", "keep walking ", "use the ", "roam "))]
    run.check(bool(walks) == walking, f"{len(walks)} walking holds (want {'some' if walking else 'none'}: this arm "
                                      f"{'walks' if walking else 'starts in a battle'})")
    idle = [r for r in run.records if r.get("decision") == "watch"]
    generic = [(r["frame"], r["reason"]) for r in idle if str(r.get("reason", "")).startswith(GENERIC_BUSY)]
    run.check(not generic, f"{len(idle)} stretches standing still, NONE under the catch-all {GENERIC_BUSY!r}: {generic[:3] or 'none'}")


def battle_lines(run: Run) -> list[str]:
    return [line for line in run.ai_log.splitlines() if "[AI-HANDS] battle" in line]


def decisions(run: Run) -> list[dict]:
    """The decider's every decision at the action menu (the action log's `decide` records)."""
    return [r for r in run.records if r.get("decision") == "decide" and str(r.get("action", "")).startswith("battle ")]


def outcomes(run: Run) -> list[str]:
    found = re.search(r"battles: \d+ played:? (\[.*?\])", run.outcome)
    return json.loads(found.group(1).replace("'", '"')) if found else []


def party_of(truth: dict | None) -> dict[str, list]:
    """PID -> [species, total experience, level] by the framework's decoder (the second path)."""
    return {row[0]: row[1:] for row in (truth or {}).get("party_exp") or []}


def moves_of(truth: dict | None) -> dict[str, list[str]]:
    return {row[0]: row[2] for row in (truth or {}).get("party_moves") or []}


def balls_of(truth: dict | None) -> int:
    return sum((truth or {}).get("balls", {}).values()) if isinstance((truth or {}).get("balls"), dict) else -1


def stat(truth: dict | None, key: str) -> int | None:
    return ((truth or {}).get("game_stats") or {}).get(key)


def flag(truth: dict | None, name: str) -> bool | None:
    return ((truth or {}).get("flags") or {}).get(name)


def trainer(truth: dict | None, tid: str) -> bool | None:
    return ((truth or {}).get("trainer_defeated") or {}).get(tid)


def grade_common(run: Run, walking: bool) -> None:
    check_purity(run, None)
    check_after_is_this_run(run)
    check_hands(run, walking)
    run.measure("outcomes", outcomes(run))
    run.measure("frames", ((run.verdict or {}).get("counters") or {}).get("real_frames"))
    summary = next((line for line in run.stdout.splitlines() if line.startswith("[AI-HANDS] outcome=")), "")
    pad = re.search(r"presses=(\d+)", summary)
    run.measure("presses", int(pad.group(1)) if pad else None)
    for line in battle_lines(run):
        run.notes.append(line[:600])


def exp_rose(run: Run, pid: str) -> tuple[bool, str]:
    before, after = party_of(run.before).get(pid), party_of(run.after).get(pid)
    ok = before is not None and after is not None and after[1] > before[1]
    return ok, f"{pid}: {before} -> {after}"


# ---------------------------------------------------------------------- the arms
def grade_WILD(run: Run) -> None:
    grade_common(run, walking=True)
    results = outcomes(run)
    run.check("won" in results, f"a wild battle WON by fighting among the battles played: {results}")
    ok, text = exp_rose(run, MUDKIP)
    run.check(ok, f"the Mudkip's experience rose, by PID (the framework's decoder): {text}")
    fights = [d for d in decisions(run) if d.get("action") == "battle fight"]
    run.check(bool(fights), f"the AI chose FIGHT {len(fights)} times; its moves {sorted({(d.get('extra') or {}).get('move') for d in fights})}")
    played, wild = len(results), (stat(run.after, "wild_battles") or 0) - (stat(run.before, "wild_battles") or 0)
    run.check(wild == played, f"the game's own wild-battle count rose by {wild} == the battles the AI played {played}")
    run.measure("won", results.count("won"))


def grade_CATCH(run: Run) -> None:
    grade_common(run, walking=True)
    results = outcomes(run)
    run.check(results == ["caught"] and (run.after or {}).get("battle_outcome") == 7,
              f"the battle ended CAUGHT: the AI's outcome {results}, gBattleOutcome {(run.after or {}).get('battle_outcome')} (7)")
    tid = (run.after or {}).get("player_tid")
    before = {row[0] for row in (run.before or {}).get("party_ot") or []} | {row[0] for row in (run.before or {}).get("boxes") or []}
    after = [(row[0], row[1], "party") for row in (run.after or {}).get("party_ot") or []] + \
            [(row[0], row[1], "box") for row in (run.after or {}).get("boxes") or []]
    new = [entry for entry in after if entry[0] not in before]
    run.check(len(new) == 1 and new[0][1] == tid,
              f"ONE new PID owned by the player: {new} (the player's visible id {tid}; a catch is a new PID with the player's OT)")
    throws = [d for d in decisions(run) if d.get("action") == "battle ball"]
    spent = balls_of(run.before) - balls_of(run.after)
    run.check(bool(throws) and spent == len(throws),
              f"the balls in the bag fell by {spent} == the balls the AI threw {len(throws)} ({balls_of(run.before)} -> {balls_of(run.after)})")
    first = decisions(run)[0] if decisions(run) else {}
    weakened = first.get("action") == "battle fight" and "weaken" in str(first.get("reason"))
    run.check(weakened or "bar is at" in str(first.get("reason")),
              f"it weakened the foe first while the bar was above half, or threw at once with the reason why: "
              f"{first.get('action')}: {str(first.get('reason'))[:160]}")
    run.measure("throws", len(throws))


def grade_TRAINER(run: Run) -> None:
    grade_common(run, walking=False)
    run.check(outcomes(run) == ["won"], f"the battle WON: {outcomes(run)}")
    run.check(trainer(run.before, JOEY) is False and trainer(run.after, JOEY) is True,
              f"YOUNGSTER JOEY's defeated flag (TRAINER_FLAGS_START + 322): {trainer(run.before, JOEY)} -> {trainer(run.after, JOEY)}")
    ok, text = exp_rose(run, GROVYLE)
    run.check(ok, f"the Grovyle's experience rose: {text}")


def grade_RIVAL(run: Run) -> None:
    grade_common(run, walking=False)
    run.check(outcomes(run) == ["won"], f"the rival battle WON: {outcomes(run)}")
    run.check(flag(run.before, "DEFEATED_RIVAL_ROUTE103") is False and flag(run.after, "DEFEATED_RIVAL_ROUTE103") is True,
              f"DEFEATED_RIVAL_ROUTE103: {flag(run.before, 'DEFEATED_RIVAL_ROUTE103')} -> {flag(run.after, 'DEFEATED_RIVAL_ROUTE103')}")
    run.check(trainer(run.before, MAY) is False and trainer(run.after, MAY) is True,
              f"MAY's trainer flag (TRAINER_MAY_ROUTE_103_MUDKIP 529): {trainer(run.before, MAY)} -> {trainer(run.after, MAY)}")


def grade_CHALLENGE(run: Run) -> None:
    grade_common(run, walking=True)
    talks = [p for p in run.presses if str(p.get("reason", "")).startswith("talk: facing ")]
    trainer_battles = (stat(run.after, "trainer_battles") or 0) - (stat(run.before, "trainer_battles") or 0)
    run.check(bool(talks) and trainer_battles == 1,
              f"the AI walked up to May and TALKED ({len(talks)} talk A: {[str(t.get('reason'))[:70] for t in talks][:2]}); the "
              f"game's trainer-battle count rose by {trainer_battles} (1)")
    results = outcomes(run)
    won = flag(run.after, "DEFEATED_RIVAL_ROUTE103")
    run.check(len(results) == 1 and results[0] in ("won", "lost") and (results[0] == "won") == bool(won),
              f"the battle played to its end by the decider: {results}; the game agrees: DEFEATED_RIVAL_ROUTE103 {won}")
    run.measure("result", results[0] if results else None)


def grovyle_turns(run: Run) -> list[tuple[str, str]]:
    """Grovyle's decisions, from the decider's TOLD lines (Grovyle's are the ones valuing Fury Cutter): (the move, the foe
    it was aimed at in the double battle: "at <species>" before the values; "" once one foe is left and nothing is aimed)."""
    found = []
    for line in battle_lines(run):
        hit = re.search(r"turn \d+: fight (.+?): ", line)
        if hit is None or "[Fury Cutter:" not in line:
            continue
        aim = re.search(r" at (\w+) \[Fury Cutter:", line)
        found.append((hit.group(1), aim.group(1) if aim else ""))
    return found


def grade_TYPE(run: Run) -> None:
    grade_common(run, walking=False)
    turns = grovyle_turns(run)
    against = [t for t in turns if t[1] == "Geodude"]
    run.check(bool(turns) and turns[0] == ("Absorb", "Geodude"),
              f"Grovyle's FIRST move, the Geodude on the field: {turns[:1]} (want Absorb aimed at the Geodude: Grass x4, worth "
              f"120, against Pursuit 40 and Quick Attack 20)")
    run.check(bool(against) and all(move == "Absorb" for move, _ in against),
              f"every move Grovyle aimed at the Geodude is ABSORB: {against}")
    run.check(outcomes(run) == ["won"], f"the battle won: {outcomes(run)}")
    run.check(trainer(run.after, "631") is True and trainer(run.after, "754") is True,
              f"the game's defeated flags of both trainers (CLARK 631, JOHNSON 754): {trainer(run.after, '631')}, "
              f"{trainer(run.after, '754')}")
    run.measure("first", list(turns[0]) if turns else None)
    game = check_replay(run)
    if game is not None:
        hits = game_hits(game, attacker=0)
        on_geodude = [move for _, move, hit in hits if hit == "Geodude"]
        run.check(bool(hits) and hits[0][1:] == ("Absorb", "Geodude") and on_geodude and set(on_geodude) == {"Absorb"},
                  f"BY THE GAME (the replay): Grovyle's first hit {hits[:1]} is ABSORB on the Geodude, and every hit it landed "
                  f"on the Geodude was Absorb: {on_geodude}")


def grade_TYPEX(run: Run) -> None:
    grade_common(run, walking=False)
    turns = grovyle_turns(run)
    run.check(bool(turns) and turns[0][0] != "Absorb" and not any(t == ("Absorb", "Geodude") for t in turns),
              f"FAULT (types ignored): Grovyle's first move {turns[:1]} is not Absorb, and Absorb is NEVER aimed at the Geodude "
              f"({turns})")
    told = "\n".join(battle_lines(run))
    run.check("x1 type" in told and "x4 type" not in told and "x0.5 type" not in told,
              "the fault's decider weighed every matchup x1 (no 'x4 type' or 'x0.5 type' in its told values)")
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own decision rule: purity is still CLEAN")
    run.measure("first", list(turns[0]) if turns else None)
    game = check_replay(run)
    if game is not None:
        hits = game_hits(game, attacker=0)
        run.check(bool(hits) and hits[0][1] != "Absorb" and ("Grovyle", "Absorb", "Geodude") not in hits,
                  f"BY THE GAME (the replay), FAULT: Grovyle's first hit {hits[:1]} is not Absorb, and Absorb never hit the "
                  f"Geodude: {hits}")


def grade_FAINT(run: Run) -> None:
    grade_common(run, walking=False)
    lead = party_of(run.after).get(MUDKIP)
    hp = next((row[1] for row in (run.after or {}).get("party") or [] if row[0] == "Mudkip"), None)
    run.check(hp == 0, f"the lead Mudkip FAINTED: its HP by the second path {hp} (party {(run.after or {}).get('party')})")
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    party = [p for p in run.presses if str(p.get("reason", "")).startswith("party cursor on ")]
    send = [p for p in run.presses if str(p.get("reason", "")).startswith("party_action cursor on") and "SEND OUT" in str(p.get("reason"))]
    run.check(bool(sent) and bool(party) and bool(send),
              f"the AI chose who goes in ({[s.split('who goes in: ')[-1][:80] for s in sent]}), pressed on the party menu by "
              f"reading its cursor ({[str(p.get('reason')) for p in party]}) and SEND OUT ({len(send)})")
    run.check(outcomes(run) == ["won"] and trainer(run.after, KAREN) is True,
              f"the battle went on to its end: {outcomes(run)}; KAREN's flag (280) {trainer(run.before, KAREN)} -> {trainer(run.after, KAREN)}")
    run.measure("lead", lead)
    # (the step-4 verifier's round) the replacement is chosen AGAINST the foe the decider remembers through the party menu
    run.check(bool(sent) and all(" against Shroomish" in s and "REMEMBERED" in s for s in sent),
              f"the replacement was chosen against the foe REMEMBERED through the party menu (it has no battle view): "
              f"{[s.split('who goes in: ')[-1][:160] for s in sent]}")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        run.check([e["species"] for e in came] == told_sent(run) and all(e["battler"] == 0 for e in came)
                  and all(e["replaced"][2] == "Mudkip" for e in came),
                  f"BY THE GAME (the replay): after the Mudkip's HP 0 at position 0, {[(e['battler'], e['species'], e['pid']) for e in came]} "
                  f"came onto it == the decider's choice {told_sent(run)}")


def grade_DFAINT(run: Run) -> None:
    grade_common(run, walking=False)
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    run.check(len(sent) == 1 and "Grovyle on the field" in sent[0] and "REMEMBERED" in sent[0]
              and not sent[0].split("who goes in: ")[-1].startswith("Grovyle"),
              f"the PARTNER fell and the decider named a Pokemon NOT standing on the field, from the field it REMEMBERED: "
              f"{[s.split('who goes in: ')[-1][:200] for s in sent]}")
    refused = [line for line in battle_lines(run) if "already in battle" in line]
    run.check(not refused, f"the game refused nothing ('already in battle' never read): {refused[:2] or 'none'}")
    run.check(outcomes(run) == ["won"] and trainer(run.after, "631") is True and trainer(run.after, "754") is True,
              f"the battle WON: {outcomes(run)}; CLARK 631 {trainer(run.before, '631')} -> {trainer(run.after, '631')}, JOHNSON "
              f"754 {trainer(run.before, '754')} -> {trainer(run.after, '754')}")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        ok = (len(came) == 1 and came[0]["battler"] == 2 and came[0]["replaced"][2] == "Nincada"
              and came[0]["species"] == told_sent(run)[0] and (came[0]["beside"] or ("", 0, ""))[2] == "Grovyle"
              and (came[0]["beside"] or ("", 0, ""))[1] > 0 and came[0]["pid"] != (came[0]["beside"] or ("",))[0])
        run.check(ok, f"BY THE GAME (the replay): the Nincada's HP 0 at position 2, then "
                      f"{[(e['battler'], e['species'], e['pid']) for e in came]} came onto position 2 while "
                      f"{[e['beside'] for e in came]} stood at position 0 (a different PID, HP above 0)")


def grade_DFAINTX(run: Run) -> None:
    grade_common(run, walking=False)
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    run.check(len(sent) == 1 and sent[0].split("who goes in: ")[-1].startswith("Grovyle"),
              f"FAULT (the step-4 code): the decider, seeing only the party menu, named the Grovyle standing on the field: "
              f"{[s.split('who goes in: ')[-1][:160] for s in sent]}")
    run.check(outcomes(run) == ["the battle: no Pokemon could be sent in"] and "stuck" in run.outcome,
              f"the run ended STUCK, as the verifier found the step-4 code: {run.outcome!r}")
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own rule: purity is still CLEAN")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        run.check(not came, f"BY THE GAME (the replay): nobody came onto the field after the Nincada fell: {came}")


def grade_REFUSE(run: Run) -> None:
    grade_common(run, walking=False)
    said = [line for line in battle_lines(run) if "the party says" in line]
    run.check(len(said) == 1 and "SKITTY is already in battle!" in said[0] and "Skitty" in said[0].split(":")[-1],
              f"the AI READ the party menu's refusal and the decider was told who was refused: {said}")
    waits = [p for p in run.presses if p["action"].startswith("press A ") and p.get("reason") == "text printer 6 WAIT"
             and "ui=party(busy)[" in str(p.get("digest"))]
    run.check(len(waits) == 1, f"ONE A pressed on the refusal's WAIT, over the busy party list: "
                               f"{[(p['frame'], (p.get('digest') or '')[:110]) for p in waits]}")
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    run.check(len(sent) == 1 and sent[0].split("who goes in: ")[-1].startswith("Mightyena") and "refused" in sent[0],
              f"the next choice is the other healthy member, the refused one named: {[s.split('who goes in: ')[-1][:200] for s in sent]}")
    run.check(outcomes(run) == ["won"] and (run.after or {}).get("battle_outcome") == 1,
              f"the battle WON: {outcomes(run)}, gBattleOutcome {(run.after or {}).get('battle_outcome')}")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        mightyena = next((row[0] for row in (run.before or {}).get("party_exp") or [] if row[1] == "Mightyena"), None)
        run.check(len(came) == 1 and came[0]["pid"] == mightyena,
                  f"BY THE GAME (the replay): {[(e['battler'], e['species'], e['pid']) for e in came]} came onto the field: "
                  f"the Mightyena by its PID {mightyena}")


def grade_LEARN(run: Run) -> None:
    grade_common(run, walking=False)
    before, after = party_of(run.before).get(MUDKIP), party_of(run.after).get(MUDKIP)
    run.check(before is not None and after is not None and before[2] == 14 and after[2] == 15,
              f"the Mudkip (PID {MUDKIP}) reached level 15 (the second path): {before} -> {after}")
    moves = moves_of(run.after).get(MUDKIP) or []
    run.check("Bide" in moves and "Growl" not in moves and len(moves) == 4,
              f"its moves now {moves} (was {moves_of(run.before).get(MUDKIP)}): BIDE learned, GROWL forgotten")
    told = [line for line in battle_lines(run) if "would learn" in line]
    forget = [p for p in run.presses if str(p.get("reason", "")).startswith("move_forget cursor on") and "Growl" in str(p.get("reason"))]
    run.check(bool(told) and bool(forget),
              f"the decision told with its reason ({[t.split('would learn ')[-1][:160] for t in told]}) and pressed on the "
              f"summary screen on GROWL by reading the cursor ({[str(p.get('reason')) for p in forget]})")


GRADERS = {"WILD": grade_WILD, "CATCH": grade_CATCH, "TRAINER": grade_TRAINER, "RIVAL": grade_RIVAL,
           "CHALLENGE": grade_CHALLENGE, "TYPE": grade_TYPE, "TYPEX": grade_TYPEX, "FAINT": grade_FAINT, "LEARN": grade_LEARN,
           "DFAINT": grade_DFAINT, "DFAINTX": grade_DFAINTX, "REFUSE": grade_REFUSE}


# ---------------------------------------------------------------------- pre-registration
def check_predictions(run: Run) -> None:
    for name, want in PREDICTED.get(run.arm.name, {}).items():
        got = run.measures.get(name)
        held = got == want
        run.predictions.append((name, want, got, held))
        run.check(held, f"PRE-REGISTERED {name}: predicted {want}, measured {got}")


def md5_of(path: Path) -> str:
    import hashlib

    return hashlib.md5(path.read_bytes()).hexdigest()


def write_evidence(run: Run, code_ref: str, tag: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{tag}-{run.arm.name}.txt"
    fixture = FIXTURES[run.arm.fixture]
    env = " ".join(f"{k}={v}" for k, v in {ENV_BRAIN: "battle", ENV_SEED: str(run.arm.seed), **run.arm.env}.items())
    out = [
        f"AI PLAYER BUILD STEP 4 (BATTLES) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"code: {code_ref}",
        f"fixture: {fixture[0].relative_to(REPO).as_posix()} md5={md5_of(fixture[0])}",
        f"fixture documentation: {run.arm.doc or '-'}",
        f"command: {' '.join(run.command)}",
        f"env: {env}",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        SELFTEST_LINE,
        "checks (pre-registered in ai_player/gates/live_step4.py's docstring and PREDICTED; each quotes both values):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
        f"MEASURED: {json.dumps(run.measures, sort_keys=True, ensure_ascii=False, default=str)}",
    ]
    if run.notes:
        out += ["", "---- notes: the decider's told lines ----", *run.notes]
    if run.replay is not None:
        game = run.replay.get("game_battle") or {}
        out += ["", f"---- THE REPLAY in-process (hands_harness.py --battle-log): {run.replay.get('frames')} frames, "
                    f"{run.replay.get('presses')} presses, {run.replay.get('reason')!r}; the GAME's battle, read each frame "
                    f"(gBattleMons, gBattlerAttacker, gCurrentMove, gBattlerTarget, gChosenMoveByBattler) ----",
                f"at the start: {json.dumps(game.get('start'), ensure_ascii=False)}",
                *[json.dumps(e, ensure_ascii=False) for e in game.get("events") or []],
                *[f"chosen {json.dumps(c, ensure_ascii=False)}" for c in game.get("chosen") or []]]
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
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {str(r.get('reason'))[:220]} | "
                           f"{(r.get('digest') or '')[:200]}")
    if run.stdout:
        keep = [line for line in run.stdout.splitlines() if line.startswith(("[AI-", "[DRIVER]"))]
        out += ["", "---- evidence lines from stdout ([AI-*]) ----", *[line[:600] for line in keep]]
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
        if "pokebot.py" in cmd and PROFILE in cmd:
            found.append(f"{proc.info['pid']}: {cmd[:120]}")
    return found


def main() -> int:
    global SELFTEST_LINE
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build step 4 (battles).")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS))
    parser.add_argument("--evidence-tag", default=EVIDENCE_TAG)
    args = parser.parse_args()
    broken = selftest_after_check()
    SELFTEST_LINE = (f"[SELFTEST] check_after_is_this_run on 5 synthetic runs (its own: pass; a stale mtime, a frame +3000, no "
                     f"file, the fixture's md5: fail): {'PASS' if not broken else 'FAIL ' + str(broken)}")
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
            print(f"ABORT: fixture {name} has md5 {actual}, pinned {md5}")
            return 2
    build_root = launcher.resolve_build_root()
    code_ref = tree_provenance(REPO)
    print(f"code: {code_ref}")
    results: list[Run] = []
    for arm in [a for a in ARMS if a.name in wanted]:
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        run = run_arm(arm, build_root)
        if arm.name in REPLAYED:
            replay_arm(run)
        GRADERS[arm.name](run)
        check_predictions(run)
        evidence = write_evidence(run, code_ref, args.evidence_tag)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text[:400]}")
    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<9} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    held = sum(1 for run in results for p in run.predictions if p[3])
    total = sum(len(run.predictions) for run in results)
    print(f"  PRE-REGISTERED NUMBERS: {held} of {total} held")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
