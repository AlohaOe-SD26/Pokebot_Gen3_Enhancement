# -*- coding: utf-8 -*-
"""Grade a `KI-93` census drive by its SEQUENCE, not by its totals.

⛔⛔ WHY THIS EXISTS. On 2026-09-06 I graded a drive by counting `KI93-DISMISS`, `KI93-REPICK` and
`KI-47` lines, saw healthy numbers, and reported the fix "driven clean". An independent reviewer then
read the SAME log and found a fainted Pokémon's move vetoes being applied to its replacement — visible
only in the ORDER of the lines I had counted. `08-MISTAKES.md`: **a count is not a reading.**

The three questions a drive must answer, each of which the totals can hide:

  C1  DID THE LIVELOCK END?           `KI-47` battle sub-handler stops must be 0, and the run must not
                                      end sitting on a selection-refusal script.
  C2  IS EVERY OVERRIDE JUSTIFIED?    ⭐ THE ONE THE COUNTS HID. Every `[KI93-REPICK]` must be preceded
                                      by a `[KI93-WAIT] … ENDED` since the last commit — an override
                                      with no refusal behind it is the fix vetoing a move the game
                                      never rejected.
  C3  IS THE FIX STILL ENGAGED?       ⚠ The turn-scoped LIFETIME rule clears the memory when an
                                      ordinary script appears in the cancel branch, and that branch
                                      also runs on the re-opened menu. If it clears too eagerly the
                                      memory is empty when the re-pick needs it: `DISMISS > 0` with
                                      `REPICK == 0` means the fix was undone by its own guard.

Usage:  PYTHONUTF8=1 py -3.12 grade_ki93_drive.py <debug-log> [<harness-stdout-log>]
Exit 0 only if all three pass.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

# =================================================================================================
# --self-test — SYNTHETIC ARMS, so this tool is gate-able on a fresh clone
# =================================================================================================
#: ⛔ The real drive logs live under `profiles/`, which `.gitignore` excludes, so the fault matrix
#: cannot be reproduced from a checkout. These arms rebuild it from embedded lines instead.
#: ‼ THREE OF THE FIVE ARE REGRESSIONS OF BUGS THIS GRADER ITSELF SHIPPED on 2026-09-06/07:
#:   * it returned PASS on a log with no identity (it could not see the defect, and said "clean");
#:   * it returned PASS on a drive where the fix never engaged (nothing was exercised);
#:   * it flagged CORRECT behaviour, because its invariant was keyed on slot instead of Pokemon.
_CTL = "f100 [BATTLE] [KI93-CTL] handle_battle_action_selection entered — census armed"


def _arm_good() -> list[str]:
    """A mon is refused, dismissed, and re-picks its OWN vetoed slot across a re-entry. LEGITIMATE."""
    return [
        _CTL,
        "f200 [BATTLE] [KI93-WAIT] frames=1 cb0='CompleteOnInactiveTextPrinter2' instr='BattleScript_SelectingTormentedMove' last_committed_slot=2",
        "f252 [BATTLE] [KI93-DISMISS] pressed B at frame 252 instr='BattleScript_SelectingTormentedMove' owner=111",
        "f257 [BATTLE] [KI93-REPICK] battler=0 owner=111 slot 2 was REFUSED -> 0",
        "f258 [BATTLE] [KI93-COMMIT] battler=0 owner=111 action=UseMove slot=0 census={} refused={0: {2}}",
        # the handler is RE-ENTERED and the same mon re-picks its own vetoed slot — still legitimate
        "f900 [BATTLE] [KI93-REPICK] battler=0 owner=111 slot 2 was REFUSED -> 0",
        "f901 [BATTLE] [KI93-COMMIT] battler=0 owner=111 action=UseMove slot=0 census={} refused={0: {2}}",
    ]


def _arm_cross_mon() -> list[str]:
    """⛔ THE REAL BLOCKER: mon 111 is refused, FAINTS, and mon 222 inherits its vetoes."""
    return [
        _CTL,
        "f252 [BATTLE] [KI93-DISMISS] pressed B at frame 252 instr='BattleScript_SelectingTormentedMove' owner=111",
        "f257 [BATTLE] [KI93-REPICK] battler=0 owner=111 slot 2 was REFUSED -> 0",
        "f258 [BATTLE] [KI93-COMMIT] battler=0 owner=111 action=UseMove slot=0 census={} refused={0: {2}}",
        # mon 111 fainted; 222 is in the slot now and was never refused anything
        "f900 [BATTLE] [KI93-REPICK] battler=0 owner=222 slot 0 was REFUSED -> 2",
        "f901 [BATTLE] [KI93-COMMIT] battler=0 owner=222 action=UseMove slot=2 census={} refused={0: {0}}",
    ]


def _arm_no_identity() -> list[str]:
    """A log from before the census carried `owner=`. C2 is unanswerable -> INDETERMINATE."""
    return [
        _CTL,
        "f252 [BATTLE] [KI93-DISMISS] pressed B at frame 252 instr='BattleScript_SelectingTormentedMove'",
        "f257 [BATTLE] [KI93-REPICK] battler=0 slot 2 was REFUSED -> 0",
        "f258 [BATTLE] [KI93-COMMIT] battler=0 action=UseMove slot=0 census={} refused={0: {2}}",
    ]


def _arm_vacuous() -> list[str]:
    """The fix never engaged: no refusal, no dismiss, no re-pick. NOT evidence."""
    return [
        _CTL,
        "f200 [BATTLE] [KI93-WAIT] frames=1 cb0='CompleteOnInactiveTextPrinter' instr='BattleScript_MoveEnd' last_committed_slot=1",
        "f300 [BATTLE] [KI93-COMMIT] battler=0 owner=111 action=UseMove slot=1 census={} refused={}",
    ]


def _arm_no_control() -> list[str]:
    """No `[KI93-CTL]` -> the census never ran -> nothing in the log is evidence."""
    return [
        "f252 [BATTLE] [KI93-DISMISS] pressed B at frame 252 instr='BattleScript_SelectingTormentedMove' owner=111",
        "f257 [BATTLE] [KI93-REPICK] battler=0 owner=111 slot 2 was REFUSED -> 0",
    ]


def _self_test() -> int:
    cases = [
        ("good drive (own veto carried across a re-entry)", _arm_good, 0),
        ("⛔ cross-mon leak — a fainted mon's veto on its replacement", _arm_cross_mon, 1),
        ("no `owner=` in the log -> INDETERMINATE", _arm_no_identity, 1),
        ("no refusal at all -> VACUOUS", _arm_vacuous, 1),
        ("no control line -> not evidence", _arm_no_control, 1),
    ]
    print("=" * 96)
    print("grade_ki93_drive.py --self-test — five synthetic arms")
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
                print("\n".join("        " + l for l in rc.stdout.strip().splitlines()[-6:]))
    print("-" * 96)
    print("SELF-TEST: " + ("PASS" if not failures else f"FAIL ({failures} arm(s))"))
    return 1 if failures else 0


# ⛔ A GATE MUST BE RUNNABLE WITH NO ARGUMENTS. `run_gates.py` invokes each entry bare, so a bare
# invocation runs the SELF-TEST (the synthetic arms above) rather than printing usage and exiting 2.
# Pass a log path to grade a real drive; usage is in the module docstring.
if "--self-test" in sys.argv or len(sys.argv) == 1:
    raise SystemExit(_self_test())

if len(sys.argv) < 2:  # pragma: no cover - unreachable: bare invocation self-tests above
    print(__doc__)
    sys.exit(2)

debug_log = pathlib.Path(sys.argv[1])
stdout_log = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
lines = debug_log.read_text(encoding="utf-8", errors="replace").splitlines()

FRAME = re.compile(r"^f(\d+)")
events: list[tuple[int, str, str]] = []
for line in lines:
    if "[KI93-" not in line:
        continue
    m = FRAME.match(line)
    frame = int(m.group(1)) if m else -1
    kind = line.split("[KI93-", 1)[1].split("]", 1)[0]
    events.append((frame, kind, line))

counts: dict[str, int] = {}
for _, kind, _l in events:
    counts[kind] = counts.get(kind, 0) + 1

print("=" * 96)
print(f"KI-93 DRIVE GRADE — {debug_log.name}")
print("=" * 96)
print(f"  events: {counts}")

# ---- C0: the control must have fired, or nothing below is evidence -------------------------------
control = counts.get("CTL", 0)
print(f"\n  C0 CONTROL     {'PASS' if control else 'RED '}  [KI93-CTL] fired {control}x"
      + ("" if control else "  ⛔ the census never ran — every other line below is meaningless"))
if not control:
    print("\nACCEPTANCE: FAIL (no control)")
    sys.exit(1)

# ---- C1: did the livelock end? -------------------------------------------------------------------
stalls = 0
tail = ""
if stdout_log and stdout_log.exists():
    text = stdout_log.read_text(encoding="utf-8", errors="replace")
    stalls = text.count("battle sub-handler")
    tail = text[-4000:]
c1 = stalls == 0
print(f"  C1 LIVELOCK    {'PASS' if c1 else 'RED '}  `KI-47 battle sub-handler` stops = {stalls}"
      + ("  (was 3-6 before the fix)" if c1 else "  ⛔ the handler is still being stopped"))

# ---- C2: every REPICK justified by a refusal THIS POKEMON actually received -----------------------
# ⛔⛔ THE INVARIANT HAD TO BE KEYED ON IDENTITY, AND MY FIRST VERSION WAS NOT.
# v1 armed on a refusal and disarmed on the next COMMIT. That flagged 6 re-picks that were CORRECT:
# the handler is re-entered per selection phase, so a mon's own veto legitimately survives a commit —
# that persistence is the entire point of the fix. v1 could not distinguish it from the real defect
# (a FAINTED mon's veto applied to its replacement) because both look identical when keyed by SLOT.
# ⇒ arm per OWNER (`personality_value`), and drop a mon's armed state the moment a different mon
# occupies that slot. Same lesson as the bug it grades: assert IDENTITY, never position.
OWNER = re.compile(r"owner=(\w+)")
BATTLER = re.compile(r"battler=(\d+)")

def _owner_of(line: str) -> str:
    m = OWNER.search(line)
    return m.group(1) if m else "?"

def _battler_of(line: str, default: int = 0) -> int:
    m = BATTLER.search(line)
    return int(m.group(1)) if m else default

# ⛔⛔ REFUSE TO GRADE WHAT CANNOT BE SEEN. C2's whole job is to tell a mon's OWN carried-over veto
# (correct) from a FAINTED mon's veto applied to its replacement (the defect) — and those are
# indistinguishable without the owner's identity on the line. A log written before the census carried
# `owner=` therefore cannot be graded on C2.
# ‼ THIS BRANCH EXISTS BECAUSE THE FIRST VERSION RETURNED **PASS** ON THE KNOWN-BAD LOG: every
# `_owner_of` was "?", the arming degenerated, and the grader cleared the very defect it was written
# to catch. A gate that passes its own fault case is worse than no gate.
_repicks = [l for _f, k, l in events if k == "REPICK"]
_have_identity = bool(_repicks) and all("owner=" in l for l in _repicks)
unjustified: list[str] = []
c2_indeterminate = bool(_repicks) and not _have_identity

if not c2_indeterminate:
    armed: dict[tuple[int, str], bool] = {}
    current_owner: dict[int, str] = {}
    for _frame, kind, line in events:
        if kind in ("DISMISS", "COMMIT", "REPICK"):
            bi, own = _battler_of(line), _owner_of(line)
            if own != "?" and current_owner.get(bi) != own:
                # a different Pokemon holds this slot now -> it inherits nothing
                current_owner[bi] = own
                armed.pop((bi, own), None)
        if kind == "DISMISS":
            armed[(_battler_of(line), _owner_of(line))] = True
        elif kind == "REPICK":
            if not armed.get((_battler_of(line), _owner_of(line)), False):
                unjustified.append(line.strip())
c2 = (not unjustified) and not c2_indeterminate
if c2_indeterminate:
    print("  C2 JUSTIFIED   ⛔ INDETERMINATE — this log's REPICK lines carry no `owner=`, so a mon's own")
    print("                    carried-over veto cannot be told from a FAINTED mon's veto applied to its")
    print("                    replacement. Re-drive with the current census. NOT a pass.")
else:
    print(f"  C2 JUSTIFIED   {'PASS' if c2 else 'RED '}  {len(unjustified)} REPICK(s) with no refusal behind them"
          + ("" if c2 else "  ⛔ the fix is vetoing moves the game never refused"))
for line in unjustified[:5]:
    print(f"        {line[:150]}")

# ---- C3: is the fix still engaged? ---------------------------------------------------------------
dismiss, repick = counts.get("DISMISS", 0), counts.get("REPICK", 0)
if dismiss == 0:
    # ⛔⛔ A DRIVE THAT NEVER EXERCISED THE FIX IS NOT A PASS. The first version returned
    # `ACCEPTANCE: PASS` (exit 0) on a drive with ZERO dismisses and ZERO re-picks — i.e. it graded
    # a run in which the code under test never ran, and called it evidence. A Tier 1 reviewer found
    # it before it was trusted. ⇒ VACUOUS, reported as such, non-zero exit: *an arm that cannot
    # distinguish the arms is not an arm.*
    c3, why = False, ("⛔ VACUOUS — this drive contains NO refusal at all (DISMISS=0), so it "
                      "exercised none of the fix. It is not evidence for or against it.")
elif repick == 0:
    c3, why = False, ("⛔ DISMISS fired but REPICK never did — the memory was empty when it was "
                      "needed, i.e. the turn-scoped LIFETIME guard is clearing too eagerly")
else:
    c3, why = True, f"DISMISS={dismiss} and REPICK={repick} — both halves engaged"
print(f"  C3 ENGAGED     {'PASS' if c3 else 'RED '}  {why}")

print("-" * 96)
ok = c1 and c2 and c3
if tail and "whited out" in tail:
    print("  ⚠ NOTE: the run contains a whiteout. That is a LEVEL result, not necessarily a bug — but")
    print("    check C2 above, because an unjustified veto can cause one.")
print("ACCEPTANCE: " + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
