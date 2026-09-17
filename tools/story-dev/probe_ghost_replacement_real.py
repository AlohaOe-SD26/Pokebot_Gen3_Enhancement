# -*- coding: utf-8 -*-
"""⛔ IS THE `#24-ghostreplacement` FIX A NO-OP ON THE **REAL** PARTY? Run the shipped ranker on it.

⛔⛔ WHY THIS EXISTS, AND IT IS A CORRECTION TO MY OWN WORK. On 2026-09-17 I shipped a
`cannot_damage` leading term for `rank_replacement` and marked `#24-ghostreplacement` FIXED and
A/B-PROVEN on the strength of gate #39's case **C8**. C8 pits a mon holding ONLY a Normal move
against a Dark biter — and a Normal move into a Ghost deals literally 0, so `cannot_damage` fires
and the Dark mon wins. The gate is green and the fix is real.

‼‼ **BUT THAT IS NOT THE PARTY.** The real Swellow holds **Aerial Ace — a FLYING move, 1x on a
Ghost** — so its `outgoing` is NOT zero, `cannot_damage` is 0 for it just as it is for Mightyena,
and the key falls straight through to `incoming` exactly as before. Ghost -> Normal is 0x and
Ghost -> Flying is 1x, and `rank_replacement` takes the PRODUCT across the candidate's own types
(`story_mode.py`, the incoming loop), so Swellow scores a PERFECT defensive **0.00** against
Mightyena's 0.50 and is chosen anyway.

⇒ **THE FIX DOES NOT FIX THE CASE IT WAS FILED FOR.** I built the arm out of a synthetic mon
instead of the pinned party — the exact "hand-built probe fixture" trap I had written a warning
about earlier the same day, in the docstring of a different probe. A fixture invented to demonstrate
a defect will demonstrate it; only the real one can tell you whether the defect is still there.

⭐ THIS PROBE THEREFORE USES THE **PINNED PARTY**, LOADED FROM THE SAVE, and the **SHIPPED** pure
function. It is deliberately not a re-implementation: it imports `rank_replacement` and
`_RankingFoe` from production and feeds them the same shapes `choose_new_lead_after_faint` does
(`story_mode.py:318-342`).

‼ ON `damage_of`: production estimates damage with `BattleStrategyUtil.calculate_move_damage_range`,
which needs a live `battle_state` we do not have offline. This probe supplies
`base_power x type-effectiveness x STAB`, and skips `banned_moves` exactly as production does. That
is NOT a damage prediction — but the question here is only ever **"is outgoing zero or non-zero"**
and **"which candidate has the lower `incoming`"**, and both are decided by the type chart, which is
the real one. Any metric that is positive where the real one is positive gives the same verdict.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ghost_replacement_real.py
Exit 0 if the ranker picks a mon that can actually hurt a Ghost; 1 if it still picks one that cannot.
"""
import math
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

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
context.emulation_speed = 0

from modules.pokemon import get_type_by_name
from modules.pokemon_party import get_party
from plugins.custom_modes.story_mode import _RankingFoe, rank_replacement

SAVES = REPO / "tools" / "story-dev" / "saves"
FIXTURE = "post_e4ice_FINAL.ss1"
BAR = "=" * 104


def main() -> int:
    f = SAVES / FIXTURE
    if not f.is_file():
        print(f"  ABORT (instrument) — no fixture {FIXTURE}")
        return 1
    context.emulator.load_save_state(f.read_bytes())
    for _ in range(20):
        context.emulator.run_single_frame()

    ghost = get_type_by_name("Ghost")
    banned = context.config.battle.banned_moves

    party = [m for m in get_party() if m is not None and getattr(m, "species", None) is not None]
    candidates = [(i, m, list(m.species.types)) for i, m in enumerate(party)]
    foes = [_RankingFoe([ghost], object())]

    def damage_of(mon, learned, foe):
        """base power x effectiveness x STAB — enough to settle zero vs non-zero. See the docstring."""
        try:
            if learned.move.name in banned:
                return 0.0
            mult = 1.0
            for t in (ghost,):
                mult *= learned.move.type.get_effectiveness_against(t)
            stab = 1.5 if learned.move.type in mon.species.types else 1.0
            return float(learned.move.base_power) * mult * stab
        except Exception:
            return None

    print(BAR)
    print(f"  #24-ghostreplacement on the REAL party ({FIXTURE}) vs a PURE GHOST")
    print(BAR)
    for i, mon, types in candidates:
        inc = 0.0
        for own in types:
            pass
        mult = 1.0
        for own in types:
            mult *= ghost.get_effectiveness_against(own)
        inc = mult
        best, rows = 0.0, []
        for lm in mon.moves:
            if lm is None or lm.move is None:
                continue
            d = damage_of(mon, lm, None)
            flag = "BANNED" if lm.move.name in banned else f"{d:.0f}"
            rows.append(f"{lm.move.name}({lm.move.type.name[:3]}):{flag}")
            if d:
                best = max(best, d)
        print(f"    slot {i}  {mon.species.name:<11} L{mon.level:<3} incoming={inc:<5} "
              f"best_outgoing={best:<7.0f} {'  '.join(rows)}")

    best_index, report = rank_replacement(candidates, [ghost], foes, damage_of)
    chosen = party[best_index] if best_index is not None else None
    name = chosen.species.name if chosen is not None else "NONE"
    print(f"\n  >>> rank_replacement PICKS slot {best_index} = {name}   key={report.get('key')}")

    # can the chosen mon actually hurt a Ghost?
    can_hurt = False
    if chosen is not None:
        for lm in chosen.moves:
            if lm is None or lm.move is None or lm.move.name in banned:
                continue
            if lm.pp > 0 and ghost.get_effectiveness_against and lm.move.base_power > 0:
                if lm.move.type.get_effectiveness_against(ghost) > 0:
                    can_hurt = True
    print(f"      can it damage a Ghost at all? {can_hurt}")

    print(f"\n{BAR}")
    if name == "Mightyena":
        print("  ✅ the ranker picks the Dark attacker — the fix reaches the REAL party.")
        print(BAR)
        return 0
    print(f"  ⛔⛔ THE `cannot_damage` FIX IS A NO-OP HERE: it still picks **{name}**.")
    print("     Why: `cannot_damage` only separates candidates whose best outgoing is LITERALLY 0.")
    print("     Swellow's Aerial Ace is FLYING (1x on a Ghost), so its outgoing is non-zero, the new")
    print("     term is 0 for BOTH candidates, and `incoming` decides exactly as it did before —")
    print("     and Ghost->Normal is 0x, so the Normal/Flying mon scores a PERFECT 0.00.")
    print("  ⇒ `#24-ghostreplacement` must be REOPENED. The leading term has to express *how long")
    print("     this mon takes to win*, not merely *can it do anything at all*.")
    print("  ‼ And gate #39's C8 must be rebuilt from THIS party, not from a synthetic mon.")
    print(BAR)
    return 1


if __name__ == "__main__":
    sys.exit(main())
