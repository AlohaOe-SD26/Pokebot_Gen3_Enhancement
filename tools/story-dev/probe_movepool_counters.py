"""MEASUREMENT (read-only): does MOVEPOOL-awareness give Winona a huntable counter?

`counter_plan.py:155-157` keeps a candidate only if the SPECIES' OWN TYPE is one of the needed
types. User point, 2026-08-07: that is too narrow — a species can LEARN a move of a counter type
without being that type. Before changing the selector, measure whether it would actually help.

Scope: the FOUR grounds the hunt whitelist can currently reach
(`training_areas.hunt_ground_tile`): FIERY_PATH + the three TRAINING_GRASS maps.

‼ MOVE CLASSIFICATION MATTERS AND IS EASY TO GET WRONG. Only a DAMAGING move counters a boss:
`base_power > 0`. Everything with `base_power == 0` is status / stat-change / field effect and
does NOT answer a type weakness — Toxic, Growl, Sunny Day. **Smog is NOT in that group**: it is
20-power Poison damage with a poison side-effect (`effect=POISON_HIT`), and treating it as
"status" would wrongly reject a real answer. Classify on base_power, never on the name or on
whether the move has a secondary effect.
"""
import sys, pathlib
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.map_data import MapRSE
from modules.pokemon import get_species_by_name
import json
from modules.story.training_areas import hunt_ground_tile

NEEDED = {"Winona": {"Rock", "Ice", "Dragon"},
          "Norman": {"Fighting"},
          "Wattson": {"Ground"}}

# The maps a hunt may currently stand on.
grounds = [m for m in MapRSE if hunt_ground_tile(m) is not None]
print(f"huntable grounds ({len(grounds)}): {[m.name for m in grounds]}\n")

# ‼ Read the CACHE, not get_encounter_index(): the builder needs a loaded ROM (context.rom)
# and dies with AttributeError outside the emulator. The cache is the same data.
idx = json.loads((REPO / 'sandbox-pokebot' / 'cache' / 'encounter_index_BPEE0.json').read_text(encoding='utf-8'))['index']
# species index -> list of locations; invert to map -> species present
from collections import defaultdict
by_map = defaultdict(list)
for sid, locs in idx.items():
    for l in locs:
        by_map[tuple(l["map"])].append((sid, l))

from modules.pokemon import get_species_by_index

def damaging_moves_of_types(species, types, max_level):
    """(level_up_hits, tm_hm_hits) — DAMAGING moves only (base_power > 0)."""
    lv, tm = [], []
    for e in species.learnset.level_up:
        if e.move.base_power > 0 and e.move.type.name in types and e.level <= max_level:
            lv.append((e.level, e.move.name, e.move.base_power))
    for e in species.learnset.tm_hm:
        if e.move.base_power > 0 and e.move.type.name in types:
            tm.append((e.item.name, e.move.name, e.move.base_power))
    return sorted(lv), tm

# ‼ THE NAIVE VERSION OF THIS IDEA IS WORSE THAN WHAT WE HAVE. Most raw hits are TM/HM:
# TM13 Ice Beam / TM14 Blizzard (TMs are single-use and we almost certainly do not own them) and
# HM06 Rock Smash at **20 power** — the exact case `CREDIBLE_ANSWER_POWER` exists to reject
# ("a 20-power HM is 2.0x against Normal and still loses to Slaking 27 times running"). An
# unfiltered movepool rule would call every Zigzagoon a Norman counter.
# So the real question is the ACTIONABLE subset: a DAMAGING move, learned by LEVEL-UP (no TM we
# may not own), that clears the credible-power floor.
CREDIBLE = 75.0  # mirrors StoryMode.CREDIBLE_ANSWER_POWER (story_mode.py:846)

def actionable(species, types, max_level):
    own = {t.name for t in species.types}
    out = []
    for e in species.learnset.level_up:
        m = e.move
        if m.base_power <= 0 or m.type.name not in types or e.level > max_level:
            continue
        stab = 1.5 if m.type.name in own else 1.0
        score = m.base_power * 2.0 * stab
        if score >= CREDIBLE:
            out.append((e.level, m.name, m.base_power, round(score)))
    return sorted(out)

print("=" * 72)
print("ACTIONABLE ONLY — damaging, LEVEL-UP, power*2.0*STAB >= %g" % CREDIBLE)
print("=" * 72)
for boss, needed in NEEDED.items():
    hits = []
    for g in grounds:
        for sid, loc in by_map.get(tuple(g.value), []):
            try: sp = get_species_by_index(int(sid))
            except Exception: continue
            own = {t.name for t in sp.types}
            cap = max(loc.get("max_level", 0), 0)
            a = actionable(sp, needed, cap + 15)
            if a:
                hits.append((g.name, sp.name, "/".join(sorted(own)), cap, a[0], bool(own & needed)))
    seen=set(); uniq=[]
    for h in hits:
        if (h[0],h[1]) in seen: continue
        seen.add((h[0],h[1])); uniq.append(h)
    bytype=[h for h in uniq if h[5]]; bymove=[h for h in uniq if not h[5]]
    print()
    print(f"{boss} needs {sorted(needed)} -> {len(bytype)} by TYPE, {len(bymove)} NEW by movepool")
    for h in bymove[:8]:
        print(f"    {h[1]} ({h[2]}) on {h[0]} Lmax={h[3]}  learns {h[4][1]} (L{h[4][0]}, {h[4][2]}bp, score {h[4][3]})")
print()

for boss, needed in NEEDED.items():
    print("=" * 72)
    print(f"{boss} — needs {sorted(needed)}")
    print("=" * 72)
    by_type, by_move = [], []
    for g in grounds:
        for sid, loc in by_map.get(tuple(g.value), []):
            try:
                sp = get_species_by_index(int(sid))
            except Exception:
                continue
            own = {t.name for t in sp.types}
            cap = max(loc.get("max_level", 0), 0)
            # allow some training headroom above the wild's level
            lv, tm = damaging_moves_of_types(sp, needed, cap + 15)
            if own & needed:
                by_type.append((g.name, sp.name, sorted(own), loc.get("rate"), cap))
            elif lv or tm:
                by_move.append((g.name, sp.name, sorted(own), cap, lv[:3], tm[:3]))
    print(f"  BY SPECIES TYPE (what the selector accepts today): {len(by_type)}")
    for r in by_type[:6]:
        print(f"     {r[1]} ({'/'.join(r[2])}) on {r[0]} rate={r[3]}% Lmax={r[4]}")
    print(f"  BY LEARNABLE DAMAGING MOVE (what it would gain): {len(by_move)}")
    seen = set()
    for r in by_move:
        key = (r[0], r[1])
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > 8:
            break
        print(f"     {r[1]} ({'/'.join(r[2])}) on {r[0]} Lmax={r[3]}")
        if r[4]:
            print(f"        level-up: {r[4]}")
        if r[5]:
            print(f"        TM/HM   : {r[5]}")
    print()
