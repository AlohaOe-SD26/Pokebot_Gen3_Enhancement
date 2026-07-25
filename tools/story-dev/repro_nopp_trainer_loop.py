"""A/B proof for the NO-PP TRAINER-LOOP fix (batch2/treecko.log, f1.2M-ish: 15,000
frames of no progress inside an unfleeable trainer battle —
`instr=BattleScript_SelectingMoveWithNoPP`, `bt="There's no PP left for this move"`,
`scripts=['EventScript_DoTrainerBattle']`).

ROOT CAUSE: `LevelUpTravelBattleStrategy.decide_turn` (plugins/custom_modes/story_mode.py),
the trainer-battle branch. When `get_strongest_move_against` returns None, the old code
walked `active.moves` looking for `util.move_is_usable(learned)`; if NONE matched it fell
straight to `return TurnAction.use_move(0)` on the theory that "nothing usable -> the game
uses Struggle". That's wrong: `move_is_usable` is STRICTER than "has PP" (it also rejects
zero-power/status moves and banned moves), so a mon can fail every usability check while
STILL holding a move with PP > 0 (e.g. a status move). Gen 3 does not substitute Struggle
for a hand-picked 0-PP move in that case — it prints "There's no PP left for this move!"
and bounces back to move selection. In an unfleeable trainer battle that is an infinite
loop. Struggle is only auto-used when EVERY move is truly at 0 PP.

THE FIX (already applied, sandbox-pokebot/plugins/custom_modes/story_mode.py:193-208):
adds a second pass, before the `use_move(0)` fallback, that returns the first move slot
with `pp > 0` even if it fails `move_is_usable`.

WHAT THIS SCRIPT PROVES
  1. THE DECISION, A/B. A battler whose moves ALL fail `move_is_usable` (all zero-power
     or banned) but where slot 1 has pp > 0 (a status move with PP left):
       BEFORE (second pass neutralized in THIS SCRIPT ONLY, production code untouched)
             -> falls through to use_move(0), a 0-PP move -> the "no PP" loop.
       AFTER  (real code, unmodified)
             -> returns the first slot with pp > 0 (not the blind slot-0 fallback).
     The "before" run calls the REAL, UNMODIFIED `decide_turn` — we neutralize only the
     DATA the second pass sees (by making `active.moves` return items only on its first
     iteration, mimicking "this loop doesn't run"), never the code itself.
  2. The TRUE all-zero-PP case (every move pp == 0) still falls through to
     `use_move(0)` on the real, unmodified code path -- so Struggle can still fire.
  3. No regression on the normal paths:
       a) a strongest move exists -> still returned directly (PP-only pass never runs).
       b) a `move_is_usable` move exists -> still preferred over the PP-only pass
          (ordering: usability beats "has PP alone").
  4. Reports on the None-padding / index-0-safety questions asked by the reviewer.

Run: py -3.12 tools/story-dev/repro_nopp_trainer_loop.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

# LevelUpLeadBattleStrategy.__init__ (the parent class) calls get_party() to record
# the pre-battle lead index, which needs a real emulator + loaded save (state_cache
# reads context.emulator.get_frame_count()). No battle-state fault injection needed
# for THAT -- any loaded save works, we never touch its party data below.
p = load_profile_by_name("repro-fresh")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)
from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False
context.emulator.load_save_state((REPO / "tools/story-dev/saves/norman_done.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.pokemon import LearnedMove, get_move_by_name
from modules.battle_strategies import BattleStrategyUtil, TurnAction
import plugins.custom_modes.story_mode as sm

STRATEGY = sm.LevelUpTravelBattleStrategy()

# ---------------------------------------------------------------------------
# Fake battle-state plumbing. Only the attributes decide_turn/util actually
# touch are implemented; everything else intentionally raises if accessed so
# the test fails loudly instead of silently faking behaviour we didn't mean to.
# ---------------------------------------------------------------------------


class CountingMoves:
    """Wraps a real moves list. First `iter()` call (the util.move_is_usable
    pass) yields the real list; every call after that (the PP-only second
    pass) yields an EMPTY iterator -- i.e. "that loop doesn't run". This lets
    us drive the REAL, unmodified decide_turn and reproduce the pre-fix
    behaviour by starving the second pass of data, without touching
    story_mode.py or reimplementing its logic."""

    def __init__(self, moves, neutralize_second_pass: bool):
        self._moves = list(moves)
        self._neutralize = neutralize_second_pass
        self._iter_count = 0

    def __iter__(self):
        self._iter_count += 1
        if self._neutralize and self._iter_count > 1:
            return iter([])
        return iter(self._moves)

    def __len__(self):
        return len(self._moves)


class FakeBattler:
    def __init__(self, moves):
        self.moves = moves


class FakeSide:
    def __init__(self, active):
        self.active_battler = active


class FakeBattleState:
    def __init__(self, active, opponent_active):
        self.is_trainer_battle = True
        self.own_side = FakeSide(active)
        self.opponent = FakeSide(opponent_active)


def lm(move_name, pp):
    return LearnedMove.create(get_move_by_name(move_name), remaining_pp=pp)


def outcome_str(result):
    action, arg = result
    return f"{action.name}({arg})"


results = {}

print("=" * 78)
print("1) THE DECISION, A/B")
print("-" * 78)

# All 4 moves fail move_is_usable: Growl/Leer (0 base power, status) with PP left,
# plus two banned/zero-power fillers. Slot 1 (Leer) has pp > 0.
moves_real = [
    lm("Growl", 0),   # status, 0 PP left  -> fails move_is_usable (pp==0)
    lm("Leer", 10),   # status, PP LEFT    -> fails move_is_usable (base_power==0), but pp>0
    lm("Tail Whip", 0),  # status, 0 PP    -> fails move_is_usable
    lm("Harden", 0),  # status, 0 PP       -> fails move_is_usable
]
opponent = FakeBattler([lm("Tackle", 35)])

# Fault injection shared by BEFORE and AFTER: no strongest move found (this is
# the precondition for reaching the branch under test in the real code).
_orig_get_strongest = BattleStrategyUtil.get_strongest_move_against
BattleStrategyUtil.get_strongest_move_against = lambda self, pokemon, opp: None

try:
    # BEFORE: real decide_turn, but active.moves starves the 2nd (PP-only) pass.
    active_before = FakeBattler(CountingMoves(moves_real, neutralize_second_pass=True))
    battle_before = FakeBattleState(active_before, opponent)
    before = STRATEGY.decide_turn(battle_before)
    print(f"BEFORE (2nd pass neutralized): {outcome_str(before)}  "
          f"-> slot {before[1]} pp={moves_real[before[1]].pp} "
          f"({'0-PP move selected -> BUG' if moves_real[before[1]].pp == 0 else 'has PP'})")

    # AFTER: real decide_turn, real (un-neutralized) moves list.
    active_after = FakeBattler(CountingMoves(moves_real, neutralize_second_pass=False))
    battle_after = FakeBattleState(active_after, opponent)
    after = STRATEGY.decide_turn(battle_after)
    print(f"AFTER  (real code, real data):  {outcome_str(after)}  "
          f"-> slot {after[1]} pp={moves_real[after[1]].pp} "
          f"({'has PP -> FIXED' if moves_real[after[1]].pp > 0 else '0-PP move selected -> BUG'})")

    assert before == (TurnAction.UseMove, 0), before
    assert moves_real[before[1]].pp == 0, "BEFORE must reproduce the 0-PP bug"
    assert after == (TurnAction.UseMove, 1), after
    assert moves_real[after[1]].pp > 0, "AFTER must pick a move with PP"
    print("   PASS: unmodified decide_turn picks the 0-PP slot 0 when the 2nd pass is "
          "starved of data, and picks the PP-holding slot 1 with real data -> the fix is "
          "the difference, not a reimplementation.")
finally:
    BattleStrategyUtil.get_strongest_move_against = _orig_get_strongest

print("\n" + "=" * 78)
print("2) TRUE ALL-ZERO-PP CASE STILL FALLS THROUGH TO use_move(0) (Struggle)")
print("-" * 78)
moves_allzero = [
    lm("Growl", 0),
    lm("Leer", 0),
    lm("Tail Whip", 0),
    lm("Harden", 0),
]
BattleStrategyUtil.get_strongest_move_against = lambda self, pokemon, opp: None
try:
    active = FakeBattler(moves_allzero)  # real list, both passes see it -- no neutering
    battle = FakeBattleState(active, opponent)
    result = STRATEGY.decide_turn(battle)
    print(f"all-zero-PP: {outcome_str(result)} "
          f"(pp of every move: {[m.pp for m in moves_allzero]})")
    assert result == (TurnAction.UseMove, 0), result
    print("   PASS: real code (2nd pass included, un-neutered) still falls through to "
          "use_move(0) when every move is genuinely at 0 PP -> Struggle path unchanged.")
finally:
    BattleStrategyUtil.get_strongest_move_against = _orig_get_strongest

print("\n" + "=" * 78)
print("3) NO REGRESSION ON NORMAL PATHS")
print("-" * 78)

# 3a) a strongest move exists -> returned directly, PP-only pass never consulted.
moves_3a = [lm("Tackle", 35), lm("Growl", 40)]
BattleStrategyUtil.get_strongest_move_against = lambda self, pokemon, opp: 0
try:
    active = FakeBattler(moves_3a)
    battle = FakeBattleState(active, opponent)
    result = STRATEGY.decide_turn(battle)
    print(f"3a) strongest move present: {outcome_str(result)}")
    assert result == (TurnAction.UseMove, 0), result
    print("    PASS: strongest-move path unchanged (fix never touched).")
finally:
    BattleStrategyUtil.get_strongest_move_against = _orig_get_strongest

# 3b) a move_is_usable move exists (slot 0, has power + PP) AND a PP-only-eligible
# status move with PP also exists (slot 1) -- usability pass must win (ordering).
moves_3b = [lm("Tackle", 35), lm("Leer", 10)]
BattleStrategyUtil.get_strongest_move_against = lambda self, pokemon, opp: None
try:
    active = FakeBattler(moves_3b)  # real list, no neutering -- exercise real ordering
    battle = FakeBattleState(active, opponent)
    result = STRATEGY.decide_turn(battle)
    print(f"3b) usable move (slot 0) + PP-only move (slot 1): {outcome_str(result)}")
    assert result == (TurnAction.UseMove, 0), (
        "usability pass must be preferred over the PP-only pass", result
    )
    print("    PASS: the usable move (slot 0) is chosen; the PP-only pass is a LAST "
          "resort, it does not preempt move_is_usable.")
finally:
    BattleStrategyUtil.get_strongest_move_against = _orig_get_strongest

print("\n" + "=" * 78)
print("4) None-padding / use_move(0) safety review")
print("-" * 78)
print("""
Checked modules/battle_state.py BattlePokemon.moves (this is the type of
`battle_state.own_side.active_battler` -- the object decide_turn actually
iterates in a live battle, NOT the party-level Pokemon.moves):

    for index in range(4):
        move_index = unpack_uint16(...)
        if move_index == 0:
            continue                      # <- empty slot SKIPPED, not padded
        result.append(LearnedMove(...))
    return result

So for the in-battle active battler, .moves NEVER contains None -- empty move
slots are omitted entirely, they don't appear as list items. `learned.pp`
cannot throw on a None here, and the `learned is not None` checks in
decide_turn's loops are defensive-but-dead for this call site.

(By contrast, the OUT-OF-BATTLE `Pokemon.moves` property in modules/pokemon.py
DOES return a fixed 4-tuple that CAN contain None for empty slots -- that
matters for the OTHER pp/move_is_usable call sites in this file that operate
on party Pokemon, e.g. choose_new_lead_after_faint's `mon.moves` scan, which
already guards with `learned is None` checks. Not a bug, just worth flagging
that the two `.moves` shapes differ and callers must not assume the party-mon
shape when adding new active-battler code.)

Is use_move(0) safe when slot 0 is "empty"? Every Pokemon knows at least one
move (Gen 3 never allows an empty moveset), and BattlePokemon.moves only ever
omits KNOWN-empty slots, so if the active battler exists, index 0 of its
.moves list is always a real, learned move. No unguarded crash path found.
""")

print("=" * 78)
print("ALL PASS")
