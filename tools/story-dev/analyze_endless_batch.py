"""ANALYSE AN `install_sandbox.py` ENDLESS-RESET BATCH — the per-profile debug logs, not an x4 batch.

⛔ WHY THIS EXISTS AND WHY IT IS NOT `x4_headless.py --resummarise`. The 2026-09-15/16 dataset was
produced by `install_sandbox.py`'s 4-lane ENDLESS RESET mode, NOT by `x4_headless.py`. There is
therefore no `x4-runs/<stamp>/` directory and no MANIFEST, and the batch summariser cannot read it.
The logs live at:

    sandbox-pokebot/profiles/endless-P<n>-<starter>/debug-logs/Old/*.log

‼ ONE LOG IS ONE RUN. Endless-reset opens a NEW debug log on every reset, so the count of logs is
the count of runs — and a single start-stamp names only each lane's FIRST run. (That mistake was
made and corrected on 2026-09-15: a stamp here is a RUN id, never a BATCH id.)

⛔ WHAT THIS DELIBERATELY DOES **NOT** CLAIM. There is no badge or chapter marker in these logs —
grepped for, absent. So progress is reported as **MAPS REACHED**, which is a strictly weaker claim
than badges: reaching Mauville does NOT mean the Mauville gym was beaten. Every milestone below is
named `reached_*` for that reason. ‼ Do not let a reader upgrade "reached" into "cleared"; the
distinction is the whole reason the column is named this way.

USAGE
    PYTHONUTF8=1 py -3.12 analyze_endless_batch.py                 # the 2026-09-15/16 batch
    PYTHONUTF8=1 py -3.12 analyze_endless_batch.py --since 20260915 --until 20260916
    PYTHONUTF8=1 py -3.12 analyze_endless_batch.py --self-test     # fault arms, touches no logs

Exit 0 always for the report (it is a measurement, not a gate); 1 if --self-test fails.
"""

import argparse
import collections
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
PROFILES = REPO / "sandbox-pokebot" / "profiles"

#: Story-ordered milestones. ‼ REACHING a city is NOT beating its gym — see the module docstring.
#: Ordered by the story's own sequence so "furthest reached" is well defined.
MILESTONES = [
    ("littleroot", "LITTLEROOT TOWN"),
    ("rustboro", "RUSTBORO CITY"),
    ("dewford", "DEWFORD TOWN"),
    ("slateport", "SLATEPORT CITY"),
    ("mauville", "MAUVILLE CITY"),
    ("lavaridge", "LAVARIDGE TOWN"),
    ("fortree", "FORTREE CITY"),
    ("lilycove", "LILYCOVE CITY"),
    ("mossdeep", "MOSSDEEP CITY"),
    ("sootopolis", "SOOTOPOLIS CITY"),
    ("victory_road", "VICTORY ROAD"),
    ("ever_grande", "EVER GRANDE CITY"),
]

#: ⛔ THE FALSIFICATION TEST. The handoff claims no run can reach the Elite Four because §Ch24 is
#: not wired into `story_mode.py`. That is a CLAIM, and this is the arm that could refute it: if any
#: log shows a League INTERIOR map, the claim is wrong and must be retracted rather than defended.
#: Ever Grande CITY is the outdoor map and does NOT count — the door apron is outside.
LEAGUE_INTERIOR = ("POKEMON LEAGUE", "SIDNEY", "PHOEBE", "GLACIA", "DRAKE", "CHAMPION", "HALL OF FAME")

_FRAME = re.compile(r"^f(\d+) ")
_DERAIL = re.compile(r"\[STORY\] DERAIL #\d+: (.*)")
_WHITEOUT = re.compile(r"\[STORY\] WHITEOUT recovery #(\d+)")
_MAPTO = re.compile(r"\[MAP\] .*? -> ([A-Z0-9 '.]+)\(")
_HBMAP = re.compile(r"\[hb\] .*? map=([A-Z0-9 '.]+)\(")
_OWNED = re.compile(r"owned=(\d+)")
_LEVELS = re.compile(r":L(\d+)")


def _signature(reason: str) -> str:
    """Collapse a derail message to a comparable SIGNATURE.

    ⛔ Numbers and coordinates are stripped because they are per-incident noise; MAP NAMES are KEPT
    because "blocked walking to Fallarbor" and "blocked walking to Mauville" are different defects.
    A signature that merged them would hide exactly the distinction `#26-healmap-route111split` is
    about.
    """
    s = reason.strip()
    s = re.sub(r"\(\s*-?\d+\s*,\s*-?\d+\s*\)", "(x,y)", s)   # coordinates
    s = re.sub(r"\b\d[\d,]*\b", "N", s)                        # counts / frame numbers
    return s[:110]


def analyse(since: str, until: str):
    lanes = sorted(p for p in PROFILES.glob("endless-P*") if p.is_dir())
    runs = []
    for lane in lanes:
        for log in sorted((lane / "debug-logs" / "Old").glob("*.log")):
            stamp = log.name.split("debug-")[-1].replace(".log", "")
            day = stamp.split("-")[0]
            if not (since <= day <= until):
                continue
            runs.append((lane.name, stamp, log))
    return runs


def report(runs) -> None:
    bar = "=" * 92
    print(bar)
    print(f"ENDLESS-RESET BATCH ANALYSIS — {len(runs)} runs across "
          f"{len({r[0] for r in runs})} lanes")
    print(bar)
    if not runs:
        print("  no logs matched. Check --since/--until and that the logs are under debug-logs/Old/.")
        return

    derails = collections.Counter()
    derail_runs = collections.Counter()
    whiteouts, frames, owned_max, lvl_max = [], [], [], []
    furthest = collections.Counter()
    #: ⛔ MEASURED reach — one increment per milestone a run ACTUALLY visited. ADDED 2026-09-16
    #: because the CUMULATIVE row below was an ASSUMED-ORDER ROLL-UP: `cum += furthest[key]` walked
    #: backwards through MILESTONES and *inferred* that reaching Ever Grande implied having reached
    #: every earlier town. `seen_maps` was already computed per run and then thrown away, so the
    #: real number was one line away the whole time. ‼ CLAUDE.md rule 7 — instrument the ACTION, not
    #: the input to it: an inferred cumulative is an input, a `seen_maps` hit is the action.
    reached = collections.Counter()
    league_hits = []
    per_lane = collections.Counter()

    for lane, stamp, log in runs:
        per_lane[lane] += 1
        seen_maps, last_frame, wo, dex, lvl = set(), 0, 0, 0, 0
        seen_sigs = set()
        with log.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = _FRAME.match(line)
                if m:
                    last_frame = int(m.group(1))
                d = _DERAIL.search(line)
                if d:
                    sig = _signature(d.group(1))
                    derails[sig] += 1
                    seen_sigs.add(sig)
                if _WHITEOUT.search(line):
                    wo += 1
                mm = _MAPTO.search(line) or _HBMAP.search(line)
                if mm:
                    seen_maps.add(mm.group(1).strip())
                o = _OWNED.search(line)
                if o:
                    dex = max(dex, int(o.group(1)))
                for lv in _LEVELS.findall(line):
                    lvl = max(lvl, int(lv))
        for sig in seen_sigs:
            derail_runs[sig] += 1
        whiteouts.append(wo)
        frames.append(last_frame)
        owned_max.append(dex)
        lvl_max.append(lvl)

        best = "(none)"
        for key, name in MILESTONES:
            if any(name in m for m in seen_maps):
                best = key
                reached[key] += 1
        furthest[best] += 1
        hit = [m for m in seen_maps if any(k in m for k in LEAGUE_INTERIOR)]
        if hit:
            league_hits.append((lane, stamp, sorted(hit)))

    print(f"  runs per lane: {dict(per_lane)}")
    tot = sum(frames)
    print(f"  total frames : {tot:,}  (~{tot/60/60/60:.1f} emulated hours at 60fps)")
    print(f"  frames/run   : median {sorted(frames)[len(frames)//2]:,}  max {max(frames):,}")
    print(f"  whiteouts    : total {sum(whiteouts)}, median/run {sorted(whiteouts)[len(whiteouts)//2]}, max {max(whiteouts)}")
    print(f"  dex owned    : median {sorted(owned_max)[len(owned_max)//2]}, max {max(owned_max)}")
    print(f"  party max lvl: median {sorted(lvl_max)[len(lvl_max)//2]}, max {max(lvl_max)}")

    print("\n  FURTHEST MILESTONE *REACHED* PER RUN  (⛔ reached != gym cleared):")
    for key, _name in MILESTONES:
        n = furthest.get(key, 0)
        if n:
            print(f"      {key:<14} {n:>4}  ({n/len(runs)*100:5.1f}%)  {'#' * min(40, n)}")
    if furthest.get("(none)"):
        print(f"      {'(none)':<14} {furthest['(none)']:>4}")

    print("\n  REACHED — runs whose log ACTUALLY NAMES this map  (MEASURED, not inferred):")
    print("      ‼ Quote THIS row. The assumed-roll-up beside it is kept only so the two can be")
    print("        compared; where they disagree, the MEASURED one is right by construction.")
    cum = 0
    order = [k for k, _ in MILESTONES]
    roll = {}
    for key in reversed(order):
        cum += furthest.get(key, 0)
        roll[key] = cum
    for key in order:
        meas, assumed = reached.get(key, 0), roll.get(key, 0)
        flag = "" if meas == assumed else f"   ← ‼ DISAGREES by {meas - assumed:+d}"
        print(f"      {key:<14} MEASURED {meas:>4} ({meas/len(runs)*100:5.1f}%)   "
              f"assumed-roll-up {assumed:>4} ({assumed/len(runs)*100:5.1f}%){flag}")
    print("      ⛔ 'reached' means the map was LOADED — never that its gym was cleared.")

    print("\n  ⛔ FALSIFICATION ARM — did ANY run enter a League INTERIOR map?")
    if league_hits:
        print(f"      *** {len(league_hits)} RUN(S) DID. The 'no run can reach the Elite Four' claim")
        print("      *** is REFUTED and must be retracted, not explained away:")
        for lane, stamp, hit in league_hits[:10]:
            print(f"          {lane} {stamp}: {hit}")
    else:
        print("      none — consistent with §Ch24 being unwired in story_mode.py.")
        print("      ‼ CONSISTENT WITH, NOT PROOF OF: this shows the interior was never entered,")
        print("        not WHY. The cause is still the missing Segment 24 dispatch.")

    print(f"\n  TOP DERAIL SIGNATURES  ({sum(derails.values())} derails total):")
    print(f"      {'runs':>5} {'total':>6}  signature")
    for sig, n in derails.most_common(18):
        print(f"      {derail_runs[sig]:>5} {n:>6}  {sig}")
    print(bar)


def self_test() -> int:
    """FAULT ARMS. ⛔ A report that cannot be wrong is not a measurement."""
    bar = "=" * 92
    print(bar)
    print("SELF-TEST — analyze_endless_batch.py")
    print(bar)
    fails = []

    cases = [
        ("signature strips coordinates",
         _signature("Could not reach (25, 55) on ROUTE111 from (47, 9)"),
         "Could not reach (x,y) on ROUTE111 from (x,y)"),
        ("signature strips counts but KEEPS map names",
         _signature("nothing progressed for 18,000 frames on FallarborTown"),
         "nothing progressed for N frames on FallarborTown"),
    ]
    for name, got, want in cases:
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}\n          got={got!r}")
        if not ok:
            fails.append(name)
            print(f"          want={want!r}")

    # ⛔ THE ARM THAT MATTERS: two DIFFERENT map names must NOT collapse to one signature. If they
    #   did, the report would merge distinct defects and under-count the worst one.
    a = _signature("the walk to FallarborTown is BLOCKED")
    b = _signature("the walk to MauvilleCity is BLOCKED")
    ok = a != b
    print(f"  {'PASS' if ok else 'FAIL'}  distinct map names stay DISTINCT signatures")
    if not ok:
        fails.append("map names collapsed")

    # ⛔ And the inverse: the SAME defect with different numbers MUST collapse, or the top-N list
    #   fragments into noise and the real leader is invisible.
    c = _signature("DERAIL: nothing progressed for 18,000 frames")
    d = _signature("DERAIL: nothing progressed for 9,000 frames")
    ok = c == d
    print(f"  {'PASS' if ok else 'FAIL'}  same defect, different numbers, COLLAPSES to one signature")
    if not ok:
        fails.append("numbers did not collapse")

    # ⛔ The LEAGUE_INTERIOR arm must fire on an interior map and NOT on the outdoor city.
    ok = (any(k in "EVER GRANDE CITY POKEMON LEAGUE" for k in LEAGUE_INTERIOR)
          and not any(k in "EVER GRANDE CITY" for k in LEAGUE_INTERIOR))
    print(f"  {'PASS' if ok else 'FAIL'}  league-interior detector fires on the LEAGUE, not on the CITY")
    if not ok:
        fails.append("league detector wrong")

    # ⛔⛔ THE ARM FOR THE 2026-09-16 CUMULATIVE FIX. A MEASURED cumulative and an ASSUMED-ORDER
    #   roll-up are only worth printing side by side if they CAN differ — otherwise the new row is
    #   decoration, and a reader would read their agreement as corroboration when it is tautology.
    #   This builds the run the roll-up cannot see: one that loaded LITTLEROOT and MOSSDEEP and
    #   nothing between. The roll-up walks back from furthest=mossdeep and therefore CLAIMS a
    #   Lavaridge visit; MEASURED says 0, because no log line ever named Lavaridge.
    _seen = {"LITTLEROOT TOWN", "MOSSDEEP CITY"}
    _reached = {k for k, name in MILESTONES if any(name in m for m in _seen)}
    _best = [k for k, name in MILESTONES if any(name in m for m in _seen)][-1]
    _roll, _c = {}, 0
    for k in reversed([k for k, _ in MILESTONES]):
        _c += 1 if k == _best else 0
        _roll[k] = _c
    ok = ("lavaridge" not in _reached) and _roll["lavaridge"] == 1
    print(f"  {'PASS' if ok else 'FAIL'}  MEASURED and ASSUMED cumulatives DISAGREE on a skipping run")
    print(f"          lavaridge: measured={'lavaridge' in _reached}  assumed={_roll['lavaridge']}")
    if not ok:
        fails.append("cumulative arms cannot disagree — the MEASURED row would prove nothing")

    print()
    if fails:
        print(f"  ⛔ {len(fails)} arm(s) FAILED: {fails}")
        print(bar)
        return 1
    print("  ✅ all arms behaved.")
    print(bar)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="20260915")
    ap.add_argument("--until", default="20260916")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    report(analyse(args.since, args.until))
    return 0


if __name__ == "__main__":
    sys.exit(main())
