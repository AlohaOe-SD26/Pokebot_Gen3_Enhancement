"""LIVE TEST batch runner (user command "Conduct Live Tests", 2026-07-22).

Runs N independent Story-mode harness runs (default: fresh new game -> current story
frontier), each in its OWN profile (repro-liveK) so lanes can't interfere with each
other, the user's real save, or the committed checkpoints. Lanes run in parallel
batches; every run gets its own log; a summary.json per run + a batch summary.json
are auto-extracted for the Live Test report.

Usage (from tools/story-dev/):
    PYTHONUTF8=1 py -3.12 livetest.py --count 10 [--lanes 3] [--state fresh]
                                      [--frames 600000] [--timeout-min 75]
    --state fresh          new game per run (default), or a saves/ basename
                           (e.g. post_rival.ss1) to sweep a specific arc fast
    --lanes 3              how many harness processes run concurrently
    --out <dir>            output root (default livetest-runs/<stamp>/)

Each run directory contains: harness log (run.log), stdout (stdout.txt),
summary.json. The batch's summary.json aggregates all runs.

Success marker: the story's current content-end message (update END_MARKERS when
the frontier moves!). Everything else the summarizer counts: derails, whiteouts,
hang dumps, Manual drops, shiny events, final flags/party, frames.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- Keep in sync with the story frontier (grep the content-end message) ----
END_MARKERS = [
    "arrived in Slateport City",  # Ch8a content end (2026-07-22)
]
FAIL_MARKERS = {
    "hang": "HANG CONFIRMED",
    "manual": "BotModeError -> Manual",
}


def summarize_run(log_path: Path, stdout_path: Path, wall_seconds: float, killed: bool) -> dict:
    text = ""
    for p in (stdout_path, log_path):
        try:
            text += p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    reached = any(m in text for m in END_MARKERS)
    summary = {
        "wall_seconds": round(wall_seconds, 1),
        "killed_on_timeout": killed,
        "reached_frontier": reached,
        # A SUCCESSFUL run also prints HANG CONFIRMED (the harness uses it to end the
        # post-content idle), so a hang only counts when the frontier was NOT reached.
        "hang_confirmed": (FAIL_MARKERS["hang"] in text) and not reached,
        "dropped_to_manual": FAIL_MARKERS["manual"] in text,
        "derails": len(re.findall(r"derail #\d+", text)),
        "whiteouts": len(re.findall(r"WHITEOUT recovery", text)),
        "shiny_events": re.findall(r".*[Ss]hiny.*", text)[:20],
        "frames_run": None,
        "final_flags": None,
        "final_party": None,
        "last_positions": re.findall(r"POS .*", text)[-3:],
        "errors": re.findall(r"(BotModeError|Traceback|Exception).*", text)[:10],
    }
    m = re.search(r"\[done\] ran (\d+) frames.*?party=\[(.*?)\]", text)
    if m:
        summary["frames_run"] = int(m.group(1))
        summary["final_party"] = m.group(2)
    m = re.search(r"\[final flags\] (.*)", text)
    if m:
        summary["final_flags"] = m.group(1).strip()
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--lanes", type=int, default=3)
    ap.add_argument("--state", default="fresh")
    ap.add_argument("--frames", type=int, default=600_000)
    ap.add_argument("--timeout-min", type=float, default=75.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_root = Path(args.out) if args.out else HERE / "livetest-runs" / stamp
    out_root.mkdir(parents=True, exist_ok=True)
    print(f"[livetest] {args.count} run(s), {args.lanes} lane(s), state={args.state}")
    print(f"[livetest] output: {out_root}")

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env.pop("SAVE_POST_RIVAL", None)  # never clobber committed checkpoints from a sweep

    pending = list(range(1, args.count + 1))
    running: list[tuple[int, subprocess.Popen, Path, float, object, str]] = []
    results: dict[int, dict] = {}
    timeout_s = args.timeout_min * 60
    # One lane == one PROFILE, leased from a free pool: two harness processes must never
    # share a profile directory (current_state/state writes would clash).
    free_profiles = [f"repro-live{i}" for i in range(1, args.lanes + 1)]

    def launch(idx: int, lane_profile: str):
        run_dir = out_root / f"run{idx:02d}"
        run_dir.mkdir(exist_ok=True)
        log_file = run_dir / "run.log"
        stdout_file = run_dir / "stdout.txt"
        cmd = [
            "py", "-3.12", str(HERE / "story_harness.py"), args.state,
            "--driver", "story", "--frames", str(args.frames),
            "--profile", lane_profile, "--log", str(log_file),
        ]
        fh = open(stdout_file, "w", encoding="utf-8", errors="replace")
        proc = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT)
        print(f"[livetest] run{idx:02d} started (profile {lane_profile}, pid {proc.pid})")
        return (idx, proc, run_dir, time.time(), fh, lane_profile)

    while pending or running:
        while pending and free_profiles:
            running.append(launch(pending.pop(0), free_profiles.pop(0)))
        time.sleep(5)
        still = []
        for idx, proc, run_dir, t0, fh, lane_profile in running:
            elapsed = time.time() - t0
            killed = False
            if proc.poll() is None and elapsed > timeout_s:
                proc.kill()
                killed = True
                print(f"[livetest] run{idx:02d} KILLED after {elapsed/60:.1f} min (timeout)")
            if proc.poll() is not None or killed:
                fh.close()
                s = summarize_run(run_dir / "run.log", run_dir / "stdout.txt", elapsed, killed)
                s["profile"] = lane_profile
                (run_dir / "summary.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
                results[idx] = s
                free_profiles.append(lane_profile)
                verdict = "FRONTIER" if s["reached_frontier"] else ("HANG" if s["hang_confirmed"] else "INCOMPLETE")
                print(f"[livetest] run{idx:02d} done in {elapsed/60:.1f} min -> {verdict} "
                      f"(derails={s['derails']} whiteouts={s['whiteouts']})")
            else:
                still.append((idx, proc, run_dir, t0, fh, lane_profile))
        running = still

    batch = {
        "stamp": stamp,
        "count": args.count,
        "state": args.state,
        "reached_frontier": sum(1 for s in results.values() if s["reached_frontier"]),
        "hangs": sum(1 for s in results.values() if s["hang_confirmed"]),
        "manual_drops": sum(1 for s in results.values() if s["dropped_to_manual"]),
        "timeouts": sum(1 for s in results.values() if s["killed_on_timeout"]),
        "runs": {f"run{idx:02d}": s for idx, s in sorted(results.items())},
    }
    (out_root / "summary.json").write_text(json.dumps(batch, indent=2), encoding="utf-8")
    print(f"[livetest] BATCH DONE: {batch['reached_frontier']}/{args.count} reached the frontier; "
          f"hangs={batch['hangs']} manual={batch['manual_drops']} timeouts={batch['timeouts']}")
    print(f"[livetest] batch summary: {out_root / 'summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
