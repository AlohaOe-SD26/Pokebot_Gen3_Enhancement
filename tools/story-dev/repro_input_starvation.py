"""Guard-repro for the KI-15-family input-starvation fixes in walking.py.

The post-battle freeze leaves the avatar permanently 'moving' (not NOT_MOVING /
not standing-still) while NO script runs — and any loop that politely presses
nothing at that state parks forever (live: 20k-frame hangs; probed: any input
edge revives it; reloads defuse the state, so this proves the CODE PATHS, with
live proof riding the next batch).

 1) ensure_facing_direction: starved (movement never settles, no script) →
    jolts the turn direction after ~120f and RAISES by 3000f (was: silent forever).
 2) wait_for_player_avatar_to_be_standing_still: same shape → direction jolts
    after 240f, RAISES by 3000f.
Healthy controls: an avatar that settles/turns promptly completes as before.

Run:  python tools/story-dev/repro_input_starvation.py
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.modes.util import walking
from modules.player import RunningState, TileTransitionState
from modules.memory import GameState


def install(*, frozen: bool, facing="Down", settle_after=None):
    """frozen=True models the post-battle freeze: never NOT_MOVING, never standing
    still — unless a press arrives and settle_after says how many presses revive it."""
    state = {"presses": [], "frozen": frozen}

    def avatar():
        f = state["frozen"]
        return SimpleNamespace(
            facing_direction=facing,
            local_coordinates=(5, 5),
            tile_transition_state=(TileTransitionState.TRANSITIONING if f else TileTransitionState.NOT_MOVING),
            running_state=(RunningState.MOVING if f else RunningState.NOT_MOVING),
        )

    def press(b):
        state["presses"].append(b)
        if settle_after is not None and len(state["presses"]) >= settle_after:
            state["frozen"] = False

    walking.get_player_avatar = avatar
    walking.get_game_state = lambda: GameState.OVERWORLD
    walking.get_global_script_context = lambda: SimpleNamespace(is_active=False)
    walking.player_avatar_is_standing_still = lambda: not state["frozen"]
    walking.context.emulator = SimpleNamespace(press_button=press)
    return state


def drive(gen, cap=8000):
    n = 0
    try:
        while n < cap:
            next(gen)
            n += 1
    except StopIteration:
        return n, "returned"
    except Exception as e:
        return n, f"raised {type(e).__name__}: {e}"
    return n, "cap hit (silent spin)"


print("=" * 70)

# 1) ensure_facing_direction, permanently frozen: must jolt then RAISE (never spin).
st = install(frozen=True, facing="Down")
n, out = drive(walking.ensure_facing_direction("Up"))
jolts = len(st["presses"])
print(f"[facing/frozen]   {out} after {n} frames ({jolts} jolt presses)")
assert out.startswith("raised BotModeError"), out
assert jolts > 100, "the jolt taps must fire while starved"

# 2) ensure_facing_direction, freeze that an input edge revives (the probed reality).
st = install(frozen=True, facing="Down", settle_after=3)
n, out = drive(walking.ensure_facing_direction("Up"))
print(f"[facing/revived]  {out} after {n} frames ({len(st['presses'])} presses)")
# after revival the loop presses the turn each frame; our mock never changes
# facing_direction, so a raise is still the exit — the point is presses now flow.
assert len(st["presses"]) >= 3

# 3) stand-still waiter, permanently frozen: jolts then raises.
st = install(frozen=True)
n, out = drive(walking.wait_for_player_avatar_to_be_standing_still())
print(f"[standstill/frozen] {out} after {n} frames ({len(st['presses'])} jolts)")
assert out.startswith("raised BotModeError"), out
assert len(st["presses"]) > 100

# 4) stand-still waiter, healthy: returns immediately, zero presses.
st = install(frozen=False)
n, out = drive(walking.wait_for_player_avatar_to_be_standing_still())
print(f"[standstill/ok]     {out} after {n} frames ({len(st['presses'])} presses)")
assert out == "returned" and len(st["presses"]) == 0

print("-" * 70)
print("ALL PASS: starving loops now jolt and are bounded; healthy paths unchanged.")
