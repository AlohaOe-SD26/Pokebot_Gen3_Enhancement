"""LIVE repro for the user-reported HM-move-replace infinite dialogue loop
(2026-07-24 bug report). Marshtomp:L31, Linoone:L26, Shroomish:L21, Loudred:L21,
Route 112, wild Koffing; Marshtomp leveled up and tried to learn a new move while
already knowing Rock Smash (HM06) -> the bot looped for ~8000 frames, never
escaping (user killed it manually). Observed transitions (from the report):

  cycle A:  Unknown -> AskWhetherToLearn -> SelectMoveToReplace -> AskWhetherToLearn -> ...
  cycle B:  Unknown -> AskWhetherToLearn -> Unknown -> ConfirmCancellation -> Unknown -> AskWhetherToLearn -> ...

THIS IS A LIVE run against the real emulator + unmodified production code (custom-pokebot
build) -- no reader mocking of game state. The ONLY things patched are OBSERVATION-ONLY
wrappers (they call straight through to the original and return its exact result
unchanged) so we can see, per frame:
  * which battle-strategy CLASS is actually live (on_battle_started's real routing,
    called through modules.story_mode.StoryMode.on_battle_started unbound -- the only
    stub is `_should_catch`, and even THAT calls the real
    StoryMode._should_catch(shim, encounter) so the catch/no-catch decision is genuine);
  * every call to `which_move_should_be_replaced` -- args (pokemon, new move), the
    is_hm() verdict for each of the 4 current move slots, and the return value;
  * every LearnMoveState transition (on change only) with the frame number;
  * every button `handle_move_replacement_dialogue` presses;
  * ENTRY/EXIT of `handle_move_replacement_dialogue` itself (battle_handler.py's call
    site), so a false-restart (the generator returning early and being re-invoked,
    which would silently reset its own 6000-frame safety-valve counter) is visible.

SETUP (state-writes, explicitly NOT "fixes" -- test scaffolding only, exactly the
technique story_harness.py's inject_treecko()/SailReconMode already use):
  * loads saves/route116team.ss1 (real wild grass, Route 116) and force-sets
    BADGE01_GET=True so `_should_catch` takes the SAME branch it would for the user's
    actual (post-badge-1, 4/4 party) run -- proven by calling the real function, not
    assumed;
  * debug_write_party() overwrites the party with a hand-built Marshtomp (lead, L30,
    exp = exp_for_31 - 1, moves = Water Gun / Mud Shot / Rock Smash(HM06) / Bide -- ALL
    FOUR slots damaging, none free, deliberately the hardest case for the HM guard) plus
    Linoone/Shroomish/Loudred at the reported levels (their exact moves don't matter --
    only Marshtomp levels up here). This mirrors the user's real party.

Run:  py -3.12 tools/story-dev/repro_hm_move_replace_loop.py [--frames N] [--build custom|sandbox]
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
ap.add_argument("--frames", type=int, default=20000)
ap.add_argument("--build", default="custom", choices=["custom", "sandbox"])
ap.add_argument("--profile", default="repro-hm-replace")
ap.add_argument("--log", default=None)
ap.add_argument(
    "--force-decline",
    action="store_true",
    help="FAULT INJECTION (H2 test): after which_move_should_be_replaced returns its "
    "real (logged) verdict, FORCE the return value to 4 (DECLINE) regardless -- tests "
    "whether the DECLINE/ConfirmCancellation dialogue path itself can loop, independent "
    "of the HM guard's own decision.",
)
ap.add_argument(
    "--force-slot",
    type=int,
    default=None,
    help="FAULT INJECTION: force which_move_should_be_replaced's return to this exact "
    "slot index regardless of its real verdict -- e.g. --force-slot 2 forces the code "
    "to try to replace the HM (Rock Smash) slot, simulating what happens if some future "
    "bug (or an as-yet-unfound edge case) ever causes the guard to pick the HM anyway. "
    "Tests the DOWNSTREAM handling of the game's refusal, independent of upstream cause.",
)
args = ap.parse_args()

_REPO = Path(__file__).resolve().parents[2]
BUILD = _REPO / f"{args.build}-pokebot"
sys.path.insert(0, str(BUILD))
SCRATCH = Path(__file__).parent
SAVES = SCRATCH / "saves"
LOG = Path(args.log) if args.log else SCRATCH / f"repro_hm_replace_{args.build}.log"

state_path = SAVES / "route116team.ss1"
assert state_path.is_file(), f"missing {state_path}"

logf = open(LOG, "w", encoding="utf-8")


def log(msg):
    logf.write(msg + "\n")
    logf.flush()
    print(msg)


# ---- bootstrap headless (mirrors story_harness.py) ----------------------------
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
log(f"[setup] battle.new_move config = {context.config.battle.new_move!r} (fork default is 'cancel')")

from modules.memory import get_game_state, GameState, read_symbol, unpack_uint16
from modules.modes import FrameInfo, get_bot_listeners, get_bot_mode_by_name, BotModeError, BotMode
from modules.plugins import load_plugins, load_built_in_plugins, plugin_profile_loaded
from modules.state_cache import state_cache
from modules.stats import StatsDatabase
from modules.tasks import get_global_script_context, get_tasks, task_is_active
from modules.battle_state import battle_is_active, get_current_battle_script_instruction, get_main_battle_callback
from modules.pokemon_party import get_party
from modules.game import decode_string
from modules.memory import get_event_flag, set_event_flag

load_plugins()
load_built_in_plugins()
plugin_profile_loaded(context.profile)
context.stats = StatsDatabase(context.profile)
context.bot_listeners = get_bot_listeners(context.rom)
assert get_bot_mode_by_name("Story") is not None, "Story mode did not register"

# ---- test scaffolding: force badge1 + inject the reported party ---------------
set_event_flag("BADGE01_GET", True)
log(f"[setup] STATE-WRITE: forced BADGE01_GET=True (matches the user's real post-gym-1 "
    f"party -- route116team.ss1 is otherwise pre-gym-1)")

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
linoone = debug_create_pokemon(
    species=get_species_by_name("Linoone"), level=26,
    moves=[LearnedMove.create(get_move_by_name("Tackle"))], nickname="LINOONE",
)
shroomish = debug_create_pokemon(
    species=get_species_by_name("Shroomish"), level=21,
    moves=[LearnedMove.create(get_move_by_name("Tackle"))], nickname="SHROOMISH",
)
loudred = debug_create_pokemon(
    species=get_species_by_name("Loudred"), level=21,
    moves=[LearnedMove.create(get_move_by_name("Tackle"))], nickname="LOUDRED",
)
debug_write_party([marshtomp, linoone, shroomish, loudred])
log(f"[inject] party = Marshtomp:L30 exp={exp31 - 1} (exp_for_31={exp31}) "
    f"moves=WaterGun/MudShot/RockSmash(HM06)/Bide, Linoone:L26, Shroomish:L21, Loudred:L21")
log("[inject] Marshtomp's 4 move slots are ALL damaging (none free/status) -- the "
    "hardest case for the HM guard: it must free a NON-HM slot even though every "
    "slot looks 'occupied'.")

# ---- OBSERVATION-ONLY instrumentation ------------------------------------------
import plugins.custom_modes.story_mode as story_mode_mod
from plugins.custom_modes.story_mode import StoryMode, LevelUpTravelBattleStrategy
from modules.battle_strategies.default import DefaultBattleStrategy
import modules.battle_move_replacing as bmr
import modules.battle_handler as battle_handler_mod

_cur_frame = {"f": 0}


def _wrap_which_move(cls, tag):
    orig = cls.which_move_should_be_replaced

    def wrapped(self, pokemon, new_move):
        result = orig(self, pokemon, new_move)
        if args.force_decline and result != 4:
            log(f"f{_cur_frame['f']}: [force-decline] overriding real verdict {result} -> 4 (DECLINE)")
            result = 4
        if args.force_slot is not None and result != args.force_slot:
            log(f"f{_cur_frame['f']}: [force-slot] overriding real verdict {result} -> {args.force_slot}")
            result = args.force_slot
        try:
            slots = []
            for i, lm in enumerate(pokemon.moves):
                if lm is None:
                    slots.append(f"{i}:<empty>")
                    continue
                m = lm.move
                is_hm = m.tm_hm is not None and m.tm_hm.name.startswith("HM")
                slots.append(f"{i}:{m.name}(tm_hm={m.tm_hm.name if m.tm_hm else None},is_hm={is_hm},bp={m.base_power})")
            log(f"f{_cur_frame['f']}: *** which_move_should_be_replaced[{tag}] "
                f"pokemon={pokemon.species.name} new_move={new_move.name}(bp={new_move.base_power}) "
                f"slots=[{', '.join(slots)}] -> RETURNED {result} "
                f"({'DECLINE' if result == 4 else f'replace slot {result}'}) ***")
        except Exception as e:
            log(f"f{_cur_frame['f']}: which_move_should_be_replaced[{tag}] logging error: {e}")
        return result

    cls.which_move_should_be_replaced = wrapped
    return orig


_orig_levelup_which = _wrap_which_move(LevelUpTravelBattleStrategy, "LevelUpTravelBattleStrategy")
_orig_default_which = _wrap_which_move(DefaultBattleStrategy, "DefaultBattleStrategy(stock)")

_orig_get_learn_state = bmr.get_learn_move_state
_last_ml_state = {"v": None}


def _wrapped_get_learn_state():
    s = _orig_get_learn_state()
    if s != _last_ml_state["v"]:
        log(f"f{_cur_frame['f']}: LearnMoveState {_last_ml_state['v']} -> {s}")
        _last_ml_state["v"] = s
    return s


bmr.get_learn_move_state = _wrapped_get_learn_state

_orig_hmrd = battle_handler_mod.handle_move_replacement_dialogue
_hmrd_calls = {"n": 0}


def _wrapped_hmrd(strategy):
    _hmrd_calls["n"] += 1
    n = _hmrd_calls["n"]
    log(f"f{_cur_frame['f']}: >>> handle_move_replacement_dialogue ENTER (invocation #{n}, strategy={type(strategy).__name__})")
    try:
        result = yield from _orig_hmrd(strategy)
        log(f"f{_cur_frame['f']}: <<< handle_move_replacement_dialogue EXIT (invocation #{n}, normal StopIteration)")
        return result
    except GeneratorExit:
        log(f"f{_cur_frame['f']}: <<< handle_move_replacement_dialogue EXIT (invocation #{n}, GeneratorExit)")
        raise


battle_handler_mod.handle_move_replacement_dialogue = _wrapped_hmrd

_orig_press = context.emulator.press_button
_button_log = {"active": False}


def _wrapped_press(button):
    if _button_log["active"]:
        log(f"f{_cur_frame['f']}:     press_button({button!r})")
    return _orig_press(button)


context.emulator.press_button = _wrapped_press


# ---- driver: real StoryMode.on_battle_started routing, spin for a wild --------
class HmReplLoopMode(BotMode):
    @staticmethod
    def name():
        return "HmReplLoop"

    def on_battle_started(self, encounter):
        shim = SimpleNamespace(_catch_team_target=4)
        shim._should_catch = lambda enc: StoryMode._should_catch(shim, enc)
        strategy = StoryMode.on_battle_started(shim, encounter)
        log(f"f{_cur_frame['f']}: on_battle_started -> LIVE STRATEGY = {type(strategy).__name__} "
            f"(_should_catch would have returned "
            f"{shim._should_catch(encounter) if encounter is not None else '<trainer>'})")
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

# ---- faithful main loop (mirrors modules/main.py / story_harness.py) ----------
previous_frame_info = None
prev_party = None
prev_ctrl = None
trace_active = False
no_progress = 0
last_sig = None
last_heartbeat = 0

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
        context.bot_mode_instance = HmReplLoopMode()
        context.controller_stack.append(context.bot_mode_instance.run())

    ctrl = frame_info.controller_stack[-1] if frame_info.controller_stack else "<none>"
    if ctrl != prev_ctrl:
        log(f"f{step}: CONTROLLER -> {ctrl}   (state={game_state.name if hasattr(game_state,'name') else game_state})")
        prev_ctrl = ctrl

    ba = battle_is_active()

    def _battle_text():
        try:
            return decode_string(read_symbol("gDisplayedStringBattle"))
        except Exception:
            return ""

    def _party_snapshot():
        try:
            return "|".join(f"{p.species.name}:L{p.level}:exp{p.total_exp}" for p in get_party())
        except Exception as e:
            return f"<err {e}>"

    ml = str(_wrapped_get_learn_state()).replace("LearnMoveState.", "") if ba else "n/a"
    ml_active = (ml not in ("DialogueNotActive", "n/a")) or any(
        ph in _battle_text() for ph in ("trying to learn", "make room for", "Delete a move", "wants to learn", "Stop")
    )
    _button_log["active"] = ml_active
    if ml_active and not trace_active:
        trace_active = True
        log(f"f{step}: === MOVE-LEARN WINDOW OPEN === party=[{_party_snapshot()}] bt={_battle_text()!r}")
    if trace_active and not ml_active:
        trace_active = False
        log(f"f{step}: === window closed === party=[{_party_snapshot()}]")

    ps = _party_snapshot()
    if ps != prev_party:
        if prev_party is not None:
            log(f"f{step}: PARTY CHANGE [{prev_party}] -> [{ps}]")
        prev_party = ps

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
        log(f"f{step}: *** BotModeError -> Manual: {e}")
        context.set_manual_mode()
    except Exception as e:
        import traceback

        log(f"f{step}: *** EXCEPTION: {e}\n{traceback.format_exc()}")
        context.set_manual_mode()

    sig = (ctrl, game_state.name if hasattr(game_state, "name") else str(game_state),
           get_current_battle_script_instruction() if ba else "", ml, ps)
    if sig == last_sig:
        no_progress += 1
    else:
        no_progress = 0
        last_sig = sig
    if no_progress in (1000, 3000, 6000, 9000, 12000, 15000, 18000):
        log(f"f{step}: !!! NO-PROGRESS x{no_progress} sig={sig}")
    if no_progress >= 20000:
        log(f"f{step}: HANG CONFIRMED (20000 frames no progress). Stopping.")
        break

    if step - last_heartbeat >= 2000:
        last_heartbeat = step
        log(f"f{step}: heartbeat ctrl={ctrl} state={sig[1]} ml={ml} party=[{ps}] hmrd_invocations={_hmrd_calls['n']}")

    if marshtomp is not None and ps.split("|")[0].split(":")[1] not in (f"L30",) and "MOVELEARN_DONE" not in globals():
        pass  # (level-change is already visible via the PARTY CHANGE log line)

    context.emulator.get_inputs()
    context.emulator.run_single_frame()
    previous_frame_info = frame_info
    previous_frame_info.previous_frame = None

log(f"[done] ran {step + 1} frames; final mode={context.bot_mode} party=[{_party_snapshot()}]")
log(f"[done] handle_move_replacement_dialogue was invoked {_hmrd_calls['n']} time(s) total")
try:
    for p in get_party():
        mv = ", ".join(lm.move.name for lm in p.moves if lm is not None)
        log(f"[moveset] {p.species.name} L{p.level}: {mv}")
except Exception as e:
    log(f"[moveset] err {e}")
logf.close()
