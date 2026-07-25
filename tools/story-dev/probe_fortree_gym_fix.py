"""A/B proof for the do_fortree_gym() except-branch fix (2026-07-24).

THE BUG. `do_fortree_gym` navigates to the challenge tile (15,3) inside the
Fortree Gym. Its rotating turnstile doors reshape the walkable grid at
runtime, which the static planner can't see, so `navigate_to_anywhere` raises
BotModeError. The `except` branch used to call `_ride_out_scripted_scene("B")`
UNCONDITIONALLY before pushing toward the goal -- but most of the time there
is no scene to ride at all, so the rider burns its full engage-timeout budget
every round and starves the push that actually solves the door.

THE FIX (already applied, uncommitted, in
sandbox-pokebot/modules/story/early_game.py): only ride when
`get_global_script_context().is_active or not player_avatar_is_controllable()`.

THIS SCRIPT drives the REAL generator against the REAL emulator from the
captured wedge save. It has three modes:

  --drive        A/B: run do_fortree_gym() for up to --cap frames, report
                 frames consumed, position samples, and BADGE06_GET.
                 Run once with the fix stashed out (BEFORE) and once with it
                 applied (AFTER) -- see the sibling shell invocations.
  --push-test    Independent of the fix: does pressing the computed push
                 direction into the turnstile actually move the avatar /
                 reshape the grid? Manual loop, does not go through
                 do_fortree_gym at all.
  --control      SIMULATED regression control: monkeypatch
                 get_global_script_context so is_active=True on demand and
                 spy on _ride_out_scripted_scene to prove the rider still
                 runs when a real scene is flagged active, even with the fix
                 applied.

Usage: py -3.12 tools/story-dev/probe_fortree_gym_fix.py <--drive|--push-test|--control> [cap]
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
BUILD = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

MODE = sys.argv[1] if len(sys.argv) > 1 else "--drive"
CAP = int(sys.argv[2]) if len(sys.argv) > 2 else 60000

STATE = _REPO / "tools" / "story-dev" / "saves" / "fortree_gym_wedge.ss1"
assert STATE.is_file(), STATE

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.bot_mode = "Story"
context.emulator.load_save_state(STATE.read_bytes())
for _ in range(10):
    context.emulator.run_single_frame()

from modules.memory import get_event_flag
from modules.player import get_player_avatar
from modules.map_data import MapRSE
import modules.story.early_game as eg

GYM = MapRSE.FORTREE_CITY_GYM


def pos():
    return tuple(get_player_avatar().local_coordinates)


def dist():
    x, y = pos()
    return abs(x - 15) + abs(y - 3)


print(f"[loaded] {STATE.name}  pos={pos()}  BADGE06_GET={get_event_flag('BADGE06_GET')}")

if MODE == "--drive":
    print("=" * 70)
    gen = eg.do_fortree_gym()
    frames = 0
    last_report = 0
    samples = []
    outcome = None
    try:
        while frames < CAP:
            next(gen)
            context.emulator.run_single_frame()
            frames += 1
            if frames - last_report >= 5000:
                last_report = frames
                samples.append((frames, pos(), dist()))
                print(f"  f={frames:>6} pos={pos()} dist_to_target={dist()} "
                      f"BADGE06_GET={get_event_flag('BADGE06_GET')}")
    except StopIteration:
        outcome = "returned (do_fortree_gym completed)"
    except Exception as e:
        outcome = f"raised {type(e).__name__}: {e}"
    if outcome is None:
        outcome = "cap hit (still running)"
    print("-" * 70)
    print(f"[result] {outcome} after {frames} frames")
    print(f"[final]  pos={pos()} dist_to_target={dist()} BADGE06_GET={get_event_flag('BADGE06_GET')}")
    started = dist()  # note: dist() now is FINAL dist, kept for symmetry below
    print(f"[samples] {samples}")

elif MODE == "--push-test":
    print("=" * 70)
    print("Manual replica of the except-branch push, OUTSIDE do_fortree_gym,")
    print("to measure whether the push alone can make progress.")
    from modules.modes.util.global_navigation import navigate_to_anywhere
    from modules.modes.util.walking import wait_for_player_avatar_to_be_standing_still

    def try_navigate():
        g = navigate_to_anywhere(GYM, (15, 3), avoid_encounters=True, avoid_scripted_events=False)
        n = 0
        try:
            while n < 4000:
                next(g)
                context.emulator.run_single_frame()
                n += 1
        except StopIteration:
            return "arrived", n
        except Exception as e:
            return f"raised {type(e).__name__}", n
        return "cap (still navigating)", n

    outcome, n = try_navigate()
    print(f"[navigate #0] {outcome} after {n} frames, pos={pos()} dist={dist()}")

    for round_ in range(1, 9):
        x, y = pos()
        push = "Up" if y > 3 else ("Left" if x > 15 else "Right")
        p0 = pos()
        for _ in range(24):
            context.emulator.press_button(push)
            context.emulator.run_single_frame()
        g = wait_for_player_avatar_to_be_standing_still()
        n = 0
        try:
            while n < 600:
                next(g)
                context.emulator.run_single_frame()
                n += 1
        except StopIteration:
            pass
        p1 = pos()
        print(f"[push #{round_}] dir={push} pos {p0} -> {p1} moved={p0 != p1} dist={dist()}")
        outcome, n = try_navigate()
        print(f"[navigate #{round_}] {outcome} after {n} frames, pos={pos()} dist={dist()}")
        if outcome == "arrived":
            break
    print("-" * 70)
    print(f"[final] pos={pos()} dist_to_target={dist()} BADGE06_GET={get_event_flag('BADGE06_GET')}")

elif MODE == "--control":
    print("=" * 70)
    print("SIMULATED regression control: force get_global_script_context().is_active")
    print("True for the FIRST except-branch round only, spy on _ride_out_scripted_scene,")
    print("and confirm the (fixed) rider still runs it when a real scene is flagged.")

    calls = {"ride": 0, "gsc_reads": 0}
    real_gsc = eg.get_global_script_context
    real_ride = eg._ride_out_scripted_scene

    # Force "a scene IS active" on every read for this probe -- proves the gate
    # lets the rider through when is_active is True, without needing to script
    # an actual in-game cutscene at this exact wedge tile.
    class _ForcedActiveCtx:
        is_active = True

    def spy_gsc():
        calls["gsc_reads"] += 1
        return _ForcedActiveCtx()

    def spy_ride(button="B", **kw):
        calls["ride"] += 1
        print(f"    >> _ride_out_scripted_scene called (call #{calls['ride']})")
        return real_ride(button, **kw)

    eg.get_global_script_context = spy_gsc
    eg._ride_out_scripted_scene = spy_ride

    gen = eg.do_fortree_gym()
    frames = 0
    outcome = None
    try:
        while frames < 3000:
            next(gen)
            context.emulator.run_single_frame()
            frames += 1
    except StopIteration:
        outcome = "returned"
    except Exception as e:
        outcome = f"raised {type(e).__name__}: {e}"
    if outcome is None:
        outcome = "cap hit (still running)"

    eg.get_global_script_context = real_gsc
    eg._ride_out_scripted_scene = real_ride

    print("-" * 70)
    print(f"[result] {outcome} after {frames} frames; gsc_reads={calls['gsc_reads']} ride_calls={calls['ride']}")
    if calls["ride"] > 0:
        print("PASS (simulated): with is_active forced True, the fixed rider still called "
              "_ride_out_scripted_scene -- the gate does not skip a genuine scene.")
    else:
        print("FAIL (simulated): the rider never called _ride_out_scripted_scene even though "
              "is_active was forced True -- gate is over-eager / broken.")

else:
    print(f"unknown mode {MODE!r}")
