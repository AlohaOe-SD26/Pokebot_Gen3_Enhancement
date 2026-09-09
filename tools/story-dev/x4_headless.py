"""HEADLESS ENDLESS-RESET batch runner (`#24-x4headless`, user request 2026-07-31).

WHAT IT IS
----------
N independent `Story (ENDLESS RESET)` bots, headless, in parallel lanes — the exact
mode the user's GUI `ENDLESS LOOP x4` runs, minus the tile view. One lane is literally:

    python pokebot.py <profile> -m "Story (ENDLESS RESET)" -s 0 -na -hl --endless-target 0

WHY IT EXISTS — the comparability problem
-----------------------------------------
`tools/story-dev/livetest.py` drives **plain `Story`**, where a `BotModeError` reaches
`main_loop`, drops the bot to Manual, and the run ENDS. The user's batches run
**`Story (ENDLESS RESET)`**, which SWALLOWS that error and starts a fresh run. So every
finish-rate number livetest has ever produced is HARSHER than the user's, and the two
were never directly comparable. This runner closes that gap: same mode, same flags,
same per-lane starter split, so a batch measured here can be put beside one of the
user's bundles without an asterisk.

SPEED / VIDEO — VERIFIED, NOT ASSUMED (2026-07-31)
--------------------------------------------------
Three separate mechanisms already guarantee an unthrottled lane with the renderer ON;
this runner ASSERTS the result rather than re-engineering it.
  1. `-s 0` -> `StartupSettings.emulation_speed = 0` -> `PokebotHeadless.run()` sets
     `context.emulation_speed = 0`.
  2. `-hl` WITHOUT `-nv` -> `PokebotHeadless.run()` sets `context.video = True`.
     ‼ Headless removes the GUI WINDOW, not the RENDERER. The faithful PokéNav
     Match-Call path needs the renderer and is therefore fine here.
  3. `StoryEndlessResetMode.run()` calls `_apply_debug_emulation_config()`, which FORCES
     `speed=0` + `video=True`, and re-pins the speed after every run (a derail calls
     `set_manual_mode()`, which drops to 1x — the "second run crawled at 1x" bug of
     2026-07-25). `set_manual_mode()` sets `video = True`, never off.

‼ AND THEN WE CHECK. Every run writes a fresh debug log whose RUN HEADER carries
`emulation: speed=… video=… audio=…`. This runner watches every lane's debug-logs
directory for the whole batch and asserts `speed=0 video=True` on EVERY header it sees —
not just the first, because the failure mode being guarded is precisely "run 1 was fine
and run 2 crawled". A lane silently at 1x is ~20x slower and, from the outside, looks
exactly like a hang. On a violation the batch ABORTS LOUDLY (`--on-bad-header warn` to
downgrade), because a mis-configured lane makes the whole sample worthless.

TWO TRAPS THIS RUNNER HANDLES FOR YOU
-------------------------------------
* **rich wraps a lane's stdout** when it is a file, so long lines are physically split
  mid-word and a naive regex over `=== ENDLESS RESET: run N -> … ===` matches nothing.
  Verified in the user's own bundle `P1-stdout-20260726-233837.txt`. Lanes launch with
  `COLUMNS=20000`, AND `_RUN_END_RE` is wrap-tolerant — ‼ width alone is not enough, and
  believing it was cost batch `20260731-105549` its finish rate (reported 69%, true 23.7%,
  with the dominant end reason missing entirely). Any width can be exceeded.
* **Eight lanes all bind HTTP port 8888** and eight thread tracebacks land in the logs.
  Each lane profile gets its own `http.yml` with `enable: false`.

STORAGE (mirrors livetest's rule: a batch must never be compared to code it did not run)
----------------------------------------------------------------------------------------
    tools/story-dev/x4-runs/
      INDEX.md          <- one row per batch, WITH THE COMMIT HASH the batch ran
      LATEST.txt        <- pointer to the newest batch's stamp (Windows-safe, not a symlink)
      <stamp>/
        MANIFEST.txt    <- lanes, starters, profiles, bounds, commit, verdicts
        summary.json    <- machine-readable batch + per-lane summary
        L01/ … L0N/     <- per-lane stdout.txt + the debug logs produced in this window

Usage (from tools/story-dev/):
    PYTHONUTF8=1 py -3.12 x4_headless.py --lanes 8 --minutes 180
    PYTHONUTF8=1 py -3.12 x4_headless.py --lanes 4 --runs 5          # 5 runs per lane
    PYTHONUTF8=1 py -3.12 x4_headless.py --resummarise x4-runs/<stamp>   # re-read stored logs

‼ `--resummarise` exists because the LOGS are the data and the summary is only a reading of
them. When a parser bug is found, re-read the stored batch — never re-run three hours of
emulation to fix a regex, which would also produce a different sample and destroy the
comparison you were trying to make.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
#: ⛔⛔ WHICH FORK THE LANES RUN. Defaults to `custom` because that is the fork that HOLDS STILL:
#: the standing directive is "during a sandbox round, do NOT modify custom-pokebot", so a batch
#: pointed here measures the PROMOTED PRODUCT and cannot be poisoned by whatever is being edited in
#: the sandbox mid-batch. `14-AGENT-PLAYBOOK.md` calls analysing logs against undeployed code the
#: largest single waste in this project — this is the mechanical guard against it.
#: ‼ Rebound by `--build`; the MANIFEST records which was used, because a finish rate whose build is
#: unknown is not a measurement.
BUILD_ROOTS = {"sandbox": "sandbox-pokebot", "custom": "custom-pokebot"}
BUILD_NAME = "custom"
BUILD_ROOT = REPO_ROOT / BUILD_ROOTS[BUILD_NAME]
PROFILES = BUILD_ROOT / "profiles"
RUNS_ROOT = HERE / "x4-runs"

BOT_MODE = "Story (ENDLESS RESET)"

#: ‼ MUST MATCH `sandbox-pokebot/modules/endless_x4.py: LANE_STARTERS`. Duplicated (not
#: imported) because importing it drags in `modules.profiles` / `modules.roms` /
#: `modules.tile_bridge`, which this runner has no need of — but `repro_x4_headless.py`
#: parses that file and asserts the two tables are identical, so they cannot drift.
#:
#: Modulo cycling gives BOTH shapes the user asked for from one table:
#:   --lanes 4 -> torchic, mudkip, treecko, random   (exactly the GUI dashboard's split)
#:   --lanes 8 -> 2x each starter + 2 random         (per-starter sample size DOUBLES)
#: The doubling is the point: `#24-starter-gym3` (Treecko stalls at Wattson in 11 of 14
#: runs; Mudkip never does) is a starter-specific bug, and 1 lane per starter is too thin
#: a sample to separate that from noise.
LANE_STARTERS: tuple[str, ...] = ("torchic", "mudkip", "treecko", "random")

#: The template profile whose `metadata.yml` (ROM binding) lane profiles are cloned from.
TEMPLATE_PROFILE = "endless-P1-torchic"


# ---------------------------------------------------------------------------
# Lane identity (pure — covered by repro_x4_headless.py)
# ---------------------------------------------------------------------------
def lane_starter(slot: int) -> str:
    return LANE_STARTERS[slot % len(LANE_STARTERS)]


def lane_tag(slot: int) -> str:
    return f"H{slot + 1}"


def lane_profile_name(slot: int) -> str:
    """Namespaced away from the GUI's `endless-P{n}-…` lanes ON PURPOSE.

    Two bot processes must never share a profile directory (they clash on
    `current_save.sav` / `current_state.ss1` / `stats.db` — `livetest.py` learned this
    the hard way). The user can be running their own GUI x4 batch on this box at the
    same time as a headless batch, so the two families must not overlap.
    """
    return f"endless-{lane_tag(slot)}-{lane_starter(slot)}"


# ---------------------------------------------------------------------------
# RUN HEADER assertion (pure — covered by repro_x4_headless.py)
# ---------------------------------------------------------------------------
#: The debug log's header line, e.g. `    emulation:     speed=0 video=True audio=False`
_EMULATION_RE = re.compile(r"emulation:\s+speed=(\S+)\s+video=(\S+)(?:\s+audio=(\S+))?")
_HEADER_END = "--- END RUN HEADER ---"


def parse_run_header(text: str) -> dict | None:
    """Extract the emulation facts from a debug log's RUN HEADER.

    Returns None while the header is still being written (so a watcher can retry) and
    `{"speed": …, "video": …, "audio": …}` once it is complete. A COMPLETE header with
    no `emulation:` line yields `{}` — "the header exists and does not say", which is a
    different thing from "not written yet" and must not be silently treated as a pass.
    """
    if _HEADER_END not in text:
        return None
    m = _EMULATION_RE.search(text)
    if not m:
        return {}
    return {"speed": m.group(1), "video": m.group(2), "audio": m.group(3) or "?"}


def header_verdict(header: dict | None) -> tuple[str, str]:
    """('ok'|'bad'|'unknown', human reason). `bad` is what aborts a batch."""
    if header is None:
        return "unknown", "run header not written yet"
    if not header:
        return "unknown", "run header has no `emulation:` line (debug_logger changed?)"
    speed, video = header.get("speed"), header.get("video")
    if speed == "0" and video == "True":
        return "ok", f"speed={speed} video={video}"
    return "bad", (
        f"speed={speed} video={video} — expected speed=0 video=True. "
        "A lane at 1x is ~20x slower and looks exactly like a hang; "
        "video off silently degrades the faithful PokeNav path to its state-write fallback."
    )


# ---------------------------------------------------------------------------
# Outcome parsing (pure — covered by repro_x4_headless.py)
# ---------------------------------------------------------------------------
_RUN_START_RE = re.compile(r"=== ENDLESS RESET: starting run (\d+)/(\S+) ===")

#: ‼ `re.DOTALL` + a bounded gap, because A RUN-OUTCOME RECORD CAN SPAN LINES. Learned the
#: expensive way on batch `20260731-105549`: `COLUMNS=400` was set precisely to stop rich
#: wrapping these lines, and it was not enough — a counter-chain derail message is ~1,000
#: characters (it lists every candidate counter with map, tile, level band and rate), so it
#: still wrapped and the `(N frames) ===` tail landed on the following line. The parser then
#: matched 1 of 7 outcomes on that lane and the batch summary reported a **69% finish rate
#: against a true ~22%**, with the counter chain — the dominant end reason — appearing ZERO
#: times.
#:
#: `COLUMNS` is now far larger, but width is a mitigation and this is the fix: any message
#: long enough will wrap at any width, so the PARSER must tolerate it. The gap is bounded so
#: a truncated record (a lane killed mid-print) cannot swallow the next one.
_RUN_END_RE = re.compile(
    r"=== ENDLESS RESET: run (\d+)/\S+ -> (.{0,4000}?) \(([\d,\-]+) frames\) ===", re.DOTALL
)
_BATCH_DONE = "=== ENDLESS RESET: batch complete ==="


def classify_outcome(outcome: str) -> str:
    """Bucket a run's outcome string.

    ‼ START PESSIMISTIC. `StoryEndlessResetMode` defaults `outcome = "finished"` and only
    a raised `BotModeError` changes it, so a run that handed itself to Manual used to
    report SUCCESS — 16 dead runs read as wins and a batch summary claimed ~80% against a
    true ~20% (2026-07-26). The mode now emits `stopped: handed to Manual mid-run`; treat
    ONLY the literal `finished` as a finish.
    """
    o = outcome.strip()
    if o == "finished":
        return "finished"
    for prefix, bucket in (
        ("derailed:", "derailed"),
        ("stopped:", "stopped"),
        ("crashed:", "crashed"),
        ("frame-cap", "frame_cap"),
    ):
        if o.startswith(prefix):
            return bucket
    return "other"


def _derail_reason(outcome: str) -> str:
    """The short, groupable cause of a derail.

    This is THE measurement that matters right now: the handoff records that the counter
    chain correctly names its answer and then ENDS THE RUN, and that 4 of 6 remaining
    hangs are that. Grouping raw outcome strings would scatter it across every distinct
    boss/level/type combination, so trim to the stable prefix.

    ⛔⛔ THE PID PASS BELOW IS LOAD-BEARING AND WAS MISSING UNTIL 2026-09-08. The digit pass
    normalises DECIMAL runs only, and **a PID is HEX** — so `Marill#30AD95BD` became
    `Marill#NADNBD` (the letters survive) and EVERY DISTINCT PID BECAME ITS OWN KEY. Because
    `summary.json` is written through `.most_common()`, that scattered the single biggest
    blocker into a pile of count-1 rows at the BOTTOM of the file while a genuinely smaller
    cause sat at the top.
    ⭐ MEASURED on batch `20260907-203713`, re-aggregating its 49 real outcome strings:
        as shipped : Ch23 training = 16 events across **16 separate keys**; displayed #1 was
                     "this boss: N losses ... Normal" at 6.
        with fix   : Ch23 training = 16 events across 6 keys; #1 becomes the Victory Road
                     training failure at 9.
    ⇒ the ranking INVERTS, and every reader — agent, gate or human — who trusted the top of
    `summary.json` was handed the wrong blocker, low by ~3x. This is SESSION DISCIPLINE rule 7
    (instrument the ACTION, not the input) applied to the summariser itself.
    ‼ Order matters: collapse the hex PID BEFORE the digit pass, or the digits inside it are
    already gone and the pattern no longer matches.
    """
    o = outcome.strip()
    for prefix in ("derailed:", "stopped:", "crashed:"):
        if o.startswith(prefix):
            o = o[len(prefix):].strip()
            break
    o = re.sub(r"#[0-9A-Fa-f]{6,}", "#PID", o)   # ⛔ BEFORE the digit pass — see docstring
    o = re.sub(r"\d[\d,]*", "N", o)          # levels, losses, frame counts
    o = re.sub(r"\s+", " ", o)
    return o[:140]


def summarize_lane(stdout_text: str, debug_text: str) -> dict:
    """Per-lane metrics. `stdout_text` carries run boundaries + outcomes; `debug_text` is
    the concatenation of that lane's debug logs and carries the battle-level evidence."""
    both = stdout_text + "\n" + debug_text

    runs = []
    for m in _RUN_END_RE.finditer(stdout_text):
        try:
            frames = int(m.group(3).replace(",", ""))
        except ValueError:
            frames = 0
        runs.append({
            "run": int(m.group(1)),
            "outcome": m.group(2).strip(),
            "bucket": classify_outcome(m.group(2)),
            "frames": frames,
        })

    buckets = Counter(r["bucket"] for r in runs)
    outcomes = Counter(
        re.findall(r"outcome=BattleOutcome\.([A-Za-z]+)", both)
    )
    total_battles = sum(outcomes.values())

    summary = {
        "runs_started": len(_RUN_START_RE.findall(stdout_text)),
        "runs_ended": len(runs),
        "batch_completed_naturally": _BATCH_DONE in stdout_text,
        "finished": buckets.get("finished", 0),
        "derailed": buckets.get("derailed", 0),
        "stopped": buckets.get("stopped", 0),
        "crashed": buckets.get("crashed", 0),
        "frame_cap": buckets.get("frame_cap", 0),
        "finish_rate": round(buckets.get("finished", 0) / len(runs), 3) if runs else None,
        # The grouped cause of every non-finish. This is what tells you WHICH blocker is
        # killing runs, and it is the only number that should drive the next item.
        "end_reasons": dict(
            Counter(_derail_reason(r["outcome"]) for r in runs if r["bucket"] != "finished").most_common()
        ),
        # --- canaries, each tied to a known issue -------------------------------
        # KI-38: the after-faint chooser abandoning an ACTIVE battle. `GAVE UP` ran at
        # ~22/h on the broken builds while `NO ELIGIBLE REPLACEMENT` was 0 — i.e. a valid
        # living target ALWAYS existed. Both numbers, always, or the next reader re-derives
        # that distinction from scratch.
        "faint_chooser_gave_up": len(re.findall(r"GAVE UP", both)),
        "no_eligible_replacement": len(re.findall(r"NO ELIGIBLE REPLACEMENT", both)),
        # KI-40 / KI-36: the mode being starved or wedged.
        "global_watchdog": len(re.findall(r"global watchdog", both)),
        "stuck_dumps": len(re.findall(r"DUMP \[STUCK", both)),
        # Where an in-battle wedge was parked. `BattleScript_FaintedMonTryChoose` here is
        # KI-38; anything else is news.
        "stuck_battle_scripts": dict(Counter(re.findall(r"instr=(\S+)", both)).most_common(10)),
        # --- health ------------------------------------------------------------
        "derails": len(re.findall(r"derail #\d+", both)),
        "whiteouts": len(re.findall(r"recovered from the whiteout", both)),
        "losses": len(re.findall(r"lost a battle at map", both)),
        "losses_by_map": dict(Counter(re.findall(r"lost a battle at map \((\d+, \d+)\)", both)).most_common(10)),
        "battle_outcomes": dict(outcomes.most_common()),
        "battles": total_battles,
        # A run can look perfectly healthy — no error, no hang, full HP — while fleeing
        # everything and gaining nothing (3,011 RanAway vs 5 Won, 2.9M frames, 2026-07-26).
        "flee_rate": round(outcomes.get("RanAway", 0) / total_battles, 3) if total_battles else None,
        "badges": dict(Counter(re.findall(r"([A-Z][a-z]+) Badge earned", both)).most_common()),
        "runs": runs,
    }
    return summary


# ---------------------------------------------------------------------------
# Reporting (pure — covered by repro_x4_headless.py)
# ---------------------------------------------------------------------------
def lane_summary(lane: "Lane", stdout_text: str, debug_text: str, n_logs: int) -> dict:
    """Assemble ONE lane's summary dict — the thing that becomes `batch["lanes_detail"][tag]`.

    ⭐ EXTRACTED SO A GATE CAN DRIVE THE REAL PATH. This lived inline in `run_batch`, which meant the
    only way to test anything downstream of it was to hand-build a `lanes_detail` dict — and a
    hand-built fixture tests the FUNCTION, never the WIRING. `#24-lane-respawn-build` shipped once
    with `build_commits` recorded on the `Lane` and never copied into this dict: seven gate checks
    passed, and the feature had never worked. ‼ If a value has to travel from an object into a
    report, the test must make that JOURNEY, not assert the destination's shape.
    """
    s = summarize_lane(stdout_text, debug_text)
    verdicts = [v for v, _ in lane.headers.values()]
    s["header_verdict"] = "BAD" if "bad" in verdicts else ("ok" if "ok" in verdicts else "unknown")
    s["headers_checked"] = len(verdicts)
    s["restarts"] = lane.restarts
    s["starter"] = lane.starter
    s["profile"] = lane.profile
    s["debug_logs_collected"] = n_logs
    #: ⭐ #24-lane-respawn-build — the commits this lane's PROCESSES actually loaded.
    s["build_commits"] = list(lane.build_commits)
    return s


# ---------------------------------------------------------------------------
def build_provenance_lines(batch: dict) -> list[str]:
    """⭐⭐ #24-lane-respawn-build — DOES THIS BATCH SPAN MORE THAN ONE BUILD?

    `code_commit` is captured ONCE, at batch start. But a lane that dies is RESPAWNED, and the new
    process imports whatever is **on disk at that moment** — so an edit or a promotion mid-batch
    lands in some lanes and not others, while the MANIFEST still names a single commit.
    ⇒ every spawn records the commit it loaded; this reports the set.

    ‼ DETECT rather than merely forbid. "Never promote while a batch runs" was already a rule, and a
    rule nobody can verify is prose. This makes the honest mistake — an interrupted session, a second
    operator, a promotion that felt safe — announce itself instead of silently poisoning a number.
    ⛔ `.get` throughout on purpose: a reporting function must never crash on an older batch dict
    (the gate's fixture predates this field).
    """
    detail = batch.get("lanes_detail") or {}
    seen: dict[str, list[str]] = {}
    for tag, d in detail.items():
        for commit in (d or {}).get("build_commits") or []:
            seen.setdefault(commit, []).append(tag)
    if not seen:
        return ["build_commits  (not recorded — this batch predates #24-lane-respawn-build)"]
    # ⛔ "UNVERIFIED" IS NOT "MIXED", AND THE LOUD CLAIM MUST NOT FIRE ON A GIT HICCUP.
    # `git_commit()` returns "unknown" when git is missing or times out. Folding that into the
    # commit set would make a perfectly clean batch shout "do not quote a rate from it" — a false
    # alarm, and this project rates a gate that cries wolf as worse than no gate. So `unknown` is
    # reported as a SEPARATE, quieter caveat, and only two distinct REAL commits mean MIXED.
    unknown_tags = sorted(set(seen.pop("unknown", [])))
    if not seen:
        return [f"build_commits  ⚠ UNVERIFIED — git could not identify the build for: "
                f"{', '.join(unknown_tags)}. Not necessarily mixed; simply unknown."]
    caveat = ([f"               ⚠ plus UNVERIFIED spawns (git failed) on: {', '.join(unknown_tags)}"]
              if unknown_tags else [])
    if len(seen) == 1:
        only = next(iter(seen))
        return [f"build_commits  {only}  (every lane, every spawn — SINGLE BUILD)"] + caveat
    out = [
        "build_commits  ⛔⛔ MIXED BUILD — THIS BATCH SPANS MORE THAN ONE COMMIT.",
        "               A finish rate whose build is ambiguous is NOT a measurement. Do not",
        "               compare this batch against another, and do not quote a rate from it.",
        "               Cause: a lane died and was respawned against the ON-DISK code after the",
        "               tree changed (see #24-lane-respawn-build).",
    ]
    for commit, tags in sorted(seen.items()):
        out.append(f"               {commit}  <- {', '.join(sorted(set(tags)))}")
    return out + caveat


def render_manifest(batch: dict) -> str:
    lines = [
        "ENDLESS-RESET HEADLESS BATCH — MANIFEST",
        "=" * 72,
        f"stamp          {batch['stamp']}",
        f"code_commit    {batch['code_commit']}",
        *build_provenance_lines(batch),
        # ⛔ WHICH FORK PRODUCED THESE NUMBERS. `.get` on purpose: the gate's fixture predates this
        # field, and a reporting function must never crash on an older batch dict.
        f"build          {batch.get('build', '?')}",
        f"bot_mode       {BOT_MODE}",
        f"lanes          {batch['lanes']}",
        f"bound          runs/lane={batch['runs_per_lane'] or 'infinite'}  "
        f"minutes={batch['minutes'] or 'unbounded'}",
        f"started        {batch['started']}",
        f"ended          {batch.get('ended', '(running)')}",
        f"wall_minutes   {batch.get('wall_minutes', '?')}",
        f"VERDICT        {batch.get('verdict', '?')}",
        "",
        "LANES",
        "-" * 72,
        f"{'tag':<5} {'starter':<9} {'profile':<26} {'runs':>5} {'fin':>4} {'header':<8} restarts",
    ]
    for ln in batch["lane_rows"]:
        lines.append(
            f"{ln['tag']:<5} {ln['starter']:<9} {ln['profile']:<26} "
            f"{ln['runs_ended']:>5} {ln['finished']:>4} {ln['header_verdict']:<8} {ln['restarts']}"
        )
    lines += [
        "",
        "EMULATION ASSERTION",
        "-" * 72,
        "Every run's debug-log RUN HEADER must read `emulation: speed=0 video=True`.",
        f"headers checked: {batch['headers_checked']}   violations: {len(batch['header_violations'])}",
    ]
    for v in batch["header_violations"]:
        lines.append(f"  !! {v['tag']}  {Path(v['log']).name}  {v['reason']}")
    if not batch["header_violations"]:
        lines.append("  all clean.")
    lines += [
        "",
        "READ NEXT",
        "-" * 72,
        "summary.json  — per-lane finish rate, end_reasons, canaries (KI-38/KI-40), outcomes",
        "L*/stdout.txt — run boundaries and outcomes",
        "L*/debug-logs — one file per run: [MAP]/[PARTY]/[BATTLE]/[STEP] + STUCK dumps",
        "",
        "!! A batch may only be compared against the code whose commit is recorded above.",
    ]
    return "\n".join(lines) + "\n"


def render_index(rows: list[dict]) -> str:
    """INDEX.md — self-healing, rebuilt from disk. The COMMIT COLUMN is the whole point:
    two bundles in this project were analysed in depth against code that was never
    running, the largest single waste of the project (08-MISTAKES 2026-07-28)."""
    head = (
        "# Headless ENDLESS-RESET batches — index\n"
        "_Auto-generated by `x4_headless.py`; do not hand-edit._\n\n"
        "‼ A review may ONLY compare a batch against the code at its `commit`.\n\n"
        "| batch | commit | lanes | bound | runs | finished | rate | watchdog | GAVE UP | verdict |\n"
        "|-------|--------|-------|-------|------|----------|------|----------|---------|---------|\n"
    )
    body = "\n".join(
        f"| {r['stamp']} | `{r['commit']}` | {r['lanes']} | {r['bound']} | {r['runs']} "
        f"| {r['finished']} | {r['rate']} | {r['watchdog']} | {r['gave_up']} | {r['verdict']} |"
        for r in rows
    )
    return head + body + "\n"


def index_row(stamp: str, summary: dict) -> dict:
    lanes = summary.get("lanes_detail", {})
    runs = sum(l.get("runs_ended", 0) for l in lanes.values())
    fin = sum(l.get("finished", 0) for l in lanes.values())
    return {
        "stamp": stamp,
        "commit": summary.get("code_commit", "?"),
        "lanes": summary.get("lanes", "?"),
        "bound": f"{summary.get('runs_per_lane') or 'inf'}r/{summary.get('minutes') or 'inf'}m",
        "runs": runs,
        "finished": fin,
        "rate": f"{fin / runs:.0%}" if runs else "n/a",
        "watchdog": sum(l.get("global_watchdog", 0) for l in lanes.values()),
        "gave_up": sum(l.get("faint_chooser_gave_up", 0) for l in lanes.values()),
        "verdict": summary.get("verdict", "?"),
    }


def rebuild_index(runs_root: Path) -> None:
    rows = []
    for d in sorted(runs_root.iterdir(), reverse=True) if runs_root.exists() else []:
        if not d.is_dir():
            continue
        try:
            s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        rows.append(index_row(d.name, s))
    (runs_root / "INDEX.md").write_text(render_index(rows), encoding="utf-8")


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------
def ensure_lane_profile(slot: int) -> Path:
    """Create/refresh a headless lane profile without importing the bot.

    ‼ `story.yml` is REWRITTEN on every batch launch, exactly as `modules/endless_x4.py`
    does it and for the same reason: these are bot-managed profiles whose whole purpose
    is "H2 is always the Mudkip lane", and a stale hand-edit turning H2 into a second
    Torchic would silently corrupt the starter coverage the batch exists to provide.
    """
    name = lane_profile_name(slot)
    path = PROFILES / name
    path.mkdir(parents=True, exist_ok=True)

    meta = path / "metadata.yml"
    if not meta.exists():
        template = PROFILES / TEMPLATE_PROFILE / "metadata.yml"
        if not template.exists():
            # ⭐ FALL BACK TO ANY PROFILE IN THIS FORK. `metadata.yml` is only a ROM binding, and the
            # two forks' bindings are byte-identical, so any profile here is a valid donor. This
            # exists because `--build custom` FATAL'd on its first launch: the template lived only in
            # the sandbox, since that was the only fork this runner could target before 2026-09-07.
            # ‼ The donor is NAMED in the log — a batch whose ROM binding came from an unnamed source
            # is a batch nobody can reproduce.
            for candidate in sorted(PROFILES.glob("*/metadata.yml")):
                template = candidate
                print(f"[x4h] no `{TEMPLATE_PROFILE}` template in {PROFILES.parent.name}; "
                      f"using the ROM binding from `{candidate.parent.name}`", flush=True)
                break
        if not template.exists():
            raise SystemExit(
                f"[x4h] FATAL: no template profile at {template}. Create one lane profile "
                f"via the GUI (or copy any profile's metadata.yml) and re-run."
            )
        shutil.copy2(template, meta)

    (path / "story.yml").write_text(
        "# Managed by tools/story-dev/x4_headless.py — REWRITTEN on every batch launch.\n"
        "# Edit LANE_STARTERS in x4_headless.py, not this file.\n"
        f"character_name: {lane_tag(slot)}\n"
        "gender: boy\n"
        f"starter: {lane_starter(slot)}\n"
        "starter_nickname: none\n",
        encoding="utf-8",
    )
    # ‼ Every lane would otherwise try to bind 127.0.0.1:8888 and dump an OSError
    # traceback from its HTTP thread into the log (visible in the user's own bundle
    # `P1-stdout-20260726-233837.txt`). Harmless, but it buries the story lines.
    (path / "http.yml").write_text(
        "# Managed by tools/story-dev/x4_headless.py.\n"
        "# OFF for headless lanes: N lanes cannot share one port, and the failures are noise.\n"
        "http_server:\n"
        "  enable: false\n"
        "  ip: 127.0.0.1\n"
        "  port: 8888\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
@dataclass
class Lane:
    slot: int
    tag: str
    starter: str
    profile: str
    profile_dir: Path
    out_dir: Path
    proc: subprocess.Popen | None = None
    fh: object = None
    restarts: int = 0
    finished_naturally: bool = False
    #: ⭐ #24-lane-respawn-build — the commit THIS LANE'S PROCESS LOADED, recorded at every spawn.
    #: A respawn imports whatever is on disk at that moment, so a batch's single `code_commit` can
    #: be a lie. One entry per spawn; more than one DISTINCT value means the batch is mixed.
    build_commits: list[str] = field(default_factory=list)
    #: debug-log path -> ('ok'|'bad'|'unknown', reason); one entry per run.
    headers: dict[str, tuple[str, str]] = field(default_factory=dict)

    @property
    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None


def git_commit() -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, timeout=15).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                               capture_output=True, text=True, timeout=15).stdout.strip()
        return f"{rev}{'-dirty' if dirty else ''}" if rev else "unknown"
    except Exception:
        return "unknown"


def lane_command(lane: Lane, runs_per_lane: int) -> list[str]:
    """The launch line. Kept in one place so it can be asserted by the repro.

    Deliberately IDENTICAL to a GUI x4 lane's arguments except that `--tile-*` (which
    selects the tile frontend) is replaced by `-hl`. The `--tile-*` args are GUI-only.
    """
    return [
        sys.executable, str(BUILD_ROOT / "pokebot.py"),
        lane.profile,
        "-m", BOT_MODE,
        "-s", "0",                       # unthrottled
        "-na",                           # muted at the source
        "-hl",                           # headless: no GUI WINDOW; renderer stays ON
        "--endless-target", str(runs_per_lane),   # 0 == forever
    ]


def lane_env() -> dict:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    # ‼ Without this a lane's stdout is block-buffered at 8 KiB because it is a FILE, not
    # a console — a lane can run for many minutes with nothing on disk, which reads
    # exactly like "the batch produced no logs" (user report, 2026-07-26).
    env["PYTHONUNBUFFERED"] = "1"
    # ‼ rich wraps at ~78 columns when stdout is a file, physically splitting the run
    # outcome lines this runner parses. Verified against the user's own lane logs.
    # 400 was NOT enough — a counter-chain derail message is ~1,000 chars and still wrapped,
    # which cost batch `20260731-105549` its finish-rate number entirely. This is a
    # mitigation only; `_RUN_END_RE` is wrap-tolerant because ANY width can be exceeded.
    env["COLUMNS"] = "20000"
    env.pop("SAVE_POST_RIVAL", None)     # never clobber committed checkpoints from a sweep
    return env


def spawn(lane: Lane, runs_per_lane: int) -> None:
    stdout_path = lane.out_dir / "stdout.txt"
    lane.fh = open(stdout_path, "a", encoding="utf-8", errors="replace")
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    lane.proc = subprocess.Popen(
        lane_command(lane, runs_per_lane),
        cwd=str(BUILD_ROOT),
        env=lane_env(),
        stdout=lane.fh,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=creation_flags,
    )
    # ⭐ PROVENANCE PER SPAWN, not per batch. A respawned lane loads the CURRENT on-disk code, so
    # this is the only moment the truth is available. Printed as well as stored, because the reader
    # who needs it most is someone scanning stdout after a surprising result.
    _spawn_commit = git_commit()
    lane.build_commits.append(_spawn_commit)
    print(f"[x4h] {lane.tag} ({lane.starter}) started — pid {lane.proc.pid}, "
          f"profile `{lane.profile}`, build {_spawn_commit}", flush=True)


def check_headers(lane: Lane, since: float, on_bad: str) -> list[dict]:
    """Assert `speed=0 video=True` on every NEW debug log this lane has produced.

    Checked continuously for the whole batch — not once at the start — because the
    failure being guarded against is "run 1 was unthrottled and run 2 crawled at 1x".
    """
    violations = []
    log_dir = lane.profile_dir / "debug-logs"
    if not log_dir.exists():
        return violations
    for log in sorted(log_dir.glob("*.log")):
        try:
            if log.stat().st_mtime < since - 5:
                continue
        except OSError:
            continue
        key = str(log)
        if lane.headers.get(key, ("unknown", ""))[0] in ("ok", "bad"):
            continue
        try:
            head = log.open("r", encoding="utf-8", errors="replace").read(8192)
        except OSError:
            continue
        verdict, reason = header_verdict(parse_run_header(head))
        lane.headers[key] = (verdict, reason)
        if verdict == "bad":
            print(f"\n{'!' * 72}\n[x4h] EMULATION ASSERTION FAILED — {lane.tag} — {log.name}\n"
                  f"       {reason}\n{'!' * 72}\n", flush=True)
            violations.append({"tag": lane.tag, "log": key, "reason": reason})
        elif verdict == "ok":
            print(f"[x4h] {lane.tag} header OK ({reason}) — {log.name}", flush=True)
    return violations


def stop_lane(lane: Lane) -> None:
    if lane.proc is not None and lane.proc.poll() is None:
        try:
            lane.proc.terminate()
        except Exception:
            pass
        try:
            lane.proc.wait(timeout=20)
        except Exception:
            try:
                lane.proc.kill()
            except Exception:
                pass
    if lane.fh is not None:
        try:
            lane.fh.close()
        except Exception:
            pass
        lane.fh = None


def collect_logs(lane: Lane, since: float) -> int:
    """Copy the debug logs produced during THIS batch into the batch directory.

    ‼ A profile's `debug-logs/` is CUMULATIVE and never archived, exactly like
    `badge-log.json`. Copying the directory wholesale would fold months-old runs into a
    fresh batch's numbers, which has already produced one phantom regression report in
    this project. Filter by mtime against the batch start, always.
    """
    dest = lane.out_dir / "debug-logs"
    dest.mkdir(exist_ok=True)
    n = 0
    src_dir = lane.profile_dir / "debug-logs"
    if not src_dir.exists():
        return 0
    for f in sorted(src_dir.glob("*.log")):
        try:
            if f.stat().st_mtime < since - 5:
                continue
            shutil.copy2(f, dest / f.name)
            n += 1
        except OSError:
            pass
    return n



def _merge_end_reasons(lanes_detail: dict) -> Counter:
    """Sum each lane's `end_reasons` into one Counter.

    Trivial, and it exists as a named function ONLY because getting it wrong was invisible:
    the buggy version returned a plausible-looking dict with plausible-looking counts.
    `repro_x4_headless.py` asserts a reason shared by several lanes sums rather than
    overwrites.
    """
    merged: Counter = Counter()
    for lane in lanes_detail.values():
        merged.update(lane.get("end_reasons", {}))
    return merged

def status(target: str) -> int:
    """Print progress for a RUNNING or finished batch. STRICTLY READ-ONLY.

    ⛔ WHY THIS EXISTS: `--resummarise` reads a FINISHED batch, so there was no way to answer
    "how is it going?" during an 8-hour run without opening files by hand. Lanes write stdout LIVE
    and unbuffered (`lane_env` sets `PYTHONUNBUFFERED=1` precisely so a long-running lane is not
    invisible on disk), so the data is already there.
    ‼ It opens files and NOTHING else — no signals, no writes, no process inspection. Checking on a
    batch must never be able to perturb it.
    """
    root = RUNS_ROOT
    if target.strip().lower() == "latest":
        # ⛔⛔ RESOLVE BY NEWEST STAMP DIRECTORY, **NOT** VIA `LATEST.txt`. That pointer is only
        # written when a batch COMPLETES, so `--status latest` used to report the last FINISHED
        # batch while a new one was actively running — the single case this command exists for.
        # A status command that silently reports a DIFFERENT batch is worse than none: the numbers
        # look plausible and belong to someone else.
        # Stamps are `YYYYmmdd-HHMMSS`, so lexical sort == chronological, and the directory exists
        # from the moment the batch starts.
        stamps = sorted(
            (d for d in root.glob("[0-9]" * 8 + "-" + "[0-9]" * 6) if d.is_dir()),
            key=lambda d: d.name,
        )
        if not stamps:
            pointer = root / "LATEST.txt"          # fallback for an unusual layout
            if not pointer.exists():
                print(f"[x4h] no batch directories under {root} — has a batch ever run?", flush=True)
                return 2
            batch_dir = root / pointer.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        else:
            batch_dir = stamps[-1]
    else:
        batch_dir = Path(target)
    if not batch_dir.exists():
        print(f"[x4h] no such batch dir: {batch_dir}", flush=True)
        return 2

    manifest = batch_dir / "MANIFEST.txt"
    header = manifest.read_text(encoding="utf-8", errors="replace").splitlines()[:12] \
        if manifest.exists() else ["(no MANIFEST yet — the batch is still starting)"]
    # ‼ A batch with no `ended` line in its MANIFEST (or no MANIFEST yet) is still RUNNING.
    # Stating it removes the only way to misread this output.
    _man_text = (batch_dir / "MANIFEST.txt").read_text(encoding="utf-8", errors="replace") \
        if (batch_dir / "MANIFEST.txt").exists() else ""
    _live = "(no MANIFEST yet)" not in _man_text and "ended " not in _man_text
    print("=" * 78)
    print(f"x4 BATCH STATUS — {batch_dir.name}   [{'RUNNING' if _live else 'finished'}]")
    print(f"  dir: {batch_dir}")
    print("=" * 78)
    for line in header:
        if line.strip() and not line.startswith("="):
            print("  " + line)

    lane_dirs = sorted(d for d in batch_dir.glob("L*") if d.is_dir())
    if not lane_dirs:
        print("\n  no lane directories yet.")
        return 0

    # ⛔⛔ USE `summarize_lane`, NEVER A HAND-ROLLED COUNT. The first version of this function
    # counted the literal string "FINISHED" and reported 0% for a batch whose own INDEX row records
    # 36% — a status tool that understates progress is worse than none, because it turns a healthy
    # batch into a false alarm. `summarize_lane` is the SAME logic the batch summary and the gate
    # use, so this figure and the recorded one can never disagree.
    # ‹ `debug_text=""` is deliberate: runs/finished derive from `_RUN_END_RE` over stdout alone.
    print(f"\n  {'lane':<6} {'runs':>5} {'fin':>4} {'rate':>6}  last activity")
    print("  " + "-" * 72)
    total_runs = total_fin = 0
    reasons: Counter = Counter()
    for d in lane_dirs:
        out = d / "stdout.txt"
        text = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
        lane_sum = summarize_lane(text, "")
        runs, fin = lane_sum["runs_ended"], lane_sum["finished"]
        total_runs += runs
        total_fin += fin
        reasons.update(lane_sum.get("end_reasons", {}))
        rate = f"{(100 * fin / runs):.0f}%" if runs else "-"
        tail = ""
        for line in reversed(text.splitlines()):
            if line.strip():
                tail = line.strip()[:58]
                break
        print(f"  {d.name:<6} {runs:>5} {fin:>4} {rate:>6}  {tail}")
    overall = f"{(100 * total_fin / total_runs):.0f}%" if total_runs else "-"
    print("  " + "-" * 72)
    print(f"  {'TOTAL':<6} {total_runs:>5} {total_fin:>4} {overall:>6}")

    if reasons:
        # ⭐ The code's own comment calls this "the only number that should drive the next item".
        print("\n  WHY RUNS ENDED (grouped) — the number that should drive the next item:")
        for reason, n in reasons.most_common(8):
            print(f"    {n:>4}x  {reason[:66]}")

    print("\n  ⚠ A rate from a PARTIAL batch is a running figure, not a result — lanes mid-run")
    print("    drag it down. Compare only completed batches, and only against the same build.")
    return 0


def resummarise(batch_dir: Path) -> int:
    """Re-parse a stored batch's logs and rewrite its `summary.json` / `MANIFEST.txt`.

    ‼ WHY THIS EXISTS. On batch `20260731-105549` the parser under-counted run outcomes
    (see `_RUN_END_RE`) and the summary claimed a 69% finish rate against a true ~22%,
    with the dominant end reason missing entirely. **The raw logs were fine** — only the
    reading of them was wrong. Re-running three hours of emulation to fix a regex would
    have been absurd, and worse, it would have produced a DIFFERENT sample, so the old and
    new numbers could not be compared. Separating "the data" from "a reading of the data"
    is what makes a parser bug cheap.

    The recorded `code_commit` is preserved: it describes the code that PRODUCED the logs,
    not the code that parsed them.
    """
    # ‼ RESOLVE THE PATH. This compared `batch_dir.parent == RUNS_ROOT` below, and
    # `--resummarise x4-runs/<stamp>` (a relative path, the natural way to type it) made that
    # comparison False — so the corrected numbers were written to summary.json and MANIFEST
    # while INDEX.md silently kept the WRONG ones. INDEX.md is the first thing a review
    # reads, so a stale row there is worse than no row: batch 20260731-105549 sat in the
    # index claiming a 69% finish rate for an hour after it had been corrected to 23.7%.
    batch_dir = batch_dir.resolve()
    summary_path = batch_dir / "summary.json"
    if not summary_path.exists():
        print(f"[x4h] FATAL: no summary.json in {batch_dir}", flush=True)
        return 2
    old = json.loads(summary_path.read_text(encoding="utf-8"))
    print(f"[x4h] re-summarising {batch_dir.name} (code_commit {old.get('code_commit')})", flush=True)

    lanes_detail: dict[str, dict] = {}
    lane_rows = []
    for row in old.get("lane_rows", []):
        tag = row["tag"]
        slot = int(tag.lstrip("H")) - 1
        out_dir = batch_dir / f"L{slot + 1:02d}"
        try:
            stdout_text = (out_dir / "stdout.txt").read_text(encoding="utf-8", errors="replace")
        except OSError:
            stdout_text = ""
        debug_text = ""
        for f in sorted((out_dir / "debug-logs").glob("*.log")):
            try:
                debug_text += f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
        s = summarize_lane(stdout_text, debug_text)
        previous = old.get("lanes_detail", {}).get(tag, {})
        # Carry forward the facts that come from the RUN, not from parsing.
        for key in ("build_commits", "header_verdict", "headers_checked", "restarts", "starter",
                    "profile",
                    "debug_logs_collected"):
            s[key] = previous.get(key, row.get(key))
        lanes_detail[tag] = s
        lane_rows.append({**row, "runs_ended": s["runs_ended"], "finished": s["finished"]})
        print(f"[x4h]   {tag}: runs {previous.get('runs_ended', '?')} -> {s['runs_ended']}, "
              f"finished {previous.get('finished', '?')} -> {s['finished']}", flush=True)

    total_runs = sum(s["runs_ended"] for s in lanes_detail.values())
    total_fin = sum(s["finished"] for s in lanes_detail.values())
    batch = {
        **old,
        "resummarised": True,
        "lane_rows": lane_rows,
        "lanes_detail": lanes_detail,
        "totals": {
            "runs": total_runs,
            "finished": total_fin,
            "finish_rate": round(total_fin / total_runs, 3) if total_runs else None,
            "global_watchdog": sum(s["global_watchdog"] for s in lanes_detail.values()),
            "faint_chooser_gave_up": sum(s["faint_chooser_gave_up"] for s in lanes_detail.values()),
            "no_eligible_replacement": sum(s["no_eligible_replacement"] for s in lanes_detail.values()),
            "stuck_dumps": sum(s["stuck_dumps"] for s in lanes_detail.values()),
            # ‼ MUST ACCUMULATE, NOT REBUILD A DICT. This was
            # `Counter({k: v for s in ... for k, v in s["end_reasons"].items()})` — an inner
            # dict comprehension, so a reason appearing in several lanes had every lane but
            # the LAST silently overwritten. Batch `20260731-105549` reported 9 end reasons
            # for 29 non-finishing runs and the discrepancy is the only thing that exposed
            # it. Sum across lanes.
            "end_reasons": dict(_merge_end_reasons(lanes_detail).most_common()),
        },
    }
    summary_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")
    (batch_dir / "MANIFEST.txt").write_text(render_manifest(batch), encoding="utf-8")
    if batch_dir.parent == RUNS_ROOT.resolve():
        rebuild_index(RUNS_ROOT)
    else:
        print(f"[x4h] NOTE: {batch_dir} is outside {RUNS_ROOT}, so INDEX.md was NOT rebuilt.",
              flush=True)
    print(f"\n[x4h] TOTALS now: {total_fin}/{total_runs} finished "
          f"({batch['totals']['finish_rate']})", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Headless ENDLESS-RESET batch runner (matches the GUI x4 mode exactly).")
    # Default 4 to MIRROR the user's GUI dashboard (torchic/mudkip/treecko/random). On the
    # dev box use 8: four lanes measured ~4 cores of a 16C/32T machine, so 8 is comfortable
    # and still leaves headroom. Do not max it out.
    ap.add_argument("--build", choices=sorted(BUILD_ROOTS), default="custom",
                    help="which fork the lanes run (default: custom — the fork that HOLDS STILL "
                         "while the sandbox is being edited). Recorded in the MANIFEST.")
    ap.add_argument("--status", default=None, metavar="BATCH_DIR",
                    help="print live progress for a RUNNING (or finished) batch and exit. "
                         "Accepts a batch dir or the word 'latest'. Strictly read-only — it opens "
                         "files and never signals a process, so it is safe to run at any time.")
    ap.add_argument("--lanes", type=int, default=4)
    ap.add_argument("--minutes", type=float, default=0.0,
                    help="wall-clock bound; 0 = unbounded (then --runs must be set)")
    ap.add_argument("--runs", type=int, default=0,
                    help="runs PER LANE (--endless-target); 0 = infinite")
    ap.add_argument("--out", default=None, help="batch directory (default x4-runs/<stamp>)")
    ap.add_argument("--stagger", type=float, default=6.0,
                    help="seconds between lane launches (avoids a startup thundering herd)")
    ap.add_argument("--max-restarts", type=int, default=3,
                    help="per-lane respawns if a lane process dies before the bound")
    ap.add_argument("--on-bad-header", choices=["abort", "warn"], default="abort",
                    help="what to do when a lane reports speed!=0 or video!=True")
    ap.add_argument("--collect", choices=["full", "none"], default="full",
                    help="copy this batch's debug logs into the batch dir")
    ap.add_argument("--wipe-saves", action="store_true",
                    help="delete each lane's current_save.sav/current_state.ss1 first "
                         "(NOT needed: ENDLESS RESET hard-resets and picks NEW GAME itself)")
    ap.add_argument("--resummarise", default=None, metavar="BATCH_DIR",
                    help="re-parse a stored batch's logs and rewrite its summary/MANIFEST, "
                         "without running anything. Use after fixing a parser bug: the raw "
                         "logs are the data, the summary is only a reading of them.")
    args = ap.parse_args()

    if args.status:
        return status(args.status)

    if args.resummarise:
        return resummarise(Path(args.resummarise))

    # ⛔ REBIND THE BUILD BEFORE ANY LANE IS PREPARED. `ensure_lane_profile` and `lane_command`
    # read these at call time, so this must happen before either runs.
    global BUILD_NAME, BUILD_ROOT, PROFILES
    BUILD_NAME = args.build
    BUILD_ROOT = REPO_ROOT / BUILD_ROOTS[BUILD_NAME]
    PROFILES = BUILD_ROOT / "profiles"
    if not (BUILD_ROOT / "pokebot.py").exists():
        print(f"[x4h] FATAL: --build {BUILD_NAME} -> {BUILD_ROOT} has no pokebot.py", flush=True)
        return 2

    if args.lanes < 1:
        print("[x4h] FATAL: --lanes must be >= 1", flush=True)
        return 2
    if args.minutes <= 0 and args.runs <= 0:
        # ‼ An unbounded batch is how a machine gets left running for a day. Refuse it.
        print("[x4h] FATAL: give a bound — --minutes N and/or --runs N (runs per lane).",
              flush=True)
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_root = Path(args.out) if args.out else RUNS_ROOT / stamp
    out_root.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    started = datetime.now()
    since = time.time()

    print(f"[x4h] batch {stamp} — {args.lanes} lane(s), "
          f"runs/lane={args.runs or 'infinite'}, minutes={args.minutes or 'unbounded'}, "
          f"code={commit}, build={BUILD_NAME} ({BUILD_ROOT.name})", flush=True)
    print(f"[x4h] output: {out_root}", flush=True)
    if commit.endswith("-dirty"):
        print("[x4h] ‼ WORKING TREE IS DIRTY — this batch cannot be attributed to a commit.",
              flush=True)

    lanes: list[Lane] = []
    for slot in range(args.lanes):
        prof_dir = ensure_lane_profile(slot)
        if args.wipe_saves:
            for name in ("current_save.sav", "current_state.ss1"):
                f = prof_dir / name
                if f.exists():
                    f.unlink()
        out_dir = out_root / f"L{slot + 1:02d}"
        out_dir.mkdir(exist_ok=True)
        lanes.append(Lane(slot=slot, tag=lane_tag(slot), starter=lane_starter(slot),
                          profile=lane_profile_name(slot), profile_dir=prof_dir,
                          out_dir=out_dir))

    header_violations: list[dict] = []
    aborted = ""
    deadline = since + args.minutes * 60 if args.minutes > 0 else None

    for i, lane in enumerate(lanes):
        spawn(lane, args.runs)
        if i < len(lanes) - 1 and args.stagger > 0:
            time.sleep(args.stagger)

    try:
        while True:
            time.sleep(5)
            now = time.time()

            for lane in lanes:
                header_violations.extend(check_headers(lane, since, args.on_bad_header))

            if header_violations and args.on_bad_header == "abort":
                aborted = "EMULATION ASSERTION FAILED"
                break

            for lane in lanes:
                if lane.alive:
                    continue
                try:
                    text = (lane.out_dir / "stdout.txt").read_text(encoding="utf-8", errors="replace")
                except OSError:
                    text = ""
                if _BATCH_DONE in text:
                    lane.finished_naturally = True
                    if lane.proc is not None:
                        stop_lane(lane)
                        lane.proc = None
                        print(f"[x4h] {lane.tag} completed its {args.runs} run(s).", flush=True)
                    continue
                if lane.proc is None:
                    continue
                code = lane.proc.returncode
                stop_lane(lane)
                lane.proc = None
                if lane.restarts >= args.max_restarts or deadline is None or now >= deadline:
                    print(f"[x4h] ‼ {lane.tag} died (exit {code}) and will NOT be restarted "
                          f"(restarts={lane.restarts}).", flush=True)
                    continue
                lane.restarts += 1
                print(f"[x4h] ‼ {lane.tag} died (exit {code}); restart "
                      f"{lane.restarts}/{args.max_restarts}.", flush=True)
                spawn(lane, args.runs)

            if all(not l.alive and l.proc is None for l in lanes):
                print("[x4h] all lanes have stopped.", flush=True)
                break
            if deadline is not None and now >= deadline:
                print(f"[x4h] time bound reached ({args.minutes} min) — stopping lanes.", flush=True)
                break
    except KeyboardInterrupt:
        aborted = "interrupted by user (Ctrl-C)"
        print("\n[x4h] interrupted — stopping lanes and summarising what we have.", flush=True)

    for lane in lanes:
        stop_lane(lane)
    # Give the OS a moment to flush the line-buffered debug logs before they are read.
    time.sleep(2)

    lanes_detail: dict[str, dict] = {}
    lane_rows = []
    for lane in lanes:
        try:
            stdout_text = (lane.out_dir / "stdout.txt").read_text(encoding="utf-8", errors="replace")
        except OSError:
            stdout_text = ""
        n_logs = collect_logs(lane, since) if args.collect == "full" else 0
        debug_text = ""
        for f in sorted((lane.out_dir / "debug-logs").glob("*.log")) if n_logs else []:
            try:
                debug_text += f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
        s = lane_summary(lane, stdout_text, debug_text, n_logs)
        lanes_detail[lane.tag] = s
        lane_rows.append({
            "tag": lane.tag, "starter": lane.starter, "profile": lane.profile,
            "runs_ended": s["runs_ended"], "finished": s["finished"],
            "header_verdict": s["header_verdict"], "restarts": lane.restarts,
            # ‼ carried here too so `resummarise()`'s `row` fallback can find it.
            "build_commits": list(lane.build_commits),
        })

    ended = datetime.now()
    total_runs = sum(s["runs_ended"] for s in lanes_detail.values())
    total_fin = sum(s["finished"] for s in lanes_detail.values())
    verdict = "FAILED — " + aborted if aborted else "OK"
    batch = {
        "stamp": stamp,
        "code_commit": commit,
        "bot_mode": BOT_MODE,
        "lanes": args.lanes,
        "runs_per_lane": args.runs,
        "minutes": args.minutes,
        "started": started.isoformat(timespec="seconds"),
        "ended": ended.isoformat(timespec="seconds"),
        "wall_minutes": round((ended - started).total_seconds() / 60, 1),
        "verdict": verdict,
        "headers_checked": sum(s["headers_checked"] for s in lanes_detail.values()),
        "header_violations": header_violations,
        "totals": {
            "runs": total_runs,
            "finished": total_fin,
            "finish_rate": round(total_fin / total_runs, 3) if total_runs else None,
            "global_watchdog": sum(s["global_watchdog"] for s in lanes_detail.values()),
            "faint_chooser_gave_up": sum(s["faint_chooser_gave_up"] for s in lanes_detail.values()),
            "no_eligible_replacement": sum(s["no_eligible_replacement"] for s in lanes_detail.values()),
            "stuck_dumps": sum(s["stuck_dumps"] for s in lanes_detail.values()),
            # ‼ MUST ACCUMULATE, NOT REBUILD A DICT. This was
            # `Counter({k: v for s in ... for k, v in s["end_reasons"].items()})` — an inner
            # dict comprehension, so a reason appearing in several lanes had every lane but
            # the LAST silently overwritten. Batch `20260731-105549` reported 9 end reasons
            # for 29 non-finishing runs and the discrepancy is the only thing that exposed
            # it. Sum across lanes.
            "end_reasons": dict(_merge_end_reasons(lanes_detail).most_common()),
        },
        "lane_rows": lane_rows,
        "lanes_detail": lanes_detail,
    }
    (out_root / "summary.json").write_text(json.dumps(batch, indent=2), encoding="utf-8")
    (out_root / "MANIFEST.txt").write_text(render_manifest(batch), encoding="utf-8")

    if args.out is None:
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)
        (RUNS_ROOT / "LATEST.txt").write_text(
            f"{stamp}\n{out_root}\ncommit {commit}\n", encoding="utf-8")
        rebuild_index(RUNS_ROOT)

    print("\n" + render_manifest(batch), flush=True)
    print(f"[x4h] batch summary: {out_root / 'summary.json'}", flush=True)
    if header_violations:
        print(f"[x4h] ‼ {len(header_violations)} EMULATION ASSERTION VIOLATION(S) — "
              f"this batch's timings are NOT comparable.", flush=True)
        return 3
    return 1 if aborted else 0


if __name__ == "__main__":
    sys.exit(main())
