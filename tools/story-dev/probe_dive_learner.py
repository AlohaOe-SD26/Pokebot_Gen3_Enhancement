"""§Ch21 UNBLOCK — where can this bot actually CATCH a Dive learner? Measured from our own data.

‼‼ THIS PROBE EXISTS BECAUSE I WROTE A "MEASURED" CORRECTION THAT HAD NO MEASUREMENT. On
2026-08-12 I corrected KI-63's suggested roster swap — Wailmer is rod-only, Spheal is the real
answer — and committed it as `docs: correct two of my own claims`. An adversarial pass then pointed
out that the commit touched **one file, docs only**: no script, no artifact. Every number in it was
independently re-derived and turned out to be RIGHT, but it was **right by luck of a good recall,
not by anything reproducible**, and `probe_ch19_hazards.py` checks only the party's learners, never
the encounter tables the plan rests on.

That is the exact failure mode this project's rules exist to prevent, committed by the agent
enforcing them. So: this file makes the claim reproducible. It reads OUR ROM's data, not memory.

WHAT IT ANSWERS, in the order the decision needs it:
  1. Which species learn Dive at all, and does anyone in our party? (KI-63's core claim.)
  2. Is there an EVOLUTION escape — does anything our party can become learn Dive? (If yes, no
     catch is needed and the whole roster problem evaporates.)
  3. Which LAND encounter tables host a Dive learner, ranked by rate? ‼ Land specifically, because
     `_hm_hunting_grounds` reads `land_encounters` ONLY — a 60%-rate fishing slot the bot has no
     machinery to use is not an option, it is a distraction.
  4. Which of those also learn SURF, since Zigzagoon L15 is our only Surf carrier and dropping it
     is not free.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dive_learner.py
"""

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

BAR = "=" * 100

DIVE = "Dive"
SURF = "Surf"

#: Our party as measured on `post_mossdeep_gym.ss1` by `probe_ch19_hazards.py`. Hard-coded on
#: purpose: this probe answers a DATA question and must run without an emulator, so the party is an
#: input. ‼ If it ever disagrees with the hazard probe, believe the hazard probe — it reads the save.
PARTY = ["Sceptile", "Zigzagoon", "Swellow", "Skitty", "Mightyena", "Castform"]


def head(title):
    print(f"\n{BAR}\n{title}\n{BAR}\n")


species = json.loads((BUILD / "modules/data/species.json").read_text(encoding="utf-8"))
if isinstance(species, dict):
    species_list = list(species.values())
else:
    species_list = species


def name_of(entry):
    return entry.get("name") or entry.get("Name") or "?"


# ‼ LEARNSETS STORE MOVE **IDS**, NOT NAMES — `learnset.tm_hm` is a list of ints and
# `learnset.level_up` is a {level: move_id} map. The first draft of this probe matched on strings,
# found ZERO Dive learners, and its own guard refused to call that a pass. Deriving the ids from
# `moves.json` by name (rather than hard-coding "Dive = 291") means a data change breaks this
# loudly instead of silently answering "nobody learns Dive".
moves = json.loads((BUILD / "modules/data/moves.json").read_text(encoding="utf-8"))
move_entries = list(moves.values()) if isinstance(moves, dict) else moves


def move_id_for(move_name):
    for index, entry in enumerate(move_entries):
        if isinstance(entry, dict) and entry.get("name") == move_name:
            return entry.get("index", entry.get("id", index))
    return None


DIVE_ID = move_id_for(DIVE)
SURF_ID = move_id_for(SURF)
print(f"\nresolved move ids from moves.json: {DIVE}={DIVE_ID}  {SURF}={SURF_ID}")
if DIVE_ID is None or SURF_ID is None:
    print("‼ could not resolve the move ids — this probe cannot measure anything. NOT a pass.")
    raise SystemExit(1)


def learns(entry, move_id):
    """Does this species learn `move_id` by TM/HM or by level-up?

    Both pools are checked: `tm_hm` is what matters for an HM, and `level_up` catches a species
    that would learn it naturally anyway."""
    learnset = entry.get("learnset") or {}
    tm_hm = learnset.get("tm_hm") or []
    if move_id in tm_hm:
        return True
    level_up = learnset.get("level_up") or {}
    if isinstance(level_up, dict) and move_id in level_up.values():
        return True
    return False


print(BAR)
print("PROBE — Dive learners, read from OUR data files (species.json + the encounter index)")
print(BAR)

dive_learners = {name_of(e) for e in species_list if learns(e, DIVE_ID)}
surf_learners = {name_of(e) for e in species_list if learns(e, SURF_ID)}
print(f"\nspecies parsed: {len(species_list)}")
print(f"species that learn {DIVE}: {len(dive_learners)}")
print(f"species that learn {SURF}: {len(surf_learners)}")
if not dive_learners:
    print("‼ ZERO Dive learners parsed — the learnset key shape must have changed. This probe is")
    print("  measuring nothing, which is NOT a pass.")
    raise SystemExit(1)

# ---------------------------------------------------------------------------------------------
head("1 — OUR PARTY (KI-63's core claim)")

for mon in PARTY:
    marks = []
    if mon in dive_learners:
        marks.append("DIVE")
    if mon in surf_learners:
        marks.append("SURF")
    print(f"  {mon:<12} {'+'.join(marks) if marks else '-'}")
party_dive = [m for m in PARTY if m in dive_learners]
print(f"\n  Dive learners in the party: {party_dive or 'NONE'}")
print(f"  Surf carriers in the party: {[m for m in PARTY if m in surf_learners] or 'NONE'}")
print("  ‼ The Surf line matters: dropping our ONLY Surf carrier to make room would trade one")
print("    blocker for another.")

# ---------------------------------------------------------------------------------------------
head("2 — IS THERE AN EVOLUTION ESCAPE? (if yes, no catch is needed at all)")

by_name = {name_of(e): e for e in species_list}

# ‼‼ `evolutions[].target_species` IS A LIST INDEX INTO species.json — not a national dex number.
# Verified against a known pair: Wartortle sits at index 8 and its `target_species` is 9, which is
# Blastoise. Reading it as a national dex number instead produced "Zigzagoon -> Slaking" and
# "Skitty -> Gulpin" — visibly absurd, which is the only reason it was caught. ‼ The wrong mapping
# would still have returned the RIGHT ANSWER to the question being asked ("no evolution learns
# Dive"), i.e. it would have confirmed a correct conclusion with garbage data. Sanity-check any
# id→name resolution against a pair you already know before trusting what it says about pairs you
# do not.
def evolutions_of(mon_name):
    entry = by_name.get(mon_name) or {}
    out = []
    for item in entry.get("evolutions") or []:
        if isinstance(item, dict):
            target_index = item.get("target_species")
            if isinstance(target_index, int) and 0 <= target_index < len(species_list):
                out.append(name_of(species_list[target_index]))
    return out


# A control on the resolution itself, printed rather than assumed.
_control = evolutions_of("Wartortle")
print(f"  [control] Wartortle evolves into {_control} (expected ['Blastoise'])")
if _control != ["Blastoise"]:
    print("  ‼ the evolution id→name mapping is WRONG; section 2 below cannot be believed.")
    # ‼ ADDED 2026-08-22 (sanity check PASS 4). This printed "cannot be believed" and then CARRIED
    # ON AND EXITED 0 — a positive control that announces its own failure and still reports PASS is
    # not a control. Three of this suite's probes were found with the same shape on the same day.
    raise SystemExit(1)


escape = []
for mon in PARTY:
    evos = evolutions_of(mon)
    for evo in evos:
        flag = " <== LEARNS DIVE" if evo in dive_learners else ""
        print(f"  {mon:<12} -> {evo}{flag}")
        if evo in dive_learners:
            escape.append((mon, evo))
    if not evos:
        print(f"  {mon:<12} -> (no evolution)")
print(f"\n  evolution escape available: {escape or 'NONE — a CATCH IS MANDATORY'}")

# ---------------------------------------------------------------------------------------------
head("3 — LAND encounter tables that host a Dive learner, ranked by rate")

print("‼ LAND ONLY, and that is a decision not an oversight: `_hm_hunting_grounds` reads")
print("  `land_encounters` exclusively, so a 60%-rate fishing slot is not an option the bot can")
print("  take today — it is a distraction with three missing subsystems behind it.\n")

index_path = BUILD / "cache/encounter_index_BPEE0.json"
rows = []
if not index_path.is_file():
    print(f"‼ no encounter index at {index_path} — cannot answer (3). NOT a pass.")
    raise SystemExit(1)

payload = json.loads(index_path.read_text(encoding="utf-8"))
index = payload.get("index", {})

# ‼ THE INDEX IS KEYED BY SPECIES **LIST INDEX** (the same id space as `target_species`), and each
# value is a flat list of locations carrying `method` / `rate` / `min_level` / `max_level`. That is
# not obvious from the file, so the resolution gets a printed CONTROL: if the key space is ever
# something else, this line says so instead of the probe quietly reporting an empty result.
_ctrl_key = next(iter(index))
_ctrl_name = name_of(species_list[int(_ctrl_key)]) if int(_ctrl_key) < len(species_list) else "?"
_ctrl_where = index[_ctrl_key][0].get("map_name") if index[_ctrl_key] else "?"
print(f"  [control] index key {_ctrl_key} resolves to {_ctrl_name}, first location {_ctrl_where}")

LAND_METHODS = {"grass"}          # the only method `_hm_hunting_grounds` can use
for key, locations in index.items():
    try:
        entry = species_list[int(key)]
    except (ValueError, IndexError):
        continue
    sp = name_of(entry)
    if sp not in dive_learners or not isinstance(locations, list):
        continue
    for slot in locations:
        if not isinstance(slot, dict):
            continue
        if str(slot.get("method", "")).strip().lower() not in LAND_METHODS:
            continue
        rows.append((
            slot.get("rate") or 0,
            slot.get("map_name") or "?",
            sp,
            slot.get("min_level"),
            slot.get("max_level"),
            sp in surf_learners,
        ))

rows.sort(key=lambda r: -r[0])
if not rows:
    print("‼ no LAND table in the index hosts a Dive learner — either the plan is wrong or the")
    print("  index shape changed. Either way this is NOT a pass.")
    # ‼ ADDED 2026-08-22 (sanity check PASS 4). The probe SAID "NOT a pass" and exited 0 anyway.
    # An agent fault-injected this branch (309 `grass` slots rewritten to `surf`) and the suite
    # stayed green over it. The words were right; only the exit code was missing.
    raise SystemExit(1)
for rate, map_name, sp, lo, hi, also_surf in rows[:18]:
    surf_mark = "  +SURF (covers BOTH duties)" if also_surf else ""
    print(f"  {rate:>3}%  {map_name:<42} {sp:<12} L{lo}-{hi}{surf_mark}")

# ---------------------------------------------------------------------------------------------
head("VERDICT")

best = [r for r in rows if r[5]]          # Dive AND Surf — one catch covers both duties
print(f"  party Dive learners            : {party_dive or 'NONE'}  (KI-63 holds: {not party_dive})")
print(f"  evolution escape               : {escape or 'NONE'}")
print(f"  LAND tables with a Dive learner: {len(rows)}")
print(f"  ...of which ALSO learn Surf    : {len(best)}")
if best:
    rate, map_name, sp, lo, hi, _ = best[0]
    print(f"\n  BEST SINGLE CATCH: {sp} at {rate}% on {map_name} (L{lo}-{hi})")
    print("  — it covers BOTH duties, so it can replace a passenger without costing us Surf.")
print("\n‼ WHAT THIS PROBE DOES NOT ANSWER, said plainly rather than left implied:")
print("  * TIDE. If the best table is a Shoal Cave LOW-tide map, the bot must arrive at low tide,")
print("    and which RTC hours give it is UNVERIFIED here.")
print("  * REACHABILITY. A rate is not a route — the spin tile must be derived and two-way swept")
print("    from a real anchor before it goes in `TRAINING_GRASS` (the Route 114 lesson).")
