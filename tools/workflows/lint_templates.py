"""Lint the workflow STAGE TEMPLATES (backlog P11 + P1 + P10, spec S2-3) and hold the ONE parser of their fields.

    py -3.12 tools/workflows/lint_templates.py            lint every template + models.json; exit 0 clean, 1 findings

WHY THIS EXISTS. Until 2026-10-21 no workflow prompt lived in the repo: every workflow script was typed fresh, so the
rules that made a prompt cheap and safe (what to read, with RANGES; what never to read whole; when to stop; how long
the answer may be; which model tier) were re-remembered or forgotten per script. The measured cost: 33 agents opened
with one 1.18 MB design note, agents past 200 calls (3 %) held 53 % of context weight, and Opus-class agents were about
90 % of input-equivalent (backlog P11). A template only helps while its fields are really there, so this lint checks
them mechanically; prose rules about prompts have failed here before (CLAUDE.md session discipline rule 6).

WHAT A TEMPLATE IS. `templates/<role>.md`. Line 1 is the marker `<!-- stage-template:<role>@<ver> -->`, exactly the
string `tools/usage_audit.py` looks for on the FIRST line of an agent's first prompt to count UNTEMPLATED agents (so
compliance is MEASURED, never assumed); no other line may be a marker. A FIELD is a `## NAME` heading at column 0
OUTSIDE a code fence and outside an HTML comment; its body runs to the next `## ` heading. A word in prose ("the MODEL
field"), a heading inside a fence or inside `<!-- -->` is a MENTION and neither satisfies nor breaks a field (the
mention rule of `lint_docs._blank_fenced`; that file runs its lint at import, so the logic is re-implemented here).
A fence opens with 3+ backticks or tildes; a backtick run whose info string holds another backtick is INLINE code
(```x``` at a line start), not a fence, so it cannot blank the rest of the file. Required fields: GOAL, READ-LIST,
DO-NOT-READ, STOP, RETURN-CAP, MODEL, WAIT-RULE, MAP-FIRST, LOOKUP-FIRST. Placeholders are `{{name}}` (a value is
required) or `{{name?}}` (may be empty); `render.py` fills them.

THE CHECKS (each one has a FAULT and a CONTROL arm in tools/story-dev/selftest_workflows.py):
  * the marker is line 1, names this file's role, and is the ONLY marker line; every required field is present
    exactly once and non-empty; a fence or an HTML comment that never closes is a finding (T-1, T-4);
  * READ-LIST: every line is a `- ` or `* ` bullet with a `backticked path`, an indented continuation of the bullet
    above, or a lone optional placeholder line. An entry is a whole file `path`, a line range `path:START-END`, or an
    ANCHORED range `path:@<line prefix>+N` (the N lines from the first line that starts with the prefix, the way
    `grep -n '^<prefix>'` finds it; `render.py` turns it into START-END). The BYTES actually read are measured from
    disk: a whole file, or a range's own lines, over READ_LIMIT is a finding (T-2). WHY the range's bytes and not the
    file's: `04-HANDOFF.md:1-120` is 74 KB because its line 6 alone is 23 KB, so "has a range" said nothing. A path
    that does not exist is a finding, ranged or not, unless the bullet says `[later]` (a file an earlier stage
    writes); a folder is a finding. An entry under a DO-NOT-READ path must carry a range (a slice may be read, the
    whole never); paths are RESOLVED against the repo root first (`./x`, `a/../x`, a `../<repo folder>/` detour,
    backslashes, the repo's absolute prefix, case: `repo_relative`), so a spelling cannot step round the list. A
    RELATIVE path that resolves outside the repo is a finding; an absolute one outside it (a scratch report) is
    allowed and size-checked. A path still holding a placeholder is checked when `render.py` fills it;
  * DO-NOT-READ holds the STANDING entries (`ai_player/evidence/`, `**/INDEX.md`, whole `07`/`08`, whole
    `ai_player/README.md`): the files whose whole-read made the heaviest contexts;
  * RETURN-CAP has `words: N` (1..200) and `file: <path>`: a stage hands over a short answer and a file, so the
    coordinator's context does not grow by every stage's full report;
  * MODEL is ONE line, `top|mid|cheap` (a `(note)` may follow), and equals `models.json`; `models.json`'s
    `agent_model` maps `top` to null (the coordinator's own model) and mid/cheap to a model name (T-3, T-5). A stage
    below `top` must name a `proof` (P10): the JSON a PLANT RUN wrote, COMMITTED in this repository, that names this
    stage, tier and template version AND the sha256 of this template's text (MODEL line aside: it is what the move
    changes), the run's id and an existing transcript, at least 3 planted defects of 3 different kinds whose input
    FILES exist and hash to the recorded sha256, a finding for each plant that QUOTES text of that plant's input, and
    one CLEAN control input (another file, hashed the same way) with ZERO findings. WHY so much: the source spec
    accepted any file containing `PLANT-CAUGHT`, which anyone can type; the first version of this check took any JSON
    of the right shape, which anyone can type too (review 2026-10-21), and an edited template kept its proof unless
    someone remembered to bump `@<ver>`. One caught plant is N = 1, and agreement is not a confidence signal.
    `verify` (the adversarial verify) is pinned to `top` in CODE, so no JSON edit can move it.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TEMPLATES = HERE / "templates"
MODELS = HERE / "models.json"

FIELDS = ("GOAL", "READ-LIST", "DO-NOT-READ", "STOP", "RETURN-CAP", "MODEL", "WAIT-RULE", "MAP-FIRST", "LOOKUP-FIRST")
TIERS = ("top", "mid", "cheap")
#: The adversarial verify stays top tier BY RULE (spec S2-3; backlog P11 "design, root cause and the adversarial verify
#: stay top tier"). Hard-coded here so that editing models.json alone can never move it.
PINNED_TOP = frozenset({"verify"})
#: Bytes. "over 30 KB" in the spec; usage_audit flags unranged Reads over 30 k characters, the same order.
READ_LIMIT = 30_000
MAX_RETURN_WORDS = 200
MIN_PLANTS = 3
#: The standing DO-NOT-READ entries every template must carry.
STANDING_DO_NOT_READ = ("ai_player/evidence/", "**/INDEX.md", "PROJECT KNOWLEDGE/07-CHANGELOG.md",
                        "PROJECT KNOWLEDGE/08-MISTAKES.md", "ai_player/README.md")

MARKER_RE = re.compile(r"^<!-- stage-template:(?P<role>[a-z][a-z0-9-]*)@(?P<ver>[1-9][0-9]*) -->$")
HEADING_RE = re.compile(r"^## (?P<name>[A-Z][A-Z-]*)\s*$")
PLACEHOLDER_RE = re.compile(r"\{\{\s*(?P<name>[a-z_][a-z0-9_]*)(?P<opt>\?)?\s*\}\}")
ANY_BRACES_RE = re.compile(r"\{\{.*?\}\}")
BULLET_RE = re.compile(r"^[-*] `(?P<entry>[^`]+)`(?P<rest>.*)$")
RANGE_RE = re.compile(r"^(?P<path>.+?):(?P<start>[0-9]+)-(?P<end>[0-9]+)$")
ANCHOR_RE = re.compile(r"^(?P<path>.+?):@(?P<anchor>.+)\+(?P<count>[1-9][0-9]{0,3})$")
WORDS_RE = re.compile(r"^words:\s*(?P<n>\S+)\s*$", re.M)
FILE_RE = re.compile(r"^file:\s*(?P<path>\S.*?)\s*$", re.M)
MODEL_RE = re.compile(r"^(?P<tier>[a-z]+)(?:[ \t]+\([^()\n]*\))?$")
FENCE_RE = re.compile(r"^(?P<run>`{3,}|~{3,})(?P<info>.*)$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def blank_hidden(text: str) -> tuple[list[str], str | None]:
    """The lines of `text` with what a reader of FIELDS must not see blanked (line count kept): the contents and
    markers of ``` / ~~~ fenced blocks, and every `<!-- ... -->` HTML comment (its characters become spaces, so text
    beside it on the line stays). Returns (lines, problem): problem names a fence or comment that never closes,
    which the lint reports instead of silently blanking the rest of the file (lint_docs' "fail toward catching")."""
    out: list[str] = []
    fence: tuple[str, int] | None = None   # (fence character, run length) while inside a fence
    in_comment = False
    for line in text.split("\n"):
        stripped = line.strip()
        if fence is not None:
            closing = FENCE_RE.match(stripped)
            if closing and closing["run"][0] == fence[0] and len(closing["run"]) >= fence[1] and not closing["info"].strip():
                fence = None
            out.append("")
            continue
        if not in_comment:
            opening = FENCE_RE.match(stripped)
            if opening and not (opening["run"][0] == "`" and "`" in opening["info"]):
                fence = (opening["run"][0], len(opening["run"]))
                out.append("")
                continue
        chars, i = list(line), 0
        while i < len(line):
            if in_comment:
                end = line.find("-->", i)
                stop = len(line) if end < 0 else end + 3
                chars[i:stop] = " " * (stop - i)
                in_comment, i = end < 0, stop
            else:
                start = line.find("<!--", i)
                if start < 0:
                    break
                in_comment, i = True, start
        out.append("".join(chars))
    problem = ("a code fence never closes" if fence is not None else
               "an HTML comment never closes" if in_comment else None)
    return out, problem


def parse(text: str) -> dict:
    """Split a template (or a rendered prompt) into its marker and fields. Returns {"marker": (role, ver) | None,
    "fields": {NAME: [bodies...]}, "unclosed": problem | None, "extra_markers": [line numbers]}. Bodies are taken from
    the ORIGINAL text, so a fenced example inside a field body is kept as written."""
    raw = text.replace("\r\n", "\n").split("\n")
    blanked, problem = blank_hidden("\n".join(raw))
    first = raw[0].strip() if raw else ""
    m = MARKER_RE.match(first)
    marker = (m["role"], int(m["ver"])) if m else None
    fields: dict[str, list[str]] = {}
    heads = [(i, HEADING_RE.match(b)) for i, b in enumerate(blanked)]
    heads = [(i, h["name"]) for i, h in heads if h]
    for k, (i, name) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(raw)
        fields.setdefault(name, []).append("\n".join(raw[i + 1:end]).strip("\n"))
    extra = [i + 1 for i, line in enumerate(raw) if i and MARKER_RE.match(line.strip())]
    return {"marker": marker, "fields": fields, "unclosed": problem, "extra_markers": extra}


def norm_path(path: str, repo: Path = REPO) -> str:
    """A path as the DO-NOT-READ match sees it: forward slashes, the repo's absolute prefix dropped, `.`/`..` folded
    (`./x`, `gates/../x`), lower case (Windows paths). A trailing '/' is kept: it marks a folder rule."""
    p = path.replace("\\", "/").strip()
    root = str(repo).replace("\\", "/").rstrip("/") + "/"
    if p.lower().startswith(root.lower()):
        p = p[len(root):]
    folder = p.endswith("/")
    p = posixpath.normpath(p) if p else p
    if p in (".", ""):
        p = ""
    return (p + "/" if folder and p else p).lower()


def repo_relative(path: str, repo: Path = REPO) -> str | None:
    """A READ-LIST path as the repo-relative path of the file it NAMES: resolved against the repo root (`..`, links,
    a `../<repo folder>/` detour and case all folded by the OS), or None when it lands outside the repo. WHY (round
    2): `norm_path` folds `x/../` lexically but never sees that `../Pokebot_Gen3_Enhancement/ai_player/evidence/f`
    is the evidence folder again, so that spelling slipped past every DO-NOT-READ rule."""
    p = Path(path.replace("\\", "/").strip())
    try:
        target = (p if p.is_absolute() else repo / p).resolve()
        return target.relative_to(Path(repo).resolve()).as_posix()
    except (OSError, ValueError, RuntimeError):
        return None


def _under(path: str, rule: str, repo: Path = REPO) -> bool:
    """Is READ-LIST `path` covered by DO-NOT-READ `rule` (a folder ending in '/', a glob, or one file)? Both are
    normalised (`norm_path`); `*` crosses folders (fnmatch), and a leading `**/` also matches at the repo root."""
    rel, r = norm_path(path, repo), norm_path(rule, repo)
    pats = [r + "*"] if r.endswith("/") else [r]
    pats += [p[3:] for p in pats if p.startswith("**/")]
    return any(fnmatch.fnmatchcase(rel, p) for p in pats)


def parse_entry(entry: str) -> dict:
    """A READ-LIST entry -> {"path", "kind": whole|range|anchor|bad}, plus start/end or anchor/count."""
    e = entry.strip()
    a = ANCHOR_RE.match(e)
    if a:
        return {"path": a["path"].strip(), "kind": "anchor", "anchor": a["anchor"], "count": int(a["count"])}
    m = RANGE_RE.match(e)
    if m:
        start, end = int(m["start"]), int(m["end"])
        kind = "range" if start >= 1 and end >= start else "bad"
        return {"path": m["path"].strip(), "kind": kind, "start": start, "end": end}
    return {"path": e, "kind": "whole"}


def file_lines(path: Path) -> list[bytes]:
    """A file's lines as `grep -n` and the Read tool number them (split on LF), each with its LF."""
    data = path.read_bytes()
    parts = data.split(b"\n")
    lines = [p + b"\n" for p in parts[:-1]]
    return lines + ([parts[-1]] if parts[-1] else [])


def resolve_range(spec: dict, path: Path) -> tuple[int, int] | str:
    """(START, END) of a range or anchored entry in `path` (1-based, inclusive, END clipped to the file), or why not."""
    lines = file_lines(path)
    if spec["kind"] == "anchor":
        hits = [i for i, b in enumerate(lines) if b.decode("utf-8", "replace").rstrip("\r\n").startswith(spec["anchor"])]
        if not hits:
            return f"no line starts with {spec['anchor']!r}"
        start = hits[0] + 1
        end = start + spec["count"] - 1
    else:
        start, end = spec["start"], spec["end"]
    if start > len(lines):
        return f"starts at line {start}, past the end ({len(lines)} lines)"
    return start, min(end, len(lines))


def range_bytes(path: Path, start: int, end: int) -> int:
    return sum(len(b) for b in file_lines(path)[start - 1:end])


def bullet_entries(body: str) -> tuple[list[tuple[str, str]], list[str]]:
    """The (entry, rest-of-line) bullets of a list field, and the lines that are neither a bullet, an indented
    continuation of the bullet above, nor a lone placeholder (each one is a lint finding)."""
    entries, bad = [], []
    blanked, _ = blank_hidden(body)
    seen_bullet = False
    for line in blanked:
        s = line.strip()
        if not s:
            continue
        b = BULLET_RE.match(s)
        if b:
            entries.append((b["entry"], b["rest"]))
            seen_bullet = True
        elif PLACEHOLDER_RE.fullmatch(s):
            continue
        elif seen_bullet and line[:1] in (" ", "\t"):
            continue  # the indented continuation of the bullet above: description, not a path
        else:
            bad.append(s)
    return entries, bad


def read_list_errors(body: str, do_not_read: list[str], repo: Path = REPO) -> list[str]:
    """READ-LIST size and contradiction rules (shared by the lint and `render.py`). Bytes are read from disk."""
    errors = []
    entries, bad = bullet_entries(body)
    errors += [f"READ-LIST line is not a `path` bullet: {s[:80]!r}" for s in bad]
    for entry, rest in entries:
        if ANY_BRACES_RE.search(entry):
            continue  # a placeholder path: checked again after render.py fills it
        spec = parse_entry(entry)
        path = spec["path"]
        if spec["kind"] == "bad":
            errors.append(f"READ-LIST `{entry}` is not a range (START >= 1 and END >= START)")
            continue
        rel = repo_relative(path, repo)
        if rel is None and not Path(path.replace("\\", "/").strip()).is_absolute():
            # a RELATIVE path that climbs out of the repo: no template has a reason to, and the only use found was
            # a detour back in that hid a DO-NOT-READ path. An ABSOLUTE path outside the repo is a scratch file
            # (a builder report, a sweep summary) and stays allowed; the size rules below still apply to it.
            errors.append(f"READ-LIST `{path}` leaves the repository: name the file from the repo root")
            continue
        if spec["kind"] == "whole" and rel is not None:
            for rule in do_not_read:
                if _under(rel, rule, repo):
                    errors.append(f"READ-LIST `{path}` is under DO-NOT-READ `{rule}` and has no range")
        target = Path(path) if Path(path).is_absolute() else repo / path
        if target.is_dir():
            errors.append(f"READ-LIST `{path}` is a folder: name the files (with ranges when large)")
            continue
        if not target.is_file():
            if "[later]" not in rest:
                errors.append(f"READ-LIST `{path}` does not exist: fix the path, or tag it [later] if an earlier stage "
                              f"writes it")
            continue
        if spec["kind"] == "whole":
            size = target.stat().st_size
            if size > READ_LIMIT:
                errors.append(f"READ-LIST `{path}` is {size:,} bytes (over {READ_LIMIT:,}) and has no :START-END range")
            continue
        span = resolve_range(spec, target)
        if isinstance(span, str):
            errors.append(f"READ-LIST `{entry}`: {span}")
            continue
        size = range_bytes(target, *span)
        if size > READ_LIMIT:
            errors.append(f"READ-LIST `{entry}` reads lines {span[0]}-{span[1]}, {size:,} bytes (over {READ_LIMIT:,}): "
                          f"narrow the range")
    return errors


def return_cap_errors(body: str) -> list[str]:
    blanked = "\n".join(blank_hidden(body)[0])
    errors = []
    words = WORDS_RE.findall(blanked)
    if len(words) != 1:
        errors.append(f"RETURN-CAP needs exactly one `words: N` line (found {len(words)})")
    else:
        try:
            n = int(words[0])
        except ValueError:
            n = -1
        if not 1 <= n <= MAX_RETURN_WORDS:
            errors.append(f"RETURN-CAP words {words[0]!r} is not an integer in 1..{MAX_RETURN_WORDS}")
    if len(FILE_RE.findall(blanked)) != 1:
        errors.append("RETURN-CAP needs exactly one `file: <path>` line (the report the answer points to)")
    return errors


def model_tier(body: str) -> str | None:
    """The tier a MODEL body names: exactly ONE non-blank line, `top|mid|cheap`, optionally followed by a
    parenthesised note ("top (pinned)"). None for anything else (two lines, two words): an agent would read the
    second line too, and the lint must see what the agent sees."""
    lines = [s.strip() for s in blank_hidden(body)[0] if s.strip()]
    if len(lines) != 1:
        return None
    m = MODEL_RE.fullmatch(lines[0])
    return m["tier"] if m else None


def template_digest(text: str) -> str:
    """The sha256 a plant-run proof records for a template: its text with LF line ends and the MODEL field's body
    left out (its lines dropped, blank ones too). WHY the MODEL body is left out: the move the proof EARNS is exactly
    the edit of that line (top -> mid), so hashing it would make every proof stale the moment it is used. Every other
    byte counts."""
    raw = text.replace("\r\n", "\n").split("\n")
    blanked, _ = blank_hidden("\n".join(raw))
    out, in_model = [], False
    for line, seen in zip(raw, blanked):
        head = HEADING_RE.match(seen)
        if head:
            in_model = head["name"] == "MODEL"
            out.append(line)
        elif not in_model:
            out.append(line)
    return hashlib.sha256("\n".join(out).encode("utf-8")).hexdigest()


def _resolve(ref: str, repo: Path) -> Path:
    return Path(ref) if Path(ref).is_absolute() else repo / ref


def _input_errors(item: object, label: str, repo: Path) -> tuple[list[str], str | None, str | None]:
    """(errors, sha256, text) of a plant's or the control's INPUT: a file that exists and hashes (LF line ends) to
    `input_sha256`."""
    if not isinstance(item, dict):
        return [f"{label} is not an object"], None, None
    ref, want = item.get("input"), item.get("input_sha256")
    if not isinstance(ref, str) or not ref.strip():
        return [f"{label} names no input file"], None, None
    if not isinstance(want, str) or not SHA256_RE.match(want):
        return [f"{label} has no input_sha256 (64 lowercase hex)"], None, None
    path = _resolve(ref, repo)
    if not path.is_file():
        return [f"{label} input {ref!r} does not exist"], None, None
    data = path.read_bytes()
    # LF line ends before hashing: this project is checked out on several computers, and a CRLF checkout of the same
    # committed file must not retire a proof
    got = hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
    if got != want:
        return [f"{label} input {ref!r} hashes to {got[:12]}, not the recorded {want[:12]}"], None, None
    return [], got, data.decode("utf-8", "replace")


def proof_errors(proof: object, role: str, tier: str, version: int, text: str, repo: Path = REPO) -> list[str]:
    """P10: does a PLANT RUN's JSON earn `role` the tier `tier` for THIS template text (`text`, version `version`)?
    The shape:
    {"stage", "tier", "template": "<role>@<ver>", "template_sha256": template_digest(text),
     "run": {"id": "...", "transcript": "<existing path>"},
     "plants": [{"id", "kind", "input": "<file>", "input_sha256"}, ...],
     "findings": [{"plant_id", "quote": "<text found in that plant's input>"}, ...],
     "control": {"input": "<another file>", "input_sha256", "findings": []}}."""
    if not isinstance(proof, dict):
        return ["proof is not a JSON object"]
    errors = []
    if proof.get("stage") != role:
        errors.append(f"proof is for stage {proof.get('stage')!r}, not {role!r}")
    if proof.get("tier") != tier:
        errors.append(f"proof earned tier {proof.get('tier')!r}, not {tier!r}")
    if proof.get("template") != f"{role}@{version}":
        errors.append(f"proof is for template {proof.get('template')!r}, not {role}@{version} (a changed template "
                      f"needs a new plant run)")
    if proof.get("template_sha256") != template_digest(text):
        errors.append(f"proof was made on other template text (template_sha256 {str(proof.get('template_sha256'))[:12]!r}"
                      f" is not this template's {template_digest(text)[:12]}): an edited template needs a new plant run")
    run = proof.get("run")
    if not isinstance(run, dict) or not isinstance(run.get("id"), str) or not run.get("id", "").strip():
        errors.append("proof names no plant run (`run.id`)")
    elif not isinstance(run.get("transcript"), str) or not _resolve(run["transcript"], repo).is_file():
        errors.append(f"proof's run transcript {run.get('transcript')!r} does not exist")
    plants = proof.get("plants")
    if not isinstance(plants, list):
        return errors + ["proof has no plants list"]
    ids = [p.get("id") for p in plants if isinstance(p, dict)]
    kinds = {p.get("kind") for p in plants if isinstance(p, dict) and isinstance(p.get("kind"), str) and p.get("kind")}
    if len(plants) < MIN_PLANTS or len(ids) != len(plants):
        errors.append(f"proof has {len(plants)} plants; at least {MIN_PLANTS} objects are needed")
    if any(not isinstance(i, str) or not i for i in ids) or len(set(map(str, ids))) != len(ids):
        errors.append("every plant needs a unique non-empty string id")
    if len(kinds) < MIN_PLANTS:
        errors.append(f"proof plants cover {len(kinds)} kinds; at least {MIN_PLANTS} different kinds are needed")
    inputs: dict[str, tuple[str, str]] = {}
    for plant in plants:
        pid = plant.get("id") if isinstance(plant, dict) else None
        errs, digest, body = _input_errors(plant, f"plant {pid!r}", repo)
        errors += errs
        if digest is not None and isinstance(pid, str):
            inputs[pid] = (digest, body)
    findings = proof.get("findings")
    if not isinstance(findings, list):
        errors.append("proof has no findings list")
        findings = []
    caught = set()
    for f in findings:
        if not isinstance(f, dict) or f.get("plant_id") not in inputs:
            continue
        quote = f.get("quote")
        if isinstance(quote, str) and quote.strip() and quote.strip() in inputs[f["plant_id"]][1]:
            caught.add(f["plant_id"])
    missed = [i for i in ids if isinstance(i, str) and i not in caught]
    if missed:
        errors.append(f"planted defects NOT caught by the cheaper agent (no finding QUOTING text of that plant's input): "
                      f"{missed}")
    control = proof.get("control")
    errs, control_digest, _ = _input_errors(control, "the CLEAN control", repo)
    if errs:
        errors += errs if isinstance(control, dict) else ["proof has no CLEAN control input"]
    elif control_digest in {d for d, _ in inputs.values()}:
        errors.append("the CLEAN control's input is one of the planted inputs: it is not clean")
    elif control.get("findings") != []:
        errors.append(f"the clean control drew findings (must be zero): {control.get('findings')!r}")
    return errors


def committed_errors(path: Path, repo: Path) -> list[str]:
    """[] when `path` is a file COMMITTED in `repo` (tracked, and no change against HEAD); else why not. A proof only
    on one disk, or edited after its commit, is not a record anyone else can check."""
    try:
        rel = path.resolve().relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        return [f"proof {path} is outside the repository"]

    def git(*args: str) -> int:
        return subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=str(repo), capture_output=True,
                              timeout=60).returncode
    if git("ls-files", "--error-unmatch", "--", rel) != 0:
        return [f"proof {rel} is not tracked by git: commit it"]
    if git("cat-file", "-e", f"HEAD:{rel}") != 0 or git("diff", "--quiet", "HEAD", "--", rel) != 0:
        return [f"proof {rel} differs from its committed version"]
    return []


def lint_text(text: str, role: str, models: dict, repo: Path = REPO) -> list[str]:
    """Every finding for one template's text (empty list = clean)."""
    errors = []
    doc = parse(text)
    if doc["unclosed"]:
        errors.append(doc["unclosed"])
    if doc["marker"] is None:
        errors.append("MARKER: line 1 must be `<!-- stage-template:<role>@<ver> -->`")
    elif doc["marker"][0] != role:
        errors.append(f"MARKER names role {doc['marker'][0]!r} in the file for {role!r}")
    for line in doc["extra_markers"]:
        errors.append(f"MARKER: line {line} is a second marker (only line 1 may be one)")
    fields = doc["fields"]
    for name in FIELDS:
        bodies = fields.get(name, [])
        if not bodies:
            errors.append(f"{name}: required field missing")
        elif len(bodies) > 1:
            errors.append(f"{name}: field appears {len(bodies)} times")
        elif not bodies[0].strip():
            errors.append(f"{name}: required field is empty")
    dnr_body = (fields.get("DO-NOT-READ") or [""])[0]
    dnr_entries, dnr_bad = bullet_entries(dnr_body)
    errors += [f"DO-NOT-READ line is not a `path` bullet: {s[:80]!r}" for s in dnr_bad]
    dnr_paths = [e.replace("\\", "/").strip() for e, _ in dnr_entries]
    if fields.get("DO-NOT-READ"):
        for standing in STANDING_DO_NOT_READ:
            if standing not in dnr_paths:
                errors.append(f"DO-NOT-READ lacks the standing entry `{standing}`")
    if fields.get("READ-LIST"):
        errors += read_list_errors(fields["READ-LIST"][0], dnr_paths, repo)
    if fields.get("RETURN-CAP"):
        errors += return_cap_errors(fields["RETURN-CAP"][0])
    if fields.get("MODEL"):
        tier = model_tier(fields["MODEL"][0])
        stage = (models.get("stages") or {}).get(role)
        if tier not in TIERS:
            shown = " / ".join(s.strip() for s in fields["MODEL"][0].split("\n") if s.strip())[:60]
            errors.append(f"MODEL {shown!r} is not one of {'|'.join(TIERS)} on exactly one line (a `(note)` may follow)")
        elif not isinstance(stage, dict):
            errors.append(f"MODEL: models.json has no stage {role!r}")
        elif stage.get("tier") != tier:
            errors.append(f"MODEL {tier!r} disagrees with models.json {stage.get('tier')!r}")
        else:
            errors += tier_errors(role, tier, stage, doc["marker"][1] if doc["marker"] else 0, repo, text)
    return errors


def tier_errors(role: str, tier: str, stage: dict, version: int, repo: Path = REPO, text: str = "") -> list[str]:
    if tier == "top":
        return []
    if role in PINNED_TOP:
        return [f"MODEL: {role!r} is pinned to top by rule (the adversarial verify never moves down)"]
    ref = stage.get("proof")
    if not ref:
        return [f"MODEL {tier!r} below top names no plant-run proof"]
    path = _resolve(ref, repo)
    try:
        proof = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"MODEL proof {ref!r} unreadable: {type(error).__name__}"]
    errors = committed_errors(path, repo)
    return [f"MODEL proof {ref}: {e}" for e in errors + proof_errors(proof, role, tier, version, text, repo)]


def models_errors(models: dict) -> list[str]:
    """models.json's `agent_model`: the workflow `agent()` model option per tier. `top` must be null (no option: the
    agent runs on the coordinator's own, top, model), so a pinned stage, which `tier_errors` holds at `top`, can only
    ever map to null; `mid` and `cheap` must name a model. WHY: `render.py --format json` hands this value straight
    to the workflow script, and `agent_model.top = "haiku"` once rendered `verify` on haiku while its prompt said top."""
    agent_model = models.get("agent_model")
    if not isinstance(agent_model, dict):
        return ["models.json: `agent_model` is not an object"]
    errors = []
    if "top" not in agent_model or agent_model["top"] is not None:
        errors.append(f"models.json: agent_model.top must be null (the coordinator's own model), not "
                      f"{agent_model.get('top')!r}")
    for tier in ("mid", "cheap"):
        if not isinstance(agent_model.get(tier), str) or not agent_model[tier].strip():
            errors.append(f"models.json: agent_model.{tier} must name a model")
    return errors


def load_models(path: Path = MODELS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def lint_all(templates: Path = TEMPLATES, models_path: Path = MODELS, repo: Path = REPO) -> list[str]:
    """Every finding over the template folder and models.json."""
    try:
        models = load_models(models_path)
    except (OSError, ValueError) as error:
        return [f"models.json unreadable: {type(error).__name__}: {error}"]
    errors = list(models_errors(models))
    roles = sorted(p.stem for p in templates.glob("*.md"))
    if not roles:
        errors.append(f"no templates under {templates}")
    stages = models.get("stages") if isinstance(models.get("stages"), dict) else {}
    for role in sorted(set(stages) - set(roles)):
        errors.append(f"models.json stage {role!r} has no template")
    # (a pinned stage moved off top is caught per template: its MODEL disagrees, or `tier_errors` refuses the move)
    for role in roles:
        text = (templates / f"{role}.md").read_text(encoding="utf-8")
        errors += [f"{role}.md: {e}" for e in lint_text(text, role, models, repo)]
    return errors


def main(argv: list[str] | None = None) -> int:
    errors = lint_all()
    for e in errors:
        print(f"FAIL {e}")
    roles = sorted(p.stem for p in TEMPLATES.glob("*.md"))
    print(f"{'CLEAN' if not errors else 'FINDINGS'}: {len(roles)} templates ({', '.join(roles)}), {len(errors)} findings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
