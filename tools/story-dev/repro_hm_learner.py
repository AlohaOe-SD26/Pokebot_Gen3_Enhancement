"""Part A of the HM-learner A/B proof (user report 2026-07-23) — no main loop needed.

From rocksmash_got.ss1:
  1. `hm_learner_slot(HM06)` picks the highest-level COMPATIBLE party mon (the old
     code took the highest level unconditionally — the reported teach loop).
  2. `_hm_hunting_grounds(HM06)` derives, purely from ROM data (encounter tables ×
     TM/HM learnsets), which swept training grasses host a Rock Smash learner.
  3. With the party fault-injected to 'nobody compatible', `hm_learner_slot` returns
     None — proving Segment 10b would now take the hunt path, not the menu loop.
Part B (the live hunt + catch) = `story_harness.py rocksmash_got.ss1 --driver hmtest`.
"""

import pathlib as _pl
import sys

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
_SAVES = _pl.Path(__file__).resolve().parent / "saves"
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

p = load_profile_by_name("repro-ml")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False
context.emulator.load_save_state((_SAVES / "rocksmash_got.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.items import get_item_by_name
from modules.pokemon import Species
from modules.pokemon_party import get_party
from modules.story import early_game

HM06 = get_item_by_name("HM06")

party = [m for m in get_party() if m is not None]
print("party:", [(i, m.species.name, m.level, m.species.can_learn_tm_hm(HM06)) for i, m in enumerate(party)])

# 1. Compatible pick.
slot = early_game.hm_learner_slot(HM06)
assert slot is not None and party[slot].species.can_learn_tm_hm(HM06), "A1 FAILED: incompatible pick"
compat_levels = [m.level for m in party if m.species.can_learn_tm_hm(HM06)]
assert party[slot].level == max(compat_levels), "A1 FAILED: not the highest compatible"
print(f"A1 PASS: picks {party[slot].species.name} L{party[slot].level} (slot {slot})")

# 2. Data-driven hunting grounds.
grounds = early_game._hm_hunting_grounds(HM06)
for g in grounds:
    print(f"   ground: {g[0].name} tile={g[1]} learners={g[2]}")
assert grounds, "A2 FAILED: no grounds derived"
print(f"A2 PASS: {len(grounds)} ground(s), nearest-to-frontier = {grounds[-1][0].name} {grounds[-1][2]}")

# 3. Fault-injected 'nobody compatible' → hunt path (not a menu loop).
party_species = {m.species.name for m in party}
_real = Species.can_learn_tm_hm
Species.can_learn_tm_hm = lambda self, tm_hm: False if self.name in party_species else _real(self, tm_hm)
assert early_game.hm_learner_slot(HM06) is None, "A3 FAILED: patched party still yields a slot"
grounds_b = early_game._hm_hunting_grounds(HM06)
assert grounds_b, "A3 FAILED: no grounds under the fault injection"
print(f"A3 PASS: patched party -> slot None; hunt would target {grounds_b[-1][0].name} {grounds_b[-1][2]}")
Species.can_learn_tm_hm = _real
print("ALL PART-A CHECKS PASS")
