"""A/B proof for the SWEEPER-SUFFICIENCY GATE (user directive 2026-07-23).

The user's exact observations, tested against the real ROM data via the REAL
`_sufficiency_verdict` + `_prepare_for_fight`:

  A. Combusken L20 (Double Kick) + low team vs Roxanne  -> SUFFICIENT: skip training
     (the observed waste: the old code band-trained the whole team to 13-17).
  B. Torchic L14 (no Fighting move until Combusken@16) vs Roxanne
     -> TOPUP: train JUST Torchic to L16 (the evolution lookahead).
  C. Mudkip L14 (Water Gun) vs Roxanne (ace Nosepass L15) -> SUFFICIENT (>= ace-1).
  D. Poochyena-only L14 vs Roxanne -> None: band prep exactly as today.
  E. Marshtomp L23 (Mud Shot) vs Wattson (ace Manectric L24) -> SUFFICIENT, and the
     Electric-weak Swellow present must NOT be picked (defensive veto).
  F. losses >= 2 -> the gate is bypassed (reactive logic owns the decision).
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.pokemon import get_move_by_name, get_species_by_name

import plugins.custom_modes.story_mode as sm


def mon(species, level, move_names, hp=50):
    sp = get_species_by_name(species)
    return SimpleNamespace(
        species=sp,
        level=level,
        current_hp=hp,
        total_hp=hp,
        is_egg=False,
        # Rough level-scaled stats from base stats — enough for the stat-fit ratio,
        # which only ever compares attack vs special_attack on the SAME mon.
        stats=SimpleNamespace(
            attack=sp.base_stats.attack, special_attack=sp.base_stats.special_attack
        ),
        moves=[SimpleNamespace(move=get_move_by_name(n), pp=10) for n in move_names],
    )


def verdict(party, cfg, losses=0):
    import modules.pokemon_party as pp
    from modules.story import early_game

    orig_gp, orig_bs = pp.get_party, early_game._battler_slots
    pp.get_party = lambda: party
    early_game._battler_slots = lambda: list(range(len(party)))
    try:
        self = SimpleNamespace(
            _defeat_counts={},
            _loss_ko_history={},
            _sweep_score=sm.StoryMode._sweep_score,
            SWEEP_SCORE_FLOOR=sm.StoryMode.SWEEP_SCORE_FLOOR,
        )
        return sm.StoryMode._sufficiency_verdict(self, cfg)
    finally:
        pp.get_party = orig_gp
        early_game._battler_slots = orig_bs


ROXANNE = {"keys": [(0, 0)], "band": (13, 17), "ace_types": ("Rock",), "ace_level": 15}
WATTSON = {"keys": [(0, 0)], "band": (20, 24), "ace_types": ("Electric",), "ace_level": 24}

# A: Combusken L20 sweeps — skip.
v = verdict([mon("Combusken", 20, ["Double Kick", "Ember"]), mon("Poochyena", 9, ["Tackle"])], ROXANNE)
print(f"A Combusken L20 vs Roxanne: {v}")
assert v is not None and v[0] == "sufficient" and v[1] == 0, v

# B: Torchic L14 — evolution lookahead → top up JUST Torchic to 16.
v = verdict([mon("Torchic", 14, ["Ember", "Scratch"]), mon("Poochyena", 12, ["Tackle", "Bite"])], ROXANNE)
print(f"B Torchic L14 vs Roxanne:   {v}")
assert v is not None and v[0] == "topup" and v[1] == 0 and v[2] == 16, v

# C: Mudkip L14 Water Gun — sufficient at ace-1.
v = verdict([mon("Mudkip", 14, ["Water Gun", "Tackle"])], ROXANNE)
print(f"C Mudkip L14 vs Roxanne:    {v}")
assert v is not None and v[0] == "sufficient", v

# D: no sweeper anywhere — band prep (None).
v = verdict([mon("Poochyena", 14, ["Tackle", "Bite"])], ROXANNE)
print(f"D Poochyena-only:           {v}")
assert v is None, v

# E: Marshtomp L23 vs Wattson sufficient; Electric-weak Swellow ignored.
v = verdict(
    [mon("Swellow", 28, ["Wing Attack", "Quick Attack"]), mon("Marshtomp", 23, ["Mud Shot", "Water Gun"])],
    WATTSON,
)
print(f"E Marshtomp+Swellow vs Wattson: {v}")
assert v is not None and v[0] == "sufficient" and v[1] == 1, v

# F: the gate is bypassed once losing — drive the REAL _prepare_for_fight with
#    losses=2 and a sufficient sweeper; training must still be considered (the
#    reactive path owns it), proving the gate only touches proactive attempts.
recorded = {}


def fake_train(target, slots=None, grass=None, heal_center=None):
    recorded["target"] = target
    if False:
        yield


import modules.pokemon_party as pp
from modules.map_data import MapRSE, PokemonCenter
from modules.story import early_game

party = [mon("Combusken", 18, ["Double Kick", "Ember"])]  # L18: EVERY escalation choice exceeds it
orig = (early_game.train_team, pp.get_party, early_game._battler_slots)
early_game.train_team = fake_train
pp.get_party = lambda: party
early_game._battler_slots = lambda: [0]
try:
    self = SimpleNamespace(
        _defeat_counts={(0, 0): 2},
        _loss_ko_history={(0, 0): [(0, 0), (1, 0)]},  # two 0-KO losses -> heavy escalation
        _sweep_score=sm.StoryMode._sweep_score,
        SWEEP_SCORE_FLOOR=sm.StoryMode.SWEEP_SCORE_FLOOR,
        _sufficiency_verdict=lambda cfg: sm.StoryMode._sufficiency_verdict(self, cfg),
        TRAIN_CATCHUP_GAP=getattr(sm.StoryMode, "TRAIN_CATCHUP_GAP", 4),
    )
    cfg = dict(ROXANNE)
    cfg["grass"] = (MapRSE.ROUTE116, (11, 7))
    cfg["heal"] = PokemonCenter.RustboroCity
    gen = sm.StoryMode._prepare_for_fight(self, cfg)
    try:
        while True:
            next(gen)
    except StopIteration:
        pass
    print(f"F losses=2 (0-KO x2):       trained to {recorded.get('target')} (escalation owns it)")
    # The gate must NOT have skipped prep (Combusken L18 would pass sufficiency!) —
    # with losses=2 the reactive escalation owns it: every choice yields target >= 19.
    assert recorded.get("target", 0) >= 19, recorded
finally:
    early_game.train_team, pp.get_party, early_game._battler_slots = orig

print("ALL PASS: skip on a real sweeper, targeted top-up for Torchic, band prep when "
      "no sweeper, defensive veto works, and losses hand control back to the reactive net.")
