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

STORAGE SCHEME (user directive 2026-07-22 â€” stale tests must never get lumped into a
current review):
  livetest-runs/
    INDEX.md            <- self-healing index of EVERY batch (current + archived):
                           stamp, code commit, scope, scorecard, reviewed-or-not
    <stamp>/            <- the CURRENT batch (only ever ONE in the root)
      summary.json      <- includes the git commit (+dirty flag) the code was at
      REVIEWED.md       <- written by the reviewer once the Live Test report is done
      run01/ ...        <- per-run artifacts
    archive/<stamp>/    <- "old tests": every previous batch is auto-moved here the
                           moment a NEW batch starts (stale by definition â€” new code)
Batches are tied to code by the recorded commit hash: a review must only ever read
batches whose commit matches the code under discussion.

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
    # Substring of the story's content-end message. Keep it DASH-FREE and short: the
    # message contains an em-dash and encoding round-trips have corrupted it once.
    "Dynamo Badge earned",  # Ch9 content end (2026-07-22)
    "Rock Smash in hand",   # Ch10a content end (2026-07-22 overnight)
    "Rock Smash taught",    # Ch10b content end (2026-07-22 overnight)
    "reached Fallarbor",    # Ch10c content end (2026-07-22 overnight)
    "Meteor Falls scene done",  # Ch11a content end (2026-07-22 overnight)
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


def git_commit() -> str:
    """Short commit of the code under test (+ '-dirty' if the tree has changes)."""
    try:
        root = HERE.parents[1]
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                             capture_output=True, text=True, timeout=15).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                               capture_output=True, text=True, timeout=15).stdout.strip()
        return f"{rev}{'-dirty' if dirty else ''}" if rev else "unknown"
    except Exception:
        return "unknown"


def archive_previous_batches(runs_root: Path) -> None:
    """Move every previous batch out of the root into archive/ â€” they are stale
    relative to the new batch's code by definition, and the root must only ever
    hold the CURRENT batch (user directive: old tests live separately)."""
    archive = runs_root / "archive"
    for d in sorted(runs_root.iterdir()) if runs_root.exists() else []:
        if d.is_dir() and d.name != "archive":
            archive.mkdir(exist_ok=True)
            target = archive / d.name
            try:
                d.rename(target)
                print(f"[livetest] archived stale batch -> archive/{d.name}", flush=True)
            except Exception as e:
                print(f"[livetest] WARNING: could not archive {d.name}: {e}", flush=True)


def rebuild_index(runs_root: Path) -> None:
    """Regenerate INDEX.md from disk (self-healing): one line per batch, current and
    archived, with commit + scorecard + review status (REVIEWED.md presence)."""
    rows = []
    def scan(base: Path, location: str):
        if not base.exists():
            return
        for d in sorted(base.iterdir(), reverse=True):
            if not d.is_dir() or d.name == "archive":
                continue
            s = {}
            try:
                s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
            except Exception:
                pass
            reviewed = "yes" if (d / "REVIEWED.md").exists() else "NO"
            rows.append(
                f"| {d.name} | {location} | {s.get('state', '?')} | {s.get('count', '?')} "
                f"| {s.get('code_commit', '?')} | {s.get('reached_frontier', '?')}/{s.get('count', '?')} "
                f"| {s.get('hangs', '?')} | {s.get('manual_drops', '?')} | {reviewed} |"
            )
    scan(runs_root, "CURRENT")
    scan(runs_root / "archive", "archive")
    index = (
        "# Live Test batches â€” index (auto-generated by livetest.py; do not hand-edit)\n\n"
        "A review must only read batches whose `commit` matches the code under discussion.\n"
        "`reviewed = NO` means no Live Test report was produced for that batch yet.\n\n"
        "| batch | location | scope | runs | commit | frontier | hangs | manual | reviewed |\n"
        "|-------|----------|-------|------|--------|----------|-------|--------|----------|\n"
        + "\n".join(rows) + "\n"
    )
    (runs_root / "INDEX.md").write_text(index, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10)
    # Default 6 lanes: sized for the user's main box (Ryzen 9 5950X, 16C/32T, 128 GB â€”
    # specs-scan 2026-07-22); each headless lane â‰ˆ 1 core. Up to ~12 is fine there;
    # drop to 2-3 on lesser machines or when anything else heavy is running.
    ap.add_argument("--lanes", type=int, default=6)
    ap.add_argument("--state", default="fresh")
    ap.add_argument("--frames", type=int, default=600_000)
    ap.add_argument("--timeout-min", type=float, default=75.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    runs_root = HERE / "livetest-runs"
    if args.out is None:
        archive_previous_batches(runs_root)
    out_root = Path(args.out) if args.out else runs_root / stamp
    out_root.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    print(f"[livetest] {args.count} run(s), {args.lanes} lane(s), state={args.state}, code={commit}", flush=True)
    print(f"[livetest] output: {out_root}", flush=True)

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
        if args.state == "fresh":
            # A lane profile reused across batches keeps its .sav flash â€” and a "fresh"
            # boot with a save present CONTINUES it instead of starting a new game
            # (live-hit: run01 of the first batch "reached the frontier" in 7 min by
            # resuming an old save). Wipe the lane's game state so fresh means fresh.
            prof_dir = HERE.parents[1] / "sandbox-pokebot" / "profiles" / lane_profile
            for name in ("current_save.sav", "current_state.ss1"):
                f = prof_dir / name
                if f.exists():
                    f.unlink()
            states = prof_dir / "states"
            if states.exists():
                for f in states.glob("*.ss1"):
                    f.unlink()
        log_file = run_dir / "run.log"
        stdout_file = run_dir / "stdout.txt"
        cmd = [
            "py", "-3.12", str(HERE / "story_harness.py"), args.state,
            "--driver", "story", "--frames", str(args.frames),
            "--profile", lane_profile, "--log", str(log_file),
        ]
        fh = open(stdout_file, "w", encoding="utf-8", errors="replace")
        proc = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT)
        print(f"[livetest] run{idx:02d} started (profile {lane_profile}, pid {proc.pid})", flush=True)
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
                print(f"[livetest] run{idx:02d} KILLED after {elapsed/60:.1f} min (timeout)", flush=True)
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
        "code_commit": commit,
        "reached_frontier": sum(1 for s in results.values() if s["reached_frontier"]),
        "hangs": sum(1 for s in results.values() if s["hang_confirmed"]),
        "manual_drops": sum(1 for s in results.values() if s["dropped_to_manual"]),
        "timeouts": sum(1 for s in results.values() if s["killed_on_timeout"]),
        "runs": {f"run{idx:02d}": s for idx, s in sorted(results.items())},
    }
    (out_root / "summary.json").write_text(json.dumps(batch, indent=2), encoding="utf-8")
    if args.out is None:
        rebuild_index(runs_root)
    print(f"[livetest] BATCH DONE: {batch['reached_frontier']}/{args.count} reached the frontier; "
          f"hangs={batch['hangs']} manual={batch['manual_drops']} timeouts={batch['timeouts']}")
    print(f"[livetest] batch summary: {out_root / 'summary.json'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
