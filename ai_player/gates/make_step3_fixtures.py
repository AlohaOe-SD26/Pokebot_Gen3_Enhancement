"""TEST SIDE: build the two fixtures of build step 3's live proof (`gates/live_step3.py`), by PLAYING, with button
presses only (no memory write), in a throwaway emulator.

    py -3.12 ai_player/gates/make_step3_fixtures.py [--only house|route]

  house_2f_clockset.ss1   the player's room AFTER the wall clock is set: `clock_room.ss1` (the CLOCK arm's fixture,
                          md5 pinned below) played on by the AI's OWN clock skill (`hands_harness.py` play, brain
                          `clock`, seed 3, the time pinned 13:37: the step-2 CLOCK skill, unchanged), which ends when
                          Mom has come up, spoken and left (`VAR_LITTLEROOT_INTRO_STATE` 6, `FLAG_SET_WALL_CLOCK` set).
                          WHY: with the clock NOT set, going downstairs runs `..._EventScript_GoUpstairsToSetClock`
                          (`data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc`, VAR_LITTLEROOT_INTRO_STATE 5): Mom
                          sends the player back upstairs. That is the STUCK arm (from `clock_room.ss1` itself); the
                          HOUSE and BUMP arms need the house open.
  route101_south.ss1      the south end of Route 101 with the AI's own memory of how it got there: `pokedex_done.ss1`
  route101_south.world.jsonl   (Birch's lab after the Pokedex, md5 pinned below) played on by the AI's OWN step-3
                          navigator (brain `explore`, goal ROUTE101, personality Story, seed 3: the TOWN arm's run), out of
                          the lab, through Littleroot (Mom's Running Shoes scene on the way) and over the north edge onto
                          Route 101; the memory it wrote (`world.jsonl`) is kept beside the state, so the ROUTE arm starts
                          knowing what this walk saw (`AI_PLAYER_WORLD`: knowledge grows over a playthrough), and the ROAM
                          arm starts from the same state knowing nothing.
  route101_xp.ss1         (the step-3 verifier's second round: "no live run has yet shown an intent's novelty clock reset
  route101_xp.world.jsonl  by an XP gain") a WILD BATTLE WON BUT NOT YET PAID: the foe's HP just reached 0, the party's
                          experience not yet given. Two stages, in one throwaway emulator:
                          1. the AI's OWN hands (`hands_harness.py` play: brain `goto`, errands (7,15) (5,15) (6,15), Story,
                             seed 3) from `route101_south.ss1` (md5 pinned below): it walks onto those tiles and so SEES the
                             15 x 11 windows around them; its memory (`world.jsonl`) is kept beside the state, so the XP arm
                             starts knowing every tile it will see there (a new tile would be novelty too, and would hide
                             which novelty moved the clock);
                          2. TEST-SIDE BUTTON PRESSES (no memory write), as `make_defeat_text_fixture.py` does: from (6,15),
                             Left onto the tall grass (5,15) and Right back, until a wild battle begins (bounded); then
                             FIGHT with the first move (the action and move cursors read only to choose a press; A on a text
                             that shows its arrow, A after a stall). The FIRST battle is fought to its end and not saved:
                             the Mudkip stands 1 point short of level 9 (418 of 419), and a level-up's stats box is a
                             screen the AI's eyes do not read as a wait yet (build step 4: the battle decider; measured,
                             the AI watched it 900 frames and gave up, as its stall detector should). In the SECOND
                             battle the state is saved on the FIRST frame the foe's HP (`gBattleMons[1].hp`,
                             `include/pokemon.h` struct BattlePokemon @0x28) is 0, the party's experience checked
                             unchanged since that battle began. AFTER the save the same presses go on to the end of the
                             battle, to print what the AI will meet (the experience given, NO level gained (checked), back
                             on the map).
  littleroot_twin.ss1     (build step 3.1, the step-3 review's finding 3: "a repeating scene") Littleroot Town just after the
                          player's first time out of the house: `house_2f_clockset.ss1` (md5 pinned below) played on by the
                          AI's OWN navigator (brain `explore`, goal LITTLEROOT_TOWN, Story, seed 3: the HOUSE arm's run, on
                          the code of step 3.1), saved where it ends. VAR_LITTLEROOT_TOWN_STATE is 0 (the rival not met:
                          checked), so the twin guards the road north (`data/maps/LittlerootTown/map.json` coord events
                          (10,1), (11,1): `LittlerootTown_EventScript_NeedPokemonTriggerLeft/Right`, every time the player
                          steps there: she walks up, "If you go in the grass, wild POKéMON will jump out!", pushes the
                          player one step back south, and walks back). The SCENE arm's errand past her repeats that scene.
Each is saved with a `.build.json` printout (what was played, the second-path truth of the end). A rebuild does not
reproduce the bytes (the emulator's real-time clock is in a state; measured on the step-2 fixtures): re-pin the md5s in
`live_step3.py` after one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import run, truth  # noqa: E402
from ai_player.gates.make_defeat_text_fixture import DOWN_ARROW_STATES, printer0  # noqa: E402
from ai_player.gates.probe_eyes import _symbol, _u32  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CLOCK_ROOM = (FIXTURES / "clock_room.ss1", "5d1d0ce0974470bf11040fc39f832041")
POKEDEX_DONE = (REPO / "tools" / "story-dev" / "saves" / "pokedex_done.ss1", "380fba7a4bf4afdf2fc9a0ad158de29e")
HOUSE = FIXTURES / "house_2f_clockset.ss1"
ROUTE = FIXTURES / "route101_south.ss1"
ROUTE_WORLD = FIXTURES / "route101_south.world.jsonl"
#: The XP fixture (module docstring): its source (pinned), the AI's errands, the two tiles of the test-side walk.
ROUTE_PINNED = (ROUTE, "81bf318a1532c5364f60064530f9984b")
XP = FIXTURES / "route101_xp.ss1"
XP_WORLD = FIXTURES / "route101_xp.world.jsonl"
XP_ERRANDS = "7,15;5,15;6,15"
XP_FLOOR, XP_GRASS = (6, 15), (5, 15)
#: Bounds of the test-side stage: steps walked to meet a battle, frames of the fight, frames after the save.
WALK_STEPS_MAX, FIGHT_FRAMES_MAX, AFTER_FRAMES_MAX = 300, 20_000, 20_000
STEP_HOLD, STEP_SETTLE = 40, 24  # hold a direction until the tile changes (at most); then let the step end
PRESS_GAP, STALL_FRAMES = 8, 120  # as `make_defeat_text_fixture.py`
#: `include/pokemon.h` struct BattlePokemon (0x58 bytes): species @0, hp @0x28, level @0x2A; battler 1 = the foe.
BATTLE_MON_SIZE, BATTLE_MON_HP, BATTLE_MON_LEVEL = 0x58, 0x28, 0x2A
BATTLE_STATES = ("BATTLE", "BATTLE_STARTING")
#: (build step 3.1) the SCENE arm's fixture (module docstring), its source pinned, and the variable that keeps the twin
#: on guard (`include/constants/vars.h` VAR_LITTLEROOT_TOWN_STATE 0x4050; save block 1 vars[] @0x139C from 0x4000).
TWIN = FIXTURES / "littleroot_twin.ss1"
HOUSE_PINNED = (HOUSE, "2cc0b61450870d34646f7583bfd0c787")
VAR_LITTLEROOT_TOWN_STATE = 0x4050


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def check(source: tuple[Path, str]) -> None:
    if md5(source[0]) != source[1]:
        raise SystemExit(f"{source[0]} has md5 {md5(source[0])}, pinned {source[1]}")


def build_house() -> dict:
    check(CLOCK_ROOM)
    result = run("clock", CLOCK_ROOM[0], 3, 10000, None, None, "13:37", Path(tempfile.mkdtemp(prefix="ai_step3_fix_")), HOUSE)
    truth = result["truth"]
    ok = (result["reason"] == "clock: clock set to 13:37" and truth["VAR_LITTLEROOT_INTRO_STATE"] == 6
          and truth["FLAG_SET_WALL_CLOCK"] is True and truth["map"] == [1, 1])
    out = {"fixture": str(HOUSE.relative_to(REPO)), "from": str(CLOCK_ROOM[0].relative_to(REPO)), "from_md5": CLOCK_ROOM[1],
           "played": "the AI's own clock skill (hands_harness run: brain clock, seed 3, clock 13:37)",
           "reason": result["reason"], "frames": result["frames"], "presses": result["presses"],
           "truth": truth, "md5": md5(HOUSE), "ok": ok}
    (FIXTURES / "house_2f_clockset.build.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def build_route() -> dict:
    check(POKEDEX_DONE)
    run_dir = Path(tempfile.mkdtemp(prefix="ai_step3_fix_"))
    result = run("explore", POKEDEX_DONE[0], 3, 20000, None, None, None, run_dir, ROUTE, "Story", None,
                 {"goal_map": "ROUTE101"})
    shutil.copyfile(run_dir / "world.jsonl", ROUTE_WORLD)
    truth = result["truth"]
    ok = result["reason"].startswith("explore: done") and truth["map"] == [0, 16]
    out = {"fixture": str(ROUTE.relative_to(REPO)), "world": str(ROUTE_WORLD.relative_to(REPO)),
           "from": str(POKEDEX_DONE[0].relative_to(REPO)), "from_md5": POKEDEX_DONE[1],
           "played": "the AI's own step-3 navigator (hands_harness run: brain explore, goal ROUTE101, Story, seed 3)",
           "reason": result["reason"], "frames": result["frames"], "presses": result["presses"],
           "lines": [line for line in result["lines"] if line.startswith("[AI-WORLD]")],
           "truth": truth, "md5": md5(ROUTE), "world_md5": md5(ROUTE_WORLD), "ok": ok}
    (FIXTURES / "route101_south.build.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def build_xp() -> dict:
    """The XP fixture (module docstring): stage 1 the AI's own errands, stage 2 test-side presses to a won battle."""
    check(ROUTE_PINNED)
    run_dir = Path(tempfile.mkdtemp(prefix="ai_step3_fix_"))
    stage1 = run("goto", ROUTE, 3, 6000, None, None, None, run_dir, None, "Story", None, {"goto": XP_ERRANDS})
    if not str(stage1["reason"]).startswith("goto: done") or stage1["truth"]["pos"] != list(XP_FLOOR):
        raise SystemExit(f"stage 1 (the AI's errands) did not end on {XP_FLOOR}: {stage1['reason']} at {stage1['truth'].get('pos')}")
    shutil.copyfile(run_dir / "world.jsonl", XP_WORLD)

    from modules.context import context
    from modules.memory import get_game_state, read_symbol
    from modules.pokemon_party import get_party

    emulator = context.emulator

    def tile() -> tuple[int, int]:
        sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
        pos = bytes(emulator.read_bytes(sb1, 4))
        return int.from_bytes(pos[0:2], "little", signed=True), int.from_bytes(pos[2:4], "little", signed=True)

    def state() -> str:
        return get_game_state().name

    def foe() -> dict:
        raw = bytes(read_symbol("gBattleMons", BATTLE_MON_SIZE, BATTLE_MON_SIZE))
        return {"species": int.from_bytes(raw[0:2], "little"), "hp": int.from_bytes(raw[BATTLE_MON_HP:BATTLE_MON_HP + 2], "little"),
                "level": raw[BATTLE_MON_LEVEL]}

    def experience() -> dict[str, list]:
        return {f"{m.personality_value:08x}": [m.species.name, m.total_exp, m.level] for m in get_party()}

    walk: list[list] = []
    presses: list[list] = []

    def walk_to_a_battle() -> None:
        """Stage 2a: Left onto the grass and Right back, until a wild battle begins (bounded)."""
        for _ in range(WALK_STEPS_MAX):
            here = tile()
            if here not in (XP_FLOOR, XP_GRASS):
                raise SystemExit(f"the test-side walk left its two tiles: {here}")
            button, want = ("Left", XP_GRASS) if here == XP_FLOOR else ("Right", XP_FLOOR)
            walk.append([emulator.get_frame_count(), button])
            emulator.hold_button(button)
            try:
                for _ in range(STEP_HOLD):
                    emulator.run_single_frame()
                    if tile() == want or state() in BATTLE_STATES:
                        break
            finally:
                emulator.release_button(button)
            for _ in range(STEP_SETTLE):
                if state() in BATTLE_STATES:
                    break
                emulator.run_single_frame()
            if state() in BATTLE_STATES:
                return
        raise SystemExit(f"no wild battle in {WALK_STEPS_MAX} steps")

    def fight(save: bool) -> tuple[dict | None, bool]:
        """Stage 2b: FIGHT with the first move until the foe's HP is 0 (`save`: the fixture is saved there), then on to
        the end of the battle. Returns (what was saved, back on the map)."""
        saved = None
        seen_alive = zero = False
        on_map = 0  # after the foe's HP reached 0: frames in a row back on the map (the battle is over)
        start = experience()
        last_press, last_change, previous = -PRESS_GAP, 0, None
        for step in range(FIGHT_FRAMES_MAX + AFTER_FRAMES_MAX):
            now_state = state()
            if not zero:
                if now_state == "BATTLE" and foe()["hp"] > 0:
                    seen_alive = True
                if seen_alive and now_state == "BATTLE" and foe()["hp"] == 0:
                    zero = True
                    if experience() != start:
                        raise SystemExit(f"the experience changed before the foe's HP reached 0: {start} -> {experience()}")
                    if save:
                        XP.write_bytes(emulator.get_save_state())
                        saved = {"frame": emulator.get_frame_count(), "foe": foe(), "experience": experience(), "md5": md5(XP),
                                 "truth": truth(context)}
                elif step >= FIGHT_FRAMES_MAX or now_state == "OVERWORLD":
                    raise SystemExit(f"the foe's HP never reached 0 (step {step}, state {now_state}, foe {foe()})")
            else:
                on_map = on_map + 1 if now_state == "OVERWORLD" else 0
                if on_map >= 120:
                    return saved, True
            char, active, printer_state = printer0(read_symbol)
            controller = _symbol(_u32(read_symbol("gBattlerControllerFuncs", 0, 4), 0) - 1) or "?"
            key = (char, active, printer_state, controller, now_state)
            if key != previous:
                previous, last_change = key, step
            button = None
            if now_state == "BATTLE" and step - last_press >= PRESS_GAP:
                if controller == "HandleInputChooseAction":
                    cursor = read_symbol("gActionSelectionCursor", 0, 1)[0]
                    button = "A" if cursor == 0 else ("Up" if cursor & 2 else "Left")
                elif controller == "HandleInputChooseMove":
                    cursor = read_symbol("gMoveSelectionCursor", 0, 1)[0]
                    button = "A" if cursor == 0 else ("Up" if cursor & 2 else "Left")
                elif active and printer_state in DOWN_ARROW_STATES:
                    button = "A"
                elif step - last_change >= STALL_FRAMES:
                    button = "A"
            if button is not None:
                emulator.press_button(button)
                presses.append([emulator.get_frame_count(), button, controller,
                                ("after the save" if saved else "before the save") if save else "the first battle"])
                last_press = step
            emulator.run_single_frame()
        return saved, False

    # The FIRST battle is fought to its end and NOT saved: measured 2026-10-08, the party's Mudkip stands 1 point short
    # of level 9 (418 of 419), so the first win levels it up, and the level-up's stats box is a screen the AI's eyes do
    # not yet read as a wait (the AI watched it 900 frames and gave up, correctly: `hands/dialogue.py` stall detector).
    # Reading it is the battle decider's (build step 4). The SECOND battle gives experience and no level (asserted).
    walk_to_a_battle()
    first_battle = {"began_on": list(tile()), "experience_at_start": experience()}
    _, back = fight(save=False)
    if not back:
        raise SystemExit("the first battle did not end")
    first_battle["experience_after"] = experience()
    walk_to_a_battle()
    battle_tile, battle_frame = tile(), emulator.get_frame_count()
    exp_at_start = experience()
    saved, back = fight(save=True)
    if saved is None:
        raise SystemExit("no save was made")
    on_map = 120 if back else 0
    after = experience()
    end = truth(context)
    gained = {pid: [exp_at_start[pid][1], after[pid][1]] for pid in after if pid in exp_at_start and after[pid][1] != exp_at_start[pid][1]}
    levels = {pid: [exp_at_start[pid][2], after[pid][2]] for pid in after if pid in exp_at_start}
    ok = (saved is not None and bool(gained) and stage1["truth"]["map"] == [0, 16] and battle_tile in (XP_FLOOR, XP_GRASS)
          and end["map"] == [0, 16] and on_map >= 120 and all(a == b for a, b in levels.values()))
    out = {"fixture": str(XP.relative_to(REPO)), "world": str(XP_WORLD.relative_to(REPO)),
           "from": str(ROUTE.relative_to(REPO)), "from_md5": ROUTE_PINNED[1],
           "played": (f"stage 1: the AI's own hands (hands_harness run: brain goto, errands {XP_ERRANDS}, Story, seed 3); stage 2: "
                      f"test-side presses (Left/Right between {XP_FLOOR} and {XP_GRASS} until a wild battle; FIGHT, the first move; "
                      f"A on an arrow or a stall), saved on the first frame the foe's HP was 0"),
           "stage1_reason": stage1["reason"], "stage1_frames": stage1["frames"], "stage1_presses": stage1["presses"],
           "stage1_lines": [line for line in stage1["lines"] if line.startswith("[AI-WORLD]")],
           "walk": walk, "first_battle_not_saved": first_battle,
           "battle_began_on": list(battle_tile), "battle_began_at_frame": battle_frame,
           "experience_at_battle_start": exp_at_start, "saved": {k: v for k, v in saved.items() if k != "truth"},
           "truth_of_the_save": saved["truth"], "presses": presses,
           "after_the_save_played_on": {"experience": after, "gained": gained, "levels": levels, "back_on_the_map": on_map >= 120,
                                        "truth": end},
           "md5": md5(XP), "world_md5": md5(XP_WORLD), "ok": ok}
    (FIXTURES / "route101_xp.build.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def littleroot_town_state() -> int:
    """VAR_LITTLEROOT_TOWN_STATE from save block 1 of the emulator as it stands (test side, read only)."""
    from modules.context import context
    from modules.memory import read_symbol

    from ai_player.gates.hands_harness import SB1_VARS, VARS_START

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    return int.from_bytes(bytes(context.emulator.read_bytes(sb1 + SB1_VARS + 2 * (VAR_LITTLEROOT_TOWN_STATE - VARS_START), 2)),
                          "little")


def build_twin() -> dict:
    """The SCENE arm's fixture (module docstring): the AI's own walk out of the house, saved where it ends."""
    check(HOUSE_PINNED)
    run_dir = Path(tempfile.mkdtemp(prefix="ai_step3_fix_"))
    result = run("explore", HOUSE, 3, 12000, None, None, None, run_dir, TWIN, "Story", None, {"goal_map": "LITTLEROOT_TOWN"})
    truth = result["truth"]
    state = littleroot_town_state()
    ok = (result["reason"].startswith("explore: done") and truth["map"] == [0, 9] and truth["VAR_LITTLEROOT_INTRO_STATE"] == 7
          and state == 0)
    out = {"fixture": str(TWIN.relative_to(REPO)), "from": str(HOUSE.relative_to(REPO)), "from_md5": HOUSE_PINNED[1],
           "played": "the AI's own step-3.1 navigator (hands_harness run: brain explore, goal LITTLEROOT_TOWN, Story, seed 3)",
           "reason": result["reason"], "frames": result["frames"], "presses": result["presses"],
           "lines": [line for line in result["lines"] if line.startswith("[AI-WORLD]")],
           "VAR_LITTLEROOT_TOWN_STATE": state, "truth": truth, "md5": md5(TWIN), "ok": ok}
    (FIXTURES / "littleroot_twin.build.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=("house", "route", "xp", "twin"))
    args = parser.parse_args()
    results = []
    if args.only in (None, "house"):
        results.append(build_house())
    if args.only in (None, "route"):
        results.append(build_route())
    if args.only in (None, "xp"):
        results.append(build_xp())
    if args.only in (None, "twin"):
        results.append(build_twin())
    for result in results:
        brief = {k: v for k, v in result.items() if k not in ("truth", "lines", "stage1_lines", "walk", "presses", "truth_of_the_save")}
        print("FIXTURE " + json.dumps(brief, ensure_ascii=False))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
