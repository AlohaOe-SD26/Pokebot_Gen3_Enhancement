"""The training-relocation floor is keyed on the WRONG MON. NO EMULATOR.

WHAT IS WRONG. `_prepare_for_fight` decides where to grind like this:

    floor = max(local_max, team_max_now - self.FODDER_LEVEL_GAP)
    better = best_training_area(team_max_now, min_wild_max=floor, allow=_allow)

`team_max_now` is the STRONGEST mon in the party. But the mons that actually need training
are the stragglers — measured in batch4 (`x4-runs/20260731-201554`), a typical Norman party
is `Marshtomp L35 / Ninjask L30 / Swellow L32 / Poochyena L12 / Shedinja L20`, and `need` is
the L12 and L20. Keying the floor to L35 demands wilds above L23, which rejects
**ROUTE111 (L19-22)** — the one area actually reachable in that part of Hoenn — even though
L19-22 is close to ideal for a L20 trainee.

MEASURED CONSEQUENCE. In batch4 the bot printed
`local grass (max L4) is fodder for a L<N> team and no better area is available`
**167 times**, every single one of them `local grass (max L4)` (= ROUTE102, Norman's patch),
with teams L32-41. Each of those is a prep grind skipped entirely.

‼ WHICH TERM IS AT FAULT — this matters, because the obvious "key it all to the trainee" is
wrong. `train_team` runs with SWAP-TRAIN on: the under-levelled trainee is switched out on
turn 1 and a STRONGER team-mate does the fighting, so the winnability/scoring argument
(`best_training_area`'s first parameter) is correctly `team_max_now`. Only `min_wild_max`
— the "is this somewhere worth going" floor — should be keyed to the mons being trained.

‼ SCOPE, STATED HONESTLY: this fix is NECESSARY BUT PROBABLY NOT SUFFICIENT at Petalburg.
When every richer area is reachable both floors agree, so the fix changes nothing; it only
pays when the far areas are out of reach AND something mid-band is in reach. From Petalburg
even ROUTE111 is often unreachable, which is why some L32-34 runs refused too. Its real
value is unlocking the agreed PRE-EMPTIVE training plan (train near Lavaridge, where
ROUTE111/ROUTE117 demonstrably ARE reachable, before travelling to Petalburg).
"""

from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.story.training_areas import best_training_area  # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


FODDER_GAP = 12
ROUTE102_MAX = 4  # Norman's local patch, probed 2026-08-01

#: Reachability as it actually is around Petalburg: the rich post-Norman routes
#: (115/118/119/121) are not walkable from there, mid-Hoenn is.
NEAR_PETALBURG = {"ROUTE111", "ROUTE117", "ROUTE116", "ROUTE102", "ROUTE101", "ROUTE103"}
ALLOW_NEAR = lambda m, t, p: m.name in NEAR_PETALBURG  # noqa: E731
ALLOW_ALL = lambda m, t, p: True  # noqa: E731

#: (label, team_max, trainee levels) — the party shapes that dominate batch4's refusals.
SHAPES = [
    ("L35 team, stragglers L12/L20", 35, [12, 20]),   # 44 refusals
    ("L36 team, straggler L12", 36, [12]),            # 39 refusals
    ("L33 team, stragglers L20/L27", 33, [20, 27]),   # 15 refusals — already works today
]


def floor_today(local_max: int, team_max: int) -> int:
    return max(local_max, team_max - FODDER_GAP)


print("1. THE DEFECT — the current floor returns 'no better area' where one exists")
regressed = []
for label, team_max, need in SHAPES:
    now = floor_today(ROUTE102_MAX, team_max)
    pick_now = best_training_area(team_max, min_wild_max=now, allow=ALLOW_NEAR)
    trainee = max(ROUTE102_MAX, max(need) - FODDER_GAP)
    pick_new = best_training_area(team_max, min_wild_max=trainee, allow=ALLOW_NEAR)
    print(f"       {label}")
    print(f"         floor now={now:<3} -> {pick_now[0].name if pick_now else 'None'}"
          f"      floor trainee-keyed={trainee:<3} -> {pick_new[0].name if pick_new else 'None'}")
    if pick_now is None and pick_new is not None:
        regressed.append(label)
check(
    "at least one real batch4 party shape is rescued by the trainee-keyed floor",
    len(regressed) >= 2,
    f"rescued: {regressed}",
)

print("2. the fix must not make things WORSE where the current code already works")
worse = []
for label, team_max, need in SHAPES:
    trainee = max(ROUTE102_MAX, max(need) - FODDER_GAP)
    for allow, aname in ((ALLOW_NEAR, "near"), (ALLOW_ALL, "all")):
        a = best_training_area(team_max, min_wild_max=floor_today(ROUTE102_MAX, team_max), allow=allow)
        b = best_training_area(team_max, min_wild_max=trainee, allow=allow)
        if a is not None and b is None:
            worse.append((label, aname))
check("the trainee-keyed floor never turns a working pick into None", not worse, str(worse))

print("3. it must never admit a patch that is fodder FOR THE TRAINEE")
# The floor exists so the bot doesn't walk somewhere to grind equally-worthless xp. Keyed
# to the trainee it must still refuse anything at-or-below that trainee's own fodder line.
bad = []
for label, team_max, need in SHAPES:
    trainee = max(ROUTE102_MAX, max(need) - FODDER_GAP)
    pick = best_training_area(team_max, min_wild_max=trainee, allow=ALLOW_ALL)
    if pick is not None and pick[2][1] <= max(need) - FODDER_GAP:
        bad.append((label, pick[0].name, pick[2]))
check("no pick is fodder for the trainee it is meant to train", not bad, str(bad))

print("4. the rule is available as a PURE function (added by the fix)")
# Kept last on purpose: checks 1-3 demonstrate the defect using only today's public API and
# pass BEFORE the fix, so this file is a running demonstration rather than an assertion that
# a symbol exists. This one goes green when the rule is extracted and wired in.
try:
    from modules.story.training_areas import relocation_floor  # noqa: E402

    got = relocation_floor(ROUTE102_MAX, [12, 20], FODDER_GAP)
    check("relocation_floor(local=4, trainees=[12,20], gap=12) == 8", got == 8, f"got {got}")
    check(
        "it never drops below the local patch (no point relocating to something worse)",
        relocation_floor(30, [12], FODDER_GAP) == 30,
        f"got {relocation_floor(30, [12], FODDER_GAP)}",
    )
    check(
        "an empty trainee list degrades to the local patch rather than raising",
        relocation_floor(ROUTE102_MAX, [], FODDER_GAP) == ROUTE102_MAX,
    )
except ImportError:
    check(
        "training_areas.relocation_floor exists",
        False,
        "NOT YET ADDED — the sandbox edit is deliberately held until batch "
        "20260801-075805 lands, because x4_headless relaunches dead lanes and a "
        "restarted lane would re-import mid-batch",
    )

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
