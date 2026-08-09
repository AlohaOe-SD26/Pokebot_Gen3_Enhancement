"""CONVERSION for a batch: hunts started vs counters actually caught — the one number that
grades the counter chain.

WHY THIS IS A SCRIPT NOW. It has lived as a copy-paste blob in `04-HANDOFF.md`, and this
project has twice been burned by an ad-hoc reading of batch logs (`08-MISTAKES`: a regex that
missed box-drawing characters and reported "Slugma encountered 0 times" when it was 34; a
partial mid-batch count compared against a final one). A blob cannot carry a positive control;
a script can, and must.

WHAT IT REPORTS, AND WHY THE SPLIT MATTERS
  * `hunts`    — `counter hunt — going to ... to catch <SPECIES>` events (hunts STARTED).
  * `reported` — `counter hunt CAUGHT <SPECIES>` events.
  * `REAL`     — reported catches whose species was ACTUALLY HUNTED in that batch.
‼ The third line exists because a "catch" of a species nobody hunted is a pre-existing party
mon being mislabelled, which is exactly how batch `20260808-174145` reported 13 catches when
only 3 were real. **Grade on REAL conversion.**

‼ POSITIVE CONTROL, printed before any result: the number of files opened and the total bytes
searched. A regex that matches nothing and a glob that found nothing produce the same `0`, and
telling them apart is the whole point — `x4-runs/` is gitignored, so the Grep TOOL silently
reports 0 on it and only a Bash-side read works at all.

Run:
    cd tools/story-dev
    PYTHONUTF8=1 py -3.12 analyse_conversion.py 20260809-081643
    PYTHONUTF8=1 py -3.12 analyse_conversion.py 20260809-081643 --compare 20260808-174145
"""
import argparse
import collections
import glob
import os
import re
import sys

HUNT_RE = re.compile(r"to catch ([A-Za-z]+)")
CAUGHT_RE = re.compile(r"counter hunt CAUGHT ([A-Za-z]+)")
FINISH_RE = re.compile(r"\bfinished\b")


def read_batch(stamp: str):
    """Return (hunts, caught, files, bytes_read) for one batch stamp."""
    pattern = os.path.join("x4-runs", stamp, "L0*", "stdout.txt")
    hunts, caught = collections.Counter(), collections.Counter()
    files = paths = 0
    total = 0
    for path in glob.glob(pattern):
        paths += 1
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        files += 1
        total += len(text)
        for m in HUNT_RE.finditer(text):
            hunts[m.group(1)] += 1
        for m in CAUGHT_RE.finditer(text):
            caught[m.group(1)] += 1
    return hunts, caught, files, total


def report(stamp: str) -> dict:
    hunts, caught, files, total = read_batch(stamp)
    print("=" * 78)
    print(f"BATCH {stamp}")
    print("=" * 78)
    # ---- positive control FIRST: prove the search saw something ----
    print(f"  CONTROL: {files} stdout file(s) read, {total:,} characters searched")
    if files == 0:
        print("  ‼ CONTROL FAILED — no lane stdout found. Wrong stamp, or the batch has not "
              "written anything yet. Every number below would be a false zero.")
        return {}
    if total == 0:
        print("  ‼ CONTROL FAILED — files found but empty.")
        return {}

    real = {k: v for k, v in caught.items() if k in hunts}
    false = {k: v for k, v in caught.items() if k not in hunts}
    n_hunts, n_reported, n_real = sum(hunts.values()), sum(caught.values()), sum(real.values())
    rate = (100.0 * n_real / n_hunts) if n_hunts else 0.0

    print(f"  hunts started : {n_hunts}   {dict(hunts)}")
    print(f"  reported catches: {n_reported}   {dict(caught)}")
    print(f"  REAL catches  : {n_real}   {real}")
    if false:
        print(f"  ‼ FALSE catches (species never hunted — pre-existing party mons): {false}")
    print(f"  ⇒ REAL CONVERSION: {n_real}/{n_hunts} = {rate:.1f}%")
    return {"hunts": n_hunts, "reported": n_reported, "real": n_real, "rate": rate,
            "per_species_hunts": dict(hunts), "per_species_real": real}


def two_proportion_z(x1: int, n1: int, x2: int, n2: int):
    """z for two independent proportions. Returns None when it cannot be computed."""
    if not n1 or not n2:
        return None
    p1, p2 = x1 / n1, x2 / n2
    p = (x1 + x2) / (n1 + n2)
    denominator = (p * (1 - p) * (1 / n1 + 1 / n2)) ** 0.5
    if denominator == 0:
        return None
    return (p1 - p2) / denominator


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stamp")
    ap.add_argument("--compare", default="", help="an earlier batch stamp to test against")
    args = ap.parse_args()

    now = report(args.stamp)
    if not now:
        return 1
    if not args.compare:
        return 0

    print()
    then = report(args.compare)
    if not then:
        return 1
    z = two_proportion_z(now["real"], now["hunts"], then["real"], then["hunts"])
    print()
    print("=" * 78)
    print(f"  {args.compare}: {then['real']}/{then['hunts']} = {then['rate']:.1f}%")
    print(f"  {args.stamp}: {now['real']}/{now['hunts']} = {now['rate']:.1f}%")
    if z is None:
        print("  z: not computable")
    else:
        verdict = "RESOLVABLE" if abs(z) >= 1.96 else "NOT resolvable — directional only"
        print(f"  z = {z:+.2f}  ⇒ {verdict}")
    # ‼ State the sample size next to the verdict. A conversion built on a handful of hunts
    # cannot resolve anything, and this project has read such a pair as a result before.
    print(f"  (sample: {now['hunts']} vs {then['hunts']} hunts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
