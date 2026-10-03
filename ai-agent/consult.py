"""Asking Claude for help between cycles. OFF by default (`config.json` -> consult.enabled).

When enabled, after each cycle the learner runs the Claude Code CLI in print mode with READ-ONLY tools (it can read
files and search; it cannot edit, run commands or push). Claude reads `findings/LATEST.md` and replies with a short
diagnosis and up to two proposals. Proposals go to `inbox/` and are checked against `knowledge.GENES` before any is
run, so a reply can only choose among knob values that have already run.

Code changes, relaunches and anything that needs judgment stay with an interactive Claude session, where a person
can see them. Every call is logged in `data/consult_log.jsonl`, and a daily cap bounds the cost.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path

import knowledge as K

PROMPT = """You are advising the Emerald AI strategy learner (folder ai-agent/ of this repo). Read ai-agent/README.md
and ai-agent/findings/LATEST.md. You may also read PROJECT KNOWLEDGE/05-KNOWN-ISSUES.md for what each failure means.
Do NOT edit any file.
Reply with:
1. A diagnosis of at most 10 lines: which strategy is winning, where runs end, and what the knob effects suggest.
2. Exactly one fenced ```json block of the form
   {"proposals": [{"name": "short-name", "why": "one sentence", "genes": {"POKEBOT_...": "0 or 1"}}],
    "for_the_developer": "what code change or investigation would help most, one paragraph"}
   with at most 2 proposals, using ONLY the knobs and values in LATEST.md's knob table. A knob you leave out stays at
   its baseline value. Propose combinations the table has NOT already measured well.
"""
JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def _calls_today(log: Path) -> int:
    if not log.exists():
        return 0
    today = dt.date.today().isoformat()
    return sum(1 for line in log.read_text(encoding="utf-8").splitlines() if line.startswith(f'{{"day": "{today}"'))


def maybe_consult(cfg: dict, repo: Path, ai: Path, tag: str) -> str:
    """Run one consult if enabled and under the daily cap. Returns a one-line outcome for the learner's log."""
    c = cfg.get("consult", {})
    if not c.get("enabled"):
        return "consult: off"
    log = ai / "data" / "consult_log.jsonl"
    if _calls_today(log) >= int(c.get("max_calls_per_day", 2)):
        return "consult: daily cap reached"
    exe = shutil.which("claude")
    if not exe:
        return "consult: the `claude` command is not on PATH"
    cmd = [exe, "-p", PROMPT, "--output-format", "text", "--max-turns", str(c.get("max_turns", 8)),
           "--allowedTools", "Read,Grep,Glob"]
    started = dt.datetime.now()
    try:
        proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=60 * float(c.get("timeout_minutes", 20)))
        reply, rc = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired:
        reply, rc = "", "timeout"
    (ai / "findings").mkdir(exist_ok=True)
    (ai / "findings" / f"claude-{tag}.md").write_text(reply or "(no reply)", encoding="utf-8")
    accepted = 0
    m = JSON_BLOCK.search(reply or "")
    if m:
        try:
            body = json.loads(m.group(1))
        except ValueError:
            body = {}
        for i, p in enumerate(body.get("proposals", [])[:2]):
            if isinstance(p, dict) and isinstance(p.get("genes"), dict) and not K.validate_genes(p["genes"]):
                (ai / "inbox").mkdir(exist_ok=True)
                (ai / "inbox" / f"claude-{tag}-{i + 1}.json").write_text(json.dumps(p, indent=1), encoding="utf-8")
                accepted += 1
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"day": dt.date.today().isoformat(), "tag": tag, "started": started.isoformat(),
                             "seconds": round((dt.datetime.now() - started).total_seconds()), "exit": rc,
                             "proposals_accepted": accepted}) + "\n")
    return f"consult: exit {rc}, {accepted} proposal(s) queued"
