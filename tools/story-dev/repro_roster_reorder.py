"""REPRO — the party-reorder PLANNER, exhaustively. No emulator, milliseconds.

‼ WHY THE PLANNER IS SPLIT FROM THE DRIVER, AND WHY ONLY THIS HALF IS PROVEN HERE. Reordering the
party is two problems: *which swaps* (pure arithmetic) and *driving the party menu* (KI-38
territory — four unbounded loops and a `set_manual_mode()` trapdoor, and `RotatePokemon(i, j)` with
`j != 0` has never been driven in this project). Keeping them apart means the arithmetic can be
proven to exhaustion in milliseconds, so that when the driven test eventually fails, the planner is
already ruled out.

WHAT THIS PROVES:
  1. **Every permutation of six.** All 720 target orders reachable, each in <= 5 swaps, each
     verified by APPLYING the returned swaps and comparing. A planner that returns plausible pairs
     without ever being replayed is not proven — so this replays every one.
  2. **The already-correct case is FREE** (zero swaps). This runs before content that may already
     be satisfied, so "no work needed" must cost nothing.
  3. **The REGI shape** — "species X first, species Y last" — which is the requirement that
     motivated the whole module, via `plan_last_slot`.
  4. **It refuses impossible requests** rather than reordering around them: a PID that is not in
     the party, and asking for the same Pokémon to be both first and last.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_roster_reorder.py
"""

import itertools
import argparse
import pathlib
import sys

# ‼ `--build` — added 2026-08-23 (`#24-p4residuals` (e)). This gate hardcoded
# `sandbox-pokebot`, so the identical defect landing in `custom-pokebot` — THE FORK THAT
# SHIPS — was invisible to it. Default stays `sandbox` so nothing about the standing suite
# changes; `--build custom` is for verifying a promotion. Idiom copied from
# `repro_pid_identity_key.py`, which already had it.
_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"],
                 help="which fork to test (default sandbox; use custom to verify a promotion)")
_ARGS, _ = _ap.parse_known_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
_FORK = REPO / f"{_ARGS.build}-pokebot"
if not _FORK.is_dir():
    raise SystemExit(f"‼ no such fork: {_FORK} — refusing to report success")
sys.path.insert(0, str(_FORK))

from modules.story.roster import MAX_SWAPS, plan_last_slot, plan_reorder

BAR = "=" * 96
results = []


def check(label, ok, detail=""):
    results.append((label, ok))
    print(f"  {'[AS PREDICTED]' if ok else '[‼ FAIL]'} {label}")
    if detail:
        print(f"        {detail}")


def apply_swaps(order, swaps):
    """Replay the plan. ‼ The planner is only proven if its output is EXECUTED and compared."""
    out = list(order)
    for i, j in swaps:
        out[i], out[j] = out[j], out[i]
    return out


print(BAR)
print("REPRO — the party-reorder planner (pure; the menu driver is proven separately)")
print(BAR)

PARTY = [111, 222, 333, 444, 555, 666]  # stand-in personality values

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n1 — EVERY permutation of six: reachable, replayed, and within the bound\n{BAR}\n")

worst = 0
failures = []
for target in itertools.permutations(PARTY):
    plan = plan_reorder(PARTY, list(target))
    got = apply_swaps(PARTY, plan)
    if got != list(target):
        failures.append((target, plan, got))
    worst = max(worst, len(plan))

check(f"all {720} permutations reachable and replay EXACTLY", not failures,
      f"worst plan = {worst} swap(s); failures = {len(failures)}")
check(f"no plan exceeds the MAX_SWAPS bound of {MAX_SWAPS}", worst <= MAX_SWAPS,
      f"worst observed {worst}")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n2 — The already-correct case costs NOTHING\n{BAR}\n")

check("an already-correct party plans ZERO swaps", plan_reorder(PARTY, PARTY) == [])
check("a prefix that already holds plans ZERO swaps", plan_reorder(PARTY, [111, 222]) == [])
print("        (this matters: the reorder runs before content that may already be satisfied)")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n3 — THE REGI SHAPE: ‼ WAILORD first, RELICANTH last (EMERALD order)\n{BAR}\n")

# ‼‼ THE ORDER IS THE OPPOSITE OF THE ONE EVERYONE REMEMBERS, AND GETTING IT WRONG FAILS SILENTLY.
# `src/braille_puzzles.c:92-104` `CheckRelicanthWailord()`:
#     if gPlayerParty[0]                     == SPECIES_WAILORD
#     and gPlayerParty[gPlayerPartyCount-1]  == SPECIES_RELICANTH
# The decomp carries the comment "Emerald change: why did they flip it?" — **Ruby/Sapphire is
# Relicanth-first, Emerald is WAILORD-first.** On a mismatch `VAR_RESULT` is FALSE and the script
# falls to `_NoEffect`: no message, no error, nothing happens. That is exactly the failure shape
# this project keeps getting caught by, so the order is pinned here in a test rather than trusted
# to anyone's memory.
# ‼ Also note: the party does NOT need to be six. It reads `gPlayerPartyCount - 1`, so a party of
# exactly TWO (Wailord, Relicanth) satisfies it — which is why the spec is built from the LIVE
# party rather than assuming six slots.
WAILORD, RELICANTH = 333, 111          # deliberately mis-seated to start, so the plan must work
spec = plan_last_slot(PARTY, WAILORD, RELICANTH)
plan = plan_reorder(PARTY, spec)
final = apply_swaps(PARTY, plan)
print(f"  party  {PARTY}")
print(f"  spec   {spec}")
print(f"  plan   {plan}")
print(f"  result {final}")
check("WAILORD ends up FIRST (Emerald order, not R/S)", final[0] == WAILORD)
check("RELICANTH ends up LAST", final[-1] == RELICANTH)
check("everything else keeps its relative order",
      [p for p in final if p not in (WAILORD, RELICANTH)]
      == [p for p in PARTY if p not in (WAILORD, RELICANTH)],
      "a team built over a whole run must not be reshuffled as a side effect")
check(f"and it costs at most {MAX_SWAPS} swaps", len(plan) <= MAX_SWAPS, f"{len(plan)} swap(s)")

# ‼ A TWO-MON PARTY MUST ALSO SATISFY IT — `gPlayerPartyCount - 1` is the LIVE count.
pair = [WAILORD, RELICANTH]
check("a party of exactly TWO satisfies the shape with zero swaps",
      plan_reorder(pair, plan_last_slot(pair, WAILORD, RELICANTH)) == [],
      "the tomb check reads gPlayerPartyCount-1, so six slots are not required")

# ‼ THE CASE THAT LOOKS FINE AND IS NOT: pinning only slot 0 leaves the LAST slot to chance.
naive = plan_reorder(PARTY, [WAILORD])
naive_final = apply_swaps(PARTY, naive)
check("‼ a spec that pins ONLY slot 0 does NOT pin the last slot (why plan_last_slot exists)",
      naive_final[-1] != RELICANTH,
      f"naive result {naive_final} — last slot is {naive_final[-1]}, not {RELICANTH}")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n4 — It REFUSES impossible requests instead of quietly reordering around them\n{BAR}\n")

missing_refused = False
try:
    plan_reorder(PARTY, [999])
except ValueError:
    missing_refused = True
check("asking for a PID that is not in the party raises", missing_refused,
      "silently ignoring it would leave content gated on an order it never got")

same_refused = False
try:
    plan_last_slot(PARTY, RELICANTH, RELICANTH)
except ValueError:
    same_refused = True
check("asking for the same mon first AND last raises", same_refused,
      "otherwise it plans nothing and looks like success")

# ‼ THE OSCILLATION HOLE, found by an adversarial review before the driver was ever run.
# A spec repeating a PID is unsatisfiable, and planning around it is the worst outcome:
# `order.index(pid)` returns the slot it was ALREADY placed in, so the swap undoes previous work
# and the plan NEVER converges — the driver would perform real menu swaps for its entire budget
# and then report failure with a scrambled party. `plan_last_slot` guarded `first == last`, but a
# direct `plan_reorder([pid, pid])` did not.
dup_refused = False
try:
    plan_reorder(PARTY, [WAILORD, WAILORD])
except ValueError:
    dup_refused = True
check("a spec that REPEATS a pid raises (it would otherwise never converge)", dup_refused,
      "one Pokémon cannot occupy two slots — planning around it burns the whole swap budget")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n5 — Smaller parties (the bot does not always carry six)\n{BAR}\n")

small = [11, 22, 33]
ok_small = True
for target in itertools.permutations(small):
    if apply_swaps(small, plan_reorder(small, list(target))) != list(target):
        ok_small = False
check("every permutation of a THREE-mon party also replays exactly", ok_small)
# ‼ THE ORDER OF THE TWO GUARDS MATTERS, and the first draft of this check got it backwards.
# `plan_reorder` validates that every target PID is in the party BEFORE it plans anything, so a
# spec containing an unknown PID RAISES — it is never silently truncated. That precedence is the
# safer one (a caller asking for a Pokémon we do not have is a bug, not a rounding error), so the
# check now asserts the precedence rather than the truncation.
raised_before_truncating = False
try:
    plan_reorder(small, [33, 22, 11, 999999])
except ValueError:
    raised_before_truncating = True
check("an over-long spec containing an UNKNOWN pid raises (validation precedes truncation)",
      raised_before_truncating,
      "asking for a mon we do not have is a caller bug — refusing beats quietly reordering")
check("a spec exactly as long as the party is honoured in full",
      apply_swaps(small, plan_reorder(small, [33, 22, 11])) == [33, 22, 11])

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\nSUMMARY\n{BAR}\n")
for label, ok in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
passed = sum(1 for _l, ok in results if ok)
print(f"\n  {passed} / {len(results)} checks pass.")
if passed != len(results):
    print("\nRESULT: FAIL")
    raise SystemExit(1)
print("\nRESULT: ALL PASS — the PLANNER is proven exhaustively.")
print("\n‼ THE DRIVER IS NOT PROVEN BY THIS FILE AND MUST NOT BE DESCRIBED AS SUCH.")
print("  `reorder_party()` drives `RotatePokemon`, whose cursor loops are unbounded (KI-38) and")
print("  which has NEVER been driven with a non-zero destination in this project. It needs a live")
print("  driver before any content depends on party ORDER.")
