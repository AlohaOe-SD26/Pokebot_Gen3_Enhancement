"""Self-test for the workflow STAGE TEMPLATES and their tools (backlog P11 + P1 + N6 + P10, spec S2-3). Offline, ~5 s.

WHY THIS EXISTS. `tools/workflows/` turns the prompt rules that kept agents cheap and safe into fields a lint can see,
a renderer that refuses an unsafe prompt, a fix-round decision that never reads a missing verdict as a pass, and a
list of the AI-player suites a change made stale. Each of those is a GUARD, and a guard that cannot be shown to fire is
not a guard (CLAUDE.md rule 6), so every check below has a FAULT arm (the rule broken -> it must fail) and a CONTROL.

  T-1 FAULT each of the 9 required fields AND the marker removed in turn from every real template -> the lint fails
      NAMING it (10 cases x 5 templates); the standing DO-NOT-READ entries and a RETURN-CAP over 200 words / without a
      file fail too. CONTROL: the real templates and models.json lint CLEAN.
  T-2 FAULT an unranged READ-LIST entry for a 600 KB file -> fail (in the lint AND in render.py after a placeholder is
      filled); an unranged entry under a DO-NOT-READ folder, a missing file, a folder -> fail. CONTROL: the same file
      ranged, a small file, a missing file tagged [later] -> pass.
  T-3 FAULT `MODEL: mid` with no proof -> fail; a proof missing one planted id, a proof whose control has a finding,
      only 2 plants, 3 plants of 2 kinds, a proof for another template version, a MODEL that disagrees with models.json,
      and `verify` moved to mid even WITH a valid proof -> fail. CONTROL: 3 plants of 3 kinds all found and a clean
      control -> pass.
  T-4 mention control: "DO-NOT-READ" in prose and a fenced `## DO-NOT-READ` block do NOT satisfy the missing field;
      "MODEL: cheap" in prose and a fenced `## MODEL` / `cheap` do NOT break a real `top` template; an unclosed fence
      is a finding (never a silent blank-out).
  T-5 render.py refuses an unresolved placeholder, an empty required value, a value carrying `{{...}}`, a value that
      injects a second field, a field left empty after filling, and a text without this role's marker. CONTROL: full
      values render every real template, line 1 is the marker, no braces remain; an optional placeholder may be left out.
  T-6 stage_helpers.refix_decision: 15 JSON shapes (the spec's six, including the string "false" and a missing file,
      plus the contradictions) map to PASS / REFIX / UNKNOWN as stated; UNKNOWN is never PASS; the CLI exit codes.
  T-7 regression_due on a throw-away git repo: changing a covered file lists its suite (uncommitted AND committed);
      changing only a doc does not (CONTROL); a covered file outside the digest scope is seen; an unknown glob in the
      map is an error (exit 2), not silence; never run / no provenance / an unknown commit are DUE; uncommitted
      evidence is cleared ONLY through a kept tree that recomputes to its digest; the newest evidence wins; read-only.
  T-8 the MARKER, through usage_audit's OWN parser (`usage_audit.scan_file`, imported read-only): an agent whose first
      prompt is a rendered template (bare, and inside the harness's indented "computed task" framing) is TEMPLATED;
      the same prompt without the marker is not (CONTROL). A NOTE (not graded) reports how usage_audit sees an agent
      whose first user message is the harness's USER-REQUEST relay and whose second is the template.

Run: cd tools/story-dev && py -3.12 selftest_workflows.py [--workflows-dir <a copy of tools/workflows>]
(`--workflows-dir` points the test at a scratch copy: that is how call-deleting mutants are run against it.)
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools"
WORKFLOWS = REPO / "tools" / "workflows"
if "--workflows-dir" in sys.argv:
    WORKFLOWS = Path(sys.argv[sys.argv.index("--workflows-dir") + 1]).resolve()
for p in (str(WORKFLOWS), str(TOOLS), str(REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)

lt = importlib.import_module("lint_templates")
render = importlib.import_module("render")
sh = importlib.import_module("stage_helpers")
rd = importlib.import_module("regression_due")
import usage_audit as ua  # noqa: E402  (read-only: its parser is the one that counts templated agents)
from ai_player.gates.provenance import read_tree, snapshot_tree, tree_digest  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []
NOTES: list[str] = []
ROLES = ("build", "doc-check", "recon", "sweep-analysis", "verify")


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def quiet(fn, *args):
    """Call a tool's CLI `main` with its stdout/stderr captured (the test reads exit codes, not the console)."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


def guarded(name: str, fn) -> None:
    """Run one test group; an exception is a FAIL of that group, never a crash of the suite."""
    try:
        fn()
    except Exception as error:  # noqa: BLE001
        check(f"{name} raised", False, f"{type(error).__name__}: {error}")


def template(role: str) -> str:
    return (WORKFLOWS / "templates" / f"{role}.md").read_text(encoding="utf-8")


def models() -> dict:
    return lt.load_models(WORKFLOWS / "models.json")


def without_field(text: str, name: str) -> str:
    """`text` with the `## NAME` heading and its body removed (up to the next `## ` heading)."""
    lines = text.split("\n")
    out, skipping = [], False
    for line in lines:
        if line.startswith("## "):
            skipping = line.strip() == f"## {name}"
            if skipping:
                continue
        if not skipping:
            out.append(line)
    return "\n".join(out)


def replace_field(text: str, name: str, body: str) -> str:
    lines = text.split("\n")
    out, skipping = [], False
    for line in lines:
        if line.startswith("## "):
            if skipping:
                skipping = False
            if line.strip() == f"## {name}":
                out += [line, body]
                skipping = True
                continue
        if not skipping:
            out.append(line)
    return "\n".join(out)


def values_for(role: str, tmp: Path) -> dict[str, str]:
    """A full set of placeholder values for `role` whose READ-LIST paths exist and are small (or are [later])."""
    small = tmp / "spec-small.md"
    small.write_text("# spec\n", encoding="utf-8")
    vals = {name: ("" if optional else f"value-{name}") for name, optional in render.placeholders(template(role)).items()}
    for key in ("spec", "summary", "builder_report"):
        if key in vals:
            vals[key] = str(small)
    if "reads" in vals:
        vals["reads"] = f"- `{small}` the one file"
    return vals


# ------------------------------------------------------------------------------------------------------------- T-1
def t1() -> None:
    m = models()
    for role in ROLES:
        errs = lt.lint_text(template(role), role, m, REPO)
        check(f"T-1 CONTROL {role}.md lints clean", errs == [], str(errs))
    allerrs = lt.lint_all(WORKFLOWS / "templates", WORKFLOWS / "models.json", REPO)
    check("T-1 CONTROL lint_all over the real folder is CLEAN", allerrs == [], str(allerrs))
    for name in lt.FIELDS:
        missed = []
        for role in ROLES:
            errs = lt.lint_text(without_field(template(role), name), role, m, REPO)
            if not any(e.startswith(f"{name}:") and "missing" in e for e in errs):
                missed.append(role)
        check(f"T-1 FAULT field {name} removed -> lint fails naming it (5 templates)", not missed, f"not named in {missed}")
    missed = []
    for role in ROLES:
        text = template(role).split("\n", 1)[1]
        if not any(e.startswith("MARKER") for e in lt.lint_text(text, role, m, REPO)):
            missed.append(role)
    check("T-1 FAULT marker removed -> lint fails naming MARKER (5 templates)", not missed, f"not named in {missed}")
    wrong = template("build").replace("stage-template:build@1", "stage-template:verify@1", 1)
    check("T-1 FAULT a marker naming another role fails",
          any(e.startswith("MARKER") for e in lt.lint_text(wrong, "build", m, REPO)))
    dnr = template("build").replace("- `ai_player/evidence/`", "- `ai_player/other/`", 1)
    errs = lt.lint_text(dnr, "build", m, REPO)
    check("T-1 FAULT DO-NOT-READ without the standing `ai_player/evidence/` entry fails",
          any("standing entry `ai_player/evidence/`" in e for e in errs), str(errs))
    over = template("build").replace("words: 200", "words: 250", 1)
    check("T-1 FAULT RETURN-CAP words 250 fails", any("RETURN-CAP words" in e for e in lt.lint_text(over, "build", m, REPO)))
    nofile = "\n".join(x for x in template("build").split("\n") if not x.startswith("file: "))
    check("T-1 FAULT RETURN-CAP without `file:` fails",
          any("file: <path>" in e for e in lt.lint_text(nofile, "build", m, REPO)))
    dup = template("build") + "\n## STOP\nagain\n"
    check("T-1 FAULT a field present twice fails",
          any(e.startswith("STOP:") and "2 times" in e for e in lt.lint_text(dup, "build", m, REPO)))
    empty = replace_field(template("build"), "STOP", "")
    check("T-1 FAULT an empty field fails",
          any(e.startswith("STOP:") and "empty" in e for e in lt.lint_text(empty, "build", m, REPO)))
    tmp = Path(tempfile.mkdtemp(prefix="swf-t1-"))
    try:
        shutil.copytree(WORKFLOWS / "templates", tmp / "templates")
        extra = json.loads(json.dumps(m))
        extra["stages"]["design"] = {"tier": "top", "proof": None}
        (tmp / "models.json").write_text(json.dumps(extra), encoding="utf-8")
        e = lt.lint_all(tmp / "templates", tmp / "models.json", REPO)
        check("T-1 FAULT a models.json stage with no template is a finding", any("'design' has no template" in x for x in e), str(e))
        del extra["stages"]["design"], extra["stages"]["recon"]
        (tmp / "models.json").write_text(json.dumps(extra), encoding="utf-8")
        e = lt.lint_all(tmp / "templates", tmp / "models.json", REPO)
        check("T-1 FAULT a template with no models.json stage is a finding",
              any(x.startswith("recon.md: MODEL: models.json has no stage") for x in e), str(e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------------------------------------------------- T-2
def _read_list_template(entries: str) -> str:
    return replace_field(template("build"), "READ-LIST", entries)


def t2() -> None:
    m = models()
    tmp = Path(tempfile.mkdtemp(prefix="swf-t2-"))
    try:
        (tmp / "big.md").write_bytes(b"x" * 600_000)
        (tmp / "small.md").write_bytes(b"x" * 1_000)
        (tmp / "ai_player" / "evidence").mkdir(parents=True)
        (tmp / "ai_player" / "evidence" / "e.txt").write_bytes(b"x" * 100)

        def errs(entries: str) -> list[str]:
            return lt.lint_text(_read_list_template(entries), "build", m, tmp)
        e = errs("- `big.md` the whole thing")
        check("T-2 FAULT unranged 600 KB READ-LIST entry fails naming the range rule",
              any("big.md" in x and "range" in x for x in e), str(e))
        check("T-2 CONTROL the same 600 KB file with :1-200 passes", errs("- `big.md:1-200` a slice") == [])
        check("T-2 CONTROL an unranged small file passes", errs("- `small.md`") == [])
        check("T-2 FAULT an unranged entry under DO-NOT-READ `ai_player/evidence/` fails",
              any("DO-NOT-READ" in x for x in errs("- `ai_player/evidence/e.txt`")))
        check("T-2 CONTROL the same evidence file ranged passes", errs("- `ai_player/evidence/e.txt:1-20`") == [])
        check("T-2 FAULT a missing file without [later] fails", any("does not exist" in x for x in errs("- `nope.md`")))
        check("T-2 CONTROL a missing file tagged [later] passes", errs("- `nope.md` written by the build [later]") == [])
        check("T-2 FAULT a folder fails", any("folder" in x for x in errs("- `ai_player/evidence`")))
        check("T-2 FAULT a prose line in READ-LIST fails", any("not a `path` bullet" in x for x in errs("read big.md")))
        e = errs("- `big.md:0-10`")
        check("T-2 FAULT a range starting at 0 is not a range", any("range" in x for x in e), str(e))
        vals = values_for("build", tmp)
        vals["spec"] = str(tmp / "big.md")
        try:
            render.render(template("build"), vals, "build", tmp)
            ok, why = False, "rendered"
        except render.RenderError as error:
            ok, why = any("big.md" in r and "range" in r for r in error.reasons), str(error.reasons)
        check("T-2 FAULT render.py refuses a placeholder filled with an unranged 600 KB path", ok, why)
        vals["spec"] = str(tmp / "big.md") + ":10-60"
        out = render.render(template("build"), vals, "build", tmp)
        check("T-2 CONTROL render.py accepts the same path ranged", "big.md:10-60" in out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------------------------------------------------- T-3
def _proof(role: str = "recon", tier: str = "mid", n: int = 3, kinds: int = 3, found: int | None = None,
           control_findings=None, version: int = 1) -> dict:
    plants = [{"id": f"P{i}", "kind": f"kind{min(i, kinds - 1)}", "input": f"planted {i}"} for i in range(n)]
    found = n if found is None else found
    return {"stage": role, "tier": tier, "template": f"{role}@{version}", "plants": plants,
            "findings": [{"plant_id": f"P{i}", "quote": "..."} for i in range(found)],
            "control": {"input": "a clean doc", "findings": [] if control_findings is None else control_findings}}


def t3() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="swf-t3-"))
    try:
        def lint(role: str, tier: str, proof: dict | None, model_line: str | None = None) -> list[str]:
            m = json.loads(json.dumps(models()))
            ref = None
            if proof is not None:
                (tmp / "proof.json").write_text(json.dumps(proof), encoding="utf-8")
                ref = str(tmp / "proof.json")
            m["stages"][role] = {"tier": tier, "proof": ref}
            text = replace_field(template(role), "MODEL", model_line or tier)
            return lt.lint_text(text, role, m, REPO)
        e = lint("recon", "mid", None)
        check("T-3 FAULT MODEL mid with no proof fails", any("names no plant-run proof" in x for x in e), str(e))
        e = lint("recon", "mid", _proof(found=2))
        check("T-3 FAULT a proof missing one planted id fails", any("NOT caught" in x and "P2" in x for x in e), str(e))
        e = lint("recon", "mid", _proof(control_findings=[{"quote": "false alarm"}]))
        check("T-3 FAULT a proof whose clean control has a finding fails", any("control drew findings" in x for x in e), str(e))
        p = _proof()
        del p["control"]
        check("T-3 FAULT a proof with no control fails", any("no CLEAN control" in x for x in lint("recon", "mid", p)))
        e = lint("recon", "mid", _proof(n=2, kinds=2))
        check("T-3 FAULT only 2 plants fails (the plant-count rule itself, not only the kinds rule)",
              any("plants; at least 3 objects" in x for x in e), str(e))
        p = _proof()
        p["plants"].append("a plant that is not an object")
        e = lint("recon", "mid", p)
        check("T-3 FAULT a plant that is not an object fails", any("plants; at least 3 objects" in x for x in e), str(e))
        e = lint("recon", "mid", _proof(n=3, kinds=2))
        check("T-3 FAULT 3 plants of only 2 kinds fails", any("kinds" in x for x in e), str(e))
        e = lint("recon", "mid", _proof(version=2))
        check("T-3 FAULT a proof for another template version fails", any("template" in x for x in e), str(e))
        e = lint("recon", "cheap", _proof(tier="mid"))
        check("T-3 FAULT a mid proof does not earn cheap", any("earned tier" in x for x in e), str(e))
        e = lint("recon", "mid", _proof(role="build"))
        check("T-3 FAULT a proof for another stage fails", any("for stage" in x for x in e), str(e))
        e = lint("recon", "mid", _proof(), model_line="top")
        check("T-3 FAULT MODEL top in the template vs mid in models.json fails", any("disagrees" in x for x in e), str(e))
        e = lint("recon", "mid", _proof(), model_line="medium")
        check("T-3 FAULT MODEL `medium` is not a tier", any("is not one of" in x for x in e), str(e))
        e = lint("verify", "mid", _proof(role="verify"))
        check("T-3 FAULT verify moved to mid fails EVEN WITH a valid proof (pinned top)", any("pinned" in x for x in e), str(e))
        e = lint("recon", "mid", _proof())
        check("T-3 CONTROL 3 plants of 3 kinds, all found, clean control -> pass", e == [], str(e))
        e = lint("recon", "cheap", _proof(tier="cheap", n=4, kinds=3))
        check("T-3 CONTROL 4 plants of 3 kinds at cheap -> pass", e == [], str(e))
        check("T-3 CONTROL models.json ships EVERY stage at top",
              all(s.get("tier") == "top" for s in models()["stages"].values()) and set(models()["stages"]) == set(ROLES))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------------------------------------------------- T-4
def t4() -> None:
    m = models()
    base = without_field(template("build"), "DO-NOT-READ")
    fenced = ("\nThe DO-NOT-READ list is below; DO-NOT-READ matters.\n```\n## DO-NOT-READ\n- `ai_player/evidence/`\n"
              "- `**/INDEX.md`\n```\n")
    mention = base.replace("## STOP", fenced + "\n## STOP", 1)
    e = lt.lint_text(mention, "build", m, REPO)
    check("T-4 FAULT a prose mention and a FENCED `## DO-NOT-READ` do not satisfy the missing field",
          any(x.startswith("DO-NOT-READ:") and "missing" in x for x in e), str(e))
    noisy = template("build").replace(
        "## READ-LIST", "Prose: MODEL: cheap is not a field.\n```\n## MODEL\ncheap\n```\n~~~\n## MODEL\nmid\n~~~\n\n## READ-LIST", 1)
    e = lt.lint_text(noisy, "build", m, REPO)
    check("T-4 CONTROL fenced `## MODEL` blocks and a prose MODEL do not break a real top template", e == [], str(e))
    check("T-4 CONTROL the parsed MODEL is still `top`",
          lt.model_tier(lt.parse(noisy)["fields"]["MODEL"][0]) == "top")
    unclosed = template("build").replace("## READ-LIST", "```\n## READ-LIST", 1)
    e = lt.lint_text(unclosed, "build", m, REPO)
    check("T-4 FAULT an unclosed fence is a finding (never a silent blank-out)", any("never closes" in x for x in e), str(e))


# ------------------------------------------------------------------------------------------------------------- T-5
def t5() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="swf-t5-"))
    try:
        def refused(text: str, vals: dict, role: str = "build", needle: str = "") -> tuple[bool, str]:
            try:
                render.render(text, vals, role, tmp)
                return False, "rendered"
            except render.RenderError as error:
                return (not needle or any(needle in r for r in error.reasons)), str(error.reasons)
        full = values_for("build", tmp)
        for role in ROLES:
            out = render.render(template(role), values_for(role, tmp), role, tmp)
            ok = out.split("\n", 1)[0] == f"<!-- stage-template:{role}@1 -->" and "{{" not in out and "}}" not in out
            check(f"T-5 CONTROL {role} renders with full values; line 1 is the marker, no braces remain", ok)
        vals = dict(full)
        del vals["goal"]
        check("T-5 FAULT an unresolved placeholder is refused", *refused(template("build"), vals, needle="{{goal}}"))
        vals = dict(full, goal="   ")
        check("T-5 FAULT an empty required value is refused", *refused(template("build"), vals, needle="empty value"))
        vals = dict(full, goal="see {{other}}")
        check("T-5 FAULT a value carrying {{...}} is refused", *refused(template("build"), vals, needle="{{other}}"))
        vals = dict(full, goal="x\n## MODEL\ncheap")
        check("T-5 FAULT a value that injects a second MODEL field is refused",
              *refused(template("build"), vals, needle="MODEL"))
        text = replace_field(template("build"), "STOP", "{{stop_note?}}")
        check("T-5 FAULT a field left empty after filling is refused", *refused(text, full, needle="STOP"))
        check("T-5 FAULT a text without this role's marker is refused",
              *refused(template("build").split("\n", 1)[1], full, needle="marker"))
        check("T-5 FAULT a template rendered as another role is refused",
              *refused(template("build"), full, role="verify", needle="marker"))
        vals = dict(full)
        vals.pop("extra_reads", None)
        out = render.render(template("build"), vals, "build", tmp)
        check("T-5 CONTROL an optional {{extra_reads?}} may be left out", "{{" not in out)
        code = quiet(render.main, ["build", "--values", str(_dump(tmp, full)), "--format", "json", "--out", str(tmp / "o.json")])
        data = json.loads((tmp / "o.json").read_text(encoding="utf-8"))
        check("T-5 CONTROL the CLI --format json gives prompt, tier top and model null",
              code == 0 and data["tier"] == "top" and data["model"] is None and data["prompt"].startswith("<!-- stage-"))
        bad = dict(full)
        del bad["goal"]
        code = quiet(render.main, ["build", "--values", str(_dump(tmp, bad)), "--out", str(tmp / "o2.txt")])
        check("T-5 FAULT the CLI exits 2 on a refusal and writes nothing", code == 2 and not (tmp / "o2.txt").exists())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _dump(tmp: Path, vals: dict) -> Path:
    path = tmp / f"values-{len(list(tmp.iterdir()))}.json"
    path.write_text(json.dumps(vals), encoding="utf-8")
    return path


# ------------------------------------------------------------------------------------------------------------- T-6
def t6() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="swf-t6-"))
    try:
        cases = [
            ("all_pass true, FAILURES []", '{"all_pass": true, "FAILURES": []}', "PASS"),
            ("all_pass true, no FAILURES key", '{"all_pass": true}', "PASS"),
            ("all_pass false, FAILURES non-empty", '{"all_pass": false, "FAILURES": ["x broke"]}', "REFIX"),
            ("missing file", None, "UNKNOWN"),
            ("bad JSON", '{"all_pass": false, "FAILURES": [', "UNKNOWN"),
            ("all_pass absent", '{"FAILURES": ["x"]}', "UNKNOWN"),
            ('all_pass the STRING "false"', '{"all_pass": "false", "FAILURES": ["x"]}', "UNKNOWN"),
            ('all_pass the STRING "true"', '{"all_pass": "true", "FAILURES": []}', "UNKNOWN"),
            ("all_pass false, FAILURES empty", '{"all_pass": false, "FAILURES": []}', "UNKNOWN"),
            ("all_pass false, FAILURES missing", '{"all_pass": false}', "UNKNOWN"),
            ("all_pass true WITH failures (contradiction)", '{"all_pass": true, "FAILURES": ["x"]}', "UNKNOWN"),
            ("lowercase failures key only", '{"all_pass": false, "failures": ["x"]}', "UNKNOWN"),
            ("FAILURES a string", '{"all_pass": false, "FAILURES": "x"}', "UNKNOWN"),
            ("top level a list", '[{"all_pass": true}]', "UNKNOWN"),
            ("top level a string that CONTAINS all_pass", '"all_pass: true"', "UNKNOWN"),
        ]
        for i, (label, body, want) in enumerate(cases):
            path = tmp / f"v{i}.json"
            if body is not None:
                path.write_text(body, encoding="utf-8")
            got = sh.refix_decision(path)
            check(f"T-6 {label} -> {want}", got == want, f"got {got}")
        never = all(sh.refix_decision(tmp / f"v{i}.json") != "PASS" for i, c in enumerate(cases) if c[2] == "UNKNOWN")
        check("T-6 no UNKNOWN shape ever reads PASS", never)
        codes = [quiet(sh.main, ["refix", str(tmp / "v0.json")]), quiet(sh.main, ["refix", str(tmp / "v2.json")]),
                 quiet(sh.main, ["refix", str(tmp / "v3.json")])]
        check("T-6 CLI exit codes: PASS 0, REFIX 1, UNKNOWN 2", codes == [0, 1, 2], str(codes))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------------------------------------------------- T-7
def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          cwd=str(repo), capture_output=True, text=True, check=True, timeout=60).stdout


def _evidence(repo: Path, name: str, commit: str, digest: str, mtime: float | None = None) -> None:
    path = repo / "ai_player" / "evidence" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    state = "clean at HEAD" if digest == rd.CLEAN_DIGEST else "has UNCOMMITTED changes"
    path.write_text(f"TITLE\ncode: HEAD {commit}; ai_player/ {state} (working-tree digest sha256:{digest})\n",
                    encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def _tree_hash(repo: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(repo.rglob("*")):
        if ".git" in p.relative_to(repo).parts or not p.is_file():
            continue
        h.update(str(p.relative_to(repo)).encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def t7() -> None:
    repo = Path(tempfile.mkdtemp(prefix="swf-t7-"))
    try:
        _git(repo, "init", "-q")
        files = {"ai_player/__init__.py": "", "ai_player/brain/a.py": "A = 1\n", "ai_player/README.md": "# doc\n",
                 "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py": "HOOK = 1\n", "other/x.py": "X = 1\n"}
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "c1")
        c1 = _git(repo, "rev-parse", "--short", "HEAD").strip()
        smap_path = repo / "map.json"
        smap = {"evidence_dir": "ai_player/evidence", "exclude": ["ai_player/evidence/**", "**/*.md"],
                "suites": {"units": {"evidence": ["*-units.txt"],
                                     "covers": ["ai_player/**", "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py"]},
                           "other": {"evidence": ["*-other.txt"], "covers": ["other/**"]},
                           "ghost": {"evidence": ["*-ghost.txt"], "covers": ["other/**"]}}}
        smap_path.write_text(json.dumps(smap), encoding="utf-8")
        _evidence(repo, "2026-10-21-t-units.txt", c1, rd.CLEAN_DIGEST)
        _evidence(repo, "2026-10-21-t-other.txt", c1, rd.CLEAN_DIGEST)

        def rows() -> dict[str, tuple[bool, str]]:
            return {n: (due, why) for n, due, why in rd.assess(repo, rd.load_map(smap_path, repo))}
        before = _tree_hash(repo)
        r = rows()
        check("T-7 read-only: assess changed no file of the repo", _tree_hash(repo) == before)
        check("T-7 CONTROL nothing changed -> units ok (same tree)", r["units"][0] is False, r["units"][1])
        check("T-7 FAULT no evidence -> DUE never run", r["ghost"][0] and "never run" in r["ghost"][1], r["ghost"][1])

        (repo / "ai_player/README.md").write_text("# doc changed\n", encoding="utf-8")
        r = rows()
        check("T-7 CONTROL an uncommitted doc-only change does not list units", r["units"][0] is False, r["units"][1])
        _git(repo, "commit", "-q", "-am", "doc")
        r = rows()
        check("T-7 CONTROL a COMMITTED doc-only change does not list units", r["units"][0] is False, r["units"][1])

        (repo / "ai_player/brain/a.py").write_text("A = 2\n", encoding="utf-8")
        r = rows()
        check("T-7 FAULT an uncommitted change to a covered file lists units, naming the file",
              r["units"][0] and "ai_player/brain/a.py" in r["units"][1], r["units"][1])
        check("T-7 CONTROL the same change does not list `other` (not covered)", r["other"][0] is False, r["other"][1])
        _git(repo, "commit", "-q", "-am", "code")
        r = rows()
        check("T-7 FAULT a COMMITTED covered change (both trees clean, equal digests) still lists units",
              r["units"][0] and "a.py" in r["units"][1], r["units"][1])

        c3 = _git(repo, "rev-parse", "--short", "HEAD").strip()
        _evidence(repo, "2026-10-22-t-units.txt", c3, rd.CLEAN_DIGEST)
        r = rows()
        check("T-7 CONTROL the NEWEST evidence (by its date) wins: units ok again", r["units"][0] is False, r["units"][1])
        hook = repo / "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py"
        hook.write_text("HOOK = 2\n", encoding="utf-8")
        r = rows()
        check("T-7 FAULT a covered file OUTSIDE the digest scope (same HEAD, same digest) lists units",
              r["units"][0] and "ai_player_mode.py" in r["units"][1], r["units"][1])
        _git(repo, "checkout", "-q", "--", "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py")

        # uncommitted evidence: cleared only through a kept tree that recomputes to its digest
        (repo / "ai_player/brain/a.py").write_text("A = 3\n", encoding="utf-8")
        _, diff, untracked, _ = read_tree(repo)
        dirty = tree_digest(diff, untracked)[:16]
        _evidence(repo, "2026-10-23-t-units.txt", c3, dirty)
        _evidence(repo, "2026-10-23-t-other.txt", c3, dirty)
        aside = Path(tempfile.mkdtemp(prefix="swf-t7-kept-"))
        kept = snapshot_tree(repo, folder=aside)  # kept at evidence time, held OUTSIDE trees/ for the no-kept-tree arm
        check("T-7 setup: the kept tree is the evidence's digest", kept is not None and kept.stem == dirty, str(kept))
        r = rows()
        check("T-7 CONTROL dirty evidence on THIS dirty tree (same HEAD, same digest) -> units ok",
              r["units"][0] is False, r["units"][1])
        _git(repo, "commit", "-q", "-am", "commit the tested change")
        r = rows()
        check("T-7 FAULT dirty evidence, no kept tree -> `other` DUE (cannot be cleared)",
              r["other"][0] and "uncommitted evidence" in r["other"][1], r["other"][1])
        (repo / "ai_player" / "evidence" / "trees").mkdir(parents=True, exist_ok=True)
        kept = Path(shutil.move(str(kept), str(repo / "ai_player" / "evidence" / "trees" / kept.name)))
        shutil.rmtree(aside, ignore_errors=True)
        r = rows()
        check("T-7 CONTROL with the kept tree, `other` (does not cover a.py) is cleared", r["other"][0] is False, r["other"][1])
        check("T-7 FAULT with the kept tree, units (covers a.py) stays DUE", r["units"][0] and "a.py" in r["units"][1],
              r["units"][1])
        aside = Path(tempfile.mkdtemp(prefix="swf-t7-other-"))
        other_tree = snapshot_tree(repo, folder=aside)  # a VALID kept tree of THIS (clean) tree: another digest
        shutil.copyfile(other_tree, kept)
        shutil.rmtree(aside, ignore_errors=True)
        r = rows()
        check("T-7 FAULT a valid kept tree of ANOTHER digest under the evidence's name clears nothing",
              r["other"][0] and "uncommitted" in r["other"][1], r["other"][1])
        kept.write_bytes(b"not a zip")
        r = rows()
        check("T-7 FAULT a damaged kept tree clears nothing", r["other"][0] and "uncommitted" in r["other"][1], r["other"][1])

        _evidence(repo, "2026-10-24-t-other.txt", "deadbeef", rd.CLEAN_DIGEST)
        r = rows()
        check("T-7 FAULT an evidence commit unknown to the repo -> DUE", r["other"][0] and "unknown commit" in r["other"][1],
              r["other"][1])
        (repo / "ai_player/evidence/2026-10-25-t-other.txt").write_text("no code line here\n", encoding="utf-8")
        r = rows()
        check("T-7 FAULT an evidence file with no code line -> DUE no provenance",
              r["other"][0] and "no provenance" in r["other"][1], r["other"][1])

        smap["suites"]["units"]["covers"].append("ai_player/brian/**")
        smap_path.write_text(json.dumps(smap), encoding="utf-8")
        try:
            rd.load_map(smap_path, repo)
            ok, why = False, "loaded"
        except rd.MapError as error:
            ok, why = "ai_player/brian/**" in str(error), str(error)
        check("T-7 FAULT an unknown glob in suite_map.json is an error naming it", ok, why)
        code = quiet(rd.main, ["--map", str(smap_path), "--repo", str(repo)])
        check("T-7 FAULT the CLI exits 2 on that map (not silence)", code == 2, str(code))
        real = rd.load_map(WORKFLOWS / "suite_map.json", REPO)
        check("T-7 CONTROL the shipped suite_map.json loads (every glob matches a real file)", bool(real["suites"]))
    finally:
        shutil.rmtree(repo, ignore_errors=True)


# ------------------------------------------------------------------------------------------------------------- T-8
def _transcript(path: Path, users: list[str]) -> None:
    lines = []
    for i, text in enumerate(users):
        lines.append({"type": "user", "timestamp": f"2026-10-21T12:00:0{i}Z", "message": {"role": "user", "content": text}})
    lines.append({"type": "assistant", "timestamp": "2026-10-21T12:00:09Z",
                  "message": {"id": "msg_1", "role": "assistant", "model": "claude-x", "content": [{"type": "text", "text": "ok"}],
                              "usage": {"input_tokens": 1, "output_tokens": 1}}})
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")


def _templated(path: Path):
    agent = ua.Agent(path, "s", "workflow", "wf_test", "stage", "phase")
    ua.scan_file(path, agent, Counter())
    return agent.templated


def t8() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="swf-t8-"))
    try:
        for role in ROLES:
            prompt = render.render(template(role), values_for(role, tmp), role, tmp)
            first = prompt.split("\n", 1)[0]
            check(f"T-8 {role}: line 1 is exactly `<!-- stage-template:{role}@<ver> -->` and starts with usage_audit.MARKER",
                  lt.MARKER_RE.fullmatch(first) is not None and first.startswith(ua.MARKER) and f":{role}@" in first)
            computed = ("[Workflow harness — computed task] The task text below was computed at runtime by a workflow "
                        "script.\n" + "\n".join("  " + x for x in prompt.split("\n")))
            for label, text in (("bare", prompt), ("in the computed-task framing", computed)):
                path = tmp / f"{role}-{label[:4]}.jsonl"
                _transcript(path, [text])
                check(f"T-8 {role} ({label}): usage_audit.scan_file counts the agent TEMPLATED", _templated(path) is True)
            path = tmp / f"{role}-nomark.jsonl"
            _transcript(path, [prompt.split("\n", 1)[1]])
            check(f"T-8 CONTROL {role} without its marker: usage_audit counts it UNTEMPLATED", _templated(path) is False)
        relay = "[Workflow harness — user request] The harness relays, verbatim and indented below, the user request.\n  hi"
        path = tmp / "relay.jsonl"
        _transcript(path, [relay, "[Workflow harness — computed task] ...\n  " + render.render(
            template("build"), values_for("build", tmp), "build", tmp).replace("\n", "\n  ")])
        NOTES.append(f"T-8 NOTE (not graded): an agent whose FIRST user message is the harness's user-request relay and "
                     f"whose SECOND is a rendered template is seen by usage_audit as templated={_templated(path)} "
                     f"(usage_audit reads only the first non-tool-result user message).")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    for name, fn in (("T-1", t1), ("T-2", t2), ("T-3", t3), ("T-4", t4), ("T-5", t5), ("T-6", t6), ("T-7", t7), ("T-8", t8)):
        guarded(name, fn)
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:300]}"))
    for note in NOTES:
        print(note)
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
