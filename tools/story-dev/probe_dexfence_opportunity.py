# -*- coding: utf-8 -*-
"""Does `#24-dexhunt`'s catching fence have an OPPORTUNITY WINDOW at all? Measured, not argued.

⛔⛔ WHY THIS EXISTS. `04-HANDOFF.md` carries this warning against the item:

    "NO CHEAP FIXTURE TEST EXISTS FOR THIS ITEM — a Tier 2 auditor tried and could not compute a
     discriminator. Grading needs an hours-long `x4_headless.py --build sandbox` batch."

That is true of the fence's EFFICACY (does catching raise the dex?) and it stays true. But it was
being read as though the *precondition* were unmeasurable too, and it is not. The fence fires only
in a specific run state:

    BADGE01_GET set  AND  party == 6  AND  no hunt armed  AND  spare balls  AND  species unowned

If that state never occurs, an 8-hour A/B returns "no difference" — which reads as a REFUTATION of a
feature that never ran. That is this project's most expensive documented failure shape (`08-MISTAKES`
2026-09-09: a mandatory test that was vacuous for the thing it tested). **The precondition is
answerable RIGHT NOW, offline, from the recorded corpus — no ROM, no emulator, no batch.**

⭐ WHAT IT MEASURES, per lane and in aggregate:
  * the party-size histogram over every heartbeat (`ids=[...]` is the authority, NOT `party=[...]`
    — see the parser note below);
  * how many heartbeats sit at party >= 6, which IS the fence's opportunity window;
  * WHERE and WHEN the run first reaches party 6 (frame + map), so "after badge 1" is READ off the
    geography rather than assumed;
  * the `owned=<n>` dex trajectory, which is both the baseline the directive wants to raise and the
    thing an A/B would grade on.

‼ WHAT IT DOES *NOT* MEASURE, stated so nobody cites it for more than it says:
  * It cannot see whether a hunt was ARMED at a given heartbeat — that is not logged. So the window
    reported here is an UPPER BOUND on the fence's opportunity; the armed-hunt fraction subtracts
    from it. (`counter_hunt` spins are bounded at HUNT_SPIN_BUDGET_FRAMES = 120,000 frames, so the
    subtraction is small, but it is NOT zero and this tool must not be quoted as if it were.)
  * It cannot see ball counts.
  * It says nothing about whether catching HELPS. Opportunity is a precondition for the A/B, never
    a result of it.

‼ HEARTBEAT PARSER NOTE — `ids=[...]`, NOT `party=[...]`. Both fields exist and both list the party,
but `party=['Torchic:L5']` carries no stable identity while `ids=['Torchic#3E751CAF:L5:exp135']`
does. Counting from `ids` also means this tool silently reports ZERO on a `--build custom` corpus
(where the field does not exist) instead of quietly measuring the wrong thing — a loud zero is a
better failure than a plausible number. See `04-HANDOFF.md`: `--build sandbox` IS MANDATORY.

FAULT ARM (self-test — the reason this probe can be believed):
    POKEBOT_DEXFENCE_PROBE_FAULT=1 PYTHONUTF8=1 py -3.12 probe_dexfence_opportunity.py
raises the party-6 threshold to 7, which is IMPOSSIBLE in Gen 3 (`PARTY_SIZE == 6`). The window must
then collapse to zero and the script must exit 1. A probe that passes in both arms measures nothing.

USAGE
    PYTHONUTF8=1 py -3.12 probe_dexfence_opportunity.py [<batch-dir> ...]
With no argument it scans every batch under `x4-runs/` that carries the sandbox telemetry.
"""
from __future__ import annotations

import collections
import glob
import os
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).resolve().parent
RUNS = HERE / "x4-runs"

FAULT = os.environ.get("POKEBOT_DEXFENCE_PROBE_FAULT", "").strip()

#: Gen 3's party is six. The fence admits a catch ONLY at a FULL party, because that is the state in
#: which the game stores the catch via `CopyMonToPC` instead of consuming a party slot — and
#: `#24-partycap` MEASURED that consuming party slots costs 36 points of finish rate (52.0% -> 15.8%),
#: because the empty slots are the runway HM and counter catches land on.
#: ⛔ The fault arm sets this to 7 to prove the window is really being computed from the data.
FULL_PARTY = 7 if FAULT else 6

#: A heartbeat is emitted once per in-game minute of emulated time, so a heartbeat COUNT is directly
#: readable as emulated minutes. (`04-HANDOFF.md` 2026-09-09 uses the same equivalence: "median 163
#: heartbeats = 163 MINUTES".)
HEARTBEAT_MINUTES = 1

_HB = re.compile(
    r"^f(?P<frame>\d+) \[hb\].*?map=(?P<map>[^(]*)\([^)]*\).*?ids=\[(?P<ids>.*?)\] owned=(?P<owned>\d+)"
)


def _party_size(ids: str) -> int:
    """Members in an `ids=[...]` field. Empty list is 0; otherwise commas + 1.

    ‼ A species name cannot contain a comma and the PID/level/exp suffixes are comma-free, so
    comma-counting is exact here. It is NOT exact for `party=[...]` in every build, which is the
    second reason this tool reads `ids`.
    """
    ids = ids.strip()
    return 0 if not ids else ids.count(",") + 1


def scan_lane(lane: pathlib.Path) -> dict:
    sizes: collections.Counter[int] = collections.Counter()
    owned_at_full: list[int] = []
    owned_seen: list[int] = []
    first_full: tuple[str, str] | None = None
    total = 0

    for log in sorted(lane.rglob("*.log")):
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.split("\n"):
            m = _HB.match(line)
            if not m:
                continue
            total += 1
            n = _party_size(m.group("ids"))
            sizes[n] += 1
            owned = int(m.group("owned"))
            owned_seen.append(owned)
            if n >= FULL_PARTY:
                owned_at_full.append(owned)
                if first_full is None:
                    first_full = (m.group("frame"), m.group("map").strip())

    return {
        "lane": lane.name,
        "heartbeats": total,
        "sizes": dict(sorted(sizes.items())),
        "window": sum(c for s, c in sizes.items() if s >= FULL_PARTY),
        "first_full": first_full,
        "owned_at_full": owned_at_full,
        "owned_max": max(owned_seen) if owned_seen else 0,
    }


def main(argv: list[str]) -> int:
    if argv:
        batches = [pathlib.Path(a) for a in argv]
    else:
        batches = [p for p in sorted(RUNS.glob("*")) if p.is_dir()]

    print("=" * 100)
    print("DEX-FENCE OPPORTUNITY — can `#24-dexhunt`'s fence EVER fire? (offline, from the run corpus)")
    if FAULT:
        print(f"  ⛔ FAULT ARM ACTIVE: FULL_PARTY={FULL_PARTY} (impossible in Gen 3) — the window MUST be 0")
    print("=" * 100)

    grand_window = 0
    grand_hb = 0
    lanes_reaching_full = 0
    lanes_total = 0
    all_owned_at_full: list[int] = []
    scanned_batches = 0

    for batch in batches:
        lanes = [p for p in sorted(batch.glob("L*")) if p.is_dir()]
        if not lanes:
            continue
        rows = [scan_lane(l) for l in lanes]
        if not any(r["heartbeats"] for r in rows):
            continue  # a `--build custom` batch: no `ids=`/`owned=` telemetry at all
        scanned_batches += 1
        print(f"\n--- {batch.name} ---")
        for r in rows:
            lanes_total += 1
            grand_hb += r["heartbeats"]
            grand_window += r["window"]
            all_owned_at_full.extend(r["owned_at_full"])
            if r["window"]:
                lanes_reaching_full += 1
            where = (
                f"first@f{r['first_full'][0]} on {r['first_full'][1][:24]}"
                if r["first_full"]
                else "NEVER reached a full party"
            )
            pct = (100.0 * r["window"] / r["heartbeats"]) if r["heartbeats"] else 0.0
            print(
                f"  {r['lane']}  hb={r['heartbeats']:<6} window={r['window']:<6} ({pct:4.1f}%)  "
                f"owned_max={r['owned_max']:<3} {where}"
            )
            print(f"        party-size histogram: {r['sizes']}")

    print("\n" + "=" * 100)
    if not scanned_batches:
        print("  ⛔ NO SANDBOX-TELEMETRY BATCH FOUND. `ids=`/`owned=` are sandbox-only fields.")
        print("     Re-run the batch as `x4_headless.py --build sandbox` — a `custom` batch emits NOTHING")
        print("     here and would read as a refutation. (`04-HANDOFF.md`: `--build sandbox` IS MANDATORY.)")
        return 1

    pct = (100.0 * grand_window / grand_hb) if grand_hb else 0.0
    print(f"  lanes reaching a FULL party : {lanes_reaching_full} of {lanes_total}")
    print(f"  fence OPPORTUNITY WINDOW    : {grand_window} of {grand_hb} heartbeats ({pct:.1f}%)")
    print(f"                              ~= {grand_window * HEARTBEAT_MINUTES} emulated MINUTES across the corpus")
    if all_owned_at_full:
        print(
            f"  dex `owned` while at party 6 : min {min(all_owned_at_full)} / "
            f"max {max(all_owned_at_full)}  ⇒ the headroom an A/B would grade on"
        )
    print("  ‼ UPPER BOUND: armed-hunt heartbeats are not logged and are NOT subtracted here.")
    print("=" * 100)

    if grand_window <= 0:
        print("  VERDICT: NO OPPORTUNITY — the fence could never fire on this corpus.")
        print("           An A/B would print 'no difference', which must NOT be read as a refutation.")
        return 1

    print(f"  VERDICT: THE FENCE HAS AN OPPORTUNITY WINDOW ({lanes_reaching_full}/{lanes_total} lanes). Not vacuous.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
