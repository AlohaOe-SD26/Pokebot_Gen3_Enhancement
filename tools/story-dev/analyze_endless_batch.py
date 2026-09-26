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
    PYTHONUTF8=1 py -3.12 analyze_endless_batch.py                 # the 2026-09-15/16 batch (the defaults)
    ⚠ For any OTHER batch pass --since/--until (YYYYMMDD). Reads debug-logs/ AND debug-logs/Old/.
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
#:
#: ⛔⛔ EACH ENTRY IS (key, map-section NAME, allowed (group, number) ids or None). FIXED 2026-09-26:
#: (1) THE ORDER WAS WRONG — `victory_road` sat BEFORE `ever_grande`, but the bot surfs into Ever
#:     Grande's SOUTH side first and only then enters Victory Road; "furthest" was mis-ranked.
#: (2) THE LEAGUE COULD NEVER BE SEEN BY NAME. The logger prints the REGION-MAP SECTION name, and every
#:     League room, the Hall of Fame and the Ever Grande Poké Center are all `MAPSEC_EVER_GRANDE_CITY`
#:     (decomp) ⇒ they print as `EVER GRANDE CITY(16,N)`. So the end-game milestones key on the
#:     (group, number) id — AND on the name, because a mid-warp read can print a WRONG name beside a
#:     League-shaped id (seen in the 2026-09-15 corpus: `ROUTE 102(16,0)` etc.). Name AND id, never id alone.
MILESTONES = [
    ("littleroot", "LITTLEROOT TOWN", None),
    ("rustboro", "RUSTBORO CITY", None),
    ("dewford", "DEWFORD TOWN", None),
    ("slateport", "SLATEPORT CITY", None),
    ("mauville", "MAUVILLE CITY", None),
    ("lavaridge", "LAVARIDGE TOWN", None),
    ("fortree", "FORTREE CITY", None),
    ("lilycove", "LILYCOVE CITY", None),
    ("mossdeep", "MOSSDEEP CITY", None),
    ("sootopolis", "SOOTOPOLIS CITY", None),
    ("ever_grande", "EVER GRANDE CITY", {(0, 8)}),                     # the OUTDOOR map (south side first)
    ("victory_road", "VICTORY ROAD", {(24, 43), (24, 44), (24, 45)}),
    ("league_lobby", "EVER GRANDE CITY", {(16, 10), (16, 14)}),        # POKEMON_LEAGUE_1F / 2F
    ("elite_four", "EVER GRANDE CITY", {(16, 0)}),                     # SIDNEY'S ROOM — past the point of no return
    ("champion", "EVER GRANDE CITY", {(16, 4)}),                       # CHAMPION'S ROOM
    ("hall_of_fame", "EVER GRANDE CITY", {(16, 11)}),
]

#: A run whose debug log carries this `[STORY]` line CLEARED THE GAME (`story_mode.py` logs it only
#: after `run_the_gauntlet` returns, which raises unless IS_CHAMPION and SYS_GAME_CLEAR are both set).
CLEARED_MARKER = "§Ch24 COMPLETE"

#: ⛔ AN ID-KEYED MILESTONE NEEDS THIS MANY SIGHTINGS (review 2026-09-26). The logger reads the map
#: NAME from the current header and the (group, number) from SaveBlock1 — two memory sources — so a
#: mid-warp frame can pair a name with the WRONG id (the corpus holds `GRANITE CAVE(16,0)` and
#: `ROUTE 102(16,0)`). Name AND id already rejects those; a single frame that happens to pair the
#: RIGHT name with a League id would still slip through. A real visit logs a map load AND heartbeats
#: (every ~3,600 frames; even the Hall of Fame's ~10k-frame credits give several), so 2 costs nothing.
MIN_ID_SIGHTINGS = 2

#: ⛔ THE FALSIFICATION TEST. The handoff claims no run can reach the Elite Four because §Ch24 is
#: not wired into `story_mode.py`. That is a CLAIM, and this is the arm that could refute it: if any
#: log shows a League INTERIOR map, the claim is wrong and must be retracted rather than defended.
#: Ever Grande CITY is the outdoor map and does NOT count — the door apron is outside.
#: ⛔ RETIRED 2026-09-26 as a NAME list — it could never fire (see MILESTONES). Kept as the id set.
LEAGUE_INTERIOR_IDS = {(16, n) for n in range(0, 12)} | {(16, 14)}   # every League map; NOT (16,12)/(16,13), the PC

_FRAME = re.compile(r"^f(\d+) ")
_DERAIL = re.compile(r"\[STORY\] DERAIL #\d+: (.*)")
_WHITEOUT = re.compile(r"\[STORY\] WHITEOUT recovery #(\d+)")
_MAPTO = re.compile(r"\[MAP\] .*? -> ([A-Z0-9 '.]+)\((\d+),\s*(\d+)\)")
_HBMAP = re.compile(r"\[hb\] .*? map=([A-Z0-9 '.]+)\((\d+),\s*(\d+)\)")
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


def _map_hits(line: str):
    """(NAME, (group, number)) for a map-load or heartbeat line, else None."""
    mm = _MAPTO.search(line) or _HBMAP.search(line)
    if not mm:
        return None
    return mm.group(1).strip(), (int(mm.group(2)), int(mm.group(3)))


def _milestones_reached(seen) -> list:
    """Milestone keys whose NAME and id (when given) appear in `seen`.

    `seen` maps (name, (g, n)) -> sighting count (a Counter). An id-keyed milestone needs
    `MIN_ID_SIGHTINGS`; a name-only town needs one.
    """
    out = []
    for key, name, ids in MILESTONES:
        if any(name in n and (ids is None or (gid in ids and c >= MIN_ID_SIGHTINGS))
               for (n, gid), c in seen.items()):
            out.append(key)
    return out


def _league_hits(seen) -> list:
    return sorted(f"{n}{gid}" for (n, gid), c in seen.items()
                  if "EVER GRANDE CITY" in n and gid in LEAGUE_INTERIOR_IDS and c >= MIN_ID_SIGHTINGS)


def _seen_from_lines(lines) -> "collections.Counter":
    seen = collections.Counter()
    for line in lines:
        hit = _map_hits(line)
        if hit:
            seen[hit] += 1
    return seen


def analyse(since: str, until: str):
    lanes = sorted(p for p in PROFILES.glob("endless-P*") if p.is_dir())
    runs = []
    for lane in lanes:
        logs = {q.name: q for q in (lane / "debug-logs").glob("*.log")}
        logs.update({q.name: q for q in (lane / "debug-logs" / "Old").glob("*.log")})
        for log in (logs[k] for k in sorted(logs)):
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
        seen_maps, last_frame, wo, dex, lvl, cleared = collections.Counter(), 0, 0, 0, 0, False
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
                hit = _map_hits(line)
                if hit:
                    seen_maps[hit] += 1
                if CLEARED_MARKER in line:
                    cleared = True
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
        for key in _milestones_reached(seen_maps):
            best = key
            reached[key] += 1
        if cleared:
            reached["cleared"] += 1
        furthest[best] += 1
        hit = _league_hits(seen_maps)
        if hit:
            league_hits.append((lane, stamp, hit))

    print(f"  runs per lane: {dict(per_lane)}")
    tot = sum(frames)
    print(f"  total frames : {tot:,}  (~{tot/60/60/60:.1f} emulated hours at 60fps)")
    print(f"  frames/run   : median {sorted(frames)[len(frames)//2]:,}  max {max(frames):,}")
    print(f"  whiteouts    : total {sum(whiteouts)}, median/run {sorted(whiteouts)[len(whiteouts)//2]}, max {max(whiteouts)}")
    print(f"  dex owned    : median {sorted(owned_max)[len(owned_max)//2]}, max {max(owned_max)}")
    print(f"  party max lvl: median {sorted(lvl_max)[len(lvl_max)//2]}, max {max(lvl_max)}")

    print("\n  FURTHEST MILESTONE *REACHED* PER RUN  (⛔ reached != gym cleared):")
    for key, _name, _ids in MILESTONES:
        n = furthest.get(key, 0)
        if n:
            print(f"      {key:<14} {n:>4}  ({n/len(runs)*100:5.1f}%)  {'#' * min(40, n)}")
    if furthest.get("(none)"):
        print(f"      {'(none)':<14} {furthest['(none)']:>4}")

    print("\n  REACHED — runs whose log ACTUALLY NAMES this map  (MEASURED, not inferred):")
    print("      ‼ Quote THIS row. The assumed-roll-up beside it is kept only so the two can be")
    print("        compared; where they disagree, the MEASURED one is right by construction.")
    cum = 0
    order = [k for k, _n, _i in MILESTONES]
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
    print(f"      cleared        MEASURED {reached.get('cleared', 0):>4}  (debug log carries '{CLEARED_MARKER}')")

    print("\n  LEAGUE INTERIOR — runs that loaded a League map (name EVER GRANDE CITY and group 16, not the PC):")
    if league_hits:
        print(f"      {len(league_hits)} run(s):")
        for lane, stamp, hit in league_hits[:10]:
            print(f"          {lane} {stamp}: {hit}")
    else:
        print("      none.")
        print("      ⚠ Before 2026-09-26 this arm matched NAMES the logger never prints, so its")
        print("        historical 'none' proved nothing. It now keys on name AND (group, number).")

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

    # ⛔⛔ REWRITTEN 2026-09-26. The old arm tested the synthetic string "EVER GRANDE CITY POKEMON
    #   LEAGUE", which NO log line can contain, so it passed while the detector could never fire. These
    #   arms feed REAL line shapes through the SAME parser the report uses.
    real = [   # a REAL visit is seen more than once: a map load plus heartbeats
        "f100 [MAP] EVER GRANDE CITY(16,4) -> EVER GRANDE CITY(16,11) pos=(7, 16)",
        "f103 [hb] mode=Story state=7 controllable=False map=EVER GRANDE CITY(16,11) pos=(7, 12) party=[]",
        "f101 [hb] mode=Story state=7 controllable=True map=EVER GRANDE CITY(16,10) pos=(9, 3) party=[]",
        "f102 [hb] mode=Story state=7 controllable=True map=EVER GRANDE CITY(16,10) pos=(9, 2) party=[]",
    ]
    decoys = [
        "f200 [MAP] EVER GRANDE CITY(0,8) -> EVER GRANDE CITY(16,12) pos=(7, 8)",     # the Poke Center
        "f201 [MAP] ROUTE 102(0,0) -> ROUTE 102(16,0) pos=(3, 3)",                     # mid-warp mis-read
        "f202 [hb] mode=Story state=7 controllable=True map=EVER GRANDE CITY(0,8) pos=(18, 42) party=[]",
        "f203 [hb] mode=Story state=7 controllable=True map=EVER GRANDE CITY(0,8) pos=(18, 43) party=[]",
        # ⛔ the review's residual: the RIGHT name beside a League id on ONE transient frame
        "f204 [MAP] EVER GRANDE CITY(0,8) -> EVER GRANDE CITY(16,0) pos=(18, 42)",
    ]
    seen_real = _seen_from_lines(real)
    seen_decoy = _seen_from_lines(decoys)
    got_real = set(_milestones_reached(seen_real))
    got_decoy = set(_milestones_reached(seen_decoy))
    ok = bool({"hall_of_fame", "league_lobby"} <= got_real and _league_hits(seen_real)
              and not ({"league_lobby", "elite_four", "champion", "hall_of_fame"} & got_decoy)
              and not _league_hits(seen_decoy) and "ever_grande" in got_decoy)
    print(f"  {'PASS' if ok else 'FAIL'}  real League lines fire; the PC, mid-warp mis-reads (incl. ONE right-name frame) and the outdoor city do NOT")
    print(f"          real={sorted(got_real)} decoy={sorted(got_decoy)}")
    if not ok:
        fails.append("league detector wrong on real line shapes")
    # ⛔ The `cleared` marker must match the REAL line and not a lookalike (review 2026-09-26).
    real_clear = "f900 [STORY] Story: §Ch24 COMPLETE — the game is cleared. end_at=((16, 11), (7, 16)) pairs=[]"
    lookalike = "f901 [STORY] §Ch24 champion: the post-battle chain did not reach the Hall of Fame"
    ok = CLEARED_MARKER in real_clear and CLEARED_MARKER not in lookalike
    print(f"  {'PASS' if ok else 'FAIL'}  the cleared marker matches the real completion line, not a §Ch24 failure line")
    if not ok:
        fails.append("cleared marker")
    _keys = [k for k, _n, _i in MILESTONES]
    ok = _keys.index("ever_grande") < _keys.index("victory_road")
    print(f"  {'PASS' if ok else 'FAIL'}  milestone ORDER: Ever Grande (south) before Victory Road")
    if not ok:
        fails.append("milestone order")

    # ⛔⛔ THE ARM FOR THE 2026-09-16 CUMULATIVE FIX. A MEASURED cumulative and an ASSUMED-ORDER
    #   roll-up are only worth printing side by side if they CAN differ — otherwise the new row is
    #   decoration, and a reader would read their agreement as corroboration when it is tautology.
    #   This builds the run the roll-up cannot see: one that loaded LITTLEROOT and MOSSDEEP and
    #   nothing between. The roll-up walks back from furthest=mossdeep and therefore CLAIMS a
    #   Lavaridge visit; MEASURED says 0, because no log line ever named Lavaridge.
    _seen = collections.Counter({("LITTLEROOT TOWN", (0, 9)): 1, ("MOSSDEEP CITY", (0, 6)): 1})
    _reached = set(_milestones_reached(_seen))
    _best = _milestones_reached(_seen)[-1]
    _roll, _c = {}, 0
    for k in reversed([k for k, _n, _i in MILESTONES]):
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
