r"""GRADER — USER RULING 20 Phase 2 step T (per-catch telemetry, 2026-09-28): grade a Story DEBUG LOG's `[CATCH]` lines.

WHY: every later Phase 2 arm (the ball restock, the pre-gym-1 target of 6, the open fence) is graded on these lines, so
the lines themselves must be proven honest first. A grader that only counted lines would pass a run whose `end` lines
were missing, or whose `thrown` disagreed with the bag.

Checks (each prints ok/FAIL):
  PAIR    every `[CATCH] start` is closed by exactly one `[CATCH] end` before the next start; no orphan end.
  VACUOUS zero starts = the run measured nothing: exit 2, never a pass.
  DEST    an `end=caught` names `dest=party|box` (never `?`) and an 8-hex `pid` (a `-` is reported, not failed).
  THROWN  `thrown=` equals the net drop in the independent `[BALLS] a -> b` lines between that start and its end, after
          removing warp FLICKERS (a count that jumps and returns within 3 frames — measured 17->5->17 on warps).
  HB      every `[hb]` carries `box=` and `badges=` (M3).
  ENVALL  the run header has an `env-all:` line (M5).
  REPLAY  with `--ref CONTROL_LOG`: every `[BATTLE] started` / `ended (outcome=...)` line, frame and outcome, is
          IDENTICAL to the control's (the LOG-ONLY test: telemetry must not change one battle).
Anchored on `^f<digits> \[CATCH\] (start|end) `: a `[DEXCATCH] ... start` mention, or text inside another line, can
never count.

Run:  PYTHONUTF8=1 py -3.12 grade_r20_telemetry.py LOG [--ref CONTROL_LOG]
      PYTHONUTF8=1 py -3.12 grade_r20_telemetry.py --self-test
Exit: 0 PASS, 1 FAIL, 2 VACUOUS.
"""
from __future__ import annotations

import re
import sys

LINE = re.compile(r"^f(\d+) \[([A-Za-z][\w-]*)\] (.*)$")
CATCH = re.compile(r"^f(\d+) \[CATCH\] (start|end) (.*)$")
BALLS = re.compile(r"^f(\d+) \[BALLS\] (\d+) -> (\d+)")
BATTLE = re.compile(r"^f(\d+) \[BATTLE\] (started|ended)(?: \(outcome=(\w+(?:\.\w+)?)\))?")
KV = re.compile(r"(\w+)=(\S+)")
HEX8 = re.compile(r"^[0-9A-F]{8}$")
FLICKER_FRAMES = 3


def _kv(text: str) -> dict:
    return dict(KV.findall(text))


def _net_ball_drop(events: list) -> "int | None":
    """Net drop across [BALLS] events, with flickers (a->b then b->a within FLICKER_FRAMES) removed."""
    ev = list(events)
    changed = True
    while changed:
        changed = False
        for i in range(len(ev) - 1):
            f1, a1, b1 = ev[i]
            f2, a2, b2 = ev[i + 1]
            if a2 == b1 and b2 == a1 and f2 - f1 <= FLICKER_FRAMES:
                del ev[i:i + 2]
                changed = True
                break
    if not ev:
        return 0
    return ev[0][1] - ev[-1][2]


def grade(lines: list, ref_lines: "list | None" = None, out=print) -> int:
    fails: list = []

    def check(cond, msg):
        out(f"  {'ok  ' if cond else 'FAIL'} {msg}")
        if not cond:
            fails.append(msg)

    events, balls, battles, hbs = [], [], [], []
    has_envall = any("env-all:" in ln for ln in lines)
    for ln in lines:
        ln = ln.rstrip("\r\n")
        m = CATCH.match(ln)
        if m:
            events.append((int(m.group(1)), m.group(2), _kv(m.group(3)), ln))
            continue
        m = BALLS.match(ln)
        if m:
            balls.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
            continue
        m = BATTLE.match(ln)
        if m:
            battles.append((int(m.group(1)), m.group(2), m.group(3)))
            continue
        m = LINE.match(ln)
        if m and m.group(2) == "hb":
            hbs.append(ln)

    starts = [e for e in events if e[1] == "start"]
    out(f"  [CATCH] start={len(starts)} end={len(events) - len(starts)}  [BALLS]={len(balls)}  [BATTLE]={len(battles)}")
    if not starts:
        out("  VACUOUS — zero `[CATCH] start` lines: this run measured nothing.")
        return 2

    # PAIR
    pairs, open_start, orphans_end, unclosed = [], None, 0, 0
    for ev in events:
        if ev[1] == "start":
            if open_start is not None:
                unclosed += 1
                out(f"  FAIL start without end: {open_start[3][:140]}")
            open_start = ev
        else:
            if open_start is None:
                orphans_end += 1
                out(f"  FAIL end without start: {ev[3][:140]}")
            else:
                pairs.append((open_start, ev))
                open_start = None
    if open_start is not None:
        unclosed += 1
        out(f"  FAIL start without end: {open_start[3][:140]}")
    check(unclosed == 0 and orphans_end == 0,
          f"PAIR every start has exactly one end ({unclosed} start(s) without end, {orphans_end} orphan end(s))")

    for s, e in pairs:
        kv = e[2]
        label = f"{s[2].get('kind', '?')} {s[2].get('sp', '?')} f{s[0]}->f{e[0]}"
        if kv.get("end") == "caught":
            check(kv.get("dest") in ("party", "box"), f"DEST {label}: dest={kv.get('dest')} is party|box")
            pid = kv.get("pid", "-")
            if not HEX8.match(pid):
                out(f"  note {label}: pid={pid} (not 8 hex — the new mon could not be identified)")
        th = kv.get("thrown")
        if th not in (None, "?"):
            window = [b for b in balls if s[0] < b[0] <= e[0]]
            net = _net_ball_drop(window)
            check(str(net) == th, f"THROWN {label}: thrown={th} vs [BALLS] net drop {net}")

    check(all("box=" in h and "badges=" in h for h in hbs) and bool(hbs),
          f"HB every [hb] carries box= and badges= ({len(hbs)} heartbeat(s))")
    check(has_envall, "ENVALL the run header has an `env-all:` line")

    if ref_lines is not None:
        ref = []
        for ln in ref_lines:
            m = BATTLE.match(ln.rstrip("\r\n"))
            if m:
                ref.append((int(m.group(1)), m.group(2), m.group(3)))
        same = ref == battles
        if not same:
            for i, (a, b) in enumerate(zip(ref, battles)):
                if a != b:
                    out(f"  first REPLAY difference at #{i}: control {a} vs this {b}")
                    break
            else:
                out(f"  REPLAY length differs: control {len(ref)} vs this {len(battles)}")
        check(same and bool(ref), f"REPLAY every [BATTLE] start/end identical to the control ({len(ref)} lines)")

    out("")
    if fails:
        out(f"FAIL — {len(fails)} check(s) failed")
        return 1
    out("PASS — the catch telemetry is paired, honest against the bag, and changed no battle")
    return 0


def _self_test() -> int:
    hdr = ["--- RUN HEADER ---", "    env-all:       (no POKEBOT_* env vars set)", "--- END RUN HEADER ---"]
    hb = ["f100 [hb] mode=Story money=1 box=0 badges=6 msg=''"]
    good = hdr + hb + [
        "f200 [BATTLE] started hp=[]",
        "f200 [CATCH] start kind=dex sp=Oddish#43 lv=20 attempt=1 badges=6 party=6/6 box=0 spare=17 exp_throws=2.0 map=0,36",
        "f250 [BALLS] 17 -> 5", "f251 [BALLS] 5 -> 17",
        "f300 [BALLS] 17 -> 16",
        "f400 [BATTLE] ended (outcome=BattleOutcome.Caught) party=[]",
        "f400 [CATCH] end kind=dex sp=Oddish#43 end=caught res=Caught thrown=1 frames=200 dest=box pid=0000ABCD "
        "party=6/6 box=1 spare=16 badges=6 bail=-",
    ]
    cases = [
        ("clean pair PASSES", good, None, 0),
        ("start without end FAILS", [ln for ln in good if "[CATCH] end" not in ln], None, 1),
        ("empty log is VACUOUS", hdr + hb, None, 2),
        ("a [DEXCATCH] ... start mention does not count (VACUOUS)",
         hdr + hb + ["f200 [DEXCATCH] [DEXCATCH] attempt #1 on Oddish -> box start kind=dex"], None, 2),
        ("thrown disagreeing with [BALLS] FAILS", [ln.replace("thrown=1", "thrown=2") for ln in good], None, 1),
        ("dest=? on a catch FAILS", [ln.replace("dest=box", "dest=?") for ln in good], None, 1),
        ("a heartbeat without box= FAILS", [ln.replace(" box=0 badges=6", "") for ln in good], None, 1),
        ("no env-all header FAILS", [ln for ln in good if "env-all" not in ln], None, 1),
        ("REPLAY identical PASSES", good, good, 0),
        ("REPLAY with a moved battle FAILS", good, [ln.replace("f400 [BATTLE]", "f401 [BATTLE]") for ln in good], 1),
    ]
    bad = 0
    for name, log, ref, want in cases:
        got = grade(log, ref, out=lambda *_a, **_k: None)
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} self-test: {name} (exit {got}, want {want})")
    print("SELF-TEST PASS" if not bad else f"SELF-TEST FAIL ({bad})")
    return 1 if bad else 0


def main(argv: list) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if "--self-test" in argv:
        return _self_test()
    if not argv:
        print(__doc__)
        return 1
    log = argv[0]
    ref = None
    if "--ref" in argv:
        ref = open(argv[argv.index("--ref") + 1], encoding="utf-8", errors="replace").read().splitlines()
    lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
    return grade(lines, ref)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
