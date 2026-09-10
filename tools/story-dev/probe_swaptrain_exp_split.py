# -*- coding: utf-8 -*-
"""THE SWAP-TRAINING EXP SPLIT — does a rotated-out trainee earn FULL exp, or a SHARE?

⛔⛔ WHY THIS DECIDES REAL WORK. `#24-lowlevelmules`'s planned fix ("catch higher, train the
remainder") was costed with `estimate_frames_to_level`, which models a SOLO fight. If swap-training
splits exp two ways, every estimate is up to 2x optimistic and the arrival level that clears the
250,000-frame ceiling is **L42, not L35** — at which point the planned fix **refuses anyway**. The
project has carried that as "⚠ Not proven" for weeks because the measurement was BLOCKED: party
snapshots carried `Species:L<lv>` and nothing stable, so no mon could be followed across readings.
✅ UNBLOCKED 2026-09-09 by `party_ids` (`modules/debug_logger.py`), which logs
`ids=['Species#PID:L<lv>:exp<n>', ...]` every heartbeat.

⛔ RUN IT ONLY AGAINST A `--build sandbox` BATCH. `x4_headless.py` defaults to `custom`, and
`custom-pokebot/modules/debug_logger.py` has NO `party_ids` (measured: 0 occurrences) ⇒ a default
batch produces zero windows and this tool would print "no data", which reads exactly like "no
effect". The tool says so out loud when it finds no `ids=` at all.

HOW IT MEASURES, and the guard that makes it honest:
  * a heartbeat is ~1 per 3,600 frames; a battle is shorter ⇒ a battle normally sits BETWEEN two
    heartbeats, giving a clean before/after pair of per-PID exp;
  * ‼ **A WINDOW IS USED ONLY IF IT CONTAINS EXACTLY ONE BATTLE.** Two battles in one window would
    attribute both payouts to one event — the "an aggregate cannot attribute" failure this project
    has logged. Multi-battle windows are COUNTED AND REPORTED, never silently dropped.
  * the swap-training signature is a **turn-0, full-HP** `RotateLead` (a later, hurt rotation is an
    emergency survival switch — a different mechanic). Measured in a 12-min smoke: of **32**
    rotations, **31** were turn>0 and HURT and exactly **1** was the turn-0 full-HP signature.
    ‼ This read '30 of 31' until 2026-09-09: the parser dropped `[TURN 3] ... 3/23 [Infatuated]`
    because it did not allow a STATUS TAG between HP and the arrow. See the note on `TURN`.

Always exits 0 — an OBSERVATION tool, not a gate.
"""
import argparse
import collections
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent

FRAME = re.compile(r"^f(\d+)\s")
IDS = re.compile(r"ids=\[([^\]]*)\]")
ONE_ID = re.compile(r"'(\w+)#([0-9A-F?]{8}):L(\d+):exp(\d+)'")
TURN = re.compile(r"\[TURN (\d+)\]\s+(\w+)\s+L(\d+)\s+(\d+)/(\d+)\s*(?:\[[^\]]*\]\s*)?->\s*(\w+).*?vs\s+(\w+)\s+L(\d+)")
BATTLE_ANY = re.compile(r"\[TURN \d+\]")


def parse_ids(line):
    m = IDS.search(line)
    if not m:
        return None
    return {pid: (sp, int(lv), int(exp)) for sp, pid, lv, exp in ONE_ID.findall(m.group(1))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batch", default="latest", help="batch dir under x4-runs, or 'latest'")
    a = ap.parse_args()

    runs = HERE / "x4-runs"
    if a.batch == "latest":
        cands = sorted([p for p in runs.iterdir() if p.is_dir() and list(p.glob("L0*"))])
        if not cands:
            print("  ⛔ no batches under x4-runs.")
            return 0
        bdir = cands[-1]
    else:
        bdir = runs / a.batch
    logs = sorted(bdir.rglob("*.log"))

    print("=" * 102)
    print(f"SWAP-TRAINING EXP SPLIT — batch {bdir.name}")
    print("=" * 102)

    windows = []          # (rotated_out_pid, gains dict, foe_level, trainee_level)
    multi = single = no_rot = 0
    ids_lines = 0

    for f in logs:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:  # noqa: BLE001
            continue
        beats = []        # (index, frame, ids)
        for i, line in enumerate(lines):
            fm = FRAME.match(line)
            if not fm:
                continue
            d = parse_ids(line)
            if d:
                ids_lines += 1
                beats.append((i, int(fm.group(1)), d))

        for (i0, _f0, d0), (i1, _f1, d1) in zip(beats, beats[1:]):
            seg = lines[i0 + 1:i1]
            n_battles = sum(1 for l in seg if BATTLE_ANY.search(l) and "[TURN 0]" in l)
            if n_battles == 0:
                continue
            if n_battles > 1:
                multi += 1
                continue
            single += 1
            rot = None
            for l in seg:
                m = TURN.search(l)
                if m and m.group(6) == "RotateLead" and m.group(1) == "0" \
                        and m.group(4) == m.group(5):
                    rot = m
                    break
            if rot is None:
                no_rot += 1
                continue
            gains = {pid: d1[pid][2] - d0[pid][2] for pid in d0 if pid in d1
                     and d1[pid][2] > d0[pid][2]}
            if not gains:
                continue
            trainee_sp, trainee_lv = rot.group(2), int(rot.group(3))
            out_pid = next((p for p, v in d0.items() if v[0] == trainee_sp and v[1] == trainee_lv),
                           None)
            windows.append((out_pid, gains, int(rot.group(8)), trainee_lv))

    print(f"  logs: {len(logs)}   heartbeats with ids=: {ids_lines:,}")
    if ids_lines == 0:
        print("\n  ⛔⛔ NO `ids=` FIELD IN ANY LOG. This is almost certainly a `--build custom` batch:")
        print("      `party_ids` exists ONLY in sandbox-pokebot. Re-run with `--build sandbox`.")
        print("      ‼ DO NOT read this as 'no effect' — it is 'no instrument'.")
        print("=" * 102)
        return 0

    print(f"  single-battle windows: {single:,}   ⛔ multi-battle EXCLUDED: {multi:,}   "
          f"no turn-0 full-HP rotation: {no_rot:,}")
    print(f"  USABLE swap-training windows: {len(windows):,}")
    if not windows:
        print("\n  ⚠ none yet — turn-0 full-HP rotations are rare early (measured: 1 in 32 in a")
        print("    12-minute smoke). Let the batch run longer, then re-run this.")
        print("=" * 102)
        return 0

    n_gainers = collections.Counter(len(g) for _, g, _, _ in windows)
    print("\n  HOW MANY PARTY MEMBERS GAINED EXP IN A SWAP-TRAINING WINDOW:")
    for k in sorted(n_gainers):
        print(f"    {n_gainers[k]:>5} windows  ->  {k} mon gained")
    print("\n  ⇒ **1 = the trainee earns FULL exp (solo model correct, bar stays L35).**")
    print("    **2+ = the payout is SHARED (every estimate up to 2x optimistic, bar moves to L42).**")

    shares = []
    for out_pid, g, _foe, _lv in windows[:12]:
        tag = "trainee" if out_pid in g else "trainee got NOTHING"
        parts = ", ".join(f"{p[:4]}..+{v}" for p, v in sorted(g.items(), key=lambda x: -x[1]))
        shares.append(f"    {tag:<20} {parts}")
    print("\n  SAMPLE WINDOWS (pid prefix + exp gained):")
    print("\n".join(shares))
    print("=" * 102)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
