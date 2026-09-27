r"""GATE — the HM teach's slot picker is TOTAL and never deletes what the mon was trained on (KI-104, 2026-09-26).

WHY: the old rule ("zero power, else the lowest RAW base power") was measured in the live batch deleting Combusken's
Double Kick (it hits twice) for Rock Smash, Swampert's Earthquake, Marshtomp's Mud Shot (keeping the weaker Muddy
Water) and Machoke's Low Kick (stored as power 1). The replacement must stay TOTAL: the HM teach gates story progress,
and a picker that returns None / 4 / an HM slot stalls, derails or silently deletes the wrong move (adversarial recon).

  S1  THE LIVE SHAPES: Combusken + Rock Smash ⇒ Peck (not Double Kick); Marshtomp + Surf ⇒ Muddy Water (dominated by
      Surf); Machoke + Strength ⇒ not Low Kick; Marill + Waterfall ⇒ Tail Whip (status); Blaziken + Strength ⇒ Scratch
      (dominated by Strength; the `#26-hmwrongitem` drive's own case, where the old rule took Double Kick).
  S2  TOTALITY: Swampert with three HMs ⇒ its one non-HM slot; an HM in EVERY position 0-3 is never chosen; 500 seeded
      random movesets with a non-HM slot ⇒ always an int 0-3 on a non-HM; an incoming STATUS HM (Flash) still gets a
      slot; an all-HM moveset ⇒ ValueError (the caller's refusal, before the bag opens); an empty slot is used first.
  S3  BANNED moves go before usable attacks.
  S4  WIRING: `teach_hm_move`'s default path calls `choose_hm_slot`; the old rule only under
      `POKEBOT_HMTEACH_FAULT_OLDSLOT` (registered in 29); a slot outside 0-3 or holding an HM is refused BEFORE the bag.
FAULT ARMS (built in): the old raw-power rule (S1); a picker that refuses (None) when only STAB moves remain (S2); a
picker that treats an HM as type COVERAGE (any same-type move makes a non-HM move expendable) (S1).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_hmslot_rule.py
"""
from __future__ import annotations

import ast
import io
import pathlib
import random
import sys
import tokenize

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

from modules.story import early_game as EG  # noqa: E402

M = EG.HmSlotMove
EGSRC = ROOT / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def mv(name, type_, power, effect="HIT", hm=False, prio=0):
    return M(name, type_, power, effect, hm, prio)


ROCK_SMASH = mv("Rock Smash", "Fighting", 20, "DEFENSE_DOWN_HIT", hm=True)
SURF = mv("Surf", "Water", 95, hm=True)
STRENGTH = mv("Strength", "Normal", 80, hm=True)
WATERFALL = mv("Waterfall", "Water", 80, "FLINCH_HIT", hm=True)
DIVE = mv("Dive", "Water", 60, "SEMI_INVULNERABLE", hm=True)
FLASH = mv("Flash", "Normal", 0, "ACCURACY_DOWN", hm=True)


def s1(pick, sink=None):
    combusken = [mv("Scratch", "Normal", 40), mv("Peck", "Flying", 35), mv("Double Kick", "Fighting", 30, "DOUBLE_HIT"),
                 mv("Ember", "Fire", 40, "BURN_HIT")]
    check(pick(combusken, ("Fire", "Fighting"), ROCK_SMASH) == 1,
          "S1 Combusken + Rock Smash ⇒ Peck, NOT Double Kick (30 but two hits; the old rule took it 5 times live)", sink)
    marshtomp = [mv("Take Down", "Normal", 90, "RECOIL"), mv("Mud Shot", "Ground", 55, "SPEED_DOWN_HIT"), ROCK_SMASH,
                 mv("Muddy Water", "Water", 95, "ACCURACY_DOWN_HIT")]
    check(pick(marshtomp, ("Water", "Ground"), SURF) == 3,
          "S1 Marshtomp + Surf ⇒ Muddy Water (dominated by Surf), NOT its only Ground move", sink)
    machoke = [mv("Low Kick", "Fighting", 1, "LOW_KICK"), mv("Seismic Toss", "Fighting", 1, "LEVEL_DAMAGE"),
               mv("Vital Throw", "Fighting", 70, "VITAL_THROW"), mv("Karate Chop", "Fighting", 50, "HIGH_CRITICAL")]
    check(pick(machoke, ("Fighting",), STRENGTH) != 0, "S1 Machoke + Strength ⇒ NOT Low Kick (stored as power 1)", sink)
    marill = [mv("Tackle", "Normal", 35), DIVE, mv("Tail Whip", "Normal", 0, "DEFENSE_DOWN"), mv("Water Gun", "Water", 40)]
    check(pick(marill, ("Water",), WATERFALL) == 2, "S1 Marill + Waterfall ⇒ Tail Whip (the status move)", sink)
    blaziken = [mv("Scratch", "Normal", 40), mv("Blaze Kick", "Fire", 85, "BLAZE_KICK"),
                mv("Double Kick", "Fighting", 30, "DOUBLE_HIT"), ROCK_SMASH]
    check(pick(blaziken, ("Fire", "Fighting"), STRENGTH) == 0,
          "S1 Blaziken + Strength ⇒ Scratch (dominated by Strength); the old rule took Double Kick in the live drive", sink)


def s2(pick, sink=None):
    swampert = [SURF, DIVE, mv("Mud Shot", "Ground", 55, "SPEED_DOWN_HIT"), ROCK_SMASH]
    check(pick(swampert, ("Water", "Ground"), WATERFALL) == 2, "S2 Swampert with three HMs ⇒ its one non-HM slot", sink)
    base = [mv("Tackle", "Normal", 35), mv("Ember", "Fire", 40), mv("Bite", "Dark", 60), mv("Peck", "Flying", 35)]
    ok_all = True
    for k in range(4):
        ms = list(base)
        ms[k] = ROCK_SMASH
        got = pick(ms, ("Fire",), STRENGTH)
        ok_all = ok_all and isinstance(got, int) and got != k
    check(ok_all, "S2 an HM in EVERY position 0-3 is never chosen", sink)
    rng = random.Random(260926)
    types = ["Normal", "Fire", "Water", "Grass", "Fighting", "Ground", "Flying", "Dark", "Psychic"]
    bad = 0
    for _ in range(500):
        ms = []
        for _slot in range(4):
            if rng.random() < 0.3:
                ms.append(rng.choice([ROCK_SMASH, SURF, STRENGTH, DIVE, WATERFALL, FLASH]))
            else:
                ms.append(mv(f"M{_slot}", rng.choice(types), rng.choice([0, 1, 20, 35, 40, 60, 75, 90]),
                             rng.choice(["HIT", "DOUBLE_HIT", "MULTI_HIT"])))
        if all(m.is_hm for m in ms):
            ms[rng.randrange(4)] = mv("Tackle", "Normal", 35)
        got = pick(ms, (rng.choice(types),), rng.choice([ROCK_SMASH, SURF, STRENGTH, FLASH]))
        if not (isinstance(got, int) and 0 <= got <= 3 and not ms[got].is_hm):
            bad += 1
    check(bad == 0, f"S2 500 seeded movesets with a non-HM slot ⇒ always an int 0-3 on a non-HM ({bad} bad)", sink)
    check(pick(base, ("Fire",), FLASH) in range(4), "S2 an incoming STATUS HM (Flash) still gets a slot", sink)
    check(pick([mv("Tackle", "Normal", 35), None, None, None], ("Normal",), SURF) == 1, "S2 an empty slot is used first",
          sink)
    try:
        pick([SURF, DIVE, STRENGTH, ROCK_SMASH], ("Water",), WATERFALL)
        raised = False
    except ValueError:
        raised = True
    check(raised, "S2 an all-HM moveset ⇒ ValueError (the caller's refusal, before the bag opens)", sink)


def s3(pick, sink=None):
    ms = [mv("Solar Beam", "Grass", 120, "SOLAR_BEAM"), mv("Tackle", "Normal", 35), mv("Absorb", "Grass", 20, "ABSORB"),
          mv("Bite", "Dark", 60)]
    check(pick(ms, ("Grass",), STRENGTH, ("Solar Beam",)) == 0,
          "S3 a BANNED move (the strategy never selects it) goes before usable attacks", sink)


def _strip(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def s4():
    src = EGSRC.read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "teach_hm_move")
    body = _strip(ast.get_source_segment(src, fn) or "")
    arm = "POKEBOT_HMTEACH_FAULT_OLDSLOT"
    i_arm = body.find(f'os.environ.get("{arm}") == "1"')
    i_old = body.find("min(eligible, key=lambda i: moves[i].move.base_power)")
    i_new = body.find("replace_slot = choose_hm_slot(")
    check(0 <= i_arm < i_old < i_new, "S4 the default path calls choose_hm_slot; the old rule only under the arm")
    check(body.count("min(eligible, key=lambda i: moves[i].move.base_power)") == 1,
          "S4 … and the old rule appears exactly once")
    check(f"`{arm}`" in REGISTRY.read_text(encoding="utf-8"), f"S4 {arm} is registered in 29")
    i_guard = body.find("an HM move — the game refuses to forget it")
    i_bag = body.find('StartMenuNavigator("BAG").step()')
    check(0 < i_guard < i_bag and "is not a slot 0-3" in body,
          "S4 a slot outside 0-3 or holding an HM is refused BEFORE the bag opens")


def main() -> int:
    print("=" * 92)
    print("GATE — the HM teach's slot picker is total and keeps what the mon was trained on (KI-104)")
    print("=" * 92)
    s1(EG.choose_hm_slot)
    s2(EG.choose_hm_slot)
    s3(EG.choose_hm_slot)
    s4()

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []

    def old_rule(moves, mon_types, incoming, banned=()):
        slots = list(moves) + [None] * (4 - len(moves))
        for i, m in enumerate(slots):
            if m is None:
                return i
        eligible = [i for i, m in enumerate(slots) if not m.is_hm]
        if not eligible:
            raise ValueError
        zero = [i for i in eligible if slots[i].power == 0]
        return zero[0] if zero else min(eligible, key=lambda i: slots[i].power)

    s1(old_rule, sink)
    check(bool(sink), f"FAULT the old raw-power rule FAILS S1 ({len(sink)} caught)")
    sink = []

    def refuses_stab(moves, mon_types, incoming, banned=()):
        got = EG.choose_hm_slot(moves, mon_types, incoming, banned)
        return None if moves[got] is not None and moves[got].type in mon_types else got

    try:
        s2(refuses_stab, sink)
    except Exception as error:  # noqa: BLE001 - a crash on None is also a failure of the thing under test
        sink.append(f"raised {type(error).__name__}")
    check(bool(sink), f"FAULT a picker that returns None when only STAB remains FAILS S2 ({len(sink)} caught)")
    sink = []

    def coverage_rule(moves, mon_types, incoming, banned=()):
        slots = list(moves) + [None] * (4 - len(moves))
        eligible = [i for i, m in enumerate(slots) if m is not None and not m.is_hm]
        pool = [m for m in slots if m is not None] + [incoming]
        dup = [i for i in eligible if slots[i].power > 0 and any(o is not slots[i] and o.type == slots[i].type for o in pool)]
        return min(dup, key=lambda i: slots[i].power) if dup else EG.choose_hm_slot(moves, mon_types, incoming, banned)

    s1(coverage_rule, sink)
    check(bool(sink), f"FAULT a picker that treats an HM as type COVERAGE FAILS S1 ({len(sink)} caught)")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
