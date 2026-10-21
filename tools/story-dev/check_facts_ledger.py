"""LINT the verified-facts ledger (backlog P5, spec S3-2): `PROJECT KNOWLEDGE/facts-ledger.jsonl`.

WHY. A fact that an agent checked once (a decomp symbol, a map, a refuted claim) is re-derived by the next agent, or
worse, re-asserted after it was refuted. The ledger holds one JSON object per line, APPEND-ONLY:
    id, claim, status (CONFIRMED | REFUTED | UNVERIFIED), source {kind: decomp|probe|code|user|evidence, ref},
    tool (the command that RE-CHECKS it), dependents (paths that rely on it), first_seen, last_checked, checked_by,
    correction (REFUTED only: what is true instead)
A ledger is only as good as its `tool` field: a row whose tool does not re-check the claim is a lie with a format.

RULES (exit 1 on any failure, every failure listed):
  json        every non-blank line parses as one object; ids are unique
  required    every field above is present; status and source.kind are in their sets; dates are YYYY-MM-DD
  confirmed   a CONFIRMED row has a non-empty source.ref AND a tool
  refuted     a REFUTED row has a correction
  tool        the tool names a .py script that exists under `tools/` (where every gate lives)
  dependents  every dependent path exists
  refs        decomp: `pret/pokeemerald@<sha>:<path>[:<symbol>]`, <sha> a prefix of `tools/decomp.pin`; with the pinned
              clone present the path must exist there and the symbol must be found by `decomp_lookup.py symbol` in
              that file. code/probe/evidence: `<path>[:<text>]`, the path exists and the text occurs in it.
  history     `--against-head` (or `--against FILE`): a REFUTED row may never be removed or edited, and no row id may
              disappear (append-only). Appending passes.
WARN (exit 4, never a pass): with no pinned clone (or one at the wrong commit), decomp refs cannot be checked: the
lint prints `SKIPPED <n> decomp refs (...)`. A check that silently skips on another machine is vacuous.

Run:  py -3.12 tools/story-dev/check_facts_ledger.py [--against-head] [--ledger F] [--repo DIR] [--decomp DIR]
Exit: 0 clean (every decomp ref verified); 1 a failure; 4 WARN (clean, but decomp refs SKIPPED).
"""
from __future__ import annotations

import argparse
import json
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
REPO = HERE.parents[1]
LEDGER_REL = "PROJECT KNOWLEDGE/facts-ledger.jsonl"
sys.path.insert(0, str(REPO / "tools"))
import decomp_lookup as dl  # noqa: E402

FIELDS = ("id", "claim", "status", "source", "tool", "dependents", "first_seen", "last_checked", "checked_by")
STATUSES = {"CONFIRMED", "REFUTED", "UNVERIFIED"}
KINDS = {"decomp", "probe", "code", "user", "evidence"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECOMP_REF_RE = re.compile(r"^pret/pokeemerald@([0-9a-f]{7,40}):([^:]+)(?::(.+))?$")
EXIT_OK, EXIT_FAIL, EXIT_WARN = 0, 1, 4


def parse_rows(text: str) -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for n, ln in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if not ln.strip():
            continue
        try:
            obj = json.loads(ln)
        except ValueError as exc:
            problems.append(f"FAIL json: line {n} does not parse ({exc})")
            continue
        if not isinstance(obj, dict):
            problems.append(f"FAIL json: line {n} is not an object")
            continue
        obj["_line"] = n
        rows.append(obj)
    return rows, problems


# --- the guards: each is ONE function, called on ONE line of lint() (the mutant harness deletes one call at a time)

def check_unique(rows: list[dict]) -> list[str]:
    seen, out = {}, []
    for r in rows:
        if r.get("id") in seen:
            out.append(f"FAIL json: id {r.get('id')!r} on lines {seen[r['id']]} and {r['_line']}")
        seen[r.get("id")] = r["_line"]
    return out


def check_required(rows: list[dict]) -> list[str]:
    out = []
    for r in rows:
        tag = f"line {r['_line']} {r.get('id', '?')}"
        missing = [f for f in FIELDS if f not in r]
        if missing:
            out.append(f"FAIL required: {tag} lacks {missing}")
        if r.get("status") not in STATUSES:
            out.append(f"FAIL required: {tag} status {r.get('status')!r} not in {sorted(STATUSES)}")
        src = r.get("source")
        if src is not None and (not isinstance(src, dict) or src.get("kind") not in KINDS):
            out.append(f"FAIL required: {tag} source must be {{kind: {'|'.join(sorted(KINDS))}, ref}}")
        for f in ("first_seen", "last_checked"):
            if f in r and not DATE_RE.match(str(r[f])):
                out.append(f"FAIL required: {tag} {f} {r[f]!r} is not YYYY-MM-DD")
        if "dependents" in r and not isinstance(r["dependents"], list):
            out.append(f"FAIL required: {tag} dependents must be a list of paths")
    return out


def check_confirmed(rows: list[dict]) -> list[str]:
    out = []
    for r in rows:
        if r.get("status") == "CONFIRMED":
            src = r.get("source") if isinstance(r.get("source"), dict) else {}
            if not str(src.get("ref", "")).strip():
                out.append(f"FAIL confirmed: line {r['_line']} {r.get('id')} is CONFIRMED with no source.ref")
            if not str(r.get("tool", "")).strip():
                out.append(f"FAIL confirmed: line {r['_line']} {r.get('id')} is CONFIRMED with no tool")
    return out


def check_refuted(rows: list[dict]) -> list[str]:
    return [f"FAIL refuted: line {r['_line']} {r.get('id')} is REFUTED with no correction"
            for r in rows if r.get("status") == "REFUTED" and not str(r.get("correction", "")).strip()]


def check_tool(rows: list[dict], repo: Path) -> list[str]:
    out = []
    for r in rows:
        tool = str(r.get("tool", ""))
        if not tool.strip():
            continue
        scripts = re.findall(r"[\w./\\-]+\.py\b", tool)
        if not scripts:
            out.append(f"FAIL tool: line {r['_line']} {r.get('id')}: {tool!r} names no .py script")
            continue
        for s in scripts:
            p = (repo / s).resolve()
            tools_dir = (repo / "tools").resolve()
            if not p.is_file():
                out.append(f"FAIL tool: line {r['_line']} {r.get('id')}: {s} does not exist")
            elif tools_dir not in p.parents:
                out.append(f"FAIL tool: line {r['_line']} {r.get('id')}: {s} is not under tools/")
    return out


def check_dependents(rows: list[dict], repo: Path) -> list[str]:
    out = []
    for r in rows:
        for d in r.get("dependents") or []:
            if not (repo / d).exists():
                out.append(f"FAIL dependents: line {r['_line']} {r.get('id')}: {d} does not exist")
    return out


def check_refs(rows: list[dict], repo: Path, root: Path | None, pin: str | None) -> tuple[list[str], int]:
    """(problems, skipped decomp refs). `root` None = no usable pinned clone (every decomp ref is SKIPPED, loudly)."""
    out, skipped = [], 0
    for r in rows:
        src = r.get("source") if isinstance(r.get("source"), dict) else {}
        kind, ref = src.get("kind"), str(src.get("ref", "")).strip()
        tag = f"line {r['_line']} {r.get('id')}"
        if not ref:
            continue
        if kind == "decomp":
            m = DECOMP_REF_RE.match(ref)
            if not m:
                out.append(f"FAIL refs: {tag}: decomp ref {ref!r} is not pret/pokeemerald@<sha>:<path>[:<symbol>]")
                continue
            sha, path, sym = m.groups()
            if pin and not pin.startswith(sha):
                out.append(f"FAIL refs: {tag}: decomp ref names {sha}, not the pinned {pin[:8]}")
                continue
            if root is None:
                skipped += 1
                continue
            if not (root / path).is_file():
                out.append(f"FAIL refs: {tag}: {path} does not exist in the pinned clone")
            elif sym and not dl.symbol(root, sym, (path,)):
                out.append(f"FAIL refs: {tag}: symbol {sym} is not defined in {path} at the pinned commit")
        elif kind in ("code", "probe", "evidence"):
            path, _, text = ref.partition(":")
            p = repo / path
            if not p.is_file():
                out.append(f"FAIL refs: {tag}: {kind} ref path {path} does not exist")
            elif text and text not in p.read_text(encoding="utf-8", errors="replace"):
                out.append(f"FAIL refs: {tag}: {text!r} does not occur in {path}")
    return out, skipped


def check_history(rows: list[dict], baseline: list[dict]) -> list[str]:
    now = {r.get("id"): r for r in rows}
    out = []
    for old in baseline:
        rid = old.get("id")
        if rid not in now:
            out.append(f"FAIL history: row {rid} ({old.get('status')}) was REMOVED; the ledger is append-only")
            continue
        if old.get("status") == "REFUTED":
            a = {k: v for k, v in old.items() if k != "_line"}
            b = {k: v for k, v in now[rid].items() if k != "_line"}
            if a != b:
                out.append(f"FAIL history: REFUTED row {rid} was EDITED; a refuted row may never change")
    return out


def head_baseline(repo: Path) -> tuple[list[dict] | None, str]:
    res = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{LEDGER_REL}"], capture_output=True, timeout=60)
    if res.returncode != 0:
        return None, "the ledger is not in HEAD yet: nothing to compare (append-only starts at its first commit)"
    rows, _ = parse_rows(res.stdout.decode("utf-8"))
    return rows, f"compared with HEAD:{LEDGER_REL} ({len(rows)} rows)"


def resolve_clone(decomp: Path | None, pin_file: Path, no_decomp: bool) -> tuple[Path | None, str | None, str]:
    try:
        pin = dl.read_pin(pin_file)
    except dl.DecompRefused as exc:
        return None, None, f"no pin: {exc}"
    if no_decomp:
        return None, pin, "--no-decomp"
    try:
        return dl.decomp_root(decomp, pin_file), pin, "pinned clone"
    except dl.DecompRefused as exc:
        return None, pin, f"{exc.kind}: {exc}"


def lint(text: str, repo: Path, root: Path | None, pin: str | None,
         baseline: list[dict] | None) -> tuple[list[str], int, int]:
    rows, problems = parse_rows(text)
    problems += check_unique(rows)
    problems += check_required(rows)
    problems += check_confirmed(rows)
    problems += check_refuted(rows)
    problems += check_tool(rows, repo)
    problems += check_dependents(rows, repo)
    ref_problems, skipped = check_refs(rows, repo, root, pin)
    problems += ref_problems
    if baseline is not None:
        problems += check_history(rows, baseline)
    return problems, skipped, len(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=REPO / LEDGER_REL)
    ap.add_argument("--repo", type=Path, default=REPO, help="where dependents, code refs and tools resolve")
    ap.add_argument("--decomp", type=Path)
    ap.add_argument("--pin-file", type=Path, default=dl.PIN_FILE)
    ap.add_argument("--no-decomp", action="store_true", help="skip decomp refs (prints SKIPPED, exits WARN)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--against-head", action="store_true")
    g.add_argument("--against", type=Path, help="a baseline ledger file (tests)")
    args = ap.parse_args(argv)

    if not args.ledger.is_file():
        print(f"FAIL: no ledger at {args.ledger}")
        return EXIT_FAIL
    text = args.ledger.read_bytes().decode("utf-8")
    root, pin, how = resolve_clone(args.decomp, args.pin_file, args.no_decomp)
    baseline, note = None, ""
    if args.against_head:
        baseline, note = head_baseline(args.repo)
    elif args.against:
        baseline, _ = parse_rows(args.against.read_bytes().decode("utf-8"))
        note = f"compared with {args.against} ({len(baseline)} rows)"
    problems, skipped, n = lint(text, args.repo, root, pin, baseline)
    for p in problems:
        print(p)
    if note:
        print(f"history: {note}")
    if problems:
        print(f"FACTS LEDGER LINT FAILED: {len(problems)} problem(s) in {n} row(s)")
        return EXIT_FAIL
    if skipped:
        print(f"SKIPPED {skipped} decomp refs (no pinned clone: {how})")
        print(f"WARN: FACTS LEDGER LINT CLEAN BUT NOT VERIFIED: {n} row(s), {skipped} decomp ref(s) unchecked")
        return EXIT_WARN
    print(f"FACTS LEDGER LINT OK: {n} row(s); decomp refs checked against the {how}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
