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
    agent, because every later turn re-reads it. It is reported on TWO axes:
    - BY OBJECT (the headline): what the result WAS -- source, doc, evidence (logs and run output), suite (a suite
      run's own stdout) or other -- decided from the path and suffix of the FILE ARGUMENTS of cat/sed/head/tail/
      grep/rg/awk/Get-Content/Select-String/type, of `gh api <path>`, or of a Read (path_object has the rule and its
      order). A call that reads several objects splits its weight evenly; one that reads none is "other". This axis
      exists because of 08-MISTAKES 2026-10-19: "a cost category must be defined by the OBJECT read, never by the
      command". The review of 2026-10-21 found the command buckets mixed docs, logs and source (bash_cat held 3 doc,
      2 evidence and 1 source read in a 25-call hand label), so "Bash cat/grep 33 %" could not say source vs logs.
      Selftest U8 holds this axis to the reviewer's 25 hand labels.
    - by COMMAND (secondary, the spec S1-6 buckets; it answers "which tool habit"): Bash is categorised by its FIRST
      REAL COMMAND token (after `cd x &&`, env assignments, `time`/`sudo`, and echo/printf/Write-Output header lines),
      never by a substring: `git commit -m "cat the log"` is not a `cat` (U3). A suite is a test/probe/selftest/gates
      script by basename OR by folder (`ai_player/gates/check_purity.py`).
  * NOT COUNTED: the bot tuner's consults. `ai-agent/consult.py` runs `claude -p ... --no-session-persistence`, which
    writes no transcript, so they are outside every total here; the report says so.
  * A COLD RE-WRITE is a response whose cache write exceeds half of the previous response's whole context after a gap
    of more than 300 s (the 5-minute prompt cache expired, so the context was paid for again).
  * UNTEMPLATED: a workflow agent whose first prompt lacks `<!-- stage-template:<role>@<ver> -->` (spec S2-3); this is
    how template compliance is measured rather than assumed.

WHAT IT WRITES. Nothing, unless asked: `--append` adds ONE row per finished workflow to
`PROJECT KNOWLEDGE/cost-ledger.jsonl` (append-only; a changed re-run appends rev+1, an unchanged one appends nothing;
readers take the newest rev per key). Rows hold numbers and labels capped at 80 characters, NEVER prompt text.
Rows written since 2026-10-21 also carry `objects` (shares by object) and `classifier: 2`; older rows (no
`classifier` field = classifier 1) are never rewritten, and a workflow whose USAGE is unchanged is not re-appended
just because the classifier moved its buckets (same_numbers), so compare `categories` only between rows of the same
classifier. `--calibrate` appends one calibration row there.

Run:  py -3.12 tools/usage_audit.py                     the ~30-line report over everything
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
# Navigation and HEADER printing: skipped when looking for the first real command. `echo "=== X ==="; cat x` is a
# cat; before echo/printf/Write-Output were here, 3,681 real calls that were cat/grep runs behind an echo header
# were filed as bash_other (review 2026-10-21, finding 10).
NAV_CMDS = {"cd", "pushd", "popd", "set-location", "export", "set", "source", ".", "for", "while", "until", "if",
            "done", "fi", "echo", "printf", "write-output", "write-host"}
PY_OPTS_WITH_ARG = {"-x", "-w", "-m", "-c"}   # `py -3.12 -X utf8 x.py`: `utf8` is not the script
ENV_ASSIGN = re.compile(r"^(\$env:)?[A-Za-z_][A-Za-z0-9_]*=", re.I)
PY_CMDS = {"py", "python", "python3", "pytest"}
SUITE_RE = re.compile(r"(test|probe|selftest|gates)", re.I)
# A suite also lives in a suite FOLDER: `ai_player/gates/check_purity.py` has no test/probe in its basename.
SUITE_DIR_RE = re.compile(r"(^|/)(tests?|gates|probes?|selftests?)/", re.I)
EVIDENCE_SUFFIXES = {".log", ".txt", ".out"}

# THE OBJECT AXIS (08-MISTAKES 2026-10-19: "a cost category must be defined by the OBJECT read, never by the
# command"). The command axis above answers "which tool habit"; this one answers "what did the context fill up WITH",
# which is the question a lever like "map before Read" or "summarise logs" is about. Headline order:
OBJECTS = ("source", "doc", "evidence", "suite", "other")
# Code is source. Config and data tables (.json/.yaml/.toml/.ini) are source too: they ARE the program (e.g.
# tools/ops/ops_config.json, modules/data tables), and reading one is reading the program, not a run's output.
# EXCEPT under evidence/, debug-logs/ or a scratchpad, where the same suffix is what a run wrote (see path_object).
CODE_SUFFIXES = {".py", ".pyi", ".c", ".h", ".s", ".inc", ".js", ".mjs", ".ts", ".ps1", ".psm1", ".sh", ".bat",
                 ".cmd", ".lua"}
CONFIG_SUFFIXES = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
DOC_SUFFIXES = {".md", ".rst"}
LOG_SUFFIXES = {".log", ".txt", ".out", ".err", ".jsonl", ".csv"}     # .jsonl = logs, ledgers, transcripts
RUN_OUTPUT_DIR_RE = re.compile(r"(^|/)(evidence|debug-logs)(/|$)", re.I)
SCRATCH_DIR_RE = re.compile(r"(^|/)scratchpad(/|$)", re.I)
# Commands whose stdout IS the file they are given. The ones in PROGRAM_FIRST take a pattern or program as their
# first positional argument, which is not a file (unless it came through -e / -f / -Pattern instead).
READER_CMDS = {"cat", "type", "sed", "head", "tail", "less", "more", "nl", "awk", "gawk", "grep", "rg", "egrep",
               "fgrep", "findstr", "get-content", "gc", "select-string", "sls"}
PROGRAM_FIRST = {"sed", "awk", "gawk", "grep", "rg", "egrep", "fgrep", "findstr", "select-string", "sls"}
PS_READERS = {"get-content", "gc", "select-string", "sls"}   # PowerShell options are case-insensitive words
# Options that consume the NEXT token, per command (case-sensitive for the Unix tools: grep -A 3 takes a value,
# grep -a does not). A value mistaken for a file would invent an object; a file mistaken for a value would drop one.
OPTS_WITH_ARG = {
    "head": {"-n", "-c", "--lines", "--bytes"}, "tail": {"-n", "-c", "--lines", "--bytes"},
    "grep": {"-A", "-B", "-C", "-m", "-e", "-f", "-d", "-D", "--max-count", "--context", "--regexp", "--file"},
    "rg": {"-A", "-B", "-C", "-m", "-M", "-e", "-f", "-g", "-t", "-T", "--glob", "--type", "--max-count",
           "--context", "--regexp", "--file"},
    "awk": {"-F", "-v", "-f"}, "sed": {"-e", "-f"},
    "get-content": {"-totalcount", "-tail", "-head", "-first", "-encoding", "-delimiter", "-readcount"},
    "select-string": {"-pattern", "-context", "-encoding"},
}
for _a, _b in (("egrep", "grep"), ("fgrep", "grep"), ("gawk", "awk"), ("gc", "get-content"), ("sls", "select-string")):
    OPTS_WITH_ARG[_a] = OPTS_WITH_ARG[_b]
PATTERN_OPTS = {"-e", "-f", "--regexp", "--file", "-pattern"}  # the pattern/program came this way: positionals = files
PATH_OPTS = {"-path", "-literalpath"}                          # PowerShell: the next token IS a file
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


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


def _split(cmd: str) -> list[tuple[str, str]]:
    """(segment, the separator AFTER it) for && || ; | and newlines OUTSIDE quotes; the last separator is ""."""
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
            out.append(("".join(cur), cmd[i:i + 2])); cur = []; i += 2; continue
        if ch in ";|\n":
            out.append(("".join(cur), ch)); cur = []; i += 1; continue
        cur.append(ch); i += 1
    out.append(("".join(cur), ""))
    return out


def split_segments(cmd: str) -> list[str]:
    """Split a shell command on && || ; | and newlines OUTSIDE quotes (a quoted '&& cat' is not a command)."""
    return [s.strip() for s, _ in _split(cmd) if s.strip()]


def split_pipelines(cmd: str) -> list[list[str]]:
    """The segments grouped into PIPELINES (joined by a single `|`): only a pipeline's LAST stdout reaches the
    context, so `gh api X | base64 -d > f.c` shows nothing even though its first segment fetched source."""
    out, cur = [], []
    for seg, sep in _split(cmd):
        if seg.strip():
            cur.append(seg.strip())
        if sep != "|" and cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


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
            return "bash_suite" if script and is_suite_path(script) else "bash_other"
        return "bash_suite" if "." in name and is_suite_path(toks[0]) else "bash_other"
    return "bash_other"


def is_suite_path(script: str) -> bool:
    """A suite/probe/gate script: by its basename (selftest_x.py, probe_y.py) OR by the folder it lives in
    (ai_player/gates/check_purity.py). Matching the basename only filed real gate runs as bash_other (finding 10)."""
    path = script.strip("'\"").replace("\\", "/")
    return bool(SUITE_RE.search(_name(path)) or SUITE_DIR_RE.search(path))


def _py_script(toks: list[str]) -> tuple[str, bool]:
    """(script, is_module) of a `py ...` command line after the interpreter token; ("", False) for inline code."""
    rest = list(toks)
    while rest:
        tok = rest.pop(0)
        if tok.lower() == "-m":
            return (rest[0] if rest else ""), True
        if tok.lower() == "-c" or tok == "-":
            return "", False
        if tok.lower() in PY_OPTS_WITH_ARG:
            rest = rest[1:]
            continue
        if not tok.startswith("-"):
            return tok, False
    return "", False


def path_object(path: str) -> str:
    """The OBJECT a file path is: source, doc, evidence (run output and logs) or other. Order matters and is the
    documented rule: (1) anything under evidence/ or debug-logs/ is evidence, whatever its suffix; (2) code suffixes
    are source, even in a scratchpad (an agent's own script is still a script); (3) anything else in a scratchpad
    is a run's or an agent's OUTPUT, so evidence -- including a scratchpad .md such as recon_results.md, which is a
    result written by an agent, not project documentation; (4) .md is doc; (5) log suffixes are evidence; (6)
    config/data suffixes are source; (7) otherwise other (a directory with no file filter, a binary, an unknown
    suffix: the object is not known)."""
    p = path.strip("'\"").replace("\\", "/").split("?", 1)[0].rstrip("/").lower()
    suffix = Path(p).suffix
    if RUN_OUTPUT_DIR_RE.search(p):
        return "evidence"
    if suffix in CODE_SUFFIXES:
        return "source"
    if SCRATCH_DIR_RE.search(p):
        return "evidence"
    if suffix in DOC_SUFFIXES:
        return "doc"
    if suffix in LOG_SUFFIXES:
        return "evidence"
    if suffix in CONFIG_SUFFIXES:
        return "source"
    return "other"


def strip_heredocs(cmd: str) -> str:
    """Drop here-document and PowerShell here-string BODIES. `cat > x.py <<'EOF' ... EOF` writes a file; its body
    lines are text, and a body line such as `grep -n foo big.log` is not a command that put a log in the context."""
    out, end = [], None
    for line in cmd.split("\n"):
        if end is not None:
            if line.strip() == end:
                end = None
            continue
        out.append(line)
        m = HEREDOC_RE.search(line)
        if m:
            end = m.group(2)
        elif re.search(r"@['\"]\s*$", line):
            end = "'@" if line.rstrip().endswith("'") else '"@'
    return "\n".join(out)


def _tokens(seg: str, powershell: bool) -> list[tuple[str, bool]]:
    """Shell words of one segment as (text, bare): quotes removed, `"$D"/x.h` kept as ONE word, and `bare` False
    when the word began inside quotes (so a quoted "<pattern>" is never taken for a redirection). A backslash
    escapes only a quote, a backslash or a space (bash) and never in PowerShell, so `C:\\a\\b.py` survives."""
    out, cur, quote, bare, started, i = [], [], None, True, False, 0
    while i < len(seg):
        ch = seg[i]
        if quote:
            if ch == quote:
                quote = None
            elif ch == "\\" and quote == '"' and not powershell and seg[i + 1:i + 2] in ('"', "\\"):
                cur.append(seg[i + 1]); i += 1
            else:
                cur.append(ch)
        elif ch in "'\"":
            quote = ch
            if not started:
                bare, started = False, True
        elif ch.isspace():
            if started:
                out.append(("".join(cur), bare))
            cur, bare, started = [], True, False
        elif ch == "\\" and not powershell and seg[i + 1:i + 2] in ('"', "'", " ", "\\"):
            cur.append(seg[i + 1]); i += 1; started = True
        else:
            cur.append(ch); started = True
        i += 1
    if started:
        out.append(("".join(cur), bare))
    return out


def _reader_files(name: str, args: list[str]) -> list[str]:
    """The FILE arguments of a reader command (cat/sed/grep/Get-Content/...): not its options, option values,
    pattern or program, and not redirection targets."""
    want = OPTS_WITH_ARG.get(name, set())
    ps = name in PS_READERS
    positional, named, pattern_given, i = [], [], False, 0
    while i < len(args):
        tok = args[i]
        key = tok.lower() if ps else tok
        if ps and key in PATH_OPTS:
            named += args[i + 1:i + 2]
            i += 2
            continue
        if name in ("grep", "egrep", "fgrep", "rg"):
            # a file FILTER names the object of a folder search: --include=*.py, rg -g '*.md', rg -t py
            flt = None
            if "=" in tok and tok.split("=", 1)[0] in ("--include", "--glob", "--type"):
                flt, step = tok.split("=", 1), 1
                flt = flt[1] if flt[0] != "--type" else "x." + flt[1]
            elif (tok == "--include" or (name == "rg" and tok in ("--glob", "-g", "--type", "-t"))) \
                    and i + 1 < len(args):
                flt, step = args[i + 1], 2
                flt = flt if tok not in ("--type", "-t") else "x." + flt
            if flt is not None:
                named.append("*" + flt.lstrip("*"))
                i += step
                continue
        if key in PATTERN_OPTS or (name in ("awk", "gawk") and key == "-f"):
            pattern_given = True
        if key in want:
            i += 2
            continue
        if name == "findstr" and tok.startswith("/") and (len(tok) <= 3 or tok[2:3] == ":"):
            i += 1
            continue
        if tok.startswith("-") and tok != "-":
            i += 1
            continue
        positional.append(tok)
        i += 1
    if name in PROGRAM_FIRST and not pattern_given and positional:
        positional = positional[1:]
    if named and any(n.startswith("*") for n in named) and positional:
        # `grep -rn X --include=*.py dir/`: the folder is searched only for that suffix -> the filter is the object
        positional = [p for p in positional if Path(p.rstrip("/")).suffix]
    return [p for p in named + positional if p and p != "-"]


def _strip_redirects(toks: list[tuple[str, bool]]) -> tuple[list[str], bool, list[str]]:
    """(words without redirections, STDOUT goes to a file?, files fed in with `<`). When stdout goes to a file,
    nothing the segment prints reaches the context. Only BARE words are redirections (see _tokens)."""
    out, to_file, fed, i = [], False, [], 0
    while i < len(toks):
        tok, bare = toks[i]
        m = re.match(r"^(\d?|&)(>>?|<<?)(.*)$", tok) if bare else None
        if m:
            fd, op, target = m.groups()
            if not target and i + 1 < len(toks):
                target = toks[i + 1][0]
                i += 1
            if op == "<":
                fed.append(target)
            elif op.startswith(">") and fd in ("", "1", "&") and not target.startswith("&"):
                to_file = True                     # `> x`, `1> x`, `&> x`; not `2> x` or `2>&1`
            i += 1
            continue
        out.append(tok)
        i += 1
    return out, to_file, fed


def command_objects(cmd: str, powershell: bool = False) -> list[str]:
    """Every OBJECT a Bash/PowerShell command put into the context, one entry per object read, in order.

    A segment contributes when it (a) runs a READER on file arguments (cat/sed/head/tail/grep/rg/awk/Get-Content/
    Select-String/type/...) -> each file's path_object; (b) is `gh api <path>` -> the fetched path's object (decomp
    source); (c) runs a suite/probe/gate script -> "suite" (its own stdout); (d) runs any other script -> "other".
    A reader fed by a pipe (`... | head -80`, no file) adds nothing: the object is whatever fed it. A pipeline whose
    final STDOUT is redirected to a file adds nothing (`gh api X | base64 -d > party_menu.c` puts nothing in the
    context; the later `grep ... party_menu.c` does), nor does `cat a.md > b.md`. Listing and inspection commands
    (ls, wc, git, mkdir, echo) are NOT objects: their output is small next to a file dump, and counting them would
    let `wc -l x.md` halve the weight of `sed -n x.md`.
    An empty list means the call read no known object; the caller files it as "other"."""
    objs: list[str] = []
    for pipeline in split_pipelines(strip_heredocs(cmd or "")):
        parsed = [_strip_redirects(_tokens(seg, powershell)) for seg in pipeline]
        if parsed[-1][1]:
            continue                       # the pipeline's final stdout goes to a file: nothing reached the context
        for toks, _to_file, fed in parsed:
            objs += _segment_objects(toks, fed)
    return objs


def _segment_objects(toks: list[str], fed: list[str]) -> list[str]:
    """The objects ONE segment shows (see command_objects for the rule). A redirect in the MIDDLE of a pipeline
    (`a > f | b`) is not special-cased: a mutation run showed no realistic command needs it."""
    while toks and (ENV_ASSIGN.match(toks[0]) or _name(toks[0]) in PREFIX_CMDS | PREFIX_WITH_ARG):
        toks = toks[2:] if _name(toks[0]) in PREFIX_WITH_ARG else toks[1:]
    if not toks:
        return []
    name = _name(toks[0])
    if name in READER_CMDS:
        return [path_object(f) for f in (_reader_files(name, toks[1:]) or fed)]
    if name == "gh" and len(toks) > 2 and toks[1] == "api":
        target = next((t for t in toks[2:] if not t.startswith("-")), "")
        return [path_object(target) if target else "other"]
    if name in PY_CMDS:
        script, module = _py_script(toks[1:])
        if name == "pytest" or (module and script in ("pytest", "unittest")) or (script and is_suite_path(script)):
            return ["suite"]
        return ["other"] if script or module else []
    if "." in name and Path(name).suffix in CODE_SUFFIXES:            # `./run_x.sh`, `probe_y.py` run directly
        return ["suite" if is_suite_path(toks[0]) else "other"]
    return []


def split_objects(objs: list[str]) -> dict[str, float]:
    """A call's weight split EVENLY over the objects it read (two files read -> half each); none -> all "other"."""
    if not objs:
        return {"other": 1.0}
    out: dict[str, float] = {}
    for o in objs:
        out[o] = out.get(o, 0.0) + 1.0 / len(objs)
    return out


def tool_objects(name: str, inp: dict) -> dict[str, float]:
    """The OBJECT axis of one tool call: {object: fraction of its weight}, fractions summing to 1."""
    inp = inp if isinstance(inp, dict) else {}
    if name == "Read":
        return {path_object(str(inp.get("file_path", ""))): 1.0}
    if name in ("Bash", "PowerShell"):
        return split_objects(command_objects(str(inp.get("command", "")), powershell=name == "PowerShell"))
    if name == "Grep":
        # the Grep tool's file filter names the object; a bare folder search does not
        typ = str(inp.get("type") or "")
        target = ("x." + typ) if typ else str(inp.get("glob") or inp.get("path") or "")
        return {path_object(target): 1.0}
    return {"other": 1.0}


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
        self.results: list = []       # (category, chars, responses_so_far, read_path, ranged, objects)
        self.templated = None          # None = no first prompt seen
        self.weights: Counter = Counter()      # the COMMAND axis (CATEGORIES)
        self.obj_weights: Counter = Counter()  # the OBJECT axis (OBJECTS): the same total, split by what was read
        self.heavy_reads: list = []

    def usage(self) -> dict:
        tot: Counter = Counter()
        for r in self.resp.values():
            for k in WEIGHTS:
                tot[k] += r[k]
        return dict(tot)

    def finish(self) -> None:
        total = len(self.order)
        for cat, chars, k, path, ranged, objs in self.results:
            w = chars * (total - k)
            self.weights[cat] += w
            for obj, frac in objs.items():
                self.obj_weights[obj] += w * frac
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
                            name, inp, cat, objs = uses.get(x.get("tool_use_id"),
                                                            ("?", {}, "other_tool", {"other": 1.0}))
                            read_path = str(inp.get("file_path", "")) if name == "Read" else None
                            ranged = bool(inp.get("offset") or inp.get("limit")) if name == "Read" else True
                            agent.results.append((cat, result_chars(x.get("content")), len(agent.order),
                                                  read_path, ranged, objs))
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
                            uses[x.get("id")] = (x.get("name", "?"), inp, tool_category(x.get("name", ""), inp),
                                                 tool_objects(x.get("name", ""), inp))
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


def shares(weights: Counter, keys=CATEGORIES) -> dict:
    tot = sum(weights.values()) or 1
    return {c: round(100.0 * weights[c] / tot, 1) for c in keys}


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
        weights, obj_weights, models = Counter(), Counter(), Counter()
        for a in group:
            st = stages[a.stage]
            st[0] += 1; st[1] += len(a.order); st[2] += ie_of(a.usage()); st[3] = a.phase
            weights.update(a.weights)
            obj_weights.update(a.obj_weights)
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
                     "objects": shares(obj_weights, OBJECTS), "classifier": CLASSIFIER,
                     "cold_rewrites": sum(len(a.cold_rewrites()) for a in group),
                     "over150": sum(1 for a in group if len(a.order) > 150),
                     "untemplated": sum(1 for a in group if a.templated is False)})
    return rows


# The CLASSIFIER that produced a row's `categories` and `objects`. 1 = rows written before 2026-10-21 (they have no
# `classifier` field and no `objects`); 2 = the object axis plus the echo-header and suite-folder fixes.
CLASSIFIER = 2
CLASSIFICATION_FIELDS = ("categories", "objects", "classifier")


def same_numbers(old: dict, row: dict) -> bool:
    """Is the newest ledger row for a key unchanged in its USAGE? The classification fields (how the context weight
    is split into buckets) are NOT compared. WHY, measured on a scratch copy of the ledger on 2026-10-21: comparing
    `categories`, the first --append after classifier 2 shipped would re-append a rev+1 copy of 91 of the 105
    finished workflows whose usage had not changed at all, because the echo/suite fixes move their `categories`
    (and comparing the new `objects` field would re-append all of them). A classifier change is not new usage. So
    an old row keeps its classifier-1 buckets and a reader compares buckets only between rows with the same
    `classifier`; a workflow whose usage DOES change is re-appended with the current classifier. The report is
    always computed fresh with the current classifier. (With this rule the same scratch copy appended only the 3
    workflows that had newly finished, and 102 unchanged.)"""
    def usage_part(r: dict) -> dict:
        return {k: v for k, v in r.items() if k not in ("rev", "ts") + CLASSIFICATION_FIELDS}
    return usage_part(old) == usage_part(row)


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
        if old and same_numbers(old, row):
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
    obj_w, sub_ow = Counter(), Counter()
    for a in agents:
        tot.update(a.usage())
        weights.update(a.weights)
        obj_w.update(a.obj_weights)
        if a.kind != "main":
            sub_w.update(a.weights)
            sub_ow.update(a.obj_weights)
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
    o, oa = shares(obj_w, OBJECTS), shares(sub_ow, OBJECTS)
    big = sorted(agents, key=lambda a: -len(a.order))[:3]
    pts = calibration_points(ledger)
    lines = [
        f"usage_audit {scope} | files {stats['files']} | bad_lines {stats['bad_lines']}",
        WEIGHTS_TEXT,
        f"responses {calls} | tool calls {sum(tools.values())} | agents {len(agents)} (main {kinds['main']}, "
        f"subagent {kinds['subagent']}, workflow {kinds['workflow']}) | workflows {len(rows)}",
        f"tokens (M): input {tot['input'] / 1e6:.2f}, cache write 5m {tot['cw5m'] / 1e6:.2f}, 1h "
        f"{tot['cw1h'] / 1e6:.2f}, cache read {tot['cache_read'] / 1e6:.2f}, output {tot['output'] / 1e6:.2f}",
        f"input-equivalent {ie / 1e6:.2f} Mtok = {week_pct(ie / 1e6, pts)}",
        "  the % rests on these calibration points (ie Mtok -> weekly meter %): " + "; ".join(
            f"{m:g} -> {p:g}" + (" (seed: 07-CHANGELOG step 5.2; the audit behind it is not in the repo)"
                                  if (m, p) in SEED_CALIBRATION else "") for m, p in pts),
        "  NOT COUNTED: the bot tuner's consults (ai-agent/consult.py runs `claude -p --no-session-persistence`, "
        "which leaves no transcript)",
        "model mix (share of ie): " + ", ".join(f"{m} {100.0 * v / (ie or 1):.1f} %" for m, v in models.most_common()),
        "context weight BY OBJECT read, ALL agents: " + ", ".join(f"{c} {o[c]}" for c in OBJECTS)
        + f" (sum {sum(o.values()):.1f})",
        "context weight BY OBJECT read, SUBAGENTS: " + ", ".join(f"{c} {oa[c]}" for c in OBJECTS)
        + f" (sum {sum(oa.values()):.1f})",
        "  secondary, by COMMAND (tool habit, not object), ALL: " + ", ".join(f"{c} {s[c]}" for c in CATEGORIES)
        + f" (sum {sum(s.values()):.1f})",
        "  secondary, by COMMAND, SUBAGENTS: " + ", ".join(f"{c} {sa[c]}" for c in CATEGORIES)
        + f" (sum {sum(sa.values()):.1f})",
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
