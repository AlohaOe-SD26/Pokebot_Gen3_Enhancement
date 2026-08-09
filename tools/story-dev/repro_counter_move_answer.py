"""`#24-slugmaspin`: the hunt's SUCCESS TEST must accept a MOVE answer, not only a type match.

MEASURED, batch `20260808-131334`. Winona's rung fired 5 times, reached Fiery Path, and
**encountered Slugma 34 times** — 9.3% of the 365 encounters there, exactly its 10% slot — while
`counter hunt CAUGHT Slugma` stayed at **0**.

Slugma is FIRE; Winona needs Rock/Ice/Dragon. Catch-on-sight caught it; `party_counter_slot`
tested the mon's OWN TYPE, did not recognise it, so `_stop()` never fired, the spin ran to budget
and the hunt reported nothing caught. In the same batch Machop (a TYPE match) converted 6 of 64
encounters and Numel 3 of 112 — so it was never the spin, the rate, or travel.

**`#24-movepoolcounters` taught the PLANNER about movepools and left the SUCCESS TEST behind.**
This file pins the other half.

‼ The move test is deliberately LENIENT — it asks only that the mon KNOW a damaging move of a
needed type, not that the move clear the credible-power floor. A freshly caught L15 Slugma knows
Rock Throw, and that must register as success; the strict question belongs to
`_boss_plan_is_hopeless`, and asking it here would make a real catch look like a failed hunt.

‼ DAMAGING ONLY. Case 4 is the guard: Sandstorm is a ROCK move with base_power 0, and a
stat-change / field-effect / status move answers no type weakness (user directive 2026-08-07).
"""
import sys, pathlib
from types import SimpleNamespace as NS
REPO = pathlib.Path.cwd().parents[1]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
import modules.pokemon_party as pp
from modules.pokemon import get_species_by_name, get_move_by_name
import modules.story.counter_hunt as ch

def mon(species, moves):
    sp = get_species_by_name(species)
    lm = [NS(move=get_move_by_name(m)) for m in moves]
    return NS(species=sp, is_egg=False, moves=lm)

NEED = {"Rock", "Ice", "Dragon"}
CASES = [
    ("Slugma knowing Rock Throw (the batch's real case)", mon("Slugma", ["Rock Throw", "Ember"]), True),
    ("Slugma with NO counter move",                        mon("Slugma", ["Ember", "Smog"]), False),
    ("Geodude (TYPE match, control)",                      mon("Geodude", ["Tackle"]), True),
    ("Zigzagoon with a status-only move of a needed type", mon("Zigzagoon", ["Sandstorm"]), False),
]
fail = 0
for label, m, want in CASES:
    pp.get_party = lambda m=m: [m]
    got = ch.party_counter_slot(NEED) is not None
    ok = got == want
    fail += not ok
    print(f"  {'PASS' if ok else 'FAIL'}  {label:<52} recognised={got} (want {want})")
print("\n" + ("ALL PASS" if not fail else f"FAILED {fail}"))
sys.exit(1 if fail else 0)
