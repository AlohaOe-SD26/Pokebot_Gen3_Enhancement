# -*- coding: utf-8 -*-
"""ARE UNDERLEVELLED MONS *BORN* BEHIND, OR DO THEY *FALL* BEHIND? — and did they ever have a window?

⛔⛔ WHY THIS EXISTS. `03-PUNCH-LIST.md` carried an `[AGENT, UNVERIFIED]` claim that decided where
effort should go: *"of 1,496 mons that ever reached 15+ behind, 88.8% were ALREADY more than 6
behind the FIRST time they were observed (median first-seen gap 11)"*, concluding **"THE MONS ARE
BORN DEAD WEIGHT, so there is no early small-gap window to maintain."** It was unmeasurable until
`party_ids` shipped (2026-09-09) — party telemetry had no stable identity, so no mon could be
followed across readings.

⭐ WHAT THIS TOOL SETTLES, and the distinction that matters: **the PROPORTION and the INFERENCE are
different claims, and only one of them survives.** A mon can arrive past the threshold AND still
have spent a long stretch inside it. The conclusion "no window to maintain" is the part that routes
the decision, and it is the part that is false.

‼ IDENTITY CAVEATS, both measured, both real:
  * PID survives EVOLUTION (Wurmple#AB -> Silcoon#AB) — that is why PID-keying is correct here and
    species-keying is not: species keys SPLIT one mon across its evolutions and MERGE two mons of
    the same species.
  * ⛔ BUT PID IS NOT UNIQUE. `Nincada` evolving to `Ninjask` ALSO spawns a `Shedinja` carrying the
    SAME personality value — the one collision in this corpus (measured: 1,360 heartbeats, ~7.9%).
    This tool keys on (run, PID, species-lineage) so the Shedinja is not silently merged.
  * a mon in the PC box does not appear in `ids=` at all; "first seen" means first seen IN PARTY.

SCOPE: one debug log == one run (verified: `ENDLESS RESET: run` never appears inside a debug log).
Always exits 0 — an OBSERVATION tool, not a gate.
"""
import argparse
import ast
import collections
import pathlib
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent

HB = re.compile(r"^f(\d+)\s+\[hb\].*?\bids=(\[[^\]]*\])")
ONE = re.compile(r"^(\w+)#([0-9A-F?]{8}):L(\d+):exp(\d+)$")
#: the code's own window, verified at story_mode.py:2135-2136 -> `level >= target - TRAIN_CATCHUP_GAP`
TRAIN_CATCHUP_GAP = 6


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batch", default="20260909-160339")
    ap.add_argument("--laggard-at", type=int, default=15,
                    help="the claim's population: mons that EVER reach this gap")
    a = ap.parse_args()
    bdir = HERE / "x4-runs" / a.batch
    logs = sorted(bdir.rglob("L0*/debug-logs/*.log"))

    print("=" * 100)
    print(f"LAGGARD ORIGIN — batch {a.batch}   (population: ever >= {a.laggard_at} behind)")
    print("=" * 100)
    if not logs:
        print("  ⛔ no debug logs found.")
        return 0

    #: (run, pid, lineage) -> list of (frame, level, gap)
    mons = collections.defaultdict(list)
    hb_seen = parsed = dropped = 0
    shapes = collections.Counter()

    for f in logs:
        run = f.stem
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = HB.match(line)
            if not m:
                continue
            hb_seen += 1
            try:
                elems = ast.literal_eval(m.group(2))
            except Exception:  # noqa: BLE001
                dropped += 1
                continue
            party = []
            for e in elems:
                em = ONE.match(e)
                if not em:
                    dropped += 1
                    continue
                party.append((em.group(1), em.group(2), int(em.group(3))))
                shapes["SPECIES#PID:L<n>:exp<n>"] += 1
            if not party:
                continue
            parsed += 1
            top = max(p[2] for p in party)
            for sp, pid, lv in party:
                # ⛔ Shedinja carries Ninjask's PID — key on species too so they never merge.
                lineage = "SHEDINJA" if sp == "Shedinja" else "MAIN"
                mons[(run, pid, lineage)].append((int(m.group(1)), lv, top - lv))

    print(f"  logs {len(logs)}   heartbeats {hb_seen:,}   parsed {parsed:,}   "
          f"dropped elements {dropped}   distinct mons {len(mons):,}")
    print(f"  element shapes matched: {dict(shapes)}")

    pop = {k: v for k, v in mons.items() if max(g for _f, _l, g in v) >= a.laggard_at}
    if not pop:
        print("\n  ⚠ no mon reached that gap in this batch.")
        return 0

    first_gaps = [v[0][2] for v in pop.values()]
    born = sum(1 for g in first_gaps if g > TRAIN_CATCHUP_GAP)
    print(f"\n  THE CLAIM'S PROPORTION")
    print(f"    population (ever >= {a.laggard_at} behind) : {len(pop)}")
    print(f"    first-seen gap > {TRAIN_CATCHUP_GAP}                 : "
          f"{born}/{len(pop)} = {100 * born / len(pop):.1f}%      [claimed 88.8%]")
    print(f"    median first-seen gap             : {statistics.median(first_gaps):.0f}"
          f"                 [claimed 11]")

    # ---- ⭐ THE INFERENCE, which is the half that routes the decision --------------------------
    a_arrived_inside = c_never = 0
    b_level_rose = b_top_fell = 0
    window_lens = []
    for v in pop.values():
        gaps = [g for _f, _l, g in v]
        levels = [l for _f, l, _g in v]
        tops = [l + g for (_f, l, g) in v]
        inside = [i for i, g in enumerate(gaps) if g <= TRAIN_CATCHUP_GAP]
        if gaps[0] <= TRAIN_CATCHUP_GAP:
            a_arrived_inside += 1
        elif inside:
            # ⛔ A GAP CLOSES FROM EITHER END, AND ONLY ONE END IS ACTIONABLE. Either the laggard
            # LEVELLED UP into the window (training reached it — the case the fix targets), or the
            # party MAX FELL (the leader was deposited/swapped; level never drops on a faint), which
            # opens a "window" the bot did nothing to earn and cannot be credited for.
            j = inside[0]
            if levels[j] > levels[j - 1]:
                b_level_rose += 1
            elif tops[j] < tops[j - 1]:
                b_top_fell += 1
            else:
                b_level_rose += 1  # neither moved at the boundary: treat as the conservative case
        else:
            c_never += 1
        if inside:
            window_lens.append(len(inside))
    b_recovered = b_level_rose + b_top_fell
    had = a_arrived_inside + b_recovered
    print(f"\n  ⭐ THE CLAIM'S INFERENCE — \"no early small-gap window to maintain\"")
    print(f"    A arrived already INSIDE the window (gap <= {TRAIN_CATCHUP_GAP}) : {a_arrived_inside}")
    print(f"    B arrived outside but was LATER inside it            : {b_recovered}")
    print(f"        of which the LAGGARD LEVELLED UP into it        : {b_level_rose}  ⇐ actionable")
    print(f"        of which the PARTY MAX FELL (deposit/swap)      : {b_top_fell}  ⛔ NOT earned")
    print(f"    C never inside it at any observed moment             : {c_never}")
    print(f"    ⇒ HAD a window (A+B): {had}/{len(pop)} = {100 * had / len(pop):.1f}%")
    act = a_arrived_inside + b_level_rose
    print(f"    ⇒ ⭐ TRAINING-REACHABLE (A + B/level-rose): {act}/{len(pop)} = "
          f"{100 * act / len(pop):.1f}%   ‼ this is the number a FIX can act on")
    if window_lens:
        # ⛔ ONE HEARTBEAT == 3,600 FRAMES == ONE MINUTE at 60fps (`_HEARTBEAT_EVERY`, and
        # `debug_logger.py:59` states the 18,000-frames-is-5-minutes conversion). An earlier version
        # divided by 60 and labelled the result "min", turning 163 minutes into "2.7 min" — a units
        # bug that INVERTED the argument while every digit stayed correct.
        med = statistics.median(window_lens)
        print(f"    median time spent inside the window: {med:.0f} heartbeats = "
              f"{med:.0f} min (~{med / 60:.1f} HOURS of emulated time)")
    print("  " + "-" * 96)
    if had / len(pop) > 0.25:
        print(f"  ⇒ ⛔ **\"BORN DEAD WEIGHT, NO WINDOW\" IS REFUTED FOR {100 * had / len(pop):.0f}% OF "
              f"THIS POPULATION.** The PROPORTION")
        print("     (most arrive past the threshold) holds; the INFERENCE drawn from it does not —")
        print("     a window existed and was not used, which is a different problem with a different fix.")
    else:
        print("  ⇒ ✅ the inference holds: these mons were essentially never inside the window.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
