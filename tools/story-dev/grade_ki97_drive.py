# -*- coding: utf-8 -*-
"""grade_ki97_drive.py — grade a drive/lane log for the `KI-97` Fortree-segment fix.

USAGE
    py -3.12 grade_ki97_drive.py                      # bare -> --self-test (gate mode)
    py -3.12 grade_ki97_drive.py --self-test
    py -3.12 grade_ki97_drive.py <log> [<log> ...]    # grade real logs
    py -3.12 grade_ki97_drive.py <batch-dir>          # grades every L*/stdout.txt under it

EXIT CODES — 0 PASS · 1 FAIL (a real defect) · 2 INDETERMINATE (nothing proven).
‼ Two codes could not tell "broken" from "unexercised", and that conflation is what hid a
tautological control through an entire review. INDETERMINATE never stands in for PASS.

WHAT `KI-97` WAS: `StoryMode._play` re-enters from the TOP on every whiteout AND every derail.
Segment 13a's `else` called `travel_to_fortree()` with no completion gate, and that function ranks
its legs against an `order` list; any map NOT in the list ranks -1, so EVERY leg runs, starting with
`LEGS[0] = MAUVILLE_CITY (19,6)`. From SOOTOPOLIS_CITY (43,32) — no land route out — it fail-fast
derails. 6 of 14 ended runs in the 2026-09-07 batch died this way.

⛔⛔ WHY THIS IS NOT "grep for the error and require zero" — THE SUBTLETY THAT MAKES THE GRADER REAL:
`Story: Route 119 already cleared — heading to Fortree.` is **ALSO PRINTED LEGITIMATELY** before
BADGE06, in the window between clearing Route 119 and beating Winona; there it is followed by a
successful travel. MEASURED in the batch: the very first occurrence in L01 is followed by
`Story: Devon Scope in the bag ...` — a perfectly healthy run.
⇒ **the defect is the SEQUENCE, not either line.** This grader requires the Mauville failure to
follow that line within a small window before it will attribute anything to `KI-97`.

⛔ AND ATTRIBUTION MATTERS INDEPENDENTLY: the identical `(19,6)` destination is also `LEGS[0]` of
`travel_lavaridge_to_petalburg`, which has fired before from LAVARIDGE_TOWN. A Mauville failure with
NO preceding Route-119 line is therefore a DIFFERENT defect and is reported as such — loudly, because
the run still died, but never as a `KI-97` regression. (An adversarial review flagged that four
separate reports had asserted the attribution without ever quoting the preceding line.)

THE CHECKS
  C0  NON-VACUOUS  — the log must show Ch13a activity at all. A clean log from a run that never
                     reached the segment proves NOTHING; absence is not evidence.
  C1  SIGNATURE    — zero `Route-119 line -> Mauville (19,6) unreachable` sequences. This is the bug.
  C2  GATE FIRED   — `Ch13a skipped` appears at least once. ⭐ THE POSITIVE CONTROL, and PASS
                     REQUIRES IT: the acceptance criterion is that a string DISAPPEARS, and a
                     disappearance is worthless unless something proves the new code RAN.
                     ⛔ This check was a TAUTOLOGY in round 1 (`bool(gate) or not sig`, where the
                     PASS branch already required `not sig`) — it never once changed a verdict, and
                     every PASS lane was approved showing `gate fired: 0`. A check that every clean
                     run satisfies by construction is not a check.
  C3  NOT OVER-GATED — `Ch13a skipped` must never be followed by Winona's badge being won. The gate
                     only fires when BADGE06 is already set, so winning it afterwards would mean the
                     gate suppressed a Ch13a that was still needed. This is the INVERSE failure, and
                     a fix that only checks C1 cannot see it.

‼ Every check is FAULT-TESTED by `--self-test` below: each arm must turn exactly the intended check
red. A gate nobody has proven can FAIL proves nothing when it passes.
"""
import pathlib
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

SIG_A = "Story: Route 119 already cleared — heading to Fortree."
SIG_B = "Could not reach (19, 6) on MapRSE.MAUVILLE_CITY"
GATE = "Story: Fortree arc already complete (BADGE06) — Ch13a skipped."
WINONA = "BADGE: Feather Badge (Winona"
PRE_TRAVEL = "Story: to Fortree — Mauville City"
#: run separator in a batch lane log. ⛔ C3 MUST stop here: over-gating is a WITHIN-RUN claim,
#: and scanning past a reset blames one run's correct gate hit for the next run's legitimate win.
RESET = "ENDLESS RESET"
#: the derail is emitted immediately after the travel call returns; 3 lines is generous and was
#: chosen from the MEASURED spacing in the batch (adjacent in all 6 observed failures).
WINDOW = 3


# ---------------------------------------------------------------------------------------------
# --self-test — SYNTHETIC ARMS, so this tool is gate-able on a fresh clone with no logs present
# ---------------------------------------------------------------------------------------------
def _arm_good() -> list[str]:
    """Post-BADGE06 re-entry: the gate fires, no travel is issued, nothing derails."""
    return [
        "Story: someone already knows Surf — teach skipped.",
        GATE,
        "Story: Devon Scope in the bag and the Kecleon already flushed.",
        "Story: Mossdeep Gym already done — skipping.",
    ]


def _arm_signature() -> list[str]:
    """⛔ the bug itself — the Route-119 line followed by the Mauville fail-fast."""
    return [
        "Story: someone already knows Surf — teach skipped.",
        SIG_A,
        f"Story localization — derail #1: {SIG_B}: the field is idle and we are still at (43, 32) "
        "(Source (43/32 @ SOOTOPOLIS_CITY) and destination (19/6 @ MAUVILLE_CITY) are not on "
        "connected maps)",
    ]


def _arm_benign_route119() -> list[str]:
    """‼ MUST PASS. Pre-BADGE06, the Route-119 line is legitimate and the travel SUCCEEDS.
    This arm is the false-positive guard: a grader that required SIG_A to be absent would fail
    here and would be teaching the reader to bypass it."""
    return [
        SIG_A,
        PRE_TRAVEL + "...",
        "Story: reached Fortree City!",
        "BADGE: Feather Badge (Winona, Fortree) — team of 5",
    ]


def _arm_vacuous() -> list[str]:
    """No Ch13a activity of any kind -> INDETERMINATE, never a PASS."""
    return [
        "Story: Ch19 party-select — bringing 3 of 3",
        "Story: lost a battle at map (14, 0) (defeat #3 here; KO'd 1 of theirs first).",
    ]


def _arm_over_gated() -> list[str]:
    """⛔ the INVERSE failure: the gate skipped Ch13a and Winona was fought AFTERWARDS,
    i.e. BADGE06 was not actually set and the segment was needed."""
    return [
        GATE,
        "Story: to Fortree — Route 118 (west bank)...",
        "BADGE: Feather Badge (Winona, Fortree) — team of 5",
    ]


def _arm_unattributed() -> list[str]:
    """A Mauville (19,6) failure with NO preceding Route-119 line — `travel_lavaridge_to_petalburg`
    can produce the identical string. The run still died, so this is exit 1, but it must NOT be
    reported as a KI-97 regression."""
    return [
        "Story: topping up at Lavaridge before the mountain...",
        f"Story localization — derail #2: {SIG_B}: (Source (5/16 @ LAVARIDGE_TOWN) ...)",
    ]


def _arm_multi_run_ok() -> list[str]:
    """‼ MUST PASS — the false positive an independent reviewer REPRODUCED against round 1.
    Run 1 legitimately skips Ch13a (BADGE06 already set). A restart begins a DIFFERENT run, which
    fairly earns Winona for the first time. Nothing is wrong here; the unbounded C3 called it
    over-gated because it scanned across the run boundary."""
    return [
        GATE,
        "Story: Devon Scope in the bag and the Kecleon already flushed.",
        "=== ENDLESS RESET: run 1/infinite -> derailed: something unrelated (1,234,567 frames) ===",
        "Story: to Fortree — Mauville City...",
        "Story: reached Fortree City!",
        "BADGE: Feather Badge (Winona, Fortree) — team of 5",
    ]


def _self_test() -> int:
    cases = [
        ("good drive (gate fired, nothing derailed)", _arm_good, 0),
        ("‼ multi-run: gate hit, RESET, then a legitimate Winona — MUST NOT be over-gated",
         _arm_multi_run_ok, 0),
        ("‼ benign pre-BADGE06 Route-119 + successful travel -> clean but UNEXERCISED = INDET",
         _arm_benign_route119, 2),
        ("⛔ the KI-97 signature (Route-119 line -> Mauville fail-fast)", _arm_signature, 1),
        ("no Ch13a activity at all -> INDETERMINATE", _arm_vacuous, 2),
        ("⛔ OVER-GATED — skipped Ch13a, then fought Winona IN THE SAME RUN", _arm_over_gated, 1),
        ("Mauville fail with no preceding line -> NOT KI-97, still a failure", _arm_unattributed, 1),
    ]
    print("=" * 96)
    print("grade_ki97_drive.py --self-test — seven synthetic arms")
    print("=" * 96)
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for label, build, want in cases:
            path = pathlib.Path(tmp) / "arm.log"
            path.write_text("\n".join(build()) + "\n", encoding="utf-8")
            rc = subprocess.run(
                [sys.executable, str(pathlib.Path(__file__).resolve()), str(path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            ok = rc.returncode == want
            failures += 0 if ok else 1
            print(f"  {'PASS' if ok else 'RED '}  exit={rc.returncode} (want {want})  {label}")
            if not ok:
                print("\n".join("        " + l for l in rc.stdout.strip().splitlines()[-8:]))
    print("-" * 96)
    print("SELF-TEST: " + ("PASS" if not failures else f"FAIL ({failures} arm(s))"))
    return 1 if failures else 0


# ⛔ A GATE MUST BE RUNNABLE WITH NO ARGUMENTS — `run_gates.py` invokes each entry bare, so a bare
# invocation runs the SELF-TEST rather than printing usage and exiting 2.
if "--self-test" in sys.argv or len(sys.argv) == 1:
    raise SystemExit(_self_test())


def _grade(path: pathlib.Path) -> dict:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    sig, unattributed, benign = [], [], 0
    for i, line in enumerate(lines):
        if SIG_B not in line:
            continue
        back = lines[max(0, i - WINDOW):i]
        if any(SIG_A in b for b in back):
            sig.append((i + 1, line.strip()[:150]))
        else:
            unattributed.append((i + 1, line.strip()[:150]))
    for i, line in enumerate(lines):
        if SIG_A in line:
            fwd = lines[i + 1:i + 1 + WINDOW]
            if not any(SIG_B in f for f in fwd):
                benign += 1
    gate_hits = [i + 1 for i, l in enumerate(lines) if GATE in l]
    # C3: a Winona badge AFTER a gate hit means the gate skipped a segment that was still needed.
    over = []
    for g in gate_hits:
        for i, l in enumerate(lines[g:], start=g):
            if RESET in l:
                break               # a new run began — nothing after this is evidence about THIS one
            if WINONA in l:
                over.append((g, i + 1))
                break
    return {
        "path": path, "lines": len(lines), "sig": sig, "unattributed": unattributed,
        "benign": benign, "gate": gate_hits, "over": over,
        "activity": bool(gate_hits) or benign or sig or any(PRE_TRAVEL in l for l in lines),
    }


targets: list[pathlib.Path] = []
for a in sys.argv[1:]:
    p = pathlib.Path(a)
    targets.extend(sorted(p.glob("L*/stdout.txt")) if p.is_dir() else [p])
if not targets:
    print("[ki97] no logs found")
    raise SystemExit(2)

print("=" * 96)
print("grade_ki97_drive.py — KI-97 (Segment 13a Fortree gate)")
print("=" * 96)
# ⛔ THREE OUTCOMES, NOT TWO. A lane that never reached Ch13a is INDETERMINATE, not FAILED — most
# lanes of a fresh batch are still in the early game, and a grader that marked them red would fire on
# healthy runs and teach the reader to ignore it. (`08-MISTAKES.md`: a gate with false positives is
# strictly worse than no gate.) But INDETERMINATE can never stand in for PASS either: the aggregate
# verdict is only PASS if at least ONE lane actually exercised the code and came back clean.
red = indet = clean = 0
for r in (_grade(t) for t in targets):
    name = f"{r['path'].parent.name}/{r['path'].name}"
    c0 = r["activity"]
    c1 = not r["sig"]
    # ⭐ THE POSITIVE CONTROL — AND IT MUST BE ABLE TO FAIL ON ITS OWN. This read
    # `bool(gate) or not sig`, which `c1` already guaranteed, so it never once changed a
    # verdict and every PASS lane was approved with `gate fired: 0`. A check that every clean
    # run satisfies by construction is not a check (`08-MISTAKES.md` rule 4).
    c2 = bool(r["gate"])
    c3 = not r["over"]
    if not c1 or not c3 or r["unattributed"]:
        status, note = "FAIL", ""            # a real defect outranks every other consideration
        red += 1
    elif not c0:
        status, note = "INDET", "  (never reached Ch13a — proves nothing either way)"
        indet += 1
    elif not c2:
        # ⛔ CLEAN BUT UNEXERCISED IS NOT A PASS. Without a `Ch13a skipped` line the gated branch
        # never ran, so the absence of the failure is worth nothing: the run simply never tried.
        status, note = "INDET", "  (clean, but the gate never fired — nothing was exercised)"
        indet += 1
    else:
        status, note = "PASS", ""
        clean += 1
    print(f"\n{status}  {name}  ({r['lines']} lines){note}")
    print(f"   C0 non-vacuous   : {'yes' if c0 else 'NO — no Ch13a activity; this log proves nothing'}")
    print(f"   C1 signature     : {len(r['sig'])} (want 0)   [Route-119 line -> Mauville fail-fast]")
    print(f"   C2 gate fired    : {len(r['gate'])} `Ch13a skipped` line(s)   [positive control]")
    print(f"   C3 not over-gated: {'yes' if c3 else 'NO — skipped Ch13a then fought Winona'}")
    print(f"   benign Route-119 lines (expected, not a fault): {r['benign']}")
    for ln, txt in r["sig"][:3]:
        print(f"      ⛔ L{ln}: {txt}")
    for ln, txt in r["unattributed"][:3]:
        print(f"      ⚠ NOT KI-97 (no preceding Route-119 line) L{ln}: {txt}")
    for g, w in r["over"][:3]:
        print(f"      ⛔ over-gated: `Ch13a skipped` at L{g}, Winona won later at L{w}")

print("\n" + "-" * 96)
print(f"  {clean} PASS · {red} FAIL · {indet} INDETERMINATE   (of {len(targets)} log(s))")
# ⛔ THREE EXIT CODES: 0 PASS · 1 FAIL · 2 INDETERMINATE. Two codes could not tell "broken" from
# "unexercised", and that conflation is what let a tautological control hide for a whole review.
if red:
    print("VERDICT: FAIL (exit 1) — the KI-97 signature (or an over-gate) is present.")
    code = 1
elif not clean:
    print("VERDICT: INDETERMINATE (exit 2) — no log exercised the gate, so nothing is proven.")
    print("  ‼ NOT a pass. Absence of the failure in a run that never reached the code is not")
    print("    evidence. Drive from a save that re-enters `_play` with BADGE06 already set.")
    code = 2
else:
    print("VERDICT: PASS (exit 0) — a log exercised the gate post-BADGE06 and came back clean.")
    code = 0
raise SystemExit(code)
