"""Regression test for `#24-smashroute` / KI-41 obstacle clearing. NO EMULATOR.

WHAT THIS IS ABOUT. A Rock Smash rock at ROUTE111 **(18,101)** seals the Mauville ->
Route 112 corridor. Measured 2026-07-31: ROUTE112 scores **0 of 76** sampled tiles
reachable from Mauville, and FIERY_PATH's only two doors are on Route 112 — so Machop, the
counter the `#24-counters` ladder names for Norman, was unreachable. `#24-journey` did not
fix it and never could: after that fix a warp route to Fiery Path IS found and neither of
its first legs is walkable.

Live end-to-end proof (`story_harness.py --driver smashroute`, `rocksmash_taught.ss1`):
    NEW arm -> arrived=True map=FIERY_PATH, 45,305 frames (walks, smashes (18,101), arrives)

‼ THE MOST IMPORTANT TEST IN THIS FILE IS THE RE-ENTRANCY ONE (section 4). The hook lives
in `early_game._navigate_riding_out`, and `clear_obstacle` -> `_smash_rock` ->
`_navigate_riding_out` walks to the approach tile — so a clearance runs THROUGH the very
function that starts clearances. Without the guard, any failure of that short walk finds
the same rock again and recurses, each level with a fresh `cleared_obstacles` set. That is
the project's oldest bug shape: *a bounded loop re-entered by its dispatcher is still
infinite* (KI-34, 23.9M frames). It shipped once and was caught only because
`repro_smashrock_battle_wedge.py` went from sub-90s to >500s.
"""

from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.story import obstacle_clearing as oc  # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


R111 = (0, 15)
ROCK = (18, 101)


class _Stub:
    """Stands in for the live world: the ROUTE111 rocks, a party that can smash, and a
    reachable frontier that stops just south of the choke (exactly what was measured)."""

    def __init__(self, reachable: set, capability: bool = True):
        self.reachable = reachable
        self.capability = capability
        self.smashed: list = []

    def install(self):
        self._saved = (oc.obstacles_on_map, oc._have_capability, oc._reachable)
        oc.obstacles_on_map = lambda m: (
            [((18, 101), "EventScript_RockSmash"), ((19, 100), "EventScript_RockSmash")]
            if tuple(m) == R111 else []
        )
        oc._have_capability = lambda move, badge: self.capability
        oc._reachable = lambda m, tile: tuple(tile) in self.reachable
        return self

    def restore(self):
        oc.obstacles_on_map, oc._have_capability, oc._reachable = self._saved


# Measured frontier: (18,102) is reachable, (18,101) is the rock, nothing north of it is.
FRONTIER = {(18, 102), (19, 101), (17, 102), (20, 102), (18, 103)}

print("1. the script table is honest")
check("Rock Smash is actionable", "EventScript_RockSmash" in oc.CLEARABLE_SCRIPTS)
# ‼ A boulder is PUSHED, not removed, so `clear_obstacle`'s "the object is gone" success
# test can never fire — it would burn its whole attempt budget and report failure on a
# push that worked. Pinned so nobody adds it as an easy win.
check("Strength is NOT actionable (a boulder is pushed, not removed)",
      "EventScript_StrengthBoulder" not in oc.CLEARABLE_SCRIPTS)
check("...and the reason is recorded rather than lost",
      "EventScript_StrengthBoulder" in oc.KNOWN_BUT_UNSUPPORTED)
check("Cut is documented as known-but-unvalidated, not silently enabled",
      "EventScript_CutTree" in oc.KNOWN_BUT_UNSUPPORTED
      and "EventScript_CutTree" not in oc.CLEARABLE_SCRIPTS)
check("no symbol appears in both tables",
      not (set(oc.CLEARABLE_SCRIPTS) & set(oc.KNOWN_BUT_UNSUPPORTED)))

print("\n2. planning picks a reachable approach and the right facing")
stub = _Stub(FRONTIER).install()
try:
    plan = oc.find_clearable_obstacle(R111, prefer_toward=(18, 60))
    check("a plan is produced", plan is not None)
    check("it targets the (18,101) rock nearest the goal", plan and plan.tile == ROCK, str(plan and plan.tile))
    # Travel is NORTHBOUND (decreasing y), so the approach is from the SOUTH: stand at
    # y+1 and face Up. `early_game` hard-codes the mirror image — (18,100) facing Down —
    # because its travel leg walks the corridor southbound. Both are correct; the finder
    # must derive the one that matches where the bot can actually stand.
    check("the stand tile is SOUTH of the rock", plan and plan.stand_tile == (18, 102), str(plan and plan.stand_tile))
    check("...and it faces Up", plan and plan.face == "Up", str(plan and plan.face))
    check("stand_tile is orthogonally adjacent to the rock",
          plan and abs(plan.stand_tile[0] - plan.tile[0]) + abs(plan.stand_tile[1] - plan.tile[1]) == 1)
    check("describe() names the move, the tile and the facing",
          plan and all(s in plan.describe() for s in ("Rock Smash", "(18, 101)", "(18, 102)", "Up")),
          plan and plan.describe())

    print("\n3. the wrong-YES arms — both must refuse")
    stub.capability = False
    check("no plan without the move AND badge", oc.find_clearable_obstacle(R111) is None)
    stub.capability = True
    stub.reachable = set()
    check("no plan when nothing beside the rock can be reached",
          oc.find_clearable_obstacle(R111) is None)
    stub.reachable = FRONTIER
    check("...and it comes back when the world allows it again",
          oc.find_clearable_obstacle(R111) is not None)
    check("a map with no obstacles yields no plan", oc.find_clearable_obstacle((0, 12)) is None)
finally:
    stub.restore()

print("\n4. ‼ RE-ENTRANCY — the guard that stops clear -> navigate -> clear -> ... forever")
stub = _Stub(FRONTIER).install()
saved_route = oc.get_warp_graph if hasattr(oc, "get_warp_graph") else None
try:
    # `find_obstacle_on_route` walks the map graph, which needs a ROM. Drive
    # `find_clearable_obstacle` for the positive case and the ROUTE variant only for the
    # guard, which returns before touching the graph.
    check("clearing is not in progress initially", not oc.is_clearing_in_progress())
    oc._clearing_in_progress = True
    check("while clearing, find_obstacle_on_route refuses to start another",
          oc.find_obstacle_on_route(R111, (0, 20), prefer_toward=(18, 60)) is None)
    oc._clearing_in_progress = False
    check("the flag is settable back off", not oc.is_clearing_in_progress())

    # The flag must be released even when the clearance BLOWS UP. A guard stuck ON would
    # silently disable obstacle clearing for the rest of the run — as bad as one stuck off.
    plan = oc.find_clearable_obstacle(R111, prefer_toward=(18, 60))

    def _boom(*_a, **_k):
        raise RuntimeError("smash exploded")
        yield  # pragma: no cover - makes this a generator

    import modules.story.early_game as eg

    saved_smash = eg._smash_rock
    eg._smash_rock = _boom
    try:
        gen = oc.clear_obstacle(plan)
        try:
            next(gen)
        except RuntimeError:
            pass
    finally:
        eg._smash_rock = saved_smash
    check("the flag is released after the clearance raises", not oc.is_clearing_in_progress())
finally:
    oc._clearing_in_progress = False
    stub.restore()

print("\n5. failure modes never raise into a caller")
check("a bogus map is handled", oc.obstacles_on_map((99, 99)) == [])
check("find_clearable_obstacle on a bogus map returns None",
      oc.find_clearable_obstacle((99, 99)) is None)

print()
if FAILURES:
    print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
    sys.exit(1)
print("ALL PASS")
