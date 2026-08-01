"""KI-44: a freshly-caught counter must train somewhere it can REACH and RETURN from.
NO EMULATOR — the training tables are static; only the reachability predicate needs a ROM,
and that is exactly the part this test stubs so it can assert the picker's own rules.

WHAT WENT WRONG (batch4, `x4-runs/20260731-201554`, 7 of 7 attempts):

    Story: training the counter — Machop L15 -> L21 (team is L35, est 222115 frames).
    Story: counter training failed (UnreachableDestinationError('Could not reach (9, 2) on
      MapRSE.ROUTE102: ... not walkable from ROUTE103 ...')) — continuing untrained.

`train_counter` used `cfg["grass"]` — the BOSS's patch. For Norman that is
`PETALBURG_TRAINING_GRASS = (ROUTE102, (9, 2))`, while the Machop is caught in FIERY_PATH.
Two independent faults, and the log only showed the first:

  1. it cannot get there — 6 of 7 stranded on ROUTE103 (45, 7), eight maps away;
  2. it would not be worth going — ROUTE102's land wilds are **L3-4** (probed
     2026-08-01, `probe_counter_grass.py`), the "~25 xp a kill, i.e. never" patch
     `story_mode.py` already documents. A counter is L14-16 by construction.

‼ AND THE OBVIOUS REPAIR IS ALSO WRONG. "Just train where you caught it" would pick
FIERY_PATH — which is in `NO_RETURN_GROUNDS`. It can be reached and left (fine for a
catch-and-leave hunt) but the heal leg back to Lavaridge FAILS, and a training loop needs
that third leg. Same for ROUTE112 and JAGGED_PASS. That is why this test asserts a
PROPERTY (never a no-return ground, never wilds the trainee cannot beat) rather than one
hardcoded map: a future table edit must not be able to quietly reintroduce the hole.
"""

from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.story.training_areas import (  # noqa: E402
    NO_RETURN_GROUNDS,
    TRAINING_GRASS,
    best_training_area,
)

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


ALLOW_ALL = lambda m, t, p: True  # noqa: E731 — "everything is reachable", the hostile case

print("1. the picker never proposes a ground it cannot heal from")
# Sweep every level a freshly-caught counter can plausibly be. Hunting grounds run
# L14-16 (Fiery Path) up to L20-22 (Jagged Pass), so 10..30 covers it with margin.
bad = []
for level in range(10, 31):
    pick = best_training_area(level, allow=ALLOW_ALL)
    if pick is not None and pick[0] in NO_RETURN_GROUNDS:
        bad.append((level, pick[0].name))
check(
    "no no-return ground is ever picked, L10-L30, even with allow=<always true>",
    not bad,
    f"picked {bad[:4]}" if bad else "FIERY_PATH / ROUTE112 / JAGGED_PASS all refused",
)

print("2. the winnability guard holds — never a band the trainee would lose to")
bad = []
for level in range(10, 31):
    pick = best_training_area(level, allow=ALLOW_ALL)
    if pick is not None and level < pick[2][0] - 1:
        bad.append((level, pick[0].name, pick[2]))
check("trainee level >= band_low - 1 for every pick", not bad, str(bad[:3]))

print("3. the specific batch4 case: a L15 counter must NOT be sent to ROUTE102's L3-4")
pick = best_training_area(15, allow=ALLOW_ALL)
check("a ground is found for a L15 counter", pick is not None)
if pick is not None:
    name, tile, band = pick[0].name, pick[1], pick[2]
    print(f"       picked {name} {tile} L{band[0]}-{band[1]}")
    check("it is not ROUTE102 (the boss's L3-4 patch)", name != "ROUTE102")
    # The point of relocating is xp rate, which this module models as proportional to the
    # WILD level. A pick must therefore beat Route 102's ceiling by a real margin.
    r102_hi = next((hi for m, t, (lo, hi) in TRAINING_GRASS if m.name == "ROUTE102"), None)
    check(
        "its wild band is materially richer than ROUTE102's",
        r102_hi is not None and band[1] >= 2 * r102_hi,
        f"picked L{band[1]} vs ROUTE102 L{r102_hi} ceiling",
    )

print("4. `counter_training_ground` falls back rather than crashing")
# It imports story_mode (which needs a ROM) for the reachability predicate; with no
# emulator that raises, and the contract is to degrade to the configured pair — never to
# let a picker failure destroy a successful CATCH.
from modules.map_data import MapRSE  # noqa: E402
from modules.story.counter_hunt import counter_training_ground  # noqa: E402

cfg = {"grass": (MapRSE.ROUTE102, (9, 2)), "heal": "PETALBURG_PC"}
got = counter_training_ground(15, cfg)
check("returns a (grass, heal) pair", isinstance(got, tuple) and len(got) == 2, str(got))
check(
    "with no ROM it degrades to the configured pair, it does not raise",
    got == (cfg["grass"], cfg["heal"]),
    f"got {got}",
)
empty = counter_training_ground(15, {})
check("a cfg with no grass yields (None, None) rather than an exception", empty == (None, None), str(empty))

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
