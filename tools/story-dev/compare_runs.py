"""CROSS-REFERENCE RUN LOGS — cluster failures by signature across many runs.

WHY THIS EXISTS. The single most productive debugging move in this project has been comparing
two run logs and noticing they died the SAME way: Route 111 (18,99) killed four runs across two
machines, and it was only identifiable once two independent logs were put side by side. Doing
that by eye works for two logs. It does not work for seven, and it silently misses the case
where two runs die at the same TILE but in different FUNCTIONS (or vice versa) — which is
exactly the distinction that told us the (18,99) wedge was a stale reader rather than a
navigation bug.

So: extract a normalised signature from each log and GROUP BY IT. A cluster of size >= 2 across
DIFFERENT machines or starters is the strongest evidence this project has ever acted on.

Handles BOTH log formats:
  * the harness (`tools/story-dev/story_harness.py`) — `f<N>: ...`, `[done] ran ...`,
    `gen -> func @ file:line`, `NO-PROGRESS`;
  * the in-game debug logger (`<profile>/debug-logs/*.log`) — `===== DUMP ... =====` blocks with
    `map=`, `pos=`, `scripts=`, `generator call stack`.
The two carry different fields (the in-game one has `scripts=`, which is what cracked Route 111),
so the report says which fields were actually available per log rather than pretending they match.

    py -3.12 tools/story-dev/compare_runs.py tools/story-dev/night5/*.log
    py -3.12 tools/story-dev/compare_runs.py --label mine tools/story-dev/night5/*.log \
                                             --label user ~/Downloads/Story_DEBUG*.log
"""

import argparse
import pathlib
import re
import sys
from collections import defaultdict

# --- extraction ---------------------------------------------------------------------------

RE_DONE = re.compile(r"\[done\] ran ([\d,]+) frames")
RE_HANG = re.compile(r"HANG CONFIRMED \((\d+) frames")
RE_GEN = re.compile(r"gen -> ([A-Za-z_][\w.]*(?:\.[\w<>]+)*)\s+@\s+([\w./\\-]+):(\d+)")
RE_GEN2 = re.compile(r"->\s+([A-Za-z_][\w.]*)\s+@\s+([\w./\\-]+):(\d+)")  # in-game dump style
RE_POS = re.compile(r"map=([A-Z0-9 .]+?)\(([\d,\s]+)\)\s+pos=\((\d+),\s*(\d+)\)")
RE_POS2 = re.compile(r"POS ([A-Z0-9 .]+?) \(([\d,\s]+)\)\s+local=\((-?\d+),\s*(-?\d+)\)")
RE_SIGPOS = re.compile(r"sig=\([^)]*\((\d+),\s*(\d+)\)\)")
RE_SCRIPTS = re.compile(r"scripts=(\[[^\]]*\])")
RE_PARTY = re.compile(r"party=\[([^\]]*)\]")
RE_MSG = re.compile(r"(?:message|msg)='([^']{0,90})")

FAIL_MARKERS = [
    ("movelearn-stall", "Move-learn dialogue could not be resolved"),
    ("whiteout-cap", "too many whiteout recoveries"),
    ("nopp-loop", "BattleScript_SelectingMoveWithNoPP"),
    ("watchdog", "global watchdog"),
    ("facing", "could not face"),
    ("nav-stuck", "NavigationStuckError"),
    ("no-path", "Could not find a path"),
    ("hang", "HANG CONFIRMED"),
    ("traceback", "Traceback (most recent call last)"),
]

MILESTONES = [
    ("content-end", "end of built content"),
    ("badge6", "FEATHER BADGE"),
    ("badge5", "BALANCE BADGE"),
    ("badge4", "HEAT BADGE"),
]


def summarise(path: pathlib.Path, label: str) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    frames = 0
    m = RE_DONE.search(text)
    if m:
        frames = int(m.group(1).replace(",", ""))
    else:
        h = RE_HANG.search(text)
        if h:
            frames = int(h.group(1))

    # Failure kind: FIRST marker in the list order (most specific first), not first in the file —
    # a run often trips several, and the specific one is the diagnosis.
    fail = "clean/unknown"
    for name, needle in FAIL_MARKERS:
        if needle in text:
            fail = name
            break

    depth = "start"
    for name, needle in MILESTONES:
        if needle in text:
            depth = name
            break

    # Deepest generator frame near the END of the log = where it actually died.
    # ‼ WIDEN THE WINDOW UNTIL SOMETHING IS FOUND. A fixed 400-line tail reported `where=?`
    # for every move-learn stall, because that failure drops the bot to Manual and then emits
    # hundreds of heartbeat lines before the harness gives up — pushing the last real
    # generator stack far outside the window. Reporting `?` there is worse than useless: it
    # made three runs that died the SAME way look like they had nothing in common on the
    # "dying function" axis, which is precisely the clustering this tool exists to do.
    tail = ""
    gens: list = []
    for window in (400, 2000, 10000, len(lines) + 1):
        tail = "\n".join(lines[-window:])
        gens = RE_GEN.findall(tail) or RE_GEN2.findall(tail)
        if gens:
            break
    where = f"{gens[-1][0]} @ {pathlib.Path(gens[-1][1]).name}:{gens[-1][2]}" if gens else "?"
    stack = [g[0] for g in gens[-6:]]

    # ‼ REJECT OBVIOUSLY-BOGUS POSITIONS. Three real logs reported
    # `LITTLEROOT TOWN (-7,-7)` while the party was deep in the mid-game: negative locals are
    # the signature of an uninitialised/stale map read (the raw RAM value minus 7 when the
    # value is 0), not a place the player was. Left unguarded, the clustering below groups
    # three unrelated runs on a meaningless "location" and sends the reader to Littleroot.
    # A stale reader that LOOKS like data is this project's most repeated trap — so say
    # "unreliable" instead of inventing a tidy answer.
    def _pick_loc(text_block: str) -> str:
        for rx in (RE_POS, RE_POS2):
            for m_ in reversed(list(rx.finditer(text_block))):
                x, y = int(m_.group(3)), int(m_.group(4))
                if x >= 0 and y >= 0:
                    return f"{m_.group(1).strip()} ({x},{y})"
        sp_ = RE_SIGPOS.search(text_block)
        if sp_:
            return f"?({sp_.group(1)},{sp_.group(2)})"
        any_neg = RE_POS.search(text_block) or RE_POS2.search(text_block)
        return "unreliable(stale/negative read)" if any_neg else "?"

    loc = _pick_loc(tail)

    sc = RE_SCRIPTS.findall(tail)
    scripts = sc[-1] if sc else "(field absent)"
    pt = RE_PARTY.findall(tail)
    party = pt[-1][:70] if pt else "?"
    mg = RE_MSG.findall(tail)
    msg = mg[-1] if mg else ""

    return {
        "label": label, "file": path.name, "frames": frames, "fail": fail, "depth": depth,
        "where": where, "loc": loc, "scripts": scripts, "party": party, "msg": msg,
        "stack": stack,
        "whiteouts": text.count("whiteout") + text.count("Whiteout"),
        "derails": text.count("DERAIL") + text.count("BotModeError"),
        "has_scripts_field": "scripts=" in text,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("logs", nargs="*", type=pathlib.Path)
    ap.add_argument("--label", action="append", default=[],
                    help="label the logs that FOLLOW it (e.g. --label mine a.log --label user b.log)")
    args, extra = ap.parse_known_args()

    # Interleave --label with positional groups: rebuild from argv so ordering is preserved.
    groups: list[tuple[str, list[pathlib.Path]]] = []
    cur_label = "run"
    for tok in sys.argv[1:]:
        if tok == "--label":
            cur_label = None
            continue
        if cur_label is None:
            cur_label = tok
            continue
        p = pathlib.Path(tok)
        if p.exists():
            if not groups or groups[-1][0] != cur_label:
                groups.append((cur_label, []))
            groups[-1][1].append(p)
    if not groups:
        ap.error("no readable log files given")

    rows = [summarise(p, lab) for lab, ps in groups for p in ps]

    print("=" * 118)
    print(f"{'label':6} {'log':26} {'frames':>10}  {'depth':12} {'failure':16} where / location")
    print("=" * 118)
    for r in sorted(rows, key=lambda r: -r["frames"]):
        print(f"{r['label']:6} {r['file'][:26]:26} {r['frames']:>10,}  {r['depth']:12} "
              f"{r['fail']:16} {r['where']}")
        print(f"{'':6} {'':26} {'':>10}  loc={r['loc']}  scripts={r['scripts'][:56]}")
        if r["msg"]:
            print(f"{'':6} {'':26} {'':>10}  msg={r['msg'][:88]}")

    # --- the point of the tool: cluster by signature -------------------------------------
    print("\n" + "=" * 118)
    print("CLUSTERS — a group of >= 2 spanning different labels/starters is the strongest signal")
    print("=" * 118)
    for keyname, keyfn in (
        ("failure kind", lambda r: r["fail"]),
        ("dying function", lambda r: r["where"]),
        ("location", lambda r: r["loc"]),
        ("failure+location", lambda r: f"{r['fail']} @ {r['loc']}"),
    ):
        buckets: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            buckets[keyfn(r)].append(r)
        multi = {k: v for k, v in buckets.items() if len(v) >= 2 and k not in ("?", "clean/unknown")}
        print(f"\nby {keyname}:")
        if not multi:
            print("   (no cluster — every run differs on this axis)")
        for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1])):
            labels = sorted({r["label"] for r in v})
            cross = "  <<< SPANS LABELS" if len(labels) > 1 else ""
            print(f"   {len(v)}x  {k}{cross}")
            for r in v:
                print(f"        {r['label']}/{r['file'][:30]}  {r['frames']:,}f")

    missing = [r["file"] for r in rows if not r["has_scripts_field"]]
    if missing:
        print(f"\nNOTE: {len(missing)} log(s) carry NO `scripts=` field, so a parked-field-script "
              f"cause cannot be seen in them: {', '.join(m[:24] for m in missing[:4])}")
        print("      The in-game debug logger records it; the harness only does since 2026-07-24.")

    print(f"\nattrition: " + ", ".join(
        f"{r['label']}/{r['file'][:18]} wo={r['whiteouts']} derails={r['derails']}" for r in rows))


if __name__ == "__main__":
    main()
