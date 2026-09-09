# -*- coding: utf-8 -*-
"""MEASURE what a §Ch23 training refusal would actually cost, against what the run has left.

⛔ WHY THIS IS A CHECKED-IN TOOL. These figures were published in `03-PUNCH-LIST.md` from an agent's
report with no command behind them, and a reviewer refused them — correctly, because the project's own
rule is that a number in a doc must be traceable to a command a reader can re-run. Run this; cite this.

⛔⛔ FRAMES COME FROM DEBUG-LOG `f<N> [hb]` STAMPS, NEVER FROM THE PRINTED PER-RUN SUMMARY.
`story_mode.py`'s post-hoc report (`raw_frames = get_frame_count() - start_frame`) does NOT re-base
across the reset performed inside `super().run()`, so the printed total is wrong. The live enforcement
path DOES re-base, so the budget itself is correct — it is the REPORT that lies.
‼ A lane's debug log can hold MULTIPLE RUNS; a run's own start is its post-reset stamp, so segment on
the backward step in the f-sequence rather than trusting the file to be one run.

⚠ WHAT THE BUDGET IS, AND IS NOT. `MAX_FRAMES_PER_RUN = 5,000,000` lives in `StoryEndlessResetMode`
— the BATCH HARNESS. Production `StoryMode` has NO total-frame budget at all. So "spare" here means
"spare in a batch lane", and in production there is no such backstop: the per-call
`MAX_TRAINING_FRAMES` ceiling is the only pre-emptive bound that exists.

WHAT IT REPORTS
  * per refusal run: frames used, spare, % of the lane budget burned;
  * the training BILL — the sum of `estimate_frames_to_level` over EVERY battler under TRAIN_TARGET
    at that moment, not just the worst one. ‼ The production error message prints only
    `max(estimates)`, which is why this tree believed the blocker was ONE mon; it is 2-5.
  * the same bill with a 2-way EXP split, because `train_team` enables swap-training and the
    estimator has no participant divisor.

Always exits 0 — an OBSERVATION tool, not a gate.
"""
import json
import math
import pathlib
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
B = ROOT / "sandbox-pokebot"

BUDGET = 5_000_000                      # StoryEndlessResetMode.MAX_FRAMES_PER_RUN (harness only)
F = re.compile(r"^\s*f(\d+) \[hb\]", re.M)
PARTY = re.compile(r"party=\[(.*?)\]")
MON = re.compile(r"'?([A-Z][a-zA-Z]+)'?[: ]L?(\d+)")
BENCH = {"Zigzagoon", "Linoone", "Castform"}    # victory_road.BENCH_SPECIES


def _consts():
    src = (B / "modules/story/training_areas.py").read_text(encoding="utf-8")
    vr = (B / "modules/story/victory_road.py").read_text(encoding="utf-8")
    return (float(re.search(r"_CALIBRATED_AVG_WILD_BASE_EXP_YIELD\s*=\s*([\d.]+)", src).group(1)),
            int(re.search(r"FRAMES_PER_WILD_BATTLE\s*=\s*(\d+)", src).group(1)),
            int(re.search(r"WILD_MAX\s*=\s*(\d+)", vr).group(1)),
            int(re.search(r"TRAIN_TARGET\s*=\s*(\d+)", vr).group(1)),
            int(re.search(r"MAX_TRAINING_FRAMES\s*=\s*([\d_]+)", vr).group(1).replace("_", "")))


CAL, FPB, WILD, TARGET, CEIL = _consts()
_species = json.loads((B / "modules/data/species.json").read_text(encoding="utf-8"))
CURVE = {r["name"]: r.get("level_up_type") for r in _species if isinstance(r, dict) and r.get("name")}


def exp_for(level, kind):
    """Gen-3 growth curves (modules/pokemon.py). Unknown curve -> Medium Fast."""
    n = level
    if kind == "Fast":
        return (4 * n ** 3) // 5
    if kind == "Slow":
        return (5 * n ** 3) // 4
    if kind == "Medium Slow":
        return max(0, (6 * n ** 3) // 5 - 15 * n ** 2 + 100 * n - 140)
    if kind == "Erratic" or kind == "Fluctuating":
        return n ** 3            # approximation; flagged in the output
    return n ** 3                # Medium Fast


def bill(level, name, participants=1):
    kind = CURVE.get(name, "Medium Fast")
    need = exp_for(TARGET, kind) - exp_for(level, kind)
    if need <= 0:
        return 0
    xp = CAL * WILD / 7 / participants
    return math.ceil(need / xp) * FPB


rows = []
for batch_dir in sorted((ROOT / "tools/story-dev/x4-runs").glob("*")):
    for log in sorted(batch_dir.glob("*/debug-logs/*.log")):
        text = log.read_text(encoding="utf-8", errors="replace")
        if "alone needs" not in text:
            continue
        stamps = [int(m.group(1)) for m in F.finditer(text)]
        if len(stamps) < 5:
            continue
        segs, cur = [], [stamps[0]]
        for a, b in zip(stamps, stamps[1:]):
            (segs.append(cur), cur := [b]) if b < a else cur.append(b)      # noqa: E731
        segs.append(cur)
        seg = max(segs, key=len)
        used = seg[-1] - seg[0]

        best = None
        for m in PARTY.finditer(text):
            mons = [(n, int(l)) for n, l in MON.findall(m.group(1)) if 1 <= int(l) <= 100]
            if len(mons) >= 2 and (best is None or max(l for _, l in mons) > max(l for _, l in best)):
                best = mons
        under = [(n, l) for n, l in (best or []) if n not in BENCH and l < TARGET]
        solo = sum(bill(l, n) for n, l in under)
        split = sum(bill(l, n, participants=2) for n, l in under)
        rows.append((log.parent.parent.name, log.name[-10:-4], used, BUDGET - used,
                     100 * used / BUDGET, len(under), solo, split))

print("=" * 104)
print("§Ch23 TRAINING REFUSAL — what the FULL bill costs against what the lane has left")
print("=" * 104)
print(f"  constants: CAL={CAL} FRAMES/BATTLE={FPB} WILD_MAX={WILD} TRAIN_TARGET={TARGET} "
      f"per-call ceiling={CEIL:,}  lane budget={BUDGET:,}")
print(f"\n  {'lane':<5} {'log':<7} {'used':>10} {'spare':>10} {'burn':>6} {'under':>6} "
      f"{'bill solo':>11} {'bill 2-way':>11}  verdict")
for r in rows:
    v = "solo OVER" if r[6] > r[3] else "solo fits"
    v += " / 2-way OVER" if r[7] > r[3] else " / 2-way fits"
    print(f"  {r[0]:<5} {r[1]:<7} {r[2]:>10,} {r[3]:>10,} {r[4]:>5.1f}% {r[5]:>6} "
          f"{r[6]:>11,} {r[7]:>11,}  {v}")

if rows:
    burns = [r[4] for r in rows]
    spares = [r[3] for r in rows]
    unders = [r[5] for r in rows]
    print(f"\n  runs                : {len(rows)}")
    print(f"  burn %              : min {min(burns):.1f}  median {statistics.median(burns):.1f}  max {max(burns):.1f}")
    print(f"  spare frames        : min {min(spares):,}  median {int(statistics.median(spares)):,}  max {max(spares):,}")
    print(f"  battlers under L{TARGET}  : min {min(unders)}  median {statistics.median(unders)}  max {max(unders)}")
    print( "     ‼ the production message prints only max(estimates) — which is why this tree")
    print( "       believed the blocker was ONE mon.")
    print(f"  bill exceeds spare  : SOLO {sum(1 for r in rows if r[6] > r[3])}/{len(rows)}   "
          f"2-WAY {sum(1 for r in rows if r[7] > r[3])}/{len(rows)}")
    print( "\n  ⚠ Erratic/Fluctuating growth curves are approximated as Medium Fast here; species on")
    print( "    those curves may be mis-costed. Fast/Slow/Medium Slow/Medium Fast are exact.")
print("=" * 104)
