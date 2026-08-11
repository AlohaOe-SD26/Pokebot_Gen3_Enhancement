"""How many TURNS does the bot lose to status? Reads `[TURN …]` telemetry out of debug logs.
NO EMULATOR — pure log analysis, seconds.

WHY THIS EXISTS. On 2026-08-11 the Magma Hideout loss was traced to Crobat's **Confuse Ray**:
Sceptile went 122 → 110 → 30 → 4 across three selections **without ever acting** (PP frozen at 19,
the opponent untouched), and Castform lost two more turns the same way. That is ~5 turns in a fight
decided by about two.

‼ **BUT THAT IS n=1**, and this project has repeatedly been burned by promoting a single fight to a
finding (the retracted counter conclusion; the "99.4% fainted ace" reading; "the chapter wins 1 in
3" earlier the same day). **A battle-policy change has wide blast radius — every mode that uses
`DefaultBattleStrategy` — so it must be justified by a RATE, not by one fight.** This probe is the
instrument that produces the rate. Build it before changing the policy, not after.

WHAT IT COUNTS, per log:
  * turns where the actor carried a status (`[Confused]`, `[Sleep]`, `[Paralysis]`, …);
  * of those, the **LOST** ones — a move was selected and the PP did **not** decrement on the
    actor's next selection of that same move, i.e. the move never executed. ‼ A MISS still consumes
    PP, so a frozen PP is not "it missed" — it is "it never acted".
  * the same for turns with NO status, as the **CONTROL**: if no-status turns also show frozen PP
    at a similar rate, the measurement is picking up something other than status and must not be
    read as a status tax.

‼ WHAT IT CANNOT SEE. The status field was added 2026-08-11, so **logs older than that carry no
status** and will report 0 status turns — which is indistinguishable from "no status occurred".
The probe reports how many turn-lines carried a status marker at all, so a silent zero cannot be
mistaken for a real one.

Run:
  PYTHONUTF8=1 py -3.12 probe_status_tax.py                      # every profile with turn telemetry
  PYTHONUTF8=1 py -3.12 probe_status_tax.py <profile-or-logfile> # one target
"""

from __future__ import annotations

import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[2]
PROFILE_DIRS = [
    REPO / "sandbox-pokebot" / "profiles",
    REPO / "custom-pokebot" / "profiles",
]

# [TURN 4] Sceptile L44 110/122 [Confused] -> UseMove:Slam(pp19)  vs Crobat L38 90/119
TURN_RE = re.compile(
    r"\[TURN\s+(\d+)\]\s+"
    r"(?P<mon>[A-Za-z][\w'-]*)\s+L(?P<lvl>\d+)\s+(?P<hp>\d+)/(?P<max>\d+)"
    r"(?:\s+\[(?P<status>[A-Za-z/]+)\])?"
    r"\s+->\s+(?P<action>[^\s]+)"
    r"(?:\s+vs\s+(?P<foe>[A-Za-z][\w'-]*)\s+L\d+\s+(?P<fhp>\d+)/(?P<fmax>\d+))?"
)
MOVE_RE = re.compile(r"UseMove(?:AgainstRightSideOpponent)?:(?P<move>.+?)\(pp(?P<pp>\d+)\)")


# ‼‼ TWO FLAWS THE FIRST DRAFT HAD, BOTH CAUGHT BY ITS OWN CONTROL — fixed here:
#
# 1. **Not every "status" incapacitates.** `status_temporary` includes `Foresight`, `Wrapped`,
#    `Substitute`, `FocusEnergy` — none of which stop a mon acting. Lumping them in diluted the
#    tax: `mintrun1/2/3` showed `0/4 lost` on Foresight/Wrapped while `cust-verify` showed `2/2`
#    on Confused. Only the INCAPACITATING set can cost a turn, so only it is counted.
#
# 2. **The "clean" control was CONTAMINATED.** The status field was added 2026-08-11, so every
#    older log carries NO status marker — which means their confused turns were being counted as
#    *clean*. The baseline therefore contained the very thing it was supposed to exclude, and the
#    6.2%-over-145,683-turns figure it produced is meaningless as a comparator. The control is now
#    computed ONLY over logs that actually carry the instrument.
INCAPACITATING = {"Confused", "Sleep", "Freeze", "Paralysis", "Flinched", "Recharging"}


def _incapacitating(status: str | None) -> bool:
    if not status:
        return False
    return any(part in INCAPACITATING for part in status.split("/"))


def analyse(path: pathlib.Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return None
    rows = []
    seen = set()
    for m in TURN_RE.finditer(text):
        # the logger emits each line twice; collapse exact duplicates
        key = m.group(0)
        if key in seen:
            continue
        seen.add(key)
        mv = MOVE_RE.search(m.group("action"))
        rows.append(
            {
                "mon": m.group("mon"),
                "status": m.group("status"),
                "move": mv.group("move") if mv else None,
                "pp": int(mv.group("pp")) if mv else None,
            }
        )
    if not rows:
        return None

    # A turn is LOST when the SAME mon selects the SAME move again with the SAME pp — the previous
    # selection never executed. Tracked per (mon, move).
    last_pp: dict[tuple[str, str], int] = {}
    lost = defaultdict(int)      # keyed by "status" / "clean"
    total = defaultdict(int)
    status_lines = 0

    for r in rows:
        bucket = "status" if _incapacitating(r["status"]) else "clean"
        if r["status"]:
            status_lines += 1
        if r["move"] is None or r["pp"] is None:
            continue
        k = (r["mon"], r["move"])
        total[bucket] += 1
        if k in last_pp and last_pp[k] == r["pp"]:
            lost[bucket] += 1
        last_pp[k] = r["pp"]

    return {
        # ‼ Does this log carry the instrument AT ALL? Without it, "0 status turns" means
        # "cannot see", not "none happened" — and its clean bucket is contaminated.
        "instrumented": status_lines > 0,
        "turns": len(rows),
        "status_lines": status_lines,
        "lost_status": lost["status"],
        "total_status": total["status"],
        "lost_clean": lost["clean"],
        "total_clean": total["clean"],
        "statuses": sorted({r["status"] for r in rows if r["status"]}),
    }


def pct(a: int, b: int) -> str:
    return f"{100.0 * a / b:5.1f}%" if b else "   n/a"


targets: list[pathlib.Path] = []
if len(sys.argv) > 1:
    p = pathlib.Path(sys.argv[1])
    targets = [p] if p.is_file() else sorted(p.rglob("*.log"))
    if not targets:
        for d in PROFILE_DIRS:
            targets += sorted((d / sys.argv[1]).rglob("*.log"))
else:
    for d in PROFILE_DIRS:
        if d.is_dir():
            targets += sorted(d.rglob("debug-logs/*.log"))

line = "=" * 96
print(line)
print("STATUS TAX — turns where a move was SELECTED but never EXECUTED (PP did not decrement)")
print(line)
print(f"{'profile':<26} {'turns':>6} {'w/status':>9} {'LOST|status':>12} {'LOST|clean':>11}  statuses")
print("-" * 96)

agg = defaultdict(int)
inst = defaultdict(int)
uninstrumented = 0
seen_any_status = False
for t in targets:
    r = analyse(t)
    if not r:
        continue
    name = t.parent.parent.name if t.parent.name == "debug-logs" else t.stem
    for k in ("turns", "status_lines", "lost_status", "total_status", "lost_clean", "total_clean"):
        agg[k] += r[k]
    if r["instrumented"]:
        seen_any_status = True
        for k in ("turns", "status_lines", "lost_status", "total_status", "lost_clean", "total_clean"):
            inst[k] += r[k]
    else:
        uninstrumented += 1
    print(
        f"{name[:26]:<26} {r['turns']:>6} {r['status_lines']:>9} "
        f"{r['lost_status']:>4}/{r['total_status']:<4}{pct(r['lost_status'], r['total_status'])} "
        f"{r['lost_clean']:>3}/{r['total_clean']:<4}{pct(r['lost_clean'], r['total_clean'])}  "
        f"{','.join(r['statuses']) or '-'}"
    )

print("-" * 96)
print(
    f"{'ALL':<26} {agg['turns']:>6} {agg['status_lines']:>9} "
    f"{agg['lost_status']:>4}/{agg['total_status']:<4}{pct(agg['lost_status'], agg['total_status'])} "
    f"{agg['lost_clean']:>3}/{agg['total_clean']:<4}{pct(agg['lost_clean'], agg['total_clean'])}"
)

print(
    f"{'INSTRUMENTED ONLY':<26} {inst['turns']:>6} {inst['status_lines']:>9} "
    f"{inst['lost_status']:>4}/{inst['total_status']:<4}{pct(inst['lost_status'], inst['total_status'])} "
    f"{inst['lost_clean']:>3}/{inst['total_clean']:<4}{pct(inst['lost_clean'], inst['total_clean'])}"
)
print(f"  ({uninstrumented} log(s) predate the status field and are EXCLUDED from the comparison)")

print()
if not seen_any_status:
    print("‼ NO STATUS MARKERS FOUND IN ANY LOG.")
    print("  The status field was added 2026-08-11 — older logs cannot carry it, so this is")
    print("  'the instrument was not present', NOT 'no status occurred'. Re-run after a batch")
    print("  with the current build before drawing any conclusion.")
else:
    print("HOW TO READ THIS:")
    print("  * LOST|status is the tax: turns burned while incapacitated.")
    print("  * ‼ LOST|clean is the CONTROL. If it is close to LOST|status, this is NOT measuring")
    print("    a status tax — something else freezes PP and the difference is what matters, not")
    print("    the absolute number.")
    print("  * n here is small. A battle-policy change touches every mode using")
    print("    DefaultBattleStrategy; justify it on a BATCH, not on one dungeon run.")
print(line)
