"""(P3b) Aggregate the PARTY ACCOUNTING STAGE 0 measurement across drives, and GATE on it.

‼ WHY THIS EXISTS. Stage 0 shipped readers and a divergence log and wired no call site, on the
explicit basis that **nobody has ever measured whether A (`gPlayerPartyCount`) actually differs
from B (`len(get_party())`) in a real run.** Stage 1 — re-pointing ~35 capacity-shaped call sites
at A — is forbidden until that measurement exists.

⛔ **THE PROBLEM THIS FIXES IS A DOCUMENTATION ONE, AND A COLD-START AUDIT NAMED IT.** The handoff
said *"do not start Stage 1 until several LONG runs have reported"* — with no number, no command
and no owner. That is a prohibition you cannot earn your way past: the head of the live queue was
the one item in the file that was not executable. Now it is, and the criterion is CODE.

THE EXIT CRITERION (either one ends P3b):
  (a) **≥5 drives across ≥3 DIFFERENT drivers AND ≥250,000 total recomputes**, all clean; or
  (b) **the FIRST divergence of any class** (HOLE / OVERFLOW / INVALID / STALE).
(b) is the more useful outcome and it arrives sooner — a single real hole tells you more than a
million clean frames, because it converts "A can differ from B" from theory into a reproduction.

‼ **THE SAMPLE COUNTS ARE REPORTED, NEVER JUST THE VERDICT.** A "no divergence" line from a run
that recomputed 300 times is not evidence; this project has twice believed a negative from a
detector that could not have returned positive. STALE is additionally SAMPLED (1-in-300), so its
zero is weaker than the others' and is labelled as such.

⛔ **THIS SCRIPT MEASURES; IT DOES NOT DRIVE.** It cannot start an emulator, and it says so rather
than implying that reading a log is the same as taking a reading. Feed it by running the `ch20*`
drivers in `04-HANDOFF.md`'s HOW TO RUN / TEST — they exist, they PASS, and the accounting summary
rides along free on regression runs you would want anyway.

Exit 0 = the criterion is MET (Stage 1 may begin). Exit 1 = not yet, or a log could not be read.
‼ It exits non-zero while incomplete ON PURPOSE, so progress cannot be eyeballed into "good enough".

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 collect_party_accounting.py [--logs <glob>]
"""

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

#: The criterion, in one place so prose can never drift from it.
MIN_DRIVES = 5
MIN_DISTINCT_DRIVERS = 3
MIN_RECOMPUTES = 250_000

BAR = "=" * 96

#: `[PARTY-ACCT] STAGE 0 SUMMARY — 25523 get_party() recomputes, 86 full six-slot scans (...)`
SUMMARY_RE = re.compile(
    r"\[PARTY-ACCT\] STAGE 0 SUMMARY — ([\d,]+) get_party\(\) recomputes, ([\d,]+) full six-slot scans")
#: A divergence tally line: `[PARTY-ACCT]   HOLE:slot 1 of ...  x40`
TALLY_RE = re.compile(r"\[PARTY-ACCT\]\s+(HOLE|OVERFLOW|INVALID|STALE):(.*?)\s+x(\d+)\s*$")
#: The observer announcing it broke. ‼ A run with this line is UNMEASURED, not clean.
FAULT_RE = re.compile(r"\[PARTY-ACCT\] the Stage 0 party-accounting observer FAILED")
#: `--driver ch20dive` appears in the harness header; fall back to the log's own name.
DRIVER_RE = re.compile(r"CONTROLLER -> (\w+?)(?:Mode)?\.run")


def scan(path: pathlib.Path) -> "dict | None":
    """Read one harness log. Returns None when it holds no Stage 0 summary at all."""
    text = path.read_text(encoding="utf-8", errors="replace")
    summary = SUMMARY_RE.search(text)
    if summary is None:
        return None
    driver = DRIVER_RE.search(text)
    return {
        "log": path.name,
        "driver": driver.group(1) if driver else f"<unknown:{path.stem}>",
        "recomputes": int(summary.group(1).replace(",", "")),
        "scans": int(summary.group(2).replace(",", "")),
        "divergences": [(m.group(1), m.group(2), int(m.group(3))) for m in TALLY_RE.finditer(text)],
        "observer_broke": bool(FAULT_RE.search(text)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--logs", default="harness*.log",
                    help="glob for harness logs under tools/story-dev (default: harness*.log)")
    args = ap.parse_args()

    print(BAR)
    print("(P3b) PARTY ACCOUNTING STAGE 0 — accumulated measurement")
    print(BAR)

    paths = sorted(HERE.glob(args.logs))
    if not paths:
        # ‼ A collector that finds nothing must SAY it found nothing, never report a clean sweep.
        print(f"  ⛔ NO LOGS MATCHED {args.logs!r} under {HERE}.")
        print("     This is 'I could not look', NOT 'there is no divergence'. Run a driver first.")
        print(BAR)
        return 1

    runs = [r for r in (scan(p) for p in paths) if r is not None]
    skipped = len(paths) - len(runs)
    if not runs:
        print(f"  ⛔ {len(paths)} log(s) matched but NONE carries a STAGE 0 SUMMARY line.")
        print("     Either they predate Stage 0, or the harness did not reach its end-of-run block.")
        print(BAR)
        return 1

    print(f"  logs matched   : {len(paths)}  ({skipped} carried no summary and were skipped)")
    print(f"  drives counted : {len(runs)}\n")
    print(f"  {'driver':<22}{'recomputes':>12}{'scans':>8}   divergences")
    for r in runs:
        found = ", ".join(f"{k} x{n}" for k, _d, n in r["divergences"]) or "none"
        broke = "  ‼ OBSERVER BROKE — UNMEASURED" if r["observer_broke"] else ""
        print(f"  {r['driver']:<22}{r['recomputes']:>12,}{r['scans']:>8}   {found}{broke}")

    total_recomputes = sum(r["recomputes"] for r in runs)
    total_scans = sum(r["scans"] for r in runs)
    drivers = {r["driver"] for r in runs}
    # ‼ A run whose observer broke proves NOTHING either way and must not count toward the target.
    unmeasured = [r for r in runs if r["observer_broke"]]
    clean_drives = [r for r in runs if not r["observer_broke"]]
    divergences = [(r, d) for r in runs for d in r["divergences"]]

    print(f"\n  TOTAL: {total_recomputes:,} recomputes · {total_scans:,} six-slot scans · "
          f"{len(drivers)} distinct driver(s)")
    if unmeasured:
        print(f"  ‼ {len(unmeasured)} drive(s) had a BROKEN observer and do NOT count toward the target.")
    print("  ‼ STALE is sampled 1-in-300, so its zero is weaker evidence than HOLE/OVERFLOW/INVALID,")
    print("    which are exact. Read the scan count beside it, never the bare zero.")

    print("\n" + BAR)
    if divergences:
        print("✅ CRITERION (b) MET — A DIVERGENCE WAS OBSERVED. This is the useful outcome.")
        for r, (kind, detail, n) in divergences:
            print(f"    {kind} x{n}  in {r['driver']}  — {detail.strip()[:80]}")
        print("  ⇒ P3b is answered: A CAN differ from B in a real run. Reproduce this case, then")
        print("    design Stage 1 around it. ⛔ Index/cursor call sites STILL stay on B.")
        print(BAR)
        return 0

    met = (len(clean_drives) >= MIN_DRIVES
           and len(drivers) >= MIN_DISTINCT_DRIVERS
           and total_recomputes >= MIN_RECOMPUTES)
    if met:
        print(f"✅ CRITERION (a) MET — {len(clean_drives)} clean drives, {len(drivers)} distinct "
              f"drivers, {total_recomputes:,} recomputes, no divergence.")
        print("  ⇒ P3b is answered: no divergence was observable at this sample size. Stage 1 may")
        print("    begin. ‼ Report it as 'not observed in N', never as 'cannot happen'.")
        print(BAR)
        return 0

    print("🔜 NOT YET — the criterion is not met. Stage 1 may NOT begin.")
    print(f"    drives          {len(clean_drives):>4} / {MIN_DRIVES}")
    print(f"    distinct drivers{len(drivers):>4} / {MIN_DISTINCT_DRIVERS}")
    print(f"    recomputes {total_recomputes:>9,} / {MIN_RECOMPUTES:,}")
    print("  ⇒ Run more `ch20*` drivers (see 04-HANDOFF.md HOW TO RUN / TEST). ‼ This script")
    print("    MEASURES ONLY — it cannot drive the emulator, so it is not evidence by itself.")
    print(BAR)
    return 1


if __name__ == "__main__":
    sys.exit(main())
