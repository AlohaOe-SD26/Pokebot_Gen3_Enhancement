"""A/B proof for the PHANTOM-SCRIPT escape (user's 2026-07-23 Route 111 hang).

THE STATE (from `478c2506...134140.log`, f1077383→user-killed): after Rock Smash's
wild-encounter roll spawned a Geodude battle, `EventScript_SmashRock` READ active
forever while the game was fully playable (controllable=True, no text, no menus).
`_wait_until_cutscene_over` mashed at it for 8000 frames, raised, the recovery rode
the same phantom, and the run wedged until manually killed.

Fault injection: patch the state readers to exactly that profile — script active,
avatar controllable, no waiting text, no menu tasks — and drive the rider.
  A (old semantics): runs the full 8000-frame timeout and raises.
  B (fixed): escapes as 'parked script' after ~600 frames, returning cleanly.
No emulator needed — the rider only consumes those four readers + button presses.
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.story import early_game

# ---- fault injection: the exact hang profile ----
active_ctx = SimpleNamespace(is_active=True)
idle_ctx = SimpleNamespace(is_active=False)
early_game.get_global_script_context = lambda: active_ctx
early_game.get_immediate_script_context = lambda: idle_ctx
early_game.player_avatar_is_controllable = lambda: True
early_game.is_waiting_for_input = lambda: False
early_game._menu_task_active = lambda: False

pressed = []
context.emulator = SimpleNamespace(press_button=lambda b: pressed.append(b))


def drive(gen, cap=20000):
    frames = 0
    try:
        while frames < cap:
            next(gen)
            frames += 1
    except StopIteration:
        return frames, "returned"
    except Exception as e:
        return frames, f"raised {type(e).__name__}: {e}"
    return frames, "still running (cap hit)"


frames, outcome = drive(early_game._wait_until_cutscene_over("A"))
print(f"fixed rider: {outcome} after {frames} frames ({len(pressed)} presses)")
assert outcome == "returned", f"expected a clean parked-script return, got: {outcome}"
assert frames < 700, f"escape should fire at ~600 frames, took {frames}"

# Sanity 1: a REAL cutscene (avatar locked) must still ride + time out honestly.
early_game.player_avatar_is_controllable = lambda: False
frames, outcome = drive(early_game._wait_until_cutscene_over("A", timeout_frames=1000))
print(f"real-scene sanity: {outcome} after {frames} frames")
assert outcome.startswith("raised BotModeError"), outcome

# Sanity 2: a scene that ENDS normally still returns promptly.
early_game.player_avatar_is_controllable = lambda: True
active_ctx.is_active = False
frames, outcome = drive(early_game._wait_until_cutscene_over("A"))
print(f"normal-end sanity: {outcome} after {frames} frames")
assert outcome == "returned" and frames < 60, (frames, outcome)

print("ALL PASS: the parked-script state returns in ~600 frames instead of an 8000-frame "
      "raise-and-derail loop; locked real scenes and normal endings behave as before.")
