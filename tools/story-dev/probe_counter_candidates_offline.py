"""Run the REAL `find_counter_candidates` offline (no emulator) and report per-boss candidates.

‼ WHY THIS FILE HAS A POSITIVE CONTROL, AND WHY THAT IS NOT OPTIONAL.
`find_counter_candidates` swallows per-location errors (`except: continue`) and wraps the whole
body in `except -> return []`. Outside the emulator `get_map_enum` raises AttributeError on
`context.rom`, so EVERY location is skipped and the function returns **0 candidates with no
error and no warning** — identical to a genuine "this boss has no answer". My first attempt at
this probe reported exactly that and I nearly recorded it as a finding about Winona.

So: NORMAN MUST RETURN Machop @ FIERY_PATH. That pairing is independently confirmed live — the
counter hunt catches it 6 of 7 times in batch `20260807-160545`. If the control fails, the
harness is broken and NOTHING else this script prints means anything.
"""
import sys, pathlib, json

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

# --- offline stand-ins for the two things that need a loaded ROM ---------------------------
import modules.map_data as md
from modules.map_data import MapRSE

_BY_VALUE = {tuple(m.value): m for m in MapRSE}
md.get_map_enum = lambda key: _BY_VALUE[tuple(key)]   # pure id -> enum; no ROM needed

import modules.encounter_index as ei
_cache = json.loads((REPO / "sandbox-pokebot" / "cache" / "encounter_index_BPEE0.json")
                    .read_text(encoding="utf-8"))["index"]
_cache = {int(k): v for k, v in _cache.items()}
ei.get_encounter_index = lambda rebuild=False: _cache

import modules.story.counter_plan as cp
cp._team_reference_level = lambda: 30      # no live party offline

BOSSES = {"Norman (CONTROL)": {"Fighting"},
          "Wattson": {"Ground"},
          "Winona": {"Rock", "Ice", "Dragon"}}

results = {}
for boss, needed in BOSSES.items():
    cands = cp.find_counter_candidates(needed, max_results=20)
    hunt = [c for c in cands if c.get("huntable")]
    results[boss] = hunt
    print(f"\n{boss} — needs {sorted(needed)}: {len(cands)} candidates, {len(hunt)} HUNTABLE")
    for c in hunt[:6]:
        print(f"    {c['species_name']:<10} {c['map_enum'].name:<12} tile={c['hunt_tile']} "
              f"rate={c['encounter_rate']}% L{c['level_band']} via={c['answer_via']}")
    b = cp.best_huntable(cands)
    print(f"    best_huntable -> {(b['species_name'], b['map_enum'].name, b['answer_via']) if b else None}")

print("\n" + "=" * 70)
ctrl = results["Norman (CONTROL)"]
ok = any(c["species_name"] == "Machop" and c["map_enum"] is MapRSE.FIERY_PATH for c in ctrl)
print(f"POSITIVE CONTROL — Norman finds Machop @ FIERY_PATH: {'PASS' if ok else 'FAIL'}")
if not ok:
    print("  ‼ The harness is broken (most likely the ROM stand-ins above). Ignore every other")
    print("    number this script printed — a swallowed error looks exactly like 'no answer'.")
    sys.exit(1)
print("=" * 70)
