# -*- coding: utf-8 -*-
"""⭐ DOES THE LEVEL-APPROPRIATE LADDER ACTUALLY AVOID THE EXP LEAK, AT EVERY RUNG? (`#24-levelgap`)

WHY THIS EXISTS. USER RULING 2026-09-19 says train each m\u014dn at a level-appropriate ground so it
"can actually fight or be swap trained". The reason that ruling WORKS is mechanical, not
aesthetic: `SwapTrainBattleStrategy` fires when `trainee.level + UNDERLEVEL_MARGIN <= foe.level`
(`UNDERLEVEL_MARGIN = 2`), which puts TWO participants in the battle so the FINISHER banks an equal
share. \u2b50 A trainee fighting at its own level never triggers that switch and solos for FULL xp as
the only participant \u21d2 no exp leaks, and the ruling's own L65-75 CEILING survives.

\u26d4\u26d4 BUT THAT ONLY HOLDS IF EVERY RUNG OF THE LADDER IS LEVEL-APPROPRIATE. The selector picks by
`abs(hi - team_level)`, which minimises the gap to the band's TOP \u2014 it does not guarantee the
trainee is ABOVE the band. A wild is drawn from `lo..hi`, so the worst case each battle is `hi`, and
the leak returns for any trainee at or below `hi - UNDERLEVEL_MARGIN`.

\u21d2 THIS PROBE WALKS THE WHOLE LADDER, level by level, and reports **every rung where the trainee
would still swap** \u2014 i.e. every level at which the ruling's mechanism silently stops working.

\u26a0 WHAT IT DOES NOT MODEL: which wild is actually drawn (slot weights), the trainee's HP, or the
"CAN'T CONTINUE" second swap trigger (low HP after a close fight). It answers the UNDER-LEVELLED
trigger only \u2014 the one the ruling is about. A clean result here is not a promise of zero swaps.

READ-ONLY: pure table arithmetic, no ROM, no emulator, milliseconds.
"""
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

sys.path.insert(0, str(_pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement") / "sandbox-pokebot"))

from modules.story.training_areas import best_training_area

#: \u203c READ FROM THE PRODUCTION CLASS, never hardcoded \u2014 if someone retunes the trigger this probe
#: must move with it. `SwapTrainBattleStrategy.UNDERLEVEL_MARGIN`.
try:
    from plugins.custom_modes.story_mode import SwapTrainBattleStrategy

    MARGIN = int(SwapTrainBattleStrategy.UNDERLEVEL_MARGIN)
    MARGIN_SRC = "read from SwapTrainBattleStrategy.UNDERLEVEL_MARGIN"
except Exception as error:  # noqa: BLE001 - a failed import IS a finding; do not silently assume 2
    MARGIN, MARGIN_SRC = None, f"\u26d4 COULD NOT READ: {type(error).__name__}: {error}"

FLOOR, CEILING = 65, 75
#: A permissive predicate: this probe asks what the LADDER looks like, not what a given party can
#: reach today. Reachability is the selector's job and is tested elsewhere.
PERMISSIVE = lambda _m, _t, _p: True  # noqa: E731

print("=" * 104)
print("THE TRAINING LADDER: at which levels does the exp leak still fire?")
print("=" * 104)
print(f"  UNDERLEVEL_MARGIN = {MARGIN}   ({MARGIN_SRC})")
if MARGIN is None:
    print("  \u26d4 without the real margin this probe would be guessing. Refusing to report.")
    raise SystemExit(1)
print(f"  swap fires when:  trainee + {MARGIN} <= foe   \u21d2  leak whenever trainee <= band_hi - {MARGIN}")
print()

print(f"  {'lvl':<5} {'ground chosen':<34} {'band':<10} {'worst foe':<10} verdict")
print("  " + "-" * 96)
leak_levels = []
gap_levels = []
for lvl in range(10, CEILING + 1):
    r = best_training_area(lvl, allow=PERMISSIVE)
    if r is None:
        gap_levels.append(lvl)
        if lvl % 5 == 0 or lvl < 20:
            print(f"  L{lvl:<4} {'\u26d4 NO GROUND AT ALL':<34}")
        continue
    m, tile, (lo, hi) = r
    leaks = lvl <= hi - MARGIN
    if leaks:
        leak_levels.append(lvl)
    show = lvl in (10, 15, 19, 22, 25, 28, 30, 34, 36, 37, 38, 39, 40, 45, 50, 60, 65, 70, 75)
    if show or leaks:
        verdict = (f"\u26d4 SWAPS \u2014 leaks to the finisher" if leaks
                   else "\u2705 solos (full xp, no leak)")
        print(f"  L{lvl:<4} {m.name + str(tuple(tile)):<34} {str((lo, hi)):<10} "
              f"L{hi:<9} {verdict}")

print()
print("=" * 104)
if gap_levels:
    print(f"  \u26a0 {len(gap_levels)} level(s) have NO ground at all: "
          f"L{min(gap_levels)}..L{max(gap_levels)} \u2014 the selector returns None there.")

if not leak_levels:
    print("  \u2705\u2705 NO RUNG LEAKS. At every level 10-75 the chosen ground's top wild is within "
          f"{MARGIN - 1} of the trainee, so the under-levelled swap never fires and every battle is")
    print("     soloed for full xp. \u21d2 the ruling's mechanism holds across the whole ladder.")
else:
    runs = []
    start = prev = leak_levels[0]
    for l in leak_levels[1:]:
        if l == prev + 1:
            prev = l
            continue
        runs.append((start, prev))
        start = prev = l
    runs.append((start, prev))
    pretty = ", ".join(f"L{a}" if a == b else f"L{a}-L{b}" for a, b in runs)
    print(f"  \u26d4\u26d4 {len(leak_levels)} RUNG(S) STILL LEAK: {pretty}")
    print()
    print("     \u21d2 AT THOSE LEVELS THE RULING'S MECHANISM DOES NOT HOLD. The selector minimises")
    print("       `abs(hi - team_level)`, which finds the CLOSEST band \u2014 not necessarily one the")
    print("       trainee out-levels. Where the closest band's top is 2+ above the trainee, the")
    print("       under-levelled trigger still fires and the finisher still banks an equal share.")
    print()
    print("     \u2b50 WHAT A LEG MUST THEREFORE DO, and this is the actionable finding:")
    print("       do NOT simply ask for the closest band. Either")
    print("         (a) require `trainee >= hi - 1` and accept a lower band when none qualifies, or")
    print("         (b) accept the leak at those rungs and CHECK the ceiling afterwards.")
    print("       \u26d4 (b) is the shape that produced L89 finishers before the ruling. Prefer (a).")

# \u2b50 THE CORRECTED LADDER \u2014 what the same walk answers once the out-level cap is applied. This is
# the table Piece 2's selector must reproduce, so it lives here and stays re-runnable.
print()
print("=" * 104)
print("  THE CORRECTED LADDER \u2014 best_training_area(lvl, max_wild_max=lvl+1)")
print("=" * 104)
runs = []
for lvl in range(15, CEILING + 1):
    r = best_training_area(lvl, allow=PERMISSIVE, max_wild_max=lvl + 1)
    key = None if r is None else (r[0].name, tuple(r[2]))
    if not runs or runs[-1][0] != key:
        runs.append([key, lvl, lvl])
    else:
        runs[-1][2] = lvl
for key, a, b in runs:
    span = f"L{a}" if a == b else f"L{a}-L{b}"
    print(f"  {span:<10} " + ("\u26d4 NO GROUND" if key is None else f"{key[0]} {key[1]}"))

capped_leaks = [l for l in range(15, CEILING + 1)
                if (r := best_training_area(l, allow=PERMISSIVE, max_wild_max=l + 1))
                and l <= r[2][1] - MARGIN]
capped_none = [l for l in range(15, CEILING + 1)
               if best_training_area(l, allow=PERMISSIVE, max_wild_max=l + 1) is None]
print()
print(f"  leaking rungs under the cap : {capped_leaks or 'NONE \u2705'}")
print(f"  levels with no ground       : {capped_none or 'none \u2705'}")
if not capped_leaks and not capped_none:
    print("  \u2b50\u2b50 AND THE STRUCTURAL POINT: from L39 to L75 there is exactly ONE ground in the game,")
    print("     and it is the one a \u00a7Ch24 party is already standing on. \u21d2 the Fly ladder serves the")
    print("     LOW m\u014dn only, and only up to L38 \u2014 it is required, but it is not the expensive half.")
print("=" * 104)
