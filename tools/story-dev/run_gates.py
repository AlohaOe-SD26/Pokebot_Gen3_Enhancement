"""RUN THE STANDING GATE SUITE — one command, one exit code.

WHY THIS EXISTS. The suite was defined ONLY as a comment in `04-HANDOFF.md` ("THE 16-GATE SUITE"),
so running it depended on a human copying names out of prose. That failed in the obvious ways:
the handoff advertised **15** gates for a whole session after a 16th was added, and an older
version of the same list said "the ten standing `repro_*`" without naming them — which is not
reproducible. A list that must be remembered is not a gate; it is a wish.

‼ THE LIST LIVES HERE NOW, IN CODE. `04-HANDOFF.md` should point AT this file rather than
re-listing the names, so the two can never disagree again.

Usage:
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 run_gates.py
    PYTHONUTF8=1 py -3.12 run_gates.py --quick     # skip the slow ROM-loading probes

Exits 0 only if EVERY gate exits 0. Prints a one-line-per-gate summary and, for any failure, the
tail of that gate's output so the reason is on screen without hunting for a log.

‼ NEVER read an exit code through a pipe (`| head` reports ITS status, not the script's). This
runner captures each gate's output to a file and reads `returncode` directly — which is the same
mistake `04-HANDOFF.md` warns about, made impossible here.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

#: The standing suite. `slow=True` means it boots a ROM/emulator and takes real time.
GATES: list[tuple[str, bool]] = [
    ("preflight.py", False),
    ("lint_docs.py", False),
    # Tier 0 of the DOC CONSISTENCY LAYER (CLAUDE.md directive, 2026-08-13): the docs may not
    # contradict themselves or the code. Exists because a handoff passed its own quality bar and
    # still sent the next session to REBUILD FINISHED WORK. Self-test: `--self-test` (10 checks).
    ("audit_doc_consistency.py", False),
    ("verify_fixtures.py", False),
    ("audit_flag_names.py", False),
    ("repro_undefined_names.py", False),
    ("repro_no_silent_except.py", False),
    ("repro_roster_reorder.py", False),
    ("audit_encoding.py", False),
    ("repro_box_counter_move_test.py", False),
    ("repro_pid_identity_key.py", False),
    # ‼ KI-80. A boss cfg may not gain a `"grass"` key while `grass_is_fodder` is still the sole
    # gate on `_boss_plan_is_hopeless`/`_counter_ladder` — doing so SKIPS the counter machinery
    # for teams above the patch's band + 8, silently, behind a healthy-looking log line. The
    # punch list's own (P6) item asked for exactly that edit; this gate is why it cannot land by
    # accident. AST-based (a mention in a comment cannot trigger it) and SELF-RETIRING (it stops
    # enforcing the moment the coupling is removed). `--self-test` proves all four directions.
    ("repro_boss_grass_gate.py", False),
    # PARTY ACCOUNTING STAGE 0 (`06-DECISIONS-LOG.md` RULING D). Drives the REAL `get_party()` over
    # fabricated `gPlayerParty` memory to prove the divergence observer SEES each class
    # (HOLE/OVERFLOW/STALE/INVALID) and — the part that actually matters — that it changes NOTHING:
    # a byte-identical A/B against the hooks stubbed out, silence on a healthy party, and a
    # fault-injected observer that must break the LOG and never the party read.
    ("repro_party_accounting.py", False),
    # The SECOND half of the user-observed Slugma/Winona derail — not the bug, but why it took a
    # day to find. The heal's three PC piggybacks swallowed every exception, so "nothing to do"
    # and "it threw" were the same silence. Proves the two outcomes are now distinguishable, that
    # the reporter survives a broken console AND a broken run log, and — structurally — that no
    # handler in the heal has quietly reverted to `pass`.
    ("repro_heal_piggyback_reporting.py", False),
    ("repro_hm_slot_wiring.py", False),
    ("repro_multi_battle_partner.py", False),
    ("repro_whiteout_abort.py", False),
    ("repro_gym_whiteout_guard.py", True),
    ("probe_chapter_order.py", True),
    ("probe_dive_learner.py", True),
    ("probe_slot_free_plan.py", True),
    ("probe_regi_capabilities.py", True),
    ("probe_dive_routing.py", True),
    # KI-59 / `#24-impassabledirs`. Asserts the REAL production `PathTile` vectors match the decomp
    # on both halves (entry AND exit), on VICTORY_ROAD_1F (29 live tiles), with a NEGATIVE control
    # on SEAFLOOR_CAVERN_ROOM1 proving the branch is inert there. ‼ It reads production objects
    # rather than recomputing, because the probe that DID recompute (`probe_shoal_tide.py`)
    # reproduced the bug exactly and so could never have caught it.
    ("repro_impassable_dirs.py", True),
    # ‼ KI-65. `party_index` is assigned at ONE place inside a `try`; when the offer read fails the
    # name stays unbound and TWO later reads raise `UnboundLocalError` into swallowing `except`s —
    # so the HM veto (the "last line of defence") fails OPEN on the exact path it was written for,
    # and the CantForgetHM re-pick prints "Nothing else can be given up" while forgettable moves
    # exist. Two arms on an INJECTED fixture whose slot 0 is deliberately an HM (the only shape
    # that makes `:280` reachable — the two captured `movelearn_hmwedge_*.ss1` saves CANNOT test
    # this, measured, see the script docstring). ARM A must decline HONESTLY; ARM B is the control
    # the fix may not touch. Fault-tested 2026-08-16: reverted to HEAD, the gate FAILED on exactly
    # the lie + honest-message checks. It DRIVES the emulator, so a mention in a comment cannot
    # trigger it.
    ("repro_ki65_unbound_party_index.py", True),
    # `#24-orphans` (1), 2026-08-17. KI-79 made `withdraw_from_box` SAY the truth; every exit still
    # returned `None`, so the caller could not READ it and a failed withdraw was reported and then
    # silently tolerated. This asserts the verdict REACHES the caller — AST-structural, so a new
    # early `return` added later cannot quietly reintroduce the bug — plus the pure report mapping.
    # ⛔ It does NOT assert the withdraw works: that is the live two-armed `boxcounter2` A/B.
    # Fault-tested against REALITY, not only synthetics: `--build custom` (the unpromoted tree) FAILS
    # on exactly the bare returns and the discarded result. Self-test: `--self-test` (7 cases).
    ("repro_withdraw_verdict.py", False),
    # `#24-abortswallow` round 3, 2026-08-17. A broad `except` around a `yield from` in the story
    # path can swallow a whiteout; 16 such sites have been fixed, 36 candidates remain.
    # ⛔ IT IS A RATCHET, NOT A ZERO-THRESHOLD, and that is what made it gateable at all: the triage
    # MEASURED that ~64% of the candidates are not this defect, so demanding zero would be red on
    # arrival over correct-as-written code. ⛔ The "obvious" alternative — prune by whether an abort
    # SOURCE is reachable — was REFUTED by an observed failure (`mossdeep_gym.py:465` fabricated
    # "could not get out of the gym" on a dead run, and its body wraps only navigation primitives).
    # Fault-tested both ways: injecting ONE unguarded site takes it 36 -> 37 and exits 1.
    ("probe_abort_swallowing.py", False),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="skip gates that boot a ROM")
    ap.add_argument("--list", action="store_true", help="print the suite and exit")
    args = ap.parse_args()

    if args.list:
        for name, slow in GATES:
            print(f"{'SLOW' if slow else 'fast'}  {name}")
        return 0

    selected = [(n, s) for n, s in GATES if not (args.quick and s)]

    # ‼ CONTROL: a gate that does not EXIST must fail loudly, not be silently skipped. A suite that
    # quietly runs 14 of 16 and reports ALL PASS is exactly the "blind gate" shape this project has
    # been bitten by twice (audit_flag_names checking 2 files; the flag audit that exited 0 on a
    # phantom name).
    missing = [n for n, _ in selected if not (HERE / n).is_file()]
    if missing:
        print("‼ MISSING GATE SCRIPT(S) — refusing to report a pass over a suite that is not all here:")
        for n in missing:
            print(f"    {n}")
        return 1

    print("=" * 92)
    print(f"STANDING GATE SUITE — {len(selected)} gate(s)"
          f"{' (quick: ROM gates skipped)' if args.quick else ''}")
    print("=" * 92)

    results: list[tuple[str, int, float]] = []
    logs = HERE / ".gate-logs"
    logs.mkdir(exist_ok=True)

    for name, _slow in selected:
        started = time.monotonic()
        out = logs / f"{Path(name).stem}.txt"
        with out.open("w", encoding="utf-8", errors="replace") as handle:
            proc = subprocess.run(
                [sys.executable, name],
                cwd=HERE, stdout=handle, stderr=subprocess.STDOUT,
            )
        elapsed = time.monotonic() - started
        results.append((name, proc.returncode, elapsed))
        print(f"  {'PASS' if proc.returncode == 0 else 'FAIL'}  {name:<34} "
              f"exit={proc.returncode}  {elapsed:6.1f}s")

    failed = [(n, rc) for n, rc, _ in results if rc != 0]
    print("=" * 92)
    if not failed:
        total = sum(e for _, _, e in results)
        print(f"ALL {len(results)} GATES PASS  ({total:.1f}s total)")
        print("=" * 92)
        return 0

    print(f"FAILED: {len(failed)} of {len(results)}")
    for name, rc in failed:
        print(f"\n--- {name} (exit {rc}) — last 25 lines ---")
        tail = (logs / f"{Path(name).stem}.txt").read_text(encoding="utf-8", errors="replace")
        for line in tail.splitlines()[-25:]:
            print(f"    {line}")
    print("=" * 92)
    return 1


if __name__ == "__main__":
    sys.exit(main())
