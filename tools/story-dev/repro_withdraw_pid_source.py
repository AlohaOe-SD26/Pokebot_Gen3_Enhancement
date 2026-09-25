r"""GATE — a boxed HM carrier must still be collectable AFTER a counter has been hunted.

WHY THIS EXISTS (2026-09-25, the HM directive)
-----------------------------------------------
The heal's withdraw piggyback now serves TWO errands: collecting a hunted counter, and collecting a
boxed HM carrier. It has ONE pids slot, so one of them must win.

⛔⛔ **THE INTUITIVE ORDER IS WRONG, AND ITS FAILURE IS INVISIBLE TO THE OBVIOUS TEST.**
`_hunted_counter_pids` is **MONOTONIC**: created once (`story_mode.py:1974`), only ever `.add()`ed
(`:2563`), and **never cleared anywhere in the tree**. So `counter or hm` means that from the FIRST
counter hunt of a run onward, the HM carrier can never be collected again — and a test that does not
hunt a counter first passes happily.
By contrast `_wanted_hm_learner_pids` is armed for exactly ONE trip and disarmed in a `finally`.
⇒ the HM set must win, and the ordinary-heal behaviour must be byte-identical to before.

WHAT IT CHECKS
  S1  ⭐ THE REGRESSION THAT MOTIVATED THIS: HM pids present **AND** counter pids present (the
      monotonic state after any counter hunt) -> the HM pids win. `counter or hm` FAILS here.
  S2  NO HM ERRAND (the ordinary heal): HM empty, counters present -> counters, unchanged.
  S3  HM only -> HM.
  S4  Neither -> "none", and the returned pids stay falsy so `withdraw_precedence` still sees
      "nothing to defer".
  S5  THE LABEL IS TRUTHFUL — the source name matches the set actually returned. A label that can
      lie is worse than no label, because the run log is what a later reader believes.
  S6  IDENTITY, NOT A COPY — the returned object IS the set that was passed in, so a caller
      mutating or comparing it sees the same object.

⛔ ALL OFFLINE. The decision is pure; no emulator, no ROM, no bot mode.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent / "sandbox-pokebot"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def run() -> int:
    print("=" * 96)
    print("GATE — a boxed HM carrier stays collectable after a counter has been hunted")
    print("=" * 96)

    try:
        from modules.modes.util.higher_level_actions import withdraw_pid_source as pick
    except Exception as error:  # noqa: BLE001
        print(f"  ⛔ cannot import `withdraw_pid_source`: {error!r}")
        print("RESULT: FAIL — the decision under test is absent.")
        return 1

    hm = {0xAAAA}
    counters = {0xBBBB, 0xCCCC}   # monotonic: non-empty for the rest of the run

    # S1 — the regression this gate exists for
    pids, src = pick(hm, counters)
    check("S1 HM + counters (post-counter-hunt state) -> HM WINS",
          pids is hm and src == "hm-carrier",
          f"got src={src!r} pids={pids!r} — `counter or hm` would return the counters here")

    # S2 — the ordinary heal must be unchanged
    pids, src = pick(set(), counters)
    check("S2 no HM errand -> counters, unchanged", pids is counters and src == "counter",
          f"got src={src!r}")

    # S3 — HM only
    pids, src = pick(hm, set())
    check("S3 HM only -> HM", pids is hm and src == "hm-carrier", f"got src={src!r}")

    # S4 — neither; the pids must stay FALSY so precedence still sees "nothing to defer"
    pids, src = pick(set(), set())
    check("S4 neither -> 'none', and pids stay falsy", src == "none" and not pids,
          f"got src={src!r} pids={pids!r}")
    pids, src = pick(None, None)
    check("S4b None/None -> 'none', and pids stay falsy", src == "none" and not pids,
          f"got src={src!r} pids={pids!r}")

    # S5 — the label must not be able to lie
    lies = []
    for h, c in ((hm, counters), (set(), counters), (hm, set()), (set(), set())):
        p, s = pick(h, c)
        if s == "hm-carrier" and p is not h:
            lies.append(("hm-carrier", h, c))
        if s == "counter" and p is not c:
            lies.append(("counter", h, c))
        if s == "none" and p:
            lies.append(("none", h, c))
    check("S5 THE LABEL IS TRUTHFUL for every combination", not lies, f"lies {lies}")

    # S6 — identity, not a copy
    pids, _ = pick(hm, counters)
    check("S6 returns the SAME object, not a copy", pids is hm)

    print("=" * 96)
    if FAILURES:
        print(f"RESULT: FAIL — {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("RESULT: ALL PASS — the HM errand wins, ordinary heals are unchanged, the label cannot lie.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
