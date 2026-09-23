# -*- coding: utf-8 -*-
"""⭐ DOES THE FLY DISJUNCT ACTUALLY CHANGE AN ANSWER? (`#24-flyladder` Piece 2b/2c)

⛔⛔ THIS PROBE EXISTS TO FAIL IF THE FEATURE IS A NO-OP. `_training_area_allowed` gained a second
way to say yes:

    is_map_reachable(area, max_hops=4)   OR   can_fly_to_anchor(heal_centre_of(area))

If `is_map_reachable` were already True for every ladder rung, the disjunct would be decoration and
every caller would behave identically — a change that "works" while doing nothing. ⇒ the acceptance
condition here is **not** "the predicate says yes". It is **"the predicate says yes where the WALKING
half says NO"**, which is the only shape that proves the new clause is load-bearing.

‼ THE OTHER HALF OF THE ANTI-VACUITY TEST, and it is the one that bites: a fixture where Fly is
UNAVAILABLE must still say NO. `post_grind_L60.ss1` has no Fly knower (measured,
`probe_fly_unlocked.py`), so it is the natural negative control — a disjunct that admits areas there
too would be admitting them for some other reason, and the reading would be worthless.

⇒ TWO ARMS, AND BOTH MUST BEHAVE FOR THE RESULT TO COUNT:
    A. a flyable fixture  -> at least one rung must flip NO -> YES
    B. post_grind_L60     -> every rung the walking half refuses must STAY refused

⚠ WHAT THIS DOES NOT CLAIM. That the bot then successfully travels there. This measures the
PREDICATE and its oracle, which is a flag/graph question. The traversal is a drive question, and
the last-mile geometry it depends on is measured separately by `probe_lastmile_paths.py`.

READ-ONLY: loads save states, reads flags/party, runs a graph search. Nothing is walked or written.
"""
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(_ROOT / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_p = load_profile_by_name("repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False
# Registered gates must not run at 1x real time -- the suite's throttle check enforces this.
context.emulation_speed = 0

from modules.map_data import MapRSE, PokemonCenter
from modules.story import region_reach
from modules.story.training_areas import can_fly_to_anchor, fly_landing_tile

# FAULT ARM: `POKEBOT_FLYDISJUNCT_FAULT=1` stubs the Fly oracle to always say NO, which is exactly
# what a refactor that breaks `can_fly_to_anchor` would do. The gate MUST then go red.
# WHY THIS ARM IS THE WHOLE POINT OF THE GATE: the failure it guards is SILENT. If the Fly clause
# stops working, `_training_area_allowed` quietly falls back to walking-only, the per-trainee ladder
# loses five of its six rungs, and nothing raises -- the bot simply trains in the one place it can
# still walk to. A gate whose red state has never been observed is a gate nobody has tested.
import os as _os

if _os.environ.get("POKEBOT_FLYDISJUNCT_FAULT", "").strip() in ("1", "true", "yes"):
    print("  FAULT ARM ACTIVE: can_fly_to_anchor stubbed to always return False")

    def can_fly_to_anchor(_center):  # noqa: F811 - deliberate shadow, fault arm only
        return False

SAVES = _ROOT / "tools" / "story-dev" / "saves"
MAX_HOPS = 4  # `_MAX_TRAINING_TRAVEL_LEGS` — the WALKING budget, deliberately unchanged by Piece 2b

LADDER = [
    ("L15-20", MapRSE.ROUTE117, PokemonCenter.VerdanturfTown),
    ("L21-24", MapRSE.ROUTE111, PokemonCenter.FallarborTown),
    ("L25-26", MapRSE.ROUTE115, PokemonCenter.RustboroCity),
    ("L27", MapRSE.ROUTE118, PokemonCenter.MauvilleCity),
    ("L28-38", MapRSE.ROUTE121, PokemonCenter.LilycoveCity),
    ("L39-75", MapRSE.VICTORY_ROAD_1F, PokemonCenter.EvergrandeCity),
]

ARMS = [
    ("A  flyable fixture", "post_ch24_atdoor_L75.ss1", True),
    ("B  NEGATIVE CONTROL", "post_grind_L60.ss1", False),
]

print("=" * 104)
print("DOES THE FLY DISJUNCT CHANGE AN ANSWER?   walking-only  vs  walking OR fly")
print("=" * 104)

results = {}
for arm_name, fixture, expect_fly in ARMS:
    path = SAVES / fixture
    print()
    print(f"─── {arm_name}: {fixture}")
    if not path.exists():
        print("  ⚠ SKIPPED — no such fixture")
        continue
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(40):
        context.emulator.run_single_frame()

    print(f"  {'rung':<9} {'ground':<18} {'walk<=4hops':<13} {'can fly':<9} combined   effect")
    print("  " + "-" * 92)
    flips, rows = 0, []
    for rung, ground, center in LADDER:
        try:
            walk = bool(region_reach.is_map_reachable(ground, max_hops=MAX_HOPS))
        except Exception as error:  # noqa: BLE001 - a failed oracle IS the reading
            print(f"  {rung:<9} {ground.name:<18} ⛔ oracle failed: {type(error).__name__}")
            continue
        fly = can_fly_to_anchor(center)
        combined = walk or fly
        effect = ""
        if combined and not walk:
            effect = "⭐ FLIPPED NO→YES — the disjunct is load-bearing here"
            flips += 1
        elif walk:
            effect = "(walking already said yes — disjunct irrelevant)"
        else:
            effect = "still NO"
        print(f"  {rung:<9} {ground.name:<18} {str(walk):<13} {str(fly):<9} "
              f"{str(combined):<10} {effect}")
        rows.append((rung, walk, fly, combined))
    results[arm_name] = (flips, rows)
    print()
    print(f"  → {flips} rung(s) admitted ONLY because of Fly")

print()
print("=" * 104)
print("  LANDING TILES the traversal will use (door + (0,+1)):")
for _rung, ground, center in LADDER:
    landing = fly_landing_tile(center)
    door = tuple(center.value[1])
    print(f"     {ground.name:<18} {center.name:<18} door {str(door):<10} → landing "
          f"{str(landing[1]) if landing else '⛔ None'}")

print()
a = results.get("A  flyable fixture")
b = results.get("B  NEGATIVE CONTROL")
ok = True
if a is None or b is None:
    print("  ⛔ A FIXTURE WAS MISSING — this run cannot grade itself.")
    ok = False
else:
    if a[0] == 0:
        print("  ⛔⛔ VACUOUS: on the flyable fixture NOT ONE rung was admitted by Fly alone.")
        print("     Either every rung was already walkable (so Piece 2b changes nothing and must")
        print("     not be described as enabling the ladder), or the guards are failing silently.")
        ok = False
    else:
        print(f"  ✅ ARM A: {a[0]} rung(s) flipped NO→YES on Fly alone — the clause does real work.")
    leaked = [r for r in b[1] if r[3] and not r[1]]
    if leaked:
        print(f"  ⛔⛔ ARM B LEAKED: {len(leaked)} rung(s) admitted on a fixture with NO Fly knower:")
        for rung, walk, fly, _c in leaked:
            print(f"       {rung}  walk={walk} fly={fly}")
        print("     ⇒ the disjunct is saying yes for a reason that is not Fly. Do not ship.")
        ok = False
    else:
        print("  ✅ ARM B: nothing extra admitted where Fly is unavailable — the control holds.")

print()
print("  VERDICT: " + ("✅ THE FLY DISJUNCT IS LOAD-BEARING AND CORRECTLY GATED"
                       if ok else "⛔ FAIL — see above"))
print("=" * 104)
raise SystemExit(0 if ok else 1)
