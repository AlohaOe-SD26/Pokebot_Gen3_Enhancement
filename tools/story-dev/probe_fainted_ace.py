"""Does the bot enter battles with a party member ALREADY FAINTED — and does it do it at BOSSES?

WHY. `--driver normancounter` showed the bot fighting Norman with **`Blaziken L36`, its strongest
Pokémon, already at 0 HP before the first turn**, which is why a 1-HP Shedinja was leading. If
that generalises it is the biggest lever in the project: the counter chain's "N losses with no
super-effective answer" stop ends **79% of all non-finishing runs**, and it would be a
MISDIAGNOSIS of fights lost on preparation. ‼ It was measured on ONE anchor with ONE party and a
deterministic harness — four configurations, not four samples — so it is a LEAD, not a finding,
until something like this says otherwise.

THE SIGNATURE, and why it is readable from logs that predate the turn telemetry. The after-faint
chooser fires when one of OUR mons faints and a replacement must be picked, and it prints the whole
party with HP:

    [FAINT-CHOOSER] alive_slots=[...] on_field=[...] party=[(0, 'Shedinja', 0), (1, 'Blaziken', 0), ...]

At the FIRST such line of a battle, exactly ONE party member should be at 0 — the mon that just
fainted. **Every additional zero is a mon that was already down when the battle started.** That
needs no new instrumentation, so it can be mined from batches already on disk.

‼ POSITIVE CONTROLS, printed before any result:
  * files opened and bytes read (`x4-runs/` is gitignored — the Grep TOOL silently reports 0 on
    it, so a zero here must be distinguishable from "the search could not see the tree");
  * the count of battles whose first faint shows EXACTLY one zero — the normal case. If that is
    zero too, the parser is wrong and every number below is noise rather than a finding.

‼ WHAT THIS CANNOT SAY, and it is a LOT — read before quoting the number.
  1. **The sample is CONDITIONED on a faint happening at all.** The chooser only fires when one of
     our mons goes down, which in batch `20260809-081643` was **36 times across 607 battles** in a
     single lane. So the rate below describes hard/losing battles, NOT battles in general, and it
     must never be quoted as "the bot enters battles with a dead party".
  2. **The opponent is not named**, so "was this a BOSS fight" is not readable. The last battle of
     each log is offered as the closest proxy and is labelled as one.
  3. **The measured rate is ~99%, which is itself a warning sign.** This project's standing rule is
     that a probe returning the same answer for every case has probably found a SYMPTOM or a
     misreading rather than a cause (`08-MISTAKES` 2026-07-31). Treat it as a lead needing an
     independent instrument, not as a result.

‼ THE INDEPENDENT CHECK THIS STILL NEEDS. Nothing here reads party HP at the START of a battle;
it INFERS it from the first faint. The direct measurement is one more log line — party HP at
`[BATTLE] started`, alongside the `#24-bosstelemetry` turn records — and until that exists the
inference stands unconfirmed.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_fainted_ace.py 20260809-081643
"""
import collections
import glob
import os
import re
import sys

FAINT_RE = re.compile(r"\[FAINT-CHOOSER\] alive_slots=\S+ on_field=\S+ party=\[(.*?)\]\s*$")
MEMBER_RE = re.compile(r"\((\d+), '([^']*)', (\d+)\)")
START_RE = re.compile(r"\[BATTLE\] started")


def battles_from(path: str):
    """Yield the first faint-chooser party reading of each battle in one log."""
    current = None
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if START_RE.search(line):
                    current = {"seen_faint": False}
                    continue
                if current is None or current["seen_faint"]:
                    continue
                m = FAINT_RE.search(line.rstrip("\n"))
                if m:
                    current["seen_faint"] = True
                    members = [(int(i), name, int(hp)) for i, name, hp in MEMBER_RE.findall(m.group(1))]
                    if members:
                        yield members
    except OSError:
        return


def main() -> int:
    stamp = sys.argv[1] if len(sys.argv) > 1 else "20260809-081643"
    pattern = os.path.join("x4-runs", stamp, "L0*", "debug-logs", "*.log")
    paths = sorted(glob.glob(pattern))

    total_bytes = 0
    readings = []
    per_file_last = []
    for path in paths:
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            pass
        found = list(battles_from(path))
        readings.extend(found)
        if found:
            per_file_last.append(found[-1])

    print("=" * 84)
    print(f"FAINTED-ACE SCAN — batch {stamp}")
    print("=" * 84)
    print(f"  CONTROL: {len(paths)} debug log(s), {total_bytes:,} bytes read")
    if not paths:
        print("  ‼ CONTROL FAILED — no debug logs matched. Wrong stamp, or the batch stored none.")
        return 1
    print(f"  CONTROL: {len(readings)} battles had a first-faint reading")
    if not readings:
        print("  ‼ CONTROL FAILED — the faint-chooser regex matched nothing. Fix the parser, "
              "not the conclusion.")
        return 1

    zero_counts = collections.Counter(sum(1 for _, _, hp in party if hp == 0) for party in readings)
    normal = zero_counts.get(1, 0)
    print(f"  CONTROL: {normal} battles show EXACTLY one zero at the first faint (the normal case)")
    if normal == 0:
        print("  ‼ CONTROL FAILED — not one battle looks normal, so the reading is suspect.")
        return 1
    print()

    already = [p for p in readings if sum(1 for _, _, hp in p if hp == 0) >= 2]
    pct = 100.0 * len(already) / len(readings)
    print(f"  ⇒ battles entered with a party member ALREADY FAINTED: "
          f"{len(already)} of {len(readings)} = {pct:.1f}%")
    print(f"     (distribution of zeros at first faint: {dict(sorted(zero_counts.items()))})")

    # Which mon is most often already down, and was it the highest-level one?
    ace_down = 0
    names = collections.Counter()
    for party in already:
        dead = [(n, hp) for _, n, hp in party if hp == 0]
        alive = [(n, hp) for _, n, hp in party if hp > 0]
        for n, _ in dead:
            names[n] += 1
        if dead and not alive:
            ace_down += 1
    print(f"     most often already down: {names.most_common(6)}")

    # LAST battle of each run — the closest available proxy for "the fight that ended the run"
    last_already = [p for p in per_file_last if sum(1 for _, _, hp in p if hp == 0) >= 2]
    if per_file_last:
        print()
        print(f"  PROXY (last battle of each log — a run that dies on a boss dies here): "
              f"{len(last_already)} of {len(per_file_last)} entered with someone already fainted")
    print()
    print("‼ The faint-chooser does not name the opponent, so this does not prove the affected "
          "battles were BOSS battles. Read it as a rate, not as a boss-specific claim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
