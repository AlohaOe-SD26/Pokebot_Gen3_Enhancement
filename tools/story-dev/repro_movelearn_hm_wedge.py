"""REPRO for #24-movelearn-recovery -- the move-learn wedge that killed 2 of the 5
night5 cold-start runs (2026-07-25).

THIS IS A REAL CAPTURE, NOT A FAULT INJECTION. Both save states below are the actual
emulator state at the moment the run died, lifted out of the run profiles before the
next batch could overwrite them:

  saves/movelearn_hmwedge_quickattack.ss1  <- night5 run5 (profiles/n5-5), f1557569
      COMBUSKEN L32: Scratch, Rock Smash(HM06), Double Kick, Ember -- offered QUICK ATTACK
  saves/movelearn_hmwedge_slash.ss1        <- night5 run2 (profiles/n5-2), f1563956
      COMBUSKEN L39: Scratch, Peck, Double Kick, Rock Smash(HM06)  -- offered SLASH

THE BUG (read off the night5 frame logs, four distinct defects):
  D1  `new_move: cancel` => which_move_should_be_replaced() returns 4 ("decline"), but
      once the move-select screen is open branch (1) treats 4 as a SLOT INDEX and presses
      Down forever chasing a slot that does not exist. 4 means "back out", not "row 4".
  D2  Branch (5) blindly presses A on any unrecognised move-learn text. The state reads
      ml=Unknown during "<MON> is trying to learn <MOVE>.", so that stray A answers YES to
      the very prompt the bot decided to decline -- which is what opens the screen at all.
  D3  Task_HandleInputCantForgetHMsMoves (the "HM moves can't be forgotten!" window) is
      not recognised anywhere; get_learn_move_state() misreports it as AskWhetherToLearn,
      so the bot answers a Yes/No that is not on screen.
  D4  The 3-strike valve raises BotModeError from inside the battle listener, which sits
      OUTSIDE StoryMode's derail-recovery try/except -- so the whole run dies.

Observable signature of the wedge: an 8-frame ping-pong, 5 frames AskWhetherToLearn
(branch 2 presses B, closing the screen) alternating with 3 frames SelectMoveToReplace
(branch 1 presses Down). A opens it, B closes it, forever.

PASS/FAIL for this repro:
  BEFORE the fix -- the dialogue never resolves; handle_move_replacement_dialogue is
      re-invoked until the valve raises BotModeError. Verdict: WEDGED.
  AFTER  the fix -- the dialogue resolves (declined, moveset unchanged) within a few
      hundred frames and the battle carries on. Verdict: RESOLVED.

Run both arms:
  py -3.12 tools/story-dev/repro_movelearn_hm_wedge.py --state quickattack
  py -3.12 tools/story-dev/repro_movelearn_hm_wedge.py --state slash
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ap = argparse.ArgumentParser()
ap.add_argument("--state", default="quickattack", choices=["quickattack", "slash"])
ap.add_argument("--frames", type=int, default=30000)
ap.add_argument("--build", default="sandbox", choices=["custom", "sandbox"])
ap.add_argument("--profile", default="repro-movelearn-hm")
ap.add_argument("--log", default=None)
args = ap.parse_args()

_REPO = Path(__file__).resolve().parents[2]
BUILD = _REPO / f"{args.build}-pokebot"
sys.path.insert(0, str(BUILD))
SCRATCH = Path(__file__).parent
SAVES = SCRATCH / "saves"
LOG = Path(args.log) if args.log else SCRATCH / f"repro_movelearn_hm_wedge_{args.state}.log"

state_path = SAVES / f"movelearn_hmwedge_{args.state}.ss1"
assert state_path.is_file(), f"missing {state_path}"

logf = open(LOG, "w", encoding="utf-8")


def log(msg):
    logf.write(msg + "\n")
    logf.flush()
    print(msg)


from modules.context import context
from modules.profiles import create_profile, profile_directory_exists, load_profile_by_name
from modules.roms import list_available_roms
from modules.game import set_rom

if not profile_directory_exists(args.profile):
    roms = list_available_roms()
    assert roms, "no ROMs found in roms/"
    create_profile(args.profile, roms[0])
    log(f"[setup] created profile {args.profile}")

profile = load_profile_by_name(args.profile)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.debug = False
context.bot_mode = "Story"

context.emulator.load_save_state(state_path.read_bytes())

from modules.memory import get_game_state
from modules.modes import BotModeError, get_bot_listeners
from modules.plugins import load_plugins, load_built_in_plugins, plugin_profile_loaded
from modules.stats import StatsDatabase
from modules.battle_state import battle_is_active, get_current_battle_script_instruction
from modules.pokemon_party import get_party
from modules.tasks import get_tasks
import modules.battle_move_replacing as bmr
from modules.battle_handler import handle_battle

load_plugins()
load_built_in_plugins()
plugin_profile_loaded(context.profile)
context.stats = StatsDatabase(context.profile)
context.bot_listeners = get_bot_listeners(context.rom)

log(f"[setup] loaded {state_path.name} (build={args.build})")
log(f"[setup] battle.new_move config = {context.config.battle.new_move!r}")
log(f"[setup] game_state={get_game_state()} battle_is_active={battle_is_active()}")
for i, mon in enumerate(get_party()):
    moves = ", ".join(
        f"{s.move.name}"
        + ("[HM]" if s.move.tm_hm is not None and s.move.tm_hm.name.startswith("HM") else "")
        for s in mon.moves
        if s is not None
    )
    log(f"[setup] party[{i}] {mon.species.name} L{mon.level}: {moves}")

# The captured state is mid-battle on the move-select screen, so the BattleListener
# will not re-detect a battle start (POKEMON_SUMMARY_SCREEN is not one of its
# battle_states). Drive handle_battle directly -- that reproduces the exact generator
# stack the night5 logs recorded:
#     BattleListener.fight -> handle_battle -> handle_move_replacement_dialogue
from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

strategy = LevelUpTravelBattleStrategy()
log(f"[setup] strategy = {type(strategy).__name__}")

# --- instrumentation: count invocations + record every button pressed --------------
_orig_hmrd = bmr.handle_move_replacement_dialogue
_invocations = {"n": 0}
_cur = {"f": 0}


def _counted_hmrd(strategy):
    _invocations["n"] += 1
    log(f"f{_cur['f']}: >>> handle_move_replacement_dialogue ENTER (invocation #{_invocations['n']})")
    yield from _orig_hmrd(strategy)
    log(f"f{_cur['f']}: <<< handle_move_replacement_dialogue EXIT (invocation #{_invocations['n']})")


import modules.battle_handler as battle_handler_mod

battle_handler_mod.handle_move_replacement_dialogue = _counted_hmrd

_buttons = Counter()
_orig_press = context.emulator.press_button


def _recording_press(button):
    _buttons[button] += 1
    return _orig_press(button)


context.emulator.press_button = _recording_press


def _moveset_sig():
    try:
        return "|".join(
            ",".join(s.move.name for s in mon.moves if s is not None) for mon in get_party()
        )
    except Exception:
        return "<unreadable>"


def _tasks():
    tl = get_tasks()
    return [t.symbol for t in tl] if tl is not None else []


moveset_before = _moveset_sig()
log(f"[setup] moveset signature BEFORE = {moveset_before}")

stack = [handle_battle(strategy)]
verdict = "UNKNOWN"
detail = ""
last_state = None
transitions = 0
resolved_at = None

log(f"[run] driving handle_battle for up to {args.frames} frames")

for step in range(args.frames):
    _cur["f"] = step
    try:
        st = bmr.get_learn_move_state()
    except Exception:
        st = None
    if st != last_state:
        transitions += 1
        if transitions <= 40 or transitions % 200 == 0:
            log(
                f"f{step}: ml {last_state} -> {st}  tasks={_tasks()} "
                f"state={get_game_state()} instr={get_current_battle_script_instruction()}"
            )
        last_state = st

    # RESOLVED = the move-learn dialogue is gone and no move-learn text remains.
    if (
        st == bmr.LearnMoveState.DialogueNotActive
        and not bmr.move_learn_text_showing()
        and step > 60
    ):
        resolved_at = step
        verdict = "RESOLVED"
        detail = f"move-learn dialogue closed at f{step}"
        break

    try:
        next(stack[-1])
    except StopIteration:
        stack.pop()
        if not stack:
            resolved_at = step
            verdict = "RESOLVED"
            detail = f"handle_battle returned at f{step}"
            break
    except BotModeError as e:
        verdict = "WEDGED"
        detail = f"BotModeError at f{step}: {e}"
        log(f"f{step}: *** BotModeError: {e}")
        break
    except Exception as e:
        import traceback

        verdict = "ERROR"
        detail = f"{type(e).__name__} at f{step}: {e}"
        log(f"f{step}: *** EXCEPTION\n{traceback.format_exc()}")
        break

    context.emulator.run_single_frame()
else:
    verdict = "WEDGED"
    detail = f"still not resolved after {args.frames} frames (frame budget exhausted)"

moveset_after = _moveset_sig()

log("")
log("=" * 78)
log(f"[result] VERDICT = {verdict}")
log(f"[result] {detail}")
log(f"[result] handle_move_replacement_dialogue invocations = {_invocations['n']}")
log(f"[result] ml-state transitions = {transitions}")
log(f"[result] buttons pressed = {dict(_buttons)}")
log(f"[result] moveset BEFORE = {moveset_before}")
log(f"[result] moveset AFTER  = {moveset_after}")
log(f"[result] moveset changed = {moveset_before != moveset_after}")
log("=" * 78)
logf.close()

sys.exit(0 if verdict == "RESOLVED" else 1)
