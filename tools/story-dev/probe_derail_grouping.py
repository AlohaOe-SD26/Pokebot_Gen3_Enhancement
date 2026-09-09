# -*- coding: utf-8 -*-
"""GATE — `x4_headless._derail_reason` must collapse hex PIDs, or `summary.json` ranks the wrong blocker.

⛔⛔ WHY: the grouping pass was `re.sub(r"\\d[\\d,]*", "N", o)` — DECIMAL ONLY — and a PID is HEX. So
`Marill#30AD95BD` normalised to `Marill#NADNBD` (the hex LETTERS survive), every distinct PID became
its own key, and because `summary.json` is written through `.most_common()` the single biggest
blocker was scattered into count-1 rows at the BOTTOM of the file.
⭐ MEASURED on batch `20260907-203713`, re-aggregating its 49 real outcome strings:
    before : Ch23 training = 16 events / **16 keys**; displayed #1 = "this boss: N losses" (6)
    after  : Ch23 training = 16 events / 6 keys;      #1 = the Victory Road training failure (9)
⇒ the ranking INVERTS. Every reader who trusted the top of `summary.json` got the wrong blocker, low
by ~3x — the most consequential defect found in the 2026-09-08 health check.

‼ THIS GATE EXISTS BECAUSE A TIER 1 REVIEWER ASKED THE RIGHT QUESTION: the fix had been validated only
by a ONE-OFF manual re-aggregation quoted in the changelog, with no executable arm. A number in a
changelog cannot fail when someone edits the regex back. This can.
⭐ It is a PURE UNIT CHECK on the real shipped function — no ROM, no batch, milliseconds.

Exit 0 = PASS.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from x4_headless import _derail_reason  # noqa: E402  (the SHIPPED function)

#: (label, raw outcome, must_contain, must_not_contain). Every string here is a REAL shape taken
#: from `x4-runs/20260907-203713`, not invented.
ARMS = [
    ("a real Ch23 training failure carrying a hex PID",
     "derailed: Ch23 (Victory Road) failed after 3 attempts. attempt 1: BotModeError: "
     "Ch23 training: Marill#30AD95BD alone needs 406,972 frames",
     "#PID", "30AD95BD"),
    ("a PID whose hex happens to be all letters (no digits to mask it)",
     "derailed: Ch23 training: Slugma#ABCDEFAB alone needs 494,385 frames",
     "#PID", "ABCDEFAB"),
    ("a PID that is all digits (the decimal pass alone would have handled this one)",
     "derailed: Ch23 training: Marill#12345678 alone needs 406,972 frames",
     "#PID", "12345678"),
    ("⛔ NO-FIRE: an ordinary number must still normalise to N, not to #PID",
     "stopped: this boss: 3 losses with no super-effective answer to Normal",
     "N losses", "#PID"),
    ("⛔ NO-FIRE: a short hex-looking token that is NOT a PID must be left alone",
     "derailed: Story: watchdog fired at map #4B (nothing progressed)",
     "#N", "#PID"),
]


def main() -> int:
    print("=" * 92)
    print("GATE — `_derail_reason` collapses hex PIDs so `summary.json` ranks the true blocker")
    print("=" * 92)

    failures = []
    for label, raw, must, must_not in ARMS:
        got = _derail_reason(raw)
        if must not in got:
            failures.append(f"{label}\n        expected to contain {must!r}\n        got {got!r}")
        elif must_not in got:
            failures.append(f"{label}\n        expected NOT to contain {must_not!r}\n        got {got!r}")

    print(f"\n  arms: {len(ARMS)} (3 fault-shaped, 2 no-fire)")
    for f in failures:
        print(f"    ⛔ {f}")

    # ⭐ THE PROPERTY THAT ACTUALLY MATTERS: two runs differing ONLY by PID must GROUP TOGETHER.
    # An arm checking a single string cannot see a grouping bug; this one can.
    a = _derail_reason("derailed: Ch23 training: Marill#30AD95BD alone needs 406,972 frames")
    b = _derail_reason("derailed: Ch23 training: Marill#47557827 alone needs 406,972 frames")
    grouped = a == b
    print(f"  grouping : two identical failures differing ONLY by PID -> "
          f"{'SAME key ✅' if grouped else 'DIFFERENT keys ⛔'}")
    if not grouped:
        failures.append(f"two PIDs produced different keys:\n        {a!r}\n        {b!r}")

    print("\n" + "-" * 92)
    if failures:
        print("FAILED — PIDs are fragmenting the derail summary; the top of `summary.json` will lie.")
        print("         The `#[0-9A-Fa-f]{6,}` pass must run BEFORE the digit pass in `_derail_reason`.")
        print("=" * 92)
        return 1
    print("✅ PASS — hex PIDs collapse to #PID, ordinary numbers still normalise to N, and two runs")
    print("   differing only by PID group under one key.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
