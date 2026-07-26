"""Proof for KI-23 -- the boss-training-mode PLATEAU detector (`_boss_plan_is_hopeless`).

Evidence: a user's overnight ENDLESS RESET session made 198 Winona attempts, lost 41
times, whited out 41 times, and NEVER WON -- the last ~567,000 frames were spent
looping challenge -> lose -> whiteout -> re-enter. Party at the end (Sceptile L42,
Loudred L39, Mightyena L36, Shedinja L29, Ninjask L28) was FAR above Winona's L29-33,
and still lost forever: nothing in the party is super-effective against Flying
(Sceptile/Grass is resisted, Ninjask is itself part-Flying, Shedinja is 1 HP). Boss-
training mode's existing "2 consecutive zero-KO attempts" guard never catches this,
because a strong mon KOs 1-2 of the boss's mons EVERY losing attempt.

WHAT IT PROVES -- pure decision test, no emulator: drives the REAL
`StoryMode._boss_plan_is_hopeless` (unbound, called against a lightweight stand-in
`self` carrying only the instance state the method reads) against constructed
cfg/party/move stand-ins, exactly as `repro_double_battle_swap_loop.py` does for
`LevelUpLeadBattleStrategy`.
  1. WINONA case (flat KO history, no type answer, 6+ losses)  -> HOPELESS,
     needed types include Electric, Rock, Ice.
  2. Same party, IMPROVING KO history                           -> NOT hopeless.
  3. Flat KO history, but the party HOLDS an answer (Electric)  -> NOT hopeless.
  4. Too few losses (< PLATEAU_LOSS_THRESHOLD)                  -> NOT hopeless.

Run: py -3.12 tools/story-dev/repro_boss_plateau.py
"""
import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

import modules.pokemon_party as pokemon_party_module
import modules.story.early_game as early_game
from modules.pokemon import get_type_by_name
import plugins.custom_modes.story_mode as sm


def move(type_name, base_power, pp=10):
    return SimpleNamespace(
        move=SimpleNamespace(type=get_type_by_name(type_name), base_power=base_power), pp=pp
    )


def mon(name, level, moves, egg=False):
    return SimpleNamespace(name=name, level=level, is_egg=egg, moves=moves)


# The Run-1 party shape (KI-23): Grass, Normal, Dark, Bug/Flying -- nothing
# Electric/Rock/Ice, i.e. no super-effective answer to Flying.
NO_ANSWER_PARTY = [
    mon("SCEPTILE", 42, [move("Grass", 90), move("Normal", 40)]),
    mon("LOUDRED", 39, [move("Normal", 90), move("Fighting", 70)]),
    mon("MIGHTYENA", 36, [move("Dark", 80), move("Normal", 60)]),
    mon("NINJASK", 28, [move("Bug", 90), move("Flying", 60)]),
]

# Same party plus a mon carrying a super-effective (Electric) damaging move.
HAS_ANSWER_PARTY = NO_ANSWER_PARTY + [mon("MANECTRIC", 30, [move("Electric", 90)])]


def make_self(defeat_counts, loss_ko_history):
    """A stand-in `self` carrying only what `_boss_plan_is_hopeless` reads off the
    instance (the rest comes from the class or is passed in via `cfg`)."""
    fake_self = SimpleNamespace()
    fake_self.PLATEAU_LOSS_THRESHOLD = sm.StoryMode.PLATEAU_LOSS_THRESHOLD
    # Every class constant the method reads off `self` must be mirrored here. A missing
    # one raises AttributeError inside the method's broad `except`, which returns
    # "not hopeless" — i.e. a typo in this stand-in silently PASSES cases 2/3/4 while
    # making case 1/5 fail for a reason that has nothing to do with the logic.
    fake_self.CREDIBLE_ANSWER_POWER = sm.StoryMode.CREDIBLE_ANSWER_POWER
    fake_self._defeat_counts = defeat_counts
    fake_self._loss_ko_history = loss_ko_history
    return fake_self


def call(fake_self, cfg):
    return sm.StoryMode._boss_plan_is_hopeless(fake_self, cfg)


WINONA_CFG = {"keys": ["winona"], "ace_types": ("Flying",), "name": "Winona"}


def set_party(party):
    party_mock = list(party)
    pokemon_party_module.get_party = lambda: party_mock
    early_game.get_party = lambda: party_mock


def ko_history(seq_start, kos_list):
    return [(seq_start + i, kos) for i, kos in enumerate(kos_list)]


print("=" * 78)
print("CASE 1 -- Winona: flat KO history, no type answer, 6+ losses -> HOPELESS")
print("=" * 78)
set_party(NO_ANSWER_PARTY)
fake_self = make_self(
    defeat_counts={"winona": 6},
    loss_ko_history={"winona": ko_history(1, [1, 2, 1, 2, 1, 2])},
)
hopeless, needed = call(fake_self, WINONA_CFG)
print(f"    -> hopeless={hopeless}, needed={needed}")
assert hopeless is True, f"expected HOPELESS, got {hopeless}"
for t in ("Electric", "Rock", "Ice"):
    assert t in needed, f"expected {t!r} in needed types, got {needed}"
print("PASS: flagged hopeless; needed types include Electric, Rock and Ice.")

print()
print("=" * 78)
print("CASE 2 -- same party, IMPROVING KO history -> NOT hopeless")
print("=" * 78)
set_party(NO_ANSWER_PARTY)
fake_self = make_self(
    defeat_counts={"winona": 6},
    loss_ko_history={"winona": ko_history(1, [0, 1, 1, 2, 3, 4])},
)
hopeless, needed = call(fake_self, WINONA_CFG)
print(f"    -> hopeless={hopeless}, needed={needed}")
assert (hopeless, needed) == (False, []), f"expected (False, []), got {(hopeless, needed)}"
print("PASS: improving trend is not called hopeless -- the escalation path still applies.")

print()
print("=" * 78)
print("CASE 3 -- flat KO history, but the party HAS a super-effective answer -> NOT hopeless")
print("=" * 78)
set_party(HAS_ANSWER_PARTY)
fake_self = make_self(
    defeat_counts={"winona": 6},
    loss_ko_history={"winona": ko_history(1, [1, 2, 1, 2, 1, 2])},
)
hopeless, needed = call(fake_self, WINONA_CFG)
print(f"    -> hopeless={hopeless}, needed={needed}")
assert (hopeless, needed) == (False, []), f"expected (False, []), got {(hopeless, needed)}"
print("PASS: an in-party answer (Manectric/Electric) means the plan is not hopeless.")

print()
print("=" * 78)
print("CASE 4 -- too few losses (< PLATEAU_LOSS_THRESHOLD) -> NOT hopeless")
print("=" * 78)
set_party(NO_ANSWER_PARTY)
fake_self = make_self(
    defeat_counts={"winona": sm.StoryMode.PLATEAU_LOSS_THRESHOLD - 1},
    loss_ko_history={"winona": ko_history(1, [1, 2, 1, 2, 1, 2])},
)
hopeless, needed = call(fake_self, WINONA_CFG)
print(f"    -> hopeless={hopeless}, needed={needed}")
assert (hopeless, needed) == (False, []), f"expected (False, []), got {(hopeless, needed)}"
print("PASS: below the loss threshold, never called hopeless.")

print()
print("-" * 78)
print("ALL PASS: _boss_plan_is_hopeless separates 'no type answer' (Winona, KI-23) from")
print("'improving' and 'has an answer' -- and never fires on too little history.")

print()
print("=" * 78)
print("CASE 5 -- NORMAN, the REAL night5 run3 party -> HOPELESS (power-blind regression)")
print("=" * 78)
# ‼ NOT constructed: this is the exact party and moveset logged by night5 run3
# (tools/story-dev/night5/run3.log), which made 27 losing Norman attempts across
# f1,406,000 -> f1,914,000 with KOs flat at 1-2 of 4 the whole time.
#
# Norman's team is entirely NORMAL (Spinda/Vigoroth/Linoone/Slaking), and the only
# type super-effective against Normal is FIGHTING. The party's sole Fighting move was
# ROCK SMASH -- the 20-base-power HM the bot is REQUIRED to carry to progress. The
# original `eff >= 2.0` test accepted it as "an answer", so the plateau detector was
# structurally unable to fire on the boss most likely to plateau.
NORMAN_RUN3_PARTY = [
    mon("MARSHTOMP", 34, [move("Normal", 90), move("Fighting", 20),   # Take Down, ROCK SMASH
                          move("Ground", 20), move("Water", 40)]),    # Mud-slap, Water Gun
    mon("MIGHTYENA", 33, [move("Normal", 35), move("Normal", 0),
                          move("Normal", 0), move("Dark", 60)]),
    mon("SHROOMISH", 15, [move("Grass", 20), move("Normal", 35),
                          move("Grass", 0), move("Grass", 0)]),
    mon("SWELLOW", 30, [move("Flying", 35), move("Normal", 0),
                        move("Normal", 0), move("Normal", 40)]),
]
NORMAN_CFG = {"keys": ["norman"], "ace_types": ("Normal",), "name": "Norman"}

set_party(NORMAN_RUN3_PARTY)
fake_self = make_self(
    defeat_counts={"norman": 27},
    # The real KO trace from the log, attempts 1-6: 1,1,2,2,2,2 -- flat, never improving.
    loss_ko_history={"norman": ko_history(1, [1, 1, 2, 2, 2, 2])},
)
hopeless, needed = call(fake_self, NORMAN_CFG)
print(f"    -> hopeless={hopeless}, needed={needed}")
assert hopeless is True, (
    f"expected HOPELESS, got {hopeless} -- a 20-power HM (Rock Smash) is being "
    "accepted as an answer to Norman again; the detector is power-blind."
)
assert "Fighting" in needed, f"expected 'Fighting' in needed types, got {needed}"
print("PASS: Rock Smash (20 power) no longer vetoes the diagnosis; Fighting is named.")

print()
print("=" * 78)
print("CASE 6 -- a WEAK BUT REAL answer still counts (guards over-correction)")
print("=" * 78)
# Combusken's Double Kick: 30 base power, Fighting, STAB -> 30 x 2.0 x 1.5 = 90.
# This is the move that beat Norman organically (handoff 2026-07-24), so the power
# floor must NOT reject it. Without a real `species`, STAB cannot be read, so this
# case gives the mon one to prove the STAB path is what carries it over the line.
combusken = mon("COMBUSKEN", 32, [move("Fighting", 30), move("Fire", 40)])
combusken.species = SimpleNamespace(types=(get_type_by_name("Fire"), get_type_by_name("Fighting")))
set_party([combusken] + NORMAN_RUN3_PARTY[1:])
fake_self = make_self(
    defeat_counts={"norman": 27},
    loss_ko_history={"norman": ko_history(1, [1, 1, 2, 2, 2, 2])},
)
hopeless, needed = call(fake_self, NORMAN_CFG)
print(f"    -> hopeless={hopeless}, needed={needed}")
assert (hopeless, needed) == (False, []), (
    f"expected NOT hopeless, got {(hopeless, needed)} -- the power floor is too high "
    "and is rejecting Double Kick, a genuine Norman answer."
)
print("PASS: STAB Double Kick (30 x 2.0 x 1.5 = 90) still counts as a real answer.")

print()
print("-" * 78)
print("ALL PASS (cases 5-6): the answer test is POWER-WEIGHTED -- a 20-power HM no")
print("longer disables the plateau detector, and a weak-but-real STAB answer survives.")

print()
print("=" * 78)
print("CASE 7 -- STAB Rock Smash on COMBUSKEN is NOT a credible answer (real run05)")
print("=" * 78)
# ‼ NOT constructed. Batch 20260726-052205 run05 took **21 Norman losses** with this
# party and the guard never fired. Combusken is Fire/FIGHTING, so its ROCK SMASH gets
# STAB: 20 x 2.0 x 1.5 = exactly 60, which passed the original threshold on the
# boundary. The two real data points bracket the answer: 60 loses 21 times, 90
# (Double Kick, CASE 6) wins. This case pins the threshold between them so it can
# never drift back down.
combusken_rs = mon("COMBUSKEN", 31, [
    move("Normal", 40),      # Scratch
    move("Flying", 35),      # Peck
    move("Fighting", 20),    # ROCK SMASH -- the only Fighting move it owns
    move("Fire", 40),        # Ember
])
combusken_rs.species = SimpleNamespace(
    types=(get_type_by_name("Fire"), get_type_by_name("Fighting"))
)
set_party([combusken_rs] + NORMAN_RUN3_PARTY[1:])
fake_self = make_self(
    defeat_counts={"norman": 21},
    loss_ko_history={"norman": ko_history(1, [1, 2, 2, 1, 2, 2])},
)
hopeless, needed = call(fake_self, NORMAN_CFG)
print(f"    -> hopeless={hopeless}, needed={needed}")
assert hopeless is True, (
    f"expected HOPELESS, got {hopeless} -- a STAB 20-power HM (Rock Smash on a "
    "Fighting-type carrier) scores exactly 60 and is being accepted as an answer "
    "again; run05 lost 21 times with precisely this party."
)
assert "Fighting" in needed, f"expected 'Fighting' in needed types, got {needed}"
print("PASS: STAB Rock Smash (60) is below the floor; Double Kick (90, CASE 6) stays above.")

print()
print("-" * 78)
print("ALL PASS (case 7): the power floor is calibrated by two REAL runs -- 60 loses 21")
print("times, 90 wins -- not by taste.")
