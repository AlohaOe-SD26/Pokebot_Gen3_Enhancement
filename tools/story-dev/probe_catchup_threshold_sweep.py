# -*- coding: utf-8 -*-
"""WOULD A WIDER `TRAIN_CATCHUP_GAP` ADMIT ANYONE NEW *AT A REAL TRAINING EPISODE*?

⛔⛔ WHY THIS EXISTS, AND WHY IT IS CHECKED IN. A 10-agent pass concluded that widening
`TRAIN_CATCHUP_GAP` admits **zero** additional mons, and that got written into the punch list as a
permanent *"DO NOT RE-PROPOSE"*. A Tier 1 reviewer refused it: the number lived only in a scratchpad
tool, so nobody could re-run it. **An unverifiable agent report must never become a permanent
foreclosure** — this project's rule is that agent output is a NOTE, never truth.

‼‼ AND THE FIRST VERSION OF *THIS* TOOL ANSWERED THE WRONG QUESTION — a near-miss worth recording.
It evaluated admission at EVERY heartbeat and found widening would admit **66 more mons**, which
looks like a refutation of the agent. It is not: **admission only matters at a moment when a
training episode actually evaluates it.** Sweeping all of time answers *"could this mon ever be
inside the window?"*; the decision needs *"is it inside when the code looks?"*. ⇒ this version
anchors on the real episodes.

HOW IT WORKS NOW — and it needs no modelling assumption at all:
  * the episode marker is the production line `Story: training the team to Lv <T> in the grass…`
    (1,828 occurrences in the reference batch) — **and it carries the real `target` T**, so the
    predicate is evaluated exactly as `story_mode.py:2135-2136` computes it:
        catchup = T - G        ;    admitted  <=>  level >= catchup
    No `target = team_max + 1` approximation, no branch guessing.
  * party state is taken from the nearest PRECEDING heartbeat (<= 3,600 frames earlier, so at most
    one minute stale), keyed by (run, PID, species-lineage) — PID alone is NOT unique, because
    Shedinja is created as a copy of Nincada and inherits its personality value.

⛔ WHAT THIS STILL CANNOT ANSWER: whether an admitted mon is in `battlers` at that moment.
`_battler_slots()` (`modules/story/early_game.py:1894`) requires a non-egg mon holding a damaging
move, and `ids=` records no moves. A reviewer raised bench-membership as the possible real
constraint; **this tool neither confirms nor rules that out**, and says so instead of pretending.

Always exits 0 — an OBSERVATION tool, not a gate.
"""
import argparse
import ast
import bisect
import collections
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
HB = re.compile(r"^f(\d+)\s+\[hb\].*?\bids=(\[[^\]]*\])")
ONE = re.compile(r"^(\w+)#([0-9A-F?]{8}):L(\d+):exp(\d+)$")
EPISODE = re.compile(r"^f(\d+)\s.*?Story: training the team to Lv (\d+) in the grass")
CAUGHT = re.compile(r"\[BATTLE\] ended \(outcome=BattleOutcome\.Caught")
WALLY = re.compile(r"Dad and the Wally catching tutorial")
STEVEN = re.compile(r"the multi battle with Steven")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batch", default="20260909-160339")
    a = ap.parse_args()
    logs = sorted((HERE / "x4-runs" / a.batch).rglob("L0*/debug-logs/*.log"))
    print("=" * 100)
    print(f"TRAIN_CATCHUP_GAP SWEEP, EVALUATED AT REAL TRAINING EPISODES — batch {a.batch}")
    print("=" * 100)
    if not logs:
        print("  ⛔ no debug logs found.")
        return 0

    episodes = []                                   # (run, frame, target)
    beats = collections.defaultdict(list)           # run -> [(frame, {key: level})]
    first_gap, caught, tut, stv = {}, collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    hb = 0
    for f in logs:
        run = f.stem
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            em = EPISODE.match(line)
            if em:
                episodes.append((run, int(em.group(1)), int(em.group(2))))
            fm = re.match(r"^f(\d+)\s", line)
            if not fm:
                continue
            fr = int(fm.group(1))
            if CAUGHT.search(line):
                caught[run].append(fr)
            if WALLY.search(line):
                tut[run].append(fr)
            if STEVEN.search(line):
                stv[run].append(fr)
            m = HB.match(line)
            if not m:
                continue
            hb += 1
            try:
                elems = ast.literal_eval(m.group(2))
            except Exception:  # noqa: BLE001
                continue
            party = [(x.group(1), x.group(2), int(x.group(3)))
                     for x in (ONE.match(e) for e in elems) if x]
            if not party:
                continue
            top = max(p[2] for p in party)
            snap = {}
            for sp, pid, lv in party:
                key = (run, pid, "SHED" if sp == "Shedinja" else "MAIN")
                snap[key] = lv
                if key not in first_gap:
                    first_gap[key] = (top - lv, fr)
            beats[run].append((fr, snap))

    for r in beats:
        beats[r].sort(key=lambda x: x[0])
    #: parallel frame lists — bisect cannot order tuples whose second element is a dict
    bframes = {r: [fr for fr, _s in v] for r, v in beats.items()}

    #: genuine catches, anchored on the Caught line, minus the two known contaminants
    genuine = set()
    for key, (_g, fr) in first_gap.items():
        run = key[0]
        if any(fr - 7200 <= t <= fr + 3600 for t in tut[run]):
            continue
        if any(fr - 7200 <= s <= fr + 3600 for s in stv[run]):
            continue
        if any(fr - 7200 <= c <= fr for c in caught[run]):
            genuine.add(key)
    gap68 = {k for k in genuine if 6 <= first_gap[k][0] <= 8}

    print(f"  heartbeats {hb:,}   training episodes {len(episodes):,}   "
          f"genuine catches {len(genuine)}   of which arrived gap 6-8: {len(gap68)}")
    if not episodes:
        print("  ⛔ no training episodes found — cannot answer.")
        return 0
    tgts = collections.Counter(t for _r, _f, t in episodes)
    print(f"  episode targets seen: {dict(sorted(tgts.items())[:8])}{' …' if len(tgts) > 8 else ''}")

    print(f"\n  {'G':>4}{'mons admitted at >=1 episode':>32}{'of the 6-8 catches':>22}")
    rows = {}
    for G in (5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 10 ** 6):
        adm = set()
        for run, fr, target in episodes:
            arr = beats.get(run, [])
            i = bisect.bisect_right(bframes.get(run, []), fr) - 1
            if i < 0:
                continue
            bfr, snap = arr[i]
            if fr - bfr > 3600:
                continue
            catchup = target - G
            for key, lv in snap.items():
                if lv >= catchup and lv < target:
                    adm.add(key)
        rows[G] = adm
        label = "∞" if G > 1000 else str(G)
        print(f"  {label:>4}{len(adm):>18} / {len(first_gap):<10}"
              f"{len(adm & gap68):>12} / {len(gap68):<8}")

    base, inf = rows[6], rows[10 ** 6]
    print("  " + "-" * 96)
    print(f"  ⇒ from the shipped G=6 to G=INFINITY: **{len(inf) - len(base)}** additional mon(s) "
          f"admitted overall,")
    print(f"    and **{len(inf & gap68) - len(base & gap68)}** of the {len(gap68)} gap-6-8 catches.")
    if len(inf & gap68) - len(base & gap68) == 0:
        print("  ⇒ ⛔ **A WIDER WINDOW HAS NOTHING TO ADMIT** among the mons this investigation was")
        print("     about: by the time a training episode evaluates them they are already inside.")
    print("  ⛔ NOT ANSWERED: whether an admitted mon is in `battlers` then — `_battler_slots()`")
    print("     needs a damaging move and `ids=` logs no moves. Bench membership stays untested.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
