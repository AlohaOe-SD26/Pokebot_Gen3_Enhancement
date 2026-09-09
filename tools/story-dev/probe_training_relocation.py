# -*- coding: utf-8 -*-
"""DOES A TRAINING RELOCATION EVER DELIVER BATTLES? Pair the decision with its outcome, per run.

⛔⛔ WHY THIS EXISTS, AND WHY IT IS CHECKED IN. This question has now been answered THREE times with
THREE different numbers, twice by a contaminated grep:
  * an agent reported 114 relocations / 114 unreachable drops, 1:1, "zero battles delivered";
  * I "refuted" it with 114 vs **128** — but 14 of my 128 were `FIERY_PATH is not reachable` lines
    from the COUNTER-HUNT subsystem that merely name ROUTE111 as the bot's CURRENT position;
  * an earlier pairing script of mine scored **116/116 as SUCCESS** because its regex captured `S`
    from `Story:` instead of the map name, and its fallback matched the word "training" — which
    appears inside the DROP message itself.
⇒ ‼ **A SUBSTRING IS NOT A MESSAGE.** Every pattern here is anchored on the FULL shape of the exact
line it means, and the tool prints the distinct shapes it matched so a reader can audit the filter
rather than trust the total.

THE TWO MESSAGES, verbatim shapes (from `story_mode.py` / `early_game.py`):
    RELOCATE : "Story: <MAP> (max L<N>) is fodder for a L<N> team — relocating to <MAP> (L<N>-<N>) …"
    DROP     : "Story: <MAP> (<x>, <y>) is not reachable from here — dropping it as a training option…"
⛔ NOT the counter-hunt shape, which is a different subsystem and must never be counted here:
    "Story: <MAP> is not reachable from here (Could not reach …) — trying the next counter destination."

Always exits 0 — an OBSERVATION tool, not a gate.
"""
import collections
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "x4-runs"

#: anchored on the TRAINING drop message: the map is followed by "(x, y)" and "dropping it as a
#: training option". The counter-hunt message has no coordinates after the map and ends differently.
DROP = re.compile(r"Story: ([A-Z0-9_]+) \(\d+, ?\d+\) is not reachable from here — dropping it as a "
                  r"training option")
RELOC = re.compile(r"Story: [A-Z0-9_]+ \(max L\d+\) is fodder for a L\d+ team — relocating to "
                   r"([A-Z0-9_]+)")
#: the counter-hunt look-alike, counted separately so it can be SEEN rather than silently excluded
COUNTER = re.compile(r"Story: ([A-Z0-9_]+) is not reachable from here \(Could not reach")
BOUND = "ENDLESS RESET: run"


def main() -> int:
    batches = sorted({p.parent.parent.name for p in RUNS.glob("*/L0*/stdout.txt")})
    if not batches:
        print("  ⛔ no x4-runs stdout files found — nothing to measure.")
        return 0

    print("=" * 100)
    print("TRAINING RELOCATION — does the decision ever deliver battles?")
    print("=" * 100)

    shapes = collections.Counter()
    outcomes = collections.Counter()
    per_batch = []
    segments = 0

    for b in batches:
        r = d = c = 0
        for f in (RUNS / b).glob("L0*/stdout.txt"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for chunk in text.split(BOUND):
                lines = chunk.splitlines()
                if not lines:
                    continue
                segments += 1
                for i, line in enumerate(lines):
                    if COUNTER.search(line):
                        c += 1
                        shapes["COUNTER-HUNT look-alike (excluded)"] += 1
                    if DROP.search(line):
                        d += 1
                        shapes["TRAINING drop"] += 1
                    m = RELOC.search(line)
                    if not m:
                        continue
                    r += 1
                    shapes["RELOCATE decision"] += 1
                    target, verdict = m.group(1), "no signal in window"
                    for nxt in lines[i + 1:i + 60]:
                        dm = DROP.search(nxt)
                        if dm and dm.group(1) == target:
                            verdict = "DROPPED as unreachable"
                            break
                        # battle evidence must NOT be the drop message's own wording
                        if ("defeats on this map" in nxt or "spin" in nxt.lower()
                                or "levelled" in nxt.lower() or "reached Lv" in nxt):
                            verdict = "battles delivered"
                            break
                    outcomes[verdict] += 1
        if r or d or c:
            per_batch.append((b, r, d, c))

    print(f"  run segments scanned: {segments:,}\n")
    print(f"  {'batch':<20}{'relocate':>10}{'training drop':>15}{'counter look-alike':>20}")
    for b, r, d, c in per_batch:
        print(f"  {b:<20}{r:>10}{d:>15}{c:>20}")
    tr = sum(x[1] for x in per_batch)
    td = sum(x[2] for x in per_batch)
    tc = sum(x[3] for x in per_batch)
    print(f"  {'TOTAL':<20}{tr:>10}{td:>15}{tc:>20}")
    print("\n  ‼ the last column is the look-alike this tool EXCLUDES. A naive"
          "\n    '<MAP> AND is not reachable' grep folds it in and inflates the drop count.")

    print("\n  DISTINCT shapes matched (audit the filter, not the total):")
    for k, n in shapes.most_common():
        print(f"    {n:>5}x  {k}")

    print("\n  OUTCOME of each relocation decision, paired WITHIN its run:")
    total = sum(outcomes.values()) or 1
    for k, n in outcomes.most_common():
        print(f"    {n:>5}  ({100 * n / total:>5.1f}%)  {k}")
    print("\n  ⚠ 'no signal in window' is an UNKNOWN, never a success.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
