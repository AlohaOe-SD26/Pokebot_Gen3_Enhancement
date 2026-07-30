"""A/B proof for the `_navigate_riding_out` FAIL-FAST guard (early_game.py, ~line 185,
2026-07-24 fix, user log 12:39 + a treecko run — both died here).

THE BUG BEING FIXED: `_navigate_riding_out` retries `navigate_to_anywhere` up to
`tries` times, riding out a scene between attempts. That retry only helps when a
SCENE aborted the path (riding it out changes the world). If the destination is
simply UNREACHABLE (a bad plan), retrying is pointless — every attempt fails
identically and each retry still pays `_ride_out_scripted_scene`'s ~240-frame
engage wait. `get_devon_scope` wraps this in its own 10-round retry with tries=6,
so an unreachable destination burned ~14,400 frames of pure churn and let the
18,000-frame global story watchdog kill the run before the planner's real error
ever surfaced.

THE FIX: after a failure, if the field is IDLE (no active script, avatar
controllable) AND we are standing on the EXACT SAME tile as after the previous
failure, retrying cannot change the result -> raise immediately with the
planner's real error instead of burning the rest of `tries`.

WHAT THIS SCRIPT PROVES (against the REAL `_navigate_riding_out`, live emulator,
a captured save state — no reader mocks except where explicitly labelled):

  1. THE SAVING: real code, unreachable destination, idle field -> raises after
     ~one ride-out (~240 frames), not `tries` ride-outs (~1440 for tries=6).
  2. THE A/B: the SAME scenario with the guard's idle-check neutralized (monkeypatched
     in THIS SCRIPT ONLY, `early_game.py` is never touched) reproduces the OLD
     behaviour on the SAME input, so the two frame counts are directly comparable.
  3. NO REGRESSION:
       a) a REACHABLE destination still succeeds normally (real code, unpatched).
       b) a field that is NOT idle (simulated: `get_global_script_context` patched
          to report an active script — labelled SIMULATED, not a live scene) still
          retries through all `tries` instead of failing fast.

Save used: tools/story-dev/saves/rocksmash_taught.ss1 — verified below (not
trusted by name) to load controllable, idle, in MAUVILLE_CITY (0,2) @ (32,15).

Run: py -3.12 tools/story-dev/repro_navigate_failfast.py
"""

import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
_SANDBOX = str(_REPO / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"

SAVE = _REPO / "tools" / "story-dev" / "saves" / "rocksmash_taught.ss1"
SAVE_BYTES = SAVE.read_bytes()


def load_save():
    context.emulator.load_save_state(SAVE_BYTES)
    for _ in range(30):
        context.emulator.run_single_frame()


import modules.story.early_game as eg
from modules.modes import BotModeError
from modules.memory import GameState, get_game_state
from modules.player import get_player_avatar, player_avatar_is_controllable
from modules.tasks import get_global_script_context

_orig_get_player_avatar = eg.get_player_avatar
_orig_get_global_script_context = eg.get_global_script_context


def restore_patches():
    eg.get_player_avatar = _orig_get_player_avatar
    eg.get_global_script_context = _orig_get_global_script_context


def drive(gen, cap):
    """Same convention as probe_ride_fixed.py: rider decides, then the emulator
    frame is actually applied, then we count it."""
    frames = 0
    try:
        while frames < cap:
            next(gen)
            context.emulator.run_single_frame()
            frames += 1
    except StopIteration:
        return frames, "returned"
    except Exception as e:
        # ‼ Report the exception's CONCRETE type but assert on its TYPE, never on this
        # string (08-MISTAKES 2026-07-30). This repro was dead for days — and mislabelled
        # "environmental — needs a real mgba" — purely because it asserted
        # `startswith("raised BotModeError")` and the code correctly began raising
        # `UnreachableDestinationError`, which IS a BotModeError subclass. The behaviour
        # was right; the string match was not. `raised_botmode` keeps the substring
        # assertions below working while making the type check the real gate.
        return frames, _Outcome(f"raised {type(e).__name__}: {e}", exception=e)
    return frames, _Outcome(f"CAP HIT ({cap})")


class _Outcome(str):
    """The outcome string, plus the exception object it came from (if any)."""

    def __new__(cls, text, *, exception=None):
        self = super().__new__(cls, text)
        self.exception = exception
        return self

    def raised_botmode(self) -> bool:
        """True when a `BotModeError` (or any subclass) escaped — the fact these
        assertions actually mean."""
        return isinstance(self.exception, BotModeError)


# --- 0) Verify the save state (never trust the filename). --------------------
load_save()
pa = get_player_avatar()
verify = {
    "map_group_and_number": tuple(pa.map_group_and_number),
    "local_coordinates": tuple(pa.local_coordinates),
    "game_state": get_game_state().name,
    "controllable": player_avatar_is_controllable(),
    "script_active": get_global_script_context().is_active,
}
print("=" * 78)
print("0) SAVE STATE VERIFICATION:", SAVE.name)
print("  ", verify)
assert verify["game_state"] == "OVERWORLD", "not in the overworld"
assert verify["controllable"], "avatar not controllable"
assert not verify["script_active"], "a script is active"
assert verify["map_group_and_number"] == (0, 2), "expected MAUVILLE_CITY (0,2)"
assert verify["local_coordinates"] == (32, 15), "expected (32, 15)"
print("   OK: rocksmash_taught.ss1 loads clean, idle, controllable, MAUVILLE_CITY @ (32,15).")

UNREACHABLE_MAP = (99, 99)   # not in the warp graph -> navigate_to_anywhere fails INSTANTLY,
UNREACHABLE_TILE = (0, 0)    # every single attempt, with zero frames spent inside it.
REACHABLE_MAP = (0, 2)       # MAUVILLE_CITY -- same map as the save, so no warping needed.
REACHABLE_TILE = (35, 15)    # 3 tiles east; verified via calculate_path() before writing this
                              # script: "OK, 3 waypoints" from (32,15).
TRIES = 6                    # matches get_devon_scope's real call site.

# --- 1) THE SAVING: real (fixed) code, unreachable destination. --------------
print("\n" + "=" * 78)
print("1) THE FIX — real _navigate_riding_out, UNREACHABLE dest, idle field")
load_save()
frames_fixed, outcome_fixed = drive(
    eg._navigate_riding_out(UNREACHABLE_MAP, UNREACHABLE_TILE, tries=TRIES), cap=5000
)
print(f"   frames={frames_fixed}  outcome={outcome_fixed}")
assert outcome_fixed.raised_botmode(), outcome_fixed
assert "field is idle" in outcome_fixed, f"expected the fail-fast message, got: {outcome_fixed}"
assert frames_fixed < 400, f"expected roughly ONE ride-out (~240 frames), got {frames_fixed}"
print(f"   PASS: fail-fast fired after {frames_fixed} frames (~one ride-out), "
      f"not {TRIES} x ~240 = ~{TRIES*240}.")

# --- 2) THE A/B: same scenario, guard neutralized IN THIS SCRIPT ONLY. -------
print("\n" + "=" * 78)
print("2) THE A/B — SAME scenario, guard's idle-check neutralized (test-only monkeypatch)")
print("   (early_game.py is NOT edited; we patch early_game.get_player_avatar so the")
print("   guard's own try/except computes where=None every time, exactly restoring")
print("   the pre-fix code path -- _ride_out_scripted_scene and navigate_to_anywhere")
print("   are untouched, so the retry MACHINERY itself is identical to the real fix.)")
load_save()


def _raise_get_player_avatar():
    raise RuntimeError("neutralized for A/B test (forces where=None, i.e. pre-fix behaviour)")


eg.get_player_avatar = _raise_get_player_avatar
try:
    frames_old, outcome_old = drive(
        eg._navigate_riding_out(UNREACHABLE_MAP, UNREACHABLE_TILE, tries=TRIES), cap=5000
    )
finally:
    restore_patches()
print(f"   frames={frames_old}  outcome={outcome_old}")
assert outcome_old.raised_botmode(), outcome_old
assert f"after {TRIES} tries" in outcome_old, f"expected the old exhausted-retries message, got: {outcome_old}"
assert "field is idle" not in outcome_old, "guard should NOT have fired with the idle-check neutralized"
print(f"   OLD BEHAVIOUR REPRODUCED: {frames_old} frames burned across all {TRIES} tries "
      f"before surfacing the real error.")

print("\n" + "-" * 78)
print(f"   SIDE BY SIDE (identical input, identical retry machinery):")
print(f"     fixed (guard live):        {frames_fixed:>5} frames")
print(f"     old   (guard neutralized): {frames_old:>5} frames")
print(f"     saved: {frames_old - frames_fixed} frames "
      f"({100*(frames_old-frames_fixed)/frames_old:.0f}% reduction)")
assert frames_fixed < frames_old, "the fix should spend strictly fewer frames than the old path"

# --- 3a) CONTROL: a REACHABLE destination still succeeds normally. -----------
print("\n" + "=" * 78)
print("3a) CONTROL — real code, REACHABLE destination (must NOT fail fast, must succeed)")
load_save()
frames_ok, outcome_ok = drive(
    eg._navigate_riding_out(REACHABLE_MAP, REACHABLE_TILE, tries=TRIES), cap=2000
)
print(f"   frames={frames_ok}  outcome={outcome_ok}")
assert outcome_ok == "returned", f"a reachable destination must succeed, got: {outcome_ok}"
pa2 = get_player_avatar()
assert tuple(pa2.local_coordinates) == REACHABLE_TILE, (
    f"expected to actually arrive at {REACHABLE_TILE}, ended at {tuple(pa2.local_coordinates)}"
)
print(f"   PASS: arrived at {REACHABLE_TILE} in {frames_ok} frames -- the legitimate path is untouched.")

# --- 3b) CONTROL: field NOT idle (SIMULATED active script) still retries. ---
print("\n" + "=" * 78)
print("3b) CONTROL — field NOT idle (SIMULATED: get_global_script_context patched to")
print("    report an active script; NOT a live scene) -- guard must NOT fire, must")
print("    retry through all tries instead of failing fast.")
load_save()
CTRL_TRIES = 2  # kept small: the phantom-script escape inside _wait_until_cutscene_over
                # needs ~600 frames per ride-out once script_active reads True throughout,
                # since the real avatar is (truthfully) still controllable underneath.


class _AlwaysActive:
    is_active = True


eg.get_global_script_context = lambda: _AlwaysActive()
try:
    frames_ctrl, outcome_ctrl = drive(
        eg._navigate_riding_out(UNREACHABLE_MAP, UNREACHABLE_TILE, tries=CTRL_TRIES), cap=5000
    )
finally:
    restore_patches()
print(f"   frames={frames_ctrl}  outcome={outcome_ctrl}")
assert outcome_ctrl.raised_botmode(), outcome_ctrl
assert f"after {CTRL_TRIES} tries" in outcome_ctrl, (
    f"expected it to exhaust all {CTRL_TRIES} tries (guard must not fire), got: {outcome_ctrl}"
)
assert "field is idle" not in outcome_ctrl, "guard fired even though the field was reported NOT idle -- REGRESSION"
print(f"   PASS: guard did NOT fire while the field read 'not idle' -- retried all "
      f"{CTRL_TRIES} tries ({frames_ctrl} frames) exactly like the pre-fix code.")

print("\n" + "=" * 78)
print("ALL PASS: the fail-fast guard cuts the wasted-frame churn on a genuinely")
print("unreachable destination, WITHOUT touching the legitimate reachable-destination")
print("path or the scene-retry path (simulated active-script control).")
