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
