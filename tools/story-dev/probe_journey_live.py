"""#24-journey / KI-39 — LIVE fault-injected A/B in the FAITHFUL harness.

`repro_journey_planner.py` proves the PLANNER returns the Rusturf Tunnel route. That is not
the same claim as "the bot arrives", so this drives the real `navigate_to_anywhere` through
`story_harness.py --driver journey`, which replicates the actual main loop (listeners
included) — battles get fought, scenes get ridden out, and an arrival means something.

‼ WHY THE HARNESS AND NOT A BARE GENERATOR. Measured 2026-07-31: driving
`navigate_to_anywhere` directly, with no bot listeners, the Mauville -> Route 116 journey
died at 717 frames on "We unexpectedly triggered a scripted event" — Route 117's forced
doubles. That is the bare driver's artefact, not the planner's. `FieryCaveMode`'s docstring
in `story_harness.py` records the same lesson from 2026-07-26; this is the second time it
has been paid for, so it is now written into the driver itself.

THE ARMS (same save, same target, same executor, same emulator build):
  OLD — `warp_candidates`/`plan` monkeypatched to `[]`, exactly what the pre-fix code saw
        for a same-region pair.
  NEW — untouched.

MEASURED RESULT, `rocksmash_taught.ss1` (Mauville 32,15):
  | target           | OLD arm                        | NEW arm                        |
  |------------------|--------------------------------|--------------------------------|
  | ROUTE116 (72,8)  | fails, still on MAUVILLE_CITY  | ARRIVED, 33,725 frames         |
  | ROUTE116 (11,7)  | fails, still on MAUVILLE_CITY  | reaches ROUTE116, tile refused |

The second row is an HONEST refusal, not a bug: the Rusturf Tunnel's middle is sealed by the
Wanda-quest rocks in this save, so the tunnel's east door drops the player into a Route 116
pocket spanning only x=66..81 of a 100-wide map. Measured from the landing tile (65,11):
14 of 340 sampled tiles reachable, and (11,7) is not one of them. The bot crossing three
maps and a warp and then correctly reporting that the last tile is unreachable is the
system working.

Run (a few minutes per arm — NOT part of the repro sweep, which is why this is a `probe_`
and the fast pure-logic pinning lives in `repro_journey_planner.py`):
    PYTHONUTF8=1 py -3.12 tools/story-dev/probe_journey_live.py
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SAVE = "rocksmash_taught.ss1"
FRAMES = 600_000

#: (label, JOURNEY_TARGET, arm, expected arrived, expected final map)
CASES = [
    ("OLD arm — planner blinded as the pre-fix code was", "ROUTE116:72,8", "old", False, "MAUVILLE_CITY"),
    ("NEW arm — the shipped planner", "ROUTE116:72,8", "new", True, "ROUTE116"),
    # ‼ The control matters as much as the fix: a planner that started routing every walk
    # through a warp detour would be a regression wearing a fix's clothes.
    ("CONTROL — a plainly walkable target must be untouched", "ROUTE117:31,16", "new", True, "ROUTE117"),
]

#: Two harness processes must never share a profile directory (they clash on
#: `current_state.ss1` / `current_save.sav` — livetest.py learned this the hard way).
PROFILES = ["repro-live3", "repro-live4", "repro-live5"]

RESULT_RE = re.compile(r"\[journey\] RESULT arm=(\S+) arrived=(\S+) map=(\S+) detail=(.*)")
FAILURES: list[str] = []


def run_arm(target: str, arm: str, profile: str) -> tuple[bool, str, str]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["JOURNEY_ARM"] = arm
    env["JOURNEY_TARGET"] = target
    try:
        proc = subprocess.run(
            ["py", "-3.12", str(HERE / "story_harness.py"), SAVE,
             "--driver", "journey", "--frames", str(FRAMES), "--profile", profile],
            cwd=HERE, env=env, capture_output=True, text=True, errors="replace", timeout=2400,
        )
    except subprocess.TimeoutExpired:
        return False, "?", "harness timed out"
    for line in (proc.stdout + proc.stderr).splitlines():
        match = RESULT_RE.search(line)
        if match:
            return match.group(2) == "True", match.group(3), match.group(4).strip()
    return False, "?", "no RESULT line — the harness died before the driver reported"


def main() -> int:
    print(f"save={SAVE}  frames={FRAMES:,}\n")
    for i, (label, target, arm, want_arrived, want_map) in enumerate(CASES):
        print(f"{label}\n  target={target} arm={arm}")
        arrived, final_map, detail = run_arm(target, arm, PROFILES[i % len(PROFILES)])
        print(f"  -> arrived={arrived} map={final_map}  {detail}")
        ok = (arrived == want_arrived) and (final_map == want_map)
        print(f"  {'PASS' if ok else 'FAIL'}  expected arrived={want_arrived} map={want_map}\n")
        if not ok:
            FAILURES.append(label)
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
        return 1
    print("ALL PASS — the OLD arm never leaves Mauville; the NEW arm walks Mauville -> "
          "Route 117 -> Verdanturf -> Rusturf Tunnel -> Route 116 and arrives.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
