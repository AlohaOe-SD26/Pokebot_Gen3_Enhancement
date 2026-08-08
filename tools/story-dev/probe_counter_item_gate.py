"""`#24-counterdesertgate` A/B: does the counter planner refuse an ITEM-GATED ground?

Batch `20260807-200030` sent **7 hunts to ROUTE111 (25,55) for Baltoy and caught 0**: the desert
is Go-Goggles-gated (`AREA_ITEM_PREREQ`) and the spin tile sits NORTH of that gate, so the bot
treks cross-Hoenn, cannot enter, and spins wherever it stopped.

‼ BOTH ARMS ARE RUN ON PURPOSE. The new gate FAILS CLOSED, so offline — with no ROM and no
readable bag — ROUTE111 would be refused anyway, for the WRONG reason. A one-armed test would
show the desired answer and prove nothing. Arm A stubs a bag that HOLDS the goggles (ROUTE111
must be admitted); arm B stubs an empty bag (it must be refused and Winona must fall back).

‼ And Norman is the positive control throughout: `find_counter_candidates` swallows per-location
errors and returns [] on failure, so "0 candidates" is what a BROKEN harness looks like too.
"""
import sys, pathlib, json

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

import modules.map_data as md
from modules.map_data import MapRSE
md.get_map_enum = lambda k: {tuple(m.value): m for m in MapRSE}[tuple(k)]

import modules.encounter_index as ei
_c = json.loads((REPO / "sandbox-pokebot" / "cache" / "encounter_index_BPEE0.json")
                .read_text(encoding="utf-8"))["index"]
ei.get_encounter_index = lambda rebuild=False: {int(k): v for k, v in _c.items()}

import modules.items as items
import modules.story.counter_plan as cp
cp._team_reference_level = lambda: 30

class _Bag:
    def __init__(self, have): self.have = have
    def quantity_of(self, item): return 1 if self.have else 0

def set_bag(have_goggles):
    items.get_item_bag = lambda: _Bag(have_goggles)
    items.get_item_by_name = lambda n: n

# production passes a real predicate; mirror the permissive part of it so ROUTE111's
# `region` prereq is admitted exactly as `_counter_area_allowed` admits it live.
allow = lambda map_enum, tile, prereq: prereq in (None, "region")

FAIL = []
def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok: FAIL.append(label)

for have, arm in ((True, "A: bag HOLDS Go-Goggles"), (False, "B: bag is EMPTY")):
    set_bag(have)
    print(f"\n===== ARM {arm} =====")
    norman = cp.find_counter_candidates({"Fighting"}, allow=allow, max_results=30)
    nb = cp.best_huntable(norman)
    check("CONTROL — Norman still finds Machop @ FIERY_PATH",
          nb is not None and nb["species_name"] == "Machop" and nb["map_enum"] is MapRSE.FIERY_PATH,
          f"{(nb['species_name'], nb['map_enum'].name) if nb else None}")

    win = cp.find_counter_candidates({"Rock", "Ice", "Dragon"}, allow=allow, max_results=30)
    wb = cp.best_huntable(win)
    r111 = [c for c in win if c["map_enum"] is MapRSE.ROUTE111]
    print(f"    Winona best_huntable -> "
          f"{(wb['species_name'], wb['map_enum'].name, wb['answer_via']) if wb else None}")
    if have:
        check("ROUTE111 (Go-Goggles desert) IS offered when we hold the goggles", bool(r111),
              f"{len(r111)} ROUTE111 candidates")
    else:
        check("ROUTE111 is REFUSED when we do not hold the goggles", not r111,
              "this is the 7-hunts-0-catches case from batch 20260807-200030")
        check("Winona falls back to a ground she can actually use",
              wb is not None and wb["map_enum"] is MapRSE.FIERY_PATH,
              f"{(wb['species_name'], wb['map_enum'].name) if wb else None}")

print()
if FAIL:
    print(f"FAILED {len(FAIL)}:")
    for f in FAIL: print("  -", f)
    sys.exit(1)
print("ALL PASS — the gate discriminates on the ITEM, not on a fail-closed accident.")
