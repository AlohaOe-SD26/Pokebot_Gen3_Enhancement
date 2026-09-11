#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Would `#24-maintain` ever have FIRED in real runs, and would it still have been AFFORDABLE?

⛔ WHY THIS EXISTS — SO A BATCH IS NOT RUN BLIND. The A/B (2026-09-11) proved the mechanism works on
one staged laggard. It did NOT show the feature ever gets a chance in a real run. Those are different
questions, and a 3-hour batch is an expensive way to discover the answer is "it never fires".

⇒ This mines HEARTBEATS from batches we ALREADY HAVE. Each carries the full party
(`party=['Mightyena L51', …, 'Marill L13']`), so the whole history of every laggard is on disk.

THE QUESTION IT ANSWERS, and it is the one the feature lives or dies on:
  **When a mon first falls more than TRAIN_CATCHUP_GAP behind, is closing that gap still CHEAP?**
  If yes, maintenance has a real window and a batch is worth running.
  If the gap is already unaffordable the moment it opens, the feature can never help and the batch
  would measure nothing.

‼ WHAT THIS IS NOT. It is not evidence the feature IMPROVES anything — it cannot be, because these
runs were recorded with the feature OFF. It bounds the OPPORTUNITY. Rule 9: drivers answer
correctness, batches answer frequency; this sizes the prize before paying for the batch.

⚠ The proxy: maintenance fires when a battler is below `boss_target - GAP`, and the boss target
tracks the party's level. Heartbeats do not record the boss target, so this uses **gap to PARTY MAX**
as the stand-in. That is stated, not hidden — it slightly OVER-counts (party max runs a little ahead
of the boss target), so a "no window" result here would be conclusive while a "window exists" result
is an upper bound.

Usage:
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_maintain_window.py
    PYTHONUTF8=1 py -3.12 probe_maintain_window.py --batch 20260910-234959 --gap 6 --budget 150000
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNS = HERE / "x4-runs"
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))

from modules.story import training_areas as ta                      # noqa: E402
from modules.pokemon import get_species_by_name                     # noqa: E402

#: `party=['Mightyena L51 143/143', 'Marill L13 44/44']`
PARTY_RE = re.compile(r"party=\[(.*?)\]")
MON_RE = re.compile(r"'([A-Za-z0-9' .\-♀♂]+?) L(\d+)")


def wild_max(map_enum):
    return next((b[1] for m, _t, b in ta.TRAINING_GRASS if m == map_enum), None)


_curve_cache: dict = {}


def est_frames(species: str, frm: int, to: int) -> "int | None":
    """Frames to lift `species` from `frm` to `to` on the ground its OWN level selects."""
    if to <= frm:
        return 0
    ground = ta.best_training_grass(frm)
    if ground is None:
        return None
    wild = wild_max(ground[0])
    if not wild:
        return None
    if species not in _curve_cache:
        try:
            _curve_cache[species] = get_species_by_name(species).level_up_type
        except Exception:                                            # noqa: BLE001
            _curve_cache[species] = None
    curve = _curve_cache[species]
    if curve is None:
        return None
    need = curve.get_experience_needed_for_level(to) - curve.get_experience_needed_for_level(frm)
    if need <= 0:
        return 0
    per = ta._CALIBRATED_AVG_WILD_BASE_EXP_YIELD * wild / 7
    return math.ceil(need / per) * ta.FRAMES_PER_WILD_BATTLE


def scan_lane(path: Path, gap: int, budget: int) -> list[dict]:
    """One lane -> one record per mon that ever fell more than `gap` behind."""
    first_behind: dict = {}
    last_seen: dict = {}
    order = 0
    for log in sorted(path.glob("debug-logs/*.log")):
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in PARTY_RE.finditer(text):
            mons = MON_RE.findall(m.group(1))
            if len(mons) < 2:
                continue
            order += 1
            levels = [(s, int(lv)) for s, lv in mons]
            top = max(lv for _s, lv in levels)
            for species, lv in levels:
                last_seen[species] = (lv, top, order)
                if top - lv > gap and species not in first_behind:
                    first_behind[species] = (lv, top, order)

    out = []
    for species, (lv, top, when) in first_behind.items():
        end_lv, end_top, _ = last_seen.get(species, (lv, top, when))
        out.append({
            "species": species,
            "first_lv": lv, "first_top": top, "first_gap": top - lv, "first_at": when,
            "end_lv": end_lv, "end_top": end_top, "end_gap": end_top - end_lv,
            "cost_then": est_frames(species, lv, top - gap),
            "cost_end": est_frames(species, end_lv, end_top - gap),
            "budget": budget,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", default=None, help="batch dir name (default: every batch)")
    ap.add_argument("--gap", type=int, default=6, help="TRAIN_CATCHUP_GAP")
    ap.add_argument("--budget", type=int, default=150_000, help="MAINTAIN_MAX_FRAMES")
    args = ap.parse_args()

    batches = ([RUNS / args.batch] if args.batch
               else sorted(d for d in RUNS.iterdir() if d.is_dir() and d.name[:4].isdigit()))
    if not batches:
        print("  ⛔ no batches found under x4-runs/")
        return 2

    rows: list[dict] = []
    lanes = 0
    for b in batches:
        for lane in sorted(p for p in b.iterdir() if p.is_dir() and p.name.startswith("L")):
            lanes += 1
            rows.extend(scan_lane(lane, args.gap, args.budget))

    print("=" * 100)
    print("MAINTENANCE OPPORTUNITY — mined from heartbeats in batches ALREADY ON DISK")
    print("=" * 100)
    print(f"  batches {len(batches)}  lanes {lanes}  laggard-episodes {len(rows)}")
    print(f"  gap {args.gap}   budget {args.budget:,}")
    print(f"  ⚠ proxy: gap to PARTY MAX (heartbeats do not record the boss target)\n")
    if not rows:
        print("  no mon ever fell more than the gap behind — nothing for maintenance to do.")
        return 0

    afford_then = [r for r in rows if r["cost_then"] is not None and r["cost_then"] <= args.budget]
    afford_end = [r for r in rows if r["cost_end"] is not None and r["cost_end"] <= args.budget]

    print(f"  {'when it FIRST fell behind':<42}{'when the run ENDED':<34}")
    print(f"  {'affordable to fix':<20}{len(afford_then):>5} / {len(rows):<14}"
          f"{'affordable to fix':<20}{len(afford_end):>5} / {len(rows)}")
    print()
    med_then = sorted(r["first_gap"] for r in rows)[len(rows) // 2]
    med_end = sorted(r["end_gap"] for r in rows)[len(rows) // 2]
    print(f"  median gap  first {med_then:>3}   ->   end {med_end:>3}")
    costs_then = sorted(r["cost_then"] for r in rows if r["cost_then"] is not None)
    costs_end = sorted(r["cost_end"] for r in rows if r["cost_end"] is not None)
    if costs_then:
        print(f"  median cost first {costs_then[len(costs_then) // 2]:>9,} frames")
    if costs_end:
        print(f"  median cost end   {costs_end[len(costs_end) // 2]:>9,} frames")

    print("\n  worst 8 episodes, by the gap they ended at:")
    print(f"    {'species':<12}{'first':>18}{'cost then':>12}{'end':>16}{'cost end':>12}")
    for r in sorted(rows, key=lambda r: -r["end_gap"])[:8]:
        # ⛔ BUILD EVERY FIELD FIRST. Nested quotes and conditionals inside an f-string are how this
        # session produced two separate format bugs already (a ternary binding to a whole implicit
        # concatenation, and a conditional inside a FORMAT SPEC). Plain locals, then one format.
        ct = "n/a" if r["cost_then"] is None else f"{r['cost_then']:,}"
        ce = "n/a" if r["cost_end"] is None else f"{r['cost_end']:,}"
        first_txt = f"L{r['first_lv']} vs {r['first_top']}"
        end_txt = f"L{r['end_lv']} vs {r['end_top']}"
        name = r["species"][:11]
        print(f"    {name:<12}{first_txt:>18}{ct:>12}{end_txt:>16}{ce:>12}")

    print()
    print("=" * 100)
    pct_then = 100.0 * len(afford_then) / len(rows)
    pct_end = 100.0 * len(afford_end) / len(rows)
    print(f"  ⭐ THE WINDOW: {pct_then:.0f}% of laggards were CHEAP to fix when they first fell behind;")
    print(f"     only {pct_end:.0f}% still were by the end of the run.")
    if pct_then >= 60 and pct_then - pct_end >= 20:
        print("  ✅ A REAL WINDOW EXISTS — acting early is materially cheaper than acting late,")
        print("     so a batch with POKEBOT_MAINTAIN=1 has something to measure.")
    elif pct_then < 30:
        print("  ⛔ NO WINDOW — most laggards are ALREADY unaffordable the moment they fall behind.")
        print("     A batch would measure nothing; fix the ACQUISITION of low-level mons instead.")
    else:
        print("  ⚠ AMBIGUOUS — the window is narrow. Read the episodes before committing batch time.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
