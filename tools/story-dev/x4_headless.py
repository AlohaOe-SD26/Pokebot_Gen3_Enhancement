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
import ast
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback
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


def lane_profile_name(slot: int, tag: str | None = None) -> str:
    """Namespaced away from the GUI's `endless-P{n}-…` lanes ON PURPOSE.

    Two bot processes must never share a profile directory (they clash on
    `current_save.sav` / `current_state.ss1` / `stats.db` — `livetest.py` learned this
    the hard way). The user can be running their own GUI x4 batch on this box at the
    same time as a headless batch, so the two families must not overlap.
    ⭐ `tag` (`--profile-tag`, design v2 step 14 T1): `endless-<tag>-H{n}-<starter>`, a FRESH family per A/B batch, so no
    lane inherits `stats.db` / `badge-log.json` / a save from an earlier batch (the old `endless-H*` profiles carry them).
    """
    if tag:
        return f"endless-{tag}-{lane_tag(slot)}-{lane_starter(slot)}"
    return f"endless-{lane_tag(slot)}-{lane_starter(slot)}"


# ---------------------------------------------------------------------------
# Per-lane ARMS (design v2 step 14, T1 — `ai-research-notes/2026-10-01-batch14-DESIGN.md` §3 and
# `…-batch14-T1-PREDICTIONS.md`). Pure, covered by `repro_x4_headless.py` section F.
# ⛔ WHY: every lane used to inherit the launching shell's environment, so a concurrent A/B was impossible, and an
# inherited flag silently turned BOTH arms on (the result then reads as "the feature does nothing").
# ---------------------------------------------------------------------------
#: A key matching this is a fault arm or a §B switch (`29-DISABLED-FEATURES-REGISTRY.md`) and never belongs in an arm.
#: `FAULT` anywhere, not `_FAULT_`: `POKEBOT_PCPINGPONG_FAULT` and `POKEBOT_CH24ROOM_FAULT` have no trailing underscore.
_FORBIDDEN_KEY_RE = re.compile(r"FAULT|_ARM\d*$|_A$")
#: A fixed decorrelation value makes every run of a lane the same trajectory (`modules/story/intro.py:70-89`).
_FORBIDDEN_KEYS = frozenset({"POKEBOT_RNG_DECORRELATION_FRAMES"})
#: D6: behaviour or trace variables WITHOUT the `POKEBOT_` prefix that the sandbox reads (grep, 2026-10-01). They are
#: stripped from every lane of an `--arms` batch, since `env-all:` records only `POKEBOT_*` and could not show a leak.
#: ‼ The gate scans the build for any other such name, so a new one cannot slip past this list.
#: `AI_PLAYER_PACKAGE_ROOT` (2026-10-22): the AI player's plugin (`plugins/custom_modes/ai_player_mode.py`) loads its
#: package from it; only `py -3.12 -m ai_player run` should set it, and a value inherited from a shell that ran the AI
#: could point a bot lane at another checkout's package. Added after the gate had been red on it since 2026-10-07.
STRIP_UNPREFIXED: tuple[str, ...] = ("TEACH_TRACE", "TEACH_MISS_WINDOW", "TEACH_CANCEL_FORGET", "STORY_TALK_DEBUG",
                                     "KI15_TRACE", "FW_TRACE", "CAPTURE_FORCE", "SAVE_POST_RIVAL",
                                     "AI_PLAYER_PACKAGE_ROOT")
STRIP_UNPREFIXED_PREFIXES: tuple[str, ...] = ("CH21_CAPTURE_",)
_TAG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_POKEBOT_TOKEN_RE = re.compile(r"POKEBOT_[A-Za-z0-9_]+")
#: The run header's `env-all:` line (`modules/debug_logger.py:262-266`): a dict repr, or a "(no POKEBOT_* …)" note.
_ENV_ALL_RE = re.compile(r"^\s*env-all:\s+(.*)$", re.MULTILINE)
#: The run header's `build:` line holds HEAD's first 12 hex digits (`modules/debug_logger.py:128-170`).
_BUILD_RE = re.compile(r"^\s*build:\s+([0-9a-f]{7,40})\b", re.MULTILINE)


def build_source_text(build_root: Path) -> str:
    """Every `*.py` under the build's `modules/` and `plugins/`, concatenated: the text an arm key must appear in."""
    parts = []
    for sub in ("modules", "plugins"):
        for f in sorted((build_root / sub).rglob("*.py")):
            try:
                parts.append(f.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    return "\n".join(parts)


def validate_tag(tag: str | None) -> str | None:
    """None if `tag` is a usable `--profile-tag`, else why not. It must not start with `P`: `endless-P*` is the GUI's
    namespace, and `battle_log.scan_logs` globs it."""
    if not tag or not _TAG_RE.fullmatch(tag):
        return f"--profile-tag {tag!r} must be non-empty and use only [A-Za-z0-9_-], starting with a letter or digit"
    if tag[0] in "Pp":
        return f"--profile-tag {tag!r} must not start with P (the GUI's endless-P* namespace)"
    return None


def _monitor_errors(monitor, arm_names) -> list[str]:
    errors: list[str] = []
    if monitor is None:
        return errors
    if not isinstance(monitor, dict):
        return ["`monitor` must be an object keyed by arm name"]
    for arm, cfg in monitor.items():
        if arm not in arm_names:
            errors.append(f"monitor names an unknown arm {arm!r}")
            continue
        if not isinstance(cfg, dict) or set(cfg) - {"forbid", "require", "expect"}:
            errors.append(f"monitor[{arm!r}] must be an object with only forbid / require / expect")
            continue
        for entry in cfg.get("forbid", []):
            ok = (isinstance(entry, str) and entry) or (
                isinstance(entry, list) and entry and all(isinstance(s, str) and s for s in entry))
            if not ok:
                errors.append(f"monitor[{arm!r}].forbid entry {entry!r} must be a non-empty string or list of strings")
        req = cfg.get("require", {})
        if not isinstance(req, dict) or not all(
                isinstance(k, str) and k and isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
                for k, v in req.items()):
            errors.append(f"monitor[{arm!r}].require must map non-empty strings to positive seconds")
        exp = cfg.get("expect", [])
        if not isinstance(exp, list) or not all(isinstance(s, str) and s for s in exp):
            errors.append(f"monitor[{arm!r}].expect must be a list of non-empty strings")
    return errors


def validate_arms(spec, n_lanes: int, source_text: str) -> list[str]:
    """PURE pre-flight for an `--arms` file. [] means valid; otherwise every reason it is refused (all of them, so one
    run of the launcher shows the whole problem)."""
    if not isinstance(spec, dict) or not isinstance(spec.get("arms"), dict):
        return ["the file must be an object with an `arms` object"]
    if set(spec) - {"arms", "monitor", "comment"}:
        return [f"unknown top-level keys: {sorted(set(spec) - {'arms', 'monitor', 'comment'})}"]
    arms = spec["arms"]
    errors: list[str] = []
    # ⛔ WHOLE TOKENS, not substrings: the gate's typo row caught `POKEBOT_R26_KITTOPOF` passing a substring test,
    # because it sits inside `POKEBOT_R26_KITTOPOFF` (2026-10-01).
    tokens = set(_POKEBOT_TOKEN_RE.findall(source_text))
    if len(arms) < 2:
        errors.append("an A/B needs at least 2 arms")
    keysets = []
    for name, env in arms.items():
        if not isinstance(env, dict) or not env:
            errors.append(f"arm {name!r} must be a non-empty object of variables")
            continue
        keysets.append(frozenset(env))
        for key, value in env.items():
            if not isinstance(value, str):
                errors.append(f"arm {name!r}: {key} must be a string, not {type(value).__name__}")
            if not key.startswith("POKEBOT_"):
                errors.append(f"arm {name!r}: {key} is not a POKEBOT_ variable")
            if _FORBIDDEN_KEY_RE.search(key) or key in _FORBIDDEN_KEYS:
                errors.append(f"arm {name!r}: {key} is a fault arm, a §B switch or a determinism override")
            elif key not in tokens:
                errors.append(f"arm {name!r}: {key} appears nowhere in the build's source (a typo?)")
    if len(set(keysets)) > 1:
        errors.append("every arm must list the SAME variables (each arm is literal and complete)")
    envs = [tuple(sorted(e.items())) for e in arms.values() if isinstance(e, dict)]
    if len(envs) != len(set(envs)):
        errors.append("two arms are identical — the A/B would be vacuous")
    k = len(arms)
    if k and n_lanes % k:
        errors.append(f"--lanes {n_lanes} does not divide evenly into {k} arms")
    elif k:
        per = n_lanes // k
        for i in range(per):
            starters = {lane_starter(a * per + i) for a in range(k)}
            if len(starters) > 1:
                errors.append(f"within-arm position {i} has different starters across arms: {sorted(starters)} "
                              f"(lanes per arm must be a multiple of {len(LANE_STARTERS)})")
                break
    errors += _monitor_errors(spec.get("monitor"), set(arms))
    return errors


def arms_preflight(arms_path, tag, n_lanes: int, build_name: str, build_root: Path,
                   profiles: Path, repo_root: Path | None = None) -> tuple[list[str], dict | None, str]:
    """(errors, the parsed arms spec or None, its text). Every refusal `main` makes before a directory exists or a lane
    spawns, in one function a gate can drive without ever launching a lane."""
    errors: list[str] = []
    if tag is not None:
        why = validate_tag(tag)
        if why:
            errors.append(why)
    # ⛔ review R11: a fault variable left in the shell after the live fault run would abort the REAL batch ~90 s in,
    # after the operator has gone. It may only arm a batch whose tag SAYS it is a fault run.
    if os.environ.get("X4H_FAULT_ENVLEAK") == "1" and "fault" not in (tag or ""):
        errors.append("X4H_FAULT_ENVLEAK=1 is set in this shell but the --profile-tag does not contain 'fault': unset "
                      "it (a stale fault variable would abort a real batch)")
    spec, text = None, ""
    if arms_path:
        if build_name != "sandbox":
            errors.append("--arms needs --build sandbox (the custom fork has none of the flags an arm sets, and no "
                          "env-all header line to verify them)")
        if not tag:
            errors.append("--arms needs --profile-tag (an A/B starts from FRESH lane profiles)")
        # ⛔ review R9: from a git WORKTREE `.git` is a file, the lanes' `build:` header reads "not a git checkout", and
        # the build check would abort on the first header with a misleading reason. Run an A/B from a main checkout.
        root = repo_root if repo_root is not None else REPO_ROOT
        if not (root / ".git").is_dir():
            errors.append(f"--arms must run from a MAIN checkout ({root} has no .git directory: a worktree's lane "
                          f"headers cannot name their commit)")
        try:
            text = Path(arms_path).read_text(encoding="utf-8")
            spec = json.loads(text)
        except (OSError, ValueError) as exc:
            return errors + [f"cannot read the arms file {arms_path}: {exc}"], None, ""
        errors += [f"arms file: {e}" for e in validate_arms(spec, n_lanes, build_source_text(build_root))]
    if tag and not validate_tag(tag):
        taken = [lane_profile_name(s, tag) for s in range(n_lanes) if (profiles / lane_profile_name(s, tag)).exists()]
        if taken:
            errors.append(f"--profile-tag {tag}: these lane profiles already exist (pick a new tag): {taken}")
    return errors, (spec if not errors else None), text


def arm_of_slot(slot: int, n_lanes: int, arm_names: list[str]) -> str:
    """Arms take CONTIGUOUS blocks: arm k owns slots [k*per, (k+1)*per)."""
    return arm_names[slot // (n_lanes // len(arm_names))]


def lane_name(slot: int, n_lanes: int, n_arms: int) -> str:
    """The in-game player name. ⭐ PAIRED ACROSS ARMS (design §2, review R10): slot i of every arm gets the same name, so
    each starter's A and B lanes draw from one seed pool (name entry is part of the seed, `intro.py`). Names differ
    WITHIN an arm."""
    return lane_tag(slot % (n_lanes // n_arms))


def strip_inherited(environ: dict) -> tuple[dict, list[str]]:
    """PURE: (a copy of `environ` without any `POKEBOT_*` or D6 variable, the sorted names removed)."""
    env, removed = {}, []
    for k, v in environ.items():
        if (k.startswith("POKEBOT_") or k in STRIP_UNPREFIXED
                or any(k.startswith(p) for p in STRIP_UNPREFIXED_PREFIXES)):
            removed.append(k)
        else:
            env[k] = v
    return env, sorted(removed)


def arm_header_verdict(header_text: str, expect_env: dict, expect_build: str | None) -> tuple[str, str]:
    """('ok'|'bad'|'unknown', reason) for ONE run log's header against its lane's arm. FAIL-CLOSED (review R8/AI-5):
    once the header is complete, a missing / unparseable / non-dict `env-all:` is BAD, never "unknown" — the emulation
    check's "unknown" is what let a header that does not say pass silently."""
    if _HEADER_END not in header_text:
        return "unknown", "run header not written yet"
    head = header_text.split(_HEADER_END)[0]
    m = _ENV_ALL_RE.search(head)
    if not m:
        return "bad", "complete run header has NO `env-all:` line"
    raw = m.group(1).strip()
    try:
        got = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return "bad", f"`env-all:` is not a dict: {raw[:120]!r}"
    if not isinstance(got, dict):
        return "bad", f"`env-all:` is not a dict: {raw[:120]!r}"
    if got != expect_env:
        extra = sorted(set(got) - set(expect_env))
        missing = sorted(set(expect_env) - set(got))
        differ = sorted(k for k in set(got) & set(expect_env) if got[k] != expect_env[k])
        return "bad", f"env-all differs from the arm: extra={extra} missing={missing} differ={differ}"
    if expect_build:
        b = _BUILD_RE.search(head)
        if not b:
            return "bad", "complete run header has no readable `build:` commit"
        n = min(len(b.group(1)), len(expect_build))
        if b.group(1)[:n] != expect_build[:n]:
            return "bad", f"build {b.group(1)} is not the batch's commit {expect_build[:12]}"
    return "ok", "env-all == arm" + (" and build matches" if expect_build else "")


def line_hit(line: str, entry) -> bool:
    """A monitor entry matches a line: a string as a plain SUBSTRING of the whole line (review AI-4: three markers sit
    outside the category slot), a list when EVERY string is on that one line."""
    if isinstance(entry, str):
        return entry in line
    return all(s in line for s in entry)


def scan_lines(lines, forbid, watch) -> tuple[list, set]:
    """PURE: ([(entry, line) for every forbid hit], {watched substrings seen})."""
    hits, seen = [], set()
    for line in lines:
        for entry in forbid:
            if line_hit(line, entry):
                hits.append((entry, line))
        for sub in watch:
            if sub in line:
                seen.add(sub)
    return hits, seen


def freeze_verdict(start, now) -> str:
    """'ok' | 'broken' | 'unknown'. A snapshot is (HEAD, porcelain) or None when git failed. ⛔ A git hiccup is
    'unknown', never 'broken': a false alarm would kill a 13-hour batch (the `build_provenance_lines` precedent)."""
    if start is None or now is None:
        return "unknown"
    return "ok" if tuple(start) == tuple(now) else "broken"


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
    # ⭐ design v2 step 14 T1: the facts an A/B grade needs, carried off the Lane (the JOURNEY, not just the shape).
    s["arm"] = lane.arm
    s["name"] = lane.name
    s["spawns"] = [dict(sp) for sp in lane.spawns]
    s["alive_at_deadline"] = lane.alive_at_deadline
    s["alive_at_stop"] = lane.alive_at_stop
    s["cut_log"] = lane.cut_log
    s["monitor"] = {"first_seen": dict(lane.first_seen)}
    # ⛔ review R7: "checked" counts only headers that SETTLED ok; a run cut before its header completed is unknown.
    _av = [v for v, _ in lane.arm_headers.values()]
    s["arm_headers_checked"] = sum(v == "ok" for v in _av)
    s["arm_headers_unknown"] = sum(v == "unknown" for v in _av)
    s["arm_header_verdict"] = (None if lane.arm_env is None else
                               "BAD" if "bad" in _av else ("ok" if "ok" in _av else "unknown"))
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
        f"{'tag':<5} {'starter':<9} {'profile':<26} {'runs':>5} {'fin':>4} {'header':<8} restarts  arm  armhdr",
    ]
    for ln in batch["lane_rows"]:
        lines.append(
            f"{ln['tag']:<5} {ln['starter']:<9} {ln['profile']:<26} "
            f"{ln['runs_ended']:>5} {ln['finished']:>4} {ln['header_verdict']:<8} {ln['restarts']:<8}  "
            f"{ln.get('arm') or '-':<4} {ln.get('arm_header_verdict') or '-'}"
        )
    if batch.get("arms"):
        # ⭐ design v2 step 14 T1: an A/B batch. Its arms file and hash identify exactly what each arm ran.
        lines += ["", f"ARMS           {'/'.join(batch['arms'])}  file {batch.get('arms_file', '?')}  "
                      f"sha256 {str(batch.get('arms_sha256', '?'))[:16]}", f"profile_tag    {batch.get('profile_tag')}"]
    lines += [
        "",
        "EMULATION ASSERTION",
        "-" * 72,
        "Every run's debug-log RUN HEADER must read `emulation: speed=0 video=True`.",
    ]
    # ⭐ review R8: each violation under the heading of its OWN kind (an arm leak is not an emulation failure).
    _emu = [v for v in batch["header_violations"] if v.get("kind", "emulation") == "emulation"]
    _other = [v for v in batch["header_violations"] if v.get("kind", "emulation") != "emulation"]
    lines.append(f"headers checked: {batch['headers_checked']}   violations: {len(_emu)}")
    for v in _emu:
        lines.append(f"  !! {v['tag']}  {Path(v['log']).name}  {v['reason']}")
    if not _emu:
        lines.append("  all clean.")
    if batch.get("arms") or _other:
        lines += ["", "A/B INTEGRITY (arm headers, the monitor, the freeze watch)", "-" * 72,
                  f"violations: {len(_other)}   lanes lost: {batch.get('lanes_lost') or 'none'}   "
                  f"stop: {batch.get('stop_reason', '?')}"]
        for v in _other:
            lines.append(f"  !! [{v.get('kind')}] {v['tag']}  {Path(v['log']).name if v.get('log') else ''}  {v['reason']}")
        if not _other:
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
    arms = summary.get("arms")
    return {
        "stamp": stamp,
        "commit": summary.get("code_commit", "?"),
        # ⭐ an A/B batch says so: its pooled runs/rate mix arms, and must never be read as one sample.
        "lanes": f"{summary.get('lanes', '?')} ({'/'.join(arms)})" if arms else summary.get("lanes", "?"),
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
def ensure_lane_profile(slot: int, tag: str | None = None, name: str | None = None) -> Path:
    """Create/refresh a headless lane profile without importing the bot.

    ‼ `story.yml` is REWRITTEN on every batch launch, exactly as `modules/endless_x4.py`
    does it and for the same reason: these are bot-managed profiles whose whole purpose
    is "H2 is always the Mudkip lane", and a stale hand-edit turning H2 into a second
    Torchic would silently corrupt the starter coverage the batch exists to provide.
    ⭐ `tag` / `name` (design v2 step 14 T1): the profile family, and the in-game player name (`lane_name`, paired
    across arms); both default to today's behaviour.
    """
    character_name = name or lane_tag(slot)
    name = lane_profile_name(slot, tag)
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
        f"character_name: {character_name}\n"
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
    # --- design v2 step 14 T1: per-lane ARMS (all None / empty without `--arms`) -------------------
    arm: str | None = None
    arm_env: dict | None = None
    name: str | None = None
    #: debug-log path -> ('ok'|'bad'|'unknown', reason) for the env-all/build check.
    arm_headers: dict[str, tuple[str, str]] = field(default_factory=dict)
    #: one record per spawn: start / end (epoch s), exit code, commit.
    spawns: list[dict] = field(default_factory=list)
    first_spawn: float | None = None
    #: the monitor's incremental read position per log, and the partial last line (bytes) not yet scanned.
    log_offsets: dict[str, int] = field(default_factory=dict)
    log_partial: dict[str, bytes] = field(default_factory=dict)
    #: watched substring -> seconds after `first_spawn` it was first seen.
    first_seen: dict[str, float] = field(default_factory=dict)
    alive_at_deadline: bool | None = None
    #: alive when the batch stopped for ANY reason (a park, an abort, the deadline) — review R2.
    alive_at_stop: bool | None = None
    cut_log: str | None = None

    @property
    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None


def git_commit(scope: list[str] | None = None) -> str:
    """The short HEAD, `-dirty` if the working tree has changes. ⭐ `scope` (an `--arms` batch): only changes under
    those paths count as dirty. The main checkout ALWAYS carries two volatile tool files, so the unscoped check called
    every batch unattributable; the full porcelain is recorded in `ARMS.json` regardless."""
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, timeout=15).stdout.strip()
        cmd = ["git", "status", "--porcelain"] + (["--untracked-files=all", "--"] + scope if scope else [])
        dirty = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=15).stdout.strip()
        return f"{rev}{'-dirty' if dirty else ''}" if rev else "unknown"
    except Exception:
        return "unknown"


def freeze_snapshot(scope: list[str]) -> tuple[str, str] | None:
    """(HEAD's full hash, `git status --porcelain --untracked-files=all -- <scope>`), or None if git failed."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True,
                              timeout=30)
        por = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--"] + scope, cwd=REPO_ROOT,
                             capture_output=True, text=True, timeout=60)
        if head.returncode != 0 or por.returncode != 0 or not head.stdout.strip():
            return None
        return head.stdout.strip(), por.stdout
    except Exception:
        return None


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


def lane_env(lane: "Lane | None" = None) -> dict:
    """The lane process's environment. Without an arm: the launching shell's, as always. ⭐ With an arm (design v2
    step 14 T1): the shell's MINUS every `POKEBOT_*` and D6 variable, PLUS the arm's literal dict — so a variable left in
    the shell can no longer turn both arms on."""
    armed = lane is not None and lane.arm_env is not None
    env = strip_inherited(dict(os.environ))[0] if armed else dict(os.environ)
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
    if armed:
        env.update(lane.arm_env)
        # ⛔ FAULT ARM `X4H_FAULT_ENVLEAK=1` (T1-3; never set in a real run; `29`): a leaked variable the strip missed,
        # on the FIRST lane only. The live header check must abort the batch on that lane's first run.
        if os.environ.get("X4H_FAULT_ENVLEAK") == "1" and lane.slot == 0:
            env["POKEBOT_X4H_LEAK"] = "1"
    return env


def spawn(lane: Lane, runs_per_lane: int, scope: list[str] | None = None) -> None:
    stdout_path = lane.out_dir / "stdout.txt"
    lane.fh = open(stdout_path, "a", encoding="utf-8", errors="replace")
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    lane.proc = subprocess.Popen(
        lane_command(lane, runs_per_lane),
        cwd=str(BUILD_ROOT),
        env=lane_env(lane),
        stdout=lane.fh,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=creation_flags,
    )
    # ⭐ PROVENANCE PER SPAWN, not per batch. A respawned lane loads the CURRENT on-disk code, so
    # this is the only moment the truth is available. Printed as well as stored, because the reader
    # who needs it most is someone scanning stdout after a surprising result.
    _spawn_commit = git_commit(scope)
    lane.build_commits.append(_spawn_commit)
    now = time.time()
    if lane.first_spawn is None:
        lane.first_spawn = now
    in_job = _JOB.assign(lane.proc) if _JOB is not None else False
    lane.spawns.append({"start": round(now, 1), "end": None, "exit": None, "commit": _spawn_commit,
                        "pid": lane.proc.pid, "in_job": in_job})
    print(f"[x4h] {lane.tag} ({lane.starter}{', arm ' + lane.arm if lane.arm else ''}) started — pid {lane.proc.pid}, "
          f"profile `{lane.profile}`, build {_spawn_commit}", flush=True)


def check_headers(lane: Lane, since: float, on_bad: str, expect_build: str | None = None) -> list[dict]:
    """Assert `speed=0 video=True` on every NEW debug log this lane has produced.

    Checked continuously for the whole batch — not once at the start — because the
    failure being guarded against is "run 1 was unthrottled and run 2 crawled at 1x".
    ⭐ With an arm (design v2 step 14 T1(b)): every header's `env-all:` must also EQUAL the lane's arm and its `build:`
    the batch's commit. Those violations carry `kind: "arm"` and abort whatever `--on-bad-header` says.
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
        emu_done = lane.headers.get(key, ("unknown", ""))[0] in ("ok", "bad")
        arm_done = lane.arm_env is None or lane.arm_headers.get(key, ("unknown", ""))[0] in ("ok", "bad")
        if emu_done and arm_done:
            continue
        try:
            with log.open("r", encoding="utf-8", errors="replace") as fh:
                head = fh.read(8192)
        except OSError:
            continue
        if not emu_done:
            verdict, reason = header_verdict(parse_run_header(head))
            lane.headers[key] = (verdict, reason)
            if verdict == "bad":
                print(f"\n{'!' * 72}\n[x4h] EMULATION ASSERTION FAILED — {lane.tag} — {log.name}\n"
                      f"       {reason}\n{'!' * 72}\n", flush=True)
                violations.append({"tag": lane.tag, "log": key, "reason": reason, "kind": "emulation"})
            elif verdict == "ok":
                print(f"[x4h] {lane.tag} header OK ({reason}) — {log.name}", flush=True)
        if not arm_done:
            averdict, areason = arm_header_verdict(head, lane.arm_env, expect_build)
            lane.arm_headers[key] = (averdict, areason)
            if averdict == "bad":
                print(f"\n{'!' * 72}\n[x4h] ARM HEADER ASSERTION FAILED — {lane.tag} (arm {lane.arm}) — {log.name}\n"
                      f"       {areason}\n{'!' * 72}\n", flush=True)
                violations.append({"tag": lane.tag, "log": key, "reason": areason, "kind": "arm"})
            elif averdict == "ok":
                print(f"[x4h] {lane.tag} arm {lane.arm} header OK — {log.name}", flush=True)
    return violations


def monitor_lane(lane: Lane, since: float, cfg: dict, now: float, require_active: bool = True) -> list[dict]:
    """design v2 step 14 T1(g): read each of this lane's logs INCREMENTALLY (whole lines only) and apply the arm's
    `monitor` config. Returns violations: `leak` for a `forbid` hit, `vacuity` for a `require` substring not seen by its
    deadline (seconds after the lane's first spawn). First-seen times of `require` and `expect` substrings are recorded on
    the lane. ⛔ NEVER RAISES: a monitor fault must not kill a 13-hour batch; it is reported once instead."""
    violations: list[dict] = []
    forbid = cfg.get("forbid", [])
    require = cfg.get("require", {})
    watch = set(require) | set(cfg.get("expect", []))
    log_dir = lane.profile_dir / "debug-logs"
    try:
        logs = sorted(log_dir.glob("*.log")) if log_dir.exists() else []
    except OSError:
        logs = []
    for log in logs:
        key = str(log)
        try:
            if log.stat().st_mtime < since - 5:
                continue
            with log.open("rb") as fh:
                fh.seek(lane.log_offsets.get(key, 0))
                chunk = fh.read()
        except OSError:
            continue
        if not chunk:
            continue
        lane.log_offsets[key] = lane.log_offsets.get(key, 0) + len(chunk)
        data = lane.log_partial.pop(key, b"") + chunk
        complete, _, rest = data.rpartition(b"\n")
        if rest:
            lane.log_partial[key] = rest
        if not complete and not _:
            continue
        lines = complete.decode("utf-8", errors="replace").split("\n")
        hits, seen = scan_lines(lines, forbid, watch)
        for entry, line in hits:
            violations.append({"tag": lane.tag, "log": key, "kind": "leak",
                               "reason": f"arm {lane.arm} printed a forbidden {entry!r}: {line.strip()[:200]}"})
        for sub in seen:
            if sub not in lane.first_seen and lane.first_spawn is not None:
                lane.first_seen[sub] = round(now - lane.first_spawn, 1)
    if require_active and lane.first_spawn is not None:
        for sub, secs in require.items():
            if sub not in lane.first_seen and now - lane.first_spawn >= secs:
                violations.append({"tag": lane.tag, "log": "", "kind": "vacuity",
                                   "reason": f"arm {lane.arm} has not printed {sub!r} within {secs} s of its first "
                                             f"spawn — the arm's flags are not reaching the code"})
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
    # ⭐ design v2 step 14 T1: an A/B batch shows each lane's arm (from the start manifest, written before any spawn).
    arm_of = {}
    try:
        _arms = json.loads((batch_dir / "ARMS.json").read_text(encoding="utf-8"))
        arm_of = {f"L{ln['slot'] + 1:02d}": ln["arm"] for ln in _arms.get("lanes", [])}
        print(f"\n  A/B batch: arms {'/'.join(_arms.get('arm_names', []))}, tag {_arms.get('profile_tag')}")
    except (OSError, ValueError, KeyError, TypeError):
        pass
    print(f"\n  {'lane':<6} {'arm':<4} {'runs':>5} {'fin':>4} {'rate':>6}  last activity")
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
        print(f"  {d.name:<6} {arm_of.get(d.name, '-'):<4} {runs:>5} {fin:>4} {rate:>6}  {tail}")
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
                    "debug_logs_collected",
                    # ⭐ design v2 step 14 T1: run facts, not parse results — re-parsing must never lose them.
                    "arm", "name", "spawns", "alive_at_deadline", "cut_log", "monitor", "arm_headers_checked",
                    "alive_at_stop", "arm_headers_unknown", "arm_header_verdict"):
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
    # ⭐ design v2 step 14 T1 (`ai-research-notes/2026-10-01-batch14-DESIGN.md` §3; `…-T1-PREDICTIONS.md`).
    ap.add_argument("--arms", default=None, metavar="FILE",
                    help="a per-lane A/B: a JSON file of arms (each a literal, complete set of POKEBOT_* variables) "
                         "and an optional live monitor. Lanes are split into contiguous blocks, one per arm; each lane "
                         "gets ONLY its arm's POKEBOT_* variables. Needs --profile-tag and --build sandbox.")
    ap.add_argument("--profile-tag", default=None, metavar="TAG",
                    help="put the lanes in a FRESH profile family endless-TAG-H{n}-<starter>; refuses an existing one")
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

    # ⭐ design v2 step 14 T1: every refusal happens HERE, before a directory is made or a lane is spawned.
    tag = args.profile_tag
    errors, arms_spec, arms_text = arms_preflight(args.arms, tag, args.lanes, BUILD_NAME, BUILD_ROOT, PROFILES)
    if errors:
        print("[x4h] FATAL: refused before any lane started:", flush=True)
        for e in errors:
            print(f"[x4h]   - {e}", flush=True)
        return 2
    arm_names = list(arms_spec["arms"]) if arms_spec else []
    scope = [BUILD_ROOT.name, "tools/story-dev/x4_headless.py"] if arms_spec else None

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_root = Path(args.out) if args.out else RUNS_ROOT / stamp
    out_root.mkdir(parents=True, exist_ok=True)
    # ⭐ T1(e): the console is ALSO written to the batch dir, so a lane death or an abort is on disk, not only on a
    # console window that may be closed.
    tee = _Tee(out_root / "x4h.txt")
    sys.stdout = tee
    try:
        return _run_batch(args, stamp, out_root, tag, arms_spec, arms_text, arm_names, scope)
    finally:
        sys.stdout = tee.console
        tee.close()


class _Tee:
    """stdout to the console AND a file (T1(e)). Never raises from `write`: a full disk must not kill the batch."""

    def __init__(self, path: Path):
        self.console = sys.stdout
        try:
            self.fh = open(path, "a", encoding="utf-8", errors="replace")
        except OSError:
            self.fh = None

    def write(self, s):
        # ⛔ BOTH halves guarded (review R6): a dead console must not turn a print inside the loop's `except` into a
        # second exception that skips summary.json.
        try:
            self.console.write(s)
        except (OSError, ValueError):
            pass
        if self.fh is not None:
            try:
                self.fh.write(s)
            except OSError:
                pass
        return len(s)

    def flush(self):
        try:
            self.console.flush()
        except (OSError, ValueError):
            pass
        if self.fh is not None:
            try:
                self.fh.flush()
            except OSError:
                pass

    def close(self):
        if self.fh is not None:
            try:
                self.fh.close()
            except OSError:
                pass


class _KillOnCloseJob:
    """design v2 step 14 T1 (review R4): a Windows Job Object with KILL_ON_JOB_CLOSE. Every lane is assigned to it, so
    the lanes die WITH x4h however x4h dies — a closed console, an external kill, a killed parent task — instead of
    running unbounded with no summary. ⛔ Best effort and never fatal: off Windows, or if any call fails, it reports once
    and the batch runs as before (the try/finally still stops the lanes on every exit x4h itself sees)."""

    def __init__(self):
        self.handle = None
        self.note = "not Windows"
        if os.name != "nt":
            return
        try:
            import ctypes
            from ctypes import wintypes

            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.CreateJobObjectW.restype = wintypes.HANDLE
            k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
            k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

            class _BASIC(ctypes.Structure):
                _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                            ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                            ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                            ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                            ("SchedulingClass", wintypes.DWORD)]

            class _IO(ctypes.Structure):
                _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount",
                                                            "OtherOperationCount", "ReadTransferCount",
                                                            "WriteTransferCount", "OtherTransferCount")]

            class _EXT(ctypes.Structure):
                _fields_ = [("BasicLimitInformation", _BASIC), ("IoInfo", _IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                            ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                            ("PeakJobMemoryUsed", ctypes.c_size_t)]

            handle = k32.CreateJobObjectW(None, None)
            if not handle:
                self.note = f"CreateJobObject failed ({ctypes.get_last_error()})"
                return
            info = _EXT()
            info.BasicLimitInformation.LimitFlags = 0x2000          # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not k32.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):  # Extended (9)
                self.note = f"SetInformationJobObject failed ({ctypes.get_last_error()})"
                return
            self._k32, self.handle, self.note = k32, handle, "kill-on-close job active"
        except Exception as exc:  # noqa: BLE001 - best effort, reported
            self.note = f"job object unavailable: {type(exc).__name__}: {exc}"

    def assign(self, proc) -> bool:
        """Put a REAL Popen in the job (a stand-in without a Windows handle is skipped). False when not assigned."""
        h = getattr(proc, "_handle", None)
        if self.handle is None or h is None:
            return False
        try:
            return bool(self._k32.AssignProcessToJobObject(self.handle, int(h)))
        except Exception:  # noqa: BLE001 - best effort
            return False


#: The batch's job (set by `_run_batch`; None outside a batch). `spawn` assigns each new lane to it.
_JOB: "_KillOnCloseJob | None" = None


def _sha256_files(paths) -> dict:
    out = {}
    for p in paths:
        try:
            out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            out[p.name] = "unreadable"
    return out


def _newest_log(lane: Lane, since: float) -> str | None:
    try:
        logs = [p for p in (lane.profile_dir / "debug-logs").glob("*.log") if p.stat().st_mtime >= since - 5]
    except OSError:
        return None
    return max(logs, key=lambda p: p.stat().st_mtime).name if logs else None


def _run_batch(args, stamp, out_root, tag, arms_spec, arms_text, arm_names, scope) -> int:
    commit = git_commit(scope)
    started = datetime.now()
    since = time.time()

    print(f"[x4h] batch {stamp} — {args.lanes} lane(s), "
          f"runs/lane={args.runs or 'infinite'}, minutes={args.minutes or 'unbounded'}, "
          f"code={commit}, build={BUILD_NAME} ({BUILD_ROOT.name})", flush=True)
    print(f"[x4h] output: {out_root}", flush=True)
    if commit.endswith("-dirty"):
        print("[x4h] ‼ WORKING TREE IS DIRTY — this batch cannot be attributed to a commit.",
              flush=True)

    # ⭐ design v2 step 14 T1(f): the freeze snapshot is taken BEFORE any lane profile exists, so a refusal here leaves
    # nothing behind under the tag.
    freeze_start = None
    if arms_spec is not None:
        freeze_start = freeze_snapshot(scope)
        if freeze_start is None:
            # ⛔ Without the start snapshot neither the build check nor the freeze watch can work: refuse to start.
            print("[x4h] FATAL: git could not snapshot HEAD and the code's status; an A/B cannot be frozen.", flush=True)
            return 2
        if freeze_start[1].strip():
            # ⛔ review R5: porcelain shows STATUS, not content, so the watch could not see a dirty file being edited
            # AGAIN mid-batch. An A/B starts from committed code or not at all.
            print(f"[x4h] FATAL: the frozen code is not clean at the start — commit or remove these first:\n"
                  f"{freeze_start[1]}", flush=True)
            return 2

    lanes: list[Lane] = []
    for slot in range(args.lanes):
        arm = arm_of_slot(slot, args.lanes, arm_names) if arm_names else None
        name = lane_name(slot, args.lanes, len(arm_names)) if arm_names else None
        prof_dir = ensure_lane_profile(slot, tag, name)
        if args.wipe_saves:
            for fname in ("current_save.sav", "current_state.ss1"):
                f = prof_dir / fname
                if f.exists():
                    f.unlink()
        out_dir = out_root / f"L{slot + 1:02d}"
        out_dir.mkdir(exist_ok=True)
        lanes.append(Lane(slot=slot, tag=lane_tag(slot), starter=lane_starter(slot),
                          profile=lane_profile_name(slot, tag), profile_dir=prof_dir,
                          out_dir=out_dir, arm=arm, name=name,
                          arm_env=dict(arms_spec["arms"][arm]) if arm else None))

    header_violations: list[dict] = []
    aborted = ""
    deadline = since + args.minutes * 60 if args.minutes > 0 else None
    monitor_cfg = (arms_spec or {}).get("monitor") or {}
    expect_build = None
    freeze_unknown = 0
    lanes_lost: list[str] = []
    stop_reason = ""
    if arms_spec is not None:
        expect_build = freeze_start[0][:12]
        stripped = strip_inherited(dict(os.environ))[1]
        until = (datetime.fromtimestamp(since + args.minutes * 60).strftime("%Y-%m-%d %I:%M %p")
                 if args.minutes > 0 else "the batch ends")
        try:
            porcelain_full = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True,
                                            text=True, timeout=60).stdout
        except Exception as exc:  # noqa: BLE001 - recorded, never fatal: the scoped snapshot above is the guard
            porcelain_full = f"(git status failed: {exc})"
        # ⭐ T1(d): the START manifest, written BEFORE any lane spawns — the batch dir has a lane→arm record from its
        # first second, and an abort or a crash cannot lose it.
        start_manifest = {
            "stamp": stamp, "started": started.isoformat(timespec="seconds"), "code_commit": commit,
            "head": freeze_start[0], "build": BUILD_NAME, "build_root": str(BUILD_ROOT),
            "profile_tag": tag, "minutes": args.minutes, "runs_per_lane": args.runs, "lanes_n": args.lanes,
            "arms_file": str(Path(args.arms).resolve()), "arms_sha256": hashlib.sha256(arms_text.encode("utf-8")).hexdigest(),
            "arms_text": arms_text, "arm_names": arm_names,
            "lanes": [{"tag": ln.tag, "slot": ln.slot, "arm": ln.arm, "starter": ln.starter, "name": ln.name,
                       "profile": ln.profile} for ln in lanes],
            "stripped_inherited": stripped,
            "config_sha256": _sha256_files(sorted(PROFILES.glob("*.yml")) + [PROFILES / "customcatchfilters.py"]),
            "porcelain_full": porcelain_full, "freeze_scope": scope, "freeze_start": list(freeze_start),
            "fault_envleak": os.environ.get("X4H_FAULT_ENVLEAK") == "1",
            "do_not_touch_until": until,
        }
        (out_root / "ARMS.json").write_text(json.dumps(start_manifest, indent=2), encoding="utf-8")
        print(f"[x4h] A/B batch: arms {'/'.join(arm_names)} — "
              + ", ".join(f"{ln.tag}={ln.arm}" for ln in lanes), flush=True)
        if stripped:
            print(f"[x4h] stripped from every lane (inherited from this shell): {stripped}", flush=True)
        # ⛔ review R3: ANY commit, pull or merge in this checkout changes HEAD, and the freeze watch then (correctly)
        # aborts the whole batch. Said loudly, once, where the operator is looking.
        print(f"\n{'#' * 78}\n# DO NOT COMMIT, PULL OR MERGE IN {REPO_ROOT}\n# until {until}: the freeze watch aborts "
              f"this A/B if HEAD or the code moves.\n# Commit docs on a WORKTREE branch instead.\n{'#' * 78}\n", flush=True)

    # ⭐ review R4: a kill-on-close job, so the lanes cannot outlive x4h however x4h dies.
    global _JOB
    _JOB = _KillOnCloseJob()
    print(f"[x4h] lane job object: {_JOB.note}", flush=True)
    # ⭐ review R12: spawn the arms INTERLEAVED (slot 0, N/K, 1, N/K+1, …) so no arm gets a head start every time.
    if arm_names:
        per = args.lanes // len(arm_names)
        spawn_order = sorted(lanes, key=lambda ln: (ln.slot % per, ln.slot // per))
    else:
        spawn_order = list(lanes)

    last_freeze = time.time()
    try:
        for i, lane in enumerate(spawn_order):
            spawn(lane, args.runs, scope)
            if i < len(spawn_order) - 1 and args.stagger > 0:
                time.sleep(args.stagger)

        while True:
            time.sleep(5)
            now = time.time()

            for lane in lanes:
                header_violations.extend(check_headers(lane, since, args.on_bad_header, expect_build))

            # ⛔ An ARM violation aborts whatever --on-bad-header says: a contaminated A/B is void, not "noisy".
            if any(v.get("kind") == "arm" for v in header_violations):
                aborted = "ARM HEADER ASSERTION FAILED"
                break
            if header_violations and args.on_bad_header == "abort":
                aborted = "EMULATION ASSERTION FAILED"
                break

            # ⭐ T1(g): the live monitor (STOP-1 leaks, STOP-2 vacuity), every tick.
            mon_violations = []
            for lane in lanes:
                cfg = monitor_cfg.get(lane.arm) if lane.arm else None
                if not cfg:
                    continue
                try:
                    # ⛔ review R1: `require` only for a LIVE lane. A dead lane is not "flags not reaching the code"; it
                    # is a lost lane, recorded below.
                    mon_violations.extend(monitor_lane(lane, since, cfg, now, require_active=lane.alive))
                except Exception as exc:  # noqa: BLE001 - a monitor bug must not kill the batch; it is reported
                    print(f"[x4h] ‼ monitor error on {lane.tag}: {type(exc).__name__}: {exc}", flush=True)
            if mon_violations:
                for v in mon_violations:
                    print(f"\n{'!' * 72}\n[x4h] {v['kind'].upper()} — {v['tag']} — {Path(v['log']).name if v['log'] else ''}"
                          f"\n       {v['reason']}\n{'!' * 72}\n", flush=True)
                header_violations.extend(mon_violations)
                aborted = "ARM LEAK" if any(v["kind"] == "leak" for v in mon_violations) else "VACUITY"
                break

            # ⭐ T1(f): the freeze watch, every 60 s.
            if freeze_start is not None and now - last_freeze >= 60:
                last_freeze = now
                fv = freeze_verdict(freeze_start, freeze_snapshot(scope))
                if fv == "broken":
                    aborted = "FREEZE BROKEN"
                    print(f"\n{'!' * 72}\n[x4h] FREEZE BROKEN — HEAD or the code under {scope} changed mid-batch; the "
                          f"lanes may be running different code.\n{'!' * 72}\n", flush=True)
                    header_violations.append({"tag": "-", "log": "", "kind": "freeze",
                                              "reason": "HEAD or the scoped porcelain changed"})
                    break
                if fv == "unknown":
                    freeze_unknown += 1
                    print(f"[x4h] ‼ freeze watch: git did not answer ({freeze_unknown}x); not counted as broken.",
                          flush=True)

            for lane in lanes:
                if lane.alive:
                    continue
                if lane.spawns and lane.spawns[-1]["end"] is None:
                    lane.spawns[-1]["end"] = round(now, 1)
                    lane.spawns[-1]["exit"] = lane.proc.returncode if lane.proc is not None else None
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
                    if not (deadline is not None and now >= deadline):
                        # ⭐ review R1: a lane gone for good is a DEGRADED batch, said in the verdict and the summary.
                        lanes_lost.append(f"{lane.tag} (arm {lane.arm or '-'}) after {len(lane.spawns)} spawn(s)")
                    continue
                lane.restarts += 1
                print(f"[x4h] ‼ {lane.tag} died (exit {code}); restart "
                      f"{lane.restarts}/{args.max_restarts}.", flush=True)
                spawn(lane, args.runs, scope)

            if all(not l.alive and l.proc is None for l in lanes):
                stop_reason = "all lanes stopped"
                print("[x4h] all lanes have stopped.", flush=True)
                break
            if deadline is not None and now >= deadline:
                # ⭐ T1(e): which runs the deadline CUT — recorded before anything is stopped.
                for lane in lanes:
                    lane.alive_at_deadline = lane.alive
                    lane.cut_log = _newest_log(lane, since) if lane.alive else None
                stop_reason = "deadline"
                print(f"[x4h] time bound reached ({args.minutes} min) — stopping lanes.", flush=True)
                break
    except KeyboardInterrupt:
        aborted = "interrupted by user (Ctrl-C)"
        print("\n[x4h] interrupted — stopping lanes and summarising what we have.", flush=True)
    except Exception as exc:  # noqa: BLE001 - T1(e): an x4h bug must never leave 16 lanes running unbounded
        aborted = f"x4h error: {type(exc).__name__}: {exc}"
        print(f"\n[x4h] ‼ UNEXPECTED ERROR — stopping every lane.\n{traceback.format_exc()}", flush=True)
    finally:
        stop_reason = stop_reason or aborted or "stopped"
        stop_t = round(time.time(), 1)
        for lane in lanes:
            # ⭐ review R2: the CUT runs are recorded for EVERY exit (a park, an abort), not only the deadline, and a
            # spawn x4h ends is marked, so its exit code is never read as a crash.
            try:
                lane.alive_at_stop = lane.alive
                if lane.alive:
                    lane.cut_log = lane.cut_log or _newest_log(lane, since)
                    if lane.spawns and lane.spawns[-1]["end"] is None:
                        lane.spawns[-1]["end"] = stop_t
                        lane.spawns[-1]["stopped_by"] = "x4h"
            except Exception:  # noqa: BLE001 - recording must never prevent the stop below
                pass
            stop_lane(lane)
            if lane.spawns and lane.spawns[-1]["exit"] is None and lane.proc is not None:
                lane.spawns[-1]["exit"] = lane.proc.returncode
    # ⭐ review R10: a PROVISIONAL summary from the Lane records alone (no log parsing), so an interrupted copy of
    # 13 hours of logs cannot leave the batch without a summary.json.
    _provisional = {"stamp": stamp, "provisional": True, "stop_reason": stop_reason,
                    "verdict": "FAILED — " + aborted if aborted else "OK (provisional)", "lanes_lost": lanes_lost,
                    "header_violations": header_violations, "arms": arm_names or None,
                    "lanes": {ln.tag: {"arm": ln.arm, "alive_at_stop": ln.alive_at_stop, "cut_log": ln.cut_log,
                                       "spawns": ln.spawns, "first_seen": ln.first_seen} for ln in lanes}}
    try:
        (out_root / "summary.json").write_text(json.dumps(_provisional, indent=2), encoding="utf-8")
    except OSError:
        pass
    # Give the OS a moment to flush the line-buffered debug logs before they are read.
    time.sleep(2)

    lanes_detail: dict[str, dict] = {}
    lane_rows = []
    collect_interrupted = False
    for lane in lanes:
        try:
            stdout_text = (lane.out_dir / "stdout.txt").read_text(encoding="utf-8", errors="replace")
        except OSError:
            stdout_text = ""
        n_logs, debug_text = 0, ""
        if args.collect == "full" and not collect_interrupted:
            # ⭐ review R10: a second Ctrl-C during the copy must not cost the summary; the logs stay in the profiles.
            try:
                n_logs = collect_logs(lane, since)
                for f in sorted((lane.out_dir / "debug-logs").glob("*.log")) if n_logs else []:
                    try:
                        debug_text += f.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        pass
            except KeyboardInterrupt:
                collect_interrupted = True
                print("\n[x4h] ‼ log collection interrupted — summarising without the remaining logs (they are still "
                      "in each lane's profile debug-logs/).", flush=True)
        s = lane_summary(lane, stdout_text, debug_text, n_logs)
        lanes_detail[lane.tag] = s
        lane_rows.append({
            "tag": lane.tag, "starter": lane.starter, "profile": lane.profile,
            "runs_ended": s["runs_ended"], "finished": s["finished"],
            "header_verdict": s["header_verdict"], "restarts": lane.restarts,
            # ‼ carried here too so `resummarise()`'s `row` fallback can find it.
            "build_commits": list(lane.build_commits),
            "arm": lane.arm,
            "arm_header_verdict": s.get("arm_header_verdict"),
        })

    ended = datetime.now()
    total_runs = sum(s["runs_ended"] for s in lanes_detail.values())
    total_fin = sum(s["finished"] for s in lanes_detail.values())
    verdict = "FAILED — " + aborted if aborted else "OK"
    if not aborted and lanes_lost:
        verdict = f"OK — DEGRADED: lanes lost: {'; '.join(lanes_lost)}"
    batch = {
        "stamp": stamp,
        "code_commit": commit,
        # ⛔ PROVENANCE, NOT DECORATION (added 2026-09-09). `render_manifest` has always printed
        # `batch.get("build", "?")` while this dict never set the key, so EVERY manifest ever
        # produced read `build ?` — and a batch whose fork is unknown cannot be compared, which is
        # exactly what this file's own docstring says the manifest exists to prevent. The resolved
        # ROOT is recorded beside the name so a reader never has to infer the fork from log content.
        "build": BUILD_NAME,
        "build_root": str(BUILD_ROOT),
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
    if arms_spec is not None:
        # ⭐ design v2 step 14 T1: what makes the A/B's numbers attributable. `ARMS.json` holds the same, from the start.
        batch.update({
            "arms": arm_names,
            "arms_file": str(Path(args.arms).resolve()),
            "arms_sha256": hashlib.sha256(arms_text.encode("utf-8")).hexdigest(),
            "profile_tag": tag,
            "freeze_start": list(freeze_start) if freeze_start else None,
            "freeze_unknown_checks": freeze_unknown,
            "violation_kinds": dict(Counter(v.get("kind", "emulation") for v in header_violations)),
            "lanes_lost": lanes_lost,
            "stop_reason": stop_reason,
            "collect_interrupted": collect_interrupted,
            "job_object": _JOB.note if _JOB is not None else None,
        })
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
        kinds = dict(Counter(v.get("kind", "emulation") for v in header_violations))
        print(f"[x4h] ‼ {len(header_violations)} VIOLATION(S) {kinds} — this batch is NOT a clean measurement.",
              flush=True)
        return 3
    return 1 if aborted else 0


if __name__ == "__main__":
    sys.exit(main())
