# -*- coding: utf-8 -*-
"""PROBE — why `ch24grind` flees for ever: `get_strongest_move_against` returns None on the trainee.

⛔⛔ THIS IS THE **FAILING ARM** OF A FUTURE A/B, AND THAT IS ITS WHOLE JOB. `#24-grindppstall`: the
grind wins ~15 battles, then flees every subsequent encounter for as long as you let it run, gaining
ZERO EXP. This probe pins the mechanism to one predicate and one save, offline, in seconds — so any
proposed fix can be graded against something concrete instead of a re-run and a hope.

THE CHAIN IT MEASURES (`modules/battle_strategies/_util.py:255-266`):
    for learned_move in moves:
        if learned_move.move.name in context.config.battle.banned_moves:  move_strengths.append(-1)
        elif learned_move.pp == 0 (or disabled):                          move_strengths.append(-1)
        else:                                                             <damage rank>
    max_strength = max(move_strengths)
    if max_strength <= 0: return None
⇒ when EVERY move scores -1 the ranker returns **None**, the training strategy cannot pick a move,
and it FLEES. The flee path never triggers `train_team`'s "heal on HP **or PP** dip", so the PP is
never restored and the situation is identical on the next encounter. That is the infinite loop.

⭐ ON THE PINNED STALL SAVE, ALL FOUR OF THE TRAINEE'S MOVES SCORE -1 FOR **TWO DIFFERENT REASONS**:
    Dive        10/10 PP  but BANNED      -> -1      (Dive/Fly/Dig are banned as two-turn/field moves)
    Surf         0/15 PP                  -> -1
    Water Spout  0/5  PP                  -> -1
    Waterfall    0/15 PP                  -> -1
‼ The "15 wins" is just the PP budget: 15 + 15 + 5 = **35 PP** ~= 15 battles x ~2 moves.
‼‼ NOTE ON PP BUDGET, WITH A MECHANISM CORRECTION (2026-09-17): this lineage carries **Water Spout
(5 PP)** where the §Ch24 fixture carries **Ice Beam (10 PP)**, so it has less PP to grind on. ⛔ An
earlier version of this comment said the grind's own level-up learning REPLACED Ice Beam. That is
FALSE — measured: the ancestor `post_training.ss1` already had Water Spout and no Ice Beam, so the
lineages diverged before it, and Water Spout is Wailord's natural L44 move. The bot in fact
⛔ RETRACTED 2026-09-17: this said the bot "DECLINES level-up moves (Wailord crossed L52
Amnesia and L59 Hydro Pump and kept all four)". On the §Ch24 lineage Wailord LOST **Ice Beam**
to Hydro Pump at exactly L59. The policy decides per case, and its type-coverage census ignored
HM moves (`#24-learnhmcoverage`, fixed) — so a Wailord whose only non-HM move was Ice Beam
looked like it lacked Water. The L60 lineage kept its moves because Water Spout is a TM, not an
HM, which made Hydro Pump redundant. Same code, opposite outcome.

⛔ THE PREDICATE IS NOT THE BUG — ITS CONSUMERS ARE. `max_strength <= 0` is reachable three ways:
type immunity (Normal/Fighting into a Ghost — `#24-ghostzerodamage`), PP exhaustion, and a banned
move being the only one left. The consumers then diverge: `_fight_on` falls through to move SLOT 0
(a 0-damage loop) while the training path FLEES (this). ⇒ a fix must make "cannot fight" mean
**heal / rotate / recover**, never "flee and retry for ever" and never "use slot 0 regardless".
⛔ DO NOT "FIX" IT BY UNBANNING DIVE — the ban is deliberate, and unbanning only moves the wall to
the next empty-PP state.

CONTROL (a probe with no control is not a measurement): the SAME computation is run on a healthy mon
from the SAME party. It must NOT return None — otherwise the probe would report "None" for any input
and prove nothing.

    PYTHONUTF8=1 py -3.12 probe_grind_stall_predicate.py
Exit 0 if the control holds (whatever the verdict); 1 if the control fails, because then nothing here
can be trusted.
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False

from modules.pokemon_party import get_party

BAR = "=" * 96
SAVE = "grind_stall_ppzero.ss1"


def score_moves(mon):
    """Reproduce `_util.py:255-262`'s scoring, and say WHY each move scored what it did."""
    banned = context.config.battle.banned_moves
    rows, scores = [], []
    for lm in mon.moves:
        if lm is None:
            continue
        is_banned, zero_pp = lm.move.name in banned, lm.pp == 0
        bad = is_banned or zero_pp
        why = "BANNED" if is_banned else ("0 PP" if zero_pp else "usable")
        rows.append((lm.move.name, lm.pp, lm.total_pp, is_banned, why, -1 if bad else 1))
        scores.append(-1 if bad else 1)
    return rows, (max(scores) if scores else -1)


def main() -> int:
    save = REPO / "tools" / "story-dev" / "saves" / SAVE
    if not save.is_file():
        print(f"save not found: {save}")
        return 1
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(4):
        context.emulator.run_single_frame()

    party = get_party()
    lead = party[0]
    print(BAR)
    print("PROBE — does `get_strongest_move_against` return None on the ch24grind stall state?")
    print(f"  save: {SAVE}   lead: {lead.species.name} L{lead.level} "
          f"{lead.current_hp}/{lead.total_hp}")
    print(BAR)

    rows, top = score_moves(lead)
    for name, pp, total, banned, why, sc in rows:
        print(f"    {name:<13} pp={pp:>2}/{total:<3} banned={str(banned):<5} -> {sc:>2}   ({why})")
    returns_none = top <= 0
    print(f"\n  max(move_strengths) = {top}  =>  max_strength <= 0 ? {returns_none}")
    print(f"  ⇒ get_strongest_move_against returns None: {returns_none}")
    if returns_none:
        print("  ⇒ the training strategy cannot pick a move ⇒ it FLEES ⇒ no heal ⇒ it flees again.")

    # ---- CONTROL ---------------------------------------------------------------------------------
    control = next((m for i, m in enumerate(party)
                    if i != 0 and m is not None and getattr(m, "species", None)), None)
    ok = False
    if control is not None:
        _, ctop = score_moves(control)
        ok = ctop > 0
        print(f"\n  CONTROL  {control.species.name} (same party, healthy): max={ctop} -> "
              f"returns None: {ctop <= 0}   {'PASS' if ok else 'FAIL'}")
        print("    ‼ This must be False. If a healthy mon also returned None the probe would be")
        print("      reporting 'None' for any input and would prove nothing.")

    print(BAR)
    if not ok:
        print("  ⛔ CONTROL FAILED — nothing above can be trusted.")
        print(BAR)
        return 1
    print("  ✅ control holds. This is the FAILING ARM: a fix must make the bot RECOVER from this")
    print("     save (heal, restoring PP) rather than flee. See `#24-grindppstall`.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
