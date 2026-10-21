"""Render a workflow STAGE TEMPLATE into the prompt an agent receives (backlog P11, spec S2-3).

    py -3.12 tools/workflows/render.py build --set task="backlog O5" --set-file goal=goal.txt ... [--format text|json]
    py -3.12 tools/workflows/render.py verify --values values.json --out prompt.txt

WHY. A workflow script is JavaScript and cannot read the repo, so the coordinator renders each stage's prompt HERE and
pastes the result into the script (`--format json` prints a JSON object whose "prompt" value is a valid JS string
literal, plus the stage's tier and the `agent()` model option from models.json). Rendering is where a template's
promises become a real prompt, and where the model is CHOSEN, so it REFUSES rather than guesses:
  * a template the lint does not pass (`lint_templates.lint_text` on this role's text, with `models_errors` over
    models.json): a MODEL line that disagrees with models.json, a tier below top without a valid plant-run proof,
    `verify` moved off top, or `agent_model.top` set to a model would otherwise reach `agent()` unchecked. WHY here
    and not only in the lint: the lint runs at commit time, render at use time, and a models.json edited in between
    once rendered `verify` on haiku while its prompt said `top` (review 2026-10-21);
  * a value that is not a JSON STRING (null, false, a list, a number: `str()` would render "None" or "False" as if it
    were text), a value over MAX_VALUE_CHARS (a document belongs in READ-LIST with a range, not pasted into a prompt),
    a value holding a `## ` heading line (it would inject a field, e.g. a second, permissive `## RULES`), or a value
    holding any line break other than LF / CRLF (a lone CR, VT, FF, U+001C-U+001E, NEL U+0085, U+2028, U+2029:
    `str.splitlines()` and JS readers start a new line there, where the heading check does not look);
  * an unresolved `{{placeholder}}` (a value not given, or a value that itself holds `{{...}}`): an agent handed a
    literal "{{spec_range}}" reads the whole file, which is the cost the template exists to remove;
  * an empty value for a REQUIRED placeholder `{{name}}` (only `{{name?}}` may be empty), and any required field whose
    body is empty after filling;
  * a READ-LIST entry, once filled, that reads over 30 KB (a whole file, or a range's own bytes), does not exist
    (unless tagged [later]), or sits under DO-NOT-READ unranged (`lint_templates.read_list_errors`, the same function
    the lint runs: one rule, one reader). An ANCHORED entry `path:@<line prefix>+N` is resolved here to the concrete
    `path:START-END` the agent reads, found the way `grep -n '^<prefix>'` finds it;
  * a template whose line 1 is not this role's marker `<!-- stage-template:<role>@<ver> -->` (the lint), a filled
    prompt with a second marker line, or a value that opens a fence or comment that never closes, because
    `tools/usage_audit.py` counts an agent as TEMPLATED only by that marker on its first prompt's line 1.
Exit 0 = rendered; 2 = refused (the reasons are printed, nothing is written).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import lint_templates as lt  # noqa: E402  (the one parser of template fields)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

#: Characters. A value is a sentence or a paragraph (a goal, a claim, a path list); the longest real one so far was a
#: few thousand characters. Anything longer is a document, which belongs in READ-LIST with a range.
MAX_VALUE_CHARS = 20_000
#: A heading line a value must not carry: `##` then a space or the line's end, after any indentation.
VALUE_HEADING_RE = re.compile(r"^[ \t]*##(?:[ \t]|$)", re.M)
#: Every character `str.splitlines()` breaks a line at, other than LF (and CR as half of CRLF). A value may carry
#: none of them. WHY (round 2): VALUE_HEADING_RE sees only LF line starts, so `"\u2028## RULES"` or `"\r## RULES"`
#: rendered, and a reader that splits like Python (or a JS string) then saw a second `## RULES`. Refusing the
#: character is simpler than teaching every reader about it. selftest T-5c proves this set equals splitlines' own.
LINE_BREAKS = frozenset("\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")


class RenderError(ValueError):
    """The template cannot become a safe prompt; `.reasons` lists why."""

    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def placeholders(text: str) -> dict[str, bool]:
    """name -> optional, for every `{{name}}` / `{{name?}}` in `text` (a name used both ways counts as required)."""
    found: dict[str, bool] = {}
    for m in lt.PLACEHOLDER_RE.finditer(text):
        found[m["name"]] = found.get(m["name"], True) and bool(m["opt"])
    return found


def value_errors(values: dict) -> list[str]:
    """The values no prompt may carry (see the module docstring)."""
    reasons = []
    for name, value in values.items():
        if not isinstance(value, str):
            reasons.append(f"value {name!r} is a {type(value).__name__}, not a string")
            continue
        if len(value) > MAX_VALUE_CHARS:
            reasons.append(f"value {name!r} is {len(value):,} characters (over {MAX_VALUE_CHARS:,}): put the document "
                           f"in READ-LIST with a range instead")
        breaks = sorted({ch for ch in value.replace("\r\n", "\n") if ch in LINE_BREAKS})
        if breaks:
            shown = ", ".join(ascii(c) for c in breaks)
            reasons.append(f"value {name!r} holds a line break other than LF or CRLF ({shown}): a reader that splits "
                           f"lines there would see a new line, and so a possible heading")
        # format characters (a zero-width space) are invisible to a reader, so they cannot hide a heading
        visible = "".join(ch for ch in value if unicodedata.category(ch) != "Cf")
        if VALUE_HEADING_RE.search(visible):
            reasons.append(f"value {name!r} holds a `## ` heading line: it would inject a field into the prompt")
    return reasons


def resolve_anchors(text: str, repo: Path) -> str:
    """Every bullet `path:@<prefix>+N` -> `path:START-END`, the lines the agent will read. An anchor that resolves to
    nothing is left as written: `read_list_errors` (the one reader of the rule) then refuses it."""
    out = []
    for line in text.split("\n"):
        bullet = lt.BULLET_RE.match(line.strip())
        spec = lt.parse_entry(bullet["entry"]) if bullet else None
        target = lt._resolve(spec["path"], repo) if spec and spec["kind"] == "anchor" else None
        span = lt.resolve_range(spec, target) if target is not None and target.is_file() else None
        if isinstance(span, tuple):
            line = line.replace(f"`{bullet['entry']}`", f"`{spec['path']}:{span[0]}-{span[1]}`", 1)
        out.append(line)
    return "\n".join(out)


def render(text: str, values: dict, role: str, repo: Path = lt.REPO, models: dict | None = None) -> str:
    """Fill `text` (a template of `role`) from `values`; raise RenderError instead of returning an unsafe prompt.
    `models` is models.json's content (default: this folder's models.json)."""
    models = lt.load_models() if models is None else models
    lint = lt.models_errors(models) + lt.lint_text(text, role, models, repo)
    if lint:
        raise RenderError([f"the template does not lint: {e}" for e in lint])
    reasons = value_errors(values)
    wanted = placeholders(text)
    for name, optional in wanted.items():
        if optional:
            continue  # `{{name?}}` may be left out: it renders empty
        if name not in values:
            reasons.append(f"unresolved placeholder {{{{{name}}}}}: no value given")
        elif isinstance(values[name], str) and not values[name].strip():
            reasons.append(f"required placeholder {{{{{name}}}}} has an empty value")
    if reasons:
        raise RenderError(reasons)
    out = lt.PLACEHOLDER_RE.sub(lambda m: values.get(m["name"], ""), text)
    left = lt.ANY_BRACES_RE.findall(out)
    if left:
        raise RenderError([f"unresolved placeholder after filling: {s}" for s in left])
    out = resolve_anchors(out, repo)
    doc = lt.parse(out)
    # (line 1 is this role's marker: the lint above proved it of the template, and a marker line cannot hold a
    # placeholder, so no value can change it. A value CAN add lines below it, which the checks below are for.)
    if doc["unclosed"]:
        reasons.append(f"after filling, {doc['unclosed']}: a value opened it, and the agent would read the rest as code")
    for line in doc["extra_markers"]:
        reasons.append(f"line {line} is a second marker after filling (only line 1 may be one)")
    for name in lt.FIELDS:
        bodies = doc["fields"].get(name, [])
        if len(bodies) != 1:
            reasons.append(f"{name}: required field present {len(bodies)} times after filling")
        elif not bodies[0].strip():
            reasons.append(f"{name}: required field is empty after filling")
    if doc["fields"].get("READ-LIST") and doc["fields"].get("DO-NOT-READ"):
        dnr = [e for e, _ in lt.bullet_entries(doc["fields"]["DO-NOT-READ"][0])[0]]
        reasons += lt.read_list_errors(doc["fields"]["READ-LIST"][0], dnr, repo)
    if reasons:
        raise RenderError(reasons)
    return out


def render_stage(role: str, values: dict, templates: Path = lt.TEMPLATES, models_path: Path = lt.MODELS,
                 repo: Path = lt.REPO) -> dict:
    """{"role", "tier", "model", "prompt"}: the rendered prompt and the `agent()` model option, both from ONE read of
    models.json (the tier the lint just checked is the tier that is handed out)."""
    path = templates / f"{role}.md"
    if not path.is_file():
        raise RenderError([f"no template {path}"])
    try:
        models = lt.load_models(models_path)
    except (OSError, ValueError) as error:
        raise RenderError([f"models.json unreadable: {type(error).__name__}: {error}"]) from error
    prompt = render(path.read_text(encoding="utf-8"), values, role, repo, models)
    tier = models["stages"][role]["tier"]
    # the workflow agent() `model` option; null for top = no option, the agent inherits the coordinator's model
    return {"role": role, "tier": tier, "model": models["agent_model"][tier], "prompt": prompt}


def render_role(role: str, values: dict, templates: Path = lt.TEMPLATES, repo: Path = lt.REPO,
                models_path: Path = lt.MODELS) -> str:
    return render_stage(role, values, templates, models_path, repo)["prompt"]


def _values(args) -> dict:
    values: dict = {}
    if args.values:
        loaded = json.loads(Path(args.values).read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise RenderError([f"--values {args.values} is not a JSON object"])
        values.update({str(k): v for k, v in loaded.items()})  # NOT str(v): render refuses a non-string value
    for item in args.set or []:
        key, sep, val = item.partition("=")
        if not sep:
            raise RenderError([f"--set {item!r} is not key=value"])
        values[key.strip()] = val
    for item in args.set_file or []:
        key, sep, val = item.partition("=")
        if not sep:
            raise RenderError([f"--set-file {item!r} is not key=path"])
        values[key.strip()] = Path(val).read_text(encoding="utf-8").rstrip("\n")
    return values


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role")
    ap.add_argument("--set", action="append", metavar="KEY=VALUE")
    ap.add_argument("--set-file", action="append", metavar="KEY=PATH")
    ap.add_argument("--values", metavar="JSON", help="a JSON object of placeholder values")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--out", help="write here instead of stdout")
    args = ap.parse_args(argv)
    try:
        stage = render_stage(args.role, _values(args))
    except RenderError as error:
        for r in error.reasons:
            print(f"REFUSED {r}", file=sys.stderr)
        return 2
    out = json.dumps(stage, ensure_ascii=False, indent=1) if args.format == "json" else stage["prompt"]
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
