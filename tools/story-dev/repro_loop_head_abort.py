"""GATE — `#24-loopheadabort`: nav retry loops must ABORT at the loop head, and the whiteout
recovery must keep running because the latch is CLEARED BEFORE it (§1 guards that ordering).

THE DEFECT. After a whiteout, `StoryMode` sets the `_STORY_ABORT` latch so the running segment
bails out and `run()` can re-orient from the respawn Poké Center. But the navigation primitives
(`navigate_to`, `navigate_to_anywhere`, `_enter_warp_by_navigation`, `follow_path`) contain **no
`_check_abort()`**, and `raise StoryAbort` exists at exactly ONE site in the whole package
(`early_game.py`, inside `_check_abort`). So nothing raised inside those retry loops: the bot went
on re-navigating a DEAD TEAM from the Poké Center, burned its whole retry budget
(`_navigate_through_scripts` up to `max_rounds=25`, `recover_devon_goods` up to 20) and then raised
a **FABRICATED** cause — *"Could not reach X (too many scripted interruptions)"*. The real cause was
a whiteout, and the log said scripted interruptions.

WHY THE CHECK MUST BE AT THE LOOP HEAD, NOT IN THE HANDLER. `StoryAbort` SUBCLASSES `BotModeError`
on purpose (so every existing `except BotModeError` keeps working). ⇒ a check *inside* the loop's
`try` would be swallowed by that loop's own `except BotModeError` / `except Exception`. The check
must sit as the FIRST statement of the loop body, OUTSIDE the try. That is also the file's own
canonical idiom — 73 of 73 existing head checks are a bare, unguarded `_check_abort()` as the
literal first statement, and the codebase self-cites `_navigate_riding_out` (`:266`) as the
reference implementation.

⛔⛔ THE ORDERING THIS DEPENDS ON, AND WHY §1 EXISTS — INCLUDING A CLAIM THAT WAS WRONG.
While building this, I excluded three loops (`exit_building_after_whiteout`,
`_exit_training_cave_if_inside`, `_enter_warp_by_navigation`) on the stated grounds that they
"run WHILE THE LATCH IS STILL SET", so a head check would abort the recovery itself.
**AN ADVERSARIAL REVIEW REFUTED THAT, and it was right.** Parsed, not eyeballed: in
`plugins/custom_modes/story_mode.py::StoryMode.run`, the `except BotModeError` handler splits into
a DERAIL branch (`if not self._whiteout_pending`) which clears the latch and only THEN calls
`wait_until_truly_controllable` / `exit_building_after_whiteout` / `_exit_training_cave_if_inside`;
and a WHITEOUT branch which clears the latch and only then calls `exit_building_after_whiteout`
inside a later `try`. ⇒ **in BOTH branches the latch is already CLEAR when those functions run**,
so the self-abort hazard does not exist and the exclusion cost real coverage for nothing
(`_enter_warp_by_navigation` alone has ~35 call sites). All 17 loops are now patched.
‼ *The original mistake was grepping a LINE RANGE and never checking which branch the lines were
in. `08-MISTAKES.md` carries it.*

⇒ **BUT THE HAZARD IS ONE REORDERING AWAY, AND THAT IS WHAT §1 NOW GATES.** The safety of every
head check on the recovery path rests entirely on `set_story_abort(False)` happening BEFORE those
calls. Move the clear after them — a plausible future refactor — and every recovery aborts itself
on its first iteration, `recoveries > 40` trips, and the run dies with a symptom that looks like
anything except a reordered statement. §1 asserts the ordering that makes the checks safe.

WHAT THIS GATE ASSERTS
  §1  ORDERING    — in `StoryMode.run`, every whiteout-recovery call is DOMINATED by a
                    `set_story_abort(False)` (same block or an ancestor — NOT merely earlier in the
                    file: the two handler branches each clear separately). ⛔ The regression guard.
  §2  COVERAGE    — every loop that can reach a nav primitive WITHOUT passing through an
                    already-guarded helper has a BARE `_check_abort()` as `body[0]` (ratchet).
  §3  BEHAVIOUR   — drives the REAL `_navigate_through_scripts` two-armed, no emulator:
                    ARM A (latch clear) burns the budget and raises the FABRICATED cause;
                    ARM B (latch set)  raises `StoryAbort` on iteration 1 having navigated ZERO times.
                    ‼ The arms differ on TWO independent axes — attempt count AND exception type.

⚠ SCOPE, STATED HONESTLY: §1 is a STATIC ordering proof, not a live recovery drive. Proving a real
whiteout recovery end-to-end needs the emulator and belongs in a driver, not a 1-second gate.

EXIT CODES: 0 all checks pass; 1 any check fails.
Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_loop_head_abort.py [--build sandbox|custom]
      PYTHONUTF8=1 py -3.12 repro_loop_head_abort.py --self-test   # fault-inject both directions
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys

_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"],
                 help="which fork to test (default sandbox; use custom to verify a promotion)")
_ap.add_argument("--self-test", action="store_true", help="prove these checks can FAIL")
_ARGS, _ = _ap.parse_known_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
FORK = REPO / f"{_ARGS.build}-pokebot"
EARLY = FORK / "modules" / "story" / "early_game.py"

BAR = "=" * 96

#: The navigation primitives whose retry loops this gate governs.
NAV = {"navigate_to", "navigate_to_anywhere", "_enter_warp_by_navigation", "follow_path"}

#: The three routines `StoryMode`'s whiteout/derail recovery calls. ⛔ CORRECTED 2026-08-23: an
#: earlier draft claimed these run WHILE `_STORY_ABORT` IS SET — an adversarial review REFUTED it.
#: Parsed from `story_mode.py`, BOTH handler branches call `set_story_abort(False)` BEFORE these,
#: so the latch is CLEAR here and a head check is safe. §1 gates that ordering, because reversing
#: it would make every recovery abort itself.
RECOVERY_ROOTS = [
    "wait_until_truly_controllable",
    "exit_building_after_whiteout",
    "_exit_training_cave_if_inside",
]


def _parse(src: str):
    tree = ast.parse(src)
    fns = {n.name: n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    owner: dict[int, str] = {}
    for name, fn in fns.items():
        for n in ast.walk(fn):
            owner[id(n)] = name
    return tree, fns, owner


def _callees(node) -> set[str]:
    out = set()
    for c in ast.walk(node):
        if isinstance(c, ast.Call):
            f = c.func
            out.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    return out


def _recovery_closure(fns) -> set[str]:
    seen: set[str] = set()
    stack = list(RECOVERY_ROOTS)
    while stack:
        f = stack.pop()
        if f in seen or f not in fns:
            continue
        seen.add(f)
        stack.extend(_callees(fns[f]))
    return seen


def _has_head_check(loop) -> bool:
    """`loop.body[0]` must be EXACTLY the statement `_check_abort()` — nothing weaker.

    ‼‼ TIGHTENED after an adversarial review made the loose version report a FALSE GREEN four
    different ways. It previously accepted "`_check_abort` appears anywhere in any top-level body
    statement before the first `try`", which is satisfied by:
        if rounds > 3: _check_abort()     # conditional — does not fire on iteration 1
        for _z in (): _check_abort()      # never executes at all
        if False: _check_abort()          # dead code
        self._check_abort()               # AttributeError at runtime, not a check
    ⇒ require the file's own canonical idiom, which is true of all 17 insertions and of all 73
    pre-existing head checks: a BARE, UNCONDITIONAL `_check_abort()` as the literal first statement.
    ⚠ Being `body[0]` also makes "outside the `try`" automatic — a check inside the loop's own try
    would be swallowed by its `except BotModeError`, since `StoryAbort` subclasses it."""
    if not loop.body:
        return False
    first = loop.body[0]
    return (isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Call)
            and isinstance(first.value.func, ast.Name)      # a bare name, never `self._check_abort`
            and first.value.func.id == "_check_abort"
            and not first.value.args and not first.value.keywords)


def _analyse(src: str):
    """Which loops NEED a head check, by REACHABILITY — not by direct call matching.

    ‼ THE CRITERION, and it took an argument between two independent derivations to get right.
    A direct-call match finds 26 nav loops here; a naive TRANSITIVE match finds 44. Neither is the
    population that needs fixing:
      * direct-only MISSES a loop that navigates through a local helper;
      * naive-transitive OVER-COUNTS, because a loop whose only route to a primitive passes through
        a helper that ALREADY has a head check is already safe — the abort raised in that helper
        propagates straight out (verified: `buy_poke_balls_in_tens` -> `buy_poke_balls` ->
        `_navigate_riding_out`, which is guarded, with no swallowing handler in between).
    ⇒ **A loop needs a head check iff it can reach a navigation primitive WITHOUT passing through a
    function that already contains `_check_abort()`.** On the fixed tree that yields 28 loops, all
    of them guarded."""
    tree, fns, owner = _parse(src)
    closure = _recovery_closure(fns)
    guarded_fns = {n for n, f in fns.items() if "_check_abort" in _callees(f)}

    def _reaches_unguarded(name: str, seen: frozenset = frozenset()) -> bool:
        if name in NAV:
            return True
        if name not in fns or name in seen:
            return False
        for c in sorted(_callees(fns[name])):
            if c in NAV:
                return True
            if c in fns and c not in guarded_fns and _reaches_unguarded(c, seen | {name}):
                return True
        return False

    def _needs_check(loop) -> bool:
        for c in sorted(_callees(loop)):
            if c in NAV:
                return True
            if c in fns and c not in guarded_fns and _reaches_unguarded(c):
                return True
        return False

    loops = []
    for loop in ast.walk(tree):
        if not isinstance(loop, (ast.For, ast.While)) or not _needs_check(loop):
            continue
        fn = owner.get(id(loop), "<module>")
        loops.append({"line": loop.lineno, "fn": fn,
                      "guarded": _has_head_check(loop), "in_recovery": fn in closure})
    loops.sort(key=lambda r: r["line"])
    return closure, loops


# ------------------------------------------------------------------------------------------------
def check_recovery_ordering(story_src: str) -> tuple[bool, str]:
    """§1 — in `StoryMode.run`, a recovery routine may only be called AFTER `set_story_abort(False)`.

    ‼ This is the invariant every head check on the recovery path depends on. It holds today in both
    branches of the `except BotModeError` handler. If a refactor moves the clear below the calls,
    each recovery aborts itself on its first iteration and `recoveries > 40` kills the run.

    ‼‼ THIS USED `min(clears)` OVER THE WHOLE HANDLER AND COULD NOT FAIL. `StoryMode.run`'s
    `except BotModeError` holds TWO independent branches — a DERAIL branch that clears the latch and
    a WHITEOUT branch that clears it separately. A lexical minimum meant the derail clear (earlier in
    the file) vouched for the whiteout branch too: deleting the whiteout clear outright, or moving it
    BELOW its own `exit_building_after_whiteout()`, both still reported PASS. An adversarial review
    injected exactly those two faults and caught it. ⛔ That is the `repro_whiteout_abort.py` shape —
    a gate green over the regression it exists to catch — reproduced in a gate written to prevent it.
    ⇒ **A clear must DOMINATE the call**: appear in the call's own block, or in an ANCESTOR block,
    at a position before the statement that leads to the call. A clear in a sibling branch, or one
    sitting under `if recoveries > 40:` right before a `raise`, dominates nothing and no longer counts."""
    tree = ast.parse(story_src)
    run_fn = next((n for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "run"), None)
    if run_fn is None:
        return False, "could not find `StoryMode.run` — refusing to report success"

    def _is_clear(node) -> bool:
        return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", "") == "set_story_abort"
                and node.value.args and isinstance(node.value.args[0], ast.Constant)
                and node.value.args[0].value is False)

    _BLOCK_FIELDS = ("body", "orelse", "finalbody", "handlers")

    def _direct_calls(stmt) -> list[tuple[str, int]]:
        """Recovery calls belonging to THIS statement, not to its nested blocks.

        ‼ A plain `ast.walk` here counted a call nested three blocks down as if it sat at the
        current level, so the clean tree reported FAIL and every call was counted three times."""
        out: list[tuple[str, int]] = []

        def visit(node, top: bool) -> None:
            if not top and isinstance(node, ast.stmt):
                return                                   # a nested statement belongs to its block
            if isinstance(node, ast.Call):
                nm = getattr(node.func, "id", "") or getattr(node.func, "attr", "")
                if nm in RECOVERY_ROOTS:
                    out.append((nm, node.lineno))
            for name, value in ast.iter_fields(node):
                if name in _BLOCK_FIELDS and isinstance(value, list):
                    continue                             # skip nested blocks entirely
                for child in (value if isinstance(value, list) else [value]):
                    if isinstance(child, ast.AST):
                        visit(child, False)

        visit(stmt, True)
        return out

    bad: list[str] = []
    checked = 0

    def scan(body: list, cleared: bool) -> None:
        """Walk a statement list IN ORDER, carrying dominance into each nested block."""
        nonlocal checked
        seen_clear = cleared
        for stmt in body:
            if _is_clear(stmt):
                seen_clear = True
                continue
            for nm, ln in _direct_calls(stmt):
                checked += 1
                if not seen_clear:
                    bad.append(f"{nm}@{ln} is NOT dominated by set_story_abort(False)")
            for field in ("body", "orelse", "finalbody"):
                sub = getattr(stmt, field, None)
                if isinstance(sub, list) and sub and isinstance(sub[0], ast.stmt):
                    scan(sub, seen_clear)
            for h in getattr(stmt, "handlers", []) or []:
                scan(h.body, seen_clear)

    for handler in [n for n in ast.walk(run_fn) if isinstance(n, ast.ExceptHandler)]:
        scan(handler.body, cleared=False)

    if not checked:
        return False, "no recovery-routine calls found inside any handler — the check never ran"
    return not bad, (f"{checked} recovery call(s) checked; each DOMINATED by a latch clear"
                     if not bad else "; ".join(bad))


def run_static(src: str, results: list, story_src: str | None = None) -> None:
    _closure, loops = _analyse(src)

    # §1 THE ORDERING INVARIANT — the regression guard.
    if story_src is None:
        story_src = (FORK / "plugins" / "custom_modes" / "story_mode.py").read_text(
            encoding="utf-8", errors="replace")
    ok, detail = check_recovery_ordering(story_src)
    results.append((ok, "§1 ORDERING: every whiteout-recovery call runs AFTER `set_story_abort(False)`",
                    detail))

    # §2 COVERAGE RATCHET — every loop that needs a head check has one.
    unguarded = [l for l in loops if not l["guarded"]]
    results.append((not unguarded,
                    "§2 COVERAGE: every loop that can reach a nav primitive un-guarded HAS a head check",
                    f"{len(loops) - len(unguarded)}/{len(loops)} guarded"
                    + (f"; UNGUARDED: {[(l['fn'], l['line']) for l in unguarded]}" if unguarded else "")))


# ------------------------------------------------------------------------------------------------
def run_behaviour(results: list) -> None:
    """Drive the REAL `_navigate_through_scripts` two-armed. No emulator: the callees are stubbed,
    but the loop, the budget, the raise and `_check_abort` are all production code."""
    sys.path.insert(0, str(FORK))
    try:
        from modules.story import early_game as eg
    except Exception as error:  # noqa: BLE001 — an unimportable fork is a LOUD failure, not a skip
        results.append((False, "§3 BEHAVIOUR: import the fork's `early_game`",
                        f"{type(error).__name__}: {error}"))
        return

    class _Dest:
        value = 999999          # a map number `_map_group_number` will never return

    def _arm(latch: bool):
        calls = {"nav": 0}

        def _fake_nav(*_a, **_k):
            calls["nav"] += 1
            yield

        def _fake_ride(*_a, **_k):
            yield

        saved = {k: getattr(eg, k, None) for k in
                 ("_map_group_number", "navigate_to_anywhere", "_ride_out_scripted_scene", "context")}
        eg._map_group_number = lambda: 1          # never equals _Dest.value -> the loop spins
        eg.navigate_to_anywhere = _fake_nav
        eg._ride_out_scripted_scene = _fake_ride

        class _Ctx:
            message = ""
        eg.context = _Ctx()
        eg.set_story_abort(latch)
        raised = None
        try:
            for _ in eg._navigate_through_scripts(_Dest, (1, 1), max_rounds=25):
                pass
        except BaseException as err:              # noqa: BLE001 — the exception IS the measurement
            raised = err
        finally:
            eg.set_story_abort(False)
            for k, v in saved.items():
                if v is not None:
                    setattr(eg, k, v)
        return calls["nav"], raised

    a_navs, a_err = _arm(latch=False)
    b_navs, b_err = _arm(latch=True)

    a_ok = (a_navs == 25 and isinstance(a_err, Exception)
            and "too many scripted interruptions" in str(a_err)
            and type(a_err).__name__ != "StoryAbort")
    results.append((a_ok, "§3 ARM A (latch CLEAR): burns the budget, raises the FABRICATED cause",
                    f"nav_attempts={a_navs} raised={type(a_err).__name__}: {str(a_err)[:60]}"))

    b_ok = (b_navs == 0 and type(b_err).__name__ == "StoryAbort")
    results.append((b_ok, "§3 ARM B (latch SET): raises StoryAbort on iteration 1, navigating ZERO times",
                    f"nav_attempts={b_navs} raised={type(b_err).__name__}: {str(b_err)[:60]}"))

    # ‼ The discriminator, stated explicitly so a reader cannot mistake this for one measurement.
    results.append((a_navs != b_navs and type(a_err) is not type(b_err),
                    "§3 DISCRIMINATOR: the arms differ on BOTH axes (attempt count AND exception type)",
                    f"attempts {a_navs} vs {b_navs}; types {type(a_err).__name__} vs {type(b_err).__name__}"))


# ------------------------------------------------------------------------------------------------
def self_test() -> int:
    """‼ PROVE THE CHECKS CAN FAIL. A gate never seen red is an assumption."""
    print(BAR)
    print("SELF-TEST — fault-inject each direction and require the check to go RED")
    print(BAR)
    src = EARLY.read_text(encoding="utf-8", errors="replace")
    fails = 0

    def expect(label: str, ok_when_faulted: bool) -> None:
        nonlocal fails
        if ok_when_faulted:
            print(f"  OK    {label}")
        else:
            print(f"  ‼ FAIL {label} — the check did NOT notice the injected fault")
            fails += 1

    # F1 — REORDER the recovery so it runs BEFORE the latch clear: §1 must fire.
    story = (FORK / "plugins" / "custom_modes" / "story_mode.py").read_text(
        encoding="utf-8", errors="replace")
    ok_clean, _ = check_recovery_ordering(story)
    # ‼ INJECT THE ACTUAL HAZARD: a recovery call placed ABOVE its handler's latch clear.
    # (An earlier draft of this fault replaced the FIRST `set_story_abort(False)` in the file —
    # which is the mode-start one at module scope, inside no handler, so it changed nothing and
    # F1 correctly refused to pass. The fault has to be the thing the check actually guards.)
    # ‼ Match the anchor's REAL indent rather than assuming one — a hard-coded 12 spaces produced
    # an IndentationError instead of a finding, and the check failed LOUDLY rather than pass.
    _lines = story.splitlines()
    _idx = next(i for i, s in enumerate(_lines) if s.strip() == "if not self._whiteout_pending:")
    _ind = " " * (len(_lines[_idx]) - len(_lines[_idx].lstrip()))
    _lines.insert(_idx, f"{_ind}yield from exit_building_after_whiteout()")
    faulted_story = "\n".join(_lines)
    ok_faulted, why = check_recovery_ordering(faulted_story)
    expect("F1 §1 fires when a recovery call is moved ABOVE its handler's latch clear",
           ok_clean and not ok_faulted)

    # ‼ F1a / F1b — THE TWO FAULTS AN ADVERSARIAL REVIEW USED TO PROVE §1 COULD NOT FAIL.
    # §1 originally took `min(clears)` over the WHOLE handler, so the DERAIL branch's clear vouched
    # for the WHITEOUT branch too. Both of these returned PASS. They are permanent now.
    _sl = story.splitlines()
    # ‼ Find the clear that actually DOMINATES the whiteout branch's recovery call — i.e. the
    # nearest one ABOVE it at a STRICTLY SMALLER indent. A naive "first clear within 20 lines"
    # picked the one inside `if recoveries > 40:` (same indent as the call, dominating nothing),
    # so F1a/F1b failed — the fault test caught a bug in the fault test.
    _wcall = next(i for i, s in enumerate(_sl)
                  if "yield from exit_building_after_whiteout()" in s
                  and not s.lstrip().startswith("#") and i > 2600)
    _callind = len(_sl[_wcall]) - len(_sl[_wcall].lstrip())
    _ci = max(i for i, s in enumerate(_sl[:_wcall])
              if s.strip() == "set_story_abort(False)"
              and (len(s) - len(s.lstrip())) < _callind)
    _cind = " " * (len(_sl[_ci]) - len(_sl[_ci].lstrip()))
    fa = _sl[:]
    fa[_ci] = _cind + "pass  # FAULT A: whiteout-branch clear deleted"
    ok_a, _ = check_recovery_ordering("\n".join(fa))
    expect("F1a §1 fires when the WHITEOUT branch's clear is deleted (the derail clear must NOT vouch)",
           not ok_a)

    fb = _sl[:]
    fb[_ci] = _cind + "pass  # FAULT B: clear moved below the call"
    _call = next(i for i, s in enumerate(fb)
                 if "yield from exit_building_after_whiteout()" in s
                 and not s.lstrip().startswith("#") and i > _ci)
    fb.insert(_call + 1, " " * (len(fb[_call]) - len(fb[_call].lstrip())) + "set_story_abort(False)")
    ok_b, _ = check_recovery_ordering("\n".join(fb))
    expect("F1b §1 fires when the clear is moved BELOW its own recovery call", not ok_b)

    # ‼ F2a-F2e — FOUR SHAPES THAT MADE §2 REPORT A FALSE GREEN before it required `body[0]`.
    def _guarded(body_src: str) -> bool:
        loop = ast.parse("for _ in range(3):\n" + body_src).body[0]
        return _has_head_check(loop)

    for _label, _body in [
        ("F2a a CONDITIONAL check", "    if rounds > 3:\n        _check_abort()\n    pass"),
        ("F2b a check in a loop that NEVER RUNS", "    for _z in ():\n        _check_abort()\n    pass"),
        ("F2c a check under `if False`", "    if False:\n        _check_abort()\n    pass"),
        ("F2d `self._check_abort()` (an AttributeError, not a check)", "    self._check_abort()\n    pass"),
    ]:
        expect(_label + " does NOT satisfy §2", not _guarded(_body))
    expect("F2e the canonical bare `_check_abort()` DOES satisfy §2",
           _guarded("    _check_abort()\n    pass"))

    # F2 — remove a head check from a non-recovery nav loop: §2 must fire.
    marker = "    while _map_group_number() != dest:\n        _check_abort()\n"
    faulted2 = src.replace(marker, "    while _map_group_number() != dest:\n", 1)
    expect("F2 §2 fires when a head check is deleted from a guarded nav loop",
           faulted2 != src and any(
               (not l["guarded"]) and (not l["in_recovery"]) for l in _analyse(faulted2)[1]))

    # F3 — the UPWARD direction: a `_check_abort` mentioned only in a COMMENT must NOT satisfy §2.
    faulted3 = src.replace(marker,
                           "    while _map_group_number() != dest:\n        # _check_abort()\n", 1)
    expect("F3 §2 is NOT satisfied by `_check_abort` in a COMMENT (no false green)",
           faulted3 != src and any(
               (not l["guarded"]) and (not l["in_recovery"]) for l in _analyse(faulted3)[1]))

    # F4 — a check INSIDE the loop's try must NOT count (it would be swallowed by except BotModeError).
    faulted4 = src.replace(marker, "    while _map_group_number() != dest:\n", 1)
    faulted4 = faulted4.replace("        try:\n            yield from navigate_to_anywhere(",
                                "        try:\n            _check_abort()\n            yield from navigate_to_anywhere(", 1)
    expect("F4 a check INSIDE the try does NOT count as a head check (it would be swallowed)",
           faulted4 != src and any(
               (not l["guarded"]) and (not l["in_recovery"]) for l in _analyse(faulted4)[1]))

    # F5 — the healthy tree must be GREEN, or the faults above prove nothing.
    res: list = []
    run_static(src, res, story_src=story)
    expect("F5 the UNMODIFIED tree passes every static check (no false red)",
           all(ok for ok, _, _ in res))

    print(BAR)
    if fails:
        print(f"SELF-TEST FAILED — {fails} check(s) could not be made to fail")
        return 1
    print("SELF-TEST PASS — every check was driven RED by an injected fault, and green without one")
    print(BAR)
    return 0


def main() -> int:
    if _ARGS.self_test:
        return self_test()

    if not EARLY.is_file():
        print(f"‼ MISSING: {EARLY} — refusing to report success over a file that is not there")
        return 1

    print(BAR)
    print(f"LOOP-HEAD ABORT — `#24-loopheadabort`   BUILD UNDER TEST: {_ARGS.build}-pokebot")
    print(BAR)

    results: list = []
    run_static(EARLY.read_text(encoding="utf-8", errors="replace"), results)
    run_behaviour(results)

    for ok, label, detail in results:
        print(f"  {'PASS' if ok else '‼ FAIL'}  {label}")
        print(f"          {detail}")

    failed = [r for r in results if not r[0]]
    print(BAR)
    if failed:
        print(f"FAILED — {len(failed)} of {len(results)} checks")
        print("  ⛔ If §1 failed, a whiteout-recovery call is no longer DOMINATED by")
        print("     `set_story_abort(False)` in `StoryMode.run`. Do NOT 'fix' it by deleting head")
        print("     checks — restore the ordering so the latch is cleared BEFORE the recovery runs.")
        print(BAR)
        return 1
    print(f"ALL {len(results)} CHECKS PASS")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
