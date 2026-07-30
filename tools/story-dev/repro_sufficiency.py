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

# ‼ A HEADLESS EMULATOR IS REQUIRED, even though this repro runs no frames
# (08-MISTAKES 2026-07-30). `set_rom()` alone is not enough: the evolution lookahead's
# frame-cost gate prices the grind against the target map's WILD ENCOUNTER TABLE, and
# `get_wild_encounters_for_map` populates its cache through the emulator. Without one,
# `_wild_land_max` returns None -> `est_frames` is None -> the gate REJECTS the plan
# ("estimated UNKNOWN frames"), so case B silently returned None. The verdict logic was
# never wrong; the fixture just could not read the ROM data production always has.
# Same two lines as repro_boss_training.py, and for the same reason.
from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False

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
        # ‼ REQUIRED by the evolution lookahead's frame-cost gate, which calls
        # `estimate_frames_to_level(mon, ...)` — that reads `total_exp` off the mon.
        # Missing here, it raised inside the lookahead's `except Exception: pass`, so the
        # verdict silently degraded to None and case B failed with no diagnostic at all.
        # Real growth curve, not a placeholder, so the estimate is the production one.
        total_exp=sp.level_up_type.get_experience_needed_for_level(level),
        # Rough level-scaled stats from base stats — enough for the stat-fit ratio,
        # which only ever compares attack vs special_attack on the SAME mon.
        stats=SimpleNamespace(
            attack=sp.base_stats.attack, special_attack=sp.base_stats.special_attack
        ),
        moves=[SimpleNamespace(move=get_move_by_name(n), pp=10) for n in move_names],
    )


class _StoryModeStub(SimpleNamespace):
    """A stand-in `self` for `StoryMode._sufficiency_verdict` that EXPLAINS ITSELF when
    the code under test grows a new dependency, instead of vanishing into one of that
    function's broad `except Exception` handlers. See 08-MISTAKES 2026-07-30.
    """

    def __getattr__(self, name):  # only called after normal lookup fails
        raise AttributeError(
            f"repro_sufficiency's stand-in `self` has no {name!r}.\n"
            f"  `_sufficiency_verdict` (or something it calls) started using "
            f"StoryMode.{name} after this repro was written.\n"
            f"  FIX: CONSTANTS are harvested automatically — check it is UPPERCASE on "
            f"StoryMode. For a METHOD, bind the REAL one; do not re-stub its verdict.\n"
            f"  ‼ Several branches in `_sufficiency_verdict` swallow exceptions, so a "
            f"missing attribute shows up as a silently WRONG verdict, not a crash."
        )


def verdict(party, cfg, losses=0):
    import modules.pokemon_party as pp
    from modules.story import early_game

    orig_gp, orig_bs = pp.get_party, early_game._battler_slots
    pp.get_party = lambda: party
    early_game._battler_slots = lambda: list(range(len(party)))
    try:
        self = _StoryModeStub(
            _defeat_counts={},
            _loss_ko_history={},
            _sweep_score=sm.StoryMode._sweep_score,
            # ‼ EVERY class constant, harvested — not a hand-listed few (08-MISTAKES
            # 2026-07-30). Only `SWEEP_SCORE_FLOOR` was listed here; when the evolution
            # lookahead gained its frame-cost gate it began reading
            # `self.MAX_PREP_TRAINING_FRAMES`, the stub raised AttributeError, and the
            # lookahead's own `except Exception: pass` SWALLOWED it — so case B degraded
            # to `None` with no diagnostic, and the failure was filed for days as
            # "environmental — needs a real mgba". Every step of that lookahead actually
            # passes on real data (sweep score 90 >= 80, estimate 24,361 <= 250,000).
            **{k: getattr(sm.StoryMode, k) for k in dir(sm.StoryMode) if k.isupper()},
        )
        return sm.StoryMode._sufficiency_verdict(self, cfg)
    finally:
        pp.get_party = orig_gp
        early_game._battler_slots = orig_bs


# ‼ `grass` IS NOT OPTIONAL IN THESE FIXTURES (08-MISTAKES 2026-07-30). It was missing
# here, and once the evolution lookahead gained its FRAME-COST GATE, that gate reads
# `cfg["grass"]` to price the grind and REJECTS the plan when it cannot price it
# (`est_frames is None` -> fail safe). With no grass key, case B could only ever return
# None — the repro was asserting against a cfg the real gym config never has. Copied
# verbatim from the production configs (story_mode.py:2151, `RUSTBORO_TRAINING_GRASS`
# = early_game.py:1648) so the fixture cannot drift from what actually ships.
from modules.map_data import MapRSE as _MapRSE

ROXANNE = {
    "keys": [(0, 0)], "band": (13, 17), "ace_types": ("Rock",), "ace_level": 15,
    "grass": (_MapRSE.ROUTE116, (11, 7)),   # RUSTBORO_TRAINING_GRASS
}
WATTSON = {
    "keys": [(0, 0)], "band": (20, 24), "ace_types": ("Electric",), "ace_level": 24,
    "grass": (_MapRSE.ROUTE117, (31, 16)),  # ROUTE117_TRAINING_GRASS (Ch9 Wattson prep)
}

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
    self = _StoryModeStub(
        _defeat_counts={(0, 0): 2},
        _loss_ko_history={(0, 0): [(0, 0), (1, 0)]},  # two 0-KO losses -> heavy escalation
        _sweep_score=sm.StoryMode._sweep_score,
        # Same harvest as the `verdict()` stub above — hand-listing constants is what
        # rotted this file. `_prepare_for_fight` reads FODDER_LEVEL_GAP,
        # PLATEAU_LOSS_THRESHOLD, MAX_PREP_TRAINING_FRAMES and more off `self`.
        **{k: getattr(sm.StoryMode, k) for k in dir(sm.StoryMode) if k.isupper()},
    )
    # Bind the REAL methods `_prepare_for_fight` calls, so this exercises the real
    # decisions rather than a second copy of them (see the `verdict()` stub's note).
    self._sufficiency_verdict = lambda cfg: sm.StoryMode._sufficiency_verdict(self, cfg)
    self._boss_plan_is_hopeless = lambda cfg: sm.StoryMode._boss_plan_is_hopeless(self, cfg)
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
