"""Render a workflow STAGE TEMPLATE into the prompt an agent receives (backlog P11, spec S2-3).

    py -3.12 tools/workflows/render.py build --set task="backlog O5" --set-file goal=goal.txt ... [--format text|json]
    py -3.12 tools/workflows/render.py verify --values values.json --out prompt.txt

WHY. A workflow script is JavaScript and cannot read the repo, so the coordinator renders each stage's prompt HERE and
pastes the result into the script (`--format json` prints a JSON object whose "prompt" value is a valid JS string
literal, plus the stage's tier and the `agent()` model option from models.json). Rendering is where a template's
promises become a real prompt, so it REFUSES rather than guesses:
  * an unresolved `{{placeholder}}` (a value not given, or a value that itself holds `{{...}}`): an agent handed a
    literal "{{spec_range}}" reads the whole file, which is the cost the template exists to remove;
  * an empty value for a REQUIRED placeholder `{{name}}` (only `{{name?}}` may be empty), and any required field whose
    body is empty after filling;
  * a READ-LIST path, once filled, that is a file over 30 KB without a range (`lint_templates.read_list_errors`, the
    same function the lint runs: one rule, one reader);
  * a prompt whose line 1 is not this role's marker `<!-- stage-template:<role>@<ver> -->`, because
    `tools/usage_audit.py` counts an agent as TEMPLATED only by that marker in its first prompt.
Exit 0 = rendered; 2 = refused (the reasons are printed, nothing is written).
"""
from __future__ import annotations

import argparse
import json
import sys
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


def render(text: str, values: dict[str, str], role: str, repo: Path = lt.REPO) -> str:
    """Fill `text` (a template of `role`) from `values`; raise RenderError instead of returning an unsafe prompt."""
    reasons = []
    wanted = placeholders(text)
    for name, optional in wanted.items():
        if optional:
            continue  # `{{name?}}` may be left out: it renders empty
        if name not in values:
            reasons.append(f"unresolved placeholder {{{{{name}}}}}: no value given")
        elif not str(values[name]).strip():
            reasons.append(f"required placeholder {{{{{name}}}}} has an empty value")
    if reasons:
        raise RenderError(reasons)
    out = lt.PLACEHOLDER_RE.sub(lambda m: str(values.get(m["name"], "")), text)
    left = lt.ANY_BRACES_RE.findall(out)
    if left:
        raise RenderError([f"unresolved placeholder after filling: {s}" for s in left])
    doc = lt.parse(out)
    if doc["marker"] is None or doc["marker"][0] != role:
        reasons.append(f"line 1 is not the marker of role {role!r} (usage_audit would count this agent untemplated)")
    for name in lt.FIELDS:
        bodies = doc["fields"].get(name, [])
        if len(bodies) != 1:
            reasons.append(f"{name}: required field present {len(bodies)} times after filling")
        elif not bodies[0].strip():
            reasons.append(f"{name}: required field is empty after filling")
    if doc["fields"].get("READ-LIST") and doc["fields"].get("DO-NOT-READ"):
        dnr = [lt._norm(e) for e, _ in lt.bullet_entries(doc["fields"]["DO-NOT-READ"][0])[0]]
        reasons += lt.read_list_errors(doc["fields"]["READ-LIST"][0], dnr, repo)
    if reasons:
        raise RenderError(reasons)
    return out


def render_role(role: str, values: dict[str, str], templates: Path = lt.TEMPLATES, repo: Path = lt.REPO) -> str:
    path = templates / f"{role}.md"
    if not path.is_file():
        raise RenderError([f"no template {path}"])
    return render(path.read_text(encoding="utf-8"), values, role, repo)


def _values(args) -> dict[str, str]:
    values: dict[str, str] = {}
    if args.values:
        loaded = json.loads(Path(args.values).read_text(encoding="utf-8"))
        values.update({str(k): str(v) for k, v in loaded.items()})
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
        prompt = render_role(args.role, _values(args))
    except RenderError as error:
        for r in error.reasons:
            print(f"REFUSED {r}", file=sys.stderr)
        return 2
    if args.format == "json":
        models = lt.load_models()
        tier = ((models.get("stages") or {}).get(args.role) or {}).get("tier")
        # the workflow agent() `model` option; null for top = no option, the agent inherits the coordinator's model
        model = (models.get("agent_model") or {}).get(tier)
        out = json.dumps({"role": args.role, "tier": tier, "model": model, "prompt": prompt},
                         ensure_ascii=False, indent=1)
    else:
        out = prompt
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
