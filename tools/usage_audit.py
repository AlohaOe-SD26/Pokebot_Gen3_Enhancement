"""usage_audit.py -- where Claude usage goes, measured from the local transcripts (backlog P3, spec S1-6).

INTENT. Every cost lever in the improvement backlog ("-20-35 %", "cut agents at 150 calls", "map before Read") was an
ESTIMATE, and the audit behind the one real number ("step 5.2 was about 143M input-equivalent, about 36 % of a week",
07-CHANGELOG) was a throw-away script that never reached the repo. This tool makes that measurement repeatable, so
each lever becomes an A/B (project rule 9: drivers answer correctness, MEASUREMENTS answer frequency/cost).

WHAT IT READS (read-only, streamed line by line; a live transcript may end mid-line and that line is skipped and
counted as a bad line). Under every Claude Code project folder of this repo (default: the folders under
~/.claude/projects whose name starts with the Pokebot repo or learner-clone prefix; `tools/ops/ops_config.json`
key `transcript_dirs` overrides; `--root` overrides both):
  <session>.jsonl                                        the main chat
  <session>/subagents/agent-*.jsonl (+ .meta.json)       Agent-tool subagents
  <session>/subagents/workflows/wf_*/agent-*.jsonl       workflow agents (stage label from .meta.json / journal.jsonl)
  <session>/workflows/wf_*.json                          the finished workflow (name, timestamp, description)

HOW IT COUNTS (each choice is a place a wrong proxy would rank the wrong lever, so each is stated):
  * ONE API RESPONSE IS COUNTED ONCE. A response is streamed as several transcript lines that share `message.id`
    (one per content block, each repeating the usage); keyed on that id, the max of each usage field is kept.
    Counting lines instead roughly triples the tokens (selftest U2 proves the dedupe is load-bearing).
  * INPUT-EQUIVALENT (ie) = input x1 + cache write 5m x1.25 + cache write 1h x2 + cache read x0.1 + output x5. The
    weights come from `PROJECT KNOWLEDGE/ai-research-notes/2026-10-19-backlog-round2/02-cost.md` (the 1h-write 2x is
    the API's price ratio; that note names only 1.25x). The 06 2026-10-15 "143M" figure did NOT record its weights,
    so every report prints the weights it used. Corroboration, not proof (2026-10-21 first run): with these weights
    the step-5.2 workflow `ai-player-step52-gates-productive-curiosity` measures 144.0 Mtok, beside the recorded 143M.
  * "% OF A WEEK" is a FIT, through the origin, over calibration points (meter percent vs measured ie). The seed is
    the single 143M = 36 % point; `--calibrate <ie_mtok> <percent>` appends more. The line always says ESTIMATE and
    how many points it rests on: with one point it is a ratio, not a measurement.
  * CONTEXT WEIGHT (a proxy, not a bill) of a tool result = its characters x the number of LATER responses in that
    agent, because every later turn re-reads it. Bash is categorised by its FIRST REAL COMMAND token (after `cd x &&`,
    env assignments, `time`/`sudo`), never by a substring: `git commit -m "cat the log"` is not a `cat` (U3).
  * A COLD RE-WRITE is a response whose cache write exceeds half of the previous response's whole context after a gap
    of more than 300 s (the 5-minute prompt cache expired, so the context was paid for again).
  * UNTEMPLATED: a workflow agent whose first prompt lacks `<!-- stage-template:<role>@<ver> -->` (spec S2-3); this is
    how template compliance is measured rather than assumed.

WHAT IT WRITES. Nothing, unless asked: `--append` adds ONE row per finished workflow to
`PROJECT KNOWLEDGE/cost-ledger.jsonl` (append-only; a changed re-run appends rev+1, an unchanged one appends nothing;
readers take the newest rev per key). Rows hold numbers and labels capped at 80 characters, NEVER prompt text.
`--calibrate` appends one calibration row there.

Run:  py -3.12 tools/usage_audit.py                     the ~25-line report over everything
      py -3.12 tools/usage_audit.py --append            ... and append the ledger rows
      py -3.12 tools/usage_audit.py --session <id> [--since 2026-10-21T11:00:00Z]   ONE line for one session
      py -3.12 tools/usage_audit.py --calibrate 150 37  record a (measured ie Mtok, weekly meter %) pair
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "PROJECT KNOWLEDGE" / "cost-ledger.jsonl"
OPS_CONFIG = REPO / "tools" / "ops" / "ops_config.json"
PROJECTS = Path.home() / ".claude" / "projects"
DEFAULT_PREFIXES = ("C--Remote-Projects-Pokebot-Gen3-Enhancement", "C--Remote-Projects-pokebot-learner")

WEIGHTS = {"input": 1.0, "cw5m": 1.25, "cw1h": 2.0, "cache_read": 0.1, "output": 5.0}
WEIGHTS_TEXT = "WEIGHTS (input-equivalent): input 1x, cache write 5m 1.25x, cache write 1h 2x, cache read 0.1x, output 5x"
SEED_CALIBRATION = [(143.0, 36.0)]  # 07-CHANGELOG: step 5.2 = about 143M input-equivalent = about 36 % of a week
MARKER = "<!-- stage-template:"
CAP = 80
GAP_S = 300
CATEGORIES = ("read_py", "read_md", "read_evidence", "read_other", "bash_cat", "bash_grep", "bash_suite",
              "bash_other", "search_tool", "other_tool")
CAT_CMDS = {"cat", "sed", "head", "tail", "get-content", "gc"}
GREP_CMDS = {"grep", "rg", "egrep", "fgrep", "findstr", "select-string", "sls"}
PREFIX_CMDS = {"time", "sudo", "env", "command", "nice", "do", "then", "else", "!", "&"}  # `&` = PowerShell call op
PREFIX_WITH_ARG = {"timeout"}       # `timeout 600 py x.py`: the duration is not the command
NAV_CMDS = {"cd", "pushd", "popd", "set-location", "export", "set", "source", ".", "for", "while", "until", "if",
            "done", "fi"}
PY_OPTS_WITH_ARG = {"-x", "-w", "-m", "-c"}   # `py -3.12 -X utf8 x.py`: `utf8` is not the script
ENV_ASSIGN = re.compile(r"^(\$env:)?[A-Za-z_][A-Za-z0-9_]*=", re.I)
PY_CMDS = {"py", "python", "python3", "pytest"}
SUITE_RE = re.compile(r"(test|probe|selftest|gates)", re.I)
EVIDENCE_SUFFIXES = {".log", ".txt", ".out"}


def response_key(line: dict):
    """The identity of ONE API response. Tests monkeypatch this to prove the dedupe matters (U2)."""
    return (line.get("message") or {}).get("id")


def parse_ts(text):
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def split_segments(cmd: str) -> list[str]:
    """Split a shell command on && || ; | and newlines OUTSIDE quotes (a quoted '&& cat' is not a command)."""
    out, cur, quote, i = [], [], None, 0
    while i < len(cmd):
        ch = cmd[i]
        if quote:
            if ch == "\\" and quote == '"' and i + 1 < len(cmd):
                cur.append(cmd[i:i + 2]); i += 2; continue
            if ch == quote:
                quote = None
            cur.append(ch); i += 1; continue
        if ch in "'\"":
            quote = ch; cur.append(ch); i += 1; continue
        if cmd[i:i + 2] in ("&&", "||"):
            out.append("".join(cur)); cur = []; i += 2; continue
        if ch in ";|\n":
            out.append("".join(cur)); cur = []; i += 1; continue
        cur.append(ch); i += 1
    out.append("".join(cur))
    return [s.strip() for s in out if s.strip()]


def _name(tok: str) -> str:
    tok = tok.strip("'\"").replace("\\", "/").rsplit("/", 1)[-1].lower()
    return tok[:-4] if tok.endswith(".exe") else tok


def bash_category(cmd: str) -> str:
    """Category of a Bash/PowerShell command by its FIRST REAL command token (spec S1-6), never by a substring."""
    for seg in split_segments(cmd or ""):
        toks = seg.split()
        while toks and (ENV_ASSIGN.match(toks[0]) or _name(toks[0]) in PREFIX_CMDS | PREFIX_WITH_ARG):
            toks = toks[2:] if _name(toks[0]) in PREFIX_WITH_ARG else toks[1:]
        if not toks:
            continue
        name = _name(toks[0])
        if name in NAV_CMDS:
            continue
        if name in CAT_CMDS:
            return "bash_cat"
        if name in GREP_CMDS:
            return "bash_grep"
        if name == "pytest":
            return "bash_suite"
        if name in PY_CMDS:
            rest, script = toks[1:], ""
            while rest:
                tok = rest.pop(0)
                if tok.lower() == "-m":          # `py -m pytest` / `py -m unittest`
                    script = rest[0] if rest else ""
                    break
                if tok.lower() == "-c" or tok == "-":
                    break                        # inline code is never a suite run
                if tok.lower() in PY_OPTS_WITH_ARG:
                    rest = rest[1:]
                    continue
                if not tok.startswith("-"):
                    script = tok
                    break
            return "bash_suite" if script and SUITE_RE.search(_name(script)) else "bash_other"
        return "bash_suite" if SUITE_RE.search(name) and "." in name else "bash_other"
    return "bash_other"


def tool_category(name: str, inp: dict) -> str:
    inp = inp if isinstance(inp, dict) else {}
    if name == "Read":
        path = str(inp.get("file_path", "")).replace("\\", "/").lower()
        suffix = Path(path).suffix
        if suffix == ".py":
            return "read_py"
        if "/evidence/" in path or suffix in EVIDENCE_SUFFIXES:
            return "read_evidence"
        return "read_md" if suffix == ".md" else "read_other"
    if name in ("Bash", "PowerShell"):
        return bash_category(str(inp.get("command", "")))
    return "search_tool" if name in ("Grep", "Glob") else "other_tool"


def result_chars(content) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(x.get("text", "")) if isinstance(x, dict) else len(str(x)) for x in content)
    return 0


def family(model: str) -> str:
    m = (model or "").lower()
    return next((f for f in ("opus", "sonnet", "haiku") if f in m), "other")


def ie_of(u: dict) -> float:
    return sum(WEIGHTS[k] * u.get(k, 0) for k in WEIGHTS)


class Agent:
    """One transcript file: its responses (deduped by response_key) and its tool results with their weights."""

    def __init__(self, path: Path, session: str, kind: str, workflow, stage: str, phase: str):
        self.path, self.session, self.kind, self.workflow = path, session, kind, workflow
        self.stage, self.phase = stage[:CAP], phase[:CAP]
        self.resp: dict = {}          # key -> usage dict + model + first/last ts
        self.order: list = []
        self.tool_calls: Counter = Counter()
        self.results: list = []       # (category, chars, responses_so_far, read_path, ranged)
        self.templated = None          # None = no first prompt seen
        self.weights: Counter = Counter()
        self.heavy_reads: list = []

    def usage(self) -> dict:
        tot: Counter = Counter()
        for r in self.resp.values():
            for k in WEIGHTS:
                tot[k] += r[k]
        return dict(tot)

    def finish(self) -> None:
        total = len(self.order)
        for cat, chars, k, path, ranged in self.results:
            w = chars * (total - k)
            self.weights[cat] += w
            if path is not None:
                self.heavy_reads.append((w, chars, total - k, path, ranged))

    def cold_rewrites(self) -> list:
        out, prev = [], None
        for key in self.order:
            cur = self.resp[key]
            if prev is not None and is_cold_rewrite(prev, cur):
                out.append(cur)
            prev = cur
        return out


def is_cold_rewrite(prev: dict, cur: dict) -> bool:
    """Cache write above half of the previous whole context, after an idle gap over GAP_S seconds."""
    if not prev.get("last_ts") or not cur.get("first_ts"):
        return False
    gap = (cur["first_ts"] - prev["last_ts"]).total_seconds()
    context = prev["input"] + prev["cw5m"] + prev["cw1h"] + prev["cache_read"]
    return gap > GAP_S and context > 0 and (cur["cw5m"] + cur["cw1h"]) > 0.5 * context


def scan_file(path: Path, agent: Agent, stats: Counter, since=None, lean: bool = False) -> Agent:
    """Stream one transcript. `lean` (the --session fast path) skips tool results and parses only assistant lines."""
    uses: dict = {}
    with open(path, "rb") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            if lean and b'"assistant"' not in raw:
                continue
            try:
                d = json.loads(raw)
            except ValueError:
                stats["bad_lines"] += 1
                continue
            if not isinstance(d, dict):
                continue
            typ, msg = d.get("type"), d.get("message")
            if not isinstance(msg, dict):
                continue
            ts = parse_ts(d.get("timestamp"))
            content = msg.get("content")
            if typ == "user" and not lean:
                if agent.templated is None and not (isinstance(content, list) and any(
                        isinstance(x, dict) and x.get("type") == "tool_result" for x in content)):
                    agent.templated = MARKER in (content if isinstance(content, str) else json.dumps(content))
                if isinstance(content, list) and not (since and ts and ts < since):
                    for x in content:
                        if isinstance(x, dict) and x.get("type") == "tool_result":
                            name, inp, cat = uses.get(x.get("tool_use_id"), ("?", {}, "other_tool"))
                            read_path = str(inp.get("file_path", "")) if name == "Read" else None
                            ranged = bool(inp.get("offset") or inp.get("limit")) if name == "Read" else True
                            agent.results.append((cat, result_chars(x.get("content")), len(agent.order),
                                                  read_path, ranged))
            elif typ == "assistant":
                key, u = response_key(d), msg.get("usage")
                if key is None or not isinstance(u, dict) or msg.get("model") == "<synthetic>":
                    continue
                if since and ts and ts < since:
                    continue
                cc = u.get("cache_creation") or {}
                vals = {"input": u.get("input_tokens") or 0, "cache_read": u.get("cache_read_input_tokens") or 0,
                        "output": u.get("output_tokens") or 0,
                        "cw1h": cc.get("ephemeral_1h_input_tokens") or 0}
                vals["cw5m"] = cc.get("ephemeral_5m_input_tokens") or max(
                    0, (u.get("cache_creation_input_tokens") or 0) - vals["cw1h"])
                r = agent.resp.get(key)
                if r is None:
                    r = agent.resp[key] = {**vals, "model": msg.get("model") or "", "first_ts": ts, "last_ts": ts}
                    agent.order.append(key)
                else:
                    for k, v in vals.items():
                        r[k] = max(r[k], v)
                    r["last_ts"] = ts or r["last_ts"]
                if isinstance(content, list) and not lean:
                    for x in content:
                        if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("id") not in uses:
                            inp = x.get("input") if isinstance(x.get("input"), dict) else {}
                            uses[x.get("id")] = (x.get("name", "?"), inp, tool_category(x.get("name", ""), inp))
                            agent.tool_calls[x.get("name", "?")] += 1
    agent.finish()
    return agent


def project_roots(cli_roots) -> list[Path]:
    if cli_roots:
        return [Path(r) for r in cli_roots]
    try:
        dirs = json.loads(OPS_CONFIG.read_text(encoding="utf-8")).get("transcript_dirs")
        if dirs:
            return [Path(d) for d in dirs]
    except (OSError, ValueError, AttributeError):
        pass
    if not PROJECTS.is_dir():
        return []
    return sorted(p for p in PROJECTS.iterdir() if p.is_dir() and p.name.lower().startswith(
        tuple(x.lower() for x in DEFAULT_PREFIXES)))


def _meta(path: Path) -> dict:
    try:
        return json.loads(path.with_name(path.stem + ".meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _journal(wf_dir: Path, cache: dict) -> dict:
    if wf_dir not in cache:
        labels = {}
        try:
            for raw in wf_dir.joinpath("journal.jsonl").read_bytes().splitlines():
                try:
                    d = json.loads(raw)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("agentId"):
                    labels[d["agentId"]] = (str(d.get("label") or ""), str(d.get("phase") or ""))
        except OSError:
            pass
        cache[wf_dir] = labels
    return cache[wf_dir]


def discover(roots, session=None) -> list[tuple[Path, str, str, object, str, str]]:
    """(path, session, kind, workflow id, stage, phase) for every transcript, optionally one session only."""
    out, jcache = [], {}
    for root in roots:
        if not root.is_dir():
            continue
        if session:
            files = ([root / f"{session}.jsonl"] if (root / f"{session}.jsonl").is_file() else []) + \
                    (sorted((root / session).rglob("*.jsonl")) if (root / session).is_dir() else [])
        else:
            files = sorted(root.rglob("*.jsonl"))
        for p in files:
            if p.name == "journal.jsonl":
                continue
            rel = p.relative_to(root).parts
            if len(rel) == 1:
                out.append((p, p.stem, "main", None, "main", ""))
                continue
            sess, meta = rel[0], _meta(p)
            if "workflows" in rel and p.parent.name.startswith("wf_"):
                label, phase = _journal(p.parent, jcache).get(p.stem.replace("agent-", ""), ("", ""))
                out.append((p, sess, "workflow", p.parent.name, str(meta.get("description") or label or "?"),
                            str(meta.get("workflowPhase") or phase)))
            elif "subagents" in rel:
                out.append((p, sess, "subagent", None, str(meta.get("description") or meta.get("agentType") or "?"),
                            ""))
    return out


def workflow_info(root_of: dict, session: str, wf: str) -> dict:
    """Name, start time, description and completeness of a workflow (its wf_*.json exists only once it finished)."""
    sdir = root_of.get(session)
    info = {"name": wf, "wf_ts": None, "desc": "", "complete": False}
    if sdir is None:
        return info
    jpath = sdir / "workflows" / f"{wf}.json"
    script = ""
    try:
        d = json.loads(jpath.read_text(encoding="utf-8"))
        info.update(complete=True, name=d.get("workflowName") or wf, wf_ts=d.get("timestamp"),
                    desc=str(d.get("summary") or ""))
        script = d.get("script") or ""
    except (OSError, ValueError):
        for s in sorted((sdir / "workflows" / "scripts").glob(f"*{wf}.js")) if (sdir / "workflows").is_dir() else []:
            try:
                script = s.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    m = re.search(r"\bname:\s*['\"]([^'\"]+)['\"]", script)
    if m and info["name"] == wf:
        info["name"] = m.group(1)
    m = re.search(r"\bdescription:\s*['\"]([^'\"]+)['\"]", script)
    if m and not info["desc"]:
        info["desc"] = m.group(1)
    info["name"], info["desc"] = str(info["name"])[:CAP], str(info["desc"])[:CAP]
    return info


def read_ledger(path: Path) -> list[dict]:
    rows = []
    try:
        for raw in path.read_bytes().splitlines():
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            if isinstance(d, dict):
                rows.append(d)
    except OSError:
        pass
    return rows


def calibration_points(ledger: Path) -> list[tuple[float, float]]:
    pts = list(SEED_CALIBRATION)
    pts += [(float(r["ie_mtok"]), float(r["percent"])) for r in read_ledger(ledger)
            if r.get("kind") == "calibration" and r.get("ie_mtok") and r.get("percent") is not None]
    return pts


def week_pct(ie_mtok: float, pts) -> str:
    k = sum(m * p for m, p in pts) / sum(m * m for m, _ in pts)
    n = len(pts)
    return f"~{ie_mtok * k:.1f} % of a week (ESTIMATE, {n} calibration point{'s' if n != 1 else ''})"


def shares(weights: Counter) -> dict:
    tot = sum(weights.values()) or 1
    return {c: round(100.0 * weights[c] / tot, 1) for c in CATEGORIES}


def load(roots, session=None, since=None, lean=False):
    stats: Counter = Counter()
    agents, root_of = [], {}
    for root in roots:
        if root.is_dir():
            for p in root.iterdir():
                if p.is_dir():
                    root_of.setdefault(p.name, p)
    for path, sess, kind, wf, stage, phase in discover(roots, session):
        stats["files"] += 1
        agents.append(scan_file(path, Agent(path, sess, kind, wf, stage, phase), stats, since, lean))
    return agents, stats, root_of


def ledger_rows(agents, root_of) -> list[dict]:
    """One row per workflow: numbers and <=80-char labels only (never prompt text)."""
    groups = defaultdict(list)
    for a in agents:
        if a.workflow:
            groups[(a.session, a.workflow)].append(a)
    rows = []
    for (sess, wf), group in sorted(groups.items()):
        info = workflow_info(root_of, sess, wf)
        stages = defaultdict(lambda: [0, 0, 0.0, ""])
        weights, models = Counter(), Counter()
        for a in group:
            st = stages[a.stage]
            st[0] += 1; st[1] += len(a.order); st[2] += ie_of(a.usage()); st[3] = a.phase
            weights.update(a.weights)
            for r in a.resp.values():
                models[family(r["model"])] += ie_of(r)
        ie = sum(ie_of(a.usage()) for a in group)
        rows.append({"kind": "workflow", "key": f"{sess}:{wf}", "session": sess, "workflow": info["name"],
                     "wf_id": wf, "wf_ts": info["wf_ts"], "desc": info["desc"], "complete": info["complete"],
                     "stage_rows": [{"stage": s, "phase": v[3], "agents": v[0], "calls": v[1],
                                     "ie_mtok": round(v[2] / 1e6, 3)} for s, v in sorted(stages.items())],
                     "agents": len(group), "calls": sum(len(a.order) for a in group),
                     "ie_mtok": round(ie / 1e6, 3),
                     "model_mix": {m: round(100.0 * v / (ie or 1), 1) for m, v in sorted(models.items())},
                     "categories": shares(weights),
                     "cold_rewrites": sum(len(a.cold_rewrites()) for a in group),
                     "over150": sum(1 for a in group if len(a.order) > 150),
                     "untemplated": sum(1 for a in group if a.templated is False)})
    return rows


def append_ledger(rows, ledger: Path, include_running: bool) -> tuple[int, int, int]:
    """Append-only. A key's newest row identical in its numbers -> nothing appended; otherwise rev+1."""
    newest = {}
    for r in read_ledger(ledger):
        if r.get("kind") == "workflow" and r.get("key"):
            if r.get("rev", 0) >= newest.get(r["key"], {}).get("rev", 0):
                newest[r["key"]] = r
    added = same = running = 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = []
    for row in rows:
        if not row["complete"] and not include_running:
            running += 1
            continue
        old = newest.get(row["key"])
        if old and {k: v for k, v in old.items() if k not in ("rev", "ts")} == row:
            same += 1
            continue
        lines.append(json.dumps({"key": row["key"], "rev": (old or {}).get("rev", 0) + 1, "ts": now, **row},
                                ensure_ascii=True))
        added += 1
    if lines:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(line + "\n" for line in lines))
    return added, same, running


def report(agents, stats, rows, ledger: Path, ledger_note: str, scope: str) -> list[str]:
    tot, weights, sub_w, models, tools = Counter(), Counter(), Counter(), Counter(), Counter()
    for a in agents:
        tot.update(a.usage())
        weights.update(a.weights)
        if a.kind != "main":
            sub_w.update(a.weights)
        tools.update(a.tool_calls)
        for r in a.resp.values():
            models[family(r["model"])] += ie_of(r)
    ie = ie_of(tot)
    calls = sum(len(a.order) for a in agents)
    kinds = Counter(a.kind for a in agents)
    cold = [(a, r) for a in agents for r in a.cold_rewrites()]
    cw_all = (tot["cw5m"] + tot["cw1h"]) or 1
    reads = sorted((h + (a,) for a in agents for h in a.heavy_reads), key=lambda t: -t[0])
    w_all = sum(weights.values()) or 1
    unranged = [h for h in reads if not h[4] and h[1] > 30_000]
    wf_agents = [a for a in agents if a.workflow]
    s, sa = shares(weights), shares(sub_w)
    big = sorted(agents, key=lambda a: -len(a.order))[:3]
    lines = [
        f"usage_audit {scope} | files {stats['files']} | bad_lines {stats['bad_lines']}",
        WEIGHTS_TEXT,
        f"responses {calls} | tool calls {sum(tools.values())} | agents {len(agents)} (main {kinds['main']}, "
        f"subagent {kinds['subagent']}, workflow {kinds['workflow']}) | workflows {len(rows)}",
        f"tokens (M): input {tot['input'] / 1e6:.2f}, cache write 5m {tot['cw5m'] / 1e6:.2f}, 1h "
        f"{tot['cw1h'] / 1e6:.2f}, cache read {tot['cache_read'] / 1e6:.2f}, output {tot['output'] / 1e6:.2f}",
        f"input-equivalent {ie / 1e6:.2f} Mtok = {week_pct(ie / 1e6, calibration_points(ledger))}",
        "model mix (share of ie): " + ", ".join(f"{m} {100.0 * v / (ie or 1):.1f} %" for m, v in models.most_common()),
        "context weight, ALL agents: " + ", ".join(f"{c} {s[c]}" for c in CATEGORIES) + f" (sum {sum(s.values()):.1f})",
        "context weight, SUBAGENTS: " + ", ".join(f"{c} {sa[c]}" for c in CATEGORIES) + f" (sum {sum(sa.values()):.1f})",
        "  round-2 reference (subagents): .py Reads 33.4 % | Bash cat/grep 36.5 % | suites 7.6 % | evidence 2.2 %",
        f"  this run          (subagents): .py Reads {sa['read_py']} % | Bash cat/grep "
        f"{sa['bash_cat'] + sa['bash_grep']:.1f} % | suites {sa['bash_suite']} % | evidence {sa['read_evidence']} %",
        f"cold re-writes (gap > {GAP_S} s, write > half the context): {len(cold)} in {len({id(a) for a, _ in cold})}"
        f" agents = {100.0 * sum(r['cw5m'] + r['cw1h'] for _, r in cold) / cw_all:.1f} % of cache-write tokens",
        f"agents over 150 responses: {sum(1 for a in agents if len(a.order) > 150)}, over 200: "
        f"{sum(1 for a in agents if len(a.order) > 200)} | biggest: "
        + ", ".join(f"{a.stage[:24]} {len(a.order)}" for a in big),
        f"unranged Reads over 30k chars: {len(unranged)} = {100.0 * sum(h[0] for h in unranged) / w_all:.1f} % "
        f"of context weight | untemplated workflow agents: {sum(1 for a in wf_agents if a.templated is False)} of "
        f"{len(wf_agents)}",
        "10 heaviest Reads (share of weight, chars x later responses, path):",
    ]
    for w, chars, later, path, ranged, a in reads[:10]:
        short = path.replace("\\", "/")
        short = short if len(short) <= 70 else "..." + short[-67:]
        lines.append(f"  {100.0 * w / w_all:5.2f} % {chars:>8} x {later:<4} {'' if ranged else '(unranged) '}{short}")
    lines.append(ledger_note)
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", action="append", help="a Claude Code project folder (repeatable; overrides defaults)")
    ap.add_argument("--ledger", default=str(LEDGER))
    ap.add_argument("--append", action="store_true", help="append one ledger row per finished workflow")
    ap.add_argument("--include-running", action="store_true", help="with --append, also rows for running workflows")
    ap.add_argument("--session", help="ONE line for one session (main chat + subagents + workflow agents)")
    ap.add_argument("--since", help="ISO time; only responses at or after it (naive = UTC)")
    ap.add_argument("--calibrate", nargs=2, type=float, metavar=("IE_MTOK", "PERCENT"))
    args = ap.parse_args(argv)
    ledger = Path(args.ledger)
    if args.calibrate:
        row = {"kind": "calibration", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "ie_mtok": args.calibrate[0], "percent": args.calibrate[1]}
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row) + "\n")
        print(f"calibration appended: {args.calibrate[0]} Mtok = {args.calibrate[1]} % -> {ledger}; "
              f"now {len(calibration_points(ledger))} points")
        return 0
    since = parse_ts(args.since) if args.since else None
    if args.since and since is None:
        print(f"usage_audit: --since {args.since!r} is not an ISO time")
        return 2
    roots = project_roots(args.root)
    t0 = time.time()
    if args.session:
        agents, stats, _ = load(roots, args.session, since, lean=True)
        kinds = Counter()
        for a in agents:
            kinds[a.kind] += len(a.order)
        ie = sum(ie_of(a.usage()) for a in agents) / 1e6
        print(f"session {args.session}{' since ' + args.since if args.since else ''}: responses "
              f"{sum(kinds.values())} (main {kinds['main']}, subagents {kinds['subagent']}, workflow "
              f"{kinds['workflow']}) | input-equivalent {ie:.2f} Mtok | {week_pct(ie, calibration_points(ledger))} "
              f"| files {stats['files']} bad_lines {stats['bad_lines']} | weights in 1, cw5m 1.25, cw1h 2, "
              f"read 0.1, out 5 | {time.time() - t0:.1f} s")
        return 0 if stats["files"] else 1
    agents, stats, root_of = load(roots, None, since)
    rows = ledger_rows(agents, root_of)
    if args.append:
        added, same, running = append_ledger(rows, ledger, args.include_running)
        note = f"ledger: appended {added} rows ({same} unchanged, {running} running skipped) -> {ledger}"
    else:
        note = "ledger: not written (pass --append)"
    scope = f"over {len(roots)} folder(s)" + (f" since {args.since}" if args.since else "")
    print("\n".join(report(agents, stats, rows, ledger, note + f" | {time.time() - t0:.1f} s", scope)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
