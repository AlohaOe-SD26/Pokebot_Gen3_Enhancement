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

‼‼ **THE SOURCE IS `party_accounting_ledger.jsonl`, NOT THE HARNESS LOG — AND THAT IS A BUG FIX.**
The first version of this script scanned `harness*.log`. `story_harness.py` opens
`harness_<build>.log` in **`"w"` mode**, so every drive TRUNCATES the previous one: log-scanning
could only ever see ONE run, and this script's own "≥5 drives" criterion was **unreachable by
construction**. Shipped 2026-08-14, caught 2026-08-15 by asking whether the instrument could
produce the reading it demands — the same question that has now caught four blind instruments in
this project. The harness therefore appends one JSON row per drive to a durable ledger, and that
ledger is the population.

⛔ **LOG SCANNING IS NOW OPT-IN (`--logs GLOB`) AND YOU SHOULD NOT NEED IT.** Its first live run
double-counted: the ledger records `args.driver` (`ch20dive`) while a log yields `Ch20Dive` from
`CONTROLLER -> Ch20DiveMode.run`, so the fingerprints differed and ONE drive was reported as
**"2 drives / 2 distinct drivers / 51,046 recomputes"**. For a tool whose entire job is to say
*"there is enough evidence now"*, inflating the evidence is the worst failure available.
Fingerprints are casefolded and `mode`-stripped now, and the flag defaults OFF.

Exit 0 = the criterion is MET (Stage 1 may begin). Exit 1 = not yet, or a log could not be read.
‼ It exits non-zero while incomplete ON PURPOSE, so progress cannot be eyeballed into "good enough".

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 collect_party_accounting.py [--logs <glob>]
"""

import argparse
import json
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
    ap.add_argument("--logs", default=None, metavar="GLOB",
                    help="ALSO scan harness logs (e.g. 'harness*.log'). ⛔ OFF BY DEFAULT — see "
                         "the module docstring: log scanning double-counted a run on its first "
                         "live use, because the ledger and the log spell the driver differently.")
    args = ap.parse_args()

    print(BAR)
    print("(P3b) PARTY ACCOUNTING STAGE 0 — accumulated measurement")
    print(BAR)

    # ---- PRIMARY SOURCE: the durable append-only ledger -------------------------------------
    ledger_rows: "list[dict]" = []
    ledger_path = HERE / "party_accounting_ledger.jsonl"
    if ledger_path.is_file():
        for lineno, raw in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as error:
                # ‼ A row we cannot parse is not a row we may ignore — say so and refuse to present
                # the total as complete. ⚠ The realistic cause is a process killed mid-append, so
                # the damage is a truncated LAST line. Refusing the whole population for that is
                # deliberate (silently dropping a row biases the count) — but the message must make
                # the repair obvious, or a conservative check becomes a blocker. Raised by review.
                print(f"  ⛔ ledger line {lineno} is unparseable ({error}); totals are INCOMPLETE.")
                print(f"     Most likely a drive was killed mid-append, truncating the LAST line.")
                print(f"     REPAIR: delete line {lineno} of {ledger_path.name} and re-run. Each")
                print(f"     line is one independent drive, so removing a broken one loses exactly")
                print(f"     that drive — never re-hand-write a row, just re-run the driver.")
                return 1
            ledger_rows.append({
                "log": f"ledger:{lineno}",
                "driver": row.get("driver") or "<none>",
                "recomputes": int(row.get("recomputes", 0)),
                "scans": int(row.get("scans", 0)),
                "divergences": [(sig.split(":", 1)[0], sig.split(":", 1)[-1], n)
                                for sig, n in (row.get("divergences") or {}).items()],
                "observer_broke": bool(row.get("observer_broke")),
            })

    paths = sorted(HERE.glob(args.logs)) if args.logs else []
    if not paths and not ledger_rows:
        # ‼ A collector that finds nothing must SAY it found nothing, never report a clean sweep.
        print(f"  ⛔ NO LEDGER at {ledger_path.name} and no logs requested.")
        print("     This is 'I could not look', NOT 'there is no divergence'. Run a driver first.")
        print(BAR)
        return 1

    log_runs = [r for r in (scan(p) for p in paths) if r is not None]
    # ⛔⛔ DEDUPE — AND THE FINGERPRINT IS NORMALISED, WHICH IT WAS NOT THE FIRST TIME.
    # On its first live use this collector reported "2 drives / 2 distinct drivers / 51,046
    # recomputes" from a SINGLE run: the ledger records `args.driver` (`ch20dive`) while the log is
    # parsed from `CONTROLLER -> Ch20DiveMode.run` (`Ch20Dive`). Different case, different
    # fingerprint, no dedupe — and the population DOUBLED. ‼ For a tool whose only job is to say
    # "there is enough evidence now", silently inflating the evidence is the worst bug available.
    # ⇒ names are casefolded and a trailing "mode" stripped before comparison, and log scanning is
    # OFF unless explicitly asked for.
    def fingerprint(run: dict) -> tuple:
        name = run["driver"].casefold().removesuffix("mode")
        return name, run["recomputes"], run["scans"]

    ledger_fingerprints = {fingerprint(r) for r in ledger_rows}
    fresh_log_runs = [r for r in log_runs if fingerprint(r) not in ledger_fingerprints]
    deduped = len(log_runs) - len(fresh_log_runs)
    # ‼ Ledger rows are NEVER deduped against each other. Two genuine drives of the same driver can
    # legitimately produce identical numbers — `ch20dive` is deterministic and reports 25,523 every
    # time — and collapsing those would UNDER-count, which is the mirror of the over-count bug.
    runs = ledger_rows + fresh_log_runs
    if args.logs:
        print(f"  ⚠ --logs given: scanned {len(paths)} log(s); {deduped} already in the ledger and "
              f"were deduped, {len(fresh_log_runs)} added. Prefer the ledger alone.")
    if not runs:
        print(f"  ⛔ {len(paths)} log(s) matched but NONE carries a STAGE 0 SUMMARY line.")
        print("     Either they predate Stage 0, or the harness did not reach its end-of-run block.")
        print(BAR)
        return 1

    print(f"  ledger rows    : {len(ledger_rows)}   (source of record)")
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
        print(f"  ⇒ P3b is answered: no divergence was observable at this sample size.")
        print(f"  ‼ Report it as 'not observed in {total_recomputes:,}', NEVER as 'cannot happen'.")
        # ⛔ THE CAVEAT BELONGS IN THE TOOL, NOT ONLY IN THE HANDOFF. A reviewer noticed this
        # success path said a bare "Stage 1 may begin" while the docs carefully hedged — and the
        # TOOL is what a future session actually runs. A caveat that lives only in prose is a
        # caveat that gets skipped.
        print("  ⛔ CHECK THE POPULATION BEFORE ACTING. Read the driver list above: if they are all")
        print("     dungeon/route content with a STATIC party, then the scenarios most likely to")
        print("     make A differ from B — a catch into a FULL party, a Shedinja spawning unbidden")
        print("     — were never exercised. 'Clean' then means 'clean on THAT content', and it is")
        print("     NOT licence to re-point the ~35 capacity-shaped call sites at A.")
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
