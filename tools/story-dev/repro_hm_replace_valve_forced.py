"""VERIFICATION probe for the _STALLED_EXITS re-entry-proof safety valve added to
`handle_move_replacement_dialogue` (sandbox-pokebot/modules/battle_move_replacing.py,
2026-07-24). This is a SIMULATED fault, clearly labelled: it is not something the real
game can currently produce (the HM veto below always resolves cleanly in ~430 frames),
but the valve exists precisely for a hypothetical "offer we truly cannot resolve"
(e.g. a future bug, or an edge case nobody has found yet). We must prove the valve
itself works -- 3 stalled invocations -> BotModeError -- without waiting for a real
occurrence.

FAULT INJECTED (clearly marked below): once the real game genuinely enters
LearnMoveState.AskWhetherToLearn for the first time, we LATCH get_learn_move_state()
to always report AskWhetherToLearn forever after, regardless of what the game is
actually doing. Combined with --force-slot 2 (HM veto -> decline every time), this
makes the code repeatedly press B into a dialogue that (as far as it can tell) never
closes -- exactly the "genuinely cannot be resolved" case the valve guards against.

Expected: 3 invocations of handle_move_replacement_dialogue, each timing out at
frames_in_dialogue>6000 (+600 escape presses), the 3rd one raising BotModeError from
inside battle_move_replacing.py, caught by this harness's driver loop.

Run:  py -3.12 tools/story-dev/repro_hm_replace_valve_forced.py --build sandbox
"""

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ap = argparse.ArgumentParser()
# 35,000, not 25,000 (raised 2026-07-25, #24-movelearn-recovery). The valve needs
# 3 x (6000 dialogue + 1800 escape) ITERATIONS, and an iteration is not one emulator
# frame -- some branches yield several. After the summary-screen wait was bounded
# (it now presses B and yields 3x instead of pressing nothing and yielding once) the
# third strike lands at f27583, just past the old budget, so this repro stopped at
# _STALLED_EXITS=2 and looked like a regression when nothing had changed. Give the
# budget real headroom rather than tuning it to the current frame cost.
ap.add_argument("--frames", type=int, default=35000)
ap.add_argument("--build", default="sandbox", choices=["custom", "sandbox"])
ap.add_argument("--profile", default="repro-hm-valve")
ap.add_argument("--log", default=None)
args = ap.parse_args()

_REPO = Path(__file__).resolve().parents[2]
BUILD = _REPO / f"{args.build}-pokebot"
sys.path.insert(0, str(BUILD))
SCRATCH = Path(__file__).parent
SAVES = SCRATCH / "saves"
LOG = Path(args.log) if args.log else SCRATCH / f"repro_hm_valve_{args.build}.log"

state_path = SAVES / "route116team.ss1"
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
log(f"[setup] loaded save state {state_path.name}; build={args.build}")

from modules.memory import get_game_state, GameState
from modules.modes import FrameInfo, get_bot_listeners, get_bot_mode_by_name, BotModeError, BotMode
from modules.plugins import load_plugins, load_built_in_plugins, plugin_profile_loaded
from modules.state_cache import state_cache
from modules.stats import StatsDatabase
from modules.tasks import get_global_script_context, get_tasks
from modules.battle_state import battle_is_active, get_current_battle_script_instruction
from modules.pokemon_party import get_party
from modules.memory import set_event_flag

load_plugins()
load_built_in_plugins()
plugin_profile_loaded(context.profile)
context.stats = StatsDatabase(context.profile)
context.bot_listeners = get_bot_listeners(context.rom)
assert get_bot_mode_by_name("Story") is not None, "Story mode did not register"

set_event_flag("BADGE01_GET", True)

from modules.debug_utilities import debug_create_pokemon, debug_write_party
from modules.pokemon import get_species_by_name, get_move_by_name, LearnedMove

marshtomp_species = get_species_by_name("Marshtomp")
exp31 = marshtomp_species.level_up_type.get_experience_needed_for_level(31)
marshtomp_moves = [
    LearnedMove.create(get_move_by_name("Water Gun")),
    LearnedMove.create(get_move_by_name("Mud Shot")),
    LearnedMove.create(get_move_by_name("Rock Smash")),  # HM06
    LearnedMove.create(get_move_by_name("Bide")),
]
marshtomp = debug_create_pokemon(
    species=marshtomp_species, level=30, experience=exp31 - 1, moves=marshtomp_moves,
    nickname="MARSHTOMP", current_hp=None,
)
linoone = debug_create_pokemon(species=get_species_by_name("Linoone"), level=26,
                                moves=[LearnedMove.create(get_move_by_name("Tackle"))], nickname="LINOONE")
shroomish = debug_create_pokemon(species=get_species_by_name("Shroomish"), level=21,
                                  moves=[LearnedMove.create(get_move_by_name("Tackle"))], nickname="SHROOMISH")
loudred = debug_create_pokemon(species=get_species_by_name("Loudred"), level=21,
                                moves=[LearnedMove.create(get_move_by_name("Tackle"))], nickname="LOUDRED")
debug_write_party([marshtomp, linoone, shroomish, loudred])
log("[inject] party = Marshtomp:L30 (1 exp short of L31) moves=WaterGun/MudShot/RockSmash(HM06)/Bide, "
    "Linoone:L26, Shroomish:L21, Loudred:L21")

import plugins.custom_modes.story_mode as story_mode_mod
from plugins.custom_modes.story_mode import StoryMode, LevelUpTravelBattleStrategy
from modules.battle_strategies.default import DefaultBattleStrategy
import modules.battle_move_replacing as bmr
import modules.battle_handler as battle_handler_mod

_cur_frame = {"f": 0}

# ---- FAULT INJECTION #1: force which_move_should_be_replaced -> HM slot 2 --------
_orig_levelup_which = LevelUpTravelBattleStrategy.which_move_should_be_replaced
_orig_default_which = DefaultBattleStrategy.which_move_should_be_replaced


def _make_forced_which(orig, tag):
    def wrapped(self, pokemon, new_move):
        real = orig(self, pokemon, new_move)
        log(f"f{_cur_frame['f']}: [{tag}] real verdict={real}; [FAULT] forcing -> 2 (HM slot, Rock Smash)")
        return 2

    return wrapped


LevelUpTravelBattleStrategy.which_move_should_be_replaced = _make_forced_which(_orig_levelup_which, "LevelUpTravelBattleStrategy")
DefaultBattleStrategy.which_move_should_be_replaced = _make_forced_which(_orig_default_which, "DefaultBattleStrategy")

# ---- FAULT INJECTION #2: latch get_learn_move_state() to AskWhetherToLearn -------
# forever, once it is genuinely seen for the first time. SIMULATES an offer the game
# will truly never let us close (nothing like this exists today -- the HM veto always
# resolves cleanly, as proven by the OTHER arms of this verification). This isolates
# the valve's OWN correctness from whether such a game state can currently occur.
_orig_get_learn_state = bmr.get_learn_move_state
_latch = {"active": False}
_last_state = {"v": None}


def _latched_get_learn_state():
    real = _orig_get_learn_state()
    if real == bmr.LearnMoveState.AskWhetherToLearn and not _latch["active"]:
        _latch["active"] = True
        log(f"f{_cur_frame['f']}: [FAULT] latch ENGAGED -- get_learn_move_state() will report "
            f"AskWhetherToLearn forever from here on, regardless of the real game state")
    result = bmr.LearnMoveState.AskWhetherToLearn if _latch["active"] else real
    if result != _last_state["v"]:
        log(f"f{_cur_frame['f']}: LearnMoveState (patched) {_last_state['v']} -> {result} (real={real})")
        _last_state["v"] = result
    return result


bmr.get_learn_move_state = _latched_get_learn_state

_orig_hmrd = battle_handler_mod.handle_move_replacement_dialogue
_hmrd_calls = {"n": 0}


def _wrapped_hmrd(strategy):
    _hmrd_calls["n"] += 1
    n = _hmrd_calls["n"]
    log(f"f{_cur_frame['f']}: >>> handle_move_replacement_dialogue ENTER (invocation #{n})")
    try:
        result = yield from _orig_hmrd(strategy)
        log(f"f{_cur_frame['f']}: <<< handle_move_replacement_dialogue EXIT (invocation #{n}, normal StopIteration)")
        return result
    except GeneratorExit:
        log(f"f{_cur_frame['f']}: <<< handle_move_replacement_dialogue EXIT (invocation #{n}, GeneratorExit)")
        raise


battle_handler_mod.handle_move_replacement_dialogue = _wrapped_hmrd
log(f"[setup] _STALLED_EXITS starts at {bmr._STALLED_EXITS}")


class HmValveMode(BotMode):
    @staticmethod
    def name():
        return "HmValve"

    def on_battle_started(self, encounter):
        shim = SimpleNamespace(_catch_team_target=4)
        shim._should_catch = lambda enc: StoryMode._should_catch(shim, enc)
        strategy = StoryMode.on_battle_started(shim, encounter)
        log(f"f{_cur_frame['f']}: on_battle_started -> LIVE STRATEGY = {type(strategy).__name__}")
        return strategy

    def run(self):
        seq = ["Up", "Up", "Down", "Down", "Left", "Left", "Right", "Right"]
        i = 0
        while True:
            context.emulator.press_button(seq[(i // 6) % len(seq)])
            yield
            i += 1


context.bot_mode_instance = None
context.controller_stack = []

previous_frame_info = None
prev_ctrl = None
no_progress = 0
last_sig = None
last_heartbeat = 0
bot_mode_error = None

log(f"[run] starting faithful loop for up to {args.frames} frames")

for step in range(args.frames):
    context.frame = step
    _cur_frame["f"] = step

    game_state = get_game_state()
    script_context = get_global_script_context()
    script_stack = script_context.stack if script_context is not None and script_context.is_active else []
    task_list = get_tasks()
    active_tasks = [t.symbol.lower() for t in task_list] if task_list is not None else []

    frame_info = FrameInfo(
        frame_count=context.emulator.get_frame_count(),
        game_state=game_state,
        active_tasks=active_tasks,
        script_stack=script_stack,
        controller_stack=[c.__qualname__ for c in context.controller_stack],
        previous_frame=previous_frame_info,
    )

    if previous_frame_info is not None and previous_frame_info.frame_count > frame_info.frame_count:
        state_cache.reset()
        context.bot_listeners = get_bot_listeners(context.rom)

    if context.bot_mode == "Manual":
        class _Manual:
            @staticmethod
            def name():
                return "Manual"

            def run(self):
                yield
        context.bot_mode_instance = _Manual()
    elif len(context.controller_stack) == 0:
        context.bot_mode_instance = HmValveMode()
        context.controller_stack.append(context.bot_mode_instance.run())

    ctrl = frame_info.controller_stack[-1] if frame_info.controller_stack else "<none>"
    if ctrl != prev_ctrl:
        log(f"f{step}: CONTROLLER -> {ctrl}   (state={game_state.name if hasattr(game_state,'name') else game_state})")
        prev_ctrl = ctrl

    ba = battle_is_active()

    try:
        for listener in context.bot_listeners.copy():
            listener.handle_frame(context.bot_mode_instance, frame_info)
        if context.bot_mode == "Manual":
            context.controller_stack = []
        if len(context.controller_stack) > 0:
            next(context.controller_stack[-1])
    except (StopIteration, GeneratorExit):
        if context.controller_stack:
            context.controller_stack.pop()
    except BotModeError as e:
        context.emulator.reset_held_buttons()
        context.message = str(e)
        bot_mode_error = str(e)
        log(f"f{step}: *** BotModeError -> Manual: {e}")
        context.set_manual_mode()
        break
    except Exception as e:
        import traceback

        log(f"f{step}: *** EXCEPTION: {e}\n{traceback.format_exc()}")
        context.set_manual_mode()
        break

    sig = (ctrl, game_state.name if hasattr(game_state, "name") else str(game_state),
           get_current_battle_script_instruction() if ba else "")
    if sig == last_sig:
        no_progress += 1
    else:
        no_progress = 0
        last_sig = sig

    if step - last_heartbeat >= 2000:
        last_heartbeat = step
        log(f"f{step}: heartbeat ctrl={ctrl} hmrd_invocations={_hmrd_calls['n']} _STALLED_EXITS={bmr._STALLED_EXITS}")

    context.emulator.get_inputs()
    context.emulator.run_single_frame()
    previous_frame_info = frame_info
    previous_frame_info.previous_frame = None

log(f"[done] ran {step + 1} frames; final mode={context.bot_mode}")
log(f"[done] handle_move_replacement_dialogue was invoked {_hmrd_calls['n']} time(s) total")
log(f"[done] BotModeError raised: {bot_mode_error!r}")
log(f"[done] final _STALLED_EXITS = {bmr._STALLED_EXITS} (expect 0 -- reset happens right before the raise)")
logf.close()
