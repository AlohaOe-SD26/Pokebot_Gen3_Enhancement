"""Self-test for tools/usage_audit.py (backlog P3, spec S1-6). Offline, a few seconds, on a HAND-WRITTEN transcript.

WHY THIS EXISTS. usage_audit.py turns transcripts into the numbers every cost lever is judged by. A proxy that counts a
streamed response three times, or calls `git commit -m "cat the log"` a `cat`, would rank the wrong lever with full
confidence. So each counting rule below has a FAULT arm (the rule broken -> the check must fail) and a CONTROL.

  U1 golden: exact calls, tokens, input-equivalent, tool calls, category shares, OBJECT shares and bad_lines 1 (a
     mid-line transcript end); the report prints its weights, stays about 30 lines, puts the BY-OBJECT shares first
     and the command shares beneath, lists the calibration points, and says the bot tuner's consults are not counted.
  U2 FAULT: the response dedupe removed (response_key monkeypatched to the line uuid) -> the split response counts
     three times and the golden FAILS. CONTROL: dedupe on -> golden holds.
  U3 categorisation by the FIRST REAL command: `git commit -m "cat the log"` is NOT cat (FAULT for a substring rule),
     `cat file.log` IS (CONTROL); plus quoted separators, `cd x &&`, env prefixes, `timeout`, `py -X utf8`; an
     echo/printf/Write-Output header is skipped, and a script in a gates/tests folder is a suite (review finding 10).
  U4 cold re-write: gap 6 min + a write above half the context counts; gap 2 min with the same write does not
     (CONTROL); gap 6 min with a small write does not (CONTROL).
  U5 append-only ledger: run 1 writes rev 1; a changed transcript appends rev 2 and line 1 stays byte-identical; an
     unchanged re-run appends nothing (CONTROL); a running workflow is skipped. FAULT: a simulated rewrite of the
     ledger is caught by the same byte-identity check. Privacy: a sentinel in the prompt never reaches the ledger
     (FAULT arm: the sentinel IS in the transcript), and the description is capped at 80 characters. New rows carry
     `objects` and `classifier: 2`; a classifier-1 ledger (no `objects`, different `categories`) is not re-appended
     when the usage is unchanged (CONTROL), and comparing the classification fields re-appends every row (FAULT).
  U6 read-only: the transcript tree is byte- and mtime-identical after a full --append run (CONTROL); FAULT: one
     appended byte is detected by the same snapshot.
  U8 GATE, the OBJECT axis against a human: the adversarial review's 25 hand-labelled real calls (2026-10-21),
     reduced to synthetic commands with the same file arguments. CONTROL: the object classifier agrees on >= 23/25
     and prints every disagreement. FAULT: the command-only classifier stays below 23 under EVERY one of the 25
     ways of giving bash_cat and bash_grep an object (08-MISTAKES 2026-10-19: objects, never commands).
  U9 --calibrate appends a point and the % becomes a 2-point fit; the report lists both points.
  U10 --session: ONE line with responses, input-equivalent and "ESTIMATE, 1 calibration point"; --since after the
     last response gives 0 (FAULT arm for the filter); a truncated last line is tolerated. (Was U8 before 2026-10-21.)
  U11 the object rules one at a time (even split, pattern is not a file, include/type filters, heredoc bodies,
     stdout to a file, a pipeline into a file, evidence/ and scratchpad folders, config as source, PowerShell -Path,
     quoted "<", `< file`), each beside a CONTROL.
  U12 TEMPLATED by the prompt's FIRST LINE (spec S2-3, review 2026-10-21 finding 6): a rendered prompt counts bare,
     inside the computed-task framing, and after the user-request relay; a prompt that only MENTIONS the marker, a
     marker for a role with no template, and a marker with text after it on line 1 do not (each a FAULT arm for the
     substring test that preceded it); a relay with no computed task is untemplated, never unknown.
  U7 (NOT a gate; `--real`): the REAL transcript folder, read-only: all four share tables (by object and by
     command, all agents and subagents) sum to 100 +/- 0.5 and the round-2 reference numbers print beside this run's.

Run: cd tools/story-dev && py -3.12 selftest_usage_audit.py [--real]
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
import usage_audit as ua  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []
SENTINEL = "SECRET-PROMPT-TEXT-7f3a"


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def usage(inp, cw5m, cw1h, cr, out):
    return {"input_tokens": inp, "cache_creation_input_tokens": cw5m + cw1h, "cache_read_input_tokens": cr,
            "output_tokens": out, "cache_creation": {"ephemeral_5m_input_tokens": cw5m,
                                                     "ephemeral_1h_input_tokens": cw1h}}


def asst(uuid, mid, ts, u, blocks, model="claude-opus-5-5"):
    return {"type": "assistant", "uuid": uuid, "timestamp": ts,
            "message": {"id": mid, "model": model, "usage": u, "content": blocks}}


def tool_use(tid, name, inp):
    return [{"type": "tool_use", "id": tid, "name": name, "input": inp}]


def result(uuid, ts, tid, content):
    return {"type": "user", "uuid": uuid, "timestamp": ts,
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tid, "content": content}]}}


T = "2026-10-21T10:00:{:02d}.000Z"
# The hand-written fixture: 4 responses (A is streamed over 3 lines), a Read of .py, a cat, a grep, a suite run,
# an attachment line, and a malformed last line (a live transcript ends mid-line).
A1_LINES = [
    {"type": "user", "uuid": "u1", "timestamp": T.format(0),
     "message": {"role": "user", "content": f"You are a builder. {SENTINEL} Do the thing."}},
    asst("l2", "msg_A", T.format(1), usage(10, 1000, 0, 0, 5), [{"type": "thinking", "thinking": ""}]),
    asst("l3", "msg_A", T.format(2), usage(10, 1000, 0, 0, 40), tool_use("tu1", "Read", {"file_path": "C:/r/mod.py"})),
    asst("l4", "msg_A", T.format(3), usage(10, 1000, 0, 0, 120),
         tool_use("tu2", "Bash", {"command": 'cd "C:/r x" && cat notes.log | head -5'})),
    result("l5", T.format(4), "tu1", "x" * 300),
    result("l6", T.format(5), "tu2", [{"type": "text", "text": "y" * 200}]),
    {"type": "attachment", "uuid": "l7", "timestamp": T.format(5)},
    asst("l8", "msg_B", T.format(10), usage(2, 600, 100, 1000, 30),
         tool_use("tu3", "Bash", {"command": "grep -n foo bar.py"})),
    result("l9", T.format(11), "tu3", "z" * 100),
    asst("l10", "msg_C", T.format(20), usage(3, 50, 0, 1600, 20),
         tool_use("tu4", "Bash", {"command": "PYTHONUTF8=1 py -3.12 selftest_x.py"})),
    result("l11", T.format(21), "tu4", "s" * 50),
    asst("l12", "msg_D", T.format(30), usage(1, 10, 0, 1650, 7), [{"type": "text", "text": "done"}]),
]
MALFORMED = '{"type": "assistant", "uuid": "l13", "message": {"id": "msg_E", "usa'
GOLDEN = {"calls": 4, "input": 16, "cw5m": 1660, "cw1h": 100, "cache_read": 4250, "output": 177,
          "ie": 16 + 1660 * 1.25 + 100 * 2 + 4250 * 0.1 + 177 * 5, "bad_lines": 1,
          "tool_calls": {"Read": 1, "Bash": 3},
          # weights: tu1 300 x 3 later, tu2 200 x 3, tu3 100 x 2, tu4 50 x 1 = 1750
          "shares": {"read_py": 51.4, "bash_cat": 34.3, "bash_grep": 11.4, "bash_suite": 2.9},
          # by OBJECT: mod.py 900 + bar.py 200 = source 1100; notes.log 600 = evidence; the suite 50
          "objects": {"source": 62.9, "evidence": 34.3, "suite": 2.9}}


# U8: the reviewer's 25 hand-labelled REAL calls (adversarial review 2026-10-21, `hand_label_sample`, seed 7 over 16
# transcripts), each reduced to a short SYNTHETIC command with the same file arguments and no file contents. The label
# is the reviewer's, by the OBJECT read ("log" folded into evidence, "suite output" = suite). Where the reviewer's text
# elided a path or argument ("...", "$f"), the stand-in keeps the same folder, suffix and command shape.
R, SP = "C:/Remote Projects/Pokebot_Gen3_Enhancement", "C:/Users/u/AppData/Local/Temp/claude/P/S1/scratchpad"
HAND_LABELS = [
    ("Read", {"file_path": f"{R}/ai_player/host/eyes.py"}, "source"),                                       # 1
    ("Read", {"file_path": f"{R}/sandbox-pokebot/modules/battle_handler.py"}, "source"),                    # 2
    ("Read", {"file_path": f"{R}/PROJECT KNOWLEDGE/ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md"}, "doc"),
    ("Read", {"file_path": f"{R}/ai_player/README.md"}, "doc"),                                             # 4
    ("Read", {"file_path": f"{R}/tools/story-dev/evidence/2026-10-01-batch14-POWER.txt"}, "evidence"),      # 5
    ("Read", {"file_path": f"{SP}/t23_3.txt"}, "evidence"),                                                 # 6
    ("Bash", {"command": f'cd "{R}" && cat ai_player/README.md; wc -l ai_player/README.md'}, "doc"),        # 7
    ("Bash", {"command": 'cd "C:/Remote Projects/pokebot-wt-ch24" && cat '
                         '"PROJECT KNOWLEDGE/ai-research-notes/2026-10-01-battleeq-DESIGN.md"'}, "doc"),    # 8
    ("Bash", {"command": f'mkdir -p "{SP}" && cd "{SP}" && cat > run_an.py <<\'EOF\'\nimport json, sys\n'
                         'print(len(open(sys.argv[1]).read()))\nEOF\npy -3.12 run_an.py notes.md'}, "other"),  # 9
    ("Bash", {"command": "ls maps | grep -c json && py -3.12 map_trainers.py | grep -i route | awk '{print $1}'"},
     "other"),                                                                                               # 10
    ("Bash", {"command": "cat tools/story-dev/evidence/2026-09-23-fly-unlocked.stdout.txt | head -80"},
     "evidence"),                                                                                            # 11
    ("Bash", {"command": "cat tools/story-dev/evidence/2026-09-18-party-l65-audit.stdout.txt | head -60"},
     "evidence"),                                                                                            # 12
    ("Bash", {"command": 'echo "=== COUNT ENTERED_ELITE_FOUR ==="; grep -rn ENTERED_ELITE_FOUR --include=*.py '
                         "sandbox-pokebot/modules/"}, "source"),                                             # 13
    ("Bash", {"command": "gh api repos/pret/pokeemerald/contents/src/party_menu.c --jq .content | base64 -d "
                         "> party_menu.c; wc -l party_menu.c; grep -n CursorCb_Summary party_menu.c"},
     "source"),                                                                                              # 14
    ("Bash", {"command": 'sed -n 1820,1860p "PROJECT KNOWLEDGE/03-PUNCH-LIST.md"; wc -l '
                         '"PROJECT KNOWLEDGE/03-PUNCH-LIST.md"; ls'}, "doc"),                                # 15
    ("Bash", {"command": 'D=/c/Users/u/pokeemerald; echo "=== include/config.h ==="; sed -n \'40,60p\' '
                         '"$D/include/config.h" | cat -n'}, "source"),                                       # 16
    ("Bash", {"command": 'grep -n "WHITEOUT recovery" "sandbox-pokebot/profiles/P1/debug-logs/'
                         'P1-endless-debug-20261003.log"'}, "evidence"),                                     # 17
    ("Bash", {"command": 'grep -a -n "\\[MAP\\]" sandbox-pokebot/profiles/P2/P2-endless-debug-20261003.log '
                         "| tail -20"}, "evidence"),                                                         # 18
    ("Bash", {"command": "git diff --stat; ls; wc -l tools/*.py"}, "other"),                                 # 19
    ("Bash", {"command": "sed -n '1,145p' \"tools/story-dev/probe_league_leg4_guard.py\""}, "source"),       # 20
    ("Bash", {"command": 'git status --short | grep -v "^??"; git log --oneline -5; ls'}, "other"),         # 21
    ("PowerShell", {"command": f'Get-ChildItem "{R}/sandbox-pokebot/profiles" -Directory | Where-Object '
                               "{ $_.Name -like 'endless-P*' } | Select-Object Name, LastWriteTime"}, "other"),
    ("PowerShell", {"command": "Get-CimInstance Win32_Process -Filter \"Name like 'py%'\" | Select-Object "
                               "ProcessId, CommandLine | Format-List"}, "other"),                           # 23
    ("Bash", {"command": "PYTHONUTF8=1 py -3.12 probe_e4_halls.py 2>&1 | tail -45"}, "suite"),               # 24
    ("Bash", {"command": "export PYTHONUTF8=1 && time py -3.12 ai_player/gates/check_purity.py | tail -5 && "
                         "py -3.12 ai_player/gates/test_check_purity.py && py -3.12 ai_player/host/test_host.py"},
     "suite"),                                                                                               # 25
]
# The COMMAND-only classifier (the shipped design): its categories carry an object only for Reads, suites and
# "other"; bash_cat / bash_grep name a tool habit. U8's FAULT arm gives those two buckets EVERY possible object and
# shows that none of the 5 x 5 = 25 assignments reaches the bar -- so the failure is the axis, not an unlucky mapping.
COMMAND_TO_OBJECT = {"read_py": "source", "read_md": "doc", "read_evidence": "evidence", "read_other": "other",
                     "bash_suite": "suite", "bash_other": "other", "search_tool": "other", "other_tool": "other"}
U8_BAR = 23


def dominant(objs: dict) -> str:
    """The object with the largest share; a tie goes to the earlier one in ua.OBJECTS (deterministic)."""
    return max(ua.OBJECTS, key=lambda o: (objs.get(o, 0.0), -ua.OBJECTS.index(o)))


def score(classify) -> tuple[int, list[str]]:
    misses = []
    for i, (name, inp, want) in enumerate(HAND_LABELS, 1):
        got = classify(name, inp)
        if got != want:
            misses.append(f"#{i:02d} want {want} got {got}: {str(inp)[:90]}")
    return len(HAND_LABELS) - len(misses), misses


def cold_agent(gap_s: int, write: int) -> list:
    t0, t1 = "2026-10-21T12:00:00.000Z", f"2026-10-21T12:{gap_s // 60:02d}:{gap_s % 60:02d}.000Z"
    return [{"type": "user", "uuid": "c0", "timestamp": t0,
             "message": {"role": "user", "content": "<!-- stage-template:verify@1 -->\ncheck it"}},
            asst("c1", "msg_c1", t0, usage(0, 1000, 0, 9000, 10), [{"type": "text", "text": "a"}]),
            asst("c2", "msg_c2", t1, usage(0, write, 0, 0, 10), [{"type": "text", "text": "b"}])]


def write_jsonl(path: Path, rows: list, tail: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows) + tail, encoding="utf-8")


def build_fixture(root: Path) -> Path:
    proj = root / "projects" / "C--Remote-Projects-Pokebot-Gen3-Enhancement"
    sess = proj / "S1"
    write_jsonl(proj / "S1.jsonl", [{"type": "user", "uuid": "m0", "timestamp": T.format(0),
                                     "message": {"role": "user", "content": "hi"}}])
    wf1 = sess / "subagents" / "workflows" / "wf_test-001"
    write_jsonl(wf1 / "agent-a1.jsonl", A1_LINES, MALFORMED)
    (wf1 / "agent-a1.meta.json").write_text(json.dumps({"description": "build:fixture", "workflowPhase": "Build"}))
    write_jsonl(wf1 / "journal.jsonl", [{"type": "started", "agentId": "a1", "label": "build:fixture",
                                         "phase": "Build"}])
    wf2 = sess / "subagents" / "workflows" / "wf_test-002"
    write_jsonl(wf2 / "agent-a2.jsonl", cold_agent(360, 8000))   # 6 min, write 8000 > half of 10000 -> cold
    write_jsonl(wf2 / "agent-a3.jsonl", cold_agent(120, 8000))   # 2 min, same write -> not cold (CONTROL)
    write_jsonl(wf2 / "agent-a4.jsonl", cold_agent(360, 1000))   # 6 min, small write -> not cold (CONTROL)
    wf3 = sess / "subagents" / "workflows" / "wf_test-003"         # still running: no wf_*.json yet
    write_jsonl(wf3 / "agent-a5.jsonl", cold_agent(60, 10))
    wfs = sess / "workflows"
    (wfs / "scripts").mkdir(parents=True)
    long_desc = "D" * 120
    for wf, name in (("wf_test-001", "fixture-wf"), ("wf_test-002", "cold-wf")):
        (wfs / f"{wf}.json").write_text(json.dumps({"runId": wf, "timestamp": T.format(0), "workflowName": name,
                                                    "summary": long_desc, "script": "export const meta = {}"}))
    (wfs / "scripts" / "running-wf_test-003.js").write_text("export const meta = {\n  name: 'running-wf',\n}\n")
    return proj


def totals(roots) -> dict:
    agents, stats, _ = ua.load(roots)
    a1 = [a for a in agents if a.path.name == "agent-a1.jsonl"]
    agent = a1[0] if a1 else None
    u = agent.usage() if agent else {}
    shares = {k: v for k, v in ua.shares(agent.weights).items() if v} if agent else {}
    objects = {k: v for k, v in ua.shares(agent.obj_weights, ua.OBJECTS).items() if v} if agent else {}
    return {"calls": len(agent.order) if agent else -1, **{k: u.get(k, 0) for k in ua.WEIGHTS},
            "ie": ua.ie_of(u), "bad_lines": stats["bad_lines"], "tool_calls": dict(agent.tool_calls) if agent else {},
            "shares": shares, "objects": objects}


def golden_diff(got: dict) -> list[str]:
    return [f"{k}: want {v} got {got.get(k)}" for k, v in GOLDEN.items()
            if (abs(got.get(k, 0) - v) > 1e-6 if isinstance(v, (int, float)) else got.get(k) != v)]


def run_cli(*args: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = ua.main(list(args))
    return code, buf.getvalue()


def snapshot(root: Path) -> dict:
    return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


def first_line(path: Path) -> bytes:
    data = path.read_bytes() if path.exists() else b""
    return data.split(b"\n", 1)[0]


def selftest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        proj = build_fixture(root)
        roots = [proj]
        ledger = root / "ledger" / "cost-ledger.jsonl"

        # U1 golden
        got = totals(roots)
        diff = golden_diff(got)
        check("U1 golden: calls, tokens, ie, tool calls, shares, bad_lines 1", not diff, "; ".join(diff))
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger))
        check("U1 report prints the weights", ua.WEIGHTS_TEXT in out, out[:300])
        check("U1 report is about 30 lines (<= 30)", len(out.splitlines()) <= 30, str(len(out.splitlines())))
        lines_out = out.splitlines()
        obj_i = next((i for i, ln in enumerate(lines_out) if ln.startswith("context weight BY OBJECT read, ALL")), -1)
        cmd_i = next((i for i, ln in enumerate(lines_out) if "secondary, by COMMAND" in ln), -1)
        check("U1 the headline shares are BY OBJECT, the command shares beneath them as the secondary table",
              0 <= obj_i < cmd_i and "source 62.9" in lines_out[obj_i] and "evidence 34.3" in lines_out[obj_i],
              f"{obj_i} {cmd_i} {lines_out[obj_i] if obj_i >= 0 else ''}")
        check("U1 the report lists the calibration points the % rests on (the seed, marked as such)",
              "calibration points (ie Mtok -> weekly meter %): 143 -> 36 (seed" in out, out[:900])
        check("U1 the report says the bot tuner's consults are NOT counted (no transcript)",
              "NOT COUNTED" in out and "--no-session-persistence" in out, out[:900])
        check("U1 report writes no ledger without --append", not ledger.exists())

        # U2 FAULT: dedupe removed
        real_key = ua.response_key
        ua.response_key = lambda d: d.get("uuid")
        try:
            bad = totals(roots)
        finally:
            ua.response_key = real_key
        check("U2 FAULT: no dedupe -> the golden FAILS (the split response counts 3 times)",
              bool(golden_diff(bad)) and bad["calls"] == 6 and bad["input"] == 36, json.dumps(bad)[:300])
        check("U2 CONTROL: dedupe restored -> golden holds", not golden_diff(totals(roots)))

        # U3 categorisation
        cases = [('git commit -m "cat the log"', "bash_other"), ("cat file.log", "bash_cat"),
                 ('echo "a && cat b"', "bash_other"), ('cd "C:/a b" && cat x', "bash_cat"),
                 ("cd x; grep -rn foo .", "bash_grep"), ("PYTHONUTF8=1 py -3.12 selftest_a.py", "bash_suite"),
                 ("timeout 60 py -3.12 -X utf8 run_gates.py", "bash_suite"),
                 ('py -3.12 -c "import test_x"', "bash_other"), ("py -3.12 -m pytest -q", "bash_suite"),
                 ("git log | grep cat", "bash_other"), ("for f in a b; do cat $f; done", "bash_cat"),
                 ("$env:PYTHONUTF8='1'; Get-Content x.py", "bash_cat"),
                 ('& "C:/py.exe" -3.12 probe_x.py', "bash_suite"),
                 # finding 10: an echo/printf/Write-Output HEADER is navigation, not the command (FAULT before)
                 ('echo "=== X ==="; cat a.log', "bash_cat"), ("printf '%s\\n' hdr && grep -n x a.py", "bash_grep"),
                 ("Write-Output '---'; Get-Content x.md", "bash_cat"),
                 ('echo "only a header"', "bash_other"),                       # CONTROL: nothing after it
                 # finding 10: a suite is matched by its FOLDER too (FAULT before), not by any path substring
                 ("py -3.12 ai_player/gates/check_purity.py", "bash_suite"),
                 ("py -3.12 tools/story-dev/run_an.py", "bash_other")]           # CONTROL: no suite folder/name
        for cmd, want in cases:
            got_cat = ua.bash_category(cmd)
            check(f"U3 {cmd!r} -> {want}", got_cat == want, got_cat)

        # U4 cold re-writes
        agents, _, _ = ua.load(roots)
        cold = {a.path.stem: len(a.cold_rewrites()) for a in agents if a.workflow == "wf_test-002"}
        check("U4 gap 6 min + write 8000 > half of 10000 -> 1 cold re-write", cold.get("agent-a2") == 1, str(cold))
        check("U4 CONTROL: gap 2 min, same write -> 0", cold.get("agent-a3") == 0, str(cold))
        check("U4 CONTROL: gap 6 min, small write -> 0", cold.get("agent-a4") == 0, str(cold))

        # U6 read-only (snapshot around a full --append run)
        before = snapshot(proj)
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--append")
        after = snapshot(proj)
        check("U6 CONTROL: the transcript tree is unchanged by an --append run", before == after)

        # U5 append-only
        rows = ua.read_ledger(ledger)
        check("U5 run 1: one rev-1 row per FINISHED workflow (the running one skipped)",
              sorted((r["key"], r["rev"]) for r in rows) == [("S1:wf_test-001", 1), ("S1:wf_test-002", 1)]
              and "1 running skipped" in out, out.splitlines()[-1])
        line1 = first_line(ledger)
        wf1 = next((r for r in rows if r["key"] == "S1:wf_test-001"), {})
        check("U5 the row has the spec's fields", all(k in wf1 for k in (
            "key", "rev", "ts", "session", "workflow", "stage_rows", "agents", "calls", "ie_mtok", "model_mix",
            "categories", "cold_rewrites", "over150", "untemplated")), str(sorted(wf1)))
        check("U5 a new row carries the OBJECT shares", wf1.get("objects", {}).get("source") == 62.9 and
              wf1.get("objects", {}).get("evidence") == 34.3, json.dumps(wf1.get("objects")))
        check("U5 workflow name, stage label and untemplated count", wf1.get("workflow") == "fixture-wf" and
              wf1.get("stage_rows", [{}])[0].get("stage") == "build:fixture" and wf1.get("untemplated") == 1,
              json.dumps(wf1)[:300])
        wf2 = next((r for r in rows if r["key"] == "S1:wf_test-002"), {})
        check("U5 CONTROL: templated agents are not untemplated; cold re-writes 1",
              wf2.get("untemplated") == 0 and wf2.get("cold_rewrites") == 1, json.dumps(wf2)[:300])
        text = ledger.read_text(encoding="utf-8")
        check("U5 FAULT arm present: the sentinel IS in the transcript",
              SENTINEL in (proj / "S1" / "subagents" / "workflows" / "wf_test-001" / "agent-a1.jsonl").read_text())
        check("U5 privacy: the prompt sentinel never reaches the ledger", SENTINEL not in text)
        check("U5 description capped at 80 characters", all(len(r.get("desc", "")) <= 80 for r in rows) and
              len(wf1.get("desc", "")) == 80, str([len(r.get("desc", "")) for r in rows]))
        run_cli("--root", str(proj), "--ledger", str(ledger), "--append")
        check("U5 CONTROL: an unchanged re-run appends nothing", len(ua.read_ledger(ledger)) == 2,
              str(len(ua.read_ledger(ledger))))
        # rows written by classifier 1 (no `objects`, no `classifier`, other `categories`) must not be re-appended
        # when only the classifier moved their buckets: a classifier change is not new usage
        old_fmt = root / "ledger-old" / "cost-ledger.jsonl"
        old_fmt.parent.mkdir()
        old_fmt.write_text("".join(json.dumps({**{k: v for k, v in r.items() if k not in ("objects", "classifier")},
                                               "categories": {**r["categories"], "bash_other": 99.9}}) + "\n"
                                   for r in ua.read_ledger(ledger)), encoding="utf-8")
        old_bytes = old_fmt.read_bytes()
        code, out = run_cli("--root", str(proj), "--ledger", str(old_fmt), "--append")
        check("U5 CONTROL: unchanged-usage workflows in a classifier-1 ledger are not re-appended",
              old_fmt.read_bytes() == old_bytes and "appended 0 rows (2 unchanged" in out, out.splitlines()[-1])
        saved = ua.CLASSIFICATION_FIELDS
        ua.CLASSIFICATION_FIELDS = ()
        try:
            code, out = run_cli("--root", str(proj), "--ledger", str(old_fmt), "--append")
        finally:
            ua.CLASSIFICATION_FIELDS = saved
        check("U5 FAULT: comparing the classification fields re-appends every old row (2 rows)",
              "appended 2 rows" in out and len(ua.read_ledger(old_fmt)) == 4, out.splitlines()[-1])
        a1 = proj / "S1" / "subagents" / "workflows" / "wf_test-001" / "agent-a1.jsonl"
        a1_copy = root / "a1-backup.jsonl"
        shutil.copy2(a1, a1_copy)
        write_jsonl(a1, A1_LINES + [asst("l14", "msg_F", T.format(40), usage(1, 10, 0, 1700, 3),
                                         [{"type": "text", "text": "more"}])])
        run_cli("--root", str(proj), "--ledger", str(ledger), "--append")
        rows = ua.read_ledger(ledger)
        check("U5 a changed workflow appends rev 2 (and only for that key)",
              [(r["key"], r["rev"]) for r in rows][-1] == ("S1:wf_test-001", 2) and len(rows) == 3,
              str([(r["key"], r["rev"]) for r in rows]))
        check("U5 the appended rev carries `objects` and `classifier` 2",
              "objects" in rows[-1] and rows[-1].get("classifier") == 2, str(sorted(rows[-1])))
        check("U5 line 1 is byte-identical after the appends", first_line(ledger) == line1)
        fake = root / "rewritten.jsonl"
        fake.write_text(json.dumps({**wf1, "calls": 99}) + "\n", encoding="utf-8")
        check("U5 FAULT: a rewritten ledger is caught by the byte-identity check", first_line(fake) != line1)

        # U6 FAULT: the snapshot detects one byte
        snap = snapshot(proj)
        with open(a1, "ab") as fh:
            fh.write(b" ")
        check("U6 FAULT: one appended byte changes the snapshot", snapshot(proj) != snap)
        shutil.copy2(a1_copy, a1)

        # U10 --session (numbered U8 until 2026-10-21, when U8 became the hand-label gate)
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--session", "S1")
        lines = out.strip().splitlines()
        check("U10--session prints ONE line", len(lines) == 1 and code == 0, out)
        want_ie = (GOLDEN["ie"] + 3 * ua.ie_of({"cw5m": 1000, "cache_read": 9000, "output": 10}) +
                   ua.ie_of({"cw5m": 8000, "output": 10}) * 2 + ua.ie_of({"cw5m": 1000, "output": 10}) +
                   ua.ie_of({"cw5m": 1000, "cache_read": 9000, "output": 10}) + ua.ie_of({"cw5m": 10, "output": 10}))
        check("U10counts every agent of the session once (4 + 2 x 4 = 12 responses)", "responses 12 " in out, out)
        check("U10 input-equivalent", f"input-equivalent {want_ie / 1e6:.2f} Mtok" in out, f"{want_ie} | {out}")
        check("U10says ESTIMATE, 1 calibration point", "(ESTIMATE, 1 calibration point)" in out, out)
        check("U10tolerates the truncated last line (bad_lines 1)", "bad_lines 1" in out, out)
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--session", "S1",
                            "--since", "2026-10-21T12:00:30Z")
        check("U10--since keeps only the later responses (the 4 second responses, all after 12:00:30)",
              "responses 4 " in out, out)
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--session", "S1",
                            "--since", "2027-01-01T00:00:00Z")
        check("U10FAULT arm for the filter: --since after everything -> 0 responses", "responses 0 " in out, out)

        # U9 --calibrate
        run_cli("--ledger", str(ledger), "--calibrate", "100", "30")
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--session", "S1")
        check("U9 a calibration row makes it a 2-point fit", "(ESTIMATE, 2 calibration points)" in out, out)
        k = (143 * 36 + 100 * 30) / (143 ** 2 + 100 ** 2)
        got_pct = ua.week_pct(100.0, ua.calibration_points(ledger))
        check("U9 the fit is through the origin: k = (143*36 + 100*30) / (143^2 + 100^2)",
              got_pct.startswith(f"~{100 * k:.1f} % of a week"), f"want ~{100 * k:.1f} got {got_pct}")
        check("U9 CONTROL: the seed alone gives 36/143 per Mtok",
              ua.week_pct(143.0, ua.SEED_CALIBRATION).startswith("~36.0 % of a week"))
        check("U9 the report lists BOTH calibration points once a second one is recorded",
              "143 -> 36 (seed" in "\n".join(ua.report([], {"files": 0, "bad_lines": 0}, [], ledger, "", "x"))
              and "; 100 -> 30" in "\n".join(ua.report([], {"files": 0, "bad_lines": 0}, [], ledger, "", "x")))

    hand_label_gate()
    object_units()
    templated_units()


def _computed(text: str) -> str:
    """`text` as the workflow harness frames a computed task (measured 2026-10-21: one header line, 2-space indent)."""
    return ("[Workflow harness — computed task] The task text below was computed at runtime by a workflow script. "
            "The computed task text follows:\n" + "\n".join(("  " + x) if x else "" for x in text.split("\n")))


def templated_units() -> None:
    """U12: TEMPLATED is decided by the prompt's FIRST LINE (spec S2-3; review 2026-10-21, finding 6). Each FAULT case
    is the arm of one rule (it reads wrongly when that rule is removed); the CONTROL cases hold either way."""
    marker = "<!-- stage-template:verify@1 -->"
    body = "You are the ONE adversarial VERIFIER.\n\n## GOAL\nbreak it"
    relay = ("[Workflow harness — user request] The harness relays, verbatim and indented below, the user's request:\n"
             "  please review the templates")
    cases = [
        # (label, the agent's user messages in order, want) -- the rule each one guards
        ("CONTROL a bare rendered prompt", [marker + "\n" + body], True),
        ("a rendered prompt inside the computed-task framing", [_computed(marker + "\n" + body)], True),  # header strip
        ("the user-request relay FIRST, the rendered computed task second", [relay, _computed(marker + "\n" + body)],
         True),                                                                                # the relay is skipped
        ("CONTROL the relay first, a computed task WITHOUT a marker second", [relay, _computed(body)], False),
        ("a prompt that MENTIONS the marker on a later line", ["Review the lint. Line 1 must read:\n" + marker], False),
        ("a mention inside the computed framing", [_computed("Check that " + marker + " is line 1.\n" + body)], False),
        ("a marker line for a role with NO template", ["<!-- stage-template:nosuchrole@1 -->\n" + body], False),
        ("a marker followed by more text on line 1", [marker + " check it\n" + body], False),        # fullmatch
        ("a relay and no computed task after it", [relay], False),                               # never left None
        ("CONTROL text blocks (list content) whose first line is the marker",
         [[{"type": "text", "text": marker + "\n" + body}]], True),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for i, (label, users, want) in enumerate(cases):
            rows = [{"type": "user", "uuid": f"t{i}-{k}", "timestamp": T.format(k),
                     "message": {"role": "user", "content": text}} for k, text in enumerate(users)]
            rows.append(asst(f"t{i}-a", f"msg_t{i}", T.format(9), usage(1, 0, 0, 0, 1), [{"type": "text", "text": "ok"}]))
            path = Path(tmp) / f"agent-t{i}.jsonl"
            write_jsonl(path, rows)
            agent = ua.Agent(path, "s", "workflow", "wf_t", "stage", "phase")
            ua.scan_file(path, agent, Counter())
            check(f"U12 {label} -> templated {want}", agent.templated is want, f"got {agent.templated!r}")


def hand_label_gate() -> None:
    """U8: the object axis agrees with the reviewer's hand labels on at least U8_BAR of 25 calls."""
    def new(name, inp):
        return dominant(ua.tool_objects(name, inp))

    ok, misses = score(new)
    for m in misses:
        print(f"  U8 disagreement: {m}")
    check(f"U8 CONTROL: the OBJECT classifier agrees with the hand labels on >= {U8_BAR}/25 (got {ok}/25)",
          ok >= U8_BAR, "; ".join(misses))
    best, best_map = -1, None
    for cat_obj in ua.OBJECTS:
        for grep_obj in ua.OBJECTS:
            table = {**COMMAND_TO_OBJECT, "bash_cat": cat_obj, "bash_grep": grep_obj}
            got, _ = score(lambda n, i, t=table: t[ua.tool_category(n, i)])
            if got > best:
                best, best_map = got, (cat_obj, grep_obj)
    check(f"U8 FAULT: the COMMAND-only classifier fails the bar under EVERY object given to bash_cat/bash_grep "
          f"(best {best}/25 with bash_cat={best_map[0]}, bash_grep={best_map[1]})", best < U8_BAR, str(best))
    fair = {**COMMAND_TO_OBJECT, "bash_cat": None, "bash_grep": None}
    got, _ = score(lambda n, i: fair[ua.tool_category(n, i)])
    print(f"  U8 info: command-only with bash_cat/bash_grep carrying NO object (the reviewer's scoring): {got}/25")


def object_units() -> None:
    """U11: the object rules one at a time. Each case is the FAULT arm of the rule it names (it fails when that rule
    is removed) beside a CONTROL that holds either way."""
    cases = [
        # (command, powershell, want {object: share}) -- the rule each one guards
        ("cat a.md b.py", False, {"doc": 0.5, "source": 0.5}),                  # weight split evenly
        ("cat a.md", False, {"doc": 1.0}),                                        # CONTROL: one object
        ('grep -n "import os" notes.md', False, {"doc": 1.0}),                  # the pattern is not a file
        ("grep -rn FOO --include=*.py modules/", False, {"source": 1.0}),         # the include filter names it
        ("grep -rn FOO modules/", False, {"other": 1.0}),                         # CONTROL: unknown object
        ("rg -n FOO -t py src", False, {"source": 1.0}),                          # rg's type filter
        ("cat > x.py <<'EOF'\ngrep -n foo big.log\nEOF\npy -3.12 x.py", False, {"other": 1.0}),  # heredoc body
        ("cat a.md > b.md", False, {"other": 1.0}),                               # stdout to a file: nothing shown
        ("gh api repos/o/r/contents/src/a.c | base64 -d > a.c; ls", False, {"other": 1.0}),  # pipeline to a file
        ("gh api repos/o/r/contents/src/a.c --jq .content", False, {"source": 1.0}),  # CONTROL: it IS shown
        ("head -n 40 evidence/run.md", False, {"evidence": 1.0}),                 # evidence/ beats the suffix
        ("tail -5 C:/t/scratchpad/out.json", False, {"evidence": 1.0}),           # a scratchpad run output
        ("cat C:/t/scratchpad/recon_results.md", False, {"evidence": 1.0}),       # an agent's result, not a doc
        ("cat C:/t/scratchpad/fetch.py", False, {"source": 1.0}),                 # CONTROL: a script stays source
        ("cat tools/ops/ops_config.json", False, {"source": 1.0}),                # config is the program
        ("Get-Content -Path C:\\r\\x.py -TotalCount 50", True, {"source": 1.0}),  # PowerShell -Path, backslashes
        ("Select-String -Pattern foo -Path a.log", True, {"evidence": 1.0}),      # CONTROL: both named
        ("Select-String -Path a.log TODO", True, {"evidence": 1.0}),              # -Path names it; TODO = pattern
        ('grep -c "<!-- x" a.md', False, {"doc": 1.0}),                          # a quoted "<..." is no redirect
        ("grep -c foo < a.log", False, {"evidence": 1.0}),                        # a file fed with `<`
        ("py -3.12 tools/story-dev/selftest_x.py | tail -3", False, {"suite": 1.0}),
        ("git log --oneline -5; ls; wc -l a.md", False, {"other": 1.0}),          # listing is not an object
    ]
    for cmd, ps, want in cases:
        got = {k: round(v, 3) for k, v in ua.tool_objects("PowerShell" if ps else "Bash", {"command": cmd}).items()}
        check(f"U11 {cmd[:60]!r} -> {want}", got == want, str(got))
    check("U11 Read uses the same path rule", ua.tool_objects("Read", {"file_path": "C:/r/evidence/x.py"}) ==
          {"evidence": 1.0} and ua.tool_objects("Read", {"file_path": "C:/r/a.PY"}) == {"source": 1.0})


def real_smoke() -> None:
    """U7: the real folder, read-only. Not a gate (it depends on this machine's transcripts)."""
    roots = ua.project_roots(None)
    before = {str(p): p.stat().st_size for r in roots for p in r.rglob("*.json")}
    code, out = run_cli()
    print(out)
    shares_lines = [ln for ln in out.splitlines() if "(sum " in ln]
    check("U7 four share tables (by object and by command, all agents and subagents)", len(shares_lines) == 4,
          str(len(shares_lines)))
    for ln in shares_lines:
        total = float(ln.rsplit("(sum ", 1)[1].rstrip(")"))
        check(f"U7 shares sum to 100 +/- 0.5 ({ln.split(':')[0].strip()})", abs(total - 100) <= 0.5, ln[-20:])
    check("U7 the round-2 reference line is printed", "round-2 reference (subagents): .py Reads 33.4 %" in out)
    check("U7 no .json changed size (read-only)",
          all(Path(p).stat().st_size == s for p, s in before.items() if Path(p).exists()))


def main() -> int:
    selftest()
    if "--real" in sys.argv:
        real_smoke()
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:300]}"))
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
