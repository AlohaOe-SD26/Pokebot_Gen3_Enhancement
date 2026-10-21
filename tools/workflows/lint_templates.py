"""Lint the workflow STAGE TEMPLATES (backlog P11 + P1 + P10, spec S2-3) and hold the ONE parser of their fields.

    py -3.12 tools/workflows/lint_templates.py            lint every template + models.json; exit 0 clean, 1 findings

WHY THIS EXISTS. Until 2026-10-21 no workflow prompt lived in the repo: every workflow script was typed fresh, so the
rules that made a prompt cheap and safe (what to read, with RANGES; what never to read whole; when to stop; how long
the answer may be; which model tier) were re-remembered or forgotten per script. The measured cost: 33 agents opened
with one 1.18 MB design note, agents past 200 calls (3 %) held 53 % of context weight, and Opus-class agents were about
90 % of input-equivalent (backlog P11). A template only helps while its fields are really there, so this lint checks
them mechanically; prose rules about prompts have failed here before (CLAUDE.md session discipline rule 6).

WHAT A TEMPLATE IS. `templates/<role>.md`. Line 1 is the marker `<!-- stage-template:<role>@<ver> -->`, exactly the
string `tools/usage_audit.py` looks for in an agent's first prompt to count UNTEMPLATED agents (so compliance is
MEASURED, never assumed). A FIELD is a `## NAME` heading at column 0 OUTSIDE a code fence; its body runs to the next
`## ` heading. A word in prose ("the MODEL field") or a heading inside a fence is a MENTION and neither satisfies nor
breaks a field (the mention rule of `lint_docs._blank_fenced`; that file runs its lint at import, so the fence logic
is re-implemented here rather than imported). Required fields: GOAL, READ-LIST, DO-NOT-READ, STOP, RETURN-CAP, MODEL,
WAIT-RULE, MAP-FIRST, LOOKUP-FIRST. Placeholders are `{{name}}` (a value is required) or `{{name?}}` (may be empty);
`render.py` fills them.

THE CHECKS (each one has a FAULT and a CONTROL arm in tools/story-dev/selftest_workflows.py):
  * the marker is line 1 and names this file's role; every required field is present exactly once and non-empty (T-1);
  * READ-LIST: every line is a bullet with a `backticked path`, optionally `path:START-END`, or a lone optional
    placeholder line. A path that is a file over READ_LIMIT bytes must carry a range, the size READ FROM DISK (T-2).
    WHY: the 1.18 MB note above, and 337 unranged Reads over 30 k characters held 22 % of Read characters (P2).
    A missing file must carry a range or the `[later]` tag (a file an earlier stage writes). An entry under a
    DO-NOT-READ path must carry a range: a slice may be read, the whole never. A path still holding a placeholder is
    checked when `render.py` fills it (same function), not here;
  * DO-NOT-READ holds the STANDING entries (`ai_player/evidence/`, `**/INDEX.md`, whole `07`/`08`, whole
    `ai_player/README.md`): the files whose whole-read made the heaviest contexts;
  * RETURN-CAP has `words: N` (1..200) and `file: <path>`: a stage hands over a short answer and a file, so the
    coordinator's context does not grow by every stage's full report;
  * MODEL is `top|mid|cheap` and equals `models.json`. A stage below `top` must name a `proof`: the JSON a PLANT RUN
    wrote, with at least 3 planted defects of 3 different kinds, each id among the cheaper agent's findings, and one
    CLEAN control input with ZERO findings, for this stage, this tier and this template version (T-3). WHY the JSON and
    not a marker: the source spec accepted any file containing `PLANT-CAUGHT`, which anyone can type (critic,
    2026-10-19). One caught plant is N = 1, and agreement is not a confidence signal. `verify` (the adversarial
    verify) is pinned to `top` in CODE, so no JSON edit can move it.
"""
from __future__ import annotations

import fnmatch
import json
import re
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
#: (path, needs_whole_marker): the standing DO-NOT-READ entries every template must carry.
STANDING_DO_NOT_READ = ("ai_player/evidence/", "**/INDEX.md", "PROJECT KNOWLEDGE/07-CHANGELOG.md",
                        "PROJECT KNOWLEDGE/08-MISTAKES.md", "ai_player/README.md")

MARKER_RE = re.compile(r"^<!-- stage-template:(?P<role>[a-z][a-z0-9-]*)@(?P<ver>[1-9][0-9]*) -->$")
HEADING_RE = re.compile(r"^## (?P<name>[A-Z][A-Z-]*)\s*$")
PLACEHOLDER_RE = re.compile(r"\{\{\s*(?P<name>[a-z_][a-z0-9_]*)(?P<opt>\?)?\s*\}\}")
ANY_BRACES_RE = re.compile(r"\{\{.*?\}\}")
BULLET_RE = re.compile(r"^- `(?P<entry>[^`]+)`(?P<rest>.*)$")
RANGE_RE = re.compile(r"^(?P<path>.+?):(?P<start>[0-9]+)-(?P<end>[0-9]+)$")
WORDS_RE = re.compile(r"^words:\s*(?P<n>\S+)\s*$", re.M)
FILE_RE = re.compile(r"^file:\s*(?P<path>\S.*?)\s*$", re.M)


def blank_fences(text: str) -> tuple[list[str], bool]:
    """The lines of `text` with the CONTENTS and markers of ``` / ~~~ fenced blocks blanked (line count kept), and
    whether every fence closed. A fence closes only with its own marker. An unclosed fence is reported by the lint
    instead of silently blanking the rest of the file (lint_docs' "fail toward catching")."""
    out, marker = [], None
    for line in text.split("\n"):
        stripped = line.lstrip()
        hit = next((f for f in ("```", "~~~") if stripped.startswith(f)), None)
        if hit and (marker is None or hit == marker):
            marker = hit if marker is None else None
            out.append("")
            continue
        out.append("" if marker else line)
    return out, marker is None


def parse(text: str) -> dict:
    """Split a template (or a rendered prompt) into its marker and fields. Returns
    {"marker": (role, ver) | None, "fields": {NAME: [bodies...]}, "unclosed_fence": bool}. Bodies are taken from the
    ORIGINAL text, so a fenced example inside a field body is kept as written."""
    raw = text.replace("\r\n", "\n").split("\n")
    blanked, closed = blank_fences("\n".join(raw))
    first = raw[0].strip() if raw else ""
    m = MARKER_RE.match(first)
    marker = (m["role"], int(m["ver"])) if m else None
    fields: dict[str, list[str]] = {}
    heads = [(i, HEADING_RE.match(b)) for i, b in enumerate(blanked)]
    heads = [(i, h["name"]) for i, h in heads if h]
    for k, (i, name) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(raw)
        fields.setdefault(name, []).append("\n".join(raw[i + 1:end]).strip("\n"))
    return {"marker": marker, "fields": fields, "unclosed_fence": not closed}


def _entry_parts(entry: str) -> tuple[str, bool]:
    """(path, ranged) of a READ-LIST / DO-NOT-READ entry `path` or `path:START-END`."""
    m = RANGE_RE.match(entry.strip())
    if m and int(m["start"]) >= 1 and int(m["end"]) >= int(m["start"]):
        return m["path"].strip(), True
    return entry.strip(), False


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip()


def _under(path: str, rule: str) -> bool:
    """Is READ-LIST `path` covered by DO-NOT-READ `rule` (a folder ending in '/', a glob, or one file)? Case-insensitive
    (Windows paths); `*` crosses folders (fnmatch), and a leading `**/` also matches at the repo root."""
    rel, r = _norm(path).lower(), _norm(rule).lower()
    root = _norm(str(REPO)).lower() + "/"
    if rel.startswith(root):
        rel = rel[len(root):]
    pats = [r + "*"] if r.endswith("/") else [r]
    pats += [p[3:] for p in pats if p.startswith("**/")]
    return any(fnmatch.fnmatchcase(rel, p) for p in pats)


def bullet_entries(body: str) -> tuple[list[tuple[str, str]], list[str]]:
    """The (entry, rest-of-line) bullets of a list field, and the lines that are neither a bullet nor a lone
    placeholder (each one is a lint finding)."""
    entries, bad = [], []
    blanked, _ = blank_fences(body)
    for line in blanked:
        s = line.strip()
        if not s:
            continue
        b = BULLET_RE.match(s)
        if b:
            entries.append((b["entry"], b["rest"]))
        elif PLACEHOLDER_RE.fullmatch(s):
            continue
        else:
            bad.append(s)
    return entries, bad


def read_list_errors(body: str, do_not_read: list[str], repo: Path = REPO) -> list[str]:
    """READ-LIST size and contradiction rules (shared by the lint and `render.py`). Sizes are read from disk."""
    errors = []
    entries, bad = bullet_entries(body)
    errors += [f"READ-LIST line is not a `path` bullet: {s[:80]!r}" for s in bad]
    for entry, rest in entries:
        if ANY_BRACES_RE.search(entry):
            continue  # a placeholder path: checked again after render.py fills it
        path, ranged = _entry_parts(entry)
        if ranged:
            continue
        for rule in do_not_read:
            if _under(path, rule):
                errors.append(f"READ-LIST `{path}` is under DO-NOT-READ `{rule}` and has no range")
        target = Path(path) if Path(path).is_absolute() else repo / path
        if target.is_file():
            size = target.stat().st_size
            if size > READ_LIMIT:
                errors.append(f"READ-LIST `{path}` is {size:,} bytes (over {READ_LIMIT:,}) and has no :START-END range")
        elif target.is_dir():
            errors.append(f"READ-LIST `{path}` is a folder: name the files (with ranges when large)")
        elif "[later]" not in rest:
            errors.append(f"READ-LIST `{path}` does not exist: give a range, or tag it [later] if an earlier stage writes it")
    return errors


def return_cap_errors(body: str) -> list[str]:
    blanked = "\n".join(blank_fences(body)[0])
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
    lines = [s.strip() for s in blank_fences(body)[0] if s.strip()]
    return lines[0] if lines else None


def proof_errors(proof: object, role: str, tier: str, version: int) -> list[str]:
    """P10: does a PLANT RUN's JSON earn `role` the tier `tier` for template version `version`? The shape:
    {"stage", "tier", "template": "<role>@<ver>", "plants": [{"id", "kind", ...}], "findings": [{"plant_id", ...}],
     "control": {"input": "...", "findings": []}}."""
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
    plants = proof.get("plants")
    if not isinstance(plants, list):
        return errors + ["proof has no plants list"]
    ids = [p.get("id") for p in plants if isinstance(p, dict)]
    kinds = {p.get("kind") for p in plants if isinstance(p, dict) and isinstance(p.get("kind"), str) and p.get("kind")}
    if len(plants) < MIN_PLANTS or len(ids) != len(plants):
        errors.append(f"proof has {len(plants)} plants; at least {MIN_PLANTS} objects are needed")
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        errors.append("every plant needs a unique non-empty string id")
    if len(kinds) < MIN_PLANTS:
        errors.append(f"proof plants cover {len(kinds)} kinds; at least {MIN_PLANTS} different kinds are needed")
    findings = proof.get("findings")
    found = {f.get("plant_id") for f in findings if isinstance(f, dict)} if isinstance(findings, list) else set()
    if not isinstance(findings, list):
        errors.append("proof has no findings list")
    missed = [i for i in ids if isinstance(i, str) and i not in found]
    if missed:
        errors.append(f"planted defects NOT caught by the cheaper agent: {missed}")
    control = proof.get("control")
    if not isinstance(control, dict) or not isinstance(control.get("input"), str) or not control.get("input"):
        errors.append("proof has no CLEAN control input")
    elif control.get("findings") != []:
        errors.append(f"the clean control drew findings (must be zero): {control.get('findings')!r}")
    return errors


def lint_text(text: str, role: str, models: dict, repo: Path = REPO) -> list[str]:
    """Every finding for one template's text (empty list = clean)."""
    errors = []
    doc = parse(text)
    if doc["unclosed_fence"]:
        errors.append("a code fence never closes")
    if doc["marker"] is None:
        errors.append("MARKER: line 1 must be `<!-- stage-template:<role>@<ver> -->`")
    elif doc["marker"][0] != role:
        errors.append(f"MARKER names role {doc['marker'][0]!r} in the file for {role!r}")
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
    dnr_paths = [_norm(e) for e, _ in dnr_entries]
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
            errors.append(f"MODEL {tier!r} is not one of {'|'.join(TIERS)}")
        elif not isinstance(stage, dict):
            errors.append(f"MODEL: models.json has no stage {role!r}")
        elif stage.get("tier") != tier:
            errors.append(f"MODEL {tier!r} disagrees with models.json {stage.get('tier')!r}")
        else:
            errors += tier_errors(role, tier, stage, doc["marker"][1] if doc["marker"] else 0, repo)
    return errors


def tier_errors(role: str, tier: str, stage: dict, version: int, repo: Path = REPO) -> list[str]:
    if tier == "top":
        return []
    if role in PINNED_TOP:
        return [f"MODEL: {role!r} is pinned to top by rule (the adversarial verify never moves down)"]
    ref = stage.get("proof")
    if not ref:
        return [f"MODEL {tier!r} below top names no plant-run proof"]
    path = Path(ref) if Path(ref).is_absolute() else repo / ref
    try:
        proof = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"MODEL proof {ref!r} unreadable: {type(error).__name__}"]
    return [f"MODEL proof {ref}: {e}" for e in proof_errors(proof, role, tier, version)]


def load_models(path: Path = MODELS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def lint_all(templates: Path = TEMPLATES, models_path: Path = MODELS, repo: Path = REPO) -> list[str]:
    """Every finding over the template folder and models.json."""
    try:
        models = load_models(models_path)
    except (OSError, ValueError) as error:
        return [f"models.json unreadable: {type(error).__name__}: {error}"]
    errors = []
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
