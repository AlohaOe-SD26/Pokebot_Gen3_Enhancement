# -*- coding: utf-8 -*-
"""GATE — the whiteout budget must spare runs that MOVED ON and still stop runs that are STUCK.

⛔⛔ WHY THIS EXISTS. `#24-whiteoutloop` was the batch's #1 failure class: **14 of 53 ended runs (26%)**
died on `Story: too many whiteout recoveries in a row`. The counter had **no reset site anywhere** —
five references in a 4,500-line file (init, increment, log, cap, message) — so "in a row" described
behaviour the code did not implement. It was a LIFETIME loss quota.

MEASURED over batch `20260907-113851`, recomputed locally from the raw logs:
    every killed run reached exactly recovery #41 (the `> 40` cap)
    distinct respawn maps per killed run  : median 13
    longest same-location streak ANYWHERE : max 20   (against a cap of 40)
    killed runs' battle win-rate          : 86-96%; one won 866 of 907 with an L51 lead
⇒ it was a fuse on run LENGTH, not a diagnosis. `MAX_FRAMES_PER_RUN` (5,000,000) is the real length
backstop and was never reached by ANY of the 61 runs.

WHY A GATE AND NOT A DRIVE. Reproducing this needs **41 whiteouts**, i.e. many hours of emulation, so
a drive is the wrong instrument (CLAUDE.md session-discipline rule 9: choose the instrument by the
question). The decision is PURE, so it is replayed against the REAL sequences instead — the same
reason `counter_withdraw_outcome` and `pick_land_hm_slot` are pure.

⛔ THE TRAP THIS GATE PROTECTS. It is tempting to "simplify" `whiteout_budget` to reuse
`_progress_sig()`, which the sibling `_derails` counter resets on forty lines away. `_progress_sig` is
`(party_size, lead_level, total_exp)`; between whiteout N and N+1 the bot walks back through wild
grass, so `total_exp` ALWAYS grows and the reset would fire EVERY time — silently deleting the guard.
FAULT ARM 3 fails exactly that rewrite.

Bare invocation runs every check. Exit 0 = PASS.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIXTURE = HERE / "fixtures" / "whiteout-sequences-20260907.json"
CAP = 40


def _load_budget():
    """Import the REAL function from the sandbox — never a local copy of it."""
    sandbox = ROOT / "sandbox-pokebot"
    if str(sandbox) not in sys.path:
        sys.path.insert(0, str(sandbox))
    import ast

    src = (sandbox / "modules" / "story" / "early_game.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "whiteout_budget":
            mod = ast.Module(body=[node], type_ignores=[])
            ns: dict = {}
            exec(compile(mod, "early_game.whiteout_budget", "exec"), ns)  # noqa: S102
            return ns["whiteout_budget"]
    raise SystemExit("⛔ `whiteout_budget` not found in sandbox early_game.py — was it renamed?")


def replay(budget, respawns, cap=CAP):
    """Run one real sequence through the budget. Returns (stopped, peak, resets)."""
    recoveries, last, peak, resets = 0, None, 0, 0
    for key in respawns:
        recoveries, stop, moved = budget(recoveries, last, key, cap)
        last = key
        peak = max(peak, recoveries)
        resets += bool(moved)
        if stop:
            return True, peak, resets
    return False, peak, resets


def main() -> int:
    if not FIXTURE.exists():
        print(f"⛔ fixture missing: {FIXTURE}")
        return 1
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    runs = data["runs"]
    budget = _load_budget()
    failures: "list[str]" = []

    print("=" * 92)
    print("GATE — whiteout budget: spare the runs that moved on, still stop the ones that are stuck")
    print("=" * 92)

    # ---- CHECK 1 — every really-killed run survives the new budget ------------------------------
    if len(runs) != 14:
        failures.append(f"fixture has {len(runs)} runs, expected the 14 killed ones")
    still_dying = []
    for r in runs:
        stopped, peak, resets = replay(budget, r["respawns"])
        if stopped:
            still_dying.append(f"{r['run']} (peak {peak})")
    print(f"\n  CHECK 1 — the 14 runs the old counter killed, replayed through the new budget:")
    print(f"            still stopped: {len(still_dying)} of {len(runs)}   (want 0)")
    if still_dying:
        failures.append("runs still killed: " + ", ".join(still_dying[:5]))

    peaks = sorted(replay(budget, r["respawns"])[1] for r in runs)
    print(f"            peak consecutive-at-one-location: max={peaks[-1]}, median="
          f"{peaks[len(peaks)//2]}, min={peaks[0]}   (cap is {CAP})")
    if peaks[-1] >= CAP:
        failures.append(f"a real run peaks at {peaks[-1]}, at or above the cap — no margin left")

    # ---- CHECK 2 — A GENUINELY STUCK RUN IS STILL STOPPED ---------------------------------------
    # ‼ THE HALF THAT MATTERS MOST. A budget that never fires is not a fix, it is a removed guard.
    stuck = ["MOSSDEEP CITY(0,6)"] * 45
    stopped, peak, _ = replay(budget, stuck)
    print(f"\n  CHECK 2 — 45 whiteouts at ONE location: stopped={stopped} at #{peak}   (want True/41)")
    if not stopped:
        failures.append("⛔ A GENUINELY STUCK RUN IS NOT STOPPED — the guard has been deleted")
    if peak != CAP + 1:
        failures.append(f"stuck run stopped at #{peak}, expected #{CAP + 1}")

    # ---- CHECK 3 — an UNREADABLE location must not reset (fail strict, never lax) ----------------
    blind = [None] * 45
    stopped_blind, peak_blind, _ = replay(budget, blind)
    print(f"  CHECK 3 — 45 whiteouts with an UNREADABLE location: stopped={stopped_blind} at "
          f"#{peak_blind}   (want True — unreadable must be STRICTER, never laxer)")
    if not stopped_blind:
        failures.append("⛔ an unreadable location resets the budget — the guard can be blinded")

    # ---- FAULT ARM 1 — a budget that never resets (today's bug) must FAIL check 1 ----------------
    never_reset = lambda rec, last, key, cap=CAP: (rec + 1, rec + 1 > cap, False)  # noqa: E731
    killed_again = sum(replay(never_reset, r["respawns"])[0] for r in runs)
    print(f"\n  FAULT ARM 1 — the OLD lifetime counter, replayed: kills {killed_again} of {len(runs)}"
          f"   (want {len(runs)} — this arm proves the fixture reproduces the bug)")
    if killed_again != len(runs):
        failures.append(f"⛔ FAULT ARM 1: the old counter kills only {killed_again}/{len(runs)} — "
                        "the fixture does NOT reproduce the defect, so CHECK 1 proves nothing")

    # ---- FAULT ARM 2 — a budget that ALWAYS resets must fail check 2 -----------------------------
    always_reset = lambda rec, last, key, cap=CAP: (1, 1 > cap, True)  # noqa: E731
    if replay(always_reset, stuck)[0]:
        failures.append("⛔ FAULT ARM 2 inert: an always-reset budget still stopped a stuck run")
    else:
        print(f"  FAULT ARM 2 — an ALWAYS-reset budget fails to stop the stuck run, as it must.")

    # ---- FAULT ARM 3 — THE `_progress_sig` REWRITE ----------------------------------------------
    # Models the tempting "just mirror `_derails`" change: the signal always differs between
    # whiteouts (total_exp grows on the walk back), so it resets every time.
    progress_sig_like = lambda rec, last, key, cap=CAP: (1, 1 > cap, True)  # noqa: E731
    if replay(progress_sig_like, stuck)[0]:
        failures.append("⛔ FAULT ARM 3 inert: the `_progress_sig` rewrite still stopped a stuck run")
    else:
        print("  FAULT ARM 3 — the `_progress_sig()` rewrite (resets every time, because total_exp\n"
              "                always grows on the walk back) fails to stop a stuck run, as it must.")

    print("\n" + "-" * 92)
    if failures:
        print("FAILED:")
        for f in failures:
            print("  " + f)
        return 1
    print(f"✅ PASS — {len(runs)} real killed runs all survive; a stuck run and a blind run are both")
    print(f"   still stopped at #{CAP + 1}; three fault arms fire. Margin: worst real peak "
          f"{peaks[-1]} vs cap {CAP}.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
