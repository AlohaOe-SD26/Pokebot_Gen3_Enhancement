"""A training ground you can REACH but cannot get BACK from must never be proposed.

‼ THIS TEST EXISTS BECAUSE THE KNOWLEDGE WAS ALREADY WRITTEN DOWN AND STILL LOST
(user directive 2026-07-26). Recorded 2026-07-23 in 03-PUNCH-LIST and 04-HANDOFF:

    "LAVARIDGE HAS NO REACHABLE TRAINING GRASS (two-way sweep 2026-07-23,
     jaggedgrass_probe.py): Jagged Pass cannot be re-entered from the town (one-way
     ledges) and Route 112's lower grass has no return path."

On 2026-07-26 that was re-derived from scratch by a full two-way probe cycle — by a
session that had ALREADY QUOTED the Jagged Pass half in its own punch-list edit and then
asserted Fiery Path was "traversable both ways" anyway. Prose in a document nobody reads
while picking a tile does not prevent anything; a table the PICKER consults does, and a
test keeps the table honest.

THE DISTINCTION THAT MATTERS: these grounds are REACHABLE. `allow=` / `region_reach`
answer "can I get there", and for all of them the answer is YES — which is exactly what
makes them dangerous. The failure is the RETURN leg, and a training loop must return to a
Poké Center to heal. A ground whose heal trip cannot complete strands the run: the class
that dropped two real-HW runs to Manual (2026-07-22).

  1. every NO_RETURN_GROUNDS entry carries measured EVIDENCE, not a bare flag
  2. no such ground is ever returned by `best_training_grass` (any level)
  3. nor by `best_training_area` — even with a permissive `allow` that says "reachable"
  4. ordinary grounds are unaffected (the guard is not a blanket refusal)
  5. ROUTE112 / JAGGED_PASS / FIERY_PATH specifically are listed, so the 2026-07-23
     finding can never be silently dropped again

Run: py -3.12 tools/story-dev/repro_no_return_grounds.py
"""

import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot"))

from modules.map_data import MapRSE
from modules.story.training_areas import (
    NO_RETURN_GROUNDS,
    TRAINING_GRASS,
    _return_blocked,
    best_training_area,
    best_training_grass,
)

failures = []


def check(label, cond):
    print(f"    {'PASS' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


print("=" * 78)
print("1) every entry carries measured evidence, not a bare flag")
print("=" * 78)
for map_enum, reason in NO_RETURN_GROUNDS.items():
    print(f"    {map_enum.name}: {reason[:88]}")
    check(f"{map_enum.name} states a reason", isinstance(reason, str) and len(reason) > 30)
    check(f"{map_enum.name} cites a date", any(y in reason for y in ("2026-", "20260")))

print()
print("=" * 78)
print("2) best_training_grass never proposes one, at ANY level")
print("=" * 78)
bad = []
for lvl in range(2, 60):
    got = best_training_grass(lvl)
    if got is not None and _return_blocked(got[0]) is not None:
        bad.append((lvl, got[0].name))
print(f"    levels 2..59 scanned; offending picks: {bad if bad else 'none'}")
check("no no-return ground is ever the best grass", not bad)

print()
print("=" * 78)
print("3) best_training_area refuses them even when `allow` says REACHABLE")
print("=" * 78)
# ‼ The whole point: a permissive predicate models the real situation — these maps ARE
# reachable, and region_reach happily says so. The guard must not depend on `allow`.
bad2 = []
for lvl in range(2, 60):
    got = best_training_area(lvl, allow=lambda m, t, p: True)
    if got is not None and _return_blocked(got[0]) is not None:
        bad2.append((lvl, got[0].name))
print(f"    levels 2..59 with allow=ALWAYS-TRUE; offending picks: {bad2 if bad2 else 'none'}")
check("reachability saying YES does not let a no-return ground through", not bad2)

print()
print("=" * 78)
print("4) ordinary grounds still work (this is not a blanket refusal)")
print("=" * 78)
picked = {
    best_training_area(lvl, allow=lambda m, t, p: True)[0].name
    for lvl in range(2, 60)
    if best_training_area(lvl, allow=lambda m, t, p: True) is not None
}
print(f"    grounds still proposed across L2-59: {sorted(picked)}")
check("the picker still returns real grounds", len(picked) >= 3)
check("ROUTE117 (a known-good ground) is unaffected", _return_blocked(MapRSE.ROUTE117) is None)

print()
print("=" * 78)
print("5) the 2026-07-23 Lavaridge finding is pinned and cannot be dropped")
print("=" * 78)
for m in (MapRSE.JAGGED_PASS, MapRSE.ROUTE112, MapRSE.FIERY_PATH):
    check(f"{m.name} is listed as no-return", _return_blocked(m) is not None)

# Anything in TRAINING_GRASS that is ALSO flagged would be dead weight — flag it so the
# table stays truthful rather than accumulating entries the picker silently skips.
dead = [m.name for m, _t, _b in TRAINING_GRASS if _return_blocked(m) is not None]
print(f"    TRAINING_GRASS entries that are also no-return (skipped by the picker): {dead or 'none'}")

print()
print("-" * 78)
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS: reach-but-cannot-return grounds are refused by BOTH pickers, before any")
print("reachability check — because being reachable is what made them dangerous.")
