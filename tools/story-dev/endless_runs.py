"""ENDLESS DEBUG-RESET RUNS — back-to-back fresh story runs with hard failsafes.

USER REQUEST (2026-07-25): "endless debug reset runs back to back ... start a fresh session
at unthrottled speed with debugging on and run it until it finishes, reaches as far as we have
programmed or ends/crashes, with extra failsafes just in case it fails silently or loops
forever ... I get to decide how many (default 10, 0 = infinite)."

This is the CLI form, usable tonight. The Play-menu dropdown version is punch-list
`#24-endlessruns-gui` and lands in the (currently unpromoted) GUI bundle — it should call
straight into this logic rather than reimplementing it.

    py -3.12 tools/story-dev/endless_runs.py                     # 10 runs, treecko
    py -3.12 tools/story-dev/endless_runs.py --count 0           # INFINITE (Ctrl-C to stop)
    py -3.12 tools/story-dev/endless_runs.py --count 25 --starter mudkip
    py -3.12 tools/story-dev/endless_runs.py --starters all       # rotate all three starters

WHY EACH FAILSAFE EXISTS — every one of these is a failure actually observed on 2026-07-24/25:

* ``--run-timeout`` (wall clock, per run). The harness's own watchdogs are FRAME-based, so if
  the emulator process itself wedges, no frame counter advances and nothing fires. Only a
  wall-clock bound outside the process catches that.
* ``--stall-timeout`` (log growth). A run can keep burning frames while making no progress at
  all — a 2,000,000-frame fodder grind looked "alive" the whole time. If the log file stops
  GROWING we treat the run as silently dead and move on.
* **A fresh profile per run.** "FRESH boot from title" still loads the profile's battery save,
  so reusing a profile silently resumes a finished game — this produced three worthless runs
  that reported as fresh while starting in Fortree with a L39 party. Each run therefore gets
  its own profile directory containing ONLY metadata.yml + story.yml.
* **Never abort the batch on one bad run.** Every outcome is recorded and the loop continues;
  a crash in run 3 must not cost runs 4-25 of an overnight batch.

The ledger (``endless-runs/LEDGER.md``) is the deliverable — one row per run with outcome,
frames, wall-clock, badge/progress markers and the failure signature, so a batch can be read
at a glance instead of by opening 25 logs.
"""

import argparse
import datetime
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "sandbox-pokebot"
PROFILES = SANDBOX / "profiles"
HARNESS = ROOT / "tools" / "story-dev" / "story_harness.py"
OUTDIR = ROOT / "tools" / "story-dev" / "endless-runs"

# Progress markers scraped out of each log for the ledger. Ordered weakest -> strongest so the
# furthest one reached is the run's "depth".
MILESTONES = [
    ("badge1", "BADGE01_GET"),
    ("badge2", "BADGE02_GET"),
    ("badge3", "BADGE03_GET"),
    ("badge4", "BADGE04_GET"),
    ("badge5", "BADGE05_GET"),
    ("FEATHER", "FEATHER BADGE"),
    ("content-end", "end of built content"),
]

FAILURE_PATTERNS = [
    ("hang", "HANG CONFIRMED"),
    ("watchdog", "global watchdog"),
    ("movelearn-stall", "Move-learn dialogue could not be resolved"),
    ("whiteout-cap", "too many whiteout recoveries"),
    ("botmode-error", "BotModeError"),
    ("traceback", "Traceback (most recent call last)"),
]


#: A profile whose metadata.yml we COPY. ‼ Do not synthesise metadata.yml: it carries the ROM
#: reference (file_name/game_code/revision/language) and a hand-written `version: 1` makes every
#: run die instantly with "Could not find ROM `` for profile" — which the first version of this
#: script then mis-scraped as "clean-finish" (0 frames in 5 seconds). Copying from a known-good
#: profile keeps this correct even if the ROM is renamed.
TEMPLATE_PROFILE = "starter-treecko"


def fresh_profile(name: str, starter: str) -> pathlib.Path:
    """A profile with NO battery save, so the run genuinely starts from the title screen."""
    d = PROFILES / name
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    src = PROFILES / TEMPLATE_PROFILE / "metadata.yml"
    if not src.exists():
        raise SystemExit(
            f"[endless] template profile metadata missing: {src}\n"
            f"          Point TEMPLATE_PROFILE at any existing profile that runs."
        )
    shutil.copy(src, d / "metadata.yml")
    (d / "story.yml").write_text(
        f"character_name: NICK\ngender: boy\nstarter: {starter}\nstarter_nickname: none\n",
        encoding="utf-8",
    )
    return d


def scrape(log: pathlib.Path) -> tuple[str, str, int]:
    """-> (depth, failure, frames). Reads bytes-tolerantly; harness logs are not clean UTF-8."""
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ("?", "unreadable-log", 0)
    # ⛔⛔ CASE-INSENSITIVE ON **BOTH** SIDES — FIXED 2026-09-25, AND THE OBVIOUS FIX WAS WORSE.
    # The bot emits "... basket bought. **End** of built content. NEXT (WIP): Ch24 ..." with a CAPITAL E,
    # while the needle is lowercase, so a GENUINE COMPLETION matched NOTHING and was filed as a failure.
    # ‼ Lowercasing only the HAYSTACK would have broken TEN working needles in this same file
    # (HANG CONFIRMED, FEATHER BADGE, BADGE01_GET, Traceback ...). Both sides, or neither.
    _hay = text.lower()
    depth = "start"
    for label, needle in MILESTONES:
        if needle.lower() in _hay:
            depth = label
    failure = "clean-finish"
    for label, needle in FAILURE_PATTERNS:
        if needle.lower() in _hay:
            failure = label
            break
    frames = 0
    for line in reversed(text.splitlines()):
        if line.startswith("[done] ran "):
            try:
                frames = int(line.split("ran ", 1)[1].split(" ", 1)[0].replace(",", ""))
            except Exception:
                pass
            break
    # ‼ NEVER REPORT A NON-RUN AS A CLEAN FINISH. The first version of this script matched no
    # failure pattern on a run that died in 5 seconds with "Could not find ROM `` for profile"
    # and duly logged it as `clean-finish`, 0 frames — a green row for a run that never started.
    # An overnight batch of those would read as success. Zero frames is never success.
    if frames == 0 and failure == "clean-finish":
        first = next((ln for ln in text.splitlines() if ln.strip()), "")
        failure = f"never-started ({first.strip()[:70]})" if first else "never-started (empty log)"
    return (depth, failure, frames)


def run_one(idx: int, starter: str, args) -> dict:
    prof = f"endless-{starter}-{idx:03d}"
    fresh_profile(prof, starter)
    log = OUTDIR / f"run{idx:03d}-{starter}.log"
    cmd = [
        sys.executable, str(HARNESS), "fresh",
        "--driver", "story", "--frames", str(args.frames), "--profile", prof,
    ]
    started = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT)
        last_size, last_growth = -1, time.time()
        killed = None
        while proc.poll() is None:
            time.sleep(5)
            now = time.time()
            if now - started > args.run_timeout:
                killed = f"wall-clock>{args.run_timeout}s"
                break
            try:
                size = log.stat().st_size
            except OSError:
                size = last_size
            if size != last_size:
                last_size, last_growth = size, now
            elif now - last_growth > args.stall_timeout:
                # The log stopped growing: frame-based watchdogs cannot see this.
                killed = f"log-silent>{args.stall_timeout}s"
                break
        if killed:
            proc.kill()
            try:
                proc.wait(timeout=30)
            except Exception:
                pass
    elapsed = int(time.time() - started)
    depth, failure, frames = scrape(log)
    if killed:
        failure = killed
    return {
        "idx": idx, "starter": starter, "depth": depth, "failure": failure,
        "frames": frames, "secs": elapsed, "log": log.name,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--count", type=int, default=10,
                    help="how many runs; 0 = INFINITE until Ctrl-C (default 10)")
    ap.add_argument("--starter", default="treecko", choices=["treecko", "torchic", "mudkip"])
    ap.add_argument("--starters", default=None, choices=["all"],
                    help="rotate treecko/torchic/mudkip instead of a single starter")
    ap.add_argument("--frames", type=int, default=3_000_000)
    ap.add_argument("--run-timeout", type=int, default=5400,
                    help="hard wall-clock cap per run, seconds (frame watchdogs cannot see a "
                         "wedged emulator process)")
    ap.add_argument("--stall-timeout", type=int, default=600,
                    help="kill a run whose LOG stops growing for this many seconds")
    args = ap.parse_args()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    ledger = OUTDIR / "LEDGER.md"
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rotation = ["treecko", "torchic", "mudkip"] if args.starters == "all" else [args.starter]

    header = (
        f"\n## Batch started {stamp} — count={'INFINITE' if args.count == 0 else args.count}, "
        f"starters={'/'.join(rotation)}, frames={args.frames:,}, "
        f"run_timeout={args.run_timeout}s, stall_timeout={args.stall_timeout}s\n\n"
        "| # | starter | depth reached | outcome | frames | wall-clock | log |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(header)
    print(header)

    results: list[dict] = []
    idx = 0
    try:
        while args.count == 0 or idx < args.count:
            starter = rotation[idx % len(rotation)]
            idx += 1
            print(f"[endless] run {idx}"
                  f"{'' if args.count == 0 else f'/{args.count}'} ({starter}) starting...")
            try:
                r = run_one(idx, starter, args)
            except Exception as e:  # a crash in one run must never end the batch
                r = {"idx": idx, "starter": starter, "depth": "?",
                     "failure": f"launcher-error: {type(e).__name__}", "frames": 0,
                     "secs": 0, "log": "-"}
            results.append(r)
            row = (f"| {r['idx']} | {r['starter']} | {r['depth']} | {r['failure']} | "
                   f"{r['frames']:,} | {r['secs']}s | `{r['log']}` |\n")
            with ledger.open("a", encoding="utf-8") as fh:
                fh.write(row)
            print("[endless] " + row.strip())
    except KeyboardInterrupt:
        print("\n[endless] interrupted — writing summary for completed runs.")

    if results:
        depths: dict = {}
        fails: dict = {}
        for r in results:
            depths[r["depth"]] = depths.get(r["depth"], 0) + 1
            fails[r["failure"]] = fails.get(r["failure"], 0) + 1
        summary = (
            f"\n**Batch summary ({len(results)} runs):** "
            f"depth {', '.join(f'{k}×{v}' for k, v in sorted(depths.items()))} · "
            f"outcome {', '.join(f'{k}×{v}' for k, v in sorted(fails.items()))}\n"
        )
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(summary)
        print(summary)
        print(f"[endless] ledger: {ledger}")


if __name__ == "__main__":
    main()
