"""MUTANT PROOF of A1, THE FRONTIER PROBE (`gates/frontier_probe.py`, spec 2026-11-11-A1-FRONTIER-PROBE-SPEC.md 4.2, 2026-11-14):
each guard of the runner, broken in a COPY of the package, fails its predicted test of `gates/test_frontier_probe.py`.

    py -3.12 -B ai_player/gates/revert_frontier.py [M1,M2] [--workers N]       (exit 0 = every prediction held)

The `revert_r1.py` pattern: copy the package (no states, no evidence) and `PROJECT KNOWLEDGE/ai-frontier.txt` (T33's CONTROL
reads MC's newest graded target from it), apply ONE mutant's edit (its anchor must occur exactly once, or the mutant is NOT
APPLIED; `gates/check_anchors.py` checks every anchor in seconds), run `test_frontier_probe.py`'s GuardTests from the copy
(the control F0 runs the whole module, CopyLoadTests too), and check the PREDICTION: CAUGHT = the run fails and every
predicted test is among the failing ones. The unchanged copy F0 must pass every test. Serial by default: the full lane
(`run_regression.py`) runs it with no --workers. The frozen-tree watch (`provenance.watch`) is checked before every mutant
and seals the verdict. Evidence: `ai_player/evidence/<date>-frontier-REVERT.txt` (only when every mutant is run).

THE TABLE (250 mutants; the spec's "about 54" predates the amendments' tests T31-T36 and AM-11, so it is not this count):
  G01-G98  the build's guard table (B2.3, 2026-11-14): ONE edit of `frontier_probe.py` per guard of T1-T36 and AM-11, each
           shown, on a temp copy loaded by the suite's own `load_module`, to FAIL the case named here ("98 caught, 0 not
           caught"). The anchors and replacements are that table's, but G33-G36's: the verifier's round 1 (F1) made the tick
           ask `disk_decision` about each measurement, so those four are anchored on the tick's new lines (same guards, same
           predictions), and G27-G30 (`disk_decision`'s boundaries) now break the code a batch runs.
  V05-V44  the verifier's round 1 (2026-11-14): the guards its own mutants showed NO case caught (V05-V31, its names kept,
           re-anchored where the fix moved a line) and the round's further guards (V40-V44), each caught by the FAULT or
           CONTROL the round added. Its two NITs, replay's and `child_env`'s environment strips, are V09 and V15 below.
  V55-V74  the verifier's round 2 (2026-11-14): its one-edit mutants of its two findings, which NO case caught (R2-M1, the
           disk guard's and the batch's terminal ends: V69, V70, V72, V73, V74; R2-M2, the development seed check's two
           refusals: V55, V56), its names, anchors and replacements kept, each now caught by the FAULT arm the round added
           to T14 (through the real `run_batch`) or T13.
  K1-K2    the round's own two: a seed ledger that cannot be read at a path ending in the KNOWN non-ledger is allowed (K1)
           and LISTED (K2), as 2.5 says (before the round it was skipped unlisted), each caught by T13's CONTROL.
  W06-W69, V09-V80, Y01-Y12   the verifier's round 3 (2026-11-14): its one-edit mutants that NO case caught (W-names,
           anchors and replacements verbatim; W12 and W41 HUNG T26 until the suite's planted clock got a pass limit that
           FAILS), the earlier rounds' NITs it re-read (round 1's V09 and V15, round 2's V57-V63, and V80, X4's edit, now
           seen by T9's and T27's MC lines too), and the round's own guards and CONTROL-side edits (Y01-Y12: the empty job
           list, the graded-ch5 refusal, an MC replay's snapshot, MC's ledger verdict, and the other side of six rules).
  Z01-Z33  fix round 3's BOUNDED SWEEP of the refusal family (`_ai_lab/a1/fix3/sweep_guards.py`: every if/elif line of
           run_refusals, run_batch, parse_stages, start_refusal, placement_problems, manifest_problems, jobs_problems,
           seeds_named, trainer_problems, dependency_of, start_check, custody_problems, profile_refusal, legs_refusal,
           continue_rule, replay and their kin that no row edited): each guard among them, on its FAULT arm; Z25 (C2's
           class half) is predicted REDUNDANT ALONE, because C2's purity half stops the same legs. The lines the sweep
           left are bookkeeping or redundant by construction (ai_player/README.md, A1's "Run it" lines).
  H07, H09, U01, U02   the verifier's round 4 (2026-11-15): the two one-edit mutants of its bounded hunt that NO case
           caught (H-names, anchors and replacements verbatim; not the test-side H1-H4 below): a resume's skip that drops
           the LEDGER-PATH half of its (ledger path, entry id) key (H07) and the end-map rule without CUT_WORLD (H09), each
           now caught by the FAULT arm fix round 4 added to T24d or T7; and the other half of each rule, the key's id
           (U02) and HUNG (U01), caught by the arm that was there.
  P01-P03, E01-E02, H02, H03   fix round 5 (2026-11-15): `run` refuses --parallel under 1 (P01; its bound at 0, P02, and
           at 2, P03, the CONTROL side; T37), a job's env must be EMPTY (E01; every allowed key, E02; T38), and the verifier's
           round-4 NITs H02 (an ABORTED MC verdict's reading, T14) and H03 (an MC verdict's own chain count, T33's CONTROL),
           their names, anchors and replacements verbatim.
  D01-D06, V6M2, V6M3, P04   fix round 6 (2026-11-15): the merge check counts every PLANNED MC chain (batch.json's
           `mc_planned`), so an MC job DROPPED before its launch reads STOP, never a PASS over the chains that started
           (the verifier's round-6 V6-1, MAJOR; D01-D05 on T33's FAULT, D06 and D03 on its CONTROL), and T37 asserts the
           --parallel refusal in development mode (V6M3) and on --resume (V6M2), the verifier's names, anchors and
           replacements verbatim; P04 its CONTROL side (a --resume at --parallel 1 carries no --parallel refusal).
  V6M1     the lead's closing row (2026-11-15): a job's env must be EMPTY on an MC job too (the verifier's round-6 NIT
           V6-3, its name and the same edit; T38's MC arm).
  WL1-WL8  build plan step 5 (2026-11-15): the planted walls (`frontier_probe.MUTANTS`, 4.3 P1 and P2) and their offline
           planner tests T39 (WALL-OLDALE) and T40 (WALL-BRINEY): each wall's edit broken in `MUTANTS` (its refusal gone,
           the wrong map or door, a side missing: WL1-WL6, each caught by its FAULT on the walled copy's own planner), and
           `apply_mutant` adding to the staged edit (WL7) or editing the source tree instead of the staged copy (WL8, T39's
           and T40's CONTROL too).
  PQ1-PQ3  fix round 7 (2026-11-16, found by the first live run): `python_processes()` lists python.exe only (PQ1: no
           filter, its own PowerShell query returned; PQ2: the `py` launcher image instead; PQ3: the launcher too, a `py`
           launch counted twice), each caught by T41, which runs the REAL query on the REAL process table (no stub).
  H1-H4  the test-side guards (B2.3b), whose guard is not in `frontier_probe.py`: T28's two import scans (the suite's
           `importers` and `check_grader_imports.scan`'s chain report) and T30's two pins, each removed by one edit.
  X1-X4    four of 4.2's named mutants the guard table lacked: a WAIT that drops the job, a dependency SKIP DROPPED by
           --max-wait, a resume keyed by seed, and an MC job sending AI_PLAYER_GOALS (the job's goal policy ignored).
Part 0's own mutants (GM01-GM20, spec 3.15 item 6) sit with its AI-side tests in `revert_r1.py`. The predictions were
written and their sha256 recorded (the build's run book, `_ai_lab/a1/STATE.md`) BEFORE the first run.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from ai_player.gates.provenance import keep_earlier, provenance  # noqa: E402

EVIDENCE = REPO / "ai_player" / "evidence"
TIMEOUT = 600
CAUGHT, REDUNDANT, CONTROL = "CAUGHT", "REDUNDANT", "CONTROL"
PROBE, TESTS, G3 = "gates/frontier_probe.py", "gates/test_frontier_probe.py", "gates/check_grader_imports.py"
#: copied beside the package in each copy: `frontier_probe.frontier_target` reads it (T33's CONTROL)
FRONTIER = ("PROJECT KNOWLEDGE", "ai-frontier.txt")
#: the suite a mutant runs (GuardTests: one FAULT and one CONTROL test per guard; CopyLoadTests would load the mutated
#: source again and fail with it, so it adds nothing to a mutant run), and the control's (the whole module)
DEFAULT_SUITES = ("test_frontier_probe:GuardTests",)
CONTROL_SUITES = ("test_frontier_probe",)

#: (name, T, the guard, anchor, replacement, the test predicted to fail) of the guard table: G01-G98 edit frontier_probe.py
_GUARDS = [
    ("G01", "T1", "exit 7 (other gate text) is REFUSED",
     "    if code == launcher.GATE_REFUSED_EXIT:\n        return REFUSED,",
     "    if False:\n        return REFUSED,", "test_t1_fault"),
    ("G02", "T1", "exit 2 with no verdict file is REFUSED",
     "    if code == 2 and verdict is None:", "    if False:", "test_t1_fault"),
    ("G03", "T1b", "a gate TIMEOUT is INFRA",
     "    if code == launcher.GATE_REFUSED_EXIT and gate_timeout_text() in stdout:", "    if False:", "test_t1b_fault"),
    ("G04", "T2", "a host budget end (exit 4 / 124 with a verdict) is CLEAN-BUDGET",
     "    if code in budget_codes:", "    if False:", "test_t2_fault"),
    ("G05", "T2", "play: stopped: with real >= frames is BUDGET (the launcher's _ran_out)",
     "    return frames > 0 and real >= frames", "    return frames > 0 and real > frames", "test_t2_fault"),
    ("G06", "T2b", "exit 124 with no verdict is HUNG (the review's F1: not INFRA)",
     "        return HUNG, HUNG_TEXT", "        return INFRA, HUNG_TEXT", "test_t2b_fault"),
    ("G07", "T2b", "driver_killed is INFRA (never counted)",
     '    if f.get("driver_killed"):', "    if False:", "test_t2b_control"),
    ("G08", "T2b", "a launch dead before a frame is INFRA",
     '    if f.get("launch_died"):', "    if False:", "test_t2b_control"),
    ("G09", "T3", "a CLEAN verdict whose state is not this run's is INFRA",
     '    if not f.get("fresh") or not f.get("end_truth"):', '    if not f.get("end_truth"):', "test_t3_fault"),
    ("G10", "T4", "a verdict word other than CLEAN is NOT CLEAN",
     '    if verdict is not None and verdict.get("verdict") != "CLEAN":', "    if False:", "test_t4_fault"),
    ("G11", "T5", "a false `done:` claim is a mismatch and a blocker",
     "    claim = (klass == CLEAN_CHOSEN and", "    claim = False and (klass == CLEAN_CHOSEN and", "test_t5_fault"),
    ("G12", "T6", "digit runs made N in reason_norm",
     '    value = re.sub(r"\\d+", "N", str(text or ""))', '    value = str(text or "")', "test_t6_fault"),
    ("G13", "T6", "the LOOP key drops next_unmet",
     '        key = [chapter, "-", "loop", loop["pair"], "LOOP"]', '        key = [chapter, nxt or "-", "loop", loop["pair"], "LOOP"]',
     "test_t6_fault"),
    ("G14", "T7", "optional milestones are never the next unmet",
     '        if milestone.get("optional") or milestone.get("waypoint") is not None:',
     '        if milestone.get("waypoint") is not None:', "test_t7_fault"),
    ("G15", "T7", "an absent mark is UNREAD, never counted",
     '        if result["missing"]:\n            if found is None:', '        if False:\n            if found is None:',
     "test_t7_fault"),
    ("G16", "T7", "the next unmet is read on the END truth only when this run wrote it (else the start)",
     "    if end_written(before, after, written):", "    if after:", "test_t7_fault"),
    ("G17", "T8", "INFRA, REFUSED and NOT CLEAN never in the denominator",
     '        judged = [r for r in group if r.get("class") not in EXCLUDED_CLASSES]', "        judged = list(group)",
     "test_t8_fault"),
    ("G18", "T8", "ranked by count, most first",
     '        ranked.sort(key=lambda e: (-e["count"], json.dumps(e["key"])))',
     '        ranked.sort(key=lambda e: (e["count"], json.dumps(e["key"])))', "test_t8_fault"),
    ("G19", "T9", "the child sanitizes its environment before any launcher import",
     "    sanitize_environ()\n    job = json.loads(", "    job = json.loads(", "test_t9_fault"),
    ("G20", "T9", "a job's environment key off the allow-list is refused",
     "        if name not in ENV_ALLOWED:", "        if False:", "test_t9_fault"),
    ("G21", "T10", "the trainer never calls ledger.begin",
     '    if mode == "development" and entry_id is None:', "    if entry_id is None:", "test_t10_fault"),
    ("G22", "T11", "--out and stages outside every git work tree",
     "    if work_tree(resolved):", "    if False:", "test_t11_fault"),
    ("G23", "T11", "never in a pokebot-learner folder",
     '    if "pokebot-learner" in (part.lower() for part in resolved.parts):', "    if False:", "test_t11_fault"),
    ("G24", "T12", "the trainer needs the band row",
     "    if band_row(data) is None:", "    if False:", "test_t12_fault"),
    ("G25", "T12", "reserve-band runs once",
     "    if band_row(ledger.load(path)) is not None:", "    if False:", "test_t12_fault"),
    ("G26", "T13", "a development seed any entry names is refused",
     '                problems += [f"a seed of {span[0]}-{span[1]} is named: {hit}" for hit in hits[:8]]',
     "                problems += []", "test_t13_fault"),
    ("G27", "T14", "the 40 GB abort: < (40.0 does not abort)",
     "    if free_gb is not None and free_gb < ABORT_FREE_GB:", "    if free_gb is not None and free_gb <= ABORT_FREE_GB:",
     "test_t14_control"),
    ("G28", "T14", "the world cut: > (1,000,000,000 kept)",
     "    if world_bytes is not None and world_bytes > world_cut(mc):",
     "    if world_bytes is not None and world_bytes >= world_cut(mc):", "test_t14_control"),
    ("G29", "T14", "the out cap: > (5,000,000,000 launches)",
     "    if out_bytes is not None and out_bytes > OUT_CAP_BYTES:", "    if out_bytes is not None and out_bytes >= OUT_CAP_BYTES:",
     "test_t14_control"),
    ("G30", "T14", "the profile budget: > (1,250,000,000 kept)",
     "    if profile_bytes is not None and profile_bytes > profile_budget(mc):",
     "    if profile_bytes is not None and profile_bytes >= profile_budget(mc):", "test_t14_control"),
    ("G31", "T14", "the 45 GB start floor: < (45.0 starts)",
     "    if free_gb < START_FREE_GB:", "    if free_gb <= START_FREE_GB:", "test_t14_control"),
    ("G32", "T14", "P_fit (an off-by-one starts a job that does not fit)",
     "    return math.floor(round(room / per, 6))", "    return math.floor(round(room / per, 6)) + 1", "test_t14_fault"),
    ("G33", "T14", "the tick ABORTS under 40 GB",
     '    if disk_decision(None, free, None) == "abort" and not state["aborted"]:', "    if False:", "test_t14_fault"),
    ("G34", "T14", "the tick cuts a world over the cut",
     '        if leg is not None and disk_decision(size, None, None, mc=mc) == "cut-world":', "        if False:",
     "test_t14_fault"),
    ("G35", "T14", "the tick drops pending jobs over the --out cap",
     '    if not state["out_over"] and disk_decision(None, None, deps.folder_bytes(out)) == "drop":', "    if False:",
     "test_t14_fault"),
    ("G36", "T14", "the tick cuts a profile folder over its budget",
     '        if leg is not None and disk_decision(None, None, None, held, mc=mc) == "cut-profile":', "        if False:",
     "test_t14_fault"),
    ("G37", "T15", "a zip that fails its check keeps the raw logs",
     "    if problem is not None:\n        return {\"zip\": str(target)", "    if False:\n        return {\"zip\": str(target)",
     "test_t15_fault"),
    ("G38", "T15", "an AI file's copy is size-checked",
     '            out[name] = "kept" if want == got else f"size check FAILED: {got} bytes, the source {want}"',
     '            out[name] = "kept"', "test_t15_fault"),
    ("G39", "T16", "an unknown world key (rng_state) is dropped and listed",
     "        elif name not in WORLD_DROPPED:\n            unclassified.append(name)",
     "        elif name not in WORLD_DROPPED:\n            out[name] = value", "test_t16_fault"),
    ("G40", "T16", "a warp's uses dropped",
     'WARP_KEPT = ("to", "arrival", "direction", "inferred")', 'WARP_KEPT = ("to", "arrival", "direction", "inferred", "uses")',
     "test_t16_fault"),
    ("G41", "T16", "rides' counters dropped",
     'RIDE_KEPT = ("from", "to", "arrival", "who", "gfx", "tile", "words", "place", "via")',
     'RIDE_KEPT = ("from", "to", "arrival", "who", "gfx", "tile", "words", "place", "via", "uses", "closed")',
     "test_t16_fault"),
    ("G42", "T16", "an unknown ride or bump key is dropped AND listed",
     "        elif name not in dropped:\n            unclassified.append(f\"{where}.{name}\")",
     "        elif name not in dropped:\n            out[name] = value", "test_t16_fault"),
    ("G43", "T16", "a map whose tile_fields differ is dropped (fail closed)",
     '                if list(entry.get("tile_fields") or []) != list(TILE_FIELDS):', "                if False:",
     "test_t16_fault"),
    ("G44", "T16", "tiles keep 4 of the 7 fields", "TILE_STATIC = 4", "TILE_STATIC = 7", "test_t16_control"),
    ("G45", "T35", "only the trainer-battle tell names a foe (a K1 tell never does)",
     '        if record.get("decision") == "tell" and reason.startswith(TRAINER_TELL):',
     '        if record.get("decision") == "tell":', "test_t35_fault"),
    ("G46", "T17", "a saved start's origin is practice",
     '"origin": "new_game" if kind == "chain" else "practice"', '"origin": "new_game"', "test_t17_fault"),
    ("G47", "T17", "L6 at 1,000,000 frames (2.3)",
     "6: 1_000_000, 7: 1_200_000}", "6: 600_000, 7: 1_200_000}", "test_t17_control"),
    ("G48", "T18", "C1: a leg not reached stops the chain",
     "    if not reached:\n        why.append(f\"C1", "    if False:\n        why.append(f\"C1", "test_t18_fault"),
    ("G49", "T18", "C2: purity not clean stops the chain",
     "    if wrong:\n        why.append(f\"C2 purity", "    if False:\n        why.append(f\"C2 purity", "test_t18_fault"),
    ("G50", "T18", "C3: a world tail that does not parse stops the chain",
     '    if not world.get("last_ok"):', "    if False:", "test_t18_fault"),
    ("G51", "T18", "C6: STOP.txt stops the chain (the reason names C6)",
     '    if stop_seen:\n        why.append("C6', '    if False:\n        why.append("C6', "test_t18_fault"),
    ("G52", "T19", "stage custody: the md5 of the table",
     '    if state_md5 != info["md5"]:', "    if False:", "test_t19_fault"),
    ("G53", "T19", "stage custody: the truth holds ch5_rival_meet's proof",
     '    if proof is None or not LC.proof_holds(marks, proof)["held"]:', "    if False:", "test_t19_fault"),
    ("G54", "T19", "stage custody: ONE starter line",
     "    if len(lines) != 1:", "    if not lines:", "test_t19_fault"),
    ("G55", "T19", "the child's custody: the start state's md5 before the launch",
     '        if now is None or now != start.get("state_md5"):', "        if False:", "test_t19_fault"),
    ("G56", "T20", "the donor is named (never run_arm's silent fallback)",
     '            launcher.ensure_profile(build_root, job["profile"], template=DONOR)',
     '            launcher.ensure_profile(build_root, job["profile"])', "test_t20_fault"),
    ("G57", "T21", "the stage watch",
     '            if deps.stage_digest(stage) != manifests[name].get("digest") and not (out / STOP_FILE).is_file():',
     "            if False:", "test_t21_fault"),
    ("G58", "T21", "the child stops before a leg when STOP.txt exists",
     "        why = stop_seen(out)", "        why = None", "test_t21_fault"),
    ("G59", "T22", "HUNG counts toward the AI-only stop",
     "        if klass in STOP_CLASSES:", "        if klass in (REFUSED, NOT_CLEAN):", "test_t22_fault"),
    ("G60", "T22", "the AI-only stop exits 6",
     '    if result["ai_stop"]:\n        return 6', '    if result["ai_stop"]:\n        return 0', "test_t22_fault"),
    ("G61", "T22", "INFRA neither counts nor resets",
     "        elif klass in RESET_CLASSES:", "        elif klass in (*RESET_CLASSES, INFRA):", "test_t22_control"),
    ("G62", "T23", "an unknown schema_version is refused",
     "    if unknown:\n        raise SchemaRefused(", "    if False:\n        raise SchemaRefused(", "test_t23_fault"),
    ("G63", "T24", "a resumed batch salvages the leg in flight (never re-runs it)",
     '        if args.resume and (job["chain"] in started_any', '        if False and (job["chain"] in started_any',
     "test_t24_fault"),
    ("G64", "T24", "a run_id already written is never written twice",
     '                if old.get("record") == record.get("record") == "leg" and old.get("run_id") == record.get("run_id"):',
     "                if False:", "test_t24_fault"),
    ("G65", "T25", "no launch past the deadline",
     '    if legs and not leg_fits(view["now"], legs[0], view.get("deadline")):', "    if False:", "test_t25_fault"),
    ("G66", "T25", "the deadline margin: <= (exactly the margins launches)",
     '    return deadline is None or now + float(leg["wall"]) + LEG_MARGIN_SECONDS <= deadline',
     '    return deadline is None or now + float(leg["wall"]) + LEG_MARGIN_SECONDS < deadline', "test_t25_control"),
    ("G67", "T26", "the singles cap",
     '    if view.get("own_running", 0) + view.get("singles_others", 0) + 1 > SINGLES_CAP:', "    if False:",
     "test_t26_fault"),
    ("G68", "T26", "no start while run_regression.py runs",
     '    if view.get("regression"):', "    if False:", "test_t26_fault"),
    ("G69", "T26", "the disk reservation",
     "    if reserve is None or reserve < ABORT_FREE_GB + RESERVE_MARGIN_GB:", "    if False:", "test_t26_fault"),
    ("G70", "T26", "a dependency is a per-job SKIP, never a WAIT",
     '        if state == "skip":\n            return SKIP,', '        if state == "skip":\n            return WAIT,',
     "test_t26_control"),
    ("G71", "T27", "an A1 leg never stops on the world SIZE (only continue_after's C3 does)",
     '        go, why = continue_rule(row, klass, stop_now, carries_goals=job.get("goals", "carry") == "carry")',
     "        go, why = lc_go, lc_why", "test_t27_fault"),
    ("G72", "T33", "an MC job decides by continue_after itself",
     "    if mc:\n        go, why = lc_go, lc_why", "    if False:\n        go, why = lc_go, lc_why", "test_t33_fault"),
    ("G73", "T29", "a mutant's anchor must hit exactly once",
     "    if hits != 1:", "    if hits < 1:", "test_t29_fault"),
    ("G74", "T30", "the copied personalities equal the AI's",
     'PERSONALITIES = ("Catcher", "Story", "Trainer")', 'PERSONALITIES = ("Catcher", "Story", "Trainer", "Hiker")',
     "test_t30_control"),
    ("G75", "T31", "the LOOP bar: >= 40 (40 crossings key LOOP)",
     '    if loop["crossings"] - loop["crossings_raise"] < LOOP_MIN_CROSSINGS:',
     '    if loop["crossings"] - loop["crossings_raise"] <= LOOP_MIN_CROSSINGS:', "test_t31_control"),
    ("G76", "T31", "the end rule: <= 120,000 (exactly 120,000 keys LOOP)",
     '    near = isinstance(loop.get("last_to_end"), int) and loop["last_to_end"] <= LOOP_END_FRAMES',
     '    near = isinstance(loop.get("last_to_end"), int) and loop["last_to_end"] < LOOP_END_FRAMES', "test_t31_control"),
    ("G77", "T31", "warps count as crossings (KI-128's blind spot)",
     "        if a == b:\n            continue", '        if a == b or item[3] == "warp":\n            continue', "test_t31_fault"),
    ("G78", "T31", "crossings made during an active raise are excluded",
     '    if loop["crossings"] - loop["crossings_raise"] < LOOP_MIN_CROSSINGS:',
     '    if loop["crossings"] < LOOP_MIN_CROSSINGS:', "test_t31_control"),
    ("G79", "T36", "the raise comes first: an ACTIVE raise never keys LOOP",
     '    if end_ok and near and not loop.get("raise_active_at_end"):', "    if end_ok and near:", "test_t36_fault"),
    ("G80", "T31", "a reached leg is never LOOP",
     '    if reached or not loop or not loop.get("pair"):', '    if not loop or not loop.get("pair"):', "test_t31_control"),
    ("G81", "T31", "LOOP only at an end where time or space ran out (never a discrete end)",
     "    end_ok = klass in (CLEAN_BUDGET, CUT_WORLD) or", "    end_ok = True or", "test_t31_control"),
    ("G82", "T31", "a CUT-WORLD leg on the pair joins the LOOP key",
     "    end_ok = klass in (CLEAN_BUDGET, CUT_WORLD) or", "    end_ok = klass in (CLEAN_BUDGET,) or", "test_t31_fault"),
    ("G83", "T32", "goal custody: the carried snapshot's sha256",
     '        if not given or now is None or now != start.get("goals_sha256"):', "        if False:", "test_t32_fault"),
    ("G84", "T32", "an MC job never names AI_PLAYER_GOALS",
     "    if mc and ENV_GOALS in (env or {}):", "    if False:", "test_t32_fault"),
    ("G85", "T33", "an MC job's world cut is live_chain's (never A1's 1 GB)",
     "    return LC.GUARD_WORLD_BYTES if mc else WORLD_CUT_BYTES", "    return WORLD_CUT_BYTES", "test_t33_fault"),
    ("G86", "T33", "an MC seed lies in 6701-6799",
     '            if not MC_SEEDS[0] <= int(job.get("seed") or 0) <= MC_SEEDS[1]:', "            if False:", "test_t33_fault"),
    ("G87", "T34", "a dependency job waits for its source (never launched before)",
     "    if not dep:\n        return None", "    if True:\n        return None", "test_t34_fault"),
    ("G88", "T34", "the fallback only once the source chain ENDED",
     "    if source in ended or missed:", "    if True:", "test_t34_fault"),
    ("G89", "T34", "a fallback start is labelled fallback_for",
     'stage_start(stage_dir, manifest, start_id, fallback["for"])', "stage_start(stage_dir, manifest, start_id, None)",
     "test_t34_fault"),
    ("G90", "T35", "only a tile of the snapshot's tried_items is an item errand",
     "    inside = [tile for tile in tiles if tile is not None and tile in tried]",
     "    inside = [tile for tile in tiles if tile is not None]", "test_t35_fault"),
    ("G91", "T35", "a GOALS-OFF leg (snapshot kept, not carried) is measured, never unknown",
     '    if mode == "none" or tried is None:', '    if mode != "carried" or tried is None:', "test_t35_fault"),
    ("G92", "T36", "the raise reason (budget: a boss-prep raise still active)",
     "        reason = RAISE_TEXT", "        reason = reason", "test_t36_fault"),
    ("G93", "T24", "an exception while the jobs run kills every running child (live_chain's chains-run guard)",
     "        for _job, handle, _ in running:\n            with contextlib.suppress(Exception):\n                handle.kill_tree()",
     "        for _job, handle, _ in []:\n            with contextlib.suppress(Exception):\n                handle.kill_tree()",
     "test_t24_fault"),
    ("G94", "T19", "a leg with no start state or world line is refused before its launch",
     '    for key in ("state", "world"):\n        if not start.get(key):', "    for key in ():\n        if not start.get(key):",
     "test_t19_fault"),
    ("G95", "AM11c", "compare reads the FRAME of a move too (a one-frame split is a difference)",
     '        if (a[i].get("frame"), a[i].get("action")) != (b[i].get("frame"), b[i].get("action")):',
     '        if a[i].get("action") != b[i].get("action"):', "test_am11c_fault"),
    ("G96", "AM11r", "replay refuses an example without its state and world line",
     '    if missing:\n        raise Refusal(f"the example {example} lacks {missing}")',
     '    if False:\n        raise Refusal(f"the example {example} lacks {missing}")', "test_am11r_fault"),
    ("G97", "T2b", "a harness failure while judging a leg is INFRA (salvaged), never a crash of the job",
     "        except Exception as error:  # noqa: BLE001 - the harness failed to judge it: INFRA, never the AI's",
     "        except ZeroDivisionError as error:  # noqa: BLE001 - the harness failed to judge it: INFRA, never the AI's",
     "test_t2b_control"),
    ("G98", "T19", "a job's legs must be the staged milestones' (a plan from another tree is refused)",
     "    refusal = profile_refusal(job, L5.PROFILE, build_root) or legs_refusal(job)",
     "    refusal = profile_refusal(job, L5.PROFILE, build_root)", "test_t19_fault"),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): the verifier's round-1 gaps (2026-11-14,
#: verdict CONDITIONAL_PASS on e71d319d: its own one-edit mutants that NO case caught, reproduced before the fix by the
#: build's fix1_repro, "18 of 18 as predicted"; their names kept, each re-anchored where the fix moved its line) and the
#: round's further guards (V40-V44): each now caught by the FAULT or CONTROL case the round added
_ROUND1 = [
    ("V05", "T14", "the tick cuts an MC job's world by live_chain's own guard, never A1's 1 GB (its call keeps mc)",
     '        if leg is not None and disk_decision(size, None, None, mc=mc) == "cut-world":',
     '        if leg is not None and disk_decision(size, None, None) == "cut-world":', ("test_t14_control", "test_t33_fault")),
    ("V06", "T14", "the tick holds an MC job to its own profile budget, never A1's 1.25 GB (its call keeps mc)",
     '        if leg is not None and disk_decision(None, None, None, held, mc=mc) == "cut-profile":',
     '        if leg is not None and disk_decision(None, None, None, held) == "cut-profile":', ("test_t14_control",)),
    ("V07", "T11", "a stage inside a git work tree is refused (run_refusals' placement call for each stage)",
     '        problems += placement_problems(stage, f"the stage {name}", deps.work_tree)', "        problems += []",
     ("test_t11_fault",)),
    ("V08", "T21", "the stage watch's SANDBOX half (the junctioned modules/ and plugins/ changed: STOP.txt)",
     "            if deps.sandbox_digest(sandbox) != sandbox_marks.get(name) and not (out / STOP_FILE).is_file():",
     "            if False:", ("test_t21_fault",)),
    ("V10", "T25", "the child's own deadline check before every leg (a later leg never launched past --deadline)",
     '        if why is None and not leg_fits(time.time(), leg, job.get("deadline")):', "        if False:",
     ("test_t25_fault",)),
    ("V11", "T25", "the watchdog: a child alive past its job's summed watchdog is killed (then salvaged)",
     '        if now - started > float(job.get("watchdog_seconds") or job_watchdog_seconds(job)) \\',
     '        if False and now - started > float(job.get("watchdog_seconds") or job_watchdog_seconds(job)) \\',
     ("test_t25_fault",)),
    ("V12", "T33", "an MC job's custody is live_chain's own (custody_problems, continue_after's C5)",
     '    row["custody"] = LC.custody_problems(row, prev_row, lc_job, index) if mc else []', '    row["custody"] = []',
     ("test_t33_fault",)),
    ("V13", "T33", "the MC reading reads each leg's continue decision (purity, custody, the world)",
     '            elif not (record.get("continue") or {}).get("go"):', "            elif False:", ("test_t33_fault",)),
    ("V14", "T34", "GM's A/B is dropped as VACUOUS when its source's end holds no discriminating tile",
     '            if not tiles:\n                return "drop", (f"VACUOUS', '            if False:\n                return "drop", (f"VACUOUS',
     ("test_t34_fault",)),
    ("V16", "T18", "C3: a carrying chain's leg that kept no goal snapshot stops the chain",
     '    if carries_goals and not row.get("kept_goals"):', "    if False:", ("test_t18_fault",)),
    ("V20", "T14", "a launch the disk guard's ABORT killed is INFRA (never the AI's NOT CLEAN)",
     '    if guard == "abort":\n        return INFRA,', '    if False:\n        return INFRA,', ("test_t14_fault",)),
    ("V21", "T14", "a launch the world cut killed is CUT-WORLD (its kill marker judged first)",
     '    if guard == "world":\n        return CUT_WORLD,', '    if False:\n        return CUT_WORLD,', ("test_t14_fault",)),
    ("V22", "T14", "a launch the profile budget killed is CUT-WORLD (its kill marker judged first)",
     '    if guard == "profile":\n        return CUT_WORLD,', '    if False:\n        return CUT_WORLD,', ("test_t14_fault",)),
    ("V30", "T34", "a fallback start gives the job that start's OWN starter and starter_from (2.1)",
     '                    if start.get("kind") == "stage":', "                    if False:", ("test_t34_fault",)),
    ("V31", "T34", "a resolved start of ANOTHER persona is never launched (2.2)",
     '                    if start.get("persona") and start["persona"] != job["persona"]:', "                    if False:",
     ("test_t34_fault",)),
    ("V40", "T14", "the tick cuts an MC job's world over live_chain's guard at all",
     '        if leg is not None and disk_decision(size, None, None, mc=mc) == "cut-world":',
     '        if leg is not None and not mc and disk_decision(size, None, None, mc=mc) == "cut-world":', ("test_t14_fault",)),
    ("V41", "T18", "C4: a leg the probe's guard killed stops the chain, by name",
     '    if row.get("guard_killed"):\n        why.append(f"C4', '    if False:\n        why.append(f"C4', ("test_t18_fault",)),
    ("V42", "T25", "the watchdog kills only a child strictly PAST it (exactly at it: kept)",
     '        if now - started > float(job.get("watchdog_seconds") or job_watchdog_seconds(job)) \\',
     '        if now - started >= float(job.get("watchdog_seconds") or job_watchdog_seconds(job)) \\', ("test_t25_control",)),
    ("V43", "T34", "GM's discriminator counts only the maps the next leg starts on or crosses early",
     '        if isinstance(entry, dict) and entry.get("const") in DISCRIMINATOR_MAPS:', "        if isinstance(entry, dict):",
     ("test_t34_fault",)),
    ("V44", "T34", "GM's discriminator counts only tiles the end snapshot tried",
     '                if f"{key}|{xy}" in tried:', "                if True:", ("test_t34_fault",)),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): the verifier's round-2 gaps (2026-11-14, verdict
#: CONDITIONAL_PASS on 3632d5ad, "VERIFIER ROUND 2 MUTANTS: 22 of 22 as predicted"; these seven reproduced as GAPs before
#: the fix by the build's fix2_repro, "8 of 8 as predicted"; names, anchors and replacements verbatim) and the round's own
#: K1-K2 (the known non-ledger allowed and listed): each now caught by the FAULT or CONTROL arm the round added
_ROUND2 = [
    ("V55", "T13", "a seed ledger that cannot be read, and is no known non-ledger, refuses the batch (2.5)",
     '                problems += [f"a ledger could not be read: {item}" for item in unreadable[:8]]',
     "                problems += []", ("test_t13_fault",)),
    ("V56", "T13", "development seeds must be ONE contiguous range (2.5, 3.10)",
     "    if not seeds or seeds != list(range(seeds[0], seeds[-1] + 1)):", "    if not seeds:", ("test_t13_fault",)),
    ("V69", "T14", "a pending job is DROPPED once the tick found --out over its cap (2.7, 3.13)",
     '("out_over", f"--out is over its cap', '("out_over_never", f"--out is over its cap', ("test_t14_fault",)),
    ("V70", "T14", "a pending job is DROPPED once the disk guard ABORTED the batch (2.7: no launch)",
     '("abort", "ABORT.txt: the disk guard aborted the batch")',
     '("abort_never", "ABORT.txt: the disk guard aborted the batch")', ("test_t14_fault",)),
    ("V72", "T14", "an ABORTED batch exits 3 (3.2)",
     '    if result["aborted"]:\n        return 3', '    if False:\n        return 3', ("test_t14_fault",)),
    ("V73", "T14", "an ABORTED batch's entry is finished ABORTED (2.7, 3.10)",
     '    if result["aborted"]:\n        return f"ABORTED', '    if False:\n        return f"ABORTED', ("test_t14_fault",)),
    ("V74", "T14", "a harness error after ledger.begin finishes the entry as ERROR (exit 4's ledger half, 3.2)",
     '        if mode == "development" and entry_id is not None:\n            with contextlib.suppress(Exception):',
     '        if False:\n            with contextlib.suppress(Exception):', ("test_t14_fault",)),
    ("K1", "T13", "a seed ledger that cannot be read at a path ending in the KNOWN non-ledger is allowed (2.5)",
     "            if any(text.endswith(name) for name in KNOWN_NON_LEDGERS):", "            if False:",
     ("test_t13_control",)),
    ("K2", "T13", "a known non-ledger that cannot be read is LISTED (2.5; before the round it was skipped unlisted)",
     "                known.append(item)", "                pass", ("test_t13_control",)),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): the verifier's round-3 gaps (2026-11-14, verdict
#: CONDITIONAL_PASS on a2897998: its one-edit mutants that NO case caught, "failing (0)" or a TIMEOUT; reproduced before the
#: fix by fix round 3, "VERIFIER ROUND 3 RUNNER: 28 of 30" and "6 of 7 as predicted", every gap as the verifier read it;
#: names, anchors and replacements verbatim), the earlier rounds' NITs it re-read (V09, V15, V57-V63; V80 is X4's edit,
#: now caught by T9's and T27's MC lines too), and the round's own guards and CONTROL-side edits (Y01-Y12): each now caught
#: by the FAULT or CONTROL arm fix round 3 added
_ROUND3 = [
    # R3-M1: four guards with no FAULT
    ("W06", "T15", "verify_zip compares the zip's members and sizes with the raw files' (3.12; the REAL verify_zip decides)",
     "    if got != sizes:", "    if False:", ("test_t15_fault",)),
    ("W07", "T15", "verify_zip fails a zip whose testzip() names a member (a damaged CRC; the REAL verify_zip decides)",
     "            if bad is not None:", "            if False:", ("test_t15_fault",)),
    ("W10", "T19", "C5: the start world line's sha256 is the kept line's (3.6)",
     '        if now is None or now != start.get("world_sha256"):', "        if False:", ("test_t19_fault",)),
    ("W35", "T12", "run_batch refuses a --trainer batch with a seed outside the band or no band row (trainer_problems wired)",
     '            problems += trainer_problems([job["seed"] for job in jobs], data)', "            problems += []",
     ("test_t12_fault",)),
    ("W61", "T31", "the loop measure counts only the leg's own transitions, newer than the start truth's frame (3.8)",
     "                and item[0] > start):", "                ):", ("test_t31_fault",)),
    # R3-M2: the WAIT bound, whose removal HUNG T26 (now a FAIL past the suite's pass limit)
    ("W12", "T26", "a WAIT past --max-wait is DROPPED (3.13)",
     '        if view.get("waited", 0.0) >= view.get("max_wait", MAX_WAIT_SECONDS):', "        if False:",
     ("test_t26_fault",)),
    ("W41", "T26", "drive's WAIT clock advances (a WAIT can pass --max-wait)",
     '                    waited[job["chain"]] = waited.get(job["chain"], 0.0) + delta',
     '                    waited[job["chain"]] = waited.get(job["chain"], 0.0) + 0.0', ("test_t26_fault",)),
    # R3-M3: a DEVELOPMENT resume
    ("W15", "T24d", "seeds_named skips a resumed development batch's OWN entry (its --resume runs)",
     '                if (norm, entry["id"]) in ignored:', "                if False:", ("test_t24d_control",)),
    # R3-M4: record and report rules read through run_job, judge_leg and build_report
    ("W16", "T31", "judge_leg marks a reached leg's churn (3.8's churn rule, the module's own)",
     '        loop["churn"] = reached and loop["crossings"] - loop["crossings_raise"] >= LOOP_MIN_CROSSINGS',
     '        loop["churn"] = False', ("test_t31_control",)),
    ("W17", "T31", "the report's churn table lists a churn leg",
     '                      for r in group if ((r.get("measures") or {}).get("loop") or {}).get("churn")]}',
     "                      for r in group if False]}", ("test_t31_control",)),
    ("W47", "T32", "start_memory.losses_carried is the carried snapshot's loss count (3.7)",
     '                        "losses_carried": losses_of(start["snapshot"]) if start["carry"] else 0,',
     '                        "losses_carried": 0,', ("test_t32_control",)),
    ("W60", "T7", "a CUT-WORLD or HUNG leg's end map is the kept world tail's (3.5; the key's end map)",
     '    if klass not in (CUT_WORLD, HUNG) and isinstance((after or {}).get("map"), list) and len(after["map"]) == 2:',
     '    if isinstance((after or {}).get("map"), list) and len(after["map"]) == 2:', ("test_t7_fault",)),
    # N1: refusals and checks with no FAULT
    ("W11", "T32", "C5 refuses AI_PLAYER_GOALS on a leg that carries no snapshot",
     "    elif ENV_GOALS in env:", "    elif False:", ("test_t32_fault",)),
    ("W36", "T11", "run refuses a job whose stage is not given",
     '        if job.get("stage") not in stages:', "        if False:", ("test_t11_fault",)),
    ("W37", "T24", "--resume is refused while a child of this --out still runs",
     "        if alive:", "        if False:", ("test_t24_fault",)),
    ("W38", "T13", "development mode needs --prediction-file",
     "            if not args.prediction_file:", "            if False:", ("test_t13_fault",)),
    ("W62", "T21", "the orchestrator DROPs a pending job on STOP.txt (the child checks it again)",
     '("stop", "STOP.txt: the code under test changed mid-batch")',
     '("stop_never", "STOP.txt: the code under test changed mid-batch")', ("test_t21_fault",)),
    ("W50", "T26", "the disk reservation WAITs only UNDER 40 + 2.0 GB (exactly 42.0 GB: GO)",
     "    if reserve is None or reserve < ABORT_FREE_GB + RESERVE_MARGIN_GB:",
     "    if reserve is None or reserve <= ABORT_FREE_GB + RESERVE_MARGIN_GB:", ("test_t26_control",)),
    # N2: values checked only as constants
    ("W14", "T33", "an MC batch runs at most P = 3 at once (at run time, on a batch where it binds)",
     "        parallel = min(parallel, MC_PARALLEL)", "        parallel = parallel", ("test_t33_control",)),
    ("W31", "T33", "an MC job's profile budget is live_chain.GUARD_WORLD_BYTES + 250,000,000, READ (never copied)",
     "    return LC.GUARD_WORLD_BYTES + MC_PROFILE_MARGIN_BYTES if mc else PROFILE_BUDGET_BYTES",
     "    return 1_750_000_000 if mc else PROFILE_BUDGET_BYTES", ("test_t33_control",)),
    # N3: report and record fields no case asserted
    ("W49", "T8", "the reach split by start kind names 'chain leg with a goal snapshot' (3.8)",
     "        return START_KINDS[1] if carried else START_KINDS[2]", "        return START_KINDS[2]", ("test_t8_fault",)),
    ("W18", "T31", "the report's 'loops seen' table lists a flagged leg (3.8: never hidden)",
     '                           for r in group if ((r.get("measures") or {}).get("loop") or {}).get("keyed") == "flag"],',
     "                           for r in group if False],", ("test_t31_fault",)),
    ("W51", "T36", "the report gives a chapter 6-7 key its boss-prep breakdown (3.8)",
     "            if isinstance(chapter, int) and chapter >= 6:", "            if False:", ("test_t36_fault",)),
    ("W48", "T34", "a leg's start_memory.fallback_for names the pair its fallback start stands in for (3.7)",
     '                        "fallback_for": start.get("fallback_for")}', '                        "fallback_for": None}',
     ("test_t34_fault",)),
    ("W64", "T16", "experience is written only for CLEAN-* legs (3.5's Exp column)",
     "    if klass in CLEAN_CLASSES and world is not None:", "    if world is not None:", ("test_t16_fault",)),
    ("W68", "T16", "rides_delta reports a ride used in the leg, by its delta against the start's line (3.7)",
     "        if delta > 0:", "        if False:", ("test_t16_fault",)),
    ("W69", "T36", "bossprep_fields reads a raise that ended by its budget (3.7 raise_end)",
     '    elif any("the raise ends, budget spent" in line for line in texts):', "    elif False:", ("test_t36_fault",)),
    ("W32", "T34", "a fallback takes the persona's start of the job's SLOT (2.1)",
     '        start_id = ids[int(fallback.get("slot", 0)) % len(ids)]', "        start_id = ids[0]", ("test_t34_fault",)),
    # N7: the earlier rounds' NITs (V09 and V15 of round 1, V57-V63 of round 2; V80 is X4's edit)
    ("V09", "AM11r", "replay sanitizes the environment before its launch (3.11)",
     "    sanitize_environ()\n    from ai_player.gates import live_step5 as L5\n\n    example = Path(example).resolve()",
     "    from ai_player.gates import live_step5 as L5\n\n    example = Path(example).resolve()", ("test_am11r_fault",)),
    ("V15", "T9", "the orchestrator's child_env strips AI_PLAYER_*, POKEBOT_* and refused PYTHON* (3.11)",
     "           if not (k.upper().startswith(STRIPPED_PREFIXES) or LC.python_env_refused(k))}", "           if True}",
     ("test_t9_fault",)),
    ("V57", "T24", "a non-empty --out is refused without --resume",
     "    if not args.resume and out.exists() and any(out.iterdir()):", "    if False:", ("test_t24_fault",)),
    ("V58", "T24", "--resume with another jobs.json than the batch's is refused",
     '    if isinstance(old, dict) and old.get("jobs_sha256") != hashlib.sha256(jobs_raw).hexdigest():', "    if False:",
     ("test_t24_fault",)),
    ("V59", "T33", "an MC job whose goal policy is not 'never' is refused (plan and run)",
     '            if job.get("goals") != "never":', "            if False:", ("test_t33_fault",)),
    ("V60", "T24", "a job id given twice is refused (plan and run; a run_id is keyed by it)",
     "        if name in seen:", "        if False:", ("test_t24_fault",)),
    ("V61", "T20", "a profile that is not a probe profile the launcher accepts is refused (plan and run)",
     "        if not launcher._PROFILE_NAME_RE.match(profile) or not profile.startswith(PROFILE_PREFIX):", "        if False:",
     ("test_t20_fault",)),
    ("V62", "T34", "drive's dependency hang guard: pending jobs that can never resolve while nothing runs are DROPPED",
     "            if pending and idle_at_start and not launched and not running and skipped == len(pending):",
     "            if False:", ("test_t34_fault",)),
    ("V63", "T20", "a leftover profile (it exists before the job) is refused by the child, never launched in",
     '    if (Path(build_root) / "profiles" / name).exists():', "    if False:", ("test_t20_fault",)),
    ("V80", "T33", "an MC chain never sends AI_PLAYER_GOALS (X4's edit: the job's goal policy ignored), seen by T9's and "
                   "T27's MC lines too (non-fresh L2s since round 3)",
     '    out["carry"] = has and policy == "carry"', '    out["carry"] = has',
     ("test_t33_control", "test_t9_control", "test_t27_control")),
    # the round's own guards (N4, N7) and CONTROL-side edits
    ("Y01", "T11", "an EMPTY job list is refused before --out is made (N4: it crashed after the mkdir, exit 5)",
     "    if not jobs:\n        # an EMPTY list", "    if False:\n        # an EMPTY list", ("test_t11_fault",)),
    ("Y02", "T11", "--out and stages never at or under the graded chapter 1-5 folder (3.14)",
     "    if at_or_under(resolved, Path(GRADED_CH5)):", "    if False:", ("test_t11_fault",)),
    ("Y03", "AM11r", "replay of an MC example never sends its kept goal snapshot (2.4b)",
     '    if (example / "goals_last.jsonl").is_file() and not job.get("mc"):',
     '    if (example / "goals_last.jsonl").is_file():', ("test_am11r_fault",)),
    ("Y04", "T33", "an MC batch's ledger verdict names the merge check's reading, PASS or STOP (2.4b)",
     '    reading = ""\n    if mc:', '    reading = ""\n    if False:', ("test_t33_fault", "test_t33_control")),
    ("Y05", "T24d", "a resume skips ONLY the batch's own entry (another entry naming its seeds still refuses)",
     '                if (norm, entry["id"]) in ignored:', "                if ignored:", ("test_t24d_fault",)),
    ("Y06", "T32", "losses_carried is 0 when the snapshot is not carried (a GOALS-OFF leg)",
     '                        "losses_carried": losses_of(start["snapshot"]) if start["carry"] else 0,',
     '                        "losses_carried": losses_of(start["snapshot"]),', ("test_t32_fault",)),
    ("Y07", "T7", "every class but CUT-WORLD and HUNG reads the END TRUTH's map (a CLEAN leg's end map)",
     '    if klass not in (CUT_WORLD, HUNG) and isinstance((after or {}).get("map"), list) and len(after["map"]) == 2:',
     "    if False:", ("test_t7_control",)),
    ("Y08", "T16", "a CLEAN leg writes its experience row",
     "    if klass in CLEAN_CLASSES and world is not None:", "    if False:", ("test_t16_control",)),
    ("Y09", "T36", "a chapter 1-5 key carries no boss-prep breakdown",
     "            if isinstance(chapter, int) and chapter >= 6:", "            if True:", ("test_t36_control",)),
    ("Y10", "T8", "a GOALS-OFF chain leg is 'chain leg without', never 'with a goal snapshot'",
     "        return START_KINDS[1] if carried else START_KINDS[2]", "        return START_KINDS[1]", ("test_t8_control",)),
    ("Y11", "T24", "--resume is refused only for a child of THIS --out (another batch's child never blocks it)",
     '" child " in f" {c} " and str(out) in c]', '" child " in f" {c} "]', ("test_t24_control",)),
    ("Y12", "T11", "the graded-folder check is a PATH check (a sibling whose name begins with the folder's is accepted)",
     r'    return a == b or a.startswith(b.rstrip("\\/") + os.sep)', r'    return a == b or a.startswith(b.rstrip("\\/"))',
     ("test_t11_control",)),
    # fix round 3's BOUNDED SWEEP (N6: the README says what remains): the decision lines of the refusal family no row
    # edited (run_refusals, run_batch, parse_stages, start_refusal, manifest_problems, jobs_problems, seeds_named,
    # trainer_problems, dependency_of, start_check, profile_refusal, legs_refusal, continue_rule, replay), each a guard
    # now shown to FAIL its FAULT with the guard removed (Z01-Z08 on FAULT arms that were there, Z09-Z26 on new ones)
    ("Z01", "T11", "a stage whose manifest's repo or sandbox lies in a pokebot-learner folder is refused",
     '            if target and "pokebot-learner" in (part.lower() for part in Path(target).parts):', "            if False:",
     ("test_t11_fault",)),
    ("Z02", "T11", "a stage with no valid manifest.json is refused",
     '    if not isinstance(data, dict):\n        return None, [f"{stage}: no valid manifest.json"]',
     '    if False:\n        return None, [f"{stage}: no valid manifest.json"]', ("test_t11_fault",)),
    ("Z03", "T19", "a job's legs must equal the ones the staged milestones give (the comparison itself)",
     "    if got != [{k: leg.get(k) for k in fields} for leg in want]:", "    if False:", ("test_t19_fault",)),
    ("Z04", "AM11r", "replay refuses a profile that already exists (a replay plays in a NEW profile)",
     '    if (build / "profiles" / profile).exists():', "    if False:", ("test_am11r_fault",)),
    ("Z05", "T13", "a development seed range overlapping an entry's is a hit (the overlap test itself)",
     '                if entry["first"] <= last and first <= entry["last"]:', "                if False:", ("test_t13_fault",)),
    ("Z06", "T12", "a trainer seed outside the band is a problem (the band test itself)",
     "                if not TRAINER_BAND[0] <= s <= TRAINER_BAND[1]]", "                if False]", ("test_t12_fault",)),
    ("Z07", "T12", "a registered entry overlapping the trainer's seeds is a problem",
     '            if entry.get("status") == "registered" and entry.get("first", 0) <= seeds[-1] and seeds[0] <= '
     'entry.get("last", -1):', "            if False:", ("test_t12_fault",)),
    ("Z08", "T11", "run_batch's refusal gate: any problem refuses the batch (exit 2) before any launch",
     '    if problems:\n        for problem in problems:\n            print(f"REFUSED: {problem}", flush=True)\n        return 2',
     '    if False:\n        for problem in problems:\n            print(f"REFUSED: {problem}", flush=True)\n        return 2',
     ("test_t11_fault",)),
    ("Z09", "T11", "a --stage not in the ARM=DIR form is refused (its own text; the stage it would name has no manifest)",
     "        if not name.strip() or not folder.strip():", "        if False:", ("test_t11_fault",)),
    ("Z10", "T14", "a free space that cannot be read refuses the start (never compared as a number)",
     '    if free_gb is None:\n        return "the free space could not be read"',
     '    if False:\n        return "the free space could not be read"', ("test_t14_fault",)),
    ("Z11", "T11", "a --jobs file that is not a JSON list of jobs is refused",
     '    if jobs is None:\n        return ["--jobs is not a JSON list of jobs"]',
     '    if False:\n        return ["--jobs is not a JSON list of jobs"]', ("test_t11_fault",)),
    ("Z12", "T24", "--resume on an --out that holds no batch.json is refused",
     "    if args.resume and not (out / BATCH_FILE).is_file():", "    if False:", ("test_t24_fault",)),
    ("Z13", "T13", "an empty prediction file is refused (development mode)",
     '                    if not prediction_raw.decode("utf-8").strip():', "                    if False:",
     ("test_t13_fault",)),
    ("Z14", "T9", "a job with no legs is refused (plan and run)",
     '        if not job.get("legs"):\n            problems.append(f"{name}: no legs")',
     '        if False:\n            problems.append(f"{name}: no legs")', ("test_t9_fault",)),
    ("Z15", "T34", "a reached source whose kept files are not all recorded is DROPPED, never started from",
     '        if start is None:\n            return "drop", f"the source {source} {leg}\'s kept files are not all recorded"',
     '        if False:\n            return "drop", f"the source {source} {leg}\'s kept files are not all recorded"',
     ("test_t34_fault",)),
    ("Z16", "T34", "a job with no fallback whose source chain ENDED without a reached L5 is DROPPED",
     "        if not fallback:", "        if False:", ("test_t34_fault",)),
    ("Z17", "T34", "a missed chain's fallback start that is not on the stage is DROPPED",
     '        if start is None:\n            return "drop", f"its source chain {source} missed',
     '        if False:\n            return "drop", f"its source chain {source} missed', ("test_t34_fault",)),
    ("Z18", "T34", "start_check DROPs a job whose dependency can never be met (drive's half)",
     '        if state == "drop":\n            return DROP, str(info)', '        if False:\n            return DROP, str(info)',
     ("test_t34_fault",)),
    ("Z19", "T20", "the child refuses a job whose profile is not a probe profile",
     "    if not name.startswith(PROFILE_PREFIX) or name == DONOR:\n        return f\"the job's profile",
     "    if False:\n        return f\"the job's profile", ("test_t20_fault",)),
    ("Z20", "T20", "the child refuses when live_step5.PROFILE is not its job's",
     "    if profile != name:", "    if False:", ("test_t20_fault",)),
    ("Z21", "AM11r", "replay refuses a folder no leg record keeps",
     '    if record is None:\n        raise Refusal(f"no leg record in', '    if False:\n        raise Refusal(f"no leg record in',
     ("test_am11r_fault",)),
    ("Z22", "AM11r", "replay refuses a profile that is not a probe profile",
     "    if not profile.startswith(PROFILE_PREFIX) or profile == DONOR:\n        raise Refusal(f\"the replay's profile",
     "    if False:\n        raise Refusal(f\"the replay's profile", ("test_am11r_fault",)),
    ("Z23", "T14", "a STAGE's drive under 45 GB refuses the start (the --out's drive above it)",
     "        refusal = start_refusal(free)\n        if refusal:\n            problems.append(f\"the stage {name}'s drive: {refusal}\")",
     "        refusal = start_refusal(free)\n        if False:\n            problems.append(f\"the stage {name}'s drive: {refusal}\")",
     ("test_t14_fault",)),
    ("Z24", "T14", "--out's drive under 45 GB refuses the start (the stage's drive above it)",
     "    refusal = start_refusal(free)\n    if refusal:\n        problems.append(f\"--out's drive: {refusal}\")",
     "    refusal = start_refusal(free)\n    if False:\n        problems.append(f\"--out's drive: {refusal}\")",
     ("test_t14_fault",)),
    ("Z26", "T11", "a stage manifest that lacks a key or is of another schema is refused",
     '    if missing or data.get("schema_version") != SCHEMA_VERSION:', "    if False:", ("test_t11_fault",)),
    ("Z27", "T13", "run_batch refuses development seeds that are not ONE contiguous range (seed_span's wiring)",
     '            if span is None:\n                problems.append("development seeds must be ONE contiguous range")',
     '            if False:\n                problems.append("development seeds must be ONE contiguous range")',
     ("test_t13_fault",)),
    ("Z28", "T24d", "a resumed batch skips its OWN ledger entry and keeps it (the resume's wiring of seeds_named's ignore)",
     '                if isinstance(old, dict) and old.get("entry_id") is not None:', "                if False:",
     ("test_t24d_control",)),
    ("Z29", "T10", "the trainer writes no evidence and finishes no entry (the batch's end, development only)",
     '        if mode == "development":\n            evidence = write_evidence(',
     '        if True:\n            evidence = write_evidence(', ("test_t10_fault",)),
    ("Z30", "T24", "a Ctrl+C (a BaseException that is no Exception) still ends the batch, after its entry is finished",
     "        if not isinstance(error, Exception):\n            raise\n        return 4",
     "        if False:\n            raise\n        return 4", ("test_t24_fault",)),
    ("Z31", "T34", "a REACHED source chain's L5 end is the dependency's start (ready)",
     '    if record is not None and record.get("reached"):', "    if False:", ("test_t34_control",)),
    ("Z32", "T21", "start_check DROPs every pending job on STOP.txt, ABORT.txt, the AI-only stop and the --out cap",
     "        if view.get(flag):\n            return DROP, why", "        if False:\n            return DROP, why",
     ("test_t21_fault", "test_t14_fault")),
    ("Z33", "T26", "start_check WAITs a job while a reason holds (the singles cap, a lane, the reservation)",
     '    if reasons:\n        if view.get("waited", 0.0)', '    if False:\n        if view.get("waited", 0.0)',
     ("test_t26_fault",)),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): the verifier's round-4 gaps (2026-11-15, verdict
#: CONDITIONAL_PASS on bf75965a: two one-edit mutants of its bounded hunt, beside fix round 3's new arms, that NO case
#: caught, "failing (0)"; reproduced before the fix by fix round 4, "VERIFIER ROUND 3 RUNNER: 11 of 11 as predicted", both
#: gaps as the verifier read them; names, anchors and replacements verbatim) and the OTHER half of each rule they split
#: (U01, U02): H07 and H09 now caught by the FAULT arm fix round 4 added, U01 and U02 by the arm that was there
_ROUND4 = [
    # V4-M1: seeds_named's resume skip is keyed by the pair (ledger path, entry id); H07 drops the path half, U02 the id half
    ("H07", "T24d", "a resume skips its own entry only IN ITS OWN LEDGER (a divergent copy's entry of the same id naming its "
                    "seeds still refuses)",
     '                if (norm, entry["id"]) in ignored:', '                if entry["id"] in {i for _, i in ignored}:',
     ("test_t24d_fault",)),
    ("U02", "T24d", "a resume skips only its own entry's ID in its own ledger (another entry of that ledger naming its seeds "
                    "still refuses)",
     '                if (norm, entry["id"]) in ignored:', "                if norm in {p for p, _ in ignored}:",
     ("test_t24d_fault",)),
    # V4-M2: end_map_of's tail rule names two classes; H09 drops CUT_WORLD, U01 drops HUNG (W60 drops both)
    ("H09", "T7", "a CUT-WORLD leg's end map is the kept world tail's (3.5; CUT_WORLD's half of the rule alone)",
     "    if klass not in (CUT_WORLD, HUNG) and isinstance(", "    if klass not in (HUNG,) and isinstance(",
     ("test_t7_fault",)),
    ("U01", "T7", "a HUNG leg's end map is the kept world tail's (3.5; HUNG's half of the rule alone)",
     "    if klass not in (CUT_WORLD, HUNG) and isinstance(", "    if klass not in (CUT_WORLD,) and isinstance(",
     ("test_t7_fault",)),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): fix round 5 (2026-11-15, on 615ad99d): the
#: guards it added (`run` refuses --parallel under 1, V4-N3, rated MAJOR by impact: P01-P03; a job's env must be EMPTY:
#: E01-E02) and verifier round 4's two NITs, H02 and H03 (names, anchors and replacements verbatim from its hunt,
#: `_ai_lab/a1/verify4/v4_hunt.py`; reproduced "failing (0)" on 615ad99d before the fix), each now caught by the arm fix
#: round 5 added to T14 or T33's CONTROL
_ROUND5 = [
    ("P01", "T37", "run refuses --parallel under 1 (P 0 admits no job: the scheduler would never end)",
     "    if int(args.parallel) < 1:", "    if False:", ("test_t37_fault",)),
    ("P02", "T37", "the --parallel bound is 1, not 0 (--parallel 0 refused, not only a negative P)",
     "    if int(args.parallel) < 1:", "    if int(args.parallel) < 0:", ("test_t37_fault",)),
    ("P03", "T37", "the --parallel bound is 1, not 2 (--parallel 1 runs: the refusal's other side)",
     "    if int(args.parallel) < 1:", "    if int(args.parallel) < 2:", ("test_t37_control",)),
    ("E01", "T38", "plan and run refuse an ALLOWED key in a job's env (it is never sent: the probe sets every key itself)",
     "if k in ENV_ALLOWED)", "if k in ENV_ALLOWED and False)", ("test_t38_fault",)),
    ("E02", "T38", "a job's env refuses EVERY allowed key, not only AI_PLAYER_TARGET",
     "if k in ENV_ALLOWED)", "if k == ENV_TARGET)", ("test_t38_fault",)),
    ("H02", "T14", "an ABORTED MC batch's ledger verdict names the merge check's reading (verifier round 4's V4-N1)",
     "GB free): {reading}{legs} legs ran", "GB free): {legs} legs ran", ("test_t14_fault",)),
    ("H03", "T33", "an MC verdict names the batch's own chain count, not a fixed 3 (verifier round 4's V4-N2)",
     "f\"{mc['chains']} chains{", "f\"3 chains{", ("test_t33_control",)),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): fix round 6 (2026-11-15, on b19b11f9): the
#: merge check counts every PLANNED MC chain, so a job DROPPED before its launch reads STOP (verifier round 6's V6-1,
#: MAJOR: it read "PASS over 2 chains" with a third planned chain never run; D01-D06), and T37's --parallel refusal is
#: asserted in development mode and on --resume (V6-2; V6M2 and V6M3, names, anchors and replacements verbatim from
#: `_ai_lab/a1/verify6/v6_hunt.py`, reproduced "failing (0)" on b19b11f9 before the fix; P04 its control side)
_ROUND6 = [
    ("D01", "T33", "the merge check's chains include every PLANNED MC chain (a dropped one among them)",
     "    ids = sorted(set(by_job) | set(jobs) | set(planned_jobs))", "    ids = sorted(set(by_job) | set(jobs))",
     ("test_t33_fault",)),
    ("D02", "T33", "the merge check's chain count is the planned one, not the started one",
     "\"chains\": len(ids),", "\"chains\": len(set(by_job) | set(jobs)),", ("test_t33_fault",)),
    ("D03", "T33", "run writes every planned MC chain and its legs into batch.json (mc_planned)",
     "\"mc_planned\": {job[\"chain\"]: [leg[\"leg\"] for leg in job.get(\"legs\") or []] for job in jobs if job.get(\"mc\")}}",
     "\"mc_planned\": {}}", ("test_t33_fault", "test_t33_control")),
    ("D04", "T33", "the report hands batch.json's plan to the merge check",
     "\"mc\": mc_reading(records, batch.get(\"mc_planned\") if isinstance(batch, dict) else None)}",
     "\"mc\": mc_reading(records)}", ("test_t33_fault",)),
    ("D05", "T33", "an MC batch whose every planned job was dropped reads STOP, never None",
     "    if not legs and not jobs and not planned_jobs:", "    if not legs and not jobs:", ("test_t33_fault",)),
    ("D06", "T33", "a planned MC job that RAN (a leg, no job record) is never called DROPPED",
     "        if not members and job_id not in jobs:", "        if job_id not in jobs:", ("test_t33_control",)),
    ("V6M2", "T37", "the --parallel refusal is not skipped on --resume (verifier round 6's V6M2)",
     "    if int(args.parallel) < 1:", "    if int(args.parallel) < 1 and not args.resume:", ("test_t37_fault",)),
    ("V6M3", "T37", "the --parallel refusal is not a trainer-only one (verifier round 6's V6M3)",
     "    if int(args.parallel) < 1:", "    if int(args.parallel) < 1 and mode == \"trainer\":", ("test_t37_fault",)),
    ("P04", "T37", "a --resume at --parallel 1 carries no --parallel refusal (the refusal's other side on --resume)",
     "    if int(args.parallel) < 1:", "    if int(args.parallel) < 1 or args.resume:", ("test_t37_control",)),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): the lead's closing row (2026-11-15, on
#: 196882fa): verifier round 6's NIT V6-3 (V6M1: its name, and the same edit as `_ai_lab/a1/verify6/v6_hunt.py`'s, here
#: anchored on E01's anchor; it read "failing (0)" on 196882fa in verifier round 7), now caught by T38's MC arm
_ROUND7 = [
    ("V6M1", "T38", "a job's env must be EMPTY on an MC job too (verifier round 6's V6M1)",
     "if k in ENV_ALLOWED)", "if k in ENV_ALLOWED and not job.get(\"mc\"))", ("test_t38_fault",)),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): build plan step 5 (2026-11-15, on a999429f), the
#: planted walls (`MUTANTS`, 4.3 P1 and P2) and their offline planner tests T39 and T40: each wall's edit broken (its
#: wall does nothing, sits on the wrong map or door, or misses a side) or `apply_mutant` made to touch more than the staged
#: copy's one edit. The anchors are in `MUTANTS`' own text (the replacement strings as frontier_probe.py spells them)
_ROUND8 = [
    ("WL1", "T39", "WALL-OLDALE's walled step is refused (its `return None`)",
     r'"        return None\n"' + "\n" + r'            "    if nxt in walls:\n"',
     r'"        pass\n"' + "\n" + r'            "    if nxt in walls:\n"', ("test_t39_fault",)),
    ("WL2", "T39", "WALL-OLDALE walls OLDALE_TOWN itself (not another map)",
     '_OLDALE = "OLDALE_TOWN"', '_OLDALE = "LITTLEROOT_TOWN"', ("test_t39_fault",)),
    ("WL3", "T39", "WALL-OLDALE walls every side maps.json connects into OLDALE (ROUTE103's down side among them)",
     '_OLDALE_INTO = {"ROUTE101": "up", "ROUTE102": "right", "ROUTE103": "down"}',
     '_OLDALE_INTO = {"ROUTE101": "up", "ROUTE102": "right"}', ("test_t39_fault",)),
    ("WL4", "T39", "WALL-OLDALE walls past ROUTE101's up edge before any crossing (y < 0: a New Game's first way in)",
     r' or (side == \"up\" and nxt[1] < 0)', "", ("test_t39_fault",)),
    ("WL5", "T40", "WALL-BRINEY's walled door has no stand tile (its `return []`)",
     r'"        return []\n"', r'"        pass\n"', ("test_t40_fault",)),
    ("WL6", "T40", "WALL-BRINEY walls the door maps.json leads into the cottage (not the tile below it)",
     '_BRINEY_DOORS = (("ROUTE104", 17, 50),)', '_BRINEY_DOORS = (("ROUTE104", 17, 51),)', ("test_t40_fault",)),
    ("WL7", "T39/T40", "a staged copy differs from the real one by EXACTLY the wall's edit (apply_mutant adds nothing)",
     '    path.write_bytes(raw.replace(anchor, new, 1).encode("utf-8"))',
     '    path.write_bytes((raw.replace(anchor, new, 1) + "\\n").encode("utf-8"))', ("test_t39_fault", "test_t40_fault")),
    ("WL8", "T39/T40", "apply_mutant edits the STAGED copy, never the source tree",
     '    path = Path(code_root) / mutant["file"]', '    path = REPO / mutant["file"]',
     ("test_t39_fault", "test_t39_control", "test_t40_fault", "test_t40_control")),
]

#: (name, T, the guard, anchor, replacement, the tests predicted to fail): fix round 7 (2026-11-16, on dc643cd0), found by
#: the first live run: `python_processes()` lists python.exe ONLY, so its own PowerShell query is never returned (PQ1: the
#: filter removed, the query returns itself and a `py` launch twice), never only the launcher image (PQ2: the planted
#: interpreters are missed) and never the launcher too (PQ3: a `py` launch of pokebot.py counted twice by singles_of).
#: T41 runs the REAL query on the REAL process table with planted sleeper processes (no stub)
_ROUND9 = [
    ("PQ1", "T41", "python_processes() lists python.exe only, so its own PowerShell query is never returned",
     " -Filter \\\"Name='python.exe'\\\" | Where-Object", " | Where-Object", ("test_t41_control", "test_t41_fault")),
    ("PQ2", "T41", "python_processes() lists the interpreter (python.exe), not the `py` launcher image",
     "-Filter \\\"Name='python.exe'\\\"", "-Filter \\\"Name='py.exe'\\\"", ("test_t41_fault", "test_t41_control")),
    ("PQ3", "T41", "python_processes() lists the interpreter ONLY: a `py` launch is one run, never two",
     "-Filter \\\"Name='python.exe'\\\"", "-Filter \\\"Name='python.exe' OR Name='py.exe'\\\"", ("test_t41_fault",)),
]

#: (name, T, the guard, anchor, replacement, why no test catches it ALONE): fix round 3's sweep found these guards
#: REDUNDANT on every arm the suite can plant, so each is predicted REDUNDANT ALONE (the copy passes every test)
_REDUNDANT = [
    ("Z25", "T18", "C2's CLASS half: a leg of a class other than CLEAN-* stops the chain",
     '    if klass not in CLEAN_CLASSES:\n        why.append(f"C2 the class is {klass}, not CLEAN-*")',
     '    if False:\n        why.append(f"C2 the class is {klass}, not CLEAN-*")',
     "a reached NOT CLEAN leg (T18's arm) fails L5.PURITY_CLEAN too, so C2's PURITY half stops it (measured, "
     "_ai_lab/a1/fix3/z25_probe.py: the real module's reason \"C2 the class is NOT CLEAN, not CLEAN-*; C2 purity not "
     "clean: L5.PURITY_CLEAN FAIL\", Z25's copy \"C2 purity not clean: L5.PURITY_CLEAN FAIL\", both stop)."),
]

#: (name, the rule that is broken, (file, anchor, replacement), the test predicted to fail): the test-side guards (H1-H4,
#: whose guard lives in the suite or in the G-3 scan it calls) and 4.2's named mutants the guard table lacked (X1-X4)
_MORE = [
    ("H1", "T28 test-side guard removed: the suite's AI-import scan (`importers`) never reports a planted "
           "`from ai_player.gates import frontier_probe`",
     (TESTS, '            if any("frontier_probe" in name for name in names):\n                found.append(rel.as_posix())',
      "            if False:\n                found.append(rel.as_posix())"), "test_t28_fault"),
    ("H2", "T28 test-side guard removed: `check_grader_imports.scan` never reports a chain to the AI's code (an AI import "
           "planted in the probe passes the G-3 scan)",
     (G3, '                problems.append(" -> ".join(chain))\n    return sorted(set(problems))',
      "                pass\n    return sorted(set(problems))"), "test_t28_fault"),
    ("H3", "T30 test-side guard removed: the personalities pin always holds (a 4th personality passes it)",
     (TESTS, "    return set(copy_value) == set(ai_value)\n", "    return True\n"), "test_t30_fault"),
    ("H4", "T30 test-side guard removed: the tile-fields pin always holds (reordered fields pass it)",
     (TESTS, "    return list(copy_value) == list(ai_value)\n", "    return True\n"), "test_t30_fault"),
    ("X1", "4.2 (the first draft): a WAIT drops the job (`start_check` returns DROP where the singles cap, a running "
           "run_regression.py or the disk reservation should make it WAIT)",
     (PROBE, '        return WAIT, "; ".join(reasons)', '        return DROP, "; ".join(reasons)'), "test_t26_fault"),
    ("X2", "4.2 (the amendments): a dependency SKIP DROPPED by --max-wait (`drive` gives a SKIPPED job the --max-wait "
           "clock and drops it past it)",
     (PROBE, "                if verdict == SKIP:\n                    skipped += 1\n                    index += 1\n"
             "                    continue\n",
      "                if verdict == SKIP and waited.get(job[\"chain\"], 0.0) >= max_wait:\n"
      "                    pending.pop(index)\n"
      "                    not_started.append((job[\"chain\"], f\"a SKIP past --max-wait ({max_wait:g} s)\"))\n"
      "                    continue\n"
      "                if verdict == SKIP:\n"
      "                    waited[job[\"chain\"]] = waited.get(job[\"chain\"], 0.0) + delta\n"
      "                    skipped += 1\n                    index += 1\n                    continue\n"),
     "test_t26_control"),
    ("X3", "4.2 (the first draft): the resume keyed by seed (a job whose SEED has a leg record counts as started, so P1's "
           "other arm on that seed is salvaged, never run)",
     (PROBE, 'job["chain"] in started_any or',
      'str(job["seed"]) in {str(c).rsplit("-", 1)[-1] for c in started_any} or'), "test_t24_fault"),
    ("X4", "4.2 (the amendments): an MC job sending AI_PLAYER_GOALS (`leg_start` ignores the job's goal policy: every leg "
           "with a kept snapshot carries it, an MC chain's L2 and a GOALS-OFF leg included)",
     (PROBE, '    out["carry"] = has and policy == "carry"', '    out["carry"] = has'), "test_t33_control"),
]

#: name -> (prediction, the rule that is broken, [edits], tests that MUST fail, the suites the copy runs)
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str, str]], list[str], tuple[str, ...]]] = {
    "F0": (CONTROL, "nothing: the unchanged copy", [], [], CONTROL_SUITES),
}
for _name, _tid, _guard, _old, _new, _test in _GUARDS:
    if _name in MUTANTS:
        raise SystemExit(f"revert_frontier: mutant {_name} is defined twice")
    MUTANTS[_name] = (CAUGHT, f"{_tid} guard removed: {_guard}", [(PROBE, _old, _new)], [f"GuardTests.{_test}"],
                      DEFAULT_SUITES)
for _name, _what, _edit, _test in _MORE:
    if _name in MUTANTS:
        raise SystemExit(f"revert_frontier: mutant {_name} is defined twice")
    MUTANTS[_name] = (CAUGHT, _what, [_edit], [f"GuardTests.{_test}"], DEFAULT_SUITES)
for _name, _tid, _guard, _old, _new, _tests in (_ROUND1 + _ROUND2 + _ROUND3 + _ROUND4 + _ROUND5 + _ROUND6 + _ROUND7
                                                + _ROUND8 + _ROUND9):
    if _name in MUTANTS:
        raise SystemExit(f"revert_frontier: mutant {_name} is defined twice")
    MUTANTS[_name] = (CAUGHT, f"{_tid} guard removed: {_guard}", [(PROBE, _old, _new)], [f"GuardTests.{t}" for t in _tests],
                      DEFAULT_SUITES)
for _name, _tid, _guard, _old, _new, _why in _REDUNDANT:
    if _name in MUTANTS:
        raise SystemExit(f"revert_frontier: mutant {_name} is defined twice")
    MUTANTS[_name] = (REDUNDANT, f"{_tid} guard removed: {_guard}", [(PROBE, _old, _new)], _why, DEFAULT_SUITES)

DRIVER = '''
import importlib, json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
suites = json.loads(sys.argv[1])
loader = unittest.defaultTestLoader
tests = unittest.TestSuite()
files = []
for entry in suites:
    name, _, cls = entry.partition(":")
    module = importlib.import_module("ai_player.gates." + name)
    files.append(module.__file__)
    tests.addTests(loader.loadTestsFromTestCase(getattr(module, cls)) if cls else loader.loadTestsFromModule(module))
result = unittest.TextTestRunner(stream=open(root / "unittest.out", "w", encoding="utf-8"), verbosity=2).run(tests)
bad = {t.id().replace("ai_player.gates.", "", 1): kind for kind, items in (("FAIL", result.failures), ("ERROR", result.errors))
       for t, _ in items}
print("RESULT " + json.dumps({"ran": result.testsRun, "bad": bad, "modules": files}))
'''


def make_copy(edits: list[tuple[str, str, str]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ai_player_frontier_mutant_"))
    try:
        shutil.copytree(REPO / "ai_player", root / "ai_player",
                        ignore=shutil.ignore_patterns("__pycache__", "evidence", "*.ss1"))
        (root / FRONTIER[0]).mkdir()
        shutil.copy2(REPO / FRONTIER[0] / FRONTIER[1], root / FRONTIER[0] / FRONTIER[1])
        for relative, old, new in edits:
            path = root / "ai_player" / relative
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise ValueError(f"mutant anchor not unique in {relative} ({text.count(old)} hits): {old[:160]!r}")
            path.write_text(text.replace(old, new), encoding="utf-8")
        (root / "run_frontier_tests.py").write_text(DRIVER, encoding="utf-8")
    except BaseException:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root


def run(root: Path, suites: tuple[str, ...]) -> tuple[dict | None, str]:
    support = os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or str(REPO)
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_PLAYER_")}
    env.update({"PYTHONUTF8": "1", "AI_PLAYER_TEST_SUPPORT_ROOT": support, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        done = subprocess.run([sys.executable, str(root / "run_frontier_tests.py"), json.dumps(list(suites))],
                              cwd=str(root), env=env, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as error:
        return None, f"TIMEOUT after {TIMEOUT}s: {error}"
    raw = done.stdout.decode("utf-8", "replace") + done.stderr.decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):]), raw
    return None, raw


def _hit(bad: dict, test: str) -> bool:
    """Is the predicted `test` ("Class.test") among the failing ids ("module.Class.test"; a subTest's id has its
    parameters after a space)?"""
    return any(b == test or b.endswith("." + test) or b.startswith(test + " ") or ("." + test + " ") in b for b in bad)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    from ai_player.gates.provenance import unknown_mutants, watch

    unknown = unknown_mutants(sys.argv[1:], MUTANTS, ("--workers",))
    if unknown:
        print(f"REFUSED: no mutant named {unknown} ({len(MUTANTS)} exist; usage: revert_frontier.py [NAME[,NAME...]] "
              f"[--workers N]); nothing was run")
        return 2
    out = ["AI PLAYER A1, THE FRONTIER PROBE - MUTANT PROOF OF ITS GUARDS (gates/revert_frontier.py)",
           f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {provenance(REPO)}",
           "Each mutant breaks ONE guard of the frontier probe (or of its suite's own scans and pins) in a copy; CAUGHT = "
           "the run fails and every predicted test of gates/test_frontier_probe.py is among the failing ones.", ""]
    argv = list(sys.argv[1:])
    workers = 1
    if "--workers" in argv:
        at = argv.index("--workers")
        workers = max(1, int(argv[at + 1]))
        del argv[at:at + 2]
    only = set(argv[0].split(",")) if argv else None
    chosen = [(name, spec) for name, spec in MUTANTS.items() if only is None or name in only]
    tree = watch(REPO, explicit=True)

    def attempt(item):
        if tree.moved or not tree.check(f"before mutant {item[0]}"):
            return None, f"NOT RUN: the tree changed mid-run ({tree.moves[0][:300]})", None
        try:
            root = make_copy(item[1][2])
        except ValueError as error:
            return None, f"NOT APPLIED: {error}", None
        try:
            return run(root, item[1][4]) + (root,)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(attempt, chosen))
    ok_all = True
    counts = {CAUGHT: 0, REDUNDANT: 0}
    for (name, (prediction, what, edits, expected, suites)), (result, raw, root) in zip(chosen, results):
        if result is None:
            ok = False
            line = f"[{name}] NO RESULT: {raw[-1500:]}"
        else:
            bad = result["bad"]
            ran_copy = bool(result["modules"]) and all(root.name in module for module in result["modules"])
            failing = {t: bad[t] for t in sorted(bad)}
            if prediction == CONTROL:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] CONTROL, the unchanged copy: {result['ran']} tests of {list(suites)}, failing "
                        f"{sorted(bad) or 'none'} (ran the copy: {ran_copy}) -> {'PASS' if ok else 'FAIL'}")
            elif prediction == CAUGHT:
                caught = [t for t in expected if _hit(bad, t)]
                ok = ran_copy and bool(bad) and caught == list(expected)
                shown = dict(list(failing.items())[:6])
                more = f" (+{len(failing) - 6} more)" if len(failing) > 6 else ""
                line = (f"[{name}] BROKEN: {what}. Predicted CAUGHT by {list(expected)}. The copy ran {result['ran']} tests "
                        f"({'the copy' if ran_copy else 'NOT THE COPY'}); failing: {shown}{more} "
                        f"-> {'CAUGHT' if ok else 'NOT CAUGHT'}")
            else:
                ok = ran_copy and not bad and result["ran"] > 0
                line = (f"[{name}] BROKEN: {what}. Predicted REDUNDANT ALONE, because {expected} The copy ran "
                        f"{result['ran']} tests; failing: {failing or 'none'} -> {'as predicted' if ok else 'PREDICTION WRONG'}")
            if ok and prediction in counts:
                counts[prediction] += 1
        ok_all &= ok
        print(line, flush=True)
        out.append(line)
    verdict = "PASS" if ok_all else "FAIL"
    verdict, frozen_line = tree.seal(verdict)
    ok_all = verdict == "PASS"
    summary = (f"{counts[CAUGHT]} mutants CAUGHT as predicted, {counts[REDUNDANT]} REDUNDANT ALONE as predicted, of "
               f"{len(chosen) - (1 if any(n == 'F0' for n, _ in chosen) else 0)} run ({len(MUTANTS) - 1} defined)")
    out += ["", summary, frozen_line, f"OVERALL: {verdict}"]
    print(summary)
    print(frozen_line)
    print(f"OVERALL: {verdict}")
    if only is None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        path = EVIDENCE / f"{time.strftime('%Y-%m-%d')}-frontier-REVERT.txt"
        keep_earlier(path)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"evidence: {path.relative_to(REPO)}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
