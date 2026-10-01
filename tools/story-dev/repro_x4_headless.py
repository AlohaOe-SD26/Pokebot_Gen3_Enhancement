"""Repro/regression for `x4_headless.py` and the `--endless-target` headless fix.

NO EMULATOR NEEDED — every check below is pure logic or static analysis, so this runs in
the standard repro sweep. (`repro_x4_lanes.py` is the one that spawns real lane processes
and is skipped by design; this is not that.)

WHAT IT PROVES
--------------
A. Lane identity — the starter split is the DASHBOARD's at 4 lanes and 2-per-starter at 8,
   and the table has not drifted from `modules/endless_x4.py`.
B. The launch line is the GUI lane's line with `-hl` in place of the tile plumbing.
C. The RUN HEADER assertion accepts `speed=0 video=True` and REJECTS every degraded
   variant — and distinguishes "not written yet" from "written, and it does not say".
D. Outcome classification starts PESSIMISTIC (only the literal `finished` is a finish).
E. ‼ FAULT-INJECTED A/B for the `--endless-target` fix: the SAME checker is run against
   the pre-fix source (recovered from git) and the current source, and the verdict flips
   from "only honoured by the tile frontend" to "honoured by every frontend".
"""

from __future__ import annotations

import ast
import re
import subprocess
import dataclasses
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SANDBOX = REPO_ROOT / "sandbox-pokebot"

sys.path.insert(0, str(HERE))

import x4_headless as x4  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}{('  — ' + detail) if detail else ''}")
        FAILURES.append(label)


# ---------------------------------------------------------------------------
print("A. lane identity")
# ---------------------------------------------------------------------------
four = [x4.lane_starter(i) for i in range(4)]
check("4 lanes == the dashboard's split", four == ["torchic", "mudkip", "treecko", "random"], str(four))

eight = [x4.lane_starter(i) for i in range(8)]
counts = {s: eight.count(s) for s in set(eight)}
check("8 lanes == 2 per starter + 2 random",
      counts == {"torchic": 2, "mudkip": 2, "treecko": 2, "random": 2}, str(counts))
# WHY this matters: `#24-starter-gym3` (Treecko stalls at Wattson in 11 of 14 runs, Mudkip
# never does) is starter-specific. One lane per starter is too thin to separate that from
# noise; doubling the per-starter sample is the entire reason 8 lanes exist.
check("8 lanes double every starter's sample vs 4",
      all(counts[s] == 2 * four.count(s) for s in counts))

check("tags are H1..HN (namespaced away from the GUI's P1..P4)",
      [x4.lane_tag(i) for i in range(4)] == ["H1", "H2", "H3", "H4"])
check("profiles never collide with the GUI's endless-P* lanes",
      all(not x4.lane_profile_name(i).startswith("endless-P") for i in range(8)))

# ‼ The starter table is DUPLICATED from modules/endless_x4.py (importing it would drag in
# modules.profiles/roms/tile_bridge). Duplication is only safe if drift is impossible, so
# assert equality here rather than trusting a comment.
src = (SANDBOX / "modules" / "endless_x4.py").read_text(encoding="utf-8")
m = re.search(r"LANE_STARTERS:\s*tuple\[str, \.\.\.\]\s*=\s*\(([^)]*)\)", src)
check("LANE_STARTERS found in modules/endless_x4.py", m is not None)
if m:
    upstream = tuple(s.strip().strip('"\'') for s in m.group(1).split(",") if s.strip())
    check("starter table has NOT drifted from modules/endless_x4.py",
          upstream == x4.LANE_STARTERS, f"{upstream} vs {x4.LANE_STARTERS}")


# ---------------------------------------------------------------------------
print("B. launch line")
# ---------------------------------------------------------------------------
lane = x4.Lane(slot=0, tag="H1", starter="torchic", profile="endless-H1-torchic",
               profile_dir=Path("."), out_dir=Path("."))
cmd = x4.lane_command(lane, 0)
joined = " ".join(cmd)
check("mode is Story (ENDLESS RESET)", "Story (ENDLESS RESET)" in cmd)
check("unthrottled (-s 0)", "-s" in cmd and cmd[cmd.index("-s") + 1] == "0")
check("audio off (-na)", "-na" in cmd)
check("headless (-hl)", "-hl" in cmd)
check("endless target passed through", "--endless-target" in cmd
      and cmd[cmd.index("--endless-target") + 1] == "0")
check("runs-per-lane is honoured", x4.lane_command(lane, 5)[-1] == "5")
# ‼ -nv would turn the RENDERER off. Headless already removes the WINDOW; the renderer is
# load-bearing (the faithful PokeNav Match-Call path only advances with video on).
check("never passes -nv (the renderer must stay ON)", "-nv" not in cmd and "--no-video" not in joined)
# The tile plumbing selects the tile frontend; passing it would defeat -hl.
check("no --tile-* plumbing (GUI-only)", "--tile-" not in joined)

env = x4.lane_env()
check("COLUMNS pinned wide (rich wraps a file at ~78 cols and splits the lines we parse)",
      int(env.get("COLUMNS", "0")) >= 200, env.get("COLUMNS"))
check("stdout unbuffered", env.get("PYTHONUNBUFFERED") == "1")
check("UTF-8 forced", env.get("PYTHONUTF8") == "1")


# ---------------------------------------------------------------------------
print("C. RUN HEADER assertion (the anti-'silently at 1x' guard)")
# ---------------------------------------------------------------------------
GOOD = (
    "=== DEBUG LOG START ===\n"
    "--- RUN HEADER (build, config, experiment) ---\n"
    "    build:         3109cfa7 on branch main\n"
    "    emulation:     speed=0 video=True audio=False\n"
    "--- END RUN HEADER ---\n"
)
check("accepts speed=0 video=True", x4.header_verdict(x4.parse_run_header(GOOD))[0] == "ok")

for bad, why in (
    ("speed=1 video=True", "throttled to 1x — ~20x slower, looks exactly like a hang"),
    ("speed=0 video=False", "renderer off — the faithful PokeNav path degrades silently"),
    ("speed=2 video=False", "both wrong"),
):
    text = GOOD.replace("speed=0 video=True", bad)
    verdict, reason = x4.header_verdict(x4.parse_run_header(text))
    check(f"REJECTS `{bad}` ({why})", verdict == "bad", reason)

# ‼ "not written yet" must NOT read as a pass — a watcher has to retry, not conclude.
partial = GOOD.split("--- END RUN HEADER ---")[0]
check("incomplete header -> unknown, not ok", x4.header_verdict(x4.parse_run_header(partial))[0] == "unknown")
# ...and neither must "the header exists but says nothing about emulation" (a
# debug_logger change would land here). Silent passes are how a broken batch looks clean.
noemu = GOOD.replace("    emulation:     speed=0 video=True audio=False\n", "")
check("complete header with no emulation line -> unknown, not ok",
      x4.header_verdict(x4.parse_run_header(noemu))[0] == "unknown")

# The real emitter's format, verified against modules/debug_logger.py rather than assumed.
dbg = (SANDBOX / "modules" / "debug_logger.py").read_text(encoding="utf-8")
check("debug_logger still emits `emulation: speed=… video=…`",
      'f"speed={context.emulation_speed} video={context.video} "' in dbg)
check("debug_logger still closes the header with the sentinel we key on",
      '"--- END RUN HEADER ---"' in dbg)


# ---------------------------------------------------------------------------
print("D. outcome classification (start pessimistic)")
# ---------------------------------------------------------------------------
check("`finished` is a finish", x4.classify_outcome("finished") == "finished")
# ‼ 16 dead runs once read as wins because `outcome` defaulted to "finished" and a derail
# that called set_manual_mode() returned normally. Anything that is not the bare literal
# must NOT count.
check("`stopped: handed to Manual mid-run` is NOT a finish",
      x4.classify_outcome("stopped: handed to Manual mid-run (see the run's log for why)") == "stopped")
check("`derailed: …` is a derail", x4.classify_outcome("derailed: boss: 6 losses") == "derailed")
check("`frame-cap (…)` is its own bucket", x4.classify_outcome("frame-cap (5,100,000 > 5,000,000)") == "frame_cap")
check("`crashed: …` is a crash", x4.classify_outcome("crashed: ValueError: x") == "crashed")

STDOUT = (
    "=== ENDLESS RESET: starting run 1/infinite ===\n"
    "=== ENDLESS RESET: run 1/infinite -> finished (3,058,007 frames) ===\n"
    "=== ENDLESS RESET: starting run 2/infinite ===\n"
    "lost a battle at map (8, 1)\n"
    "recovered from the whiteout\n"
    "=== ENDLESS RESET: run 2/infinite -> derailed: Norman: 6 losses, no super-effective "
    "answer to Normal, need Fighting (412,004 frames) ===\n"
    "=== ENDLESS RESET: starting run 3/infinite ===\n"
    "=== ENDLESS RESET: run 3/infinite -> derailed: Norman: 8 losses, no super-effective "
    "answer to Normal, need Fighting (500,111 frames) ===\n"
)
DEBUG = (
    "[FAINT-CHOOSER] GAVE UP after 900 frames without sending a mon out\n"
    "outcome=BattleOutcome.Won\noutcome=BattleOutcome.Won\noutcome=BattleOutcome.RanAway\n"
    "Story: global watchdog — nothing progressed for 18,000 frames\n"
    "===== DUMP [STUCK — 111000 frames no progress] =====\n"
    "battle: active=True  instr=BattleScript_FaintedMonTryChoose\n"
)
s = x4.summarize_lane(STDOUT, DEBUG)
check("counts runs started/ended", (s["runs_started"], s["runs_ended"]) == (3, 3), str(s))
check("finish rate is 1/3", s["finished"] == 1 and s["finish_rate"] == 0.333, str(s["finish_rate"]))
# ‼ THE measurement this runner exists for: the two Norman derails differ only in the loss
# count, so raw strings would scatter them. They must group into ONE cause.
check("derail reasons group across differing numbers", len(s["end_reasons"]) == 1, str(s["end_reasons"]))
check("the grouped reason names the counter chain",
      "no super-effective answer to Normal" in next(iter(s["end_reasons"])), str(s["end_reasons"]))
check("KI-38 canary counted", s["faint_chooser_gave_up"] == 1)
check("KI-38's discriminator counted too (0 means a valid target always existed)",
      s["no_eligible_replacement"] == 0)
check("KI-40 watchdog canary counted", s["global_watchdog"] == 1)
check("STUCK dumps counted", s["stuck_dumps"] == 1)
check("the wedge's battle script is named",
      s["stuck_battle_scripts"].get("BattleScript_FaintedMonTryChoose") == 1)
check("whiteouts/losses counted", (s["whiteouts"], s["losses"]) == (1, 1))
check("battle outcome tally + flee rate", s["battles"] == 3 and s["flee_rate"] == 0.333)

# ‼ THE WRAPPING TRAP — this check used to assert the OPPOSITE, and that was a bug pinned
# as a feature. It read "a rich-wrapped outcome line is genuinely unparseable (hence
# COLUMNS=400)", i.e. it encoded the WORKAROUND as the intended behaviour. Then batch
# `20260731-105549` ran with COLUMNS=400 and the counter-chain derail messages are ~1,000
# characters — they wrapped anyway, the `(N frames) ===` tail landed on the next line, and
# the batch reported a **69% finish rate against a true 23.7%** with the dominant end reason
# (the counter chain, 25 of 29 non-finishes) appearing ZERO times. Width is a mitigation;
# any width can be exceeded. The PARSER must tolerate wrapping, and that is what is asserted
# now.
wrapped = STDOUT.replace("-> derailed: Norman: 6 losses, no super-effective ",
                         "-> derailed: Norman: 6 losses, no super-effective \n")
w = x4.summarize_lane(wrapped, "")
check("a rich-wrapped outcome line is STILL parsed (width is a mitigation, not the fix)",
      w["runs_ended"] == s["runs_ended"], f"{w['runs_ended']} vs {s['runs_ended']}")
check("...and the wrapped reason still groups with its unwrapped twin",
      len(w["end_reasons"]) == 1, str(w["end_reasons"]))
# Real shape from the batch: the tail lands on its own line after a ~400-char body.
split_tail = STDOUT.replace(" (412,004 frames) ===", "\n (412,004 frames) ===")
check("a record split immediately before the frame tail is parsed",
      x4.summarize_lane(split_tail, "")["runs_ended"] == s["runs_ended"])
# ...but a truncated record must NOT swallow the following one (the bound on the gap).
truncated = "=== ENDLESS RESET: run 9/infinite -> derailed: died mid-print\n" + STDOUT
check("a truncated record does not consume the next run's outcome",
      x4.summarize_lane(truncated, "")["runs_ended"] == s["runs_ended"],
      str(x4.summarize_lane(truncated, "")["runs_ended"]))

# ‼ CROSS-LANE AGGREGATION. The batch totals used
# `Counter({k: v for lane in lanes for k, v in lane.items()})` — an inner dict
# comprehension, so a reason appearing in several lanes had every lane but the LAST
# silently overwritten. It reported 9 end reasons for 29 non-finishing runs, and only the
# arithmetic not adding up exposed it: the numbers looked entirely plausible.
lanes = {
    "H1": {"end_reasons": {"norman needs Fighting": 6, "watchdog": 1}},
    "H2": {"end_reasons": {"norman needs Fighting": 9}},
    "H3": {"end_reasons": {"winona needs Rock": 5}},
}
merged = x4._merge_end_reasons(lanes)
check("a reason shared by several lanes SUMS rather than overwrites",
      merged["norman needs Fighting"] == 15, str(dict(merged)))
check("lane-unique reasons survive the merge",
      merged["winona needs Rock"] == 5 and merged["watchdog"] == 1, str(dict(merged)))
check("the merged total equals the sum of every lane's counts",
      sum(merged.values()) == 21, str(sum(merged.values())))


# ---------------------------------------------------------------------------
print("E. --endless-target: fault-injected A/B against the pre-fix source")
# ---------------------------------------------------------------------------
def endless_target_is_universal(source: str) -> tuple[bool, str]:
    """Is ENDLESS_RESET_TARGET applied for EVERY frontend, or only under `tile_shm`?

    Structural, on purpose: the alternative is booting an emulator per frontend. It
    answers exactly one question — is every assignment of that name nested inside a
    conditional on `tile_shm`?
    """
    tree = ast.parse(source)

    def guarded_by_tile_shm(node: ast.AST, stack: list[ast.AST]) -> bool:
        for parent in stack:
            if isinstance(parent, ast.If) and "tile_shm" in ast.unparse(parent.test):
                return True
        return False

    found, guarded = 0, 0

    def walk(node: ast.AST, stack: list[ast.AST]) -> None:
        nonlocal found, guarded
        for child in ast.iter_child_nodes(node):
            hit = (
                (isinstance(child, ast.Assign)
                 and any(isinstance(t, ast.Attribute) and t.attr == "ENDLESS_RESET_TARGET"
                         for t in child.targets))
                or (isinstance(child, ast.Expr) and isinstance(child.value, ast.Call)
                    and "apply_endless_target" in ast.unparse(child.value.func))
            )
            if hit:
                found += 1
                if guarded_by_tile_shm(child, stack + [node]):
                    guarded += 1
            walk(child, stack + [node])

    walk(tree, [])
    if found == 0:
        return False, "no application of --endless-target at all"
    if guarded == found:
        return False, f"all {found} application(s) are inside an `if …tile_shm…` branch"
    return True, f"{found - guarded} of {found} application(s) reachable by every frontend"


pokebot_py = SANDBOX / "pokebot.py"
after_ok, after_why = endless_target_is_universal(pokebot_py.read_text(encoding="utf-8"))

before_src = ""
try:
    before_src = subprocess.run(
        ["git", "show", "HEAD:sandbox-pokebot/pokebot.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30).stdout
except Exception:
    pass

if before_src.strip():
    before_ok, before_why = endless_target_is_universal(before_src)
    # ‼ THE A/B. Once this fix is committed, HEAD becomes the FIXED source and the "before"
    # arm legitimately passes — so assert the flip only while HEAD is still pre-fix, and
    # never let that turn into a silent skip of the arm that matters.
    if before_ok:
        print(f"  note  HEAD already contains the fix ({before_why}) — A/B arm not applicable")
    else:
        check(f"BEFORE (HEAD): bug present — {before_why}", not before_ok)
        check("AFTER (working tree): bug fixed — " + after_why, after_ok)
else:
    print("  note  could not read HEAD:sandbox-pokebot/pokebot.py — A/B arm skipped")

check("AFTER: --endless-target reaches every frontend — " + after_why, after_ok)

# And the extracted helper really does what the name says, without an emulator.
# ‼ The FUNCTION is lifted out and exec'd on its own rather than importing pokebot.py:
# importing it registers an `atexit` handler that calls `input()`, which turns a repro
# into a process that blocks (or EOFs noisily) at exit. Lift, stub, call.
import types  # noqa: E402

_fn_src = None
for _node in ast.parse(pokebot_py.read_text(encoding="utf-8")).body:
    if isinstance(_node, ast.FunctionDef) and _node.name == "apply_endless_target":
        _fn_src = ast.unparse(_node)
check("apply_endless_target exists at module level in pokebot.py", _fn_src is not None)

if _fn_src:
    stub = types.ModuleType("plugins.custom_modes.story_mode")
    stub.ENDLESS_RESET_TARGET = 10
    pkg = types.ModuleType("plugins.custom_modes")
    pkg.story_mode = stub
    plugins_pkg = types.ModuleType("plugins")
    plugins_pkg.custom_modes = pkg
    saved = {k: sys.modules.get(k) for k in
             ("plugins", "plugins.custom_modes", "plugins.custom_modes.story_mode")}
    sys.modules["plugins"] = plugins_pkg
    sys.modules["plugins.custom_modes"] = pkg
    sys.modules["plugins.custom_modes.story_mode"] = stub
    try:
        ns: dict = {}
        exec(compile(_fn_src, "pokebot.py:apply_endless_target", "exec"), ns)
        fn = ns["apply_endless_target"]
        check("apply_endless_target(None) leaves the default alone",
              fn(None) is False and stub.ENDLESS_RESET_TARGET == 10)
        check("apply_endless_target(0) sets 'run forever'",
              fn(0) is True and stub.ENDLESS_RESET_TARGET == 0)
        check("apply_endless_target(5) sets a bounded batch",
              fn(5) is True and stub.ENDLESS_RESET_TARGET == 5)
    except Exception as e:  # noqa: BLE001
        check("apply_endless_target is callable in isolation", False, f"{type(e).__name__}: {e}")
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


# ---------------------------------------------------------------------------
print("F. reporting")
# ---------------------------------------------------------------------------
batch = {
    "stamp": "20260731-120000", "code_commit": "abc1234", "lanes": 8,
    "runs_per_lane": 0, "minutes": 180.0, "started": "2026-07-31T12:00:00",
    "ended": "2026-07-31T15:00:00", "wall_minutes": 180.0, "verdict": "OK",
    "headers_checked": 24, "header_violations": [],
    "lane_rows": [{"tag": "H1", "starter": "torchic", "profile": "endless-H1-torchic",
                   "runs_ended": 3, "finished": 1, "header_verdict": "ok", "restarts": 0}],
    "lanes_detail": {"H1": {"runs_ended": 3, "finished": 1, "global_watchdog": 2,
                            "faint_chooser_gave_up": 5}},
}
man = x4.render_manifest(batch)
# The commit is the one fact a review cannot proceed without: two bundles in this project
# were analysed in depth against code that was never running.
check("MANIFEST records the commit", "abc1234" in man)
check("MANIFEST records the emulation assertion result", "EMULATION ASSERTION" in man and "24" in man)
check("MANIFEST records lanes + starters", "H1" in man and "torchic" in man)

# --- the BUILD selector (added 2026-09-07 with `--build`) --------------------------------------
# ⛔ A batch's numbers are unattributable without the fork that produced them. `--build` defaults to
# `custom` DELIBERATELY: custom is the fork that holds still while the sandbox is edited, so a batch
# measures the PROMOTED PRODUCT and cannot be poisoned mid-run by development work.
check("both forks are selectable", set(x4.BUILD_ROOTS) == {"sandbox", "custom"})
check("the default build is `custom` (the fork that holds still)", x4.BUILD_NAME == "custom")
check("BUILD_ROOT resolves under the repo root",
      x4.BUILD_ROOT.name in ("custom-pokebot", "sandbox-pokebot"))
# ‼ `.get`-based so an OLDER batch dict (no `build` key) still renders — a reporting function must
# never crash on historical data.
check("MANIFEST renders a build line for an OLD batch dict without a build key", "build" in man)
batch_with_build = dict(batch)
batch_with_build["build"] = "custom"
check("MANIFEST records the build when present",
      "custom" in x4.render_manifest(batch_with_build))

# --- the --status counter (added 2026-09-07) ---------------------------------------------------
# ⛔⛔ THIS EXISTS BECAUSE THE FIRST `--status` COUNTED THE LITERAL STRING "FINISHED" AND REPORTED
# 0% FOR A BATCH RECORDED AT 36%. The fix was to reuse `summarize_lane`; this check keeps it reused.
# ⭐ A CONTROL, not a tautology: the fixture's finish count is known from its own text, so a
# regression to any hand-rolled heuristic goes RED.
_stdout_fixture = "\n".join([
    # ⛔ COPIED FROM A REAL BATCH (`x4-runs/20260826-185918/L0*/stdout.txt`), not composed from
    # memory — the first version of this fixture invented a plausible format that `_RUN_END_RE`
    # matched zero times, and the checks silently measured nothing.
    "=== ENDLESS RESET: run 1/infinite -> finished (1,234,567 frames) ===",
    "=== ENDLESS RESET: run 2/infinite -> derailed: Story: too many whiteout recoveries in a row"
    " — stopping so I do not burn the budget (2,000,000 frames) ===",
    "=== ENDLESS RESET: run 3/infinite -> finished (999,999 frames) ===",
    # ⛔ THE ONE THAT MATTERS: a run handed to Manual must NOT count as a finish.
    # `classify_outcome`'s docstring records the cost of getting this wrong — 16 dead runs read as
    # wins and a summary claimed ~80% against a true ~20%.
    "=== ENDLESS RESET: run 4/infinite -> stopped: handed to Manual mid-run (500,000 frames) ===",
])
_s = x4.summarize_lane(_stdout_fixture, "")
check("--status counts runs via summarize_lane (4 runs seen)", _s["runs_ended"] == 4,
      f"got {_s['runs_ended']}")
check("--status counts ONLY literal `finished` (2 of 4, Manual hand-off excluded)",
      _s["finished"] == 2, f"got {_s['finished']}")
check("--status does NOT count a Manual hand-off as a finish", _s["stopped"] == 1,
      f"stopped={_s['stopped']}")
check("--status derives a finish RATE, not a raw count", _s["finish_rate"] == round(2 / 4, 3),
      f"got {_s['finish_rate']}")
check("--status surfaces WHY runs ended (the number that drives the next item)",
      bool(_s.get("end_reasons")), f"got {_s.get('end_reasons')}")

row = x4.index_row("20260731-120000", dict(batch, verdict="OK"))
idx = x4.render_index([row])
check("INDEX row carries the commit", "abc1234" in idx)
check("INDEX row carries the finish rate", "33%" in idx, idx)
check("INDEX row carries the KI-38/KI-40 canaries", "| 2 | 5 |" in idx, idx)

# --- #24-lane-respawn-build: a MIXED-BUILD batch must announce itself ------------------------
# ⭐ WHY THIS IS GATED. `code_commit` is captured ONCE at batch start, but a lane that dies is
# RESPAWNED and the new process imports whatever is on disk THEN — so an edit or a promotion
# mid-batch can put TWO BUILDS in one measurement while the MANIFEST still names one commit.
# ‼ FAULT-TESTED IN BOTH DIRECTIONS on purpose: the detector must FIRE on a mixed batch AND stay
# SILENT on a clean one. A warning that cannot fire is decoration; one that cries wolf on healthy
# batches teaches the reader to skip the MANIFEST, which is strictly worse than no warning.
# ⛔⛔ THESE DRIVE THE REAL PATH — a REAL `Lane` through the REAL `lane_summary()` — NOT a
# hand-typed `lanes_detail` dict. THAT DISTINCTION IS THE WHOLE POINT: this feature shipped once
# with `build_commits` recorded on the Lane and never copied into the summary, and SEVEN checks
# built on hand-typed fixtures all passed while the feature had never worked once. A fixture tests
# the FUNCTION; only the real assembly tests the WIRING. If a value must travel from an object into
# a report, the test has to make that JOURNEY.
def _detail(**lanes_to_commits):
    """Build `lanes_detail` the way `run_batch` does: real Lane -> real lane_summary()."""
    out = {}
    for tag, commits in lanes_to_commits.items():
        ln = x4.Lane(slot=0, tag=tag, starter="torchic", profile="p",
                     profile_dir=Path("."), out_dir=Path("."))
        ln.build_commits = list(commits)
        out[tag] = x4.lane_summary(ln, "", "", 0)
    return {"lanes_detail": out}


check("build provenance: the REAL assembly carries build_commits off the Lane",
      "build_commits" in x4.lane_summary(
          x4.Lane(slot=0, tag="L01", starter="t", profile="p",
                  profile_dir=Path("."), out_dir=Path(".")), "", "", 0))

_prov_none = "\n".join(x4.build_provenance_lines({}))
check("build provenance: an OLDER batch says 'not recorded', it does NOT cry wolf",
      "not recorded" in _prov_none and "MIXED" not in _prov_none, _prov_none)

_one = "\n".join(x4.build_provenance_lines(_detail(**{f"L0{i}": ["abc1234"] for i in range(1, 9)})))
check("build provenance: a SINGLE-build batch is quiet (real path)",
      "SINGLE BUILD" in _one and "MIXED" not in _one, _one)

# a lane that RESTARTED while the tree was unchanged records the same commit twice — still quiet.
_dup = _detail(L01=["abc1234"], L03=["abc1234", "abc1234"])
_prov_dup = "\n".join(x4.build_provenance_lines(_dup))
check("build provenance: a restart with an UNCHANGED tree stays quiet (real path)",
      "SINGLE BUILD" in _prov_dup and "MIXED" not in _prov_dup, _prov_dup)

_mix = _detail(L01=["abc1234"], L03=["abc1234", "def5678"])
_prov_mix = "\n".join(x4.build_provenance_lines(_mix))
check("build provenance: a MIXED batch FIRES (real path — the arm that was dead)",
      "MIXED BUILD" in _prov_mix, _prov_mix)
check("build provenance: the mixed report NAMES both commits",
      "abc1234" in _prov_mix and "def5678" in _prov_mix, _prov_mix)
check("build provenance: the mixed report NAMES the affected lane", "L03" in _prov_mix, _prov_mix)
check("build provenance: the mixed report REFUSES comparison, not merely notes it",
      "NOT a measurement" in _prov_mix, _prov_mix)

# ⛔ "UNVERIFIED" IS NOT "MIXED" — a git hiccup must not fire the loud claim.
_unk = "\n".join(x4.build_provenance_lines(_detail(L01=["unknown"], L03=["unknown"])))
check("build provenance: all-unknown reads UNVERIFIED, never MIXED",
      "UNVERIFIED" in _unk and "MIXED" not in _unk, _unk)
_unk_mixed = "\n".join(x4.build_provenance_lines(_detail(L01=["abc1234"], L03=["unknown"])))
check("build provenance: one unknown beside one real commit is a CAVEAT, not MIXED",
      "MIXED" not in _unk_mixed and "UNVERIFIED" in _unk_mixed, _unk_mixed)
_really = "\n".join(x4.build_provenance_lines(_detail(L01=["abc1234"], L03=["def5678", "unknown"])))
check("build provenance: two REAL commits still fire MIXED even with an unknown present",
      "MIXED BUILD" in _really, _really)

check("Lane records the build it loaded at EVERY spawn (not once per batch)",
      "build_commits" in {f.name for f in dataclasses.fields(x4.Lane)},
      str(sorted(f.name for f in dataclasses.fields(x4.Lane))))


# ---------------------------------------------------------------------------
print("F. per-lane ARMS (design v2 step 14 T1; ai-research-notes/2026-10-01-batch14-T1-PREDICTIONS.md)")
# ---------------------------------------------------------------------------
# ⛔ WHY: every lane used to inherit the launching shell's environment, so a concurrent A/B was impossible and a
# leftover flag silently turned BOTH arms on. These rows pin each refusal, the live header check (fail-closed), the
# monitor and the records. No row launches a lane: every refusal is driven through `arms_preflight` / pure helpers.
import json as _json  # noqa: E402
import os as _os  # noqa: E402
import tempfile as _tempfile  # noqa: E402

_ARMS_FILE = HERE / "arms" / "batch14.json"
_SPEC = _json.loads(_ARMS_FILE.read_text(encoding="utf-8"))
_SRC = x4.build_source_text(SANDBOX)
_COMMON = {"POKEBOT_R25_DMGAUDIT": "1", "POKEBOT_R25_WEAKEN": "observe", "POKEBOT_R25_WEAKEN_CALC": "1",
           "POKEBOT_MAINTAIN": "1", "POKEBOT_BOX_OVERFLOW_CATCH": "1"}
_PACKAGE = ("POKEBOT_R24_CATCHHURT", "POKEBOT_R24_CATCHTRAIN", "POKEBOT_R24_OVERSURVIVAL", "POKEBOT_R24_NOFAINTBAIL",
            "POKEBOT_R25_CAP", "POKEBOT_R25_RARE", "POKEBOT_R23_BALLRESTOCK", "POKEBOT_R27_KEYITEMS",
            "POKEBOT_R26_KITTOPOFF", "POKEBOT_R27_DOUBLEITEMS", "POKEBOT_R20_OPENFENCE")
_OFF_BOTH = ("POKEBOT_R20_TEAM6", "POKEBOT_R20_HUNTFIRST")
# The DESIGN's §1 table, written out: A = common + 13 at "0"; B = common + the package at "1" + the two at "0".
_WANT_A = {**_COMMON, **{k: "0" for k in _PACKAGE + _OFF_BOTH}}
_WANT_B = {**_COMMON, **{k: "1" for k in _PACKAGE}, **{k: "0" for k in _OFF_BOTH}}
check("F1 the committed arms file is the DESIGN §1 table, arm A exactly", _SPEC["arms"]["A"] == _WANT_A,
      str(set(_SPEC["arms"]["A"].items()) ^ set(_WANT_A.items())))
check("F1 the committed arms file is the DESIGN §1 table, arm B exactly", _SPEC["arms"]["B"] == _WANT_B,
      str(set(_SPEC["arms"]["B"].items()) ^ set(_WANT_B.items())))
check("F1 each arm has exactly 18 variables", len(_SPEC["arms"]["A"]) == len(_SPEC["arms"]["B"]) == 18)
check("F1 the committed arms file validates at 16 lanes (USER RULING 28) and at 8",
      x4.validate_arms(_SPEC, 16, _SRC) == [] and x4.validate_arms(_SPEC, 8, _SRC) == [],
      str(x4.validate_arms(_SPEC, 16, _SRC)))


def _refused(spec, n=16, needle="") -> bool:
    errs = x4.validate_arms(spec, n, _SRC)
    return bool(errs) and (not needle or any(needle in e for e in errs))


def _with(arm, key, value):
    s = _json.loads(_json.dumps(_SPEC))
    if value is None:
        s["arms"][arm].pop(key, None)
    else:
        s["arms"][arm][key] = value
    return s


_one = _json.loads(_json.dumps(_SPEC))
del _one["arms"]["B"]
_one["monitor"].pop("B")
check("F2 REFUSES a single arm (an A/B needs two)", _refused(_one, 16, "at least 2 arms"))
check("F2 REFUSES a non-string value", _refused(_with("B", "POKEBOT_R25_CAP", 1), 16, "must be a string"))
check("F2 REFUSES a key without the POKEBOT_ prefix", _refused(
    {**_SPEC, "arms": {"A": {**_SPEC["arms"]["A"], "TEACH_TRACE": "0"},
                       "B": {**_SPEC["arms"]["B"], "TEACH_TRACE": "0"}}}, 16, "not a POKEBOT_ variable"))
for _bad in ("POKEBOT_R24_FAULT_LIFTEARLY", "POKEBOT_PCPINGPONG_FAULT", "POKEBOT_KI80_ARM4",
             "POKEBOT_TEACHWINDOW_A", "POKEBOT_RNG_DECORRELATION_FRAMES"):
    _s = {**_SPEC, "arms": {"A": {**_SPEC["arms"]["A"], _bad: "1"}, "B": {**_SPEC["arms"]["B"], _bad: "1"}}}
    check(f"F2 REFUSES {_bad} (a fault arm, a §B switch or a determinism override)",
          _refused(_s, 16, "fault arm, a §B switch"))
_typo = {**_SPEC, "arms": {"A": {**_SPEC["arms"]["A"], "POKEBOT_R26_KITTOPOF": "0"},
                           "B": {**_SPEC["arms"]["B"], "POKEBOT_R26_KITTOPOF": "1"}}}
check("F2 REFUSES a key the build's source never mentions (a typo)", _refused(_typo, 16, "appears nowhere"))
check("F2 REFUSES arms with different variable sets", _refused(_with("B", "POKEBOT_R20_TEAM6", None), 16, "SAME variables"))
check("F2 REFUSES two identical arms (a vacuous A/B)",
      _refused({**_SPEC, "arms": {"A": dict(_SPEC["arms"]["A"]), "B": dict(_SPEC["arms"]["A"])}}, 16, "identical"))
check("F2 REFUSES a lane count that does not divide among the arms", _refused(_SPEC, 15, "divide evenly"))
check("F2 REFUSES a split whose arms get different starters (12 lanes = 6 per arm)",
      _refused(_SPEC, 12, "different starters"))
check("F2 REFUSES an unknown top-level key", _refused({**_SPEC, "arm": {}}, 16, "unknown top-level"))
check("F2 REFUSES a monitor for an arm that does not exist",
      _refused({**_SPEC, "monitor": {**_SPEC["monitor"], "C": {}}}, 16, "unknown arm"))
check("F2 REFUSES a non-positive require deadline",
      _refused({**_SPEC, "monitor": {**_SPEC["monitor"], "B": {**_SPEC["monitor"]["B"], "require": {" rare=": 0}}}},
               16, "positive seconds"))
check("F2 REFUSES an empty forbid entry",
      _refused({**_SPEC, "monitor": {**_SPEC["monitor"], "A": {"forbid": [[]]}}}, 16, "forbid entry"))

for _tag, _ok in (("s14", True), ("s14smoke", True), ("s14-fault_2", True), ("", False), ("P1", False),
                  ("p9", False), ("a/b", False), ("s 14", False), ("-x", False)):
    check(f"F3 --profile-tag {_tag!r} is {'accepted' if _ok else 'REFUSED'}", (x4.validate_tag(_tag) is None) == _ok,
          str(x4.validate_tag(_tag)))
check("F3 a tagged profile is a FRESH family, never the GUI's endless-P*",
      x4.lane_profile_name(0, "s14") == "endless-s14-H1-torchic" and x4.lane_profile_name(8, "s14") == "endless-s14-H9-torchic")
check("F3 an untagged profile name is unchanged (backward compatible)", x4.lane_profile_name(3) == "endless-H4-random")

_arms16 = [x4.arm_of_slot(s, 16, ["A", "B"]) for s in range(16)]
check("F4 arms take CONTIGUOUS blocks: H1-H8 = A, H9-H16 = B", _arms16 == ["A"] * 8 + ["B"] * 8, str(_arms16))
check("F4 within-arm position i has the SAME starter in both arms",
      all(x4.lane_starter(i) == x4.lane_starter(i + 8) for i in range(8)))
check("F4 each arm has two lanes of each starter", sorted(x4.lane_starter(s) for s in range(8)) ==
      sorted(x4.lane_starter(s) for s in range(8, 16)) == sorted(["torchic", "mudkip", "treecko", "random"] * 2))
_names = [x4.lane_name(s, 16, 2) for s in range(16)]
check("F4 the in-game name is PAIRED across arms (slot i and i+8 share one)", _names[:8] == _names[8:], str(_names))
check("F4 names are DISTINCT within an arm", len(set(_names[:8])) == 8, str(_names[:8]))

_env_in = {"PATH": "x", "COLUMNS": "80", "POKEBOT_R24_CATCHHURT": "1", "POKEBOT_HEAL_AT_FRACTION": "0.8", "TEACH_TRACE": "1",
           "TEACH_MISS_WINDOW": "1", "CAPTURE_FORCE": "1", "CH21_CAPTURE_WALLACE": "x", "SAVE_POST_RIVAL": "1",
           "STORY_TALK_DEBUG": "1", "KI15_TRACE": "1", "FW_TRACE": "1", "TEACH_CANCEL_FORGET": "1"}
_kept, _removed = x4.strip_inherited(_env_in)
check("F5 the strip removes every POKEBOT_* and every D6 variable", set(_kept) == {"PATH", "COLUMNS"}, str(_kept))
check("F5 the strip REPORTS what it removed, sorted", _removed == sorted(set(_env_in) - {"PATH", "COLUMNS"}),
      str(_removed))

# The D6 source scan: a literal non-POKEBOT name read from the environment by the build must be in the strip list.
_reads = set(re.findall(r"(?:environ\.get|environ\[|getenv)\(?\s*[\"']([A-Za-z0-9_]+)[\"']", _SRC))
_unprefixed = {n for n in _reads if not n.startswith("POKEBOT_")}
_uncovered = {n for n in _unprefixed if n not in x4.STRIP_UNPREFIXED
              and not any(n.startswith(p) for p in x4.STRIP_UNPREFIXED_PREFIXES)}
check("F5 every unprefixed env name the build reads is stripped (a NEW one turns this red)", not _uncovered,
      str(sorted(_uncovered)))
check("F5 the scan is not vacuous (it finds the known names)", {"TEACH_TRACE", "CAPTURE_FORCE"} <= _unprefixed,
      str(sorted(_unprefixed)))
_caps = set(re.findall(r"[\"'](CH21_CAPTURE_[A-Z_]+)[\"']", _SRC))
check("F5 the CH21_CAPTURE_* names read through a variable are covered by the prefix",
      bool(_caps) and all(any(c.startswith(p) for p in x4.STRIP_UNPREFIXED_PREFIXES) for c in _caps), str(_caps))

# lane_env: the real function, both shapes. The shell is given a leaked flag and a D6 variable.
_saved = {k: _os.environ.get(k) for k in ("POKEBOT_R27_KEYITEMS", "POKEBOT_HEAL_AT_FRACTION", "TEACH_TRACE",
                                          "X4H_FAULT_ENVLEAK")}
try:
    # The shell leaks the OTHER arm's value of an arm variable, and a real registered flag that is in no arm.
    _os.environ["POKEBOT_R27_KEYITEMS"] = "1"
    _os.environ["POKEBOT_HEAL_AT_FRACTION"] = "0.8"
    _os.environ["TEACH_TRACE"] = "1"
    _os.environ.pop("X4H_FAULT_ENVLEAK", None)
    _la = x4.Lane(slot=0, tag="H1", starter="torchic", profile="p", profile_dir=Path("."), out_dir=Path("."),
                  arm="A", arm_env=dict(_SPEC["arms"]["A"]))
    _e = x4.lane_env(_la)
    _pk = {k: v for k, v in _e.items() if k.startswith("POKEBOT_")}
    check("F6 an armed lane's POKEBOT_* set is EXACTLY its arm (the shell's leak is gone)", _pk == _SPEC["arms"]["A"],
          str(set(_pk) ^ set(_SPEC["arms"]["A"])))
    check("F6 the shell's KEYITEMS=1 is replaced by arm A's 0, and a flag in no arm is dropped",
          _e.get("POKEBOT_R27_KEYITEMS") == "0" and "POKEBOT_HEAL_AT_FRACTION" not in _e)
    check("F6 an armed lane drops the D6 variable", "TEACH_TRACE" not in _e)
    check("F6 an armed lane keeps the runner's own settings", _e.get("PYTHONUNBUFFERED") == "1"
          and _e.get("PYTHONUTF8") == "1" and int(_e.get("COLUMNS", "0")) >= 200)
    _plain = x4.lane_env()
    check("F6 WITHOUT an arm, lane_env is unchanged: the shell's variables pass through",
          _plain.get("POKEBOT_R27_KEYITEMS") == "1" and _plain.get("TEACH_TRACE") == "1")
    _os.environ["X4H_FAULT_ENVLEAK"] = "1"
    _lb = x4.Lane(slot=1, tag="H2", starter="mudkip", profile="p", profile_dir=Path("."), out_dir=Path("."),
                  arm="A", arm_env=dict(_SPEC["arms"]["A"]))
    check("F6 the fault arm X4H_FAULT_ENVLEAK leaks into slot 0 ONLY",
          x4.lane_env(_la).get("POKEBOT_X4H_LEAK") == "1" and "POKEBOT_X4H_LEAK" not in x4.lane_env(_lb))
finally:
    for _k, _v in _saved.items():
        if _v is None:
            _os.environ.pop(_k, None)
        else:
            _os.environ[_k] = _v

# The live header check. ⛔ The env-all line SHAPE is copied from a real run log (`evidence/2026-09-29-r24catchhurt-*`:
# `    env-all:       {'POKEBOT_R24_CATCHHURT': '1', 'POKEBOT_R24_FAULT_LIFTEARLY': '1'}`), not composed from memory.
_ENVA = dict(_SPEC["arms"]["A"])
_HDR = ("=== DEBUG LOG START ===\n--- RUN HEADER (build, config, experiment) ---\n"
        "    build:         21b420ce281c on branch main\n"
        "    emulation:     speed=0 video=True audio=False\n"
        f"    env-all:       {dict(sorted(_ENVA.items()))!r}\n"
        "--- END RUN HEADER ---\n")
_BUILD = "21b420ce281c0123456789abcdef0123456789ab"
check("F7 accepts a header whose env-all EQUALS the arm and whose build matches",
      x4.arm_header_verdict(_HDR, _ENVA, _BUILD)[0] == "ok", x4.arm_header_verdict(_HDR, _ENVA, _BUILD)[1])
_extra = _HDR.replace("{", "{'POKEBOT_X4H_LEAK': '1', ", 1)
check("F7 REJECTS an extra (leaked) variable, and names it",
      x4.arm_header_verdict(_extra, _ENVA, _BUILD)[0] == "bad" and "POKEBOT_X4H_LEAK" in x4.arm_header_verdict(
          _extra, _ENVA, _BUILD)[1])
_missing = _HDR.replace("'POKEBOT_R20_TEAM6': '0', ", "")
check("F7 REJECTS a missing variable", x4.arm_header_verdict(_missing, _ENVA, _BUILD)[0] == "bad")
_differ = _HDR.replace("'POKEBOT_R27_KEYITEMS': '0'", "'POKEBOT_R27_KEYITEMS': '1'")
check("F7 REJECTS a variable with the other arm's value", x4.arm_header_verdict(_differ, _ENVA, _BUILD)[0] == "bad")
_noline = "".join(l + "\n" for l in _HDR.splitlines() if "env-all" not in l)
check("F7 FAIL-CLOSED: a complete header with NO env-all line is BAD, never unknown",
      x4.arm_header_verdict(_noline, _ENVA, _BUILD)[0] == "bad")
_none = _HDR.replace(f"{dict(sorted(_ENVA.items()))!r}", "(no POKEBOT_* env vars set)")
check("F7 FAIL-CLOSED: env-all '(no POKEBOT_* env vars set)' is BAD", x4.arm_header_verdict(_none, _ENVA, _BUILD)[0] == "bad")
_junk = _HDR.replace(f"{dict(sorted(_ENVA.items()))!r}", "{'POKEBOT_R25_CAP': ")
check("F7 FAIL-CLOSED: an unparseable env-all is BAD", x4.arm_header_verdict(_junk, _ENVA, _BUILD)[0] == "bad")
check("F7 an INCOMPLETE header is unknown (retry), not bad and not ok",
      x4.arm_header_verdict(_HDR.split("--- END")[0], _ENVA, _BUILD)[0] == "unknown")
check("F7 REJECTS a run built from another commit",
      x4.arm_header_verdict(_HDR, _ENVA, "deadbeef0000" + "0" * 28)[0] == "bad")
_nobuild = _HDR.replace("    build:         21b420ce281c on branch main\n", "    build:         unknown\n")
check("F7 FAIL-CLOSED: no readable build line is BAD when a build is expected",
      x4.arm_header_verdict(_nobuild, _ENVA, _BUILD)[0] == "bad")

# The monitor's matching: plain substrings over WHOLE lines. ⛔ Line shapes from the emitters (review AI-4): three
# markers sit OUTSIDE the category slot.
check("F8 a substring is found anywhere on the line ([BALLS] [KIT-BUY] …)",
      x4.line_hit("f190801 [BALLS] [KIT-BUY] why=kit-none mart=RUSTBORO_CITY", "[KIT-BUY]"))
check("F8 [DEXCATCH-NOBAIL] is found inside [DEXCATCH] [DEXCATCH-NOBAIL] …",
      x4.line_hit("f5 [DEXCATCH] [DEXCATCH-NOBAIL] faint #1 — throwing on", "[DEXCATCH-NOBAIL]"))
check("F8 [DBLITEM] does NOT match the observe-only [DBLITEM-OBS]",
      not x4.line_hit("f9 [DBLITEM-OBS] would=use slot=2", "[DBLITEM]"))
_join = ["dex catch #", "(joins the party)"]
check("F8 a LIST entry needs every part on ONE line: the post-gym-1 party join hits",
      x4.line_hit("f9 [DEXFENCE] dex catch #263 (joins the party)", _join))
check("F8 a LIST entry does NOT hit the pre-gym-1 'team building (joins the party)' line",
      not x4.line_hit("f9 [DEXFENCE] pre-gym-1 team building (joins the party)", _join))
check("F8 a LIST entry does NOT hit a box catch", not x4.line_hit("f9 [DEXFENCE] dex catch #263 (goes to the PC box)", _join))
_h, _seen = x4.scan_lines(["a [KEYBATTLE] opp=1", "b plain", "c skip #255 rare=no tier="],
                          ["[KEYBATTLE]"], {" rare=", "[KEYBATTLE]", "never"})
check("F8 scan_lines reports each forbid hit with its line, and the watched substrings seen",
      _h == [("[KEYBATTLE]", "a [KEYBATTLE] opp=1")] and _seen == {" rare=", "[KEYBATTLE]"}, f"{_h} {_seen}")

# monitor_lane, on a real file written in pieces: a line split across two reads is matched ONCE, when it completes.
with _tempfile.TemporaryDirectory() as _td:
    _pd = Path(_td)
    (_pd / "debug-logs").mkdir()
    _log = _pd / "debug-logs" / "Story_(ENDLESS_RESET)-debug-20261001-200000.log"
    _lm = x4.Lane(slot=8, tag="H9", starter="torchic", profile="p", profile_dir=_pd, out_dir=_pd, arm="B",
                  arm_env={})
    _lm.first_spawn = 1000.0
    _cfg = {"forbid": ["party is not at full strength"], "require": {"[KEYBATTLE]": 60}, "expect": [" rare="]}
    _log.write_bytes(b"f1 [DEXFENCE] skip #255 Torchic - no Pok\xc3\xa9dex yet rare=no tier=\nf2 [DEXFENCE] skip #1 party is not at")
    _v1 = x4.monitor_lane(_lm, 0.0, _cfg, 1010.0)
    check("F9 a HALF-written line is not scanned yet (no false or early hit)", _v1 == [], str(_v1))
    check("F9 a complete line's watched substring is recorded with its time since first spawn",
          _lm.first_seen.get(" rare=") == 10.0, str(_lm.first_seen))
    with _log.open("ab") as _fh:
        _fh.write(b" full strength\nf3 ok\n")
    _v2 = x4.monitor_lane(_lm, 0.0, _cfg, 1020.0)
    check("F9 the split line is matched ONCE when it completes (a forbid hit -> leak)",
          [v["kind"] for v in _v2] == ["leak"], str(_v2))
    _v3 = x4.monitor_lane(_lm, 0.0, _cfg, 1030.0)
    check("F9 no new bytes, no repeated hit", _v3 == [], str(_v3))
    _v4 = x4.monitor_lane(_lm, 0.0, _cfg, 1059.0)
    check("F9 require is NOT vacuous before its deadline", _v4 == [], str(_v4))
    _v5 = x4.monitor_lane(_lm, 0.0, _cfg, 1061.0)
    check("F9 require FIRES at its deadline when never seen (vacuity)", [v["kind"] for v in _v5] == ["vacuity"], str(_v5))
    with _log.open("ab") as _fh:
        _fh.write(b"f4 [KEYBATTLE] opp=12 class=0x20 key=True allow=True reason=key_class\n")
    _v6 = x4.monitor_lane(_lm, 0.0, _cfg, 1070.0)
    check("F9 once seen, require stops firing", _v6 == [] and "[KEYBATTLE]" in _lm.first_seen, str(_v6))

    # check_headers end to end (the WIRING): a real file in a lane's debug-logs, an arm mismatch -> kind 'arm'.
    _lh = x4.Lane(slot=0, tag="H1", starter="torchic", profile="p", profile_dir=_pd, out_dir=_pd, arm="A",
                  arm_env=dict(_ENVA))
    _log2 = _pd / "debug-logs" / "Story_(ENDLESS_RESET)-debug-20261001-200500.log"
    _log2.write_text(_extra, encoding="utf-8")
    _vh = x4.check_headers(_lh, 0.0, "warn", _BUILD)
    check("F10 check_headers flags a leaked variable in a REAL log as kind 'arm' (the wiring)",
          any(v["kind"] == "arm" and "POKEBOT_X4H_LEAK" in v["reason"] for v in _vh), str(_vh))
    _lh2 = x4.Lane(slot=0, tag="H1", starter="torchic", profile="p", profile_dir=_pd, out_dir=_pd)
    check("F10 an UNARMED lane never gets an arm verdict (backward compatible)",
          not any(v.get("kind") == "arm" for v in x4.check_headers(_lh2, 0.0, "warn", _BUILD)))

    # arms_preflight: the refusals main() makes, driven without launching anything.
    _prof = _pd / "profiles"
    (_prof / "endless-s14-H3-treecko").mkdir(parents=True)
    _e1, _, _ = x4.arms_preflight(str(_ARMS_FILE), "s14", 16, "sandbox", SANDBOX, _prof)
    check("F11 preflight REFUSES a tag whose profiles already exist, naming them",
          any("already exist" in e and "endless-s14-H3-treecko" in e for e in _e1), str(_e1))
    # A MAIN checkout has a `.git` DIRECTORY; a worktree has a `.git` FILE. Both shapes are built here, so the rows hold
    # wherever the gate runs (review R9).
    _main_root = _pd / "mainroot"
    (_main_root / ".git").mkdir(parents=True)
    _wt_root = _pd / "wtroot"
    _wt_root.mkdir()
    (_wt_root / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    _e2, _s2, _ = x4.arms_preflight(str(_ARMS_FILE), "s14new", 16, "sandbox", SANDBOX, _prof, _main_root)
    check("F11 preflight ACCEPTS the committed file at 16 lanes under a fresh tag", _e2 == [] and _s2 is not None, str(_e2))
    _e2w, _, _ = x4.arms_preflight(str(_ARMS_FILE), "s14new", 16, "sandbox", SANDBOX, _prof, _wt_root)
    check("F11 preflight REFUSES an A/B launched from a git WORKTREE (its lane headers cannot name a commit)",
          any("MAIN checkout" in e for e in _e2w), str(_e2w))
    _e3, _, _ = x4.arms_preflight(str(_ARMS_FILE), "s14new", 16, "custom", SANDBOX, _prof)
    check("F11 preflight REFUSES --arms with --build custom", any("--build sandbox" in e for e in _e3), str(_e3))
    _e4, _, _ = x4.arms_preflight(str(_ARMS_FILE), None, 16, "sandbox", SANDBOX, _prof)
    check("F11 preflight REFUSES --arms without --profile-tag", any("--profile-tag" in e for e in _e4), str(_e4))
    _e5, _s5, _ = x4.arms_preflight(None, None, 4, "custom", SANDBOX, _prof)
    check("F11 preflight is a no-op for an ordinary batch (no arms, no tag)", _e5 == [] and _s5 is None, str(_e5))

    # resummarise keeps the RUN facts (a JOURNEY through the real function, on a real batch dir).
    _bd = _pd / "batch"
    (_bd / "L01").mkdir(parents=True)
    (_bd / "L01" / "stdout.txt").write_text("", encoding="utf-8")
    _row = {"tag": "H1", "starter": "torchic", "profile": "p", "runs_ended": 0, "finished": 0,
            "header_verdict": "ok", "restarts": 0, "arm": "A"}
    _old = {"stamp": "x", "code_commit": "abc1234", "lanes": 1, "runs_per_lane": 0, "minutes": 1,
            "started": "s", "verdict": "OK", "headers_checked": 1, "header_violations": [], "arms": ["A", "B"],
            "lane_rows": [_row], "lanes_detail": {"H1": {"arm": "A", "name": "H1", "alive_at_deadline": True,
                                                          "cut_log": "c.log", "spawns": [{"start": 1}],
                                                          "monitor": {"first_seen": {" rare=": 9.0}},
                                                          "arm_headers_checked": 3}}}
    (_bd / "summary.json").write_text(_json.dumps(_old), encoding="utf-8")
    import contextlib as _ctx
    import io as _io
    with _ctx.redirect_stdout(_io.StringIO()):
        x4.resummarise(_bd)
    _new = _json.loads((_bd / "summary.json").read_text(encoding="utf-8"))["lanes_detail"]["H1"]
    check("F12 --resummarise keeps the arm and the run facts (arm, cut log, first-seen, spawns, name, headers)",
          _new.get("arm") == "A" and _new.get("cut_log") == "c.log" and _new.get("alive_at_deadline") is True
          and _new.get("monitor", {}).get("first_seen") == {" rare=": 9.0} and _new.get("spawns") == [{"start": 1}]
          and _new.get("name") == "H1" and _new.get("arm_headers_checked") == 3,
          str({k: _new.get(k) for k in ("arm", "cut_log", "alive_at_deadline", "monitor", "spawns", "name",
                                         "arm_headers_checked")}))
    check("F12 the INDEX row marks an A/B batch, so its pooled rate is never read as one sample",
          "(A/B)" in str(x4.index_row("x", _json.loads((_bd / "summary.json").read_text(encoding="utf-8")))["lanes"]))

_lsum = x4.Lane(slot=8, tag="H9", starter="torchic", profile="p", profile_dir=Path("."), out_dir=Path("."),
                arm="B", name="H1")
_lsum.spawns.append({"start": 1.0, "end": 2.0, "exit": 1, "commit": "abc", "pid": 7})
_lsum.first_seen[" rare="] = 12.0
_lsum.alive_at_deadline, _lsum.cut_log = True, "cut.log"
_lsum.arm_headers = {"a.log": ("ok", ""), "b.log": ("unknown", "")}
_lsum.alive_at_stop = True
_ls = x4.lane_summary(_lsum, "", "", 0)
# ‼ `.get`, never subscripts: a dropped key must print a FAIL, not crash the gate and hide every later row (review MH-8).
check("F12 the REAL lane_summary carries the arm, name, spawns, deadline facts and first-seen off the Lane",
      _ls.get("arm") == "B" and _ls.get("name") == "H1" and (_ls.get("spawns") or [{}])[0].get("exit") == 1
      and _ls.get("cut_log") == "cut.log" and _ls.get("alive_at_deadline") is True and _ls.get("alive_at_stop") is True
      and (_ls.get("monitor") or {}).get("first_seen") == {" rare=": 12.0}, str(_ls.get("arm")))
check("F12 arm_headers_checked counts only SETTLED-ok headers; the unknown one is counted apart (review R7)",
      _ls.get("arm_headers_checked") == 1 and _ls.get("arm_headers_unknown") == 1, str(
          (_ls.get("arm_headers_checked"), _ls.get("arm_headers_unknown"))))
_man_ab = x4.render_manifest({**batch, "arms": ["A", "B"], "arms_file": "f.json", "arms_sha256": "0" * 64,
                              "profile_tag": "s14", "lane_rows": [{**batch["lane_rows"][0], "arm": "B"}]})
check("F12 the MANIFEST of an A/B names its arms, file, hash and tag, and each lane's arm",
      "ARMS           A/B" in _man_ab and "profile_tag    s14" in _man_ab and _man_ab.count("  B") >= 1, _man_ab[-400:])

check("F13 freeze: an unchanged snapshot is ok", x4.freeze_verdict(("h", "p"), ("h", "p")) == "ok")
check("F13 freeze: a new HEAD is BROKEN", x4.freeze_verdict(("h", "p"), ("h2", "p")) == "broken")
check("F13 freeze: a changed porcelain is BROKEN", x4.freeze_verdict(("h", ""), ("h", "?? sandbox-pokebot/x.py\n")) == "broken")
check("F13 freeze: a git failure is UNKNOWN, never broken (no false alarm on a 13-hour batch)",
      x4.freeze_verdict(("h", "p"), None) == "unknown" and x4.freeze_verdict(None, ("h", "p")) == "unknown")

# Structure: the batch loop cannot leave lanes running on an exception (T1(e)), and arm violations abort regardless of
# --on-bad-header. Static, because driving them needs real lanes; T1-3 drives the first one live.
_rb = ast.parse((HERE / "x4_headless.py").read_text(encoding="utf-8"))
_fn = next(n for n in ast.walk(_rb) if isinstance(n, ast.FunctionDef) and n.name == "_run_batch")
_tries = [n for n in ast.walk(_fn) if isinstance(n, ast.Try) and any(isinstance(m, ast.While) for m in ast.walk(n))]
check("F14 the batch loop sits in a try whose FINALLY stops every lane",
      any(any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "stop_lane" for f in t.finalbody for c in ast.walk(f))
          for t in _tries))
check("F14 the batch loop also catches Exception (an x4h bug ends the batch, it does not orphan the lanes)",
      any(any(isinstance(h.type, ast.Name) and h.type.id == "Exception" for h in t.handlers) for t in _tries))
_src_rb = ast.get_source_segment((HERE / "x4_headless.py").read_text(encoding="utf-8"), _fn)
check("F14 an ARM header violation aborts BEFORE (and independent of) the --on-bad-header test",
      _src_rb.find('v.get("kind") == "arm"') != -1
      and _src_rb.find('v.get("kind") == "arm"') < _src_rb.find('args.on_bad_header == "abort"'))
check("F14 the START manifest (ARMS.json) is written BEFORE the first spawn",
      -1 < _src_rb.find('"ARMS.json"') < _src_rb.find("spawn(lane, args.runs, scope)"))


# ---------------------------------------------------------------------------
print("G. T1's adversarial fold (evidence/2026-10-01-batch14-T1-ADVERSARIAL.txt): direct rows, then a DRIVEN _run_batch")
# ---------------------------------------------------------------------------
# ⛔ WHY: the mutant pass killed 103 of 155 mutants; 44 real gaps survived, almost all WIRING — F14 checked
# `_run_batch` by its source SHAPE and passed on broken behaviour. Section G closes them (the hunter's rows, adapted)
# and adds a row for each runtime fix the review asked for (R1-R12).
import contextlib as _gctx  # noqa: E402
import io as _gio  # noqa: E402
import subprocess as _greal  # noqa: E402
import types as _gtypes  # noqa: E402

_HEAD40 = "a" * 40
_BUILD12 = _HEAD40[:12]


def _ghdr(env, build=_BUILD12, body=""):
    return ("=== DEBUG LOG START ===\n--- RUN HEADER (build, config, experiment) ---\n"
            f"    build:         {build} on branch main\n"
            "    emulation:     speed=0 video=True audio=False\n"
            f"    env-all:       {dict(sorted(env.items()))!r}\n"
            "--- END RUN HEADER ---\n" + body)


def _grefused(spec, n=16, needle=""):
    try:
        errs = x4.validate_arms(spec, n, _SRC)
    except Exception:  # noqa: BLE001 - a crash is NOT a clean refusal
        return False
    return bool(errs) and (not needle or any(needle in e for e in errs))


def _gmon(arm, cfg):
    return {**_SPEC, "monitor": {**_SPEC["monitor"], arm: cfg}}


_h, _ = x4.scan_lines(["x [KIT-BUY] y"], ["[KEYBATTLE]", "[KIT-BUY]"], set())
check("G-D1 scan_lines tests EVERY forbid entry (a hit on the SECOND)", _h == [("[KIT-BUY]", "x [KIT-BUY] y")], str(_h))
for _raw in ("None", "['POKEBOT_R25_CAP']", "1"):
    _t = _ghdr(_ENVA).replace(repr(dict(sorted(_ENVA.items()))), _raw)
    check(f"G-D4 FAIL-CLOSED: env-all {_raw} (a literal, not a dict) is BAD",
          x4.arm_header_verdict(_t, _ENVA, _HEAD40)[0] == "bad", str(x4.arm_header_verdict(_t, _ENVA, _HEAD40)))
check("G-D5 a build differing only in its 12th digit is BAD",
      x4.arm_header_verdict(_ghdr(_ENVA, build="aaaaaaaaaaab"), _ENVA, _HEAD40)[0] == "bad")
check("G-D6 REFUSES a monitor key typo ('requires' would switch STOP-2 off)",
      _grefused(_gmon("B", {**_SPEC["monitor"]["B"], "requires": {"x": 5}}), 16, "only forbid"))
check("G-D7 REFUSES an EMPTY require substring (seen on every line: vacuity silently off)",
      _grefused(_gmon("B", {**_SPEC["monitor"]["B"], "require": {"": 60}}), 16, "require"))
check("G-D7 REFUSES a boolean require deadline",
      _grefused(_gmon("B", {**_SPEC["monitor"]["B"], "require": {" rare=": True}}), 16, "require"))
check("G-D8 REFUSES an empty-string forbid (it would match every line)", _grefused(_gmon("A", {"forbid": [""]}), 16, "forbid entry"))
check("G-D8 REFUSES an empty-string or non-list expect",
      _grefused(_gmon("A", {"expect": [""]}), 16, "expect") and _grefused(_gmon("A", {"expect": "abc"}), 16, "expect"))
check("G-D8 REFUSES a non-object monitor cleanly (no crash)", _grefused({**_SPEC, "monitor": []}, 16, "monitor"))
check("G-D9 REFUSES a non-object spec / arms cleanly (no crash)", _grefused([], 16) and _grefused({"arms": []}, 16))
check("G-D13 a legitimate key with _A mid-name (POKEBOT_HEAL_AT_FRACTION) is NOT refused as a §B switch",
      not any("fault arm" in e for e in x4.validate_arms(
          {**_SPEC, "arms": {"A": {**_SPEC["arms"]["A"], "POKEBOT_HEAL_AT_FRACTION": "0.5"},
                             "B": {**_SPEC["arms"]["B"], "POKEBOT_HEAL_AT_FRACTION": "0.5"}}}, 16, _SRC)))

with _tempfile.TemporaryDirectory() as _gtd:
    _gprof = Path(_gtd) / "profiles"
    _gprof.mkdir()
    _groot = Path(_gtd) / "root"
    (_groot / ".git").mkdir(parents=True)
    _e15, _s15, _ = x4.arms_preflight(str(_ARMS_FILE), "g14", 15, "sandbox", SANDBOX, _gprof, _groot)
    check("G-D10 preflight REFUSES the file at 15 lanes (validate_arms WIRED with the REAL lane count)",
          any("divide evenly" in e for e in _e15) and _s15 is None, str(_e15))
    _e12, _, _ = x4.arms_preflight(str(_ARMS_FILE), "g14", 12, "sandbox", SANDBOX, _gprof, _groot)
    check("G-D10 preflight REFUSES the file at 12 lanes (starter parity)", any("different starters" in e for e in _e12),
          str(_e12))
    _eP, _, _ = x4.arms_preflight(None, "P1", 4, "custom", SANDBOX, _gprof, _groot)
    _eP2, _, _ = x4.arms_preflight(str(_ARMS_FILE), "p9", 16, "sandbox", SANDBOX, _gprof, _groot)
    check("G-D11 preflight REFUSES a P-tag (validate_tag WIRED), with and without --arms",
          any("must not start with P" in e for e in _eP) and any("must not start with P" in e for e in _eP2))
    _sf = _os.environ.get("X4H_FAULT_ENVLEAK")
    try:
        _os.environ["X4H_FAULT_ENVLEAK"] = "1"
        _eF, _, _ = x4.arms_preflight(str(_ARMS_FILE), "s14", 16, "sandbox", SANDBOX, _gprof, _groot)
        _eF2, _, _ = x4.arms_preflight(str(_ARMS_FILE), "s14fault", 16, "sandbox", SANDBOX, _gprof, _groot)
    finally:
        if _sf is None:
            _os.environ.pop("X4H_FAULT_ENVLEAK", None)
        else:
            _os.environ["X4H_FAULT_ENVLEAK"] = _sf
    check("G-R11 a STALE X4H_FAULT_ENVLEAK refuses a real tag (it would abort the night ~90 s in)",
          any("X4H_FAULT_ENVLEAK" in e for e in _eF), str(_eF))
    check("G-R11 ... and is allowed only under a tag that says 'fault'", not any("X4H_FAULT_ENVLEAK" in e for e in _eF2),
          str(_eF2))

with _tempfile.TemporaryDirectory() as _gtd:
    _gpd = Path(_gtd)
    (_gpd / "debug-logs").mkdir()
    _gln = x4.Lane(slot=8, tag="H9", starter="torchic", profile="p", profile_dir=_gpd, out_dir=_gpd, arm="B", arm_env={})
    _gln.first_spawn = 1000.0
    _gcfg = {"forbid": ["party is not at full strength"], "require": {"[KEYBATTLE]": 60}, "expect": [" rare="]}
    _gl1 = _gpd / "debug-logs" / "Story_(ENDLESS_RESET)-debug-20261001-200000.log"
    _gl1.write_text("f1 x rare=no\n", encoding="utf-8")
    x4.monitor_lane(_gln, 0.0, _gcfg, 1010.0)
    with _gl1.open("a", encoding="utf-8") as _fh:
        _fh.write("f2 y rare=yes\n")
    x4.monitor_lane(_gln, 0.0, _gcfg, 1020.0)
    check("G-D2 first_seen keeps the FIRST sighting", _gln.first_seen.get(" rare=") == 10.0, str(_gln.first_seen))
    _gl2 = _gpd / "debug-logs" / "Story_(ENDLESS_RESET)-debug-20261001-210000.log"
    _gl2.write_text("g1 [DEXFENCE] skip #1 party is not at full strength\n", encoding="utf-8")
    _gv = x4.monitor_lane(_gln, 0.0, _gcfg, 1030.0)
    check("G-D3 a forbid hit in the lane's SECOND log (run 2) is a leak", [x["kind"] for x in _gv] == ["leak"], str(_gv))
    _gdead = x4.Lane(slot=9, tag="H10", starter="mudkip", profile="p", profile_dir=_gpd / "none", out_dir=_gpd, arm="B",
                     arm_env={})
    _gdead.first_spawn = 1000.0
    check("G-R1 require is NOT checked for a dead lane (a lost lane is not 'flags not reaching the code')",
          x4.monitor_lane(_gdead, 0.0, _gcfg, 5000.0, require_active=False) == [])

with _tempfile.TemporaryDirectory() as _gtd:
    _grepo = Path(_gtd)
    _gg = ["git", "-c", "user.name=x", "-c", "user.email=x@x"]
    _greal.run(["git", "init", "-q"], cwd=_grepo, check=True)
    _greal.run(_gg + ["commit", "-q", "--allow-empty", "-m", "i"], cwd=_grepo, check=True)
    (_grepo / "sb" / "newdir").mkdir(parents=True)
    (_grepo / "sb" / "newdir" / "a.py").write_text("x", encoding="utf-8")
    _gsaved_root = x4.REPO_ROOT
    try:
        x4.REPO_ROOT = _grepo
        _gs1 = x4.freeze_snapshot(["sb"])
        (_grepo / "sb" / "newdir" / "b.py").write_text("y", encoding="utf-8")
        _gs2 = x4.freeze_snapshot(["sb"])
    finally:
        x4.REPO_ROOT = _gsaved_root
    check("G-D12 freeze_snapshot sees a NEW file inside an already-untracked dir (--untracked-files=all)",
          _gs1 is not None and x4.freeze_verdict(_gs1, _gs2) == "broken", str((_gs1, _gs2)))

_gspr = _os.environ.get("SAVE_POST_RIVAL")
_os.environ["SAVE_POST_RIVAL"] = "1"
try:
    check("G-D14 lane_env() (unarmed) still pops SAVE_POST_RIVAL", "SAVE_POST_RIVAL" not in x4.lane_env())
finally:
    if _gspr is None:
        _os.environ.pop("SAVE_POST_RIVAL", None)
    else:
        _os.environ["SAVE_POST_RIVAL"] = _gspr


# --- the DRIVEN batch loop: nothing is launched -----------------------------------------------------------------
class _GClock:
    def __init__(self):
        self.t = 1000.0

    def time(self):
        return self.t

    def sleep(self, s):
        self.t += s


class _GProc:
    _pid = 50000

    def __init__(self, dead=False):
        _GProc._pid += 1
        self.pid = _GProc._pid
        self.alive = not dead
        self.returncode = 1 if dead else None

    def poll(self):
        return None if self.alive else self.returncode

    def terminate(self):
        if self.alive:
            self.alive, self.returncode = False, 1

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.alive, self.returncode = False, 1


def _gdrive(minutes, on_bad="warn", fault=False, freeze_seq=None, raise_check_after=None, build_for=None,
            extra_body=None, die=None, spec=None, collect_raise_at=None):
    """`_run_batch` with a FAKE Popen (each fake writes the debug log a lane would: its env-all is the POKEBOT_* set it
    was HANDED), a fake clock and fake git. ⛔ THREE guards against a real launch: `x4.subprocess` is a namespace, the
    fake is asserted in place before the call, and BUILD_ROOT is a directory with no pokebot.py."""
    root = Path(_tempfile.mkdtemp(prefix="g14_"))
    prof = root / "profiles"
    (prof / x4.TEMPLATE_PROFILE).mkdir(parents=True)
    (prof / x4.TEMPLATE_PROFILE / "metadata.yml").write_text("rom: x\n", encoding="utf-8")
    out_root = root / "out"
    out_root.mkdir()
    clock = _GClock()
    sim = _gtypes.SimpleNamespace(procs=[], envs={}, order=[])
    the_spec = spec or _SPEC

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, stdin=None, creationflags=0):
        profile = cmd[2]
        p = _GProc(dead=profile in (die or set()))
        sim.procs.append(p)
        sim.order.append(profile)
        sim.envs[profile] = dict(env)
        if p.alive:
            pk = {k: v for k, v in env.items() if k.startswith("POKEBOT_")}
            body = ("f1 [DEXFENCE] skip #1 consume the HM/counter runway\n" if pk.get("POKEBOT_R25_RARE") != "1"
                    else "f1 skip #255 rare=no tier=\nf2 [KEYBATTLE] opp=1 key=True\n")
            body += (extra_body or {}).get(profile, "")
            d = prof / profile / "debug-logs"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"Story_(ENDLESS_RESET)-debug-{p.pid}.log").write_text(
                _ghdr(pk, (build_for or {}).get(profile, _BUILD12), body), encoding="utf-8")
        return p

    fake_sub = _gtypes.SimpleNamespace(Popen=fake_popen, DEVNULL=_greal.DEVNULL, STDOUT=_greal.STDOUT,
                                       run=lambda *a, **k: _gtypes.SimpleNamespace(stdout="", returncode=0),
                                       CREATE_NO_WINDOW=0)
    snaps = list(freeze_seq or [])
    calls = {"freeze": 0, "check": 0, "collect": 0}

    def fake_freeze(scope):
        calls["freeze"] += 1
        return snaps.pop(0) if snaps else (_HEAD40, "")

    real_check, real_collect = x4.check_headers, x4.collect_logs

    def counting_check(*a, **k):
        calls["check"] += 1
        if raise_check_after is not None and calls["check"] > raise_check_after:
            raise RuntimeError("injected x4h bug")
        return real_check(*a, **k)

    def counting_collect(lane, since):
        calls["collect"] += 1
        if collect_raise_at is not None and calls["collect"] == collect_raise_at:
            raise KeyboardInterrupt
        return real_collect(lane, since)

    names = ("subprocess", "time", "PROFILES", "BUILD_ROOT", "git_commit", "freeze_snapshot", "check_headers",
             "collect_logs")
    saved = {k: getattr(x4, k) for k in names}
    saved_fault = _os.environ.get("X4H_FAULT_ENVLEAK")
    rc, exc, buf = None, None, _gio.StringIO()
    try:
        x4.subprocess, x4.time, x4.PROFILES, x4.BUILD_ROOT = fake_sub, clock, prof, root / "no-bot-here"
        x4.git_commit = lambda scope=None: "aaaaaaa"
        x4.freeze_snapshot = fake_freeze
        x4.check_headers = counting_check
        x4.collect_logs = counting_collect
        if fault:
            _os.environ["X4H_FAULT_ENVLEAK"] = "1"
        else:
            _os.environ.pop("X4H_FAULT_ENVLEAK", None)
        assert x4.subprocess.Popen is fake_popen and not (x4.BUILD_ROOT / "pokebot.py").exists()  # ⛔ never real
        args = _gtypes.SimpleNamespace(lanes=16, minutes=minutes, runs=0, out=str(out_root), stagger=6.0,
                                       max_restarts=3, on_bad_header=on_bad, collect="full", wipe_saves=False,
                                       arms=str(_ARMS_FILE), profile_tag="g14")
        t0 = clock.t
        try:
            with _gctx.redirect_stdout(buf):
                rc = x4._run_batch(args, "20261001-000000", out_root, "g14", the_spec, _ARMS_FILE.read_text(
                    encoding="utf-8"), list(the_spec["arms"]), ["sandbox-pokebot", "tools/story-dev/x4_headless.py"])
        except BaseException as e:  # noqa: BLE001
            exc = e
        elapsed = clock.t - t0
    finally:
        for k, v in saved.items():
            setattr(x4, k, v)
        if saved_fault is None:
            _os.environ.pop("X4H_FAULT_ENVLEAK", None)
        else:
            _os.environ["X4H_FAULT_ENVLEAK"] = saved_fault
    summ = None
    try:
        summ = _json.loads((out_root / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return _gtypes.SimpleNamespace(rc=rc, exc=exc, elapsed=elapsed, summary=summ or {}, out=out_root, prof=prof,
                                   calls=calls, sim=sim, log=buf.getvalue())


# G1 a clean batch: the JOURNEY of every T1 fact, spawn to summary
_r = _gdrive(minutes=2)
_s = _r.summary
check("G1 a clean driven A/B ends OK (rc 0) at the time bound",
      _r.exc is None and _r.rc == 0 and _s.get("verdict") == "OK" and _s.get("stop_reason") == "deadline",
      str((_r.exc, _r.rc, _s.get("verdict"), _s.get("stop_reason"), _s.get("header_violations"))))
_want = {f"endless-g14-H{i + 1}-{x4.lane_starter(i)}": ("A" if i < 8 else "B") for i in range(16)}
_got = {p: {k: v for k, v in e.items() if k.startswith("POKEBOT_")} for p, e in _r.sim.envs.items()}
check("G1 the env HANDED TO POPEN is exactly each lane's arm, by block (instrument the action)",
      len(_got) == 16 and all(_got.get(p) == _SPEC["arms"][a] for p, a in _want.items()),
      str({p: a for p, a in _want.items() if _got.get(p) != _SPEC["arms"][a]}))
_gnames = {}
for _i in range(16):
    _sy = _r.prof / f"endless-g14-H{_i + 1}-{x4.lane_starter(_i)}" / "story.yml"
    _gnames[_i] = next((l.split(":", 1)[1].strip() for l in _sy.read_text(encoding="utf-8").splitlines()
                        if l.startswith("character_name:")), None) if _sy.exists() else None
check("G1 the in-game name WRITTEN to story.yml is paired across arms and distinct within one",
      all(_gnames[i] == _gnames[i + 8] for i in range(8)) and len({_gnames[i] for i in range(8)}) == 8, str(_gnames))
check("G1 the arms SPAWN INTERLEAVED (H1, H9, H2, H10, …), so neither gets a head start (review R12)",
      [p.split("-")[2] for p in _r.sim.order] == [f"H{n}" for i in range(8) for n in (i + 1, i + 9)],
      str(_r.sim.order[:6]))
_aj = _json.loads((_r.out / "ARMS.json").read_text(encoding="utf-8")) if (_r.out / "ARMS.json").exists() else {}
check("G1 ARMS.json records every lane's arm and the do-not-touch time",
      [l.get("arm") for l in _aj.get("lanes", [])] == ["A"] * 8 + ["B"] * 8 and bool(_aj.get("do_not_touch_until")))
check("G1 the DO-NOT-COMMIT banner is printed (review R3)", "DO NOT COMMIT, PULL OR MERGE" in _r.log)
_ld = _s.get("lanes_detail", {})
check("G1 summary.json carries the A/B block (arms, sha256, tag, freeze start, stop reason, no lost lanes)",
      _s.get("arms") == ["A", "B"] and len(str(_s.get("arms_sha256", ""))) == 64 and _s.get("profile_tag") == "g14"
      and _s.get("freeze_start") == [_HEAD40, ""] and _s.get("lanes_lost") == [])
check("G1 lane_rows carry the arm and its header verdict",
      [x.get("arm") for x in _s.get("lane_rows", [])] == ["A"] * 8 + ["B"] * 8
      and all(x.get("arm_header_verdict") == "ok" for x in _s.get("lane_rows", [])))
check("G1 each lane's spawn is RECORDED (pid, start, end, exit, stopped_by x4h)",
      len(_ld) == 16 and all(len(d.get("spawns") or []) == 1 and (d["spawns"][0].get("pid") or 0) > 50000
                             and d["spawns"][0].get("end") and d["spawns"][0].get("exit") is not None
                             and d["spawns"][0].get("stopped_by") == "x4h" for d in _ld.values()),
      str(_ld.get("H1", {}).get("spawns")))
check("G1 the deadline facts are recorded (alive_at_deadline, alive_at_stop, the CUT log)",
      all(d.get("alive_at_deadline") is True and d.get("alive_at_stop") is True
          and str(d.get("cut_log", "")).endswith(".log") for d in _ld.values()))
check("G1 the monitor recorded B's require/expect markers and A's expect marker",
      {" rare=", "[KEYBATTLE]"} <= set((_ld.get("H9", {}).get("monitor") or {}).get("first_seen", {}))
      and "consume the HM/counter runway" in (_ld.get("H1", {}).get("monitor") or {}).get("first_seen", {}))
check("G1 every lane's env-all header SETTLED ok (checked >= 1, unknown 0)",
      all((d.get("arm_headers_checked") or 0) >= 1 and d.get("arm_headers_unknown") == 0 for d in _ld.values()))
check("G1 the freeze watch actually polled during the batch", _r.calls["freeze"] >= 2, str(_r.calls))
check("G1 every lane was stopped", len(_r.sim.procs) == 16 and all(not p.alive for p in _r.sim.procs))
check("G1 the job object was set up, and the summary records its state (review R4)",
      bool(_s.get("job_object")) and (_os.name != "nt" or _s.get("job_object") == "kill-on-close job active"),
      str(_s.get("job_object")))
_gst = _gio.StringIO()
with _gctx.redirect_stdout(_gst):
    x4.status(str(_r.out))
check("G1 --status shows each lane's arm", "L01    A" in _gst.getvalue() and "L09    B" in _gst.getvalue(),
      _gst.getvalue()[-400:])
_before = {k: (v.get("name"), v.get("arm_headers_checked")) for k, v in _ld.items()}
with _gctx.redirect_stdout(_gio.StringIO()):
    x4.resummarise(_r.out)
_after = _json.loads((_r.out / "summary.json").read_text(encoding="utf-8")).get("lanes_detail", {})
check("G1 --resummarise keeps name and arm_headers_checked on a REAL driven batch",
      all((_after[k].get("name"), _after[k].get("arm_headers_checked")) == _before[k] for k in _before)
      and _before["H1"][0] == _before["H9"][0] == "H1")

# G2 the fault arm under --on-bad-header WARN: an arm violation aborts whatever warn says
_r = _gdrive(minutes=10, on_bad="warn", fault=True)
_s = _r.summary
check("G2 X4H_FAULT_ENVLEAK under --on-bad-header WARN aborts with ARM HEADER, rc 3, on the first ticks",
      _r.exc is None and _r.rc == 3 and "ARM HEADER" in str(_s.get("verdict")) and _r.elapsed < 200,
      str((_r.exc, _r.rc, _s.get("verdict"), _r.elapsed)))
check("G2 ... naming H1 and the leaked variable, and every lane is stopped",
      any(v.get("kind") == "arm" and v.get("tag") == "H1" and "POKEBOT_X4H_LEAK" in v.get("reason", "")
          for v in _s.get("header_violations", [])) and all(not p.alive for p in _r.sim.procs))

# G3 a lane running another commit
_r = _gdrive(minutes=10, build_for={"endless-g14-H4-random": "bbbbbbbbbbbb"})
_s = _r.summary
check("G3 a lane whose header names ANOTHER commit aborts the batch (the build check, end to end)",
      "ARM HEADER" in str(_s.get("verdict")) and _r.elapsed < 200
      and any(v.get("tag") == "H4" and v.get("kind") == "arm" for v in _s.get("header_violations", [])),
      str((_s.get("verdict"), _r.elapsed)))

# G4 a leak marker in an A lane; the CUT records on an abort; the MANIFEST groups by kind
_r = _gdrive(minutes=10, extra_body={"endless-g14-H3-treecko": "f9 [KEYBATTLE] opp=1\n"})
_s = _r.summary
check("G4 a forbid marker in an A lane aborts with ARM LEAK on the first ticks",
      "ARM LEAK" in str(_s.get("verdict")) and _r.elapsed < 200, str((_s.get("verdict"), _r.elapsed)))
_ld4 = _s.get("lanes_detail", {})
check("G4 an ABORT still records which runs were cut (alive_at_stop, cut_log, stopped_by) — review R2",
      len(_ld4) == 16 and all(d.get("alive_at_stop") is True and str(d.get("cut_log", "")).endswith(".log")
                              and (d.get("spawns") or [{}])[-1].get("stopped_by") == "x4h" for d in _ld4.values()),
      str({k: (d.get("alive_at_stop"), d.get("cut_log")) for k, d in list(_ld4.items())[:2]}))
_man4 = (_r.out / "MANIFEST.txt").read_text(encoding="utf-8") if (_r.out / "MANIFEST.txt").exists() else ""
check("G4 the MANIFEST lists the leak under A/B INTEGRITY, not as an emulation failure (review R8)",
      "A/B INTEGRITY" in _man4 and "[leak] H3" in _man4, _man4[-700:])

# G5 the freeze breaks at the first poll
_r = _gdrive(minutes=10, freeze_seq=[(_HEAD40, ""), (_HEAD40, "?? sandbox-pokebot/x.py\n")])
check("G5 a changed scoped porcelain aborts with FREEZE BROKEN at the first poll",
      "FREEZE BROKEN" in str(_r.summary.get("verdict")) and _r.elapsed < 200, str((_r.summary.get("verdict"), _r.elapsed)))

# G6 an x4h bug mid-loop
_r = _gdrive(minutes=10, raise_check_after=16)
check("G6 an exception in the loop ends the batch cleanly (no raise, summary written, verdict names it)",
      _r.exc is None and _r.rc == 1 and str(_r.summary.get("verdict", "")).startswith("FAILED — x4h error"),
      str((_r.exc, _r.rc, _r.summary.get("verdict"))))
check("G6 ... and EVERY lane is stopped", len(_r.sim.procs) == 16 and all(not p.alive for p in _r.sim.procs))

# G7 a dirty start is refused before anything exists (review R5)
_r = _gdrive(minutes=10, freeze_seq=[(_HEAD40, " M sandbox-pokebot/modules/x.py\n")])
check("G7 a DIRTY frozen tree at the start is refused (rc 2): no lane launched, no tagged profile made",
      _r.rc == 2 and not _r.sim.procs and not list(_r.prof.glob("endless-g14-*")), str((_r.rc, len(_r.sim.procs))))

# G8 a lane that dies for good: DEGRADED, named, and NOT misread as vacuity (review R1)
_spec60 = _json.loads(_json.dumps(_SPEC))
_spec60["monitor"]["B"]["require"] = {" rare=": 60, "[KEYBATTLE]": 60}
_r = _gdrive(minutes=3, die={"endless-g14-H10-mudkip"}, spec=_spec60)
_s = _r.summary
check("G8 a B lane that dies at every spawn makes the batch DEGRADED, naming it (not a silent OK)",
      str(_s.get("verdict", "")).startswith("OK — DEGRADED") and any("H10" in x for x in _s.get("lanes_lost", [])),
      str((_s.get("verdict"), _s.get("lanes_lost"))))
check("G8 ... and is NOT reported as VACUITY (the healthy lanes kept running to the bound)",
      not any(v.get("kind") == "vacuity" for v in _s.get("header_violations", [])) and _r.elapsed >= 180,
      str((_s.get("header_violations"), _r.elapsed)))

# G9 a Ctrl-C during the log copy still leaves a full summary (review R10)
_r = _gdrive(minutes=2, collect_raise_at=3)
_s = _r.summary
check("G9 an interrupt during log collection still writes summary.json for all 16 lanes",
      _s.get("collect_interrupted") is True and len(_s.get("lanes_detail", {})) == 16 and _r.exc is None,
      str((_s.get("collect_interrupted"), len(_s.get("lanes_detail", {})), _r.exc)))

# G10 the job object really kills a lane when x4h's handle closes (Windows; a harmless sleeper, never the bot)
if _os.name == "nt":
    import ctypes as _gct

    _job = x4._KillOnCloseJob()
    _sleeper = _greal.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        _assigned = _job.assign(_sleeper)
        _gct.WinDLL("kernel32").CloseHandle(_job.handle)
        try:
            _sleeper.wait(timeout=15)
        except _greal.TimeoutExpired:
            pass
        check("G10 a process in the kill-on-close job DIES when the job handle closes (review R4, measured)",
              _assigned and _sleeper.poll() is not None, str((_assigned, _sleeper.poll(), _job.note)))
    finally:
        if _sleeper.poll() is None:
            _sleeper.kill()


# ---------------------------------------------------------------------------
print("H. T1's SECOND mutant pass (236 mutants; its 31 real-gap survivors closed): the R1-R12 fixes, driven")
# ⛔ WHY: the first fold added R1-R12 with rows that killed only 48 of 81 mutants of those very fixes — the job
# assignment, the console tee and the provisional summary could each be deleted with the gate green.
# ---------------------------------------------------------------------------
from datetime import datetime as _hdt  # noqa: E402


def _hdrive(minutes, on_bad="warn", fault=False, freeze_seq=None, die=None, die_at=None, spec=None,
            collect_raise_at=None, collect_exc=KeyboardInterrupt, stub_job=False):
    """_gdrive + three knobs: die_at {profile: clock time}, collect_exc (the type raised at collect_raise_at), stub_job
    (x4._KillOnCloseJob replaced by a recorder whose assign returns True)."""
    root = Path(_tempfile.mkdtemp(prefix="h14_"))
    prof = root / "profiles"
    (prof / x4.TEMPLATE_PROFILE).mkdir(parents=True)
    (prof / x4.TEMPLATE_PROFILE / "metadata.yml").write_text("rom: x\n", encoding="utf-8")
    out_root = root / "out"
    out_root.mkdir()
    clock = _GClock()
    sim = _gtypes.SimpleNamespace(procs=[], envs={}, order=[], assigned=[])
    the_spec = spec or _SPEC

    class _HProc(_GProc):
        def __init__(self, dead=False, t_die=None):
            super().__init__(dead)
            self.t_die = t_die

        def poll(self):
            if self.alive and self.t_die is not None and clock.t >= self.t_die:
                self.alive, self.returncode = False, 1
            return None if self.alive else self.returncode

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, stdin=None, creationflags=0):
        profile = cmd[2]
        p = _HProc(dead=profile in (die or set()), t_die=(die_at or {}).get(profile))
        sim.procs.append(p)
        sim.order.append(profile)
        sim.envs[profile] = dict(env)
        if p.alive:
            pk = {k: v for k, v in env.items() if k.startswith("POKEBOT_")}
            body = ("f1 [DEXFENCE] skip #1 consume the HM/counter runway\n" if pk.get("POKEBOT_R25_RARE") != "1"
                    else "f1 skip #255 rare=no tier=\nf2 [KEYBATTLE] opp=1 key=True\n")
            d = prof / profile / "debug-logs"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"Story_(ENDLESS_RESET)-debug-{p.pid}.log").write_text(_ghdr(pk, _BUILD12, body), encoding="utf-8")
        return p

    class _StubJob:
        def __init__(self):
            self.handle, self.note = None, "stub job"

        def assign(self, proc):
            sim.assigned.append(proc)
            return True

    fake_sub = _gtypes.SimpleNamespace(Popen=fake_popen, DEVNULL=_greal.DEVNULL, STDOUT=_greal.STDOUT,
                                       run=lambda *a, **k: _gtypes.SimpleNamespace(stdout="", returncode=0),
                                       CREATE_NO_WINDOW=0)
    snaps = list(freeze_seq or [])
    calls = {"freeze": 0, "collect": 0}

    def fake_freeze(scope):
        calls["freeze"] += 1
        return snaps.pop(0) if snaps else (_HEAD40, "")

    real_collect = x4.collect_logs

    def counting_collect(lane, since):
        calls["collect"] += 1
        if collect_raise_at is not None and calls["collect"] == collect_raise_at:
            raise collect_exc("injected")
        return real_collect(lane, since)

    names = ("subprocess", "time", "PROFILES", "BUILD_ROOT", "git_commit", "freeze_snapshot", "collect_logs",
             "_KillOnCloseJob", "_JOB")
    saved = {k: getattr(x4, k) for k in names}
    saved_fault = _os.environ.get("X4H_FAULT_ENVLEAK")
    rc, exc, buf = None, None, _gio.StringIO()
    try:
        x4.subprocess, x4.time, x4.PROFILES, x4.BUILD_ROOT = fake_sub, clock, prof, root / "no-bot-here"
        x4.git_commit = lambda scope=None: "aaaaaaa"
        x4.freeze_snapshot = fake_freeze
        x4.collect_logs = counting_collect
        x4._JOB = None
        if stub_job:
            x4._KillOnCloseJob = _StubJob
        if fault:
            _os.environ["X4H_FAULT_ENVLEAK"] = "1"
        else:
            _os.environ.pop("X4H_FAULT_ENVLEAK", None)
        assert x4.subprocess.Popen is fake_popen and not (x4.BUILD_ROOT / "pokebot.py").exists()
        args = _gtypes.SimpleNamespace(lanes=16, minutes=minutes, runs=0, out=str(out_root), stagger=6.0,
                                       max_restarts=3, on_bad_header=on_bad, collect="full", wipe_saves=False,
                                       arms=str(_ARMS_FILE), profile_tag="h14")
        try:
            with _gctx.redirect_stdout(buf):
                rc = x4._run_batch(args, "20261001-000000", out_root, "h14", the_spec, _ARMS_FILE.read_text(
                    encoding="utf-8"), list(the_spec["arms"]), ["sandbox-pokebot", "tools/story-dev/x4_headless.py"])
        except BaseException as e:  # noqa: BLE001
            exc = e
    finally:
        for k, v in saved.items():
            setattr(x4, k, v)
        if saved_fault is None:
            _os.environ.pop("X4H_FAULT_ENVLEAK", None)
        else:
            _os.environ["X4H_FAULT_ENVLEAK"] = saved_fault
    summ = None
    try:
        summ = _json.loads((out_root / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    man = (out_root / "MANIFEST.txt").read_text(encoding="utf-8") if (out_root / "MANIFEST.txt").exists() else ""
    aj = _json.loads((out_root / "ARMS.json").read_text(encoding="utf-8")) if (out_root / "ARMS.json").exists() else {}
    return _gtypes.SimpleNamespace(rc=rc, exc=exc, summary=summ or {}, out=out_root, prof=prof, calls=calls, sim=sim,
                                   log=buf.getvalue(), manifest=man, arms_json=aj)


# H-P1 the PROVISIONAL summary is what survives when the post-stop phase dies (R10, R1, R2)
_hr = _hdrive(minutes=10, fault=True, collect_raise_at=1, collect_exc=RuntimeError)
_hs = _hr.summary
check("H-P1 an exception AFTER the stop leaves the PROVISIONAL summary: verdict FAILED ARM HEADER, lanes_lost [], "
      "every lane's alive_at_stop + cut_log",
      isinstance(_hr.exc, RuntimeError) and _hs.get("provisional") is True
      and str(_hs.get("verdict", "")).startswith("FAILED") and "ARM HEADER" in str(_hs.get("verdict"))
      and _hs.get("lanes_lost") == [] and len(_hs.get("lanes") or {}) == 16
      and all(d.get("alive_at_stop") is True and str(d.get("cut_log") or "").endswith(".log")
              for d in (_hs.get("lanes") or {}).values()),
      str((_hr.exc, _hs.get("provisional"), _hs.get("verdict"), _hs.get("lanes_lost"))))

# H-P2 an ABORT after a lane was lost stays FAILED (R1)
_hr = _hdrive(minutes=10, die={"endless-h14-H10-mudkip"},
              freeze_seq=[(_HEAD40, ""), (_HEAD40, ""), (_HEAD40, "?? sandbox-pokebot/x.py\n")])
check("H-P2 a batch ABORTED after losing a lane reads FAILED (not 'OK — DEGRADED') and still names the lost lane",
      str(_hr.summary.get("verdict", "")).startswith("FAILED — FREEZE BROKEN")
      and any("H10" in x for x in _hr.summary.get("lanes_lost") or []),
      str((_hr.summary.get("verdict"), _hr.summary.get("lanes_lost"))))

# H-P3 a lane that dies in the deadline tick is not 'lost' (R1)
_hr = _hdrive(minutes=2, die_at={"endless-h14-H5-torchic": 1116.0})
check("H-P3 a lane that dies in the DEADLINE tick is not a lost lane (verdict OK, lanes_lost [])",
      _hr.summary.get("verdict") == "OK" and _hr.summary.get("lanes_lost") == [],
      str((_hr.summary.get("verdict"), _hr.summary.get("lanes_lost"))))

# H-P4 / H-P13 a dead lane's spawns are NOT marked stopped_by x4h; the MANIFEST names the lost lane (R2, R8)
_spec60h = _json.loads(_json.dumps(_SPEC))
_spec60h["monitor"]["B"]["require"] = {" rare=": 60, "[KEYBATTLE]": 60}
_hr = _hdrive(minutes=3, die={"endless-h14-H10-mudkip"}, spec=_spec60h)
_h10 = (_hr.summary.get("lanes_detail", {}).get("H10") or {}).get("spawns") or []
check("H-P4 a lane that DIED has 4 spawns (1 + 3 restarts), each exit 1 and none marked stopped_by x4h",
      len(_h10) == 4 and all(sp.get("stopped_by") is None and sp.get("exit") == 1 for sp in _h10), str(_h10[:2]))
check("H-P13 the MANIFEST names the lost lane", "lanes lost: ['H10 (arm B)" in _hr.manifest, _hr.manifest[-500:])

# H-P5 resummarise keeps EVERY T1 run fact on a driven batch (R2, R7)
_hr = _hdrive(minutes=2)
_hb = {k: dict(v) for k, v in _hr.summary.get("lanes_detail", {}).items()}
with _gctx.redirect_stdout(_gio.StringIO()):
    x4.resummarise(_hr.out)
_ha = _json.loads((_hr.out / "summary.json").read_text(encoding="utf-8")).get("lanes_detail", {})
_hkeys = ("arm", "name", "spawns", "alive_at_deadline", "alive_at_stop", "cut_log", "monitor", "arm_headers_checked",
          "arm_headers_unknown", "arm_header_verdict")
check("H-P5 --resummarise keeps every T1 run fact (incl. alive_at_stop, arm_headers_unknown)",
      len(_hb) == 16 and all(_ha[t].get(k) == _hb[t].get(k) and k in _ha[t] for t in _hb for k in _hkeys),
      str([(t, k) for t in _hb for k in _hkeys if _ha.get(t, {}).get(k) != _hb[t].get(k) or k not in _ha.get(t, {})][:4]))

# H-P6 the do-not-touch time is the batch's END (R3)
_huntil = _hdt.fromtimestamp(1000.0 + 2 * 60).strftime("%Y-%m-%d %I:%M %p")
check("H-P6 do_not_touch_until is the batch's END time, in ARMS.json and in the banner",
      _hr.arms_json.get("do_not_touch_until") == _huntil and f"# until {_huntil}" in _hr.log,
      str((_hr.arms_json.get("do_not_touch_until"), _huntil)))

# H-P7 every spawn is ASSIGNED to the batch's job object (R4)
_hr = _hdrive(minutes=2, stub_job=True)
_hld = _hr.summary.get("lanes_detail", {})
check("H-P7 spawn() assigns EVERY lane process to the batch's job, and records in_job",
      len(_hr.sim.assigned) == 16 and all(a is b for a, b in zip(_hr.sim.assigned, _hr.sim.procs))
      and all((d.get("spawns") or [{}])[0].get("in_job") is True for d in _hld.values()) and len(_hld) == 16,
      str((len(_hr.sim.assigned), [(d.get("spawns") or [{}])[0].get("in_job") for d in list(_hld.values())[:3]])))

# H-P8 / H-P9 an untracked file in scope, or a failed snapshot, refuses the start (R5)
_hr = _hdrive(minutes=10, freeze_seq=[(_HEAD40, "?? sandbox-pokebot/modules/new.py\n")])
check("H-P8 an UNTRACKED file in the frozen scope refuses the start (rc 2, nothing launched or made)",
      _hr.rc == 2 and not _hr.sim.procs and not list(_hr.prof.glob("endless-h14-*")), str((_hr.rc, len(_hr.sim.procs))))
_hr = _hdrive(minutes=10, freeze_seq=[None])
check("H-P9 a FAILED start snapshot refuses the start (rc 2, nothing launched or made)",
      _hr.rc == 2 and not _hr.sim.procs and not list(_hr.prof.glob("endless-h14-*")), str((_hr.rc, len(_hr.sim.procs))))


# H-P10 _Tee survives a dead console (R6)
class _HDeadConsole:
    def write(self, s):
        raise ValueError("I/O operation on closed file")

    def flush(self):
        raise OSError(22, "Invalid argument")


with _tempfile.TemporaryDirectory() as _htd:
    _hsaved = sys.stdout
    try:
        sys.stdout = _HDeadConsole()
        _htee = x4._Tee(Path(_htd) / "x4h.txt")
    finally:
        sys.stdout = _hsaved
    _hok = True
    try:
        _htee.write("abc\n")
        _htee.flush()
    except Exception:  # noqa: BLE001
        _hok = False
    _htee.close()
    check("H-P10 _Tee: a dead console (ValueError on write, OSError on flush) raises nothing and the FILE still gets "
          "the text", _hok and (Path(_htd) / "x4h.txt").read_text(encoding="utf-8") == "abc\n")

# H-P11 R7 counts with a BAD header present
_hl = x4.Lane(slot=0, tag="H1", starter="torchic", profile="p", profile_dir=Path("."), out_dir=Path("."), arm="A",
              arm_env={"x": "1"})
_hl.arm_headers = {"a.log": ("ok", ""), "b.log": ("unknown", ""), "c.log": ("bad", "leak")}
_hls = x4.lane_summary(_hl, "", "", 0)
check("H-P11 with ok + unknown + bad: checked 1, unknown 1, arm_header_verdict BAD",
      (_hls.get("arm_headers_checked"), _hls.get("arm_headers_unknown"), _hls.get("arm_header_verdict")) == (1, 1, "BAD"),
      str((_hls.get("arm_headers_checked"), _hls.get("arm_headers_unknown"), _hls.get("arm_header_verdict"))))

# H-P12 the MANIFEST groups each violation by kind; an OLD kind-less violation is an emulation one (R8)
_hman = x4.render_manifest({**batch, "arms": ["A", "B"], "header_violations": [
    {"tag": "H1", "log": "a.log", "reason": "speed=1", "kind": "emulation"},
    {"tag": "H2", "log": "b.log", "reason": "old-style"},
    {"tag": "H3", "log": "c.log", "reason": "leaked", "kind": "leak"}]})
_hemu, _, _hint = _hman.partition("A/B INTEGRITY")
check("H-P12 EMULATION counts 2 (incl. the kind-less one); A/B INTEGRITY lists ONLY the leak",
      "violations: 2" in _hemu and "H2" in _hemu and "violations: 1" in _hint and "[leak] H3" in _hint
      and "H1" not in _hint and "H2" not in _hint, _hman[-600:])

# H-P14 the DEFAULT repo root (what main() uses) is the one checked (R9)
with _tempfile.TemporaryDirectory() as _htd:
    _hmain = Path(_htd) / "m"
    (_hmain / ".git").mkdir(parents=True)
    _hwt = Path(_htd) / "w"
    _hwt.mkdir()
    (_hwt / ".git").write_text("gitdir: x\n", encoding="utf-8")
    _hsr = x4.REPO_ROOT
    try:
        x4.REPO_ROOT = _hmain
        _hem, _, _ = x4.arms_preflight(str(_ARMS_FILE), "h14d", 16, "sandbox", SANDBOX, Path(_htd) / "p")
        x4.REPO_ROOT = _hwt
        _hew, _, _ = x4.arms_preflight(str(_ARMS_FILE), "h14d", 16, "sandbox", SANDBOX, Path(_htd) / "p")
    finally:
        x4.REPO_ROOT = _hsr
    check("H-P14 with NO repo_root (main()'s call) the module REPO_ROOT is checked: main ok, worktree refused",
          _hem == [] and any("MAIN checkout" in e for e in _hew), str((_hem, _hew)))

# H-P15 after an interrupt, collection STOPS (R10)
_hr = _hdrive(minutes=2, collect_raise_at=3)
check("H-P15 after a Ctrl-C during collection no further lane is copied (3 collect calls, not 16)",
      _hr.calls["collect"] == 3 and _hr.summary.get("collect_interrupted") is True, str(_hr.calls))

# H-P16 the leak trigger is exactly '1', the same value the preflight checks (R11)
_hsf = _os.environ.get("X4H_FAULT_ENVLEAK")
try:
    _os.environ["X4H_FAULT_ENVLEAK"] = "0"
    _hla = x4.Lane(slot=0, tag="H1", starter="torchic", profile="p", profile_dir=Path("."), out_dir=Path("."),
                   arm="A", arm_env=dict(_SPEC["arms"]["A"]))
    check("H-P16 X4H_FAULT_ENVLEAK=0 does NOT leak (the preflight lets '0' through, so lane_env must agree)",
          "POKEBOT_X4H_LEAK" not in x4.lane_env(_hla))
finally:
    if _hsf is None:
        _os.environ.pop("X4H_FAULT_ENVLEAK", None)
    else:
        _os.environ["X4H_FAULT_ENVLEAK"] = _hsf

# H-P17 (optional) vacuity fires AT the deadline, not one tick later
with _tempfile.TemporaryDirectory() as _htd:
    (Path(_htd) / "debug-logs").mkdir()
    _hv = x4.Lane(slot=8, tag="H9", starter="torchic", profile="p", profile_dir=Path(_htd), out_dir=Path(_htd), arm="B",
                  arm_env={})
    _hv.first_spawn = 1000.0
    check("H-P17 require fires at EXACTLY its deadline",
          [v["kind"] for v in x4.monitor_lane(_hv, 0.0, {"require": {"[KEYBATTLE]": 60}}, 1060.0)] == ["vacuity"])


print()
if FAILURES:
    print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
    sys.exit(1)
print("ALL PASS")
