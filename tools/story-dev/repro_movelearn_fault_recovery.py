"""REPRO for the RECOVERY-SCOPE half of #24-movelearn-recovery (2026-07-25).

The companion repro (`repro_movelearn_hm_wedge.py`) fixes the move-learn wedge that
actually happened. This one proves the STRUCTURAL half: when a move-learn offer is
genuinely unanswerable, the run must lose a BATTLE, not the whole run.

WHY IT WAS BROKEN. Battle handling is not nested inside the bot mode. BattleListener
pushes `fight()` onto `context.controller_stack` and `main_loop` advances only the TOP
of that stack, so the mode generator and the battle handler are SIBLINGS. A
`BotModeError` raised in the battle handler therefore lands in `main_loop`, which sets
Manual — `StoryMode.run()`'s `except BotModeError` derail recovery is structurally
unable to see it. Cost: 2 of 5 night5 cold-start runs died at ~f1.55M.

The chain is proven in two halves, because no single arm can cover both cleanly:

  --mode stock   BATTLE SIDE, control. A real battle, a real unanswerable offer, a mode
                 that has NOT opted in. EXPECT: unchanged legacy behaviour —
                 BotModeError escapes to main_loop -> Manual, and NO fault is recorded.
                 This proves the opt-in gate really gates, so every stock bot mode
                 still behaves exactly as it always did.

  --mode optin   BATTLE SIDE, subject. Identical battle and identical fault, but the
                 mode declares `handles_battle_faults = True`. EXPECT: the valve routes
                 the fault into the channel, `handle_battle` stops driving, the battle
                 listener releases control, the mode CLAIMS the fault, and Manual is
                 never reached.

  --mode story   MODE SIDE. The real StoryMode on a clean milestone; a fault is placed
                 in the channel directly (marked SYNTHETIC below — the battle side is
                 already covered by the two arms above, and this isolates the seam that
                 was actually broken). EXPECT: StoryMode claims it inside its own try
                 and turns it into "derail #N: Story: battle handler gave up — ...",
                 then CARRIES ON in Story mode instead of dropping to Manual.

FAULT INJECTED in the stock/optin arms (same one `repro_hm_replace_valve_forced.py`
uses): once the game genuinely reaches LearnMoveState.AskWhetherToLearn, latch
`get_learn_move_state()` to report that state forever, so nothing can resolve the
dialogue and the 3-strike valve must fire. That is the point — we are testing what
happens AFTER it fires.

Run all three:
  py -3.12 tools/story-dev/repro_movelearn_fault_recovery.py --mode stock
  py -3.12 tools/story-dev/repro_movelearn_fault_recovery.py --mode optin
  py -3.12 tools/story-dev/repro_movelearn_fault_recovery.py --mode story
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
ap.add_argument("--mode", default="story", choices=["story", "stock", "optin"])
ap.add_argument("--frames", type=int, default=60000)
ap.add_argument("--inject-at", type=int, default=600, help="story arm: frame to place the synthetic fault")
ap.add_argument("--survive", type=int, default=1500, help="story arm: frames that must pass without Manual")
ap.add_argument("--build", default="sandbox", choices=["custom", "sandbox"])
ap.add_argument("--profile", default="repro-movelearn-fault")
ap.add_argument("--log", default=None)
args = ap.parse_args()

_REPO = Path(__file__).resolve().parents[2]
BUILD = _REPO / f"{args.build}-pokebot"
sys.path.insert(0, str(BUILD))
SCRATCH = Path(__file__).parent
SAVES = SCRATCH / "saves"
LOG = Path(args.log) if args.log else SCRATCH / f"repro_movelearn_fault_recovery_{args.mode}.log"

# The battle arms need a state that reaches a level-up fast; the story arm needs a
# milestone the real StoryMode can resume from cleanly.
state_path = SAVES / ("norman_done.ss1" if args.mode == "story" else "route116team.ss1")
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

from modules.memory import get_game_state, set_event_flag
from modules.modes import FrameInfo, get_bot_listeners, get_bot_mode_by_name, BotModeError, BotMode
from modules.plugins import load_plugins, load_built_in_plugins, plugin_profile_loaded
from modules.state_cache import state_cache
from modules.stats import StatsDatabase
from modules.tasks import get_global_script_context, get_tasks
import modules.battle_move_replacing as bmr
import modules.battle_fault as battle_fault

load_plugins()
load_built_in_plugins()
plugin_profile_loaded(context.profile)
context.stats = StatsDatabase(context.profile)
context.bot_listeners = get_bot_listeners(context.rom)
log(f"[setup] state={state_path.name} arm={args.mode}")

_latch = {"active": False}

if args.mode != "story":
    set_event_flag("BADGE01_GET", True)

    # Party rigged so the very next battle triggers a level-up move-learn.
    from modules.debug_utilities import debug_create_pokemon, debug_write_party
    from modules.pokemon import get_species_by_name, get_move_by_name, LearnedMove

    marshtomp_species = get_species_by_name("Marshtomp")
    exp31 = marshtomp_species.level_up_type.get_experience_needed_for_level(31)
    marshtomp = debug_create_pokemon(
        species=marshtomp_species,
        level=30,
        experience=exp31 - 1,
        moves=[
            LearnedMove.create(get_move_by_name("Water Gun")),
            LearnedMove.create(get_move_by_name("Mud Shot")),
            LearnedMove.create(get_move_by_name("Rock Smash")),
            LearnedMove.create(get_move_by_name("Bide")),
        ],
        nickname="MARSHTOMP",
        current_hp=None,
    )
    others = [
        debug_create_pokemon(
            species=get_species_by_name(n),
            level=26,
            moves=[LearnedMove.create(get_move_by_name("Tackle"))],
            nickname=n.upper(),
        )
        for n in ("Linoone", "Shroomish", "Loudred")
    ]
    debug_write_party([marshtomp, *others])
    log("[inject] party rigged: Marshtomp L30, 1 exp short of L31")

    # ---- FAULT INJECTION: latch the move-learn state so it can NEVER resolve -------
    _orig_get_learn_state = bmr.get_learn_move_state

    def _latched_get_learn_state():
        real = _orig_get_learn_state()
        if real == bmr.LearnMoveState.AskWhetherToLearn and not _latch["active"]:
            _latch["active"] = True
            log("[FAULT] latch ENGAGED — get_learn_move_state() reports AskWhetherToLearn forever")
        return bmr.LearnMoveState.AskWhetherToLearn if _latch["active"] else real

    bmr.get_learn_move_state = _latched_get_learn_state


_claimed = []


class _WalkingMode(BotMode):
    """Drives encounters without any story logic, so the arm tests the battle seam
    and nothing else."""

    @staticmethod
    def name():
        return "FaultControl"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import StoryMode

        shim = SimpleNamespace(_catch_team_target=4)
        shim._should_catch = lambda enc: StoryMode._should_catch(shim, enc)
        return StoryMode.on_battle_started(shim, encounter)

    def run(self):
        seq = ["Up", "Up", "Down", "Down", "Left", "Left", "Right", "Right"]
        i = 0
        while True:
            if getattr(self, "handles_battle_faults", False):
                reason = battle_fault.take_pending_fault()
                if reason is not None:
                    _claimed.append(reason)
                    log(f"[mode] CLAIMED the fault inside the mode's own scope: {reason}")
            context.emulator.press_button(seq[(i // 6) % len(seq)])
            yield
            i += 1


class StockMode(_WalkingMode):
    """Control: has NOT opted in."""


class OptInMode(_WalkingMode):
    handles_battle_faults = True


battle_fault.clear_pending_fault()
context.bot_mode_instance = None
context.controller_stack = []

# Watch the mode's console output for its derail line.
from modules.console import console

_derail_lines = []
_orig_print = console.print


def _watching_print(*a, **kw):
    try:
        txt = " ".join(str(x) for x in a)
        if "battle handler gave up" in txt or "derail #" in txt:
            _derail_lines.append(txt)
            log(f"[console] {txt}")
    except Exception:
        pass
    return _orig_print(*a, **kw)


console.print = _watching_print

previous_frame_info = None
manual_at = None
fault_seen_at = None
injected_at = None
bot_mode_error = None
last_step = 0

log(f"[run] mode={args.mode}; driving up to {args.frames} frames")

for step in range(args.frames):
    context.frame = step
    last_step = step

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

    if fault_seen_at is None and battle_fault.battle_fault_pending():
        fault_seen_at = step
        log(f"f{step}: fault RECORDED in the channel — the mode must claim it next")

    if context.bot_mode == "Manual":
        if manual_at is None:
            manual_at = step
            log(f"f{step}: *** MANUAL reached: {context.message}")
        break
    elif len(context.controller_stack) == 0:
        if args.mode == "story":
            context.bot_mode_instance = get_bot_mode_by_name("Story")()
        elif args.mode == "optin":
            context.bot_mode_instance = OptInMode()
        else:
            context.bot_mode_instance = StockMode()
        context.controller_stack.append(context.bot_mode_instance.run())

    # ---- SYNTHETIC fault for the story arm (battle side already covered above) ----
    if args.mode == "story" and injected_at is None and step >= args.inject_at:
        if battle_fault.request_mode_recovery(
            "SYNTHETIC: move-learn dialogue could not be resolved after 3 full attempts"
        ):
            injected_at = step
            log(f"f{step}: [SYNTHETIC] placed a battle fault in the channel for StoryMode")
        else:
            log(f"f{step}: [SYNTHETIC] request_mode_recovery REFUSED — StoryMode did not opt in!")
            break

    try:
        for listener in context.bot_listeners.copy():
            listener.handle_frame(context.bot_mode_instance, frame_info)
        if len(context.controller_stack) > 0:
            next(context.controller_stack[-1])
    except (StopIteration, GeneratorExit):
        if context.controller_stack:
            context.controller_stack.pop()
    except BotModeError as e:
        bot_mode_error = str(e)
        log(f"f{step}: *** BotModeError escaped to main_loop -> Manual: {e}")
        context.emulator.reset_held_buttons()
        context.message = str(e)
        context.set_manual_mode()
        manual_at = step
        break
    except Exception as e:
        import traceback

        log(f"f{step}: *** EXCEPTION\n{traceback.format_exc()}")
        break

    context.emulator.get_inputs()
    context.emulator.run_single_frame()
    previous_frame_info = frame_info
    previous_frame_info.previous_frame = None

    if args.mode == "story" and injected_at is not None and step - injected_at >= args.survive:
        log(f"f{step}: survived {args.survive} frames past the fault, still in {context.bot_mode} mode")
        break
    if args.mode == "optin" and _claimed and fault_seen_at is not None and step - fault_seen_at >= 600:
        log(f"f{step}: survived 600 frames past the claimed fault, still in {context.bot_mode} mode")
        break

log("")
log("=" * 78)
log(f"[result] arm                 = {args.mode}")
log(f"[result] latch engaged       = {_latch['active']}")
log(f"[result] fault recorded at   = {fault_seen_at}")
log(f"[result] fault claimed       = {len(_claimed)} {_claimed[:1]}")
log(f"[result] BotModeError escape = {bot_mode_error!r}")
log(f"[result] Manual reached at   = {manual_at}")
log(f"[result] derail lines seen   = {len(_derail_lines)}")
for line in _derail_lines[:4]:
    log(f"[result]   {line}")
log(f"[result] final bot_mode      = {context.bot_mode}  (stopped at f{last_step})")

if args.mode == "story":
    ok = (
        injected_at is not None
        and manual_at is None
        and bot_mode_error is None
        and any("battle handler gave up" in l for l in _derail_lines)
    )
    expect = "fault claimed as a DERAIL by StoryMode, never Manual"
elif args.mode == "optin":
    ok = (
        _latch["active"]
        and fault_seen_at is not None
        and len(_claimed) > 0
        and manual_at is None
        and bot_mode_error is None
    )
    expect = "valve routed the fault to the channel, mode claimed it, never Manual"
else:
    ok = _latch["active"] and manual_at is not None and fault_seen_at is None
    expect = "legacy behaviour preserved — BotModeError -> Manual, no fault recorded"

log(f"[result] VERDICT = {'PASS' if ok else 'FAIL'}  (expect: {expect})")
log("=" * 78)
logf.close()
sys.exit(0 if ok else 1)
