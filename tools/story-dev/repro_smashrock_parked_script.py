"""A/B proof for the Route 111 (18,99) permanent hang — the longest-standing bug
(4+ long runs killed, user's real-HW log + `hmfix-runs/torchic.log` f1248200-f1267300).

ROOT CAUSE (measured, not guessed): Rock Smash's wild-encounter roll can
battle-interrupt `EventScript_SmashRock`, and `get_global_script_context().is_active`
then reads True for the REST OF THE RUN (probed live on the captured wedge state
`saves/smashrock_parked.ss1`: 25,000 frames of ZERO input, script context never
clears). This is a STALE READER, not a real lock — the SAME state shows the avatar
is fully `player_avatar_is_controllable()`, and pressing a direction key turns +
walks it INSTANTLY (facing changes on the very first pressed frame; moved (18,99)
-> (18,97) within 60 frames) even while the script context stays "active" forever.

The actual bug is in `ensure_facing_direction` (modules/modes/util/walking.py): its
"a field script is active -> press B instead of turning" branch trusted that reader
blindly. Since the parked script never advances (B does nothing to a phantom), this
branch burns the whole `total_frames` absolute-bound budget (1800f) every single
call and raises "could not face Up ... input not landing" -- StoryMode.run's outer
loop then immediately retries the same leg, which walks straight back into the same
branch: an infinite raise<->retry loop indistinguishable from a hang (harness
confirms it at the 20,000-frame no-progress watchdog).

THE FIX: mirror the established PHANTOM-SCRIPT ESCAPE pattern already used in
`_wait_until_cutscene_over` / `_ride_out_all_scenes` (early_game.py) — after a
bounded stretch (600 frames) of "script reads active, but avatar is controllable
and nothing is waiting for input", stop deferring to the script gate for the rest
of the call and fall through to actually turning.

THREE PROOFS BELOW:
  1. LIVE STATE A/B (strongest): drive the real `ensure_facing_direction` generator
     against the real emulator loaded from the captured wedge state, comparing the
     pre-fix and post-fix code (toggle with --phase before/after; orchestrated via
     `git stash` on walking.py only, see the accompanying shell commands).
  2. CONTROL — healthy quick-clear: a script that reads active only briefly (like a
     REAL, uninterrupted Rock Smash) must still turn promptly, not wait out 600
     phantom frames every time.
  3. CONTROL — real locked cutscene: an avatar genuinely NOT controllable while a
     script runs must still be ridden out / bounded-raise exactly as before — the
     escape must never fire on a real scene.
"""

import argparse
import pathlib as _pl
import sys
from types import SimpleNamespace

_REPO = _pl.Path(__file__).resolve().parents[2]
_SANDBOX = _REPO / "sandbox-pokebot"
sys.path.insert(0, str(_SANDBOX))


def _drive(gen, cap, advance_emulator=False):
    from modules.context import context

    frames = 0
    try:
        while frames < cap:
            next(gen)                       # rider decides + queues a press for this frame
            if advance_emulator:
                context.emulator.run_single_frame()  # apply it (harness order — probe_ride_fixed.py)
            frames += 1
    except StopIteration:
        return frames, "returned"
    except Exception as e:
        return frames, f"raised {type(e).__name__}: {e}"
    return frames, "still running (cap hit)"


def live_state_test(state_name="smashrock_parked.ss1", direction="Up", cap=2200):
    """Drive the REAL ensure_facing_direction generator against the real emulator,
    loaded from the exact captured wedge (Route 111 (18,99), post-battle,
    scripts=['EventScript_SmashRock'], controllable=True — matches
    hmfix-runs/torchic.log f1248200 and the user's independent real-HW log)."""
    from modules.context import context
    from modules.profiles import load_profile_by_name
    from modules.game import set_rom

    profile = load_profile_by_name("hmfix-torchic")
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)

    from modules.libmgba import LibmgbaEmulator

    context.emulator = LibmgbaEmulator(profile, lambda: None)
    context.audio = False
    context.video = False
    context.emulation_speed = 0
    context.bot_mode = "Story"

    state_path = _REPO / "tools" / "story-dev" / "saves" / state_name
    context.emulator.load_save_state(state_path.read_bytes())

    from modules.player import get_player_avatar
    from modules.tasks import get_global_script_context
    from modules.modes.util.walking import ensure_facing_direction

    av = get_player_avatar()
    print(
        f"[loaded] {state_path.name}  map={av.map_group_and_number} pos={av.local_coordinates} "
        f"facing={av.facing_direction} gsc.is_active={get_global_script_context().is_active}"
    )

    frames, outcome = _drive(ensure_facing_direction(direction), cap, advance_emulator=True)
    av = get_player_avatar()
    print(
        f"ensure_facing_direction({direction!r}): {outcome} after {frames} frames  "
        f"final pos={av.local_coordinates} facing={av.facing_direction} "
        f"gsc.is_active={get_global_script_context().is_active}"
    )
    return frames, outcome


def control_tests():
    """Reader-level fault injection (fast, no emulator) for the two regression
    controls: a real scene must still be ridden out honestly, and a genuinely
    brief/healthy script-active window must not be delayed by the escape."""
    from modules.context import context
    from modules.profiles import load_profile_by_name
    from modules.game import set_rom

    profile = load_profile_by_name("repro-ml")
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)

    import modules.modes.util.walking as walking

    pressed = []
    context.emulator = SimpleNamespace(press_button=lambda b: pressed.append(b))

    # ---- CONTROL A: a REAL locked cutscene (avatar not controllable). Must still
    # be bounded (never hangs) and must NEVER take the phantom-escape early-out. ----
    from modules.player import PlayerAvatar
    from modules.memory import GameState

    class _FakeAvatar:
        facing_direction = "Down"  # never matches "Up" -> loop runs to its bound
        tile_transition_state = None
        running_state = None
        local_coordinates = (18, 99)

    walking.get_player_avatar = lambda: _FakeAvatar()
    walking.get_global_script_context = lambda: SimpleNamespace(is_active=True)
    walking.player_avatar_is_controllable = lambda: False  # genuinely locked
    walking.is_waiting_for_input = lambda: False
    walking.get_game_state = lambda: GameState.OVERWORLD

    pressed.clear()
    frames, outcome = _drive(walking.ensure_facing_direction("Up"), cap=6000)
    print(f"CONTROL A (real locked scene): {outcome} after {frames} frames, {len(pressed)} presses")
    assert outcome.startswith("raised BotModeError"), f"a real locked scene must still bounded-raise, got: {outcome}"
    assert frames >= 1800, "must not escape early on a genuinely locked avatar"
    assert "B" in pressed and "Up" not in pressed, "a locked scene must only be B-ridden, never turned"

    # ---- CONTROL B: a HEALTHY, brief script-active window (like an uninterrupted
    # Rock Smash's YES/NO prompt) that clears on its own well under the 600-frame
    # phantom threshold — must turn promptly, not stall waiting out the escape. ----
    gsc_state = SimpleNamespace(is_active=True)
    walking.get_global_script_context = lambda: gsc_state
    walking.player_avatar_is_controllable = lambda: True
    walking.is_waiting_for_input = lambda: False

    frame_counter = {"n": 0}
    real_next = None

    class _Avatar2:
        facing_direction = "Down"
        tile_transition_state = None
        running_state = None
        local_coordinates = (18, 99)

    _av2 = _Avatar2()
    walking.get_player_avatar = lambda: _av2

    def _tick_and_maybe_turn():
        frame_counter["n"] += 1
        if frame_counter["n"] > 40:  # script clears after 40 frames (a real, healthy prompt)
            gsc_state.is_active = False
        if not gsc_state.is_active:
            _av2.tile_transition_state = walking.TileTransitionState.NOT_MOVING
            _av2.running_state = walking.RunningState.NOT_MOVING
            walking.get_game_state = lambda: GameState.OVERWORLD
            _av2.facing_direction = "Up"  # the press "lands" once the real script ends

    pressed.clear()
    gen = walking.ensure_facing_direction("Up")
    frames = 0
    outcome = None
    try:
        while frames < 700:
            next(gen)
            _tick_and_maybe_turn()
            frames += 1
    except StopIteration:
        outcome = "returned"
    print(f"CONTROL B (healthy brief script, clears at f=40): {outcome} after {frames} frames")
    assert outcome == "returned" and frames < 100, (
        f"a healthy brief script-active window must resolve fast, not wait out the "
        f"600-frame phantom escape: {outcome} after {frames}"
    )
    assert pressed.count("B") < 45, (
        f"should not have waited out anywhere near the 600-frame phantom escape: {pressed.count('B')} B-presses"
    )

    print("CONTROLS PASS: a genuinely locked scene still bounded-raises without ever turning early; "
          "a healthy brief script-active window still turns promptly (no phantom-escape delay).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["live", "controls"], default="live")
    ap.add_argument("--state", default="smashrock_parked.ss1")
    ap.add_argument("--direction", default="Up")
    ap.add_argument("--cap", type=int, default=2200)
    args = ap.parse_args()

    if args.mode == "live":
        live_state_test(args.state, args.direction, args.cap)
    else:
        control_tests()
