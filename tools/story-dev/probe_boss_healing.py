"""How often does an opponent HEAL mid-battle, and does the bot lose those fights?

WHY. `--driver normancounter` showed Norman restoring **Vigoroth 1 -> 53** and **Slaking 27 -> 136**
while the party chipped 6-8 damage a turn. Chip damage into a healing 143-HP boss cannot win
whatever type it is — so "the bot has no answer to boss item usage" is a candidate explanation for
the counter chain's *"N losses with no super-effective answer"* stop, which ends **~88% of all
non-finishing runs**.

‼ THE COMPANION HYPOTHESIS IS ALREADY DEAD, and this exists partly because of that. The same run
also showed the bot entering Norman with its ace at 0 HP, which looked like the bigger lever —
until `probe_fainted_ace.py`, reading the direct `hp=` field over a whole batch, measured **6.4%**
of battles starting with any mon fainted and **2.9%** with the ace down, against a mean party
health of **90.6%**. That anchor was not representative. **Do not assume this one is either** —
that is the whole point of measuring it over a batch.

HOW IT READS. `#24-bosstelemetry` logs the opponent every turn:

    [TURN 12] Ninjask L27 80/80 -> UseMove:Scratch(pp34)  vs Slaking L31 130/143

A HEAL is the same opponent's current HP going UP between consecutive turns of one battle.
Identity is `(name, max_hp)`, so a switch to a different species — or to the same species with
different bulk — is not mistaken for healing.

‼ TWO CLASSES OF HEAL, AND ONLY ONE OF THEM IS UNDERSTOOD — do not let a claim mix them.
Across 2,565 events in two batches the magnitudes split cleanly:
  * **LARGE (>= `BIG_HEAL_HP`, default 50)** — `Slaking` dominates, at **+106 / +108 / +119** and a
    median of +81. That is a trainer using a Full Restore / Hyper Potion, and it is the only class
    any conclusion in this project rests on.
  * **SMALL (mostly +1 / +2 / +3, decaying smoothly)** — **UNEXPLAINED.** It was investigated on
    2026-08-10 and the obvious candidate was RULED OUT: held berries would spike at exactly +10
    (Oran) and +30 (Sitrus), and the histogram shows no such spike — it is a smooth decay
    (`+1` x374, `+2` x139, `+3` x127, …). Leftovers-style per-turn regen fits the tiny values for
    small wild mons but not the +14/+15/+16 cluster on `Illumise`. A reading artifact is possible
    and has not been excluded.
So the probe reports the two classes SEPARATELY, and the headline number is the large-heal one.
Anyone extending this should either explain the small class or leave it quarantined — folding it
into a total would silently inflate every "bosses heal" statement.

‼ POSITIVE CONTROLS, printed before any result:
  * files and bytes read (`x4-runs/` is gitignored; "no data" must be distinguishable from
    "could not look");
  * the number of turn records parsed, and the number of battles seen. If turns parse but no
    battle ever shows a heal, that is a real finding; if NOTHING parses, the regex is wrong.

‼ WHAT IT CANNOT SAY. The line does not mark which battles are boss battles, and a run that ends
on the counter chain's stop ends without a final battle at all. Healing is reported per battle and
for the longest battles (a proxy for boss fights, and labelled as one).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_boss_healing.py 20260809-155844
"""
import collections
import glob
import os
import re
import sys

#: Heals at or above this are the understood class (trainer item usage). Below it lies the
#: unexplained small class — see the module docstring. Quarantined, never folded into a total.
BIG_HEAL_HP = 50

TURN_RE = re.compile(r"\[TURN (\d+)\] .*? vs ([A-Za-z' .-]+?) L(\d+) (\d+)/(\d+)\s*$")
START_RE = re.compile(r"\[BATTLE\] started")


def battles_from(path: str):
    """Yield one list of (turn, opponent_key, current_hp) per battle."""
    current = []
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if START_RE.search(line):
                    if current:
                        yield current
                    current = []
                    continue
                m = TURN_RE.search(line.rstrip("\n"))
                if m:
                    turn, name, _lvl, cur, mx = m.groups()
                    current.append((int(turn), (name.strip(), int(mx)), int(cur)))
    except OSError:
        return
    if current:
        yield current


def heals_in(battle):
    """Count HP increases for the same opponent identity within one battle."""
    last = {}
    events = []
    for turn, key, cur in battle:
        if key in last and cur > last[key]:
            events.append((turn, key[0], last[key], cur))
        last[key] = cur
    return events


def main() -> int:
    stamp = sys.argv[1] if len(sys.argv) > 1 else "20260809-155844"
    paths = sorted(glob.glob(os.path.join("x4-runs", stamp, "L0*", "debug-logs", "*.log")))

    total_bytes = 0
    battles = []
    for path in paths:
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            pass
        battles.extend(list(battles_from(path)))

    print("=" * 86)
    print(f"OPPONENT MID-BATTLE HEALING — batch {stamp}")
    print("=" * 86)
    print(f"  CONTROL: {len(paths)} debug log(s), {total_bytes:,} bytes read")
    turns = sum(len(b) for b in battles)
    print(f"  CONTROL: {len(battles)} battles with turn records, {turns} turn records parsed")
    if not battles or not turns:
        print("  ‼ CONTROL FAILED — nothing parsed. Either this batch predates "
              "`#24-bosstelemetry` (2026-08-09) or the regex is wrong. Not a rate of zero.")
        return 1

    healed = [(b, heals_in(b)) for b in battles]
    with_heal = [(b, e) for b, e in healed if e]
    big = [(b, [e for e in ev if e[3] - e[2] >= BIG_HEAL_HP]) for b, ev in healed]
    big = [(b, ev) for b, ev in big if ev]
    print()
    print(f"  ⇒ battles with a LARGE heal (>= {BIG_HEAL_HP} HP — the understood class): "
          f"{len(big)} of {len(battles)} ({100.0*len(big)/len(battles):.1f}%), "
          f"{sum(len(e) for _, e in big)} events")
    print(f"     [quarantined] battles with ANY heal incl. the unexplained small class: "
          f"{len(with_heal)} ({100.0*len(with_heal)/len(battles):.1f}%), "
          f"{sum(len(e) for _, e in with_heal)} events")

    # Long battles are the closest available proxy for boss fights — labelled as a proxy.
    long_battles = [(b, e) for b, e in healed if len(b) >= 12]
    if long_battles:
        lh = [(b, [e for e in ev if e[3] - e[2] >= BIG_HEAL_HP]) for b, ev in long_battles]
        lh = [x for x in lh if x[1]]
        print(f"  PROXY — battles of >=12 turn records (boss-length): "
              f"{len(lh)} of {len(long_battles)} show healing "
              f"({100.0*len(lh)/len(long_battles):.1f}%)")

    names = collections.Counter()
    biggest = []
    for _, events in with_heal:
        for turn, name, before, after in events:
            names[name] += 1
            biggest.append((after - before, name, before, after))
    if names:
        print(f"  opponents most often healed: {names.most_common(8)}")
    biggest.sort(reverse=True)
    if biggest:
        print("  largest single heals:")
        for delta, name, before, after in biggest[:6]:
            print(f"     +{delta:<4} {name}  {before} -> {after}")
    print()
    print("‼ Turn records do not mark boss battles; the >=12-turn row is a labelled PROXY. A run "
          "that ends on the counter chain's stop ends WITHOUT a final battle, so boss-length "
          "battles are under-counted here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
