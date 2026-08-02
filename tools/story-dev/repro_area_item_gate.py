"""A training area behind an ITEM gate must be refused before the trek, not after it.
NO EMULATOR — the table is static and the call-site is checked structurally.

WHAT WENT WRONG (batch5, `x4-runs/20260801-075805`): **28 events** of

    Story: ROUTE111 (25, 55) is not reachable from here — dropping it as a training
           option for the rest of this run.

i.e. roughly one wasted cross-Hoenn trek PER RUN. `_training_area_allowed` asks
`region_reach.is_map_reachable(ROUTE111)`, which answers at MAP granularity and is correctly
True — Route 111's southern half IS walkable from Mauville. But the training tile (25,55)
sits NORTH of the Go-Goggles desert. The predicate is handed the TILE and never uses it.

‼ THE FACT WAS ALREADY WRITTEN DOWN TWICE and neither copy was queryable:
`counter_plan.huntable_candidates` ("whose tile sits north of the Go-Goggles desert") and
`early_game` ("Go-Goggles-gated by a script"). Prose in a table nobody queries is exactly the
failure `NO_RETURN_GROUNDS`' header warns about. Hence `AREA_ITEM_PREREQ`, which IS queried.

‼ `KNOWN_GATES` could not express this: it keys map-PAIR EDGES and its values are FIELD
MOVES. Here the barrier is INSIDE one map and the key is an ITEM.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

from modules.map_data import MapRSE  # noqa: E402
from modules.story.training_areas import (  # noqa: E402
    AREA_ITEM_PREREQ,
    AREA_PREREQ,
    TRAINING_GRASS,
)

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


print("1. the gate exists and names the measured case")
check("ROUTE111 has an item prerequisite", MapRSE.ROUTE111 in AREA_ITEM_PREREQ)
check("it is Go-Goggles", AREA_ITEM_PREREQ.get(MapRSE.ROUTE111) == "Go-Goggles",
      str(AREA_ITEM_PREREQ.get(MapRSE.ROUTE111)))

print("2. every gated item is a REAL item in the ROM's own data")
# A typo here would fail closed forever and silently — the area would simply never be
# proposed again, which is the KI-24 failure shape (an invisible NO).
import json  # noqa: E402

raw = json.loads((SANDBOX / "modules" / "data" / "items.json").read_text(encoding="utf-8"))
names = {i.get("name") for i in (raw if isinstance(raw, list) else raw.values())}
for area, item in AREA_ITEM_PREREQ.items():
    check(f"'{item}' exists in items.json (gate for {area.name})", item in names)

print("3. the gated area is still a real training entry (the table did not drift)")
entry = [(m, t, b) for m, t, b in TRAINING_GRASS if m is MapRSE.ROUTE111]
check("ROUTE111 is still in TRAINING_GRASS", len(entry) == 1, str(entry))
if entry:
    m, tile, band = entry[0]
    check("its tile is still the desert-side (25, 55)", tuple(tile) == (25, 55), str(tile))
    check("its band is still L19-22", tuple(band) == (19, 22), str(band))
check("it also still carries the 'region' prereq", AREA_PREREQ.get(MapRSE.ROUTE111) == "region")

print("4. ‼ the predicate actually CONSULTS the table, and fails CLOSED")
src = (SANDBOX / "plugins" / "custom_modes" / "story_mode.py").read_text(
    encoding="utf-8", errors="replace"
)
fn = re.search(r"def _training_area_allowed\(.*?(?=\ndef )", src, re.S)
check("_training_area_allowed is present", fn is not None)
if fn:
    body = fn.group(0)
    check("it imports AREA_ITEM_PREREQ", "AREA_ITEM_PREREQ" in body)
    check("it checks the bag quantity", "quantity_of" in body)
    # The gate must be evaluated BEFORE the map-granular oracle, otherwise a True from
    # is_map_reachable would already have been returned and the item never consulted.
    # ‼ Anchor on the CALL SITE, not the first mention. This function's docstring discusses
    # `is_map_reachable` at length, so a naive `.find` matches the prose and reports a false
    # failure — which is exactly what it did on the first run of this test.
    i_item = body.find("needed_item = AREA_ITEM_PREREQ.get(")
    i_oracle = body.find("return bool(region_reach.is_map_reachable(")
    check("the item gate is evaluated BEFORE the is_map_reachable CALL",
          -1 < i_item < i_oracle, f"item@{i_item} oracle-call@{i_oracle}")
    check("a lookup failure fails CLOSED (returns False)",
          re.search(r"except Exception:.*?\n\s*return False", body, re.S) is not None)

print("5. an ungated area is unaffected")
for area in (MapRSE.ROUTE116, MapRSE.ROUTE117, MapRSE.ROUTE102):
    check(f"{area.name} has no item gate", area not in AREA_ITEM_PREREQ)

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
