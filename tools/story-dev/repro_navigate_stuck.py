"""A/B proof for the KI-15 navigate_to post-battle oscillation bail.

THE BUG (KI-15, 2/3 confirmed 20k hangs — ROUTE 104 (5,6)<->(5,7)). An inline
battle fires DURING story navigation. When it ends, control returns into the
already-running `navigate_to` mid-`follow_waypoints`, but the post-battle
ReturnFromBattleToOverworld transition leaves the avatar unable to actually
advance: it bounces between two adjacent tiles. `follow_waypoints` times out at
each leg -> `navigate_to` catches TimedOutTryingToReachWaypointError, sees NO
active field script, and re-paths... forever. Nothing bails, so it spins until
the 20k story watchdog. (`tasks=[]`, `cb=ReturnFromBattleToOverworld`.)

Fault injection (reader-level, no emulator — the avatar's motion is what's
broken, not any single reader): mock `follow_waypoints` to always time out,
`get_global_script_context` to idle, and `get_player_location` to OSCILLATE
between two tiles (the real (5,6)<->(5,7) bounce). Also a FROZEN variant (one
tile) and two must-not-regress controls (healthy arrival; genuinely-progressing
blocked nav that reaches new tiles each re-path).

  A (old code): navigate_to spins forever (cap hit) on both stuck variants.
  B (fixed):    it raises NavigationStuckError within a bounded budget, while
                the healthy + progressing controls still complete/continue.

Run:  python tools/story-dev/repro_navigate_stuck.py
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.modes.util import walking
from modules.modes.util.walking import navigate_to, TimedOutTryingToReachWaypointError
from modules.modes._interface import BotModeError

# NavigationStuckError is added by the fix; it won't exist on the "A" (pre-fix) pass.
_STUCK_CLS = getattr(walking, "NavigationStuckError", None)


def _make_timeout():
    """A TimedOutTryingToReachWaypointError without touching context.rom."""
    err = TimedOutTryingToReachWaypointError.__new__(TimedOutTryingToReachWaypointError)
    BotModeError.__init__(err, "timeout (repro)")
    return err


def install_readers(position_sequence, follow_behaviour="timeout"):
    """position_sequence: a callable returning the 'current' player location each
    time it's asked (simulates avatar motion). follow_behaviour: 'timeout' (always
    time out) or 'arrive' (return cleanly on first call)."""
    walking.get_global_script_context = lambda: SimpleNamespace(is_active=False)
    walking.get_player_location = position_sequence
    # The fix's settle-wait presses nothing and waits for a stable, standing-still
    # avatar. Report it as immediately settled so the wedge still bails (the real
    # transition simply never lets the nav advance, which is what we're modelling).
    walking.player_avatar_is_controllable = lambda: True
    walking.player_avatar_is_standing_still = lambda: True

    if follow_behaviour == "arrive":
        def _fw(path, run=True, final_facing_direction=None):
            # drain the generator arg politely, then finish (healthy arrival)
            yield
            return
    else:
        def _fw(path, run=True, final_facing_direction=None):
            # a few frames of "walking", then the leg times out (avatar stuck)
            for _ in range(3):
                yield
            raise _make_timeout()

    walking.follow_waypoints = _fw


def drive(gen, cap=25000):
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


def oscillator(a=(0, (5, 6)), b=(0, (5, 7))):
    """Alternates between two tiles on every read — the real (5,6)<->(5,7) bounce."""
    state = {"n": 0}
    def _read():
        state["n"] += 1
        return a if state["n"] % 2 else b
    return _read


def frozen(pos=(0, (5, 6))):
    return lambda: pos


def progressing():
    """Reaches a NEW tile on every read — a genuinely-advancing (if repeatedly
    re-pathing) navigation that must NOT be mistaken for stuck."""
    state = {"n": 0}
    def _read():
        state["n"] += 1
        return (0, (5, state["n"]))
    return _read


print("=" * 70)
if _STUCK_CLS is None:
    print("NavigationStuckError NOT present -> running the 'A' (pre-fix) pass.")
    print("Expectation: the stuck variants SPIN FOREVER (cap hit) = bug reproduced.")
else:
    print("NavigationStuckError present -> running the 'B' (fixed) pass.")
    print("Expectation: stuck variants bail bounded; controls unaffected.")
print("=" * 70)

DEST = ((0, 0), (9, 9))

# 1) OSCILLATION (the real ROUTE 104 bounce)
install_readers(oscillator(), "timeout")
frames, outcome = drive(navigate_to(*DEST))
print(f"[oscillation] {outcome} after {frames} frames")
if _STUCK_CLS is None:
    assert outcome == "still running (cap hit)", f"expected the bug (infinite spin), got: {outcome}"
else:
    assert outcome.startswith("raised NavigationStuckError"), outcome
    assert frames < 2000, f"bail should be well-bounded, took {frames}"

# 2) FROZEN (0-amplitude bounce — total freeze)
install_readers(frozen(), "timeout")
frames, outcome = drive(navigate_to(*DEST))
print(f"[frozen]      {outcome} after {frames} frames")
if _STUCK_CLS is None:
    assert outcome == "still running (cap hit)", f"expected the bug (infinite spin), got: {outcome}"
else:
    assert outcome.startswith("raised NavigationStuckError"), outcome
    assert frames < 2000, f"bail should be well-bounded, took {frames}"

if _STUCK_CLS is not None:
    # 3) CONTROL: healthy arrival must still complete cleanly.
    install_readers(frozen(), "arrive")
    frames, outcome = drive(navigate_to(*DEST))
    print(f"[healthy]     {outcome} after {frames} frames")
    assert outcome == "returned", f"a normal arrival must complete, got: {outcome}"

    # 4) CONTROL: a nav that keeps reaching NEW tiles between re-paths must NOT
    #    prematurely bail. It never 'arrives' here (follow always times out) so it
    #    should run until the cap WITHOUT raising NavigationStuckError.
    install_readers(progressing(), "timeout")
    frames, outcome = drive(navigate_to(*DEST), cap=6000)
    print(f"[progressing] {outcome} after {frames} frames")
    assert outcome == "still running (cap hit)", (
        f"a progressing nav must not be mistaken for stuck, got: {outcome}"
    )

print("-" * 70)
if _STUCK_CLS is None:
    print("BUG REPRODUCED: navigate_to spins forever on a post-battle oscillation/freeze.")
    print("Now apply the fix and re-run to see the 'B' pass.")
else:
    print("ALL PASS: oscillation + freeze bail bounded via NavigationStuckError; "
          "healthy arrival completes and a progressing nav is not mis-flagged.")
