# -*- coding: utf-8 -*-
"""MEASURE the swap-training envelope: at what LEVEL GAP does the bot actually switch?

⛔ WHY THIS IS A CHECKED-IN TOOL AND NOT A SCRATCH SCRIPT. On 2026-09-09 a figure from this
measurement was published in `07-CHANGELOG.md` and a code comment, and a Tier 1 reviewer could not
reproduce it because the script lived only in a scratch directory. `08-MISTAKES.md`'s own rule from
that same day promises a reader can re-run a number "without trusting me at all" — a number whose
producing command is not in the repo cannot keep that promise. Run this; cite THIS.

WHAT IT MEASURES. `SwapTrainBattleStrategy` (`plugins/custom_modes/story_mode.py`) is supposed to let
a far-below Pokemon gain EXP safely: send it out, switch to a strong team-mate on turn 1 before it
takes damage, and it banks Gen-3 participation EXP. The question this answers is HOW FAR BELOW that
still works in practice.

METHOD, and every restriction is deliberate:
  * Parses battle telemetry lines of the shape
        [TURN 0] Lotad L3 16/16 -> RotateLead  vs Abra L7 21/21
    i.e. trainee level + HP, the ACTION taken, and the foe's level.
  * ⛔ TURN 0 ONLY, AT FULL HP. `decide_turn` has TWO triggers — "under-levelled" and "cannot
    continue" (low HP / no usable move). Counting later turns or damaged trainees mixes the
    low-HP bail-out into a measurement about the LEVEL gap and inflates the rate.
  * ⛔ Non-negative gaps only. A trainee ABOVE the foe is not the case under study.
  * ‼ The move regex must tolerate multi-word moves (`UseMove:Water Spout(pp5)`); an early draft of
    an independent re-implementation silently dropped those and skewed its denominators.

⚠ WHAT IT CANNOT TELL YOU. A zero at a given gap is not proof the strategy REFUSES there — it may
simply never have been INSTALLED in the runs that reached that gap. Measured example: the §Ch23
training driver returns `StoryItemBattleStrategy`, never `SwapTrainBattleStrategy`, so its +27-gap
battles contribute rows in which no rotation was ever possible. ⇒ read this as "what has been
OBSERVED", never as "what the code would do".

Bare invocation scans `sandbox-pokebot/profiles` and `tools/story-dev/x4-runs`. Always exits 0 —
this is an OBSERVATION tool, not a gate; there is no invariant here to enforce.
"""
import collections
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent

#: trainee level + current/max HP, the action, and the foe's level.
#: ⛔⛔ THE ACTION GROUP IS `(\w+)` AND THE TAIL IS `.*?` ON PURPOSE — DO NOT "TIGHTEN" THIS.
#: A stricter first draft (`([\w:]+(?:\s+[\w()]+)*?)\s+vs`) required the action to be followed by
#: exactly one space and `vs`. It captured every ROTATION (the numerators were identical) but
#: silently DROPPED two thirds of the denominators — 24,244 decisions became 7,671 — because moves
#: log as `UseMove:Water Spout(pp5)` and spacing varies. The rates then tripled (29.9% -> 62.3% at
#: gap +2) while looking entirely plausible.
#: ⇒ ‼ A PARSER THAT LOSES ROWS INFLATES EVERY RATE AND ANNOUNCES NOTHING. `(\w+)` stops at the `:`
#: and the lazy `.*?` skips whatever follows, so a move's shape can never cost us a row. An
#: independent re-implementation landed within ~1% of the permissive counts, which is the check that
#: settled it.
TURN = re.compile(
    r"\[TURN (\d+)\]\s+(\w+)\s+L(\d+)\s+(\d+)/(\d+)\s*->\s*(\w+).*?vs\s+(\w+)\s+L(\d+)"
)


def measure(roots):
    """(by_gap, files_seen, files_with_turns, decisions) — turn-0, full-HP, gap >= 0."""
    by_gap = collections.defaultdict(lambda: [0, 0])
    files = []
    for r in roots:
        if r.exists():
            files.extend(r.rglob("*.log"))
    with_turns = decisions = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - an unreadable log is simply not evidence
            continue
        if "[TURN " not in text:
            continue
        with_turns += 1
        for m in TURN.finditer(text):
            turn, _who, lvl, cur, mx, action, _foe, foelvl = m.groups()
            if turn != "0" or cur != mx:
                continue
            gap = int(foelvl) - int(lvl)
            if gap < 0:
                continue
            decisions += 1
            bucket = by_gap[min(gap, 8)]
            bucket[1] += 1
            if action.startswith("RotateLead"):
                bucket[0] += 1
    return by_gap, len(files), with_turns, decisions


def main() -> int:
    roots = [ROOT / "sandbox-pokebot" / "profiles", ROOT / "tools" / "story-dev" / "x4-runs"]
    by_gap, n_files, with_turns, decisions = measure(roots)

    print("=" * 92)
    print("SWAP-TRAINING ENVELOPE — at what level gap does the bot actually switch?")
    print("=" * 92)
    print(f"  scanned   : {n_files:,} .log files under {[r.name for r in roots]}")
    print(f"  with turns: {with_turns:,}")
    print(f"  decisions : {decisions:,}   (turn 0 only, trainee at FULL HP, gap >= 0)")
    if not decisions:
        print("\n  ⛔ no matching telemetry found — nothing can be concluded from this run.")
        print("=" * 92)
        return 0

    print(f"\n  {'gap':>5} {'rotated':>9} {'total':>9} {'rate':>8}")
    rotated_total = 0
    for g in sorted(by_gap):
        rot, tot = by_gap[g]
        rotated_total += rot
        label = f"+{g}" if g < 8 else ">=+8"
        print(f"  {label:>5} {rot:>9,} {tot:>9,} {100 * rot / tot if tot else 0:>7.1f}%")

    fired = [g for g in sorted(by_gap) if by_gap[g][0] > 0]
    print()
    print(f"  rotations in THIS population : {rotated_total:,}")
    print( "     ‼ that is the sum of the column above — turn-0, full-HP, gap >= 0 decisions ONLY.")
    print( "       It is NOT every rotation in the corpus; unrestricted the count is far higher.")
    print(f"  highest gap with a rotation  : +{max(fired) if fired else 'NONE OBSERVED'}")
    print( "     ⚠ a zero at a gap means NOT OBSERVED, not REFUSED — the strategy may never have")
    print( "       been installed in the runs that reached it (see the module docstring).")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
