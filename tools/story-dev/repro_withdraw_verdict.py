r"""GATE — `withdraw_from_box`'s verdict must REACH ITS CALLER, and must say which case it is.

WHY THIS EXISTS (`#24-orphans` (1), 2026-08-17)
------------------------------------------------
KI-79 made `withdraw_from_box` *say* the truth on the console — identity-verified, loud on failure.
The caller still could not *read* it: **every exit returned `None`**, so "the counter is in the
party", "there was nothing to collect" and "the withdraw was tried and did not land" were the SAME
value to `yield from`. A failed withdraw was reported and then silently tolerated, and the next
Slugma-class derail would have been just as invisible to production as the first.

WHAT IT CHECKS
  V1  STRUCTURAL — every `return` inside `withdraw_from_box` carries a 3-tuple verdict, and no
      execution path falls off the end without one. Parsed with AST, never by grepping for `return`.
      ‼ This is the half that ROTS: a new early-return added later would silently reintroduce the
      exact bug, and it would look completely innocent in review.
  V2  THE PURE DECISION — `withdraw_verdict_report` maps every verdict shape to a report line, and
      an UNRECOGNISED or MISSING verdict reads as FAILED rather than as a shrug.
  V3  POLARITY — the two NO-ATTEMPT codes must NOT read as failures (most heals have nothing to
      collect, and a full party declining to thin itself is correct behaviour), while `did_not_land`
      and the error paths MUST. Getting this backwards would recreate, in the report, the very lie
      KI-79 removed from the console.
  V4  THE CALLER IS WIRED — `higher_level_actions.py` BINDS the generator's result and passes it to
      the reporter. ⛔ A verdict that is returned and then dropped is the original bug with extra
      steps, so the binding is asserted structurally, in the caller, by AST.

⛔ WHAT IT DELIBERATELY DOES NOT CHECK: that the withdraw WORKS. That is a live-emulator question
and is proven separately by the two-armed `--driver boxcounter2` A/B with `POKEBOT_PCWITHDRAW_FAULT`
(evidence under `tools/story-dev/evidence/2026-08-17-withdrawverdict-*`). This gate is the cheap,
no-ROM half that stops the WIRING from rotting between those expensive runs.

⛔ AND IT DOES NOT CHECK ANY REACTION POLICY — there is none, on purpose. What production should DO
about a failed withdraw is the USER's ruling and is blocked on an unmeasured heap offset
(`06-DECISIONS-LOG.md`). This gate asserts the verdict is READABLE, never that it is ACTED ON.

Fault tests (CLAUDE.md rule 6 — prove it fires AND prove it stays quiet):
    PYTHONUTF8=1 py -3.12 repro_withdraw_verdict.py --self-test

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_withdraw_verdict.py
Exit: 0 clean, 1 on any failure.  No ROM, no emulator.
"""

from __future__ import annotations

import ast
import pathlib
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


REPO = pathlib.Path(__file__).resolve().parents[2]

#: Which fork to read. `--build custom` makes a promotion MEASURABLE rather than assumed: the same
#: assertions run against the promoted tree and prove the new branch is what actually ships there.
BUILD = "custom-pokebot" if "--build" in sys.argv and "custom" in sys.argv else "sandbox-pokebot"

PC_TRIP = REPO / BUILD / "modules" / "story" / "pc_trip.py"
CALLER = REPO / BUILD / "modules" / "modes" / "util" / "higher_level_actions.py"


def _func(src: str, name: str) -> ast.FunctionDef:
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"{name}() not found — did it get renamed?")


def _returns_a_verdict(node: ast.Return) -> bool:
    """A verdict is a 3-tuple whose 2nd element is a string literal CODE."""
    v = node.value
    return (isinstance(v, ast.Tuple) and len(v.elts) == 3
            and isinstance(v.elts[1], ast.Constant) and isinstance(v.elts[1].value, str))


def _falls_off_end(body: list[ast.stmt]) -> bool:
    """Can control reach the end of `body` without returning or raising?

    ‼ Structural, and deliberately CONSERVATIVE: anything this cannot prove terminates counts as
    falling through. A gate that guesses "probably returns" would pass the exact defect it exists
    to catch.
    """
    if not body:
        return True
    last = body[-1]
    if isinstance(last, ast.Return):
        # ‼ A `return <value>` TERMINATES. Only a bare `return` / `return None` leaves the caller
        # with nothing, which is the defect — so those two count as falling through.
        # (This condition shipped INVERTED in the first draft and W2/W7 caught it immediately,
        # which is the entire argument for writing the quiet-direction fault tests.)
        return last.value is None or (isinstance(last.value, ast.Constant)
                                      and last.value.value is None)
    if isinstance(last, ast.Raise):
        return False
    if isinstance(last, ast.If):
        # Falls through unless BOTH arms terminate — and an `if` with no `else` always can.
        return _falls_off_end(last.body) or not last.orelse or _falls_off_end(last.orelse)
    if isinstance(last, ast.Try):
        # A terminating `finally` ends the whole statement no matter what the other clauses do.
        if last.finalbody and not _falls_off_end(last.finalbody):
            return False
        # ‼ THE SUCCESS PATH: the try body runs, and ONLY IF IT FALLS THROUGH does `else` run. So
        # the success path terminates if the body terminates, or if the body falls into an `else`
        # that terminates. Getting this wrong in either direction is a live risk — the first draft
        # ignored `orelse` entirely (false FAILURE, W9) and a gate that cries wolf gets bypassed.
        success_falls = _falls_off_end(last.body) and (
            _falls_off_end(last.orelse) if last.orelse else True)
        if success_falls:
            return True
        # EVERY handler must terminate too: a bare handler that only logs is precisely how
        # `withdraw_from_box`'s error path used to return `None` on the path a caller most needs.
        return any(_falls_off_end(h.body) for h in last.handlers)
    return True


def check_structure() -> list[str]:
    out: list[str] = []
    fn = _func(PC_TRIP.read_text(encoding="utf-8"), "withdraw_from_box")
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
    if not returns:
        out.append("withdraw_from_box has NO return statements at all — its verdict cannot reach "
                   "any caller (this is the original `#24-orphans` (1) defect)")
    for r in returns:
        if not _returns_a_verdict(r):
            out.append(f"{PC_TRIP.name}:{r.lineno} `return` does not carry a 3-tuple verdict "
                       f"`(landed, code, detail)` — a bare return makes 'it worked', 'nothing to "
                       f"do' and 'it FAILED' the same value to the caller")
    if _falls_off_end(fn.body):
        out.append(f"{PC_TRIP.name}:{fn.lineno} withdraw_from_box can fall off its end without "
                   f"returning a verdict — that path yields `None` to the caller")
    return out


def check_caller_binds() -> list[str]:
    """⛔ A verdict that is returned and then DROPPED is the original bug with extra steps."""
    out: list[str] = []
    src = CALLER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    bound = False
    for node in ast.walk(tree):
        # `_verdict = yield from withdraw_from_box(...)` — an ASSIGNMENT, not a bare expression.
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.YieldFrom):
            call = node.value.value
            if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "withdraw_from_box":
                bound = True
    if not bound:
        out.append(f"{CALLER.name}: the call to withdraw_from_box does not BIND its result "
                   f"(`x = yield from ...`) — the verdict is computed and thrown away")
    if "withdraw_verdict_report(" not in src:
        out.append(f"{CALLER.name}: the bound verdict is never passed to "
                   f"`withdraw_verdict_report` — nothing reports what the caller actually saw")
    return out


def check_reporting() -> list[str]:
    """The pure decision, exercised directly — every branch, without an emulator."""
    sys.path.insert(0, str(REPO / BUILD))
    try:
        from modules.modes.util.higher_level_actions import withdraw_verdict_report as rep
    except Exception as error:  # noqa: BLE001
        return [f"could not import withdraw_verdict_report from {BUILD}: {error!r}"]

    out: list[str] = []

    def expect(label: str, verdict, want_landed, want_failed: bool) -> None:
        landed, line = rep(verdict)
        if landed != want_landed:
            out.append(f"{label}: landed={landed!r}, expected {want_landed!r}")
        if ("FAILED" in line) != want_failed:
            out.append(f"{label}: {'did not read' if want_failed else 'reads'} as FAILED "
                       f"but should{'' if want_failed else ' not'} — {line!r}")

    # ⛔ V3 POLARITY. The two NO-ATTEMPT codes must not read as failures; the real failures must.
    expect("landed", (True, "landed", "Slugma"), True, False)
    expect("not_in_box", (False, "not_in_box", "1 hunted PID(s)"), False, False)
    expect("party_full_no_deposit", (False, "party_full_no_deposit", "Slugma"), False, False)
    expect("did_not_land", (False, "did_not_land", "Slugma in_party=False"), False, True)
    expect("error", (False, "error", "RuntimeError()"), False, True)
    # ⛔ V2 the two silences: a shape nobody recognises, and no verdict at all.
    expect("unknown code", (False, "who_knows", ""), False, True)
    expect("None (the ORIGINAL bug)", None, None, True)
    expect("wrong arity", (False, "landed"), None, True)

    # The machine-readable tail is what the live A/B greps; if it moves, the proof stops proving.
    _, line = rep((True, "landed", "Slugma"))
    if "verdict landed=True code=landed" not in line:
        out.append(f"the machine-readable `verdict landed=… code=…` tail is missing from {line!r} "
                   f"— the two-armed A/B greps for it")
    # ⛔⛔ RICH MARKUP. `_piggyback_report` prints through `rich`, which parses `[...]` as a STYLE
    # TAG and SWALLOWS it. The first draft ended `[landed=True code=landed]`; the unit test passed
    # and the LIVE TRANSCRIPT had no tail at all, so the A/B would have graded a line that does not
    # exist. Any bracket reintroduced here silently breaks the proof, which is why this is a gate
    # and not a comment.
    for verdict in ((True, "landed", "Slugma"), (False, "did_not_land", "x"), None,
                    # ‼ THE FREE-TEXT FIELD, FUZZED. `detail` carries `repr(error)` on the error
                    # path, so a stdlib exception whose message contains a bracket would reopen the
                    # hole. Fixed samples could never have caught that — an adversarial review had
                    # to point it out, which is why the dynamic case is now a permanent test.
                    (False, "error", "RuntimeError(\"PC said [BOX FULL] at [10,1]\")"),
                    (False, "did_not_land", "Nidoran[M] in_party=False")):
        _, text = rep(verdict)
        if "[" in text or "]" in text:
            out.append(f"report line contains a square bracket, which `rich` will eat before it "
                       f"reaches the transcript: {text!r}")
    return out


def self_test() -> int:
    """⛔ Prove the STRUCTURAL check fires on the bug, and stays quiet on correct code."""
    fails = 0

    def expect(label: str, got: bool, want: bool) -> None:
        nonlocal fails
        ok = got == want
        fails += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  {label}: "
              f"{'flagged' if got else 'quiet'} (expected {'flagged' if want else 'quiet'})")

    def flags(src: str) -> bool:
        fn = _func(src, "f")
        return (any(not _returns_a_verdict(r) for r in ast.walk(fn) if isinstance(r, ast.Return))
                or _falls_off_end(fn.body))

    print("SELF-TEST — the structural rule, faulted both ways")
    expect("W1 a bare `return` (THE BUG) -> flagged",
           flags("def f():\n    if x:\n        return\n    return True, 'landed', 'd'\n"), True)
    expect("W2 all exits return a 3-tuple verdict -> quiet",
           flags("def f():\n    if x:\n        return False, 'not_in_box', 'd'\n"
                 "    return True, 'landed', 'd'\n"), False)
    expect("W3 falling off the end -> flagged",
           flags("def f():\n    if x:\n        return True, 'landed', 'd'\n    print('oops')\n"), True)
    expect("W4 a 2-tuple (the contract before the `detail` field) -> flagged",
           flags("def f():\n    return True, 'landed'\n"), True)
    expect("W5 `return None` written out longhand -> flagged",
           flags("def f():\n    return None\n"), True)
    # ‼ THE ERROR-HANDLER CASE, and it is the one that mattered: the real function's `except` block
    # logged and fell through, which is how it returned `None` on the path a caller most needs.
    expect("W6 a try/except whose HANDLER falls through -> flagged",
           flags("def f():\n    try:\n        return True, 'landed', 'd'\n"
                 "    except Exception:\n        print('logged')\n"), True)
    expect("W8 try/except/ELSE whose `else` falls through -> flagged (was a blind spot)",
           flags("def f():\n    try:\n        pass\n    except Exception:\n"
                 "        return False, 'error', 'd'\n    else:\n        print('oops')\n"), True)
    expect("W9 the same `else` returning a verdict -> quiet",
           flags("def f():\n    try:\n        pass\n    except Exception:\n"
                 "        return False, 'error', 'd'\n    else:\n        return True, 'landed', 'd'\n"),
           False)
    expect("W7 the same handler returning a verdict -> quiet",
           flags("def f():\n    try:\n        return True, 'landed', 'd'\n"
                 "    except Exception:\n        return False, 'error', 'd'\n"), False)
    print(f"\nSELF-TEST {'PASS' if fails == 0 else 'FAIL'} ({fails} deviation(s))")
    return 0 if fails == 0 else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    print("=" * 92)
    print(f"WITHDRAW VERDICT GATE — the verdict must REACH the caller   [{BUILD}]")
    print("=" * 92)
    failures = check_structure() + check_caller_binds() + check_reporting()
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print("  every exit of withdraw_from_box returns a verdict, the caller BINDS it, and every")
        print("  report branch is correct — including 'unrecognised' and 'no verdict at all'")
    print("=" * 92)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
