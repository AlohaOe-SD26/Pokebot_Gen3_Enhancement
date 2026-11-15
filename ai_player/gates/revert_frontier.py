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

THE TABLE (135 mutants; the spec's "about 54" predates the amendments' tests T31-T36 and AM-11, so it is not this count):
  G01-G98  the build's guard table (B2.3, 2026-11-14): ONE edit of `frontier_probe.py` per guard of T1-T36 and AM-11, each
           shown, on a temp copy loaded by the suite's own `load_module`, to FAIL the case named here ("98 caught, 0 not
           caught"). The anchors and replacements are that table's, but G33-G36's: the verifier's round 1 (F1) made the tick
           ask `disk_decision` about each measurement, so those four are anchored on the tick's new lines (same guards, same
           predictions), and G27-G30 (`disk_decision`'s boundaries) now break the code a batch runs.
  V05-V44  the verifier's round 1 (2026-11-14): the guards its own mutants showed NO case caught (V05-V31, its names kept,
           re-anchored where the fix moved a line) and the round's further guards (V40-V44), each caught by the FAULT or
           CONTROL the round added. Two of its gaps stay open as NITs: replay's and `child_env`'s environment strips.
  V55-V74  the verifier's round 2 (2026-11-14): its one-edit mutants of its two findings, which NO case caught (R2-M1, the
           disk guard's and the batch's terminal ends: V69, V70, V72, V73, V74; R2-M2, the development seed check's two
           refusals: V55, V56), its names, anchors and replacements kept, each now caught by the FAULT arm the round added
           to T14 (through the real `run_batch`) or T13.
  K1-K2    the round's own two: a seed ledger that cannot be read at a path ending in the KNOWN non-ledger is allowed (K1)
           and LISTED (K2), as 2.5 says (before the round it was skipped unlisted), each caught by T13's CONTROL.
  H1-H4    the test-side guards (B2.3b), whose guard is not in `frontier_probe.py`: T28's two import scans (the suite's
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
for _name, _tid, _guard, _old, _new, _tests in _ROUND1 + _ROUND2:
    if _name in MUTANTS:
        raise SystemExit(f"revert_frontier: mutant {_name} is defined twice")
    MUTANTS[_name] = (CAUGHT, f"{_tid} guard removed: {_guard}", [(PROBE, _old, _new)], [f"GuardTests.{t}" for t in _tests],
                      DEFAULT_SUITES)

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
