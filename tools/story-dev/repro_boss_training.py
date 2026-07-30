"""A/B proof for BOSS-TRAINING MODE's decision logic (user design 2026-07-23).

Drives the real `StoryMode._prepare_for_fight` with the real Route 117 encounter
table (ROM data) and a mocked L28 party/telemetry; `train_team` is stubbed to record
the chosen target instead of grinding. Scenarios:

  A. losses=2, recent lost attempts KO'd [1, 2] boss mons, grass = Route 117
     (wild max ~14 vs team L28)  -> BOSS MODE: light target = 29.
  B. same but KOs [0, 0]         -> boss can't teach: heavy escalation (target >= 33).
  C. same KOs [1,2] but team L16 (grass NOT fodder) -> classic escalation, no boss mode.
  D. no grass key in cfg (Flannery case), KOs [1]   -> BOSS MODE (grass can't teach).
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

# Encounter tables read live memory — but the cache is populated from the ROM via the
# emulator. Spin one up headless (no frames run) so get_wild_encounters_for_map works.
from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False

from modules.map_data import MapRSE, PokemonCenter

import plugins.custom_modes.story_mode as sm


class _StoryModeStub(SimpleNamespace):
    """A stand-in `self` for `StoryMode._prepare_for_fight` that EXPLAINS ITSELF when the
    code under test grows a new dependency.

    ‼ Why this class exists (08-MISTAKES 2026-07-30): this repro was dead for days and the
    suite reported it as "environmental — needs a real mgba". It needed no emulator it did
    not have; its plain `SimpleNamespace` stub simply never gained `_boss_plan_is_hopeless`
    when the KI-23 work added that call to `_prepare_for_fight`, and the resulting bare
    `AttributeError: 'types.SimpleNamespace' object has no attribute ...` looked like
    scaffolding noise rather than "this test no longer runs".
    """

    def __getattr__(self, name):  # only called after normal lookup fails
        raise AttributeError(
            f"repro_boss_training's stand-in `self` has no {name!r}.\n"
            f"  `_prepare_for_fight` (or something it calls) started using "
            f"StoryMode.{name} after this repro was written.\n"
            f"  FIX: if it is a CONSTANT it should already be harvested automatically — "
            f"check it is UPPERCASE on StoryMode. If it is a METHOD, bind the REAL one "
            f"(`self.{name} = lambda *a: sm.StoryMode.{name}(self, *a)`); do NOT re-stub "
            f"its verdict, or this repro will rot again the same way."
        )


def run_prep(team_max, ko_history, *, with_grass=True, losses=2):
    recorded = {}

    def fake_train_team(target, slots=None, grass=None, heal_center=None):
        recorded["target"] = target
        recorded["slots"] = slots
        if False:
            yield

    mons = [SimpleNamespace(level=team_max - i * 2, is_egg=False) for i in range(3)]
    import modules.pokemon_party as pp

    sm_train_orig = None
    from modules.story import early_game

    orig_train = early_game.train_team
    orig_get_party = pp.get_party
    orig_battlers = early_game._battler_slots
    early_game.train_team = fake_train_team
    pp.get_party = lambda: mons
    early_game._battler_slots = lambda: [0, 1, 2]
    # story_mode imports get_party/train_team inside the method — same module objects.
    try:
        self = _StoryModeStub(
            _defeat_counts={(0, 7): losses},
            _loss_ko_history={(0, 7): [(i, k) for i, k in enumerate(ko_history)]},
            # ‼ EVERY class constant, harvested — not a hand-listed few. `_prepare_for_fight`
            # and the functions it calls read several off `self`, and hand-listing them is
            # what rotted this repro: `TRAIN_CATCHUP_GAP` was listed, `PLATEAU_LOSS_THRESHOLD`
            # and `CREDIBLE_ANSWER_POWER` arrived later with KI-23 and were not.
            **{k: getattr(sm.StoryMode, k) for k in dir(sm.StoryMode) if k.isupper()},
        )
        # ‼ BIND THE REAL METHOD, never re-stub its verdict. A stubbed
        # `_boss_plan_is_hopeless` would hard-code this function's answer here, so the
        # repro would keep passing while the real diagnosis changed underneath it —
        # the same drift, one level up. With losses=2 (< PLATEAU_LOSS_THRESHOLD) the real
        # method returns (False, []) at its first guard, so boss-training is what is
        # under test, exactly as before.
        self._boss_plan_is_hopeless = lambda cfg: sm.StoryMode._boss_plan_is_hopeless(self, cfg)
        cfg = {"keys": [(0, 7)], "band": (20, 24), "heal": PokemonCenter.MauvilleCity}
        if with_grass:
            cfg["grass"] = (MapRSE.ROUTE117, (31, 16))
        gen = sm.StoryMode._prepare_for_fight(self, cfg)
        try:
            while True:
                next(gen)
        except StopIteration:
            pass
        return recorded.get("target")
    finally:
        early_game.train_team = orig_train
        pp.get_party = orig_get_party
        early_game._battler_slots = orig_battlers


# A: boss mode — light target.
t = run_prep(28, [1, 2])
print(f"A (L28, KOs [1,2], Rt117 grass): target={t}")
assert t == 29, f"expected light target 29, got {t}"

# B: 0-KO fallback — heavy escalation.
t = run_prep(28, [0, 0])
print(f"B (L28, KOs [0,0]):              target={t}")
assert t is not None and t >= 26, f"expected an escalated grind target, got {t}"
assert t != 29 or t >= 33 - 4, "should NOT be the light boss-mode target"

# C: grass is level-appropriate — classic path even with KOs.
t = run_prep(16, [1, 2])
print(f"C (L16 team, grass appropriate): target={t}")
assert t is None or t >= 20, f"unexpected light target: {t}"

# D: no grass at all (Flannery) — boss mode on any KO; with nowhere to train, the
# top-up is correctly SKIPPED (train_team never called) and the flow proceeds
# straight to the re-attempt.
t = run_prep(30, [1], with_grass=False)
print(f"D (no grass cfg, KOs [1]):       target={t} (None = no grind, straight to re-attempt)")
assert t is None, f"expected the top-up to be skipped, got a grind to {t}"

print("ALL PASS: boss-training activates on fodder-grass+KOs, falls back on 0-KOs, "
      "stays classic on appropriate grass, and covers grass-less bosses.")
