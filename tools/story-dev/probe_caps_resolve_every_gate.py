# -*- coding: utf-8 -*-
"""⛔ GATE: EVERY GATE STRING THE EDGE TABLE USES MUST BE RESOLVABLE. (`#24-waterfallcap`)

THE BUG THIS EXISTS TO MAKE IMPOSSIBLE. `region_reach.py` keeps the same fact in three places:
  * `KNOWN_GATES` (`:81-98`) — which map-boundary edges are gated, and on WHICH capability string.
  * `_GATE_MOVE_NAMES` (`:100-106`) — that capability string -> the field-move name.
  * `_resolve_caps` (`:228-236`) — which capability strings actually get RESOLVED to True/False.
Nothing made them agree. On 2026-07-26 a `"waterfall"` edge was added to `KNOWN_GATES` and the move
name was added to `_GATE_MOVE_NAMES` and the badge to `_RSE_BADGE_BY_MOVE` — **three of the four
pieces** — while `_resolve_caps` kept a hardcoded four-key literal. `_bfs_distances` (`:342`) drops
any edge whose gate is missing from `caps`, so the result was not "the gate is open" or "the gate is
closed" but **a gate that can never open, for anybody, ever**.

⛔⛔ THAT IS THIS PROJECT'S WORST FAILURE SHAPE: **IT FAILS BY BEING QUIET.** There is no exception,
no warning, and `is_map_reachable` is fail-safe, so the wrong answer is indistinguishable from a
legitimate refusal. MEASURED: a bot standing at the Victory Road grind tile believed the entire
world was 3 maps (`evidence/2026-09-18-waterfall-capability.stdout.txt`).

⭐ WHY A GATE AND NOT A COMMENT. The project rule is that anything enforceable belongs in a gate,
because a rule already broken once is evidence that prose failed. A sixth gate string added to
`KNOWN_GATES` tomorrow would re-create this bug silently; this gate turns that into a red build.

READ-ONLY, and NO EMULATOR: it inspects the tables and the resolver's KEYS, never its values, so it
needs no ROM and runs in milliseconds. (Values depend on a live party; keys do not — and it is the
KEYS that encode the bug.)

FAULT ARM: `POKEBOT_CAPS_FAULT_DROPKEY=<gate>` removes that key from the resolver's output, proving
this gate actually fires. Run `POKEBOT_CAPS_FAULT_DROPKEY=surf py -3.12 probe_caps_resolve_every_gate.py`
and it must FAIL naming `surf`.
"""
import os
import pathlib as _pl
import sys

# ‼ THIS GATE PRINTS ⭐/⛔/ℹ, AND ITS OWN DOCSTRING TELLS YOU TO RUN IT STANDALONE.
# `run_gates.py` forces PYTHONUTF8/PYTHONIOENCODING for its subprocesses, so the suite masked the
# fact that a bare `py -3.12 probe_caps_resolve_every_gate.py` on this project's default Windows
# console died with UnicodeEncodeError before printing a single finding. A gate whose documented
# reproduction crashes teaches the reader to distrust it. Every sibling gate does this; so does this.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

#: BUILD-AWARE (2026-09-23). This gate asserts an INVARIANT about `region_reach`, and that
#: invariant has to hold in BOTH forks -- but the import path was hardcoded to `sandbox-pokebot`,
#: so after a promotion nothing checked custom's copy. That is the exact hole `promote.py`'s
#: docstring records paying for on 2026-08-14: "the gate that proved the promoted fix hard-coded
#: `sandbox-pokebot` on its import path, so nothing verified the fix had actually landed."
#: The invariant here is the one `#24-waterfallcap` was: a gate string in `KNOWN_GATES` whose
#: resolver was never wired produces an edge that can NEVER open, and `is_map_reachable` is
#: fail-safe, so the wrong refusal is indistinguishable from a right one. Worth checking twice.
#:     PYTHONUTF8=1 py -3.12 probe_caps_resolve_every_gate.py --build custom
_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
_BUILD = ("custom" if "--build" in sys.argv
          and sys.argv[sys.argv.index("--build") + 1] == "custom" else "sandbox")
sys.path.insert(0, str(_ROOT / f"{_BUILD}-pokebot"))

from modules.story import region_reach

print("=" * 96)
print(f"GATE: every gate string used by KNOWN_GATES must be resolvable by _resolve_caps"
      f"   [build={_BUILD}]")
print("=" * 96)

used = sorted({gate for gate in region_reach.KNOWN_GATES.values() if gate is not None})
named = sorted(region_reach._GATE_MOVE_NAMES)
print(f"  KNOWN_GATES uses      : {used}")
print(f"  _GATE_MOVE_NAMES knows: {named}")

# `_resolve_caps` reads live party/badge state through `_live_capability`, which is wrapped in its
# own try/except and returns False with no ROM. We only inspect the KEYS, so no emulator is needed.
resolved = region_reach._resolve_caps(None, None, None, None, None)

_fault = os.environ.get("POKEBOT_CAPS_FAULT_DROPKEY", "").strip()
if _fault:
    resolved = {k: v for k, v in resolved.items() if k != _fault}
    print(f"  \u26a0 FAULT ARM ACTIVE: dropped {_fault!r} from the resolver's output")

print(f"  _resolve_caps resolves: {sorted(resolved)}")
print()

failures = []

# (1) THE BUG ITSELF: a gated edge whose gate nothing resolves is an edge that can never open.
for gate in used:
    if gate not in resolved:
        failures.append(
            f"KNOWN_GATES gates an edge on {gate!r}, but _resolve_caps never resolves it \u21d2 "
            f"`caps.get({gate!r}, False)` is ALWAYS False, so that edge is permanently sealed "
            f"for every party at every badge count. This is not a closed gate, it is a wall.")

# (2) THE OTHER HALF OF THE PAIR: a gate string with no move name can never be resolved either.
for gate in used:
    if gate not in region_reach._GATE_MOVE_NAMES:
        failures.append(
            f"KNOWN_GATES gates an edge on {gate!r}, which is absent from _GATE_MOVE_NAMES \u21d2 "
            f"no move name exists to look a capability up by.")

# (3) \u203c NOT A FAILURE, BUT SAY IT: a move name nothing gates on is harmless, but it is usually the
#     footprint of a half-landed change \u2014 exactly the state this file was written about.
unused = [g for g in named if g not in used]
if unused:
    print(f"  \u2139 NOTE (not a failure): _GATE_MOVE_NAMES knows {unused}, which KNOWN_GATES does not")
    print(f"    currently gate on. Harmless \u2014 but if a gate string is being ADDED, this is the")
    print(f"    half-finished state to look for.")
    print()

if failures:
    print("\u26d4 FAIL")
    for f in failures:
        print(f"  \u2022 {f}")
    print("=" * 96)
    raise SystemExit(1)

print(f"  \u2705 PASS \u2014 all {len(used)} gate string(s) used by KNOWN_GATES resolve.")
print("=" * 96)
