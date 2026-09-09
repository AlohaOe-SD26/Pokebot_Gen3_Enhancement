"""REPRO + GATE — the heal's PC piggybacks may never fail SILENTLY (the Slugma/Winona blind spot).

‼‼ THE FAILURE THIS CLOSES, AND IT IS THE USER'S OWN. On 2026-08-14 a Winona counter-hunt caught a
Slugma into the PC box, healed, **derailed to Manual**, and on continue re-fought Winona without
the counter. The root cause (`box_counter_pid` being type-only) is fixed and gated by
`repro_box_counter_move_test.py`. **This gate closes the second half: why it took a day to find.**

`heal_in_pokemon_center` piggybacks three PC actions between the nurse and the exit — the rotation
deposit, the KI-63 slot-freeing deposit, and the hunted-counter withdraw. All three were wrapped in
`except Exception: pass` under the contract *"a PC hiccup must not destroy a heal that already
succeeded"*. **The contract is right. The silence was not.** It made three states indistinguishable:

    it worked   ·   there was nothing to do   ·   it threw

In the user's run the withdraw block took the middle branch — correctly, given its (empty) input —
and said nothing. A single line naming the empty set would have pointed at the real bug on sight.

⛔ AND NO GATE COULD HAVE SAID SO. `repro_no_silent_except.py` did not scan
`modules/modes/util/` at all until this work, and — the sharper point — its **rule 3 escape hatch
(`# noqa: BLE001` plus prose) had already been used on all three of these handlers.** A
justification comment documents INTENT; it does not make a failure OBSERVABLE. Those three
handlers were counted LOUD by the gate while being, in fact, silent.

WHAT THIS PROVES:
  * `counter_withdraw_outcome` (extracted pure, exactly as `catch_confirmed` was) returns a
    DIFFERENT, informative message for the empty and non-empty cases. ‼ The two messages differing
    IS the fix — they used to be the same silence.
  * the empty-case message names `_hunted_counter_pids`, so the diagnosis is in the sentence.
  * ⛔ the empty case does NOT read as an error: it is the common case and must not cry wolf.
  * `_piggyback_report` NEVER raises — not with a broken console, not with a broken run log, not
    with both broken. It is telemetry on a path that must survive anything.
  * failures reach the CONSOLE; routine skips reach the RUN LOG only (a noisy diagnostic is one
    that gets ignored).
  * ⛔ STRUCTURAL: all three piggyback handlers actually CALL the reporter. A behavioural test of
    the reporter proves nothing if a handler quietly goes back to `pass`.

Exit 0 = all checks pass. Exit 1 = a check failed (details printed).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_heal_piggyback_reporting.py [--build sandbox|custom]
"""

import argparse
import ast
import pathlib
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"],
                 help="which fork to test (default sandbox; use custom to verify a promotion)")
_ARGS, _ = _ap.parse_known_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD_ROOT = REPO / f"{_ARGS.build}-pokebot"
sys.path.insert(0, str(BUILD_ROOT))

BAR = "=" * 96
TARGET = BUILD_ROOT / "modules" / "modes" / "util" / "higher_level_actions.py"


def main() -> int:
    failures = []
    performed = []

    def check(label, condition, detail=""):
        performed.append(label)
        status = "PASS" if condition else "FAIL"
        print(f"  {status}  {label}{('  — ' + detail) if detail else ''}")
        if not condition:
            failures.append(label)

    print(BAR)
    print("REPRO — the heal's PC piggybacks must never fail SILENTLY")
    print(f"BUILD UNDER TEST: {_ARGS.build}-pokebot")
    print(BAR)

    # ‼ ASSERT WHICH FORK, before testing anything. A gate that always imports sandbox cannot tell
    # you whether a promoted fix landed (that hole shipped once already — 07-CHANGELOG 2026-08-14).
    check("the file under test exists in the requested fork", TARGET.is_file(), str(TARGET))
    if not TARGET.is_file():
        print(f"\n{BAR}\nFAILED — cannot test a fork that does not contain the file\n{BAR}")
        return 1
    print(f"  (reading {TARGET.relative_to(REPO)} — verified)")

    # ---------------------------------------------------------------------------------------
    print("\n[ THE DECISION — the two states must be DISTINGUISHABLE, which is the whole fix ]")
    # ---------------------------------------------------------------------------------------
    # Imported by source-exec rather than a package import: `higher_level_actions` pulls in the
    # emulator-facing half of the bot at import time, and this gate must run with no ROM.
    # ⚠ CONSTRAINT, stated because an adversarial review asked: this only stays sound while the two
    # functions reference no module-level global. If one ever does, the exec namespace lacks it and
    # the gate CRASHES — a loud failure, not a silent false pass, so the technique is self-limiting.
    # ⛔ It also means this gate does NOT see the generator body; the STRUCTURAL AST check at the
    # bottom is what covers that, and it reads the real `heal_in_pokemon_center`.
    module_src = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(module_src)
    wanted = {"counter_withdraw_outcome", "_piggyback_report"}
    namespace: dict = {}
    extracted = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    exec(compile(ast.Module(body=extracted, type_ignores=[]), str(TARGET), "exec"), namespace)
    check("both functions were found and are importable in isolation",
          wanted <= set(namespace), f"found {sorted(set(namespace) & wanted)}")
    if not wanted <= set(namespace):
        print(f"\n{BAR}\nFAILED — the functions under test are missing\n{BAR}")
        return 1

    outcome = namespace["counter_withdraw_outcome"]
    report = namespace["_piggyback_report"]

    empty_should, empty_msg = outcome([])
    none_should, none_msg = outcome(None)
    some_should, some_msg = outcome([0x1111, 0x2222])

    check("an EMPTY pid set does not withdraw", empty_should is False, repr(empty_should))
    check("a None pid set does not withdraw (the attribute may not exist at all)",
          none_should is False, repr(none_should))
    check("a NON-EMPTY pid set does withdraw", some_should is True, repr(some_should))
    check("‼ the two messages DIFFER — they used to be the same silence",
          empty_msg != some_msg, f"{empty_msg[:40]!r} vs {some_msg[:40]!r}")
    check("the empty message NAMES the variable, so the diagnosis is in the sentence",
          "_hunted_counter_pids" in empty_msg, empty_msg[:80])
    check("the empty message names the SHAPE of the real bug, not just the state",
          "Slugma" in empty_msg or "registration" in empty_msg, empty_msg[:80])
    # ⛔ THE FALSE-POSITIVE CONTROL. The empty case is the COMMON case. If it reads as a failure,
    # every heal in every run cries wolf and the reader learns to ignore the whole channel —
    # strictly worse than the silence this replaces.
    check("⛔ the empty case does NOT read as an error (it is the common case)",
          "FAILED" not in empty_msg and "ERROR" not in empty_msg.upper(), empty_msg[:80])
    check("the withdraw message states HOW MANY, so a wrong count is visible",
          "2" in some_msg, some_msg)

    # ⛔ EQUIVALENCE WITH THE CODE THIS REPLACED. The original was a plain `if _pids:` — truthiness
    # and nothing more. If the extracted decision ever hinges on `len()` instead, an unsized-but-
    # truthy value raises, the outer handler catches it, and the withdraw is SKIPPED — which is
    # precisely the user-visible symptom this whole line of work exists to prevent. So: a truthy
    # object with NO `__len__` must still withdraw.
    class _TruthyUnsized:
        def __bool__(self):
            return True

    unsized_should, unsized_msg = outcome(_TruthyUnsized())
    check("⛔ a TRUTHY but UNSIZED pid set still withdraws (decision is bool(), never len())",
          unsized_should is True, f"{unsized_should!r} — {unsized_msg[:60]}")
    check("...and it says the count is unknown rather than inventing one",
          "unknown" in unsized_msg, unsized_msg[:70])

    class _TruthyBadLen:
        """Truthy, but `len()` raises something that is NOT a TypeError."""
        def __bool__(self):
            return True

        def __len__(self):
            raise ValueError("pathological __len__")

    bad_should, bad_msg = outcome(_TruthyBadLen())
    check("⛔ a __len__ raising a NON-TypeError still withdraws (the count is cosmetic)",
          bad_should is True, f"{bad_should!r} — {bad_msg[:60]}")

    class _FalsyRaising:
        def __bool__(self):
            return False

    falsy_should, _ = outcome(_FalsyRaising())
    check("a FALSY object does not withdraw (matches the original `if _pids:`)",
          falsy_should is False, repr(falsy_should))

    # ---------------------------------------------------------------------------------------
    print("\n[ ⛔ THE REPORTER MUST NEVER RAISE — it sits on a path that must survive anything ]")
    # ---------------------------------------------------------------------------------------
    import types

    def _run_with_broken(break_console: bool, break_logger: bool) -> "str | None":
        """Install broken stand-ins for the reporter's two outputs; return any exception."""
        saved = {name: sys.modules.get(name) for name in ("modules.console", "modules")}
        try:
            if break_console:
                bad = types.ModuleType("modules.console")

                class _Boom:
                    def print(self, *_a, **_k):
                        raise RuntimeError("fault-injected console failure")

                bad.console = _Boom()
                sys.modules["modules.console"] = bad
            if break_logger:
                bad_pkg = types.ModuleType("modules")

                class _BoomLogger:
                    @staticmethod
                    def event(*_a, **_k):
                        raise RuntimeError("fault-injected run-log failure")

                bad_pkg.debug_logger = _BoomLogger()
                sys.modules["modules"] = bad_pkg
            try:
                report("counter withdraw", "FAILED (fault-injected)", console_too=True)
                report("counter withdraw", "SKIPPED — routine")
                return None
            except Exception as error:  # noqa: BLE001 — capturing it IS the assertion
                return f"{type(error).__name__}: {error}"
        finally:
            for name, original in saved.items():
                if original is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = original

    check("survives a BROKEN console", _run_with_broken(True, False) is None,
          str(_run_with_broken(True, False)))
    check("survives a BROKEN run log", _run_with_broken(False, True) is None,
          str(_run_with_broken(False, True)))
    check("⛔ survives BOTH broken at once", _run_with_broken(True, True) is None,
          str(_run_with_broken(True, True)))

    # ---------------------------------------------------------------------------------------
    print("\n[ ⛔ STRUCTURAL — every piggyback handler must actually CALL the reporter ]")
    # ---------------------------------------------------------------------------------------
    # A behavioural test of the reporter proves nothing if a handler quietly reverts to `pass`.
    # This is the regression guard for the actual defect: three handlers that swallowed silently.
    heal = next((n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == "heal_in_pokemon_center"), None)
    check("`heal_in_pokemon_center` was located", heal is not None)
    if heal is not None:
        handlers = [n for n in ast.walk(heal) if isinstance(n, ast.ExceptHandler)]
        silent = []
        for handler in handlers:
            names = {sub.func.id for sub in ast.walk(handler)
                     if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)}
            if "_piggyback_report" not in names and not any(
                    isinstance(sub, ast.Raise) for sub in ast.walk(handler)):
                silent.append(handler.lineno)
        check("‼ NO except handler in the heal swallows without reporting",
              silent == [], f"silent handlers at lines {silent}")
        check("...and there are still THREE piggyback handlers to police (none deleted)",
              len(handlers) >= 3, f"{len(handlers)} handler(s)")

    # --- #24-pcpingpong: the heal must not REFILL a seat it was entered to EMPTY ---------------
    # ⭐ These drive the REAL decision function, not a fixture. The branch lives inside a generator
    # that needs a ROM, which is why it was extracted — on 2026-09-07 an untestable branch is
    # exactly how a feature shipped dead behind seven green checks.
    # MEASURED (37 batches, every `freeing ONE slot` attempt): 135/135 failures had a withdraw,
    # 9/9 successes did not, and the withdrawn mon was THE SAME MON just deposited in 135 of 135.
    from modules.modes.util.higher_level_actions import withdraw_precedence  # noqa: E402

    _pid = {0xABCD}
    # ‼ THE ORDINARY HEAL IS THE ONE THAT MUST NOT MOVE. This runs on every PC visit in the game;
    # a regression here is far more expensive than the bug being fixed.
    check("#24-pcpingpong: an ORDINARY heal still withdraws a boxed counter (shared path unchanged)",
          withdraw_precedence(_pid, False, False)[0] is True,
          str(withdraw_precedence(_pid, False, False)))
    check("#24-pcpingpong: an ordinary heal with nothing boxed still skips",
          withdraw_precedence(set(), False, False)[0] is False)
    check("#24-pcpingpong: a SLOT-FREEING visit DEFERS the withdraw (the fix)",
          withdraw_precedence(_pid, True, False)[0] is False,
          str(withdraw_precedence(_pid, True, False)))
    check("#24-pcpingpong: the deferral SAYS SO (a silent skip is how this survived)",
          "DEFERRED" in withdraw_precedence(_pid, True, False)[1]
          and "#24-pcpingpong" in withdraw_precedence(_pid, True, False)[1],
          withdraw_precedence(_pid, True, False)[1])
    # ⛔ THE A/B ARM MUST EXIST AND MUST RESTORE THE BUG. The 144-sample separation is a natural
    # CONTRAST, not an executed A/B; without a working fault arm the fix cannot ever be proven.
    check("#24-pcpingpong: POKEBOT_PCPINGPONG_FAULT restores the OLD behaviour (the A/B arm)",
          withdraw_precedence(_pid, True, True)[0] is True,
          str(withdraw_precedence(_pid, True, True)))
    # ⛔ THE MESSAGE MUST NOT LIE WHEN THERE IS NOTHING TO DEFER. A slot-freeing visit with NO
    # hunted counter must fall through to the accurate "SKIPPED — empty" message, not announce a
    # pending collection for a counter that does not exist. 9 of 144 such visits had no withdraw,
    # so this is a real branch. ‼ A guard that cannot tell "no" from "I broke" is worse than none.
    check("#24-pcpingpong: a slot-freeing visit with NO counter says SKIPPED, never DEFERRED",
          "DEFERRED" not in withdraw_precedence(set(), True, False)[1]
          and "empty" in withdraw_precedence(set(), True, False)[1],
          withdraw_precedence(set(), True, False)[1])

    print("\n" + BAR)
    if failures:
        print(f"FAILED — {len(failures)} of {len(performed)} check(s): {failures}")
        print(BAR)
        return 1
    print(f"ALL {len(performed)} CHECKS PASS")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
