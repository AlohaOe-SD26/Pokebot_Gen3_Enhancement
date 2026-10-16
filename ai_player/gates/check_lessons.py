"""TEST SIDE (build step 5.2, G7): the LESSONS list stays honest (`ai_player/LESSONS.md`).

    py -3.12 ai_player/gates/check_lessons.py [--lessons PATH]        exit 0 = PASS, 1 = FAIL

WHY (the user's 2026-10-15 directive: a LIVING lessons list; CLAUDE.md session rule 6, a rule already broken twice belongs
in a gate): a list of lessons is only worth its pointers. A lesson that says "GATED by X" while X does not exist (renamed,
deleted, a typo) tells the next agent a mistake is impossible when nothing stops it. So, for EVERY lesson (`### XX-N. title`):
  * it has an **Origin** with a date and at least one QUOTE of the document it cites, found there (`08`, `07`, `06`,
    `README`, `REVIEW`, `CLAUDE` "fragment": `DOCUMENTS`), a **Status** (GATED, PARTIAL, PROSE ONLY; RETIRED under
    "## Retired", with a **Retired** line) and a **Retires** line;
  * GATED and PARTIAL lessons have an **Enforced** line naming at least one REFERENCE, and EVERY reference there resolves:
      `gates/F` or a repository path (`ai_player/...`, `.claude/...`, `ai-agent/...`, `tools/...`): the file exists;
      `...::Name` or `...::Class.member`: defined in that Python file (by AST: a function, a class, a module constant);
      `mod:KEY` (a MUTANTS or SUITES key of `gates/mod.py`) and `mod:DICT.KEY` (a key of that module's dict literal);
    and any other backticked token there that LOOKS like a reference (a "/", ".py", "::" or "word:word") must resolve too,
    so a typo fails instead of being skipped;
  * PROSE ONLY and PARTIAL lessons have a **Needs** line (the gate they need);
  * every gate of build step 5.2 (`REQUIRED`) is named by some lesson's Enforced line.
MENTIONS NEVER FIRE: only the Enforced line's references are resolved. A gate named in a title, a rule, an Origin or a Needs
line (a gate still to be built) is prose. `test_safety_gates.py` LessonsTests plants both.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LESSONS = REPO / "ai_player" / "LESSONS.md"
GATES = REPO / "ai_player" / "gates"
#: the project's documents, from this repository (a mutant COPY of the package names it: `AI_PLAYER_TEST_SUPPORT_ROOT`)
SUPPORT = Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO)
KNOWLEDGE = SUPPORT / "PROJECT KNOWLEDGE"
DOCUMENTS = {
    "08": KNOWLEDGE / "08-MISTAKES.md",
    "07": KNOWLEDGE / "07-CHANGELOG.md",
    "06": KNOWLEDGE / "06-DECISIONS-LOG.md",
    "README": REPO / "ai_player" / "README.md",
    "REVIEW": KNOWLEDGE / "ai-research-notes" / "2026-10-15-step51-REVIEW-FINDINGS.md",
    "CLAUDE": SUPPORT / "CLAUDE.md",
}
STATUSES = ("GATED", "PARTIAL", "PROSE ONLY", "RETIRED")
#: the gates of build step 5.2 that some lesson must name (G1-G6)
REQUIRED = ("gates/provenance.py::FrozenTree", "gates/ledger.py", "gates/call_census.py", "gates/check_fairness.py",
            "gates/disk_budget.py::preflight", "gates/provenance.py::code_digest")
LESSON = re.compile(r"^### (?P<id>[A-Z]{2}-\d+)\. (?P<title>.+)$", re.M)
FIELD = re.compile(r"^- \*\*(?P<name>[A-Za-z ]+):\*\* ?(?P<value>.*)$", re.M)
QUOTE = re.compile(r"\b(?P<doc>08|07|06|README|REVIEW|CLAUDE) \"(?P<text>[^\"]+)\"")
TICKED = re.compile(r"`([^`]+)`")
PATH_ROOTS = ("ai_player/", ".claude/", "ai-agent/", "tools/", "PROJECT KNOWLEDGE/")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _module_names(path: Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = node
    return out


def _dict_keys(node: ast.AST) -> set[str]:
    value = getattr(node, "value", None)
    if isinstance(value, ast.Dict):
        return {k.value for k in value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    return set()


def resolve(token: str) -> str | None:
    """None when the reference resolves, else why not."""
    if "::" in token:
        file, _, name = token.partition("::")
    else:
        file, name = token, ""
    module = re.fullmatch(r"(?P<mod>[a-z_0-9]+):(?P<key>[A-Za-z_0-9.]+)", token)
    if module and "/" not in token:
        path = GATES / f"{module['mod']}.py"
        if not path.is_file():
            return f"no gate module gates/{module['mod']}.py"
        names = _module_names(path)
        key = module["key"]
        if "." in key:
            table, _, entry = key.partition(".")
            if table not in names:
                return f"gates/{module['mod']}.py defines no {table}"
            return None if entry in _dict_keys(names[table]) else f"{module['mod']}.{table} has no key {entry!r}"
        for table in ("MUTANTS", "SUITES"):
            if table in names and key in _dict_keys(names[table]):
                return None
        return f"{key!r} is no MUTANTS or SUITES key of gates/{module['mod']}.py"
    if file.startswith("gates/"):
        path = GATES / file[len("gates/"):]
    elif file.startswith("ai_player/"):
        path = REPO / file
    else:
        path = SUPPORT / file  # `.claude/`, `ai-agent/`, `tools/`: the repository's, outside the package
    if not path.exists():
        return f"{file} does not exist"
    if not name:
        return None
    if path.suffix != ".py":
        return f"{file} is not a Python file (::{name})"
    names = _module_names(path)
    top, _, member = name.partition(".")
    if top not in names:
        return f"{file} defines no {top}"
    if member:
        holder = names[top]
        if not isinstance(holder, ast.ClassDef):
            return f"{file}::{top} is not a class (.{member})"
        members = {n.name for n in holder.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        members |= {t.id for n in holder.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
        members |= {n.target.id for n in holder.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
        if member not in members:
            return f"{file}::{top} has no {member}"
    return None


def looks_like_reference(token: str) -> bool:
    return ("/" in token or token.endswith((".py", ".ps1", ".json", ".md")) or "::" in token
            or re.fullmatch(r"[a-z_0-9]+:[A-Za-z_0-9.]+", token) is not None)


def parse(text: str) -> list[dict]:
    """Every lesson: id, title, its fields, and whether it sits under '## Retired'."""
    retired_at = text.find("\n## Retired")
    starts = [m for m in LESSON.finditer(text)]
    lessons = []
    for at, found in enumerate(starts):
        end = starts[at + 1].start() if at + 1 < len(starts) else len(text)
        body = text[found.end():end]
        cut = body.find("\n## ")
        if cut >= 0:
            body = body[:cut]
        fields = {m["name"].strip(): m["value"].strip() for m in FIELD.finditer(body)}
        lessons.append({"id": found["id"], "title": found["title"], "fields": fields,
                        "retired": retired_at >= 0 and found.start() > retired_at})
    return lessons


def check(text: str, documents: dict[str, Path] = DOCUMENTS, required: tuple[str, ...] = REQUIRED) -> tuple[list[str], dict]:
    """(problems, counts by status)."""
    problems: list[str] = []
    lessons = parse(text)
    cache: dict[str, str] = {}
    counts: dict[str, int] = {}
    named: set[str] = set()
    if not lessons:
        problems.append("no lessons found (a lesson begins '### XX-N. title')")
    ids = [lesson["id"] for lesson in lessons]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"{dup}: two lessons with this id")
    for lesson in lessons:
        tag, fields = lesson["id"], lesson["fields"]
        status = next((s for s in STATUSES if fields.get("Status", "").upper().startswith(s)), None)
        counts[status or "?"] = counts.get(status or "?", 0) + 1
        if status is None:
            problems.append(f"{tag}: Status {fields.get('Status')!r} is none of {STATUSES}")
        if lesson["retired"] != (status == "RETIRED"):
            problems.append(f"{tag}: RETIRED lessons live under '## Retired', and only they")
        origin = fields.get("Origin", "")
        if not re.search(r"\d{4}-\d{2}-\d{2}", origin):
            problems.append(f"{tag}: its Origin names no date")
        quotes = list(QUOTE.finditer(origin))
        if not quotes:
            problems.append(f"{tag}: its Origin quotes no document (08/07/06/README/REVIEW/CLAUDE \"fragment\")")
        for quote in quotes:
            doc = quote["doc"]
            if doc not in cache:
                path = documents.get(doc)
                cache[doc] = _norm(path.read_text(encoding="utf-8", errors="replace")) if path and path.is_file() else ""
            if _norm(quote["text"]) not in cache[doc]:
                problems.append(f"{tag}: its Origin quotes {doc} \"{quote['text']}\", which {doc} does not contain")
        if "Retires" not in fields and status != "RETIRED":
            problems.append(f"{tag}: no Retires line (when does it retire?)")
        if status == "RETIRED" and "Retired" not in fields:
            problems.append(f"{tag}: a RETIRED lesson needs its Retired line (the date and the gate)")
        if status in ("PROSE ONLY", "PARTIAL") and not fields.get("Needs"):
            problems.append(f"{tag}: a {status} lesson names the gate it Needs")
        if status in ("GATED", "PARTIAL"):
            tokens = [t for t in TICKED.findall(fields.get("Enforced", "")) if looks_like_reference(t)]
            if not tokens:
                problems.append(f"{tag}: {status} but its Enforced line names no gate, test, mutant or file")
            for token in tokens:
                why = resolve(token)
                if why is not None:
                    problems.append(f"{tag}: Enforced names `{token}`: {why}")
                else:
                    named.add(token)
    for gate in required:
        if not any(n == gate or n.startswith(gate + ".") or n.startswith(gate + "::") for n in named):
            problems.append(f"the gate `{gate}` is named by no lesson's Enforced line")
    return problems, counts


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lessons", type=Path, default=LESSONS)
    args = parser.parse_args()
    problems, counts = check(args.lessons.read_text(encoding="utf-8"))
    for line in problems:
        print(f"  [FAIL] {line}")
    print(f"LESSONS {args.lessons.name}: {sum(counts.values())} lessons, by status {dict(sorted(counts.items()))}")
    print(f"LESSONS CHECK: {'PASS' if not problems else 'FAIL'} ({len(problems)} problems)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
