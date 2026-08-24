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
# ‼ `#24-brokenrepros` 2026-08-23: this was `pathlib.Path.cwd().parents[1]` — CWD-DEPENDENT, so
# the script passed from `tools/story-dev` and died with `ModuleNotFoundError: modules` from the
# repo root, which is why a doc-level sweep filed it as 'environmental'. ⛔ Line ~78 of THIS FILE
# already resolved the repo the correct, cwd-independent way; only this line did not.
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
import modules.pokemon_party as pp
from modules.pokemon import get_species_by_name, get_move_by_name
import modules.story.counter_hunt as ch

def mon(species, moves):
    sp = get_species_by_name(species)
    lm = [NS(move=get_move_by_name(m)) for m in moves]
    return NS(species=sp, is_egg=False, moves=lm, personality_value=999)

NEED = {"Rock", "Ice", "Dragon"}
CASES = [
    ("Slugma knowing Rock Throw (the batch's real case)", mon("Slugma", ["Rock Throw", "Ember"]), True),
    ("Slugma with NO counter move",                        mon("Slugma", ["Ember", "Smog"]), False),
    ("Geodude (TYPE match, control)",                      mon("Geodude", ["Tackle"]), True),
    ("Zigzagoon with a status-only move of a needed type", mon("Zigzagoon", ["Sandstorm"]), False),
]
# THE PRE-EXISTING-PARTY-MON FENCE (added 2026-08-08 after it cost a whole batch).
# Accepting a MOVE answer removed an ACCIDENTAL protection: while this test matched only the
# mon's own TYPE, a party mon of the needed type would have made `_boss_plan_is_hopeless` return
# False, so no hunt would fire at all. `hopeless` uses the STRICT credible-power test and this
# one is deliberately LENIENT, so a mon carrying a 20-power Rock Smash is "hopeless" to one and
# "success" to the other - and the hunt then "succeeds" instantly on a mon it never caught.
# Measured, batch 20260808-174145: 20 hunts, 13 reported catches, 3 REAL; Marshtomp 6 /
# Castform 3 / Combusken 1 were never hunt targets, and Machop fell from 6-of-8 to 0-of-7.
# Two tests with different thresholds over the same party need an EXPLICIT fence.
print("  -- fence: a mon already in the party when the hunt armed must NOT count --")
_pre = mon("Marshtomp", ["Mud Shot", "Take Down"])   # knows a GROUND move
_pre.personality_value = 12345
pp.get_party = lambda: [_pre]
_fenced = ch.party_counter_slot({"Ground"}, {12345}) is None
_unfenced = ch.party_counter_slot({"Ground"}) is not None
print(f"  {'PASS' if _fenced else 'FAIL'}  excluded by PID -> not counted as this hunt's catch")
print(f"  {'PASS' if _unfenced else 'FAIL'}  without the fence it WOULD count (that is the bug)")
extra_fail = (0 if _fenced else 1) + (0 if _unfenced else 1)
print()

fail = extra_fail
for label, m, want in CASES:
    pp.get_party = lambda m=m: [m]
    got = ch.party_counter_slot(NEED) is not None
    ok = got == want
    fail += not ok
    print(f"  {'PASS' if ok else 'FAIL'}  {label:<52} recognised={got} (want {want})")
print("\n" + ("ALL PASS" if not fail else f"FAILED {fail}"))
# STRUCTURAL: the fence is only as good as what hunt() puts in it. An empty set fences nothing,
# and the snapshot sits behind a bare `except` — so if `get_party` were not in scope there, the
# NameError would be swallowed and the fence would be silently EMPTY while every behavioural
# check above still passed. That very NameError was present in the first draft of this fix.
# Assert the WIRING, not just the predicate.
import pathlib

_src = (pathlib.Path(__file__).resolve().parents[2] / "sandbox-pokebot" / "modules" / "story"
        / "counter_hunt.py").read_text(encoding="utf-8")
print()
print("  -- wiring --")
for _label, _ok in (
    ("hunt() snapshots the party PIDs", "before_party_pids = {" in _src),
    ("it imports get_party EXPLICITLY (not relying on scope)",
     "from modules.pokemon_party import get_party as _gp_snapshot" in _src),
    ("the spin's stop test passes the fence",
     "party_counter_slot(needed_type_names, before_party_pids) is not None" in _src),
    ("the final slot lookup passes it too",
     "slot = party_counter_slot(needed_type_names, before_party_pids)" in _src),
):
    print(f"  {'PASS' if _ok else 'FAIL'}  {_label}")
    fail += 0 if _ok else 1

print("\n" + ("ALL PASS" if not fail else f"FAILED {fail}"))
sys.exit(1 if fail else 0)
