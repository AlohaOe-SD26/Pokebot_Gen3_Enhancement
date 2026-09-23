# -*- coding: utf-8 -*-
"""⛔ GATE: `_fly_to_training_anchor`'s REFUSAL must escape its own try block. (`#24-flyladder` 2c)

‼‼ THIS GATE EXISTS BECAUSE THE BUG SHIPPED IN THE SANDBOX AND WAS CAUGHT BY A REVIEWER, NOT A GATE.
The traversal ends with a deliberate refusal:

    raise UnreachableDestinationError(...)      # "admitted on the strength of Fly, but cannot fly,
                                                #  and not walkable within the hop budget"

and that `raise` sat INSIDE the `try:` whose own `except Exception as error:` caught it.
`reraise_if_aborting` re-raises ONLY when `_STORY_ABORT` is latched — i.e. after a whiteout — so on
every ordinary run the refusal was swallowed, the generator returned normally, and
`_goto_training_area` fell straight through to the walk.

⇒ **THE BACKSTOP WAS INERT, AND THE THING IT GUARDS IS NOT SMALL.** The Fly disjunct
(`_training_area_allowed`) is what makes 11-to-15-hop training areas selectable at all. Without a
live refusal the bot ADMITS such an area, fails to fly to it, and then WALKS at it under
`train_team`'s 500-round guard with no frame cap — KI-28's 19.9M-frame shape, which the block's own
comments say must never happen.

⛔ WHY NO EXISTING GATE CAUGHT IT. Gate #68 (`probe_fly_disjunct.py`) exercises the PREDICATE — a
flag-and-graph question — and nothing exercised the TRAVERSAL. A guard placed inside the handler
that catches it is a guard that has been WRITTEN but not INSTALLED, and that difference is invisible
to every check this tree had.

WHAT THIS ASSERTS — FOUR arms, and every one is a way a plausible "fix" goes wrong:
  A. REFUSAL PROPAGATES. Cannot fly ∧ target not walkable within the hop budget
     ⇒ `UnreachableDestinationError` reaches the CALLER.
  B. CONTROL — IT STILL DEGRADES QUIETLY. Cannot fly ∧ target IS walkable ⇒ no raise, no steps.
     ‼ Arm B is not decoration: a "fix" that re-raises unconditionally would pass arm A and break
     every ordinary heal-return (a Poké Center is `map_type=Indoor`, so Fly is always illegal there,
     while the grind tile is two hops away). Arm A alone would grade that as success.
  C. THE EVER GRANDE PLATEAU. Standing at `EVER_GRANDE_CITY (18,6)` — where §Ch23's last leg
     (`heal_at_league`) deliberately leaves the bot, `victory_road.py:374` `LEAGUE_DOOR_APRON` —
     the leg MUST still fly. ⛔ That tile is the SAME MAP as the Poké Center landing (27,49) and
     `calculate_path` between them is **NO PATH in both directions**, measured
     (`evidence/2026-09-18-vr-heal-roundtrip.stdout.txt`, control at (18,42) = 23 wp, so the refusal
     is a real reachability answer). ⇒ a guard comparing the MAP says "already in the anchor town"
     and skips the Fly, stranding the leg at the exact position the previous chapter hands over.
     v1 of guard 3 did precisely that.
  C'. AND THE TILE GUARD STILL SHORT-CIRCUITS. Standing ON (27,49) ⇒ no Fly.
     ‼ Without C', "fix C by always flying" passes A, B and C while making guard 3 dead code.

FAULT ARM: `POKEBOT_FLYREFUSAL_FAULT=1` re-creates the original defect by wrapping the generator in
a swallowing handler. The gate must then FAIL arm A — proving it can actually detect the bug it was
written for, rather than merely passing on fixed code.

NO EMULATOR, NO ROM, NO SAVE STATE: the oracles are monkeypatched, so this is pure control flow and
runs in well under a second.
"""
import os
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")

#: ‼ BUILD-AWARE, so a PROMOTION of this guard can be MEASURED and not assumed. `promote.py`'s own
#: docstring records a promotion that shipped with a hole precisely because the gate proving the fix
#: hard-coded `sandbox-pokebot` on its import path.
_BUILD = ("custom" if "--build" in sys.argv
          and sys.argv[sys.argv.index("--build") + 1] == "custom" else "sandbox")
sys.path.insert(0, str(_ROOT / f"{_BUILD}-pokebot"))

from modules.map_data import MapRSE, PokemonCenter
from modules.story import early_game as eg
from modules.story import region_reach as rr
from modules.story import training_areas as ta

BAR = "=" * 100
print(BAR)
print(f"GATE: the Fly-anchor REFUSAL must escape its own try block   [build={_BUILD}]")
print(f"  importing from: {_ROOT / (_BUILD + '-pokebot')}")
print(BAR)

_FAULT = os.environ.get("POKEBOT_FLYREFUSAL_FAULT", "").strip() in ("1", "true", "yes")
if _FAULT:
    print("  ⚠ FAULT ARM ACTIVE — re-creating the original defect (the refusal is swallowed)")

_real = eg._fly_to_training_anchor


def _under_test(grass_map, heal_center):
    """The generator, optionally wrapped in the exact defect this gate exists to catch."""
    if not _FAULT:
        yield from _real(grass_map, heal_center)
        return
    try:
        yield from _real(grass_map, heal_center)
    except Exception:  # noqa: BLE001 - THE INJECTED DEFECT: swallow, exactly as the original did
        return


# ⛔ Force the guards deterministically. The question here is CONTROL FLOW, not game state, so the
# oracles are stubbed rather than staged on a fixture — a fixture would make this gate need a ROM
# and would couple it to a save file's party, neither of which it is asking about.
ta.can_fly_to_anchor = lambda _c: False      # guard 4 fails: we cannot fly from here
eg._map_group_number = lambda: (0, 0)        # not on the target map, not in the anchor town

failures = []

# ---- ARM A: cannot fly AND cannot walk -> the refusal must reach the caller ------------------
rr.is_map_reachable = lambda _m, **_k: False
try:
    list(_under_test(MapRSE.ROUTE117, PokemonCenter.VerdanturfTown))
    failures.append(
        "ARM A: the generator returned NORMALLY. The refusal was swallowed, so the caller would "
        "fall through to an unbounded cross-Hoenn walk (KI-28's shape).")
    print("  ⛔ ARM A  FAIL — refusal swallowed")
except eg.UnreachableDestinationError as error:
    print(f"  ✅ ARM A  PASS — UnreachableDestinationError propagated: {str(error)[:58]}…")
except Exception as error:  # noqa: BLE001 - any OTHER exception is also a failure, and a louder one
    failures.append(f"ARM A: raised {type(error).__name__} instead of UnreachableDestinationError")
    print(f"  ⛔ ARM A  FAIL — wrong exception: {type(error).__name__}")

# ---- ARM B: cannot fly but CAN walk -> silent degrade, no raise ------------------------------
rr.is_map_reachable = lambda _m, **_k: True
try:
    steps = list(_under_test(MapRSE.ROUTE117, PokemonCenter.VerdanturfTown))
    if steps:
        failures.append(f"ARM B: yielded {len(steps)} step(s); a non-flyable approach must be a no-op")
        print(f"  ⛔ ARM B  FAIL — yielded {len(steps)} step(s)")
    else:
        print("  ✅ ARM B  PASS — walkable target degrades quietly (0 steps, no raise)")
except Exception as error:  # noqa: BLE001
    failures.append(
        f"ARM B: raised {type(error).__name__} on a WALKABLE target. A refusal that fires when "
        f"walking is possible breaks every heal-return — a Poké Center is map_type=Indoor, so Fly "
        f"is always illegal there while the grind tile is two hops away.")
    print(f"  ⛔ ARM B  FAIL — raised {type(error).__name__} on a walkable target")

# ---- ARM C: the EVER_GRANDE PLATEAU case -- same map as the landing, but unreachable from it ----
# MEASURED (`evidence/2026-09-18-vr-heal-roundtrip.stdout.txt`): `heal_at_league` leaves the bot at
# EVER_GRANDE_CITY (18,6), the League plateau, and `calculate_path` from there to the Poke Center
# landing (27,49) is NO PATH in both directions (control at (18,42) = 23 wp, so the refusal is real).
# A guard that compares the MAP would say "already in the anchor town" and SKIP the Fly -- stranding
# the leg on the plateau, at the exact position Ch23's last leg hands over.
# => guard 3 must compare the TILE. This arm pins that.
ta.can_fly_to_anchor = lambda _c: True       # we CAN fly (EVER_GRANDE_CITY map_type is "City")
eg._map_group_number = lambda: tuple(MapRSE.EVER_GRANDE_CITY.value)
_flew = {"n": 0}


def _fake_fly(_dest):
    _flew["n"] += 1
    return
    yield  # pragma: no cover - makes this a generator


import modules.story.pokemon_league as _pl_mod
_pl_mod.fly_to_destination = _fake_fly

import modules.player as _player
_player.get_player_avatar = lambda: type("A", (), {"local_coordinates": (18, 6)})()
eg.get_player_avatar = _player.get_player_avatar

list(_under_test(MapRSE.VICTORY_ROAD_1F, PokemonCenter.EvergrandeCity))
if _flew["n"] == 0:
    failures.append(
        "ARM C: standing on the EVER_GRANDE plateau (18,6) the leg did NOT fly. A map-level guard "
        "treats it as 'already in the anchor town', but (18,6) -> (27,49) is measured NO PATH, so "
        "skipping the Fly strands the leg where Ch23 hands over.")
    print("  ⛔ ARM C  FAIL — no Fly attempted from the plateau")
else:
    print("  ✅ ARM C  PASS — plateau (18,6) still flies (guard 3 compares the TILE, not the map)")

# ...and the tile-level guard must still short-circuit when we ARE on the landing.
_flew["n"] = 0
_player.get_player_avatar = lambda: type("A", (), {"local_coordinates": (27, 49)})()
eg.get_player_avatar = _player.get_player_avatar
list(_under_test(MapRSE.VICTORY_ROAD_1F, PokemonCenter.EvergrandeCity))
if _flew["n"] != 0:
    failures.append("ARM C': standing ON the landing (27,49) the leg flew anyway - guard 3 is dead.")
    print("  ⛔ ARM C' FAIL — flew while already on the landing tile")
else:
    print("  ✅ ARM C' PASS — already on the landing (27,49): no Fly, guard 3 still short-circuits")

print()
if _FAULT:
    # Under the fault arm the gate is EXPECTED to fail arm A. Passing there would mean the gate
    # cannot see the defect it was written for.
    if any(f.startswith("ARM A") for f in failures):
        print("  ✅ FAULT ARM BEHAVED — the gate detected the injected defect. Exiting 1 as designed.")
        print(BAR)
        raise SystemExit(1)
    print("  ⛔⛔ FAULT ARM DID NOT FIRE — this gate CANNOT SEE the bug it exists to catch.")
    print(BAR)
    raise SystemExit(1)

if failures:
    print("⛔ FAIL:")
    for f in failures:
        print(f"  • {f}")
    print(BAR)
    raise SystemExit(1)

print("  ✅ PASS — the refusal escapes, and a walkable target still degrades to walking.")
print(BAR)
