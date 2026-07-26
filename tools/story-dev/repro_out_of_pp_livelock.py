"""REPRO: the training loop must heal when it runs out of PP, not only when HP is low.

REAL INCIDENT (user's hardware, Story (ENDLESS RESET) log 2026-07-26 08:35:20). A fresh
run reached the pre-Pokédex step "training the starter to Lv 8", then:

    3,011 x  [BATTLE] ended (outcome=BattleOutcome.RanAway)
        5 x  Won        1 x Lost
    party=['Treecko L6 21/21']   <- FULL HP in 152 of the state dumps
    map=ROUTE 103(0,18) pos=(5,7)  <- parked on the training tile
    ~2,900,000 frames burned, Treecko never left L6, run ended on the budget.

WHY. HP and PP do not deplete together. A starter that WINS without being hit keeps full
HP while its one attacking move drains. When the last damaging PP goes, the stock
`LevelUpLeadBattleStrategy.decide_turn` finds no usable move and takes the
`lead_cannot_battle_action` branch — default **flee**. Fleeing takes no damage, so HP
stays pinned at 100%, and `train_team`'s heal gate (`_min_battler_hp_pct() <= heal_at`)
can NEVER fire. Livelock: flee -> no XP -> no level -> spin -> flee.

‼ The shiny in that same log is a RED HERRING. It was handled correctly ("shiny Zigzagoon
— no catch possible here, fighting through") and the battle ended `Won` at f1,054,368 —
1.86 MILLION frames before the run died. The reset the user saw was ENDLESS RESET
starting run 2 after the budget expired, not a crash.

WHAT THIS PROVES (pure predicate test, no emulator): `_team_is_out_of_pp` recognises the
exact logged party state, and the fixed heal gate fires on it where the old HP-only gate
did not.

  1. healthy party, PP left            -> not out of PP; old gate and new gate agree
  2. THE REAL STATE: full HP, 0 PP     -> out of PP; OLD gate would NOT heal, NEW one does
  3. status-only moves (Leer) with PP  -> still "out of PP" (0-power moves cannot train)
  4. one mon dry, another with PP      -> NOT out of PP (the team can still fight)
  5. eggs are ignored                  -> an egg's absent moves never mask a dry team
  6. unreadable party                  -> False (fail safe: never an endless heal loop)

Run: py -3.12 tools/story-dev/repro_out_of_pp_livelock.py
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

# ‼ REQUIRED on the Windows console (08-MISTAKES 2026-07-25, the cp1252 class): this file
# prints ‼ and — in its labels, and a bare print of those on a cp1252 console raises
# UnicodeEncodeError, destroying the RESULT of a test that already passed.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

import modules.story.early_game as early_game

failures = []


def check(label, cond):
    print(f"    {'PASS' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


def move(base_power, pp):
    return SimpleNamespace(move=SimpleNamespace(base_power=base_power), pp=pp)


def mon(name, moves, hp_pct=100.0, egg=False):
    return SimpleNamespace(
        name=name, moves=moves, is_egg=egg, current_hp_percentage=hp_pct
    )


def set_party(party):
    early_game.get_party = lambda: list(party)


# The heal gate as it now reads in train_team, and as it read BEFORE the fix.
HEAL_AT = 42.0  # config default hp_threshold 20 + 22, as train_team computes it


def old_gate():
    return early_game._min_battler_hp_pct() <= HEAL_AT


def new_gate():
    return early_game._min_battler_hp_pct() <= HEAL_AT or early_game._team_is_out_of_pp()


print("=" * 78)
print("CASE 1 -- healthy party with PP -> no heal needed, both gates agree")
print("=" * 78)
set_party([mon("TREECKO", [move(40, 30), move(0, 30)])])
print(f"    out_of_pp={early_game._team_is_out_of_pp()} old_gate={old_gate()} new_gate={new_gate()}")
check("not flagged out of PP", early_game._team_is_out_of_pp() is False)
check("neither gate demands a heal", old_gate() is False and new_gate() is False)

print()
print("=" * 78)
print("CASE 2 -- THE REAL LOGGED STATE: Treecko L6, 21/21 HP, Pound at 0 PP")
print("=" * 78)
# Pound 40 power exhausted; Leer 0 power with PP left — exactly what the log shows.
set_party([mon("TREECKO", [move(40, 0), move(0, 24)], hp_pct=100.0)])
o, n = old_gate(), new_gate()
print(f"    out_of_pp={early_game._team_is_out_of_pp()} old_gate={o} new_gate={n}")
check("recognised as out of PP", early_game._team_is_out_of_pp() is True)
check("‼ the OLD HP-only gate would NOT have healed (this is the 3,011-flee livelock)", o is False)
check("the NEW gate heals", n is True)

print()
print("=" * 78)
print("CASE 3 -- only status moves left (Leer with PP) -> still out of PP")
print("=" * 78)
set_party([mon("TREECKO", [move(0, 30), move(0, 30)])])
print(f"    out_of_pp={early_game._team_is_out_of_pp()}")
check(
    "a 0-power move is not a training move — PP on Leer must not count",
    early_game._team_is_out_of_pp() is True,
)

print()
print("=" * 78)
print("CASE 4 -- one mon dry but a team-mate still has PP -> NOT out of PP")
print("=" * 78)
set_party([mon("TREECKO", [move(40, 0)]), mon("ZIGZAGOON", [move(40, 12)])])
print(f"    out_of_pp={early_game._team_is_out_of_pp()}")
check("the team can still fight, so no heal is forced", early_game._team_is_out_of_pp() is False)

print()
print("=" * 78)
print("CASE 5 -- an EGG must not mask a dry team")
print("=" * 78)
set_party([mon("TREECKO", [move(40, 0)]), mon("EGG", [], egg=True)])
print(f"    out_of_pp={early_game._team_is_out_of_pp()}")
check("eggs are skipped, team still reads as dry", early_game._team_is_out_of_pp() is True)

print()
print("=" * 78)
print("CASE 6 -- unreadable party -> False (fail safe, never an endless heal loop)")
print("=" * 78)


def _boom():
    raise RuntimeError("party read failed")


early_game.get_party = _boom
result = early_game._team_is_out_of_pp()
print(f"    out_of_pp={result}")
check("a read error assumes we still have PP", result is False)

print()
print("-" * 78)
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS: running out of PP now triggers the SAME Poké Center heal as low HP")
print("(a heal restores PP too), so the flee->no-XP->spin livelock cannot recur.")
