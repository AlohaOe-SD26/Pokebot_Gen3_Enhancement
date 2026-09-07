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
import sys
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


print()
if FAILURES:
    print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
    sys.exit(1)
print("ALL PASS")
