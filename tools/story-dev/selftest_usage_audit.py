"""Self-test for tools/usage_audit.py (backlog P3, spec S1-6). Offline, a few seconds, on a HAND-WRITTEN transcript.

WHY THIS EXISTS. usage_audit.py turns transcripts into the numbers every cost lever is judged by. A proxy that counts a
streamed response three times, or calls `git commit -m "cat the log"` a `cat`, would rank the wrong lever with full
confidence. So each counting rule below has a FAULT arm (the rule broken -> the check must fail) and a CONTROL.

  U1 golden: exact calls, tokens, input-equivalent, tool calls, category shares and bad_lines 1 (a mid-line
     transcript end); the report prints its weights and stays about 25 lines.
  U2 FAULT: the response dedupe removed (response_key monkeypatched to the line uuid) -> the split response counts
     three times and the golden FAILS. CONTROL: dedupe on -> golden holds.
  U3 categorisation by the FIRST REAL command: `git commit -m "cat the log"` is NOT cat (FAULT for a substring rule),
     `cat file.log` IS (CONTROL); plus quoted separators, `cd x &&`, env prefixes, `timeout`, `py -X utf8`.
  U4 cold re-write: gap 6 min + a write above half the context counts; gap 2 min with the same write does not
     (CONTROL); gap 6 min with a small write does not (CONTROL).
  U5 append-only ledger: run 1 writes rev 1; a changed transcript appends rev 2 and line 1 stays byte-identical; an
     unchanged re-run appends nothing (CONTROL); a running workflow is skipped. FAULT: a simulated rewrite of the
     ledger is caught by the same byte-identity check. Privacy: a sentinel in the prompt never reaches the ledger
     (FAULT arm: the sentinel IS in the transcript), and the description is capped at 80 characters.
  U6 read-only: the transcript tree is byte- and mtime-identical after a full --append run (CONTROL); FAULT: one
     appended byte is detected by the same snapshot.
  U8 --session: ONE line with responses, input-equivalent and "ESTIMATE, 1 calibration point"; --since after the last
     response gives 0 (FAULT arm for the filter); a truncated last line is tolerated.
  U9 --calibrate appends a point and the % becomes a 2-point fit.
  U7 (NOT a gate; `--real`): the REAL transcript folder, read-only: shares sum to 100 +/- 0.5 and the round-2
     reference numbers print beside this run's.

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
          "shares": {"read_py": 51.4, "bash_cat": 34.3, "bash_grep": 11.4, "bash_suite": 2.9}}


def cold_agent(gap_s: int, write: int) -> list:
    t0, t1 = "2026-10-21T12:00:00.000Z", f"2026-10-21T12:{gap_s // 60:02d}:{gap_s % 60:02d}.000Z"
    return [{"type": "user", "uuid": "c0", "timestamp": t0,
             "message": {"role": "user", "content": "<!-- stage-template:verify@1 --> check it"}},
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
    return {"calls": len(agent.order) if agent else -1, **{k: u.get(k, 0) for k in ua.WEIGHTS},
            "ie": ua.ie_of(u), "bad_lines": stats["bad_lines"], "tool_calls": dict(agent.tool_calls) if agent else {},
            "shares": shares}


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
        check("U1 report is about 25 lines (<= 26)", len(out.splitlines()) <= 26, str(len(out.splitlines())))
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
                 ('& "C:/py.exe" -3.12 probe_x.py', "bash_suite")]
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

        # U8 --session
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--session", "S1")
        lines = out.strip().splitlines()
        check("U8 --session prints ONE line", len(lines) == 1 and code == 0, out)
        want_ie = (GOLDEN["ie"] + 3 * ua.ie_of({"cw5m": 1000, "cache_read": 9000, "output": 10}) +
                   ua.ie_of({"cw5m": 8000, "output": 10}) * 2 + ua.ie_of({"cw5m": 1000, "output": 10}) +
                   ua.ie_of({"cw5m": 1000, "cache_read": 9000, "output": 10}) + ua.ie_of({"cw5m": 10, "output": 10}))
        check("U8 counts every agent of the session once (4 + 2 x 4 = 12 responses)", "responses 12 " in out, out)
        check("U8 input-equivalent", f"input-equivalent {want_ie / 1e6:.2f} Mtok" in out, f"{want_ie} | {out}")
        check("U8 says ESTIMATE, 1 calibration point", "(ESTIMATE, 1 calibration point)" in out, out)
        check("U8 tolerates the truncated last line (bad_lines 1)", "bad_lines 1" in out, out)
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--session", "S1",
                            "--since", "2026-10-21T12:00:30Z")
        check("U8 --since keeps only the later responses (the 4 second responses, all after 12:00:30)",
              "responses 4 " in out, out)
        code, out = run_cli("--root", str(proj), "--ledger", str(ledger), "--session", "S1",
                            "--since", "2027-01-01T00:00:00Z")
        check("U8 FAULT arm for the filter: --since after everything -> 0 responses", "responses 0 " in out, out)

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


def real_smoke() -> None:
    """U7: the real folder, read-only. Not a gate (it depends on this machine's transcripts)."""
    roots = ua.project_roots(None)
    before = {str(p): p.stat().st_size for r in roots for p in r.rglob("*.json")}
    code, out = run_cli()
    print(out)
    shares_lines = [ln for ln in out.splitlines() if ln.startswith("context weight")]
    for ln in shares_lines:
        total = float(ln.rsplit("(sum ", 1)[1].rstrip(")"))
        check(f"U7 shares sum to 100 +/- 0.5 ({ln.split(':')[0]})", abs(total - 100) <= 0.5, ln[-20:])
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
