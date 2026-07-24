"""Direct measurement (NOT fault injection): does `get_global_script_context().is_active`
ever clear on its own after a Rock-Smash-triggered wild battle ends, or does it stay True
forever — a stale reader in the same class as the already-documented `gBattleMainFunc` /
`gDisplayedStringBattle` staleness?

Ground-truth user report (Route 111, treecko/Grovyle run) claims `EventScript_SmashRock`
reads active for 140,000+ frames after a RanAway battle ends, with the bot doing nothing
(Manual mode). This drives the REAL, UNMODIFIED `_smash_rock` generator (early_game.py
call sites at lines 4297-4298, unchanged) against the REAL emulator and, once a
battle-during-smash is observed, watches `is_active` / the script stack for 20,000 further
frames with ZERO input.

‼ CHECKPOINT DEVIATION FROM THE ORIGINAL BRIEF (documented, not silent): the brief named
`wattson_done.ss1` as "the state right before travel_to_fallarbor". Live investigation
showed that's wrong — it's captured right after BADGE03_GET (Segment 9c), standing on
Wattson's platform INSIDE Mauville Gym, and Segments 10a (get HM06) / 10b (teach it) still
have to run before travel_to_fallarbor starts. Driving those two segments' real generators
from wattson_done.ss1 hit TWO separate confounds unrelated to this hypothesis:
  1. Generic `calculate_path` cannot leave the gym at all (static ROM layout still shows
     the maze sealed post-badge; the codebase already has a dedicated fix for this,
     `_exit_mauville_gym_live()`, early_game.py:3733) — resolved by calling that real
     function first.
  2. `get_rock_smash_hm()`'s closing `_exit_small_interior()` then failed to leave the
     Rock Smash Guy's house ("Could not exit the interior through any of its door warps")
     for a reason that needs its own separate investigation — NOT part of this hypothesis.
Rather than debug an unrelated pathing gap to manufacture a starting position, this repro
uses `saves/rocksmash_taught.ss1` instead: verified live (HM06 received, BADGE03_GET,
party knows Rock Smash, standing at MAUVILLE_CITY (32,15) — right outside the Rock Smash
house, i.e. exactly the state travel_to_fallarbor actually starts from). KI-16's own
notes independently call this "a nearer post-Wattson checkpoint" that "travels the same
code cleanly end-to-end". No production code was touched to make this substitution.

Because the wild-encounter roll is RNG-gated and the save/emulator are fully
deterministic, replaying byte-identical input from the SAME save state draws the SAME
roll every time. To get a genuine multi-attempt sweep we perturb the RNG stream between
attempts by varying an idle-frame count (no input) run immediately after loading the
save, before any smash call.

Run: py -3.12 tools/story-dev/repro_smashrock_battle_wedge.py
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "sandbox-pokebot"))

SAVE = _REPO / "tools" / "story-dev" / "saves" / "rocksmash_taught.ss1"
MAX_ATTEMPTS = 12
SMASH_CAP_FRAMES = 400_000  # safety bound for the smash-driving phase (per instructions)
POST_BATTLE_WATCH_FRAMES = 20_000  # the decisive zero-input observation window


def boot(idle_frames):
    from modules.context import context
    from modules.profiles import load_profile_by_name
    from modules.game import set_rom

    profile = load_profile_by_name("repro-fresh")
    context.profile = profile
    context.config.load(profile.path, strict=False)
    set_rom(profile.rom)

    from modules.libmgba import LibmgbaEmulator

    context.emulator = LibmgbaEmulator(profile, lambda: None)
    context.audio = False
    context.video = False
    context.emulation_speed = 0
    context.bot_mode = "Story"
    context.emulator.load_save_state(SAVE.read_bytes())
    for _ in range(idle_frames):
        context.emulator.run_single_frame()
    return context


def run_attempt(attempt_idx, idle_frames):
    print(f"\n{'=' * 78}")
    print(f"ATTEMPT {attempt_idx + 1}/{MAX_ATTEMPTS}  (RNG-perturbation idle_frames={idle_frames})")
    print("=" * 78)
    context = boot(idle_frames)

    from modules.map_data import MapRSE
    from modules.story.early_game import _smash_rock, wait_until_truly_controllable
    from modules.tasks import get_global_script_context
    from modules.battle_state import battle_is_active, get_last_battle_outcome

    settle = wait_until_truly_controllable()
    try:
        while True:
            next(settle)
            context.emulator.run_single_frame()
    except StopIteration:
        pass

    calls = [
        (MapRSE.ROUTE111, (18, 102), "Up"),
        (MapRSE.ROUTE111, (19, 101), "Up"),
    ]

    state = {"frame": 0, "battle_active": None, "script_active": None, "stack": None}
    saw_battle = False
    battle_ended_frame = None

    def note(tag):
        ba = battle_is_active()
        try:
            sc = get_global_script_context()
            sa = sc.is_active
            stack = sc.stack
        except Exception as e:  # pragma: no cover - defensive only
            sa, stack = None, f"<err {e}>"
        if ba != state["battle_active"] or sa != state["script_active"] or stack != state["stack"]:
            print(f"  f{state['frame']:>7} {tag:22} battle_active={ba!s:<5} "
                  f"script_active={sa!s:<5} stack={stack}")
            state["battle_active"], state["script_active"], state["stack"] = ba, sa, stack
        return ba, sa, stack

    for map_enum, tile, face in calls:
        gen = _smash_rock(map_enum, tile, face)
        try:
            while state["frame"] < SMASH_CAP_FRAMES:
                next(gen)
                context.emulator.run_single_frame()
                state["frame"] += 1
                ba, sa, stack = note(f"smash{tile}")
                if ba:
                    saw_battle = True
                if saw_battle and not ba and battle_ended_frame is None:
                    battle_ended_frame = state["frame"]
        except StopIteration:
            print(f"  f{state['frame']:>7} _smash_rock{tile} returned (StopIteration)")
        except Exception as e:
            print(f"  f{state['frame']:>7} _smash_rock{tile} raised {type(e).__name__}: {e}")
        if saw_battle:
            break

    if not saw_battle:
        print(f"  -- no battle observed this attempt (ended at frame {state['frame']}) --")
        return None

    print(f"\n  -- battle-during-smash observed (ended ~f{battle_ended_frame}); now watching "
          f"{POST_BATTLE_WATCH_FRAMES} frames with ZERO input (no button presses at all) --")
    cleared_at = None
    for _ in range(POST_BATTLE_WATCH_FRAMES):
        context.emulator.run_single_frame()
        state["frame"] += 1
        ba, sa, stack = note("post-battle-watch(0-input)")
        if sa is False and cleared_at is None:
            cleared_at = state["frame"]

    try:
        outcome = get_last_battle_outcome()
    except Exception as e:
        outcome = f"<err {e}>"

    return {
        "attempt": attempt_idx + 1,
        "battle_ended_frame": battle_ended_frame,
        "cleared_at": cleared_at,
        "final_is_active": state["script_active"],
        "final_stack": state["stack"],
        "outcome": outcome,
    }


# ===========================================================================
# PART 2 (coordinator follow-up, 2026-07-24): the 5/12 DETERMINISTIC
# `ensure_facing_direction` wedge — NOT the RNG battle roll. Chase it: correlate
# which idle-frame perturbations fail, capture full state the MOMENT
# ensure_facing_direction gives up (before _navigate_riding_out's retry loop
# swallows it), idle 20,000 zero-input frames from there, and save a .ss1 of
# the exact wedge so it becomes an instant repro forever after.
#
# Technique: wrap the REAL `ensure_facing_direction` generator (imported from
# modules.modes.util.walking) so every frame it yields still passes straight
# through unmodified — the wrapper only OBSERVES and, if the wrapped generator
# raises the specific timeout BotModeError, captures a full state dump before
# re-raising the SAME exception unchanged. This changes no behavior (a spy, not
# a fault injection) and touches no file on disk — only the in-memory function
# reference in this script's own process, exactly like the fault-injection
# repros patch readers.
# ===========================================================================
WEDGE_SAVE_PATH = _REPO / "tools" / "story-dev" / "saves" / "r111_facing_wedge.ss1"
WEDGE_WATCH_FRAMES = 20_000


class _WedgeCaptured(Exception):
    """Sentinel: raised after a successful capture + 20k-frame watch + save, so
    it propagates straight out of _navigate_riding_out's `except BotModeError`
    retry loop (this is NOT a BotModeError) instead of being swallowed."""


def _capture_state(context, tag):
    from modules.tasks import get_global_script_context, get_tasks
    from modules.player import get_player_avatar
    from modules.battle_state import battle_is_active

    d = {"tag": tag}
    try:
        d["frame"] = context.emulator.get_frame_count()
    except Exception as e:
        d["frame"] = f"<err {e}>"
    try:
        sc = get_global_script_context()
        d["script_active"] = sc.is_active
        d["script_stack"] = list(sc.stack or [])
    except Exception as e:
        d["script_active"] = f"<err {e}>"
        d["script_stack"] = []
    try:
        d["tasks"] = [getattr(t, "symbol", getattr(t, "name", "?")) for t in get_tasks()]
    except Exception as e:
        d["tasks"] = f"<err {e}>"
    try:
        pa = get_player_avatar()
        d["map"] = pa.map_group_and_number
        d["coords"] = tuple(pa.local_coordinates)
        d["facing"] = pa.facing_direction
        d["running_state"] = pa.running_state.name
        d["tile_transition_state"] = pa.tile_transition_state.name
    except Exception as e:
        d["avatar_err"] = str(e)
    try:
        d["battle_active"] = battle_is_active()
    except Exception as e:
        d["battle_active"] = f"<err {e}>"
    held = []
    for b in ("A", "B", "Up", "Down", "Left", "Right", "Start", "Select", "L", "R"):
        try:
            if context.emulator.is_button_held(b):
                held.append(b)
        except Exception:
            pass
    d["held_buttons"] = held
    return d


def _print_dump(d, label):
    print(f"  --- {label} ---")
    for k in ("tag", "frame", "map", "coords", "facing", "running_state",
              "tile_transition_state", "battle_active", "held_buttons",
              "script_active", "script_stack", "tasks"):
        if k in d:
            print(f"    {k:24} = {d[k]}")
    if "avatar_err" in d:
        print(f"    avatar_err               = {d['avatar_err']}")


def run_facing_wedge_investigation(idle_frames_list):
    """Drive the smash calls with a spy on ensure_facing_direction; on the FIRST
    timeout-wedge raise, capture state, idle WEDGE_WATCH_FRAMES with zero input,
    save a .ss1, and stop. Also reports, per idle_frames tried, whether it wedged
    or completed cleanly (the requested failing-vs-clean correlation)."""
    from modules.modes.util import walking
    from modules.modes._interface import BotModeError

    _orig_efd = walking.ensure_facing_direction
    capture_box = {}

    def _spy_efd(facing_direction, *a, **kw):
        gen = _orig_efd(facing_direction, *a, **kw)
        while True:
            try:
                val = next(gen)
            except StopIteration:
                return
            except BotModeError as e:
                if "ensure_facing_direction: could not face" in str(e) and "captured" not in capture_box:
                    from modules.context import context as _ctx

                    print(f"\n  !!! WEDGE HIT: target facing={facing_direction!r}  error={e}")
                    dump_at_wedge = _capture_state(_ctx, "AT-WEDGE (ensure_facing_direction gave up)")
                    _print_dump(dump_at_wedge, "STATE AT THE MOMENT ensure_facing_direction GAVE UP")

                    print(f"\n  -- idling {WEDGE_WATCH_FRAMES} frames with ZERO input from this exact state --")
                    cleared_at = None
                    facing_changed_at = None
                    start_facing = dump_at_wedge.get("facing")
                    start_frame = dump_at_wedge.get("frame")
                    last = dict(dump_at_wedge)
                    for i in range(WEDGE_WATCH_FRAMES):
                        _ctx.emulator.run_single_frame()
                        cur = _capture_state(_ctx, f"watch+{i + 1}")
                        if cur.get("script_active") != last.get("script_active") or \
                           cur.get("script_stack") != last.get("script_stack") or \
                           cur.get("facing") != last.get("facing") or \
                           cur.get("running_state") != last.get("running_state") or \
                           cur.get("tile_transition_state") != last.get("tile_transition_state"):
                            print(f"    f{cur.get('frame')} CHANGE: script_active={cur.get('script_active')} "
                                  f"stack={cur.get('script_stack')} facing={cur.get('facing')} "
                                  f"running={cur.get('running_state')} tile_transition={cur.get('tile_transition_state')}")
                            last = cur
                        if cur.get("script_active") is False and cleared_at is None:
                            cleared_at = cur.get("frame")
                        if cur.get("facing") != start_facing and facing_changed_at is None:
                            facing_changed_at = cur.get("frame")

                    print(f"\n  -- watch complete: script is_active ever False during watch: "
                          f"{'YES at f' + str(cleared_at) if cleared_at is not None else 'NO (never cleared)'}")
                    print(f"  -- facing ever changed on its own (0 input): "
                          f"{'YES at f' + str(facing_changed_at) if facing_changed_at is not None else 'NO (frozen)'}")

                    WEDGE_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
                    state_bytes = _ctx.emulator.get_save_state()
                    WEDGE_SAVE_PATH.write_bytes(state_bytes)
                    print(f"\n  -- saved wedge state to {WEDGE_SAVE_PATH} --")

                    capture_box["captured"] = {
                        "dump_at_wedge": dump_at_wedge,
                        "cleared_at": cleared_at,
                        "facing_changed_at": facing_changed_at,
                        "target_facing": facing_direction,
                    }
                    raise _WedgeCaptured("captured — stopping this attempt")
                raise
            yield val

    walking.ensure_facing_direction = _spy_efd
    # early_game.py imports ensure_facing_direction by NAME at module load time
    # (`from modules.modes.util.walking import ..., ensure_facing_direction, ...`),
    # so the call sites inside _navigate_riding_out's dependency chain resolve
    # through early_game's OWN module-level binding, not walking's — patch that
    # binding too (still just an in-memory spy, no file touched).
    from modules.story import early_game as _eg

    if hasattr(_eg, "ensure_facing_direction"):
        _eg.ensure_facing_direction = _spy_efd

    from modules.map_data import MapRSE
    from modules.story.early_game import _smash_rock, wait_until_truly_controllable

    results = []
    for idle_frames in idle_frames_list:
        print(f"\n{'=' * 78}")
        print(f"FACING-WEDGE PASS  idle_frames={idle_frames}")
        print("=" * 78)
        context = boot(idle_frames)
        settle = wait_until_truly_controllable()
        try:
            while True:
                next(settle)
                context.emulator.run_single_frame()
        except StopIteration:
            pass

        calls = [
            (MapRSE.ROUTE111, (18, 102), "Up"),
            (MapRSE.ROUTE111, (19, 101), "Up"),
        ]
        outcome = "clean"
        frame = 0
        for map_enum, tile, face in calls:
            gen = _smash_rock(map_enum, tile, face)
            try:
                while frame < SMASH_CAP_FRAMES:
                    next(gen)
                    context.emulator.run_single_frame()
                    frame += 1
            except StopIteration:
                pass
            except _WedgeCaptured:
                outcome = "WEDGED (captured)"
                break
            except Exception as e:
                outcome = f"other raise: {type(e).__name__}: {e}"
                break
            if outcome != "clean":
                break
        print(f"  RESULT idle_frames={idle_frames}: {outcome}")
        results.append((idle_frames, outcome))
        # Keep testing ALL idle_frames values for the clean-vs-wedged correlation
        # (coordinator's ask #1) — the expensive dump+20k-watch+save only ever runs
        # ONCE (guarded by "captured" not in capture_box inside the spy), so repeat
        # wedges after the first just surface as a bare re-raise here (cheap).

    walking.ensure_facing_direction = _orig_efd
    if hasattr(_eg, "ensure_facing_direction"):
        _eg.ensure_facing_direction = _orig_efd
    return results, capture_box.get("captured")


if __name__ == "__main__" and "--facing-wedge" in sys.argv:
    # Reuses rocksmash_taught.ss1 and the SAME idle-frame values already measured
    # in the battle-encounter sweep above: attempts 1-12 there used
    # idle = 20 + i*733 for i in 0..11 -> 20,753,1486,2219,2952,3685,4418,5151,
    # 5884,6617,7350,8083. Reported failures were i=1,3,4,6,7 (idle=753,2219,
    # 2952,4418,5151); reported clean were i=0,2,5,8,9,10,11 (idle=20,1486,3685,
    # 5884,6617,7350,8083). Re-test ALL of them here with the spy installed so the
    # correlation is measured directly (not just recalled) and the first wedge is
    # captured immediately.
    idle_values = [20 + i * 733 for i in range(MAX_ATTEMPTS)]
    results, captured = run_facing_wedge_investigation(idle_values)

    print("\n" + "#" * 78)
    print("PER-IDLE-FRAME OUTCOME:")
    for idle_frames, outcome in results:
        print(f"  idle_frames={idle_frames:>6}  ->  {outcome}")

    if captured is None:
        print("\nNo wedge captured across the tried idle_frames values (unexpected — "
              "the earlier sweep saw 5/12 fail).")
    else:
        print(f"\nWEDGE CAPTURED. target_facing={captured['target_facing']!r}")
        print(f"is_active ever cleared during {WEDGE_WATCH_FRAMES}-frame zero-input watch: "
              f"{captured['cleared_at'] is not None} (frame={captured['cleared_at']})")
        print(f"facing ever changed on its own: "
              f"{captured['facing_changed_at'] is not None} (frame={captured['facing_changed_at']})")
        print(f"Saved state: {WEDGE_SAVE_PATH}")
    sys.exit(0)


result = None
for i in range(MAX_ATTEMPTS):
    idle = 20 + i * 733  # perturbs the RNG stream vs. a byte-identical replay
    try:
        result = run_attempt(i, idle)
    except Exception as e:
        print(f"  ATTEMPT {i + 1} raised at driver level: {type(e).__name__}: {e}")
        result = None
    if result is not None:
        break

print("\n" + "#" * 78)
if result is None:
    print(f"INCONCLUSIVE: no battle-during-smash fired in {MAX_ATTEMPTS} attempts.")
else:
    print(f"Battle-during-smash on attempt #{result['attempt']} "
          f"(outcome={result['outcome']}); battle ended ~f{result['battle_ended_frame']}.")
    if result["cleared_at"] is not None:
        n = result["cleared_at"] - result["battle_ended_frame"]
        print(f"REFUTED: is_active CLEARED on its own at f{result['cleared_at']} "
              f"(~{n} frames after battle end), zero input, script stack now {result['final_stack']}.")
    else:
        print(f"CONFIRMED: is_active NEVER cleared across {POST_BATTLE_WATCH_FRAMES} zero-input "
              f"frames after the battle ended. final is_active={result['final_is_active']} "
              f"stack={result['final_stack']}")
