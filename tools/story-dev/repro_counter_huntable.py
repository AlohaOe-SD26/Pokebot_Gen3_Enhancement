"""Proof for the #24-counters phase-2 HUNTING-GROUND GATE (`training_areas.
hunt_ground_tile`, `counter_plan.huntable` / `best_huntable`).

WHY THIS EXISTS
`find_counter_candidates` ranks catch targets over the WHOLE-GAME encounter index and
prices each by "frames to find + frames to train it up to the team's level". That cost
model has a sting in the tail: a wild that is ALREADY ABOVE the team costs ~0 to train,
so **deep-endgame encounters rank as the CHEAPEST answers**. Measured 2026-07-30 against
the real ROM tables (this script's own output), the top-ranked Fighting answer for
Norman is a **Victory Road Hariyama L38-42**, and Wattson's Ground answers include the
Magma Hideout and Mirage Tower. Phase 1 only ever PRINTED that list, so it was harmless;
phase 2 travels to it, so ranking-as-a-gate would walk a mid-game team into Victory Road.

03-PUNCH-LIST names this as #24-counters blockers (3) "Victory Road / E4 gate" and (4)
"exclude story interiors". The fix is a WHITELIST, not a blacklist of endgame maps: a
blacklist would be an ever-growing list of game facts written from memory (forbidden by
the standing rule), while a whitelist needs no claim about Mirage Tower at all — it is
simply not a ground anyone has swept, so it is refused. It also fails CLOSED, which is
the correct direction for a predicate that decides where the bot physically walks.

WHAT THIS PROVES (all offline — `set_rom()` only, no emulator, no save state)
  1. The real ROM tables really do rank an unswept endgame map #1 for Norman —
     i.e. the hazard is measured here, not assumed.
  2. Every such map is `huntable=False`, and `best_huntable()` never returns one.
  3. FIERY_PATH — the ONLY proven home of Norman's Machop answer — IS huntable, at the
     tile `story_harness --driver fierycave` actually walked, (18,19).
  4. JAGGED_PASS is refused even though it ranks ABOVE Fiery Path on cost: it is in
     NO_RETURN_GROUNDS in the strong sense (it cannot path within itself). This is the
     entry that proves the gate consults the no-return table, not just the whitelist.
  5. `best_huntable([])`, garbage input, and a candidate list with nothing huntable all
     return None and never raise — a planner that throws turns a diagnosed stop into a
     crash (the same fail-safe contract as the rest of this module).

‼ WHAT THIS DOES NOT PROVE: reachability. `region_reach` builds its graph by reading
`gMapGroups` out of EMULATOR memory, so it cannot run on this dev box at all (verified
2026-07-30: it raises `AttributeError: 'NoneType' object has no attribute 'read_bytes'`
and its own fail-safe then reports every map unreachable). So this script forces
`reachable=True` for every candidate and tests the HUNT gate in isolation. Whether the
bot can walk to Fiery Path from Petalburg must be confirmed on a machine with mgba.

Run: py -3.12 tools/story-dev/repro_counter_huntable.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-fresh")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

import modules.story.counter_plan as counter_plan
from modules.map_data import MapRSE
from modules.story.training_areas import (
    HUNTING_GROUNDS,
    NO_RETURN_GROUNDS,
    TRAINING_GRASS,
    hunt_ground_tile,
)

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        failures.append(label)


# `reachable` is orthogonal to this gate and cannot be evaluated without an emulator
# (see the docstring); force it TRUE so nothing is filtered for the wrong reason and the
# hunt gate is the only thing under test.
ALLOW_ALL = lambda _map, _tile, _prereq: True  # noqa: E731


def candidates_for(needed, team_level):
    counter_plan._team_reference_level = lambda: team_level
    return counter_plan.find_counter_candidates(needed, allow=ALLOW_ALL, max_results=40)


print("=" * 78)
print("CASE 1 — the hazard is REAL: cost ranking puts an unswept map first for Norman")
print("=" * 78)
norman = candidates_for(["Fighting"], 30)
print(f"  {len(norman)} Fighting candidates for a L30 team, ranked:")
for c in norman[:9]:
    print(
        f"    {c['species_name']:<10} {c['map_enum'].name:<26} L{c['level_band']} "
        f"est={'?' if c['est_frames'] is None else int(c['est_frames'])!s:<8} "
        f"huntable={c['huntable']!s:<5} hunt_tile={c['hunt_tile']}"
    )
# ‼ UPDATED 2026-08-07 (`#24-movepoolcounters`). This used to assert the OPPOSITE — "rank-1 is
# NOT huntable" — as a measurement of the hazard that motivates the whitelist gate. That hazard
# has now been fixed IN THE RANKING: `tier` gained a huntability term above type coverage, so an
# unhuntable candidate can no longer outrank a huntable one.
#
# ‼ Asserting the old inequality would pin the LIMITATION rather than the property, and the
# suite would then actively defend the bug — the exact failure mode recorded for
# `repro_x4_headless.py` ("a wrapped line IS unparseable"). What must be TRUE is: *if any
# candidate is huntable, the top-ranked one is huntable too*.
#
# ‼ THE GATE IS STILL LOAD-BEARING AND IS STILL TESTED (cases 2/4/5). When NOTHING is huntable,
# `cands[0]` is still an unswept endgame map, so the executor must keep calling
# `best_huntable()` and must never trust rank alone.
_huntable = [c for c in norman if c["huntable"]]
check(
    "if ANY candidate is huntable, rank 1 is huntable (ranking now agrees with the gate)",
    (not _huntable) or norman[0]["huntable"],
    f"rank 1 = {norman[0]['species_name']} @ {norman[0]['map_enum'].name} "
    f"(huntable={norman[0]['huntable']}), {len(_huntable)} huntable of {len(norman)}"
    if norman else "no candidates",
)
check(
    "the planner STILL offers unswept endgame maps (the hazard is in the DATA, not the sort)",
    any(not c["huntable"] for c in norman),
    "so the whitelist gate remains necessary — it is what makes them unusable",
)

print()
print("=" * 78)
print("CASE 2 — best_huntable() picks FIERY_PATH, the proven Machop ground")
print("=" * 78)
best = counter_plan.best_huntable(norman)
check("best_huntable returned a candidate", best is not None)
if best is not None:
    print(f"    -> {best['species_name']} @ {best['map_enum'].name} tile {best['hunt_tile']} L{best['level_band']}")
    check("it is FIERY_PATH", best["map_enum"] is MapRSE.FIERY_PATH, best["map_enum"].name)
    check("at the harness-walked tile (18,19)", best["hunt_tile"] == (18, 19), str(best["hunt_tile"]))
    check("it is a Fighting type", "Fighting" in best["types"], "/".join(best["types"]))

print()
print("=" * 78)
print("CASE 3 — JAGGED_PASS is refused although it RANKS ABOVE Fiery Path")
print("=" * 78)
jagged = [c for c in norman if c["map_enum"] is MapRSE.JAGGED_PASS]
fiery = [c for c in norman if c["map_enum"] is MapRSE.FIERY_PATH]
check("Jagged Pass IS offered as a candidate (the planner still names it)", bool(jagged))
check("Fiery Path is offered too", bool(fiery))
if jagged and fiery:
    j_rank, f_rank = norman.index(jagged[0]), norman.index(fiery[0])
    # ‼ UPDATED 2026-08-07, same reason as CASE 1: this asserted `j_rank < f_rank` to MEASURE
    # that cost-ranking alone would have picked the no-return ground. With huntability now a
    # tier term, Jagged Pass (refused by NO_RETURN_GROUNDS ⇒ no hunt tile) can no longer outrank
    # Fiery Path. Keeping the old inequality would require the ranking to stay wrong.
    # The property that matters is unchanged and is asserted immediately below: Jagged Pass is
    # still OFFERED by the planner and still REFUSED by the gate.
    check(
        "Jagged Pass no longer outranks Fiery Path (huntability is now a tier term)",
        f_rank < j_rank,
        f"fiery rank {f_rank} (est {int(fiery[0]['est_frames'])}) vs "
        f"jagged rank {j_rank} (est {int(jagged[0]['est_frames'])}) "
        f"— cost still favours Jagged Pass, which is why the gate stays",
    )
    check("...yet Jagged Pass is NOT huntable", not jagged[0]["huntable"])
    check("...and Fiery Path IS", fiery[0]["huntable"])
check(
    "the refusal comes from NO_RETURN_GROUNDS, which lists Jagged Pass",
    MapRSE.JAGGED_PASS in NO_RETURN_GROUNDS and hunt_ground_tile(MapRSE.JAGGED_PASS) is None,
)
check(
    "ROUTE112 (also no-return, not cleared for hunting) is refused too",
    hunt_ground_tile(MapRSE.ROUTE112) is None,
)
check(
    "FIERY_PATH is no-return for TRAINING yet cleared for HUNTING — the whole point",
    MapRSE.FIERY_PATH in NO_RETURN_GROUNDS
    and MapRSE.FIERY_PATH in HUNTING_GROUNDS
    and hunt_ground_tile(MapRSE.FIERY_PATH) == (18, 19),
)

print()
print("=" * 78)
print("CASE 4 — unswept maps across ALL three measured derail classes are refused")
print("=" * 78)
wattson = candidates_for(["Ground"], 20)
winona = candidates_for(["Rock", "Electric", "Ice"], 33)
swept = {m for m, t, _b in TRAINING_GRASS if t is not None} | set(HUNTING_GROUNDS)
for label, cands in (("Wattson/Ground", wattson), ("Winona/Rock+Elec+Ice", winona), ("Norman/Fighting", norman)):
    leaked = [c for c in cands if c["huntable"] and c["map_enum"] not in swept]
    check(
        f"{label}: no huntable candidate on an unswept map",
        not leaked,
        f"{len(cands)} candidates, "
        f"{sum(1 for c in cands if c['huntable'])} huntable"
        + (f", LEAKED {[c['map_enum'].name for c in leaked]}" if leaked else ""),
    )
    hunt = counter_plan.best_huntable(cands)
    print(
        f"      best_huntable -> "
        + (f"{hunt['species_name']} @ {hunt['map_enum'].name} {hunt['hunt_tile']}" if hunt else "None (diagnosis only)")
    )

print()
print("=" * 78)
print("CASE 5 — fail-safe: nothing here may raise")
print("=" * 78)
try:
    check("best_huntable([]) is None", counter_plan.best_huntable([]) is None)
    check("best_huntable(None) is None", counter_plan.best_huntable(None) is None)
    check("best_huntable(garbage) is None", counter_plan.best_huntable([{"nope": 1}, 7]) is None)
    check("hunt_ground_tile(None) is None", hunt_ground_tile(None) is None)
    check("hunt_ground_tile(garbage) is None", hunt_ground_tile("not a map") is None)
    unhuntable = [dict(c, huntable=False) for c in norman]
    check("a list with nothing huntable -> None", counter_plan.best_huntable(unhuntable) is None)
except Exception as error:  # noqa: BLE001
    check(f"no exception escaped (raised {error!r})", False)

print()
print("=" * 78)
print(f"RESULT: {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'}")
for f in failures:
    print(f"  FAILED: {f}")
print("=" * 78)
sys.exit(1 if failures else 0)
