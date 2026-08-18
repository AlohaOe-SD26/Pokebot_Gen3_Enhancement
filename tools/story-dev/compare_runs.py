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

‼ SECOND MODE, added 2026-08-17 — GRADING AN A/B MATRIX (`#24-orphans` (5)).
Give each ARM its own `--label` and the report ends with an `A/B DISCRIMINATION` section that
says, in as many words, whether the arms came out DIFFERENT:

    py -3.12 compare_runs.py --label armA <faulted>.log --label armB <unfaulted>.log
    py -3.12 compare_runs.py --label b-coup <...> --label b-deco <...> \
                             --label a-coup <...> --label a-deco <...>     # the 2x2 matrix

⛔ READ THE A/B SECTION, NOT THE CLUSTERS, WHEN YOU ARE GRADING ARMS. The clusters answer
"did these runs die the same way?"; `<<< SPANS LABELS` is the strongest AGREEMENT signal this
tool emits, which is the WRONG-SIGNED answer to "did my fix change anything?". Measured: the
two committed withdraw-verdict arms (`ACCEPTANCE: FAIL` vs `PASS`) clustered together on all
four original axes, because a focused driver's log always ends `HANG CONFIRMED` and never
reaches the milestones that outrank it. Evidence + four fault tests:
`evidence/2026-08-17-compareruns-abaxis-FAULT-TESTS.stdout.txt`.
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

# ‼ THE A/B AXIS — added 2026-08-17 (`#24-orphans` (5)), and it was added because the tool was
# MEASURED BLIND, not because it looked like a nice extra.
#
# `#24-orphans` (5) asked for "`compare_runs.py` pairing for the (P4) matrix" — feed the four
# {ARM A, ARM B} x {sandbox, custom} transcripts through this tool. Doing exactly that on the two
# committed withdraw-verdict arms produced a cluster of size 2 on ALL FOUR axes, every one tagged
# `<<< SPANS LABELS`, i.e. the strongest "these runs are the same" signal this tool can emit.
# The arms are NOT the same: one is `ACCEPTANCE: FAIL`, the other `ACCEPTANCE: PASS`.
#
# WHY it was blind: every axis here is FAILURE-shaped, and this tool was built for cross-machine
# CRASH clustering, where the arms-differ question never arises. Both A/B arms legitimately end
# with `HANG CONFIRMED` (the harness's own end-of-run marker — see the SUCCESS-outranks note in
# `summarise`, which only exempts runs that reach `content-end`/`badge6`; a focused driver reaches
# neither). So the failure axis is CONSTANT across arms by construction, and the one field that
# actually separates them was not parsed at all.
#
# ⇒ Delivering the requested "pairing" without this axis would have produced a report reading
# "the arms agree" over a matrix whose whole purpose is to show they disagree. That is this
# project's most repeated failure shape (an instrument that cannot see what it is pointed at),
# so the fix is an axis, not a wrapper script.
#
# `ACCEPTANCE: <VERDICT>` is the house verdict token: it appears in 53 of the 65 committed
# evidence transcripts, only ever as PASS or FAIL. A run may print several (a multi-stage driver
# grades each stage), so keep them ALL, in order — collapsing them to the last one would hide a
# driver whose Stage 1 failed and whose Stage 2 passed.
RE_ACCEPT = re.compile(r"ACCEPTANCE:\s*([A-Z]+)")

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
    ("content-end", "RUN COMPLETE"),
    ("badge6", "FEATHER BADGE"),
    ("badge5", "BALANCE BADGE"),
    ("badge4", "HEAT BADGE"),
]



def _safe_print(text: str = "") -> None:
    """Print that survives a cp1252 console.

    ‼ The Windows console is cp1252 and run logs are full of em dashes and arrows from
    `context.message`. A bare print() raises UnicodeEncodeError mid-report and takes the
    whole comparison down — which is exactly how gemini_relay.py destroyed two paid-for API
    responses before it was fixed the same way. An analysis tool must never lose its output
    to the terminal it is printing to.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        import sys as _s

        _s.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        _s.stdout.buffer.write(b"\n")


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

    depth = "start"
    for name, needle in MILESTONES:
        if needle in text:
            depth = name
            break

    # ‼ SUCCESS OUTRANKS EVERYTHING, AND FAILURES ARE JUDGED FROM THE TAIL.
    # Two bugs the first version had, both of which would have corrupted a cross-machine
    # comparison in opposite directions:
    #  1. A run that reached "end of built content" was labelled `no-path`, because a
    #     TRANSIENT, RECOVERED "Could not find a path" appeared somewhere earlier in the log.
    #     Scanning the whole file for failure markers means any hiccup a run survived becomes
    #     its verdict — so a SUCCESS was filed as a failure.
    #  2. A successful run still ends with "HANG CONFIRMED", because the bot prints
    #     "end of built content — handing to manual" and then idles until the frame-based
    #     detector fires 20,000 frames later. That trailing hang is an artefact of finishing,
    #     not a failure (see #24-harness-finish).
    # So: if the run reached the end of built content or won the Feather Badge, it SUCCEEDED.
    # Otherwise prefer a marker in the TAIL (the terminal failure) and only fall back to the
    # whole log with an explicit "earlier" tag, so a recovered hiccup can never masquerade as
    # the cause of death.
    tail_for_fail = "\n".join(lines[-600:])
    if depth in ("content-end", "badge6"):
        fail = "SUCCESS"
    else:
        fail = "clean/unknown"
        for name, needle in FAIL_MARKERS:
            if needle in tail_for_fail:
                fail = name
                break
        else:
            for name, needle in FAIL_MARKERS:
                if needle in text:
                    fail = f"{name}?earlier"
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

    # ‼ Scan the WHOLE text, not the tail: a multi-stage driver grades Stage 1 thousands of lines
    # before it grades Stage 2, and the tail window would silently drop the earlier verdicts.
    # `(field absent)` is deliberately NOT spelled as a verdict — a log with no ACCEPTANCE line
    # must never be comparable-equal to one that passed.
    accepts = RE_ACCEPT.findall(text)
    accept = ",".join(accepts) if accepts else "(no verdict)"

    return {
        "label": label, "file": path.name, "frames": frames, "fail": fail, "depth": depth,
        "where": where, "loc": loc, "scripts": scripts, "party": party, "msg": msg,
        "stack": stack, "accept": accept, "n_accept": len(accepts),
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

    _safe_print("=" * 118)
    _safe_print(f"{'label':6} {'log':26} {'frames':>10}  {'accept':12} {'failure':16} where / location")
    _safe_print("=" * 118)
    for r in sorted(rows, key=lambda r: -r["frames"]):
        _safe_print(f"{r['label']:6} {r['file'][:26]:26} {r['frames']:>10,}  {r['accept'][:12]:12} "
              f"{r['fail']:16} {r['where']}")
        _safe_print(f"{'':6} {'':26} {'':>10}  depth={r['depth']}")
        _safe_print(f"{'':6} {'':26} {'':>10}  loc={r['loc']}  scripts={r['scripts'][:56]}")
        if r["msg"]:
            _safe_print(f"{'':6} {'':26} {'':>10}  msg={r['msg'][:88]}")

    # --- the point of the tool: cluster by signature -------------------------------------
    _safe_print("\n" + "=" * 118)
    _safe_print("CLUSTERS — a group of >= 2 spanning different labels/starters is the strongest signal")
    _safe_print("=" * 118)
    for keyname, keyfn in (
        ("acceptance verdict", lambda r: r["accept"]),
        ("failure kind", lambda r: r["fail"]),
        ("dying function", lambda r: r["where"]),
        ("location", lambda r: r["loc"]),
        ("failure+location", lambda r: f"{r['fail']} @ {r['loc']}"),
    ):
        buckets: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            buckets[keyfn(r)].append(r)
        multi = {k: v for k, v in buckets.items() if len(v) >= 2 and k not in ("?", "clean/unknown")}
        _safe_print(f"\nby {keyname}:")
        if not multi:
            _safe_print("   (no cluster — every run differs on this axis)")
        for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1])):
            labels = sorted({r["label"] for r in v})
            cross = "  <<< SPANS LABELS" if len(labels) > 1 else ""
            _safe_print(f"   {len(v)}x  {k}{cross}")
            for r in v:
                _safe_print(f"        {r['label']}/{r['file'][:30]}  {r['frames']:,}f")

    # --- A/B DISCRIMINATION ---------------------------------------------------------------
    # ‼ The clustering above answers "did these runs die the same way?". An A/B matrix asks the
    # OPPOSITE question — "did these arms come out DIFFERENT?" — and a cross-label cluster is the
    # WRONG-SIGNED answer to it: `<<< SPANS LABELS` reads as agreement. This section states the
    # A/B answer explicitly so nobody has to invert the report in their head.
    labels_present = sorted({r["label"] for r in rows})
    if len(labels_present) >= 2:
        _safe_print("\n" + "=" * 118)
        _safe_print("A/B DISCRIMINATION — do the LABELLED ARMS actually come out different?")
        _safe_print("=" * 118)
        per_label = {lab: sorted({r["accept"] for r in rows if r["label"] == lab}) for lab in labels_present}
        for lab in labels_present:
            _safe_print(f"   {lab:10} acceptance = {', '.join(per_label[lab])}")

        graded = [r for r in rows if r["n_accept"] > 0]
        if not graded:
            # ⛔ Never print a verdict we cannot see. A tool that says "the arms agree" when it
            # parsed nothing is worse than one that says nothing (08-MISTAKES 2026-08-17: a zero
            # from an instrument that has never produced a non-zero is not a measurement).
            _safe_print("\n   ‼ NO transcript carries an `ACCEPTANCE:` line — this tool CANNOT grade")
            _safe_print("     this comparison. Do not read the clusters above as an A/B result.")
        elif len(graded) < len(rows):
            ungraded = [r["file"] for r in rows if r["n_accept"] == 0]
            _safe_print(f"\n   ‼ {len(ungraded)} of {len(rows)} transcript(s) carry NO `ACCEPTANCE:` line, so the")
            _safe_print(f"     comparison is PARTIAL: {', '.join(f[:34] for f in ungraded[:4])}")

        # ⛔ SEPARATION IS JUDGED OVER GRADED LABELS ONLY — found by fault-testing this very
        # block on 2026-08-17. The first draft compared the raw per-label sets, so a `(no verdict)`
        # arm beside a `PASS` arm printed "✅ THE ARMS SEPARATE". That is an ABSENCE being read as
        # a value: the one thing this project has been burned by most often. An unmeasured arm
        # cannot separate from anything, and a green tick above the caveat is what a skimmer keeps.
        graded_labels = sorted({r["label"] for r in rows if r["n_accept"] > 0})
        per_label_graded = {
            lab: sorted({r["accept"] for r in rows if r["label"] == lab and r["n_accept"] > 0})
            for lab in graded_labels
        }
        distinct = {tuple(v) for v in per_label_graded.values()}
        if len(graded) and len(graded_labels) < 2:
            _safe_print(f"\n   ⛔ Only {len(graded_labels)} label carries a verdict — SEPARATION CANNOT BE JUDGED.")
            _safe_print("      An unmeasured arm does not separate from anything. Re-run the missing arm.")
        elif len(graded) and len(distinct) > 1:
            _safe_print("\n   ✅ THE ARMS SEPARATE on acceptance — the matrix is discriminating.")
            blind = []
            for keyname, keyfn in (
                ("failure kind", lambda r: r["fail"]),
                ("dying function", lambda r: r["where"]),
                ("location", lambda r: r["loc"]),
            ):
                if len({keyfn(r) for r in rows}) == 1:
                    blind.append(f"{keyname} (all = {keyfn(rows[0])!r})")
            if blind:
                _safe_print("   ⛔ BUT these axes are BLIND to that difference — they are CONSTANT across")
                _safe_print("      arms, so their `<<< SPANS LABELS` clusters above are artefacts, not agreement:")
                for b in blind:
                    _safe_print(f"        - {b}")
        elif len(graded_labels) >= 2:
            _safe_print("\n   ⛔ THE ARMS DO NOT SEPARATE on acceptance — every graded label came out the same.")
            _safe_print("      For an A/B that is either a VACUOUS FIXTURE (playbook §3b: run both arms")
            _safe_print("      BEFORE writing the fix and show they already differ) or a genuine")
            _safe_print("      no-difference result. ⛔ It is never, on its own, proof that a fix works.")

    missing = [r["file"] for r in rows if not r["has_scripts_field"]]
    if missing:
        _safe_print(f"\nNOTE: {len(missing)} log(s) carry NO `scripts=` field, so a parked-field-script "
              f"cause cannot be seen in them: {', '.join(m[:24] for m in missing[:4])}")
        _safe_print("      The in-game debug logger records it; the harness only does since 2026-07-24.")

    _safe_print(f"\nattrition: " + ", ".join(
        f"{r['label']}/{r['file'][:18]} wo={r['whiteouts']} derails={r['derails']}" for r in rows))


if __name__ == "__main__":
    main()
