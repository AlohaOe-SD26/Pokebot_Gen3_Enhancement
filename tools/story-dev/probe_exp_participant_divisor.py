# -*- coding: utf-8 -*-
"""DOES PARTICIPATING IN A BATTLE HALVE EACH MON'S EXP? Measure it, don't recall it.

⛔⛔ THE QUESTION BENEATH THE QUESTION. `estimate_frames_to_level` models a SOLO fight and has **no
participant divisor**, so every training estimate in this project assumes the trainee banks the whole
payout. If Gen 3 divides exp among participants, each estimate is up to **2x optimistic**, the
arrival level clearing the 250,000-frame ceiling is **L42 rather than L35**, and
`#24-lowlevelmules`'s planned "catch higher + train the remainder" fix **refuses on its own
arithmetic**.

⭐ WHY THIS TOOL EXISTS ALONGSIDE `probe_swaptrain_exp_split.py`. That one answered *"how many mon
gain in a swap-training window?"* — 11 of 14 windows had TWO. But two mon gaining the SAME number is
equally consistent with *"each got a full share"* and *"each got half"*, so **the count cannot
settle the divisor**. ‼ That is the project's own rule biting again: *instrument the ACTION, not a
proxy for it.* The action here is the AMOUNT, and the only honest test is a CONTROLLED COMPARISON —
same foe species and level, 1 participant vs 2.

METHOD, and its guards:
  * a window is the span between two `ids=` heartbeats containing EXACTLY ONE battle (multi-battle
    windows are excluded and REPORTED — attributing two payouts to one event is the "an aggregate
    cannot attribute" failure logged here twice);
  * participants = party members whose `exp` rose across that window;
  * ⛔ **PAIRED BY (foe species, foe level)** — comparing raw means across all foes would confound
    the divisor with which foes happen to be fought in each mode. Only groups holding BOTH a
    1-participant and a 2-participant observation are compared;
  * the headline is the RATIO of per-mon exp, 2p vs 1p, within those matched groups.
    **~1.0 ⇒ no divisor (solo model correct). ~0.5 ⇒ the payout is halved per participant.**

Always exits 0 — an OBSERVATION tool, not a gate.
"""
import argparse
import collections
import pathlib
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent

FRAME = re.compile(r"^f(\d+)\s")
IDS = re.compile(r"ids=\[([^\]]*)\]")
ONE_ID = re.compile(r"'(\w+)#([0-9A-F?]{8}):L(\d+):exp(\d+)'")
TURN0 = re.compile(r"\[TURN 0\]\s+\w+\s+L\d+\s+\d+/\d+\s*(?:\[[^\]]*\]\s*)?->\s*\w+.*?vs\s+(\w+)\s+L(\d+)")
ANY_TURN0 = re.compile(r"\[TURN 0\]")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batch", default="latest")
    a = ap.parse_args()
    runs = HERE / "x4-runs"
    if a.batch == "latest":
        cands = sorted([p for p in runs.iterdir() if p.is_dir() and list(p.glob("L0*"))])
        bdir = cands[-1] if cands else None
    else:
        bdir = runs / a.batch
    if bdir is None or not bdir.exists():
        print("  ⛔ no batch found.")
        return 0

    print("=" * 104)
    print(f"EXP PARTICIPANT DIVISOR — batch {bdir.name}")
    print("=" * 104)

    #: (foe_species, foe_level) -> {n_participants: [per-mon exp, ...]}
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    single = multi = ids_lines = 0

    for f in sorted(bdir.rglob("*.log")):
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:  # noqa: BLE001
            continue
        beats = []
        for i, line in enumerate(lines):
            if not FRAME.match(line):
                continue
            m = IDS.search(line)
            if not m:
                continue
            ids_lines += 1
            beats.append((i, {pid: int(exp) for _sp, pid, _lv, exp in ONE_ID.findall(m.group(1))}))

        for (i0, d0), (i1, d1) in zip(beats, beats[1:]):
            seg = lines[i0 + 1:i1]
            starts = [l for l in seg if ANY_TURN0.search(l)]
            if len(starts) == 0:
                continue
            if len(starts) > 1:
                multi += 1
                continue
            single += 1
            foe = None
            for l in seg:
                m = TURN0.search(l)
                if m:
                    foe = (m.group(1), int(m.group(2)))
                    break
            if foe is None:
                continue
            gains = [d1[p] - d0[p] for p in d0 if p in d1 and d1[p] > d0[p]]
            if not gains or len(gains) > 2:
                continue
            # every participant should bank the same amount; use the max as the per-mon figure
            groups[foe][len(gains)].append(max(gains))

    print(f"  heartbeats with ids=: {ids_lines:,}")
    print(f"  single-battle windows: {single:,}   ⛔ multi-battle EXCLUDED: {multi:,}")

    matched = {k: v for k, v in groups.items() if 1 in v and 2 in v}
    print(f"  (foe species, level) groups seen: {len(groups):,}   "
          f"‼ with BOTH 1p and 2p observations: {len(matched):,}")
    if not matched:
        print("\n  ⚠ no matched group — cannot compare without confounding foe choice. Longer batch.")
        print("=" * 104)
        return 0

    ratios = []
    print(f"\n  {'foe':<22}{'n1':>4}{'exp@1p':>9}{'n2':>4}{'exp@2p':>9}{'ratio':>8}")
    for foe, d in sorted(matched.items(), key=lambda kv: -(len(kv[1][1]) + len(kv[1][2])))[:14]:
        m1, m2 = statistics.median(d[1]), statistics.median(d[2])
        r = m2 / m1 if m1 else 0
        ratios.append(r)
        print(f"  {foe[0] + ' L' + str(foe[1]):<22}{len(d[1]):>4}{m1:>9.0f}"
              f"{len(d[2]):>4}{m2:>9.0f}{r:>8.2f}")

    # ⛔ REPORT THE CONVERGENCE, NEVER ONE NUMBER. The first version medianed all 87 group ratios
    # with EQUAL WEIGHT and printed 0.838/INCONCLUSIVE while every large-sample group sat at
    # 0.50-0.54: a group with n2=7 outvoted one with n2=29. An unweighted median over GROUPS is a
    # summary of the groups, not of the observations.
    print(f"\n  {'min n2':>8}{'groups':>9}{'median ratio':>15}   (the convergence IS the result)")
    ladder = []
    for minn in (1, 5, 10, 20):
        s = [m2 / m1 for _f, d in matched.items()
             for m1, m2 in [(statistics.median(d[1]), statistics.median(d[2]))]
             if m1 and len(d[2]) >= minn]
        if s:
            ladder.append((minn, len(s), statistics.median(s)))
            print(f"  {minn:>8}{len(s):>9}{statistics.median(s):>15.3f}")

    p1 = [x for _f, d in groups.items() for x in d.get(1, [])]
    p2 = [x for _f, d in groups.items() for x in d.get(2, [])]
    if p1 and p2:
        print(f"\n  pooled (confounded by foe mix — a SANITY CHECK, not the result):"
              f" {statistics.median(p1):.0f} -> {statistics.median(p2):.0f} exp"
              f"  = {statistics.median(p2)/statistics.median(p1):.2f}"
              f"   (n={len(p1):,} vs {len(p2):,})")

    best = ladder[-1] if ladder else None
    print("  " + "-" * 100)
    if best and best[1] >= 2 and best[2] < 0.72:
        print(f"  ⇒ ⛔⛔ **CONSISTENT WITH A 2-WAY SPLIT.** The ratio converges toward 0.5 as the")
        print(f"     sample grows (best stratum: n2>={best[0]}, {best[1]} groups, {best[2]:.3f}).")
        print("     `estimate_frames_to_level` has NO participant divisor ⇒ every training estimate")
        print("     where swap-training fires is up to 2x OPTIMISTIC, and the arrival level clearing")
        print("     the 250,000-frame ceiling is **L42, not L35**.")
        print(f"  ‼ STRENGTH, STATED: only {best[1]} group(s) reach n2>={best[0]}. This CONFIRMS the")
        print("     project's existing corrected arithmetic; it is not yet a decisive independent")
        print("     proof. A longer batch raises n2 — nothing else is needed.")
    elif best and best[2] > 0.88:
        print("  ⇒ ✅ **NO DIVISOR — each participant banks a full share.** The L35 bar stands.")
    else:
        print("  ⇒ ⚠ NOT ENOUGH MATCHED HIGH-n GROUPS YET. Do not read the top row as the answer —")
        print("     it is dominated by groups with a handful of observations.")
    print("=" * 104)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
