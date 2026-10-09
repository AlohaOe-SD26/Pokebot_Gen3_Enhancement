"""TEST SIDE: build the fixtures of build step 4's live proof (`gates/live_step4.py`), by PLAYING, with button presses only
(no memory write), in a throwaway emulator.

    py -3.12 ai_player/gates/make_step4_fixtures.py [--only type|learn|faint] [--seeds 1-20]

  geodude_grovyle.ss1    (arm TYPE) the FIRST frame of a TRAINER battle against a GEODUDE (Rock/Ground) with GROVYLE out
                         (Fury Cutter, Pursuit, Absorb, Quick Attack): `trainer_battle_r116.ss1` (Joey's battle at its start;
                         md5 pinned below) played on by the AI's OWN battle brain (Story, the cartridge's clock pinned): it
                         beats Joey, roams Route 116's grass, and a hiker's Geodude engages it; saved on the battle's first
                         frame. WHY THIS BATTLE (the task's own example, "a Water/Grass move vs Geodude/rock"): the moves'
                         worth turns over with the type chart. Absorb is the WEAKEST move by power (20, STAB: 30) and the
                         only effective one (Grass x2 on Rock, x2 on Ground: worth 120); Quick Attack (Normal 40, x0.5 on
                         Rock: 20) and Pursuit (Dark 40, neutral: 40) look stronger. With the type chart IGNORED (the FAULT)
                         the decider weighs 40, 40, 30: Absorb is never among the near-best.
  learn_r116.ss1         (arm LEARN) the FIRST frame of a wild battle on Route 116 in which the lead MUDKIP (four moves:
                         Tackle, Growl, Mud-slap, Water Gun) is within one battle of level 15, where it learns BIDE (pret
                         `src/data/pokemon/level_up_learnsets.h` sMudkipLevelUpLearnset: LEVEL_UP_MOVE(15, MOVE_BIDE)):
                         `route116team.ss1` (md5 pinned below) played on by the AI's OWN battle brain (`hands_harness`'s
                         loop: brain `battle`, Story, the cartridge's clock pinned), saved when a wild battle begins with the
                         Mudkip's experience at 1,960 or more (level 15 is 2,035: `src/pokemon.c` GROWTH_MEDIUM_SLOW), at
                         half its HP or more, against a species the Pokedex already OWNS (so no catch takes the experience).
                         Seeds are tried in order until one gets there (the build prints which).
  faint_r116.ss1         (arm FAINT) the FIRST frame of a TRAINER battle on Route 116 begun by the AI's own roaming from
                         `route116team.ss1`, its lead Mudkip below 85 % of its HP: the battle the FAINT arm plays.
Each is saved with a `.build.json` printout (what was played, the second-path truth of the end). A rebuild does not
reproduce the bytes (the emulator's real-time clock is in a state): re-pin the md5s in `live_step4.py` after one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import HarnessControls, pin_game_clock, truth  # noqa: E402
from ai_player.gates.probe_eyes import boot, resolve_build_root  # noqa: E402

if str(resolve_build_root()) not in sys.path:
    sys.path.insert(0, str(resolve_build_root()))  # the framework's `modules` (the test side reads through it)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAVES = REPO / "tools" / "story-dev" / "saves"
TRAINER_R116 = (FIXTURES / "trainer_battle_r116.ss1", "f55f3c2ec6efb9fb20363e8ca92b73ba")
ROUTE116TEAM = (SAVES / "route116team.ss1", "9710585350be10534737c4362c33189e")
TYPE = FIXTURES / "geodude_grovyle.ss1"
LEARN = FIXTURES / "learn_r116.ss1"
FAINT = FIXTURES / "faint_r116.ss1"
RECOIL_SOURCE = (SAVES / "ch13_r119_wedge.ss1", "b04d3e4cb7d8c8e2a3b82225548906ef")
RECOIL = FIXTURES / "recoil_r102.look.json"
ROUTE103 = (SAVES / "route103.ss1", "0d951fe21be35a6eafade207ddff5961")
RIVAL = FIXTURES / "rival_r103.ss1"
#: Mudkip: level 15 at 2,035 experience (GROWTH_MEDIUM_SLOW: 6/5 n^3 - 15 n^2 + 100 n - 140); saved from 1,960 on.
LEARN_EXP_FROM, LEARN_EXP_TO = 1960, 2035
GAME_CLOCK = "2026-10-08T10:00"
PROFILE = "ai-step0-fixture"


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def check(source: tuple[Path, str]) -> None:
    if md5(source[0]) != source[1]:
        raise SystemExit(f"{source[0]} is not the pinned fixture (md5 {md5(source[0])}, want {source[1]})")


class Presser:
    """TEST-SIDE presses on the throwaway emulator, each chosen from what the AI's eyes show (read only), and logged."""

    def __init__(self, context) -> None:
        from ai_player.host.eyes import FrameworkEyes

        self.context = context
        self.emulator = context.emulator
        self.eyes = FrameworkEyes()
        self.log: list[str] = []

    def look(self):
        return self.eyes.look()

    def wait(self, frames: int) -> None:
        for _ in range(frames):
            self.emulator.run_single_frame()

    def press(self, button: str, why: str, hold: int = 5, gap: int = 14) -> None:
        self.log.append(f"f{self.emulator.get_frame_count()} {button}: {why}")
        self.emulator.hold_button(button)
        self.wait(hold)
        self.emulator.release_button(button)
        self.wait(gap)

    def until_ui(self, kind: str, budget: int = 3000):
        """A on the game's waits (and nothing else) until the `kind` menu is on screen and takes input."""
        for _ in range(budget):
            look = self.look()
            ui = look.screen.ui
            if ui is not None and ui.kind == kind and ui.accepts_input:
                return look
            if ui is None and look.screen.waits_for_button:
                self.press("A", f"a wait: {look.screen.wait_reason}")
                continue
            self.wait(1)
        raise SystemExit(f"the {kind} menu did not come within {budget} looks")

    def grid_to(self, kind: str, index: int) -> None:
        """A 2 x 2 battle grid's cursor (bit 0 the column, bit 1 the row) to `index`, read after every press."""
        for _ in range(8):
            look = self.until_ui(kind)
            cursor = look.screen.ui.cursor
            if cursor == index:
                return
            if (cursor ^ index) & 1:
                self.press("Right" if index & 1 else "Left", f"{kind} cursor {cursor}, wanted {index}")
            else:
                self.press("Down" if index & 2 else "Up", f"{kind} cursor {cursor}, wanted {index}")
        raise SystemExit(f"the {kind} cursor did not reach {index}")

    def list_to(self, kind: str, index: int) -> None:
        """A list's cursor to `index`, read after every press."""
        for _ in range(16):
            look = self.until_ui(kind)
            cursor = look.screen.ui.cursor
            if cursor == index:
                return
            self.press("Down" if cursor < index else "Up", f"{kind} cursor {cursor}, wanted {index}")
        raise SystemExit(f"the {kind} cursor did not reach {index}")


def build_type(seeds: range) -> dict:
    check(TRAINER_R116)
    from modules.memory import read_symbol
    from modules.pokemon_party import get_party

    tried = []
    for seed in seeds:
        last: dict = {}

        def stop(context):
            if not _battle_start(context, last):
                return None
            flags = int.from_bytes(read_symbol("gBattleTypeFlags", size=4), "little")
            lead = get_party()[0]
            facts = {"lead": [lead.species.name, lead.level, lead.current_hp, lead.total_hp,
                              [m.move.name for m in lead.moves if m is not None]], "foe": _enemy_species(context),
                     "trainer": bool(flags & 8), "opponent": int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little")}
            tried.append({"seed": seed, **facts})
            if flags & 8 and facts["foe"] == "Geodude" and lead.species.name == "Grovyle" and lead.current_hp * 2 >= lead.total_hp:
                return facts
            return None

        result = play_until(TRAINER_R116[0], seed, "Story", 12, 60000, stop)
        if result["found"] is not None:
            context = result["context"]
            TYPE.write_bytes(context.emulator.get_save_state())
            return {"fixture": TYPE.name, "md5": md5(TYPE), "source": [str(TRAINER_R116[0].relative_to(REPO)), TRAINER_R116[1]],
                    "played_by": f"the AI's battle brain, Story, seed {seed}, clock {GAME_CLOCK}", "frames": result["frames"],
                    "at": result["found"], "battle_starts_seen": tried, "ai_lines": [l for l in result["lines"] if "battle" in l],
                    "truth": truth(context)}
    raise SystemExit(f"no seed of {list(seeds)} reached a trainer's Geodude: {tried}")


def play_until(state: Path, seed: int, personality: str, battles: int, frames: int, stop,
               talk_to: tuple[int, int] | None = None) -> dict:
    """The AI's OWN battle brain (`ai_player.mode.HandsBrain`, brain `battle`) on a throwaway emulator, one frame per
    `next` (as `hands_harness.play`), with `stop(context)` asked after every frame: when it returns a dict, the state of
    that frame is the result (saved by the caller)."""
    from ai_player.host.eyes import FrameworkEyes
    from ai_player.mode import BrainSettings, HandsBrain
    from ai_player.options import HandsOptions

    context = boot(PROFILE)
    emulator = context.emulator
    emulator.load_save_state(state.read_bytes())
    pin_game_clock(emulator, GAME_CLOCK)
    run_dir = Path(tempfile.mkdtemp(prefix="ai_step4_fixture_"))
    options = HandsOptions(brain="battle", run_dir=run_dir, seed=seed, personality=personality, mart_item="POKé BALL",
                           mart_count=5, clock=None, fault_ungated_a=False, fault_blind_count=False, battles=battles,
                           talk_to=talk_to)
    lines: list[str] = []
    brain = HandsBrain(BrainSettings(frames=frames), lines.append, options)
    steps = brain.play(HarnessControls(emulator), FrameworkEyes())
    count, reason, found = 0, None, None
    while True:
        try:
            next(steps)
        except StopIteration as done:
            reason = done.value
            break
        emulator.run_single_frame()
        count += 1
        found = stop(context)
        if found is not None or count > frames + 10:
            break
    return {"context": context, "found": found, "frames": count, "reason": reason, "lines": lines, "seed": seed}


def _battle_start(context, last: dict) -> bool:
    """True on the FIRST frame of a battle: the framework's game state turns BATTLE from BATTLE_STARTING (the overworld's
    battle transition). Coming back from the bag or the party menu is not a start."""
    from modules.memory import get_game_state

    state = get_game_state().name
    began = state == "BATTLE" and last.get("state") == "BATTLE_STARTING"
    last["state"] = state
    return began


def _enemy_species(context) -> str:
    from modules.pokemon import get_opponent

    return get_opponent().species.name


def _enemy_level(context) -> int:
    from modules.pokemon import get_opponent

    return get_opponent().level


#: Each species' experience yield (the AI's own knowledge file, checked against the decomp by `verify_knowledge.py`).
SPECIES_EXP = {name: entry["exp_yield"] for name, entry in
               json.loads((REPO / "ai_player" / "knowledge" / "species.json").read_text(encoding="utf-8"))["species"].items()}


def _owned(context) -> set[int]:
    from modules.pokedex import get_pokedex

    return {s.national_dex_number for s in get_pokedex().owned_species}


def build_learn(seeds: range) -> dict:
    check(ROUTE116TEAM)
    from modules.memory import read_symbol
    from modules.pokemon import get_species_by_name
    from modules.pokemon_party import get_party

    tried = []
    for seed in seeds:
        last: dict = {}

        def stop(context):
            if not _battle_start(context, last):
                return None
            flags = int.from_bytes(read_symbol("gBattleTypeFlags", size=4), "little")
            party = get_party()
            lead = party[0]
            foe = _enemy_species(context)
            level = _enemy_level(context)
            # the experience this foe gives the one Pokemon that fights it (`src/battle_script_commands.c` Cmd_getexp:
            # `calculatedExp = gSpeciesInfo[...].expYield * gBattleMons[gBattlerFainted].level / 7`, a wild battle):
            # it must take the Mudkip to level 15
            gain = SPECIES_EXP[foe] * level // 7
            facts = {"lead": [lead.species.name, lead.level, lead.total_exp, lead.current_hp, lead.total_hp,
                              [m.move.name for m in lead.moves if m is not None]], "foe": [foe, level, gain],
                     "trainer": bool(flags & 8)}
            tried.append({"seed": seed, **facts})
            if (lead.species.name == "Mudkip" and LEARN_EXP_FROM <= lead.total_exp < LEARN_EXP_TO
                    and lead.total_exp + gain >= LEARN_EXP_TO and lead.current_hp * 2 >= lead.total_hp and not flags & 8
                    and get_species_by_name(foe).national_dex_number in _owned(context)):
                return facts
            return None

        result = play_until(ROUTE116TEAM[0], seed, "Story", 30, 90000, stop)
        if result["found"] is not None:
            context = result["context"]
            LEARN.write_bytes(context.emulator.get_save_state())
            return {"fixture": LEARN.name, "md5": md5(LEARN), "source": [str(ROUTE116TEAM[0].relative_to(REPO)), ROUTE116TEAM[1]],
                    "played_by": f"the AI's battle brain, Story, seed {seed}, clock {GAME_CLOCK}", "frames": result["frames"],
                    "at": result["found"], "battle_starts_seen": tried, "ai_lines": [l for l in result["lines"] if "battle" in l],
                    "truth": truth(context)}
    raise SystemExit(f"no seed of {list(seeds)} reached the learn condition: {tried}")


def build_faint(seeds: range) -> dict:
    check(ROUTE116TEAM)
    from modules.memory import read_symbol
    from modules.pokemon_party import get_party

    tried = []
    for seed in seeds:
        last: dict = {}

        def stop(context):
            if not _battle_start(context, last):
                return None
            flags = int.from_bytes(read_symbol("gBattleTypeFlags", size=4), "little")
            party = get_party()
            lead = party[0]
            facts = {"lead": [lead.species.name, lead.level, lead.current_hp, lead.total_hp], "foe": _enemy_species(context),
                     "trainer": bool(flags & 8), "opponent": int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little")}
            tried.append({"seed": seed, **facts})
            if flags & 8 and lead.current_hp * 100 < 85 * lead.total_hp and facts["opponent"] != 322:
                return facts
            return None

        result = play_until(ROUTE116TEAM[0], seed, "Story", 30, 90000, stop)
        if result["found"] is not None:
            context = result["context"]
            FAINT.write_bytes(context.emulator.get_save_state())
            return {"fixture": FAINT.name, "md5": md5(FAINT), "source": [str(ROUTE116TEAM[0].relative_to(REPO)), ROUTE116TEAM[1]],
                    "played_by": f"the AI's battle brain, Story, seed {seed}, clock {GAME_CLOCK}", "frames": result["frames"],
                    "at": result["found"], "battle_starts_seen": tried, "ai_lines": [l for l in result["lines"] if "battle" in l],
                    "truth": truth(context)}
    raise SystemExit(f"no seed of {list(seeds)} reached the faint condition: {tried}")


def build_rival(seeds: range) -> dict:
    """RIVAL: `route103.ss1` (pinned: Route 103 BEFORE the rival, DEFEATED_RIVAL_ROUTE103 clear, May at (10,3)) played on
    by the AI's OWN battle brain told to challenge the person at (10,3) (`AI_PLAYER_TALK_TO`): it walks up to her, talks,
    reads her words; saved on the FIRST frame of the battle that follows."""
    check(ROUTE103)
    from modules.memory import read_symbol
    from modules.pokemon_party import get_party

    tried = []
    for seed in seeds:
        last: dict = {}

        def stop(context):
            if not _battle_start(context, last):
                return None
            flags = int.from_bytes(read_symbol("gBattleTypeFlags", size=4), "little")
            lead = get_party()[0]
            facts = {"lead": [lead.species.name, lead.level, lead.current_hp, lead.total_hp], "foe": _enemy_species(context),
                     "trainer": bool(flags & 8), "opponent": int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little")}
            tried.append({"seed": seed, **facts})
            return facts if flags & 8 else None

        result = play_until(ROUTE103[0], seed, "Story", 1, 20000, stop, talk_to=(10, 3))
        if result["found"] is not None:
            context = result["context"]
            RIVAL.write_bytes(context.emulator.get_save_state())
            return {"fixture": RIVAL.name, "md5": md5(RIVAL), "source": [ROUTE103[0].relative_to(REPO).as_posix(), ROUTE103[1]],
                    "played_by": f"the AI's battle brain, Story, seed {seed}, talk to (10,3), clock {GAME_CLOCK}",
                    "frames": result["frames"], "at": result["found"], "battle_starts_seen": tried,
                    "ai_lines": [l for l in result["lines"]], "truth": truth(context)}
    raise SystemExit(f"no seed of {list(seeds)} reached the rival's battle: {tried}")


def build_recoil() -> dict:
    """RECORDED (arm RECOIL, `test_battle.py` RecordedRecoilTests): the AI's own Observation at the action menu of a real
    battle with a RECOIL move (`ch13_r119_wedge.ss1`, pinned: Marshtomp L32 74/99 with Take Down, against a wild Poochyena
    on Route 102), reached by A on the battle's waits only; the look's battle, party and bag written as JSON."""
    from dataclasses import asdict

    check(RECOIL_SOURCE)
    context = boot(PROFILE)
    context.emulator.load_save_state(RECOIL_SOURCE[0].read_bytes())
    pin_game_clock(context.emulator, GAME_CLOCK)
    presser = Presser(context)
    look = presser.until_ui("battle_action")
    data = {"source": [str(RECOIL_SOURCE[0].relative_to(REPO)), RECOIL_SOURCE[1]], "frame": look.frame, "digest": look.digest(),
            "presses": presser.log, "battle": asdict(look.battle), "party": [asdict(m) for m in look.party],
            "bag": asdict(look.bag), "owned_dex": list(look.progress.owned_dex)}
    RECOIL.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"fixture": RECOIL.name, "md5": md5(RECOIL), "at": look.digest(), "presses": presser.log}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=("type", "learn", "faint", "recoil", "rival"))
    parser.add_argument("--seeds", default="1-20")
    args = parser.parse_args()
    low, high = (int(p) for p in args.seeds.split("-"))
    seeds = range(low, high + 1)
    builders = {"type": lambda: build_type(seeds), "learn": lambda: build_learn(seeds), "faint": lambda: build_faint(seeds),
                "recoil": build_recoil, "rival": lambda: build_rival(seeds)}
    for name, builder in builders.items():
        if args.only and name != args.only:
            continue
        started = time.monotonic()
        out = builder()
        out["seconds"] = round(time.monotonic() - started, 1)
        path = FIXTURES / (Path(out["fixture"]).stem + ".build.json")
        path.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        print(f"[FIXTURE] {out['fixture']} md5 {out['md5']} ({out['seconds']} s): {path.name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
