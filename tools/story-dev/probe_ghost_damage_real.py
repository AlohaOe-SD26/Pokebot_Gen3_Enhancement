# -*- coding: utf-8 -*-
"""⭐ THE MEASUREMENT `#24-ghostreplacement` IS BLOCKED ON: real damage vs a REAL Ghost, from a REAL battle.

⛔⛔ WHY NOTHING CHEAPER WOULD DO. The faint chooser's leading term has to be chosen from numbers,
and two attempts have already failed for lack of them:
  * `cannot_damage` (shipped, then RETRACTED) separates only candidates whose damage is LITERALLY
    zero. Measured on the real party it is a **no-op** — the ranker still picks an L19 Zigzagoon,
    because Swellow's Aerial Ace is Flying (1x on a Ghost) and Zigzagoon carries Surf.
  * `ko_turns = ceil(foe_hp / outgoing)` — the obvious replacement — was **refuted before shipping**:
    a refuter dry-ran it against gate #39's own rows and C2 goes red. And at L75 against her L48-51
    team it may SATURATE at 1 for both Mightyena and Swellow, falling through to `incoming` and
    re-picking the wrong mon. *A term that saturates stops discriminating exactly where the real
    party lives.*
⇒ the only way to choose is to know the actual damage figures and the actual foe HP.

⭐ THE SOURCE OF TRUTH IS AN IN-BATTLE SAVE, AND WE HAVE ONE. `in_phoebe_battle_L75.ss1` was
captured by `--driver ch24phoebe` during the Phoebe fight. ‼ It is captured at the fight's END
rather than its start — see the harness note below — but that does not matter here:
`calculate_move_damage_range` computes from LEVEL, STATS and TYPES, not from the foe's current HP.
What the fixture gives us is a live `battle_state` with a REAL `Dusclops L51` (total HP **117**) and
our real L75/L76 party, which is everything the formula needs.

‼‼ AND THE HARNESS FACT WORTH KNOWING, BECAUSE IT EXPLAINS THE FIXTURE: **a driver cannot observe
mid-battle state from its own generator.** When a battle starts the harness hands the controller to
`BattleListener.fight`, and the driver's generator is not resumed until the fight ENDS. So every line
of driver code after "battle started" executes POST-battle — which is why `ch24phoebe` reported
`battle_frames_waited = 0` and an `hp_entering_phoebe` equal to `hp_after`. One cause, three wrong
readings. ⇒ to observe a battle, instrument `on_battle_started` / the strategy, never the driver body.

⛔ THIS PRINTS NUMBERS; IT DOES NOT CHOOSE THE TERM. Picking the leading term is a design decision
that belongs in `#24-ghostreplacement` with a gate case built from THIS party — not in a probe.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ghost_damage_real.py
Exit 0 if the control holds (some move must do real damage, or the formula is not running).
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

from modules.battle_state import get_battle_state
from modules.battle_strategies import BattleStrategyUtil
from modules.pokemon_party import get_party

SAVES = REPO / "tools" / "story-dev" / "saves"
FIXTURE = "in_phoebe_battle_L75.ss1"
BAR = "=" * 108


def main() -> int:
    f = SAVES / FIXTURE
    if not f.is_file():
        print(f"  ABORT (instrument) — no fixture {FIXTURE}")
        return 1
    context.emulator.load_save_state(f.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    try:
        battle_state = get_battle_state()
        foe = battle_state.opponent.left_battler
    except Exception as error:  # noqa: BLE001
        print(f"  ABORT (instrument) — no battle state: {type(error).__name__}: {error}")
        return 1
    if foe is None:
        print("  ABORT (instrument) — no opposing battler in this fixture")
        return 1

    util = BattleStrategyUtil(battle_state)
    banned = context.config.battle.banned_moves

    print(BAR)
    print(f"  REAL DAMAGE vs A REAL GHOST — {FIXTURE}")
    print(f"  FOE: {foe.species.name} L{foe.level}  types={[t.name for t in foe.species.types]}  "
          f"total_hp={foe.total_hp}")
    print(BAR)
    print(f"  {'mon':<12} {'L':>3}  {'move':<14} {'type':<9} {'pwr':>4} {'pp':>6}  "
          f"{'dmg.max':>8}  {'ko_turns':>8}  note")
    print("  " + "-" * 104)

    any_real = False
    rows = []
    for mon in get_party():
        if mon is None or getattr(mon, "species", None) is None:
            continue
        best = 0.0
        for lm in mon.moves:
            if lm is None or lm.move is None:
                continue
            mv = lm.move
            note = ""
            if mv.name in banned:
                note = "BANNED (config)"
                dmg = None
            elif mv.base_power == 0:
                note = "status"
                dmg = None
            else:
                try:
                    dmg = float(util.calculate_move_damage_range(mv, mon, foe).max)
                except Exception as error:  # noqa: BLE001
                    note = f"ERR {type(error).__name__}"
                    dmg = None
            if dmg is not None and dmg > 0:
                any_real = True
                best = max(best, dmg)
                ko = math.ceil(foe.total_hp / dmg)
                ko_s = str(ko)
                if dmg >= foe.total_hp:
                    note = "ONE-SHOTS"
            else:
                ko_s = "-"
            print(f"  {mon.species.name:<12} {mon.level:>3}  {mv.name:<14} "
                  f"{mv.type.name[:8]:<9} {mv.base_power:>4} {lm.pp:>2}/{lm.total_pp:<3}  "
                  f"{('-' if dmg is None else f'{dmg:8.0f}'):>8}  {ko_s:>8}  {note}")
        if best > 0:
            rows.append((mon.species.name, mon.level, best, math.ceil(foe.total_hp / best)))
        else:
            rows.append((mon.species.name, mon.level, 0.0, None))
        print()

    print(BAR)
    print("  PER-MON BEST, AND THE TURNS-TO-KO THAT A `ko_turns` TERM WOULD BUCKET ON:")
    for name, lvl, best, ko in sorted(rows, key=lambda r: -r[2]):
        print(f"    {name:<12} L{lvl:<3} best_damage={best:>8.0f}   ko_turns="
              f"{'NEVER' if not ko else ko}")
    distinct = {ko for _n, _l, b, ko in rows if b > 0}
    print(f"\n  distinct ko_turns buckets among mons that CAN damage it: {sorted(distinct)}")
    if len(distinct) <= 1:
        print("  ⛔⛔ THEY ALL LAND IN ONE BUCKET ⇒ a `ko_turns` leading term would NOT separate them,")
        print("     and the key would fall through to `incoming` and re-pick the wrong mon. This is")
        print("     the SATURATION the refuter predicted; the term needs a finer quantity than turns.")
    else:
        print("  ✅ More than one bucket ⇒ a `ko_turns` term CAN separate these candidates. The cap")
        print("     must be chosen so the buckets that matter stay distinct.")

    print(f"\n{BAR}")
    if not any_real:
        print("  ⛔ CONTROL FAILED — not one move did any damage. The formula is not running;")
        print("     nothing above can be trusted.")
        print(BAR)
        return 1
    print("  ✅ control holds — the damage formula is live (at least one move does real damage).")
    print("  ⛔ This probe DOES NOT choose the ranker's term. That decision belongs in")
    print("     `#24-ghostreplacement`, with a gate case built from THIS party.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
