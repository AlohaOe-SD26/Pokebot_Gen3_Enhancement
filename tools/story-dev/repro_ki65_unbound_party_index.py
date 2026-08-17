"""REPRO + GATE for KI-65 -- the compounding silence in `handle_move_replacement_dialogue`.

WHAT THIS PROVES
================
`party_index` is assigned at EXACTLY ONE place in that generator's scope
(`battle_move_replacing.py:371`, inside a `try`). When `_read_offered_move` raises, the
name stays unbound, and two later reads of it each sit inside a swallowing `except`:

  * `:397` -- the HM VETO, `except Exception: pass` (`:433-434`)
  * `:280` -- the CantForgetHM re-pick, `except Exception:` -> decline (`:290-291`)

The veto's own comment calls it "THE LAST LINE OF DEFENCE" and names the exact path it
must cover -- "the `except` fallback right above which blindly picks slot 0 without
consulting any policy at all" (`:390-391`). That fallback (`:377-381`) is PRECISELY the
path that leaves `party_index` unbound. So the veto raises `UnboundLocalError` into
`pass` and FAILS OPEN on the one case it was written for, and the bot confirms slot 0
with zero policy input. If slot 0 holds an HM the game refuses, `:280` then raises too,
and the bot prints a message that is a PROVABLE LIE.

!! WHY THE OBVIOUS FIXTURE DOES NOT WORK -- MEASURED 2026-08-16, DO NOT RETRY IT
================================================================================
KI-65's RECON block prescribed `saves/movelearn_hmwedge_quickattack.ss1`. **That fixture
cannot test this bug at all**, for three independent reasons, each measured:

 1. `:280` IS UNREACHABLE THERE. With `party_index` unbound, enumerate every assignment
    of `move_to_forget`: `:176` (4), `:285-289` (needs `party_index`, raises first),
    `:291` (4), `:373` (unreachable, `:371` raised), `:381` (0), `:432` (dead, `:397`
    raised first). **Only 0 and 4 are reachable.** That fixture's slot 0 is Scratch, not
    an HM, so the game ACCEPTS it and `CantForgetHM` never re-fires.
    => `:280` needs a fixture whose **slot 0 itself holds an HM**. Hence the injection
    below puts the HM in slot 0 deliberately.
 2. THE OUTCOME IS DECIDED BEFORE THE BUG CAN MATTER. That save is parked INSIDE the
    `CantForgetHM` window, so branch (1) runs at f2 with the INITIAL `move_to_forget = 4`,
    walks the cursor to the cancel row and backs out at f12. Policy is first consulted at
    f37 -- 25 frames too late to matter. Measured button traces for fault-ON and
    fault-OFF are BYTE-IDENTICAL: `f0 A, f2 Down x5, f12 A x224`.
 3. FAULTING THE "MOST PLAUSIBLE REAL CAUSE" IS RESCUED. `_read_offered_move` has TWO
    paths: `:135-138` task-backed via `get_party_menu_cursor_pos`, and `:140-149` via
    `gBattleStruct` + `map_battle_party_index`. Only the second can raise. On that save
    the task-backed path succeeds and binds `party_index`, and a bound function-local
    stays bound for the rest of the generator's life -- so every later raise is inert.
    Measured: faulting only `map_battle_party_index` fired 51 times and changed nothing.

=> This repro therefore uses `saves/route116team.ss1`, which reaches
`AskWhetherToLearn` **without** a prior `CantForgetHM` (branch (2) runs FIRST, before
anything is confirmed), and injects the learner so slot 0 is the HM.

THE FAULT
=========
ARM A rebinds `bmr._read_offered_move` to raise. `:371` calls it by BARE NAME, so the
module global is the seam; no production edit is needed (same mechanism as
`repro_hm_replace_valve_forced.py:188`). This models the stated precondition -- "the
read fails". SCOPE, HONESTLY: it reproduces what happens WHEN that read fails; it does
not measure how often it fails in the wild. KI-65 is about the compounding silence.

THE DISCRIMINATOR (computed on THIS fixture, before it was built)
==================================================================
Injected learner: MARSHTOMP L30, 1 exp short of L31, slots
**0 = Rock Smash (HM06)**, 1 = Water Gun, 2 = Mud Shot, 3 = Bide -- so slot 0 is an HM
and THREE forgettable moves exist. It levels naturally in a wild battle and is offered a
move.

  ARM A (fault ON)  -- `:381` sets `move_to_forget = 0` -> `:397` veto raises into `pass`
       -> A confirms slot 0 -> the GAME REFUSES (it is an HM) -> `CantForgetHM` ->
       `last_confirmed_slot = 0` -> `:273` true -> **`:280` raises** -> `:291` sets 4 ->
       `:297` prints "Nothing else can be given up - declining the new move." **while
       Water Gun, Mud Shot and Bide are all forgettable. That message is a LIE**, and
       `:377-381` then re-arms `move_to_forget = 0` every cycle -> the ping-pong.
  ARM B (fault OFF) -- the read succeeds, policy runs, the veto works, and the dialogue
       resolves without ever printing that message.

PASS/FAIL (this is a GATE -- it encodes the POST-FIX expectation)
=================================================================
  ARM B (control, must be untouched by the fix): fault never installed/fired, dialogue
        RESOLVED, no lie.
  ARM A: the fault FIRED (>=1 -- a fault that never fired makes every later assertion
        vacuous), the dialogue RESOLVED (no wedge, no derail to Manual), the LIE was
        NOT printed, and a message naming the unverifiable read WAS printed.

  BEFORE the fix ARM A prints the lie and/or wedges  -> FAIL (RED).
  AFTER  the fix ARM A declines honestly and resolves -> PASS (GREEN).

This gate DRIVES the emulator; it never greps source, so it cannot be tripped by a mere
mention of a symbol in a comment or docstring.

‼ DETERMINISM, CHECKED (2026-08-16): each arm runs as its OWN subprocess and loads the save
fresh, so no emulator state leaks between them. Two consecutive full runs produced
IDENTICAL numbers in every field (`fault_fired=87` both times). If a future run disagrees,
suspect the fixture or the build before the bug.

‼ WHAT THE FIX IS, so this gate is not mistaken for guarding more than it does: the guard
that prevents the loop is the `party_index is None` check in the HM VETO. A third fix part
(an `offer_read_failed` latch in the `:377` handler) was built and then REMOVED after an
isolated A/B showed this gate passes identically without it. ⛔ Do not re-add it, and do not
"simplify" the veto guard on the assumption something else covers it.

RUN
===
  py -3.12 tools/story-dev/repro_ki65_unbound_party_index.py                # both arms
  py -3.12 tools/story-dev/repro_ki65_unbound_party_index.py --arm a
  py -3.12 tools/story-dev/repro_ki65_unbound_party_index.py --build custom
"""

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# The lie `:297` prints today, and the marker the FIXED guard must print instead. Kept as
# constants so the production strings and these assertions cannot drift apart silently.
LIE_MARKER = "Nothing else can be given up"
HONEST_MARKER = "cannot verify"

ap = argparse.ArgumentParser()
ap.add_argument("--arm", default=None, choices=["a", "b"], help="omit to run BOTH arms")
ap.add_argument("--frames", type=int, default=30000)
ap.add_argument("--build", default="sandbox", choices=["custom", "sandbox"])
ap.add_argument("--profile", default="repro-ki65")
ap.add_argument("--log", default=None)
args = ap.parse_args()

_REPO = Path(__file__).resolve().parents[2]
SCRATCH = Path(__file__).parent


# ---------------------------------------------------------------------------------
# ORCHESTRATOR: no --arm => run both arms as subprocesses and adjudicate.
# Each arm gets its OWN log path (#24-orphans (4): a shared log destroys arm 1).
# ---------------------------------------------------------------------------------
def _run_both() -> int:
    results = {}
    for arm in ("a", "b"):
        cmd = [
            sys.executable, str(Path(__file__).resolve()),
            "--arm", arm, "--build", args.build,
            "--frames", str(args.frames), "--profile", args.profile,
        ]
        print(f"\n{'=' * 86}\n[orchestrator] ARM {arm.upper()}\n{'=' * 86}")
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = proc.stdout.splitlines()
        print("\n".join(tail[-45:]))
        if proc.stderr.strip():
            print("[stderr]\n" + proc.stderr[-2000:])
        match = None
        for line in tail:
            if line.startswith("RESULT "):
                match = line
        results[arm] = (
            dict(kv.split("=", 1) for kv in match.split()[1:]) if match else None
        )
        if match is None:
            print(f"[orchestrator] ARM {arm.upper()} produced NO RESULT line (exit={proc.returncode})")

    print("\n" + "=" * 86)
    print("[orchestrator] ADJUDICATION")
    print("=" * 86)
    a, b = results.get("a"), results.get("b")
    if a is None or b is None:
        print("‼ an arm did not report -- cannot adjudicate")
        print("ACCEPTANCE: FAIL")
        return 1

    for arm, res in (("A", a), ("B", b)):
        print(f"  ARM {arm}: " + "  ".join(f"{k}={v}" for k, v in res.items()))

    checks: list[tuple[str, bool, str]] = []
    # -- fixture controls: if these fail nothing downstream means anything ---------
    for arm, res in (("A", a), ("B", b)):
        checks.append((f"{arm}: fixture built -- slot 0 IS an HM", res["slot0_hm"] == "1", res["slot0_hm"]))
        checks.append((f"{arm}: fixture has forgettable moves", int(res["forgettable"]) >= 1, res["forgettable"]))
        checks.append((f"{arm}: the move-learn offer was REACHED", res["offer_seen"] == "1", res["offer_seen"]))

    # -- ARM B is the CONTROL. The fix must not touch it. --------------------------
    checks.append(("B: fault was never installed", b["fault_installed"] == "0", b["fault_installed"]))
    checks.append(("B: fault never fired", b["fault_fired"] == "0", b["fault_fired"]))
    checks.append(("B: dialogue RESOLVED", b["verdict"] == "RESOLVED", b["verdict"]))
    checks.append(("B: never printed the lie", b["lie_msg"] == "0", b["lie_msg"]))

    # -- ARM A is the subject. LIVENESS FIRST. ------------------------------------
    checks.append(("A: fault was installed", a["fault_installed"] == "1", a["fault_installed"]))
    checks.append(("A: fault ACTUALLY FIRED (>=1 raise)", int(a["fault_fired"]) >= 1, a["fault_fired"]))
    checks.append(("A: dialogue RESOLVED (no wedge)", a["verdict"] == "RESOLVED", a["verdict"]))
    checks.append(("A: run did NOT derail to Manual", a["derailed"] == "0", a["derailed"]))
    checks.append((f"A: did NOT print the lie ({LIE_MARKER!r})", a["lie_msg"] == "0", a["lie_msg"]))
    checks.append(
        (f"A: printed an honest message ({HONEST_MARKER!r})", a["honest_msg"] == "1", a["honest_msg"])
    )

    ok = True
    for label, passed, observed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}   (observed: {observed})")
        ok &= passed

    print("=" * 86)
    print(f"ACCEPTANCE: {'PASS' if ok else 'FAIL'}")
    print("=" * 86)
    if not ok and (a["lie_msg"] == "1" or a["verdict"] != "RESOLVED"):
        print(
            "\nThat is KI-65 REPRODUCED: `_read_offered_move` failed, the HM veto could not\n"
            "read the party and swallowed the UnboundLocalError, the bot confirmed the HM in\n"
            "slot 0, the game refused it, and `:280` raised into the `except` that prints\n"
            f"{LIE_MARKER!r} -- while three forgettable moves existed."
        )
    return 0 if ok else 1


if args.arm is None:
    sys.exit(_run_both())


# ---------------------------------------------------------------------------------
# SINGLE ARM
# ---------------------------------------------------------------------------------
BUILD = _REPO / f"{args.build}-pokebot"
sys.path.insert(0, str(BUILD))
SAVES = SCRATCH / "saves"
LOG = Path(args.log) if args.log else SCRATCH / f"repro_ki65_{args.build}_arm{args.arm}.log"

state_path = SAVES / "route116team.ss1"
assert state_path.is_file(), f"missing {state_path}"

logf = open(LOG, "w", encoding="utf-8")


def log(msg):
    logf.write(msg + "\n")
    logf.flush()
    print(msg)


log(f"[setup] LOG -> {LOG}")

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

from modules.memory import get_game_state, read_symbol, get_event_flag, set_event_flag
from modules.modes import FrameInfo, get_bot_listeners, get_bot_mode_by_name, BotModeError, BotMode
from modules.plugins import load_plugins, load_built_in_plugins, plugin_profile_loaded
from modules.state_cache import state_cache
from modules.stats import StatsDatabase
from modules.tasks import get_global_script_context, get_tasks
from modules.battle_state import battle_is_active
from modules.pokemon_party import get_party
from modules.game import decode_string
import modules.battle_move_replacing as bmr

load_plugins()
load_built_in_plugins()
plugin_profile_loaded(context.profile)
context.stats = StatsDatabase(context.profile)
context.bot_listeners = get_bot_listeners(context.rom)
assert get_bot_mode_by_name("Story") is not None, "Story mode did not register"

log(f"[setup] loaded {state_path.name} (build={args.build}) ARM {args.arm.upper()}")
log(f"[setup] battle.new_move config = {context.config.battle.new_move!r}")

set_event_flag("BADGE01_GET", True)
log("[setup] STATE-WRITE: forced BADGE01_GET=True (route116team.ss1 is otherwise pre-gym-1)")

# ---- inject the learner: the HM goes in SLOT 0, which is what makes `:280` reachable
from modules.debug_utilities import debug_create_pokemon, debug_write_party
from modules.pokemon import get_species_by_name, get_move_by_name, LearnedMove

marshtomp_species = get_species_by_name("Marshtomp")
exp31 = marshtomp_species.level_up_type.get_experience_needed_for_level(31)
marshtomp = debug_create_pokemon(
    species=marshtomp_species, level=30, experience=exp31 - 1,
    moves=[
        LearnedMove.create(get_move_by_name("Rock Smash")),  # HM06 -- SLOT 0 ON PURPOSE
        LearnedMove.create(get_move_by_name("Water Gun")),
        LearnedMove.create(get_move_by_name("Mud Shot")),
        LearnedMove.create(get_move_by_name("Bide")),
    ],
    nickname="MARSHTOMP", current_hp=None,
)
filler = [
    debug_create_pokemon(species=get_species_by_name(name), level=lvl,
                         moves=[LearnedMove.create(get_move_by_name("Tackle"))], nickname=name.upper())
    for name, lvl in (("Linoone", 26), ("Shroomish", 21), ("Loudred", 21))
]
debug_write_party([marshtomp, *filler])
log(f"[inject] Marshtomp L30 exp={exp31 - 1} (exp_for_31={exp31}); "
    "slot 0 = Rock Smash (HM06) DELIBERATELY, then Water Gun / Mud Shot / Bide")


def _is_hm_slot(slot) -> bool:
    m = slot.move if slot is not None else None
    return m is not None and m.tm_hm is not None and m.tm_hm.name.startswith("HM")


# ---- CONTROL: read the fixture BACK through the PRODUCTION reader ----------------
# (playbook 0b Q6: does the fixture actually create its condition? A bad fixture is
# indistinguishable from the fault's expected effect.)
learner = get_party()[0]
slots = learner.moves
slot0_hm = _is_hm_slot(slots[0])
forgettable = sum(1 for s in slots if s is not None and not _is_hm_slot(s))
log(f"[control] read back via get_party(): {learner.species.name} L{learner.level} slots="
    + ", ".join(f"{i}:{(s.move.name + ('[HM]' if _is_hm_slot(s) else '')) if s else '-'}"
                for i, s in enumerate(slots)))
log(f"[control] slot0_is_hm={slot0_hm}  forgettable_moves={forgettable}  "
    f"-> `:280` is reachable on this fixture: {slot0_hm and forgettable >= 1}")

# ---- THE FAULT (ARM A only) ------------------------------------------------------
_fault = {"installed": 0, "fired": 0}

if args.arm == "a":
    def _faulted_read(*a, **kw):
        _fault["fired"] += 1
        raise RuntimeError(
            "INJECTED (KI-65): _read_offered_move failed -- the precondition KI-65 "
            "describes. `party_index` is assigned ONLY here (:371), so it stays unbound."
        )

    bmr._read_offered_move = _faulted_read
    _fault["installed"] = 1
    log("[fault] ARM A: bmr._read_offered_move rebound -> always raises "
        "(:371 calls it by bare name, so the module global is the seam)")
else:
    log("[fault] ARM B: no fault installed (control arm)")

# ---- instrumentation -------------------------------------------------------------
_messages: list[str] = []
_buttons: Counter = Counter()
_frame_now = {"f": 0}
_orig_press = context.emulator.press_button


def _recording_press(button):
    _buttons[button] += 1
    return _orig_press(button)


context.emulator.press_button = _recording_press


_seen_messages: set[str] = set()


def _poll_message():
    """Record each DISTINCT message once. Dedupe on the TEXT, not on a frame-stamped
    string -- the encounter banner repeats every frame and would otherwise bury the two
    messages this gate actually grades on."""
    try:
        m = context.message
    except Exception:
        return
    if m and m not in _seen_messages:
        _seen_messages.add(m)
        _messages.append(f"f{_frame_now['f']}: " + " / ".join(m.splitlines()))


def _battle_text() -> str:
    try:
        return decode_string(read_symbol("gDisplayedStringBattle"))
    except Exception:
        return ""


def _moveset_sig() -> str:
    try:
        return ",".join((s.move.name if s is not None else "-") for s in get_party()[0].moves)
    except Exception:
        return "<unreadable>"


from plugins.custom_modes.story_mode import StoryMode


class Ki65Mode(BotMode):
    """Walks in the grass until a wild battle levels Marshtomp -- the REAL StoryMode
    battle routing decides the strategy, so the offer is reached organically."""

    @staticmethod
    def name():
        return "Ki65"

    def on_battle_started(self, encounter):
        shim = SimpleNamespace(_catch_team_target=4)
        shim._should_catch = lambda enc: StoryMode._should_catch(shim, enc)
        return StoryMode.on_battle_started(shim, encounter)

    def run(self):
        seq = ["Up", "Up", "Down", "Down", "Left", "Left", "Right", "Right"]
        i = 0
        while True:
            context.emulator.press_button(seq[(i // 6) % len(seq)])
            yield
            i += 1


context.bot_mode_instance = None
context.controller_stack = []

sig_before = _moveset_sig()
log(f"[setup] moveset BEFORE = {sig_before}")
log(f"[run] driving the faithful loop for up to {args.frames} frames")

previous_frame_info = None
verdict = "UNKNOWN"
detail = ""
derailed = 0
offer_seen = 0
offer_frame = None
window_open = False
resolved_at = None

for step in range(args.frames):
    context.frame = step
    _frame_now["f"] = step
    _poll_message()

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
        if not derailed:
            derailed = 1
            log(f"f{step}: *** DERAILED TO MANUAL *** (a silent decline is not supposed to do this)")

        class _Manual:
            @staticmethod
            def name():
                return "Manual"

            def run(self):
                yield

        context.bot_mode_instance = _Manual()
    elif len(context.controller_stack) == 0:
        context.bot_mode_instance = Ki65Mode()
        context.controller_stack.append(context.bot_mode_instance.run())

    # --- has the move-learn offer been reached? (liveness: playbook 0b Q4) --------
    ba = battle_is_active()
    ml_open = False
    if ba:
        try:
            ml_open = bmr.get_learn_move_state() != bmr.LearnMoveState.DialogueNotActive
        except Exception:
            ml_open = False
    ml_open = ml_open or any(
        p in _battle_text() for p in ("trying to learn", "make room for", "Delete a move", "wants to learn")
    )
    if ml_open and not window_open:
        window_open = True
        offer_seen = 1
        if offer_frame is None:
            offer_frame = step
            log(f"f{step}: === MOVE-LEARN WINDOW OPEN === moveset={_moveset_sig()} bt={_battle_text()!r}")
    if window_open and not ml_open:
        window_open = False
        resolved_at = step
        log(f"f{step}: === window closed === moveset={_moveset_sig()}")
        verdict = "RESOLVED"
        detail = f"offer at f{offer_frame}, dialogue closed at f{step}"
        break

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
        verdict = "WEDGED"
        detail = f"BotModeError at f{step}: {e}"
        log(f"f{step}: *** BotModeError: {e}")
        break
    except Exception as e:
        import traceback

        verdict = "ERROR"
        detail = f"{type(e).__name__} at f{step}: {e}"
        log(f"f{step}: *** EXCEPTION\n{traceback.format_exc()}")
        break

    previous_frame_info = frame_info
    context.emulator.run_single_frame()
else:
    verdict = "WEDGED" if offer_seen else "NO_OFFER"
    detail = f"frame budget {args.frames} exhausted (offer_seen={offer_seen})"

_poll_message()
sig_after = _moveset_sig()
lie = any(LIE_MARKER.lower() in m.lower() for m in _messages)
honest = any(HONEST_MARKER.lower() in m.lower() for m in _messages)

log("")
log("=" * 78)
log(f"[result] ARM {args.arm.upper()}  VERDICT = {verdict}")
log(f"[result] {detail}")
log(f"[result] fault installed={_fault['installed']} fired={_fault['fired']}")
log(f"[result] derailed_to_manual = {bool(derailed)}")
log(f"[result] moveset BEFORE = {sig_before}")
log(f"[result] moveset AFTER  = {sig_after}")
log(f"[result] buttons pressed = {dict(_buttons)}")
log(f"[result] messages ({len(_messages)}):")
for m in _messages:
    log(f"[result]   - {m}")
log(f"[result] printed the LIE ({LIE_MARKER!r}) = {lie}")
log(f"[result] printed an HONEST message ({HONEST_MARKER!r}) = {honest}")
log("=" * 78)

result_line = (
    f"RESULT arm={args.arm} build={args.build} slot0_hm={int(slot0_hm)} "
    f"forgettable={forgettable} offer_seen={offer_seen} "
    f"fault_installed={_fault['installed']} fault_fired={_fault['fired']} "
    f"verdict={verdict} derailed={derailed} "
    f"moveset_changed={int(sig_before != sig_after)} "
    f"lie_msg={int(lie)} honest_msg={int(honest)}"
)
log(result_line)
logf.close()

# A single arm never adjudicates -- the orchestrator does. Exit non-zero only if the arm
# could not run its experiment at all, so a RED subject arm still reports its numbers.
sys.exit(0 if (slot0_hm and offer_seen) else 1)
