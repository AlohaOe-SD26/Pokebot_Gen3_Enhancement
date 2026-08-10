"""Does the bot enter battles — and especially the battle that ENDS a run — with mons already down?

THE QUESTION, and why it matters more than anything else currently open. `--driver normancounter`
showed the bot fighting Norman with its ace at **0/120**, after two earlier gym battles it entered
at **23/120**, because nothing heals between the gym's trainers and its leader. If that
generalises, the counter chain's *"N losses with no super-effective answer"* stop — which ends
**~80-88% of all non-finishing runs** — is a MISDIAGNOSIS of fights lost on preparation, and the
whole counter programme is aimed at the wrong thing.

‼ THIS FILE WAS REWRITTEN 2026-08-09. The first version had to INFER the opening party state from
the after-faint chooser (at the first faint, extra zeros implied mons already down). It returned
99.4%, which is the shape of a misreading rather than a fact, and it was never promoted to a
finding. `#24-bosstelemetry` part 2 then made `[BATTLE] started` record the party directly:

    [BATTLE] started hp=[('Blaziken', 23, 120), ('Shedinja', 1, 1), ('Whismur', 52, 52), ...]

so the inference is replaced by a measurement. ‼ Batches from BEFORE that change have no `hp=`
field; this probe reports that honestly instead of scoring them as zero.

‼ POSITIVE CONTROLS, printed before any result:
  * files opened and bytes read (`x4-runs/` is gitignored — the Grep TOOL silently reports 0 on
    it, so "no data" and "could not look" must be distinguishable);
  * the number of battles entered at FULL health. A healthy bot starts most battles full, so if
    that count is ~0 the parser or the reading is wrong, not the bot.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_fainted_ace.py 20260809-155844
"""
import collections
import glob
import os
import re
import sys

STARTED_RE = re.compile(r"\[BATTLE\] started hp=\[(.*?)\]\s*$")
MEMBER_RE = re.compile(r"\('([^']*)', (\d+), (\d+)\)")


def battles_from(path: str):
    """Yield each battle's opening party as [(name, current_hp, max_hp), ...]."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                m = STARTED_RE.search(line.rstrip("\n"))
                if not m:
                    continue
                members = [(n, int(c), int(t)) for n, c, t in MEMBER_RE.findall(m.group(1))]
                if members:
                    yield members
    except OSError:
        return


def describe(party):
    fainted = [n for n, c, _ in party if c == 0]
    # "ace" = the biggest max-HP mon present. A proxy for "strongest", and labelled as one:
    # max HP tracks level and species bulk, which is the best available signal in this line.
    ace = max(party, key=lambda m: m[2]) if party else None
    frac = (sum(c for _, c, _ in party) / max(1, sum(t for _, _, t in party))) if party else 0.0
    return fainted, ace, frac


def main() -> int:
    stamp = sys.argv[1] if len(sys.argv) > 1 else "20260809-155844"
    paths = sorted(glob.glob(os.path.join("x4-runs", stamp, "L0*", "debug-logs", "*.log")))

    total_bytes = 0
    all_battles, last_per_log = [], []
    logs_with_field = 0
    for path in paths:
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            pass
        found = list(battles_from(path))
        if found:
            logs_with_field += 1
            all_battles.extend(found)
            last_per_log.append(found[-1])

    print("=" * 86)
    print(f"BATTLE-START PARTY HEALTH — batch {stamp}")
    print("=" * 86)
    print(f"  CONTROL: {len(paths)} debug log(s), {total_bytes:,} bytes read")
    if not paths:
        print("  ‼ CONTROL FAILED — no debug logs matched that stamp.")
        return 1
    if not all_battles:
        print("  ‼ NO `hp=` FIELD FOUND. This batch predates `#24-bosstelemetry` part 2 "
              "(2026-08-09), so the question CANNOT be answered from it — that is a missing "
              "instrument, not a rate of zero.")
        return 1
    print(f"  CONTROL: {logs_with_field} of {len(paths)} logs carry the field; "
          f"{len(all_battles)} battles read")

    full = sum(1 for p in all_battles if all(c == t for _, c, t in p))
    print(f"  CONTROL: {full} battles ({100.0*full/len(all_battles):.1f}%) were entered at FULL "
          f"health — if this were ~0 the reading would be suspect, not the bot")
    print()

    def report(label, battles):
        if not battles:
            print(f"  {label}: no data")
            return
        with_dead = [p for p in battles if any(c == 0 for _, c, _ in p)]
        ace_dead = [p for p in battles if describe(p)[1] and describe(p)[1][1] == 0]
        mean_frac = sum(describe(p)[2] for p in battles) / len(battles)
        print(f"  {label}  (n={len(battles)})")
        print(f"     entered with >=1 mon FAINTED : {len(with_dead):>4} "
              f"({100.0*len(with_dead)/len(battles):.1f}%)")
        print(f"     entered with the ACE fainted : {len(ace_dead):>4} "
              f"({100.0*len(ace_dead)/len(battles):.1f}%)   [ace = biggest max-HP mon]")
        print(f"     mean party HP at battle start: {100.0*mean_frac:.1f}%")

    report("ALL battles", all_battles)
    print()
    report("LAST battle of each run  (the fight a losing run dies on)", last_per_log)

    print()
    counts = collections.Counter(sum(1 for _, c, _ in p if c == 0) for p in all_battles)
    print(f"  distribution of fainted-at-start counts: {dict(sorted(counts.items()))}")
    print()
    print("‼ The line does not name the opponent, so 'was this the BOSS' is still not directly "
          "readable; the last-battle row is a labelled proxy. And a run that ends on the counter "
          "chain's stop ends WITHOUT a final battle, so the proxy under-counts those.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
