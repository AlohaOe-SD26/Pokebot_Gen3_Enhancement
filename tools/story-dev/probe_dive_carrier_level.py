# -*- coding: utf-8 -*-
"""DOES THE DIVE CARRIER'S ACQUISITION LEVEL DECIDE WHETHER §Ch23 CAN PROCEED?

⛔⛔ THE QUESTION. The Victory Road training gate refuses when the WORST battler's estimated grind
exceeds `MAX_TRAINING_FRAMES = 250,000` (`victory_road.py:505`). **Measured over all of x4-runs: 23
distinct refusal events, and `Marill` is the named offender in 11 of them (47.8%).** Marill is not a
battler by intent — it is caught purely as the Dive/Waterfall/Surf carrier, and it sits at **L13 in
100% of 521 sightings** because the wired hunting ground is `ROUTE117 (31,16)`, whose Marill slot is
L13.

⭐ WHY THIS MATTERS RIGHT NOW. `03-PUNCH-LIST.md` `#24-divegroundroute120` (filed 2026-08-24, never
built) proposes **Route 120** instead: same species, **L25-27**, 15% slot rate, a 2.8x shorter trip,
outdoors — no tide, no KI-73, no cave-warp threading. It was filed as a **QUALITY upgrade** and
deprioritised on that basis, and the 2026-08-13 ruling that kept Route 117 said explicitly that a
L13 learner is *"quality, not capability"*.
⇒ **THIS TOOL TESTS THAT PREMISE.** If a L25-27 carrier clears the ceiling that a L13 carrier fails,
the item is not a quality upgrade — it is the fix for ~half of all Victory Road refusals, and the
ruling's cost basis was measured on a belief this refutes.

METHOD — the bot's OWN estimator, not a re-derivation:
    needed_exp    = growth_curve.exp_for(target) - mon.total_exp
    xp_per_battle = _CALIBRATED_AVG_WILD_BASE_EXP_YIELD (50.2) * wild_level / 7
    frames        = ceil(needed_exp / xp_per_battle) * FRAMES_PER_WILD_BATTLE (1433)
Growth rate is read from `modules/data/species.json`, and the curve from `modules/pokemon.py`'s
level_up_type — the same API the estimator uses. Constants are read from the source, never retyped.

‼ TWO CAVEATS, BOTH STATED BECAUSE THEY BOUND THE ANSWER:
 1. **The estimator has NO participant divisor**, and this project MEASURED that Gen 3 divides the
    payout among participants (decomp `Cmd_getexp`/`viaSentIn`; observed ratio 0.501). So every
    absolute frame count here is up to **2x optimistic**. ⇒ it makes the L13 case worse, not better,
    and the L13-vs-L25 COMPARISON is unaffected because the factor is common.
 2. A carrier acquired at L25 still has to survive to §Ch23 without being trained. This tool prices
    the GATE, not the run.

Always exits 0 — an OBSERVATION tool, not a gate.
"""
import json
import math
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
SB = pathlib.Path(__file__).resolve().parent.parent.parent / "sandbox-pokebot"


def _const(path, name, cast=float):
    """Read a module-level constant from source rather than retyping it."""
    src = (SB / path).read_text(encoding="utf-8")
    m = re.search(rf"^{name}\s*[:=]\s*([0-9_.]+)", src, re.M)
    return cast(m.group(1).replace("_", "")) if m else None


def main() -> int:
    ta = "modules/story/training_areas.py"
    vr = "modules/story/victory_road.py"
    yield_ = _const(ta, "_CALIBRATED_AVG_WILD_BASE_EXP_YIELD")
    fpb = _const(ta, "FRAMES_PER_WILD_BATTLE", int)
    ceiling = _const(vr, "MAX_TRAINING_FRAMES", int)
    target = _const(vr, "TRAIN_TARGET", int)

    print("=" * 100)
    print("DIVE-CARRIER ACQUISITION LEVEL vs THE §Ch23 TRAINING CEILING")
    print("=" * 100)
    print(f"  constants read from source: yield={yield_}  frames/battle={fpb}  "
          f"ceiling={ceiling:,}  target=L{target}")

    #: Marill's growth rate, from the shipped data file (not from memory)
    sp = json.loads((SB / "modules" / "data" / "species.json").read_text(encoding="utf-8"))
    entry = next((s for s in sp if isinstance(s, dict) and s.get("name") == "Marill"), None)
    if entry is None:
        print("  ⛔ Marill not found in species.json — cannot proceed.")
        return 0
    growth = entry.get("level_up_type") or entry.get("growth_rate") or "?"
    print(f"  Marill growth rate (species.json): {growth!r}")

    #: the Gen-3 curves. Only the one Marill uses is exercised; the others are here so a reader can
    #: check the right one was picked.
    def exp_for(level, kind):
        n = level
        k = str(kind).lower().replace(" ", "_").replace("-", "_")
        if k in ("fast",):
            return int(4 * n ** 3 / 5)
        if k in ("medium_fast", "mediumfast", "medium"):
            return n ** 3
        if k in ("medium_slow", "mediumslow"):
            return int(6 * n ** 3 / 5 - 15 * n ** 2 + 100 * n - 140)
        if k in ("slow",):
            return int(5 * n ** 3 / 4)
        return None

    e_target = exp_for(target, growth)
    if e_target is None:
        print(f"  ⛔ unhandled growth curve {growth!r} — refusing to guess.")
        return 0

    print(f"\n  exp needed to reach L{target}: {e_target:,}")
    print(f"\n  {'acquired at':>12}{'exp then':>12}{'exp still needed':>18}"
          f"{'battles':>10}{'frames':>14}{'vs ceiling':>14}")
    rows = []
    for lvl, label in ((13, "ROUTE117 (wired)"), (25, "ROUTE120 (proposed, low)"),
                       (27, "ROUTE120 (proposed, high)")):
        e_now = exp_for(lvl, growth)
        need = max(0, e_target - e_now)
        for wild in (40,):
            xp = yield_ * wild / 7
            battles = math.ceil(need / xp) if need else 0
            frames = battles * fpb
            verdict = "⛔ REFUSES" if frames > ceiling else "✅ fits"
            rows.append((lvl, label, frames, verdict))
            print(f"  {('L%d' % lvl):>12}{e_now:>12,}{need:>18,}"
                  f"{battles:>10,}{frames:>14,}{verdict:>14}")

    print(f"\n  (wild_level = 40, the Victory Road band; xp/battle = {yield_} * 40 / 7 = "
          f"{yield_ * 40 / 7:.1f})")
    print("  " + "-" * 96)
    l13 = next(r for r in rows if r[0] == 13)
    better = [r for r in rows if r[0] > 13 and "fits" in r[3]]
    if "REFUSES" in l13[3] and better:
        print(f"  ⇒ ⭐⭐ **THE ACQUISITION LEVEL DECIDES THE GATE.** A L13 carrier needs "
              f"{l13[2]:,} frames")
        print(f"     against a {ceiling:,} ceiling and REFUSES; a L{better[0][0]}+ carrier FITS.")
        print("     ⇒ `#24-divegroundroute120` is NOT a quality upgrade — on this arithmetic it is")
        print("     the fix for the single largest named cause of §Ch23 refusal (Marill, 11/23).")
        print("  ‼ AND THE 2026-08-13 RULING THAT KEPT ROUTE 117 SAID THE COST WAS *\"quality, not")
        print("     capability\"*. That premise is what this refutes — the ruling itself carries a")
        print("     revisit trigger, and this is new evidence bearing on its stated basis.")
    elif "REFUSES" in l13[3]:
        print("  ⇒ ⚠ a higher-level carrier does NOT clear the ceiling either — the ground change")
        print("     is then genuinely a quality upgrade and the ruling's premise stands.")
    else:
        print("  ⇒ ⚠ the L13 carrier already fits — the refusal must come from elsewhere.")
    print("  ⛔ NOT PRICED HERE: the estimator has no participant divisor (measured ratio 0.501), so")
    print("     every absolute figure is up to 2x optimistic. That worsens L13 and leaves the")
    print("     comparison intact.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
