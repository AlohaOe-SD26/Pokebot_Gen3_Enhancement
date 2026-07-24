"""Regression guard for _wait_until_cutscene_over's handling of parked
'waiting-for-input' states (KI-15 investigation, final design).

BACKGROUND (probed on captured states, this session): a stale post-battle battle
message ("Got away safely!", ki15_gotaway_wedge.ss1) and a field dialogue's parked
WaitForAorBPress tail (the museum greeter) are indistinguishable on EVERY reader
and both ignore B. Two rider-side "clear it here" designs regressed the museum
greeter (A re-opens NPC dialogue) and were reverted. FINAL DESIGN: the rider
treats both as FREE and returns (the old, museum-green behavior); the battle
wedge — whose one unique property is that it blocks all movement — is cleared by
StoryMode.run's position-frozen persistence nudge (validated live via faithful
runs + the captured wedge state, not from this mock).

This guard pins the rider's contract:
 1) parked-wait (no script, controllable, waiting): return FREE quickly, ZERO
    A presses (A here re-opens dialogues — the museum regression).
 2) active dialogue (script running): pressed through via _dialogue_button (B).
 3) scene-over: prompt return, no presses.

Run:  python tools/story-dev/repro_cutscene_waiting_msg.py
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.story import early_game


def install(*, script_active=False, waiting=False, b_ends_script_after=None):
    ctx = SimpleNamespace(is_active=script_active)
    idle = SimpleNamespace(is_active=False)
    early_game.get_global_script_context = lambda: ctx
    early_game.get_immediate_script_context = lambda: idle
    early_game.player_avatar_is_controllable = lambda: True
    early_game._menu_task_active = lambda: False
    early_game.is_waiting_for_input = lambda: waiting

    pressed = []

    def _press(b):
        pressed.append(b)
        if b_ends_script_after is not None and b == "B" and len(pressed) >= b_ends_script_after:
            ctx.is_active = False

    early_game.context.emulator = SimpleNamespace(press_button=_press)
    return pressed


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


print("=" * 70)

# 1) Parked-wait state (battle wedge OR museum tail — same readers): FREE, no A.
pressed = install(waiting=True)
frames, outcome = drive(early_game._wait_until_cutscene_over("B"))
print(f"[parked-wait] {outcome} after {frames} frames "
      f"({len(pressed)} presses, {pressed.count('A')} A)")
assert outcome == "returned" and frames < 60, (frames, outcome)
assert pressed.count("A") == 0, "the rider must NEVER A-press a parked wait state"

# 2) An active dialogue: B-ridden until the script ends, then return.
pressed = install(script_active=True, waiting=True, b_ends_script_after=25)
frames, outcome = drive(early_game._wait_until_cutscene_over("B"))
print(f"[dialogue]    {outcome} after {frames} frames "
      f"({len(pressed)} presses, {pressed.count('A')} A)")
assert outcome == "returned", (frames, outcome)
assert pressed.count("B") >= 25 and pressed.count("A") == 0

# 3) Scene genuinely over: prompt return, no presses at all.
pressed = install()
frames, outcome = drive(early_game._wait_until_cutscene_over("B"))
print(f"[scene-over]  {outcome} after {frames} frames ({len(pressed)} presses)")
assert outcome == "returned" and frames < 60, (frames, outcome)
assert len(pressed) == 0

print("-" * 70)
print("ALL PASS: the rider returns free at parked waits (never A — no dialogue "
      "re-open), B-rides active dialogue, and returns silently when the scene is over.")
