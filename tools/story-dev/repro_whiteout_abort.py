"""REPRO — a whiteout abort must NEVER be swallowed by a chapter's own retry loop (KI-67).

‼‼ THE BUG. The story bot signals a whiteout with an abort LATCH: `StoryMode.on_whiteout` calls
`set_story_abort(True)`, `_check_abort()` raises inside whatever wait loop is running, and **only
`StoryMode.run` ever clears the latch**. But chapters carry their own 3-attempt retry loops —
deliberately, because losing a gym fight is an EXPECTED outcome and the recovery is "re-enter and
re-solve" — and those loops caught `BotModeError`, which is what `_check_abort()` raised.

So a chapter that caught the abort and retried IN PLACE ran straight into the next `_check_abort()`
and died instantly. **One whiteout consumed all three attempts in a handful of frames**, and the
chapter reported three failures, two of which never happened.

‼ AND NO DRIVER COULD SEE IT. `set_story_abort` appears ZERO times in `story_harness.py`, so every
driver's `on_whiteout` only increments a counter and `_check_abort()` is effectively dead code under
test. Every retry-path docstring in this project was therefore untested prose.

THE FIX. `_check_abort()` now raises **`StoryAbort`**, a subclass of `BotModeError`, and the chapter
retry loops re-raise it explicitly. Subclassing is the point: everything that already catches
`BotModeError` keeps catching this unchanged, so the ONLY behaviour that moves is at the call sites
that opt in. ‼ Re-raising is not "giving up on the retry" — it hands the retry to the one layer that
can perform it. `StoryMode.run` clears the latch, waits out the respawn, steps out of the Pokémon
Center and re-runs `_play()`, which re-enters the (resume-safe) chapter. That recovery is bounded
at 40 consecutive whiteouts.

WHAT THIS PROVES, WITHOUT AN EMULATOR:
  1. the mechanism — the latch really does produce a `StoryAbort`, and it really is a `BotModeError`
     (so nothing that catches the old type is broken);
  2. an A/B on the LOOP SHAPE — the old `except BotModeError` swallows it and burns every attempt,
     the new `except StoryAbort: raise` does not. ARM A is the positive control;
  3. structurally, that every chapter retry loop in the tree actually carries the guard — because a
     fix applied to the two chapters I happened to be looking at is not a fix.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_whiteout_abort.py
"""

import pathlib
import re
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

BAR = "=" * 96
results = []


def check(label, ok, detail=""):
    results.append((label, ok))
    print(f"  {'[AS PREDICTED]' if ok else '[‼ FAIL]'} {label}")
    if detail:
        print(f"        {detail}")


# ---------------------------------------------------------------------------------------------
print(BAR)
print("REPRO — KI-67: the whiteout abort must escape a chapter's retry loop")
print(BAR)

print(f"\n{BAR}\n1 — THE MECHANISM: the latch produces a StoryAbort, and it IS a BotModeError\n{BAR}\n")

from modules.modes import BotModeError  # noqa: E402
from modules.story.early_game import (  # noqa: E402
    StoryAbort,
    _check_abort,
    set_story_abort,
    story_should_abort,
)

check("StoryAbort subclasses BotModeError (so existing handlers are unaffected)",
      issubclass(StoryAbort, BotModeError))

set_story_abort(False)
try:
    _check_abort()
    quiet = True
except BaseException as error:  # noqa: BLE001
    quiet = False
    print(f"        raised {type(error).__name__} with the latch CLEAR")
check("with the latch clear, _check_abort() does nothing", quiet)

set_story_abort(True)
raised = None
try:
    _check_abort()
except BaseException as error:  # noqa: BLE001
    raised = error
check("with the latch set, _check_abort() raises StoryAbort",
      isinstance(raised, StoryAbort),
      f"raised {type(raised).__name__ if raised else '<nothing>'}")
check("story_should_abort() agrees with the latch", story_should_abort() is True)
set_story_abort(False)

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n2 — THE A/B on the LOOP SHAPE. ARM A is the control: it MUST burn all 3 attempts.\n{BAR}\n")

# ‼ These two functions are the retry loops, reduced to their essential shape. The point of ARM A
# is that it is not a straw man — it is what `do_space_center_chapter` and `do_mossdeep_gym_chapter`
# literally did, and it fails in the way the field reports describe: three attempts, in no time,
# with two invented failure reasons.
ATTEMPTS = 3


def old_loop():
    """`except BotModeError` only — swallows the abort and retries into a set latch."""
    tried, reasons = 0, []
    for attempt in range(1, ATTEMPTS + 1):
        tried += 1
        try:
            _check_abort()          # stands in for the chapter's first wait loop
            return tried, reasons, None
        except BotModeError as error:
            reasons.append(f"attempt {attempt}: {error}")
    return tried, reasons, "exhausted"


def new_loop():
    """`except StoryAbort: raise` first — the abort escapes on attempt 1."""
    tried, reasons = 0, []
    for attempt in range(1, ATTEMPTS + 1):
        tried += 1
        try:
            _check_abort()
            return tried, reasons, None
        except StoryAbort:
            raise
        except BotModeError as error:
            reasons.append(f"attempt {attempt}: {error}")
    return tried, reasons, "exhausted"


set_story_abort(True)
tried_old, reasons_old, outcome_old = old_loop()
print(f"  ARM A (old): attempts consumed = {tried_old}, outcome = {outcome_old!r}")
print(f"               reported reasons  = {len(reasons_old)} "
      f"(‼ {max(0, len(reasons_old) - 1)} of them describe failures that never happened)")
check("ARM A reproduces the bug: one whiteout burns EVERY attempt",
      tried_old == ATTEMPTS and outcome_old == "exhausted")

escaped = False
try:
    new_loop()
except StoryAbort:
    escaped = True
except BotModeError:
    escaped = False
check("ARM B: the abort ESCAPES the retry loop instead of being swallowed", escaped)

# ---- ARM C: the LAUNDERED abort — the case a type-only fix cannot see -----------------------
# ‼ THIS IS THE ARM THAT JUSTIFIES `reraise_if_aborting`. Our inner loops routinely catch an error
# and raise a BRAND-NEW one describing the goal they failed to reach — e.g.
# `walk_into_the_space_center` tries six cutscene tiles and, if none works, raises "the Team Magma
# NPCs are therefore still standing on the only land bridge". After a whiteout that sentence is a
# FABRICATED diagnosis. The abort's identity is gone, so `except StoryAbort` cannot help; only
# reading the latch can.
from modules.story.early_game import reraise_if_aborting  # noqa: E402


def launder_type_only():
    """Inner loop that re-raises a fresh error — what a type-only guard misses."""
    try:
        _check_abort()
    except StoryAbort:
        pass
    raise BotModeError("the Team Magma NPCs are still standing on the land bridge")


def launder_latch_keyed():
    """The same loop, with the latch-keyed guard."""
    try:
        _check_abort()
    except BotModeError as error:
        reraise_if_aborting(error)
    raise BotModeError("the Team Magma NPCs are still standing on the land bridge")


set_story_abort(True)
laundered = None
try:
    launder_type_only()
except BaseException as error:  # noqa: BLE001
    laundered = error
check("ARM C control: a type-only guard LAUNDERS the abort into a fake diagnosis",
      isinstance(laundered, BotModeError) and not isinstance(laundered, StoryAbort),
      f"escaped as {type(laundered).__name__}: {laundered}")

kept = None
try:
    launder_latch_keyed()
except BaseException as error:  # noqa: BLE001
    kept = error
check("ARM C: reraise_if_aborting survives the conversion and re-raises",
      isinstance(kept, StoryAbort),
      f"raised {type(kept).__name__}")
set_story_abort(False)

# ‼ AND IT MUST STAY OUT OF THE WAY WHEN THERE IS NO WHITEOUT — otherwise every ordinary retry loop
# would turn its first transient failure into a hard stop.
set_story_abort(False)
passed_through = False
try:
    reraise_if_aborting(BotModeError("an ordinary navigation failure"))
    passed_through = True
except BotModeError:
    passed_through = False
check("with the latch CLEAR, reraise_if_aborting does nothing (retries still work)",
      passed_through)

if not (tried_old == ATTEMPTS and outcome_old == "exhausted"):
    print("\n  ‼ Without ARM A passing, ARM B proves nothing — a loop that never had the bug")
    print("    also 'passes' the fix. The control is the reason the result means anything.")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n3 — STRUCTURAL: every chapter retry loop in the tree carries the guard\n{BAR}\n")

# ‼ A fix applied only to the two chapters I was looking at is not a fix. This scans the story
# surface for functions that catch `BotModeError` in a retry loop and requires each to re-raise
# `StoryAbort` first. It PRINTS what it scanned, because "no offenders" over zero files reads
# identically to a real pass — the lesson `audit_flag_names.py` taught the hard way.
STORY_DIR = BUILD / "modules" / "story"
chapter_files = sorted(STORY_DIR.glob("*.py")) + [BUILD / "plugins/custom_modes/story_mode.py"]

# ⛔⛔ AST, NOT SUBSTRINGS — REWRITTEN 2026-08-17 BECAUSE THIS GATE COULD NOT FAIL.
# An adversarial agent deleted BOTH real defenses from Ch18's retry loop in `mossdeep_gym.py` (the
# `except StoryAbort: raise` clause AND the fallback `reraise_if_aborting(error)` call — precisely
# the KI-67 regression this gate exists to prevent) and left a nearby COMMENT reading
# "`except StoryAbort` above catches it…". The old `"except StoryAbort" in body` substring test
# matched that PROSE, printed `OK mossdeep_gym.py`, and the suite went green over a live
# whiteout-swallowing regression.
# ‼ This is the project's own rule violated by its own gate: *"FAULT-TEST every gate: prove it
# fails when the thing it guards is broken, and prove it does NOT fire on mere mentions in comments
# or docstrings."* A comment is invisible to an AST, which is the whole point.
# ⛔ A parse failure is a LOUD finding, never a silent skip — an unparseable chapter file must not
# read as "no offenders".
import ast  # noqa: E402


def _guarded_retry_loops_src(source: str) -> tuple[list[bool], str | None]:
    """(one bool per retry loop that catches BotModeError, parse_error_or_None). Takes TEXT.

    ‼ Split from the path version ON PURPOSE so the fault tests below can feed it synthetic
    snippets. A checker that can only be run against the real tree cannot be fault-tested cheaply,
    and a gate nobody has seen refuse anything is a gate nobody knows is connected.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [], f"{type(exc).__name__}: {exc}"

    def names(node) -> set[str]:
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}

    out: list[bool] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        # a "chapter retry loop": `for attempt in range(...)`
        if not (isinstance(node.target, ast.Name) and node.target.id == "attempt"):
            continue
        if not (isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name)
                and node.iter.func.id == "range"):
            continue
        handlers = [h for h in ast.walk(node) if isinstance(h, ast.ExceptHandler)]
        catches_bme = any(h.type is not None and "BotModeError" in names(h.type) for h in handlers)
        if not catches_bme:
            continue
        # A real guard is EITHER an `except StoryAbort` handler OR a `reraise_if_aborting(...)`
        # CALL — both are live idioms in this tree, and both are invisible to a comment.
        guards_abort = any(h.type is not None and "StoryAbort" in names(h.type) for h in handlers)
        reraises = any(isinstance(c, ast.Call) and "reraise_if_aborting" in names(c.func)
                       for c in ast.walk(node))
        out.append(bool(guards_abort or reraises))
    return out, None


def _guarded_retry_loops(path: pathlib.Path) -> tuple[list[bool], str | None]:
    return _guarded_retry_loops_src(path.read_text(encoding="utf-8"))


# ⛔⛔ THE FAULT TESTS THAT THE SUBSTRING VERSION WOULD HAVE FAILED. Case 2 IS the attack an
# adversarial agent used on 2026-08-17 to prove the old check could not fail: delete the real
# handler, leave a COMMENT naming it. The old `"except StoryAbort" in body` test passed that; the
# AST cannot see comments, so it reports the loop UNGUARDED.
_FT = [
    ("W1 guarded by `except StoryAbort: raise`",
     "def f():\n    for attempt in range(3):\n        try:\n            go()\n"
     "        except StoryAbort:\n            raise\n        except BotModeError:\n            pass\n", [True]),
    ("W2 ‼ THE ATTACK: handler DELETED, only a COMMENT left naming it",
     "def f():\n    for attempt in range(3):\n        try:\n            go()\n"
     "        # the `except StoryAbort` clause above catches it while it is in flight\n"
     "        except BotModeError:\n            pass\n", [False]),
    ("W3 guarded by a `reraise_if_aborting(...)` CALL instead",
     "def f():\n    for attempt in range(3):\n        try:\n            go()\n"
     "        except BotModeError as e:\n            reraise_if_aborting(e)\n", [True]),
    ("W4 a retry loop that does NOT catch BotModeError is not counted",
     "def f():\n    for attempt in range(3):\n        try:\n            go()\n"
     "        except ValueError:\n            pass\n", []),
    ("W5 a docstring mentioning the handler does not count as one",
     'def f():\n    """uses except StoryAbort to re-raise."""\n    for attempt in range(3):\n'
     "        try:\n            go()\n        except BotModeError:\n            pass\n", [False]),
]
if "--self-test" in sys.argv:
    ok = True
    print(f"\n{BAR}\nFAULT TESTS for the AST retry-loop checker\n{BAR}\n")
    for label, src, want in _FT:
        got, err = _guarded_retry_loops_src(src)
        good = (got == want) and err is None
        ok &= good
        print(f"  {'PASS' if good else '‼ FAIL'}  {label}: got {got} want {want}")
    bad, err = _guarded_retry_loops_src("def f(:\n")
    print(f"  {'PASS' if err else '‼ FAIL'}  W6 an UNPARSEABLE file reports an error, never a silent pass: {err!r}"[:150])
    ok &= bool(err)
    print(f"\nSELF-TEST {'PASS' if ok else 'FAIL'}")
    raise SystemExit(0 if ok else 1)

offenders, scanned, parse_errors = [], [], []
for path in chapter_files:
    flags, err = _guarded_retry_loops(path)
    if err:
        parse_errors.append((path.name, err))
        offenders.append(f"{path.name} (UNPARSEABLE: {err[:60]})")
        continue
    for has_guard in flags:
        scanned.append((path.name, has_guard))
        if not has_guard:
            offenders.append(path.name)

for name, guarded in scanned:
    print(f"  {'OK  ' if guarded else '‼ NO'}  {name}  (retry loop catching BotModeError)")
print(f"\n  scanned {len(chapter_files)} story file(s); found {len(scanned)} chapter retry loop(s)")
check("every chapter retry loop re-raises StoryAbort",
      not offenders and len(scanned) > 0,
      f"offenders: {offenders}" if offenders else
      ("‼ found ZERO retry loops — the scan matched nothing, which is not a pass"
       if not scanned else ""))

# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n4 — THE HARNESS MIRROR: a driver must not silently un-mix its whiteout handling\n{BAR}\n")

# ‼ Adding `StoryWhiteoutRecoveryMixin` to a driver that still defines its OWN `on_whiteout` makes
# the subclass method win under the MRO: the abort latch is never set and the driver LOOKS
# converted while behaving exactly as before. That invisibility is why KI-67 survived so long, so
# the mixin refuses it at class-creation time. This check proves the refusal actually fires —
# a guard nobody has seen refuse anything is a guard nobody knows is connected.
harness_src = (pathlib.Path(__file__).parent / "story_harness.py").read_text(encoding="utf-8")
has_mixin = "class StoryWhiteoutRecoveryMixin" in harness_src
has_guard = "__init_subclass__" in harness_src and "silently stop setting the" in harness_src
check("the harness defines the whiteout-recovery mixin", has_mixin)
check("the mixin REFUSES a subclass that overrides on_whiteout (MRO silent-revert)", has_guard)

# And prove it dynamically, not just by grep.
try:
    ns = {}
    exec(  # noqa: S102 - a 12-line stand-in, not the real class, so the test cannot drift silently
        "class _Mixin:\n"
        "    def __init_subclass__(cls, **kw):\n"
        "        super().__init_subclass__(**kw)\n"
        "        if 'on_whiteout' in cls.__dict__:\n"
        "            raise TypeError('would silently stop setting the latch')\n"
        "    def on_whiteout(self):\n"
        "        return True\n",
        ns,
    )
    refused = False
    try:
        exec("class _Bad(_Mixin):\n    def on_whiteout(self):\n        return True\n", ns)
    except TypeError:
        refused = True
    check("the __init_subclass__ pattern does refuse an overriding subclass", refused)
except Exception as error:  # noqa: BLE001
    check("the __init_subclass__ pattern does refuse an overriding subclass", False, str(error))

print(f"\n{BAR}\nSUMMARY\n{BAR}\n")
for label, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
passed = sum(1 for _l, ok in results if ok)
print(f"\n  {passed} / {len(results)} checks pass.")
if passed != len(results):
    print("\nRESULT: FAIL")
    raise SystemExit(1)
print("\nRESULT: ALL PASS — a whiteout now unwinds to StoryMode.run, which is the only thing that")
print("        can clear the latch, ride out the respawn and re-enter the chapter.")
print("\n‼ STILL UNPROVEN LIVE: no driver mirrors `StoryMode.on_whiteout` yet, so the RECOVERY")
print("  itself has never been driven. See KI-67 — that needs a deliberate loss, not a repro.")
