r"""DOC CONSISTENCY GATE — the docs may not contradict themselves or the code. Exits 1.

WHY THIS EXISTS (2026-08-13, the cold-start audit)
--------------------------------------------------
`04-HANDOFF.md` answered all seven of the handoff quality-bar questions correctly — and its
NEXT-ACTIONS queue still told a fresh agent to BUILD ROOM 3, which the same file's banner reported
as driven and passing, 500 lines up. A KI header said "ARMED for Room 8" while its own body refuted
it. `24-PLAIN-ENGLISH-STATUS.md` — the file `00-README.md` sends cold readers to FIRST — was five
chapters stale. Numeric counts (gates, drift) disagreed across files. Every one of those sat NEXT TO
correct text, which is why no completeness check saw them: **completeness was checked; CONSISTENCY
was not.** Per CLAUDE.md's session-discipline rule 6, anything enforceable belongs in a GATE — this
is that gate, and it is Tier 0 of the DOC CONSISTENCY LAYER directive.

WHAT IT CHECKS (each prototyped against the live tree before being trusted; the design run found
two REAL rot instances on its first sweep — "DRIFT IS ZERO" in 02, and two stale "19 of 24"s):
  C1  GATE-COUNT claims ("17/17 gates", "N-gate suite", "the N needing no ROM", "gated by `X`")
      match `run_gates.py`'s GATES table, parsed via AST — never by counting lines, the table
      holds a multi-line comment.
  C2  DRIFT-COUNT claims match the MEASURED sandbox<->custom drift (byte-compare of ~200 .py
      files, ~0.06s — measuring is CHEAPER than the doc scan, so the gate never trusts the docs'
      own agreement).
  C3  ‼ THE HEADLINE CHECK: no `--driver X` may be queued as WORK-TO-DO in one place and reported
      COMPLETE/PASSING in another, within the same current-state file — unless the stale half is
      explicitly marked superseded. This is the exact defect the audit found.
  C4  LADDER claims ("N of 24 beats") agree with each other (the ladder only grows; any smaller
      numerator is stale).
  C5  ARTIFACT EXISTENCE: every `--driver X` cited in a current-state doc exists in
      `story_harness.py`'s argparse choices (unless its unit says it is the thing to BUILD);
      every cited `ai-research-notes/*.md` / `tools/story-dev/*.py` path exists.
  W1  (WARN only) KI headers whose status words a skimmer would misread against their own body —
      measured at ~4-in-5 false positives, so it is a human worklist, NEVER a failure.
  W2  (WARN only) `04-HANDOFF.md`'s "Last updated:" date vs its own newest git commit date.

DESIGN RULES THIS FILE KEEPS (all measured, none aesthetic):
  * ‼ CURRENT-STATE FILES ONLY may FAIL: 00-05 and 24. `06/07/08/28/31` are APPEND-ONLY HISTORY
    where stale numbers are CORRECT HISTORY — "All 16 gates PASS" in the changelog is a true
    statement about 2026-08-12. Scanning history produces only false positives.
  * ‼ THE SUPERSESSION EXEMPTION IS LOAD-BEARING, not lenience. This project's documented style
    keeps old text visible under markers ("Superseded text:", "*(superseded)*", "⛔ RETRACTED",
    "Older text follows"). A unit carrying one of those markers is EXEMPT — the gate polices
    claims presented as CURRENT, and only those.
  * Fenced code blocks are stripped before scanning (a driver name in an example fired C3 in
    fault-testing until this was added).
  * Tight phrase-bound regexes only. A loose `(\d+) gates?` matched "Route 121 gate" and
    "KI-59 gates the Regi arc"; a loose drift regex captured dates. Precision over coverage —
    a gate with false positives teaches the reader to bypass it (lint_docs' own rule).

FAULT TESTS (CLAUDE.md rule 6 — a gate must prove it fires AND prove it stays quiet):
    PYTHONUTF8=1 py -3.12 audit_doc_consistency.py --self-test
  A: the audit's exact bug reinjected (unmarked "NEXT: BUILD --driver X" beside "X PASS")
     -> MUST fail.  B: the same text marked superseded -> MUST stay quiet.  C: the same text
     inside a code fence -> MUST stay quiet.  D: a wrong gate count / drift count / ladder count
     injected -> MUST fail.  E: a fabricated driver cited as runnable -> MUST fail.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 audit_doc_consistency.py
Exit: 0 clean, 1 on any FAIL (warnings never fail the run).
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCS = REPO / "PROJECT KNOWLEDGE"

#: FAIL scope: current-state files only. History files are append-only and stale-by-design.
CURRENT_STATE = [
    "00-README.md", "01-VISION-AND-DESIGN.md", "02-ARCHITECTURE.md",
    "03-PUNCH-LIST.md", "04-HANDOFF.md", "05-KNOWN-ISSUES.md",
    "24-PLAIN-ENGLISH-STATUS.md",
]

FENCE_RE = re.compile(r"```.*?```", re.S)
TOKEN_RE = re.compile(r"--driver\s+([a-zA-Z0-9_]+)")

#: High-precision "this is queued work" vocabulary. `(?<![-\w])BUILD` kills `--build custom`.
BUILD_RE = re.compile(
    r"(?<![-\w])BUILD\b(?!\s+custom|\s+sandbox)"
    r"|\bdoes\s+not\s+exist(?:\s+yet)?\b"
    r"|\bthe\s+thing\s+to\s+(?:write|build)\b"
    r"|\bmust\s+be\s+(?:built|written)\b"
    r"|\bnot\s+(?:yet\s+)?(?:built|written|implemented)\b"
    r"|\bhas\s+not\s+been\s+built\b"
    r"|\bNEXT\s*[:>]", re.I)

DONE_RE = re.compile(
    r"ACCEPTANCE:\s*PASS"
    r"|\bIS\s+DRIVEN\b|\bDRIVEN\s+AND\s+PASSING\b"
    r"|✅\s*\*{0,2}DONE\b|\bDONE\s+\d{4}-\d\d-\d\d\b"
    r"|\bexists\s+and\s+passes\b|\bPASS\s*[x×]\s*\d", re.I)

#: ‼ The exemption that lets this project's keep-old-text-visible style survive the gate.
SUPERSEDE_RE = re.compile(
    r"\(supersed[^)]*\)|Superseded text:"
    r"|⛔\s*\*{0,2}RETRACTED|\bRETRACTED\b|\bIS OBSOLETE\b|\bis retired\b"
    r"|\bOlder (?:text|framing)\b|\bOriginal item follows\b|SUPERSEDED BY|SUPERSEDED 20\d\d"
    # This project's rename-provenance idiom: "THE OLD NAMES SURVIVE ON PURPOSE IN 06/07/08" — a
    # unit explaining that historical names are kept deliberately is DESCRIBING history, not
    # asserting a runnable artifact. Without this, the naming-correction block in 04-HANDOFF
    # (which cites the retired `--driver ch21dive` precisely to say it is retired) false-fires.
    r"|OLD NAMES SURVIVE|SURVIVE[SD]? ON PURPOSE", re.I)

UNIT_RE = re.compile(r"^(?:#{1,6}\s|\s*>?\s*(?:[-*+]\s|\d+[a-z]?\.\s|\|)|\s*$)", re.M)
MAXDIST = 250


def _read(path: pathlib.Path) -> str:
    return FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), path.read_text(encoding="utf-8", errors="replace"))


def _line(text: str, i: int) -> int:
    return text[:i].count("\n") + 1


def _units(text: str) -> list[tuple[int, int]]:
    starts = sorted({m.start() for m in UNIT_RE.finditer(text)} | {0, len(text)})
    return [(starts[i], starts[i + 1]) for i in range(len(starts) - 1)]


# ---------------------------------------------------------------------------- ground truths
def real_gate_counts() -> tuple[int, int]:
    """(total, fast) from run_gates.py's GATES table, via AST — never by counting lines."""
    tree = ast.parse((REPO / "tools" / "story-dev" / "run_gates.py").read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "GATES":
            elts = node.value.elts
            fast = sum(1 for e in elts if ast.literal_eval(e)[1] is False)
            return len(elts), fast
    raise RuntimeError("GATES table not found in run_gates.py")


def real_driver_choices() -> set[str]:
    src = (REPO / "tools" / "story-dev" / "story_harness.py").read_text(encoding="utf-8-sig")
    m = re.search(r'add_argument\(\s*"--driver".*?choices=(\[[^\]]*\])', src, re.S)
    if not m:
        raise RuntimeError("--driver choices not found in story_harness.py")
    return set(ast.literal_eval(m.group(1)))


def real_drift() -> tuple[int, list[str]]:
    """MEASURED sandbox<->custom drift. ~0.06s for ~200 files — cheaper than trusting the docs."""
    differing = []
    for sub in ("modules", "plugins"):
        base = REPO / "sandbox-pokebot" / sub
        for p in base.rglob("*.py"):
            rel = p.relative_to(REPO / "sandbox-pokebot")
            q = REPO / "custom-pokebot" / rel
            if not q.exists():
                differing.append(f"MISSING {rel}")
            elif p.read_bytes() != q.read_bytes():
                differing.append(str(rel))
    return len(differing), differing


# ---------------------------------------------------------------------------- checks
def check_gate_counts(files: dict[str, str]) -> list[str]:
    total, fast = real_gate_counts()
    claims = re.compile(
        r"(\d{1,2})\s*/\s*(\d{1,2})\s+gates?\b"
        r"|\bsuite\s+is\s+now\s+(\d{1,2})\b"
        r"|\bALL\s+(\d{1,2})\s+GATES\b"
        r"|\b(\d{1,2})[- ]gate\s+suite\b"
        r"|STANDING\s+SUITE\s*[—-]+\s*(?:all\s+)?(\d{1,2})\s+gates?"
        r"|\ball\s+(\d{1,2})\s+gates?\s+PASS\b", re.I)
    fastc = re.compile(r"\bthe\s+(\d{1,2})\s+needing\s+no\s+ROM\b", re.I)
    gated = re.compile(r"(?:gated\s+by|GATED\s+as|new\s+gate)\s+`?([a-z0-9_]+\.py)`?", re.I)
    out = []
    for name, text in files.items():
        units = _units(text)
        def exempt(i):
            for a, b in units:
                if a <= i < b:
                    return bool(SUPERSEDE_RE.search(text[a:b]))
            return False
        for m in claims.finditer(text):
            nums = [int(g) for g in m.groups() if g]
            if any(n != total for n in nums) and not exempt(m.start()):
                out.append(f"{name}:{_line(text, m.start())} claims {'/'.join(map(str, nums))} "
                           f"gates; run_gates.py has {total}: {m.group(0)!r}")
        for m in fastc.finditer(text):
            if int(m.group(1)) != fast and not exempt(m.start()):
                out.append(f"{name}:{_line(text, m.start())} claims {m.group(1)} no-ROM gates; "
                           f"real fast count is {fast}")
        for m in gated.finditer(text):
            script = m.group(1)
            if script.startswith(("repro_", "probe_", "audit_", "lint_", "verify_", "preflight")):
                src = (REPO / "tools" / "story-dev" / "run_gates.py").read_text(encoding="utf-8-sig")
                if f'"{script}"' not in src and not exempt(m.start()):
                    out.append(f"{name}:{_line(text, m.start())} says {script} is a gate; it is "
                               f"not in run_gates.py's GATES table")
    return out


def check_drift(files: dict[str, str]) -> list[str]:
    measured, _ = real_drift()
    claims = re.compile(
        r"\bdrift\s+is\s+(?:now\s+|still\s+)?(?:exactly\s+)?(\d{1,2}|ZERO)\b"
        r"|\bEXPECT\s+EXACTLY\s+(\d{1,2})\b"
        r"|\bdrift\s+(?:unchanged\s+|measured\s+)?at\s+(?:exactly\s+)?(\d{1,2})\b"
        r"|\bDRIFT\s+IS\s+(ZERO)\b"
        r"|\b(\d{1,2})\s+drifted\s+files?\b", re.I)
    out = []
    for name, text in files.items():
        units = _units(text)
        for m in claims.finditer(text):
            raw = next(g for g in m.groups() if g)
            n = 0 if raw.upper() == "ZERO" else int(raw)
            if n != measured:
                a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
                if SUPERSEDE_RE.search(text[a:b]):
                    continue
                out.append(f"{name}:{_line(text, m.start())} claims drift={n}; MEASURED drift is "
                           f"{measured}: {m.group(0)!r}")
    return out


def check_queue_vs_headline(files: dict[str, str]) -> list[str]:
    """‼ THE HEADLINE CHECK — no driver both queued as to-do and reported passing."""
    out = []
    for name, text in files.items():
        units = _units(text)
        per: dict[str, dict[str, list[int]]] = {}
        for m in TOKEN_RE.finditer(text):
            tok = m.group(1)
            a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
            seg, off = text[a:b], m.start() - a
            if SUPERSEDE_RE.search(seg):
                continue
            def nearest(rx):
                best = None
                for mm in rx.finditer(seg):
                    d = 0 if mm.start() <= off <= mm.end() else min(
                        abs(mm.start() - off), abs(mm.end() - off))
                    best = d if best is None or d < best else best
                return best
            nb, nd = nearest(BUILD_RE), nearest(DONE_RE)
            kind = None
            if nb is not None and (nd is None or nb < nd) and nb <= MAXDIST:
                kind = "BUILD"
            elif nd is not None and nd <= MAXDIST:
                kind = "DONE"
            if kind:
                per.setdefault(tok, {}).setdefault(kind, []).append(_line(text, m.start()))
        for tok, d in sorted(per.items()):
            if "BUILD" in d and "DONE" in d:
                out.append(f"{name}: --driver {tok} queued as WORK-TO-DO at line(s) {d['BUILD']} "
                           f"but reported COMPLETE/PASSING at line(s) {d['DONE']} — one of them "
                           f"is stale and unmarked")
    return out


def check_ladder(files: dict[str, str]) -> list[str]:
    claims = re.compile(r"(\d{1,2})\s+of\s+(\d{1,2})\s+beats?\b", re.I)
    found: list[tuple[str, int, int, int]] = []
    for name, text in files.items():
        units = _units(text)
        for m in claims.finditer(text):
            a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
            if SUPERSEDE_RE.search(text[a:b]):
                continue
            found.append((name, _line(text, m.start()), int(m.group(1)), int(m.group(2))))
    if not found:
        return []
    out = []
    top = max(n for _, _, n, _ in found)
    denom = {d for _, _, _, d in found}
    if len(denom) > 1:
        out.append(f"ladder DENOMINATORS disagree: {sorted(denom)} across {len(found)} claims")
    for name, line, n, _ in found:
        if n != top:
            out.append(f"{name}:{line} says the ladder is {n} of 24; the newest claim elsewhere "
                       f"is {top} of 24 — the ladder only grows, so this is stale")
    return out


def check_artifacts(files: dict[str, str]) -> list[str]:
    choices = real_driver_choices()
    path_re = re.compile(
        r"`((?:ai-research-notes|tools/story-dev)/[A-Za-z0-9._/\-]+\.(?:md|py))`")
    out = []
    for name, text in files.items():
        units = _units(text)
        for m in TOKEN_RE.finditer(text):
            tok = m.group(1)
            if tok in choices:
                continue
            a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
            seg = text[a:b]
            if SUPERSEDE_RE.search(seg) or BUILD_RE.search(seg):
                continue    # marked historical, or honestly described as the thing to build
            out.append(f"{name}:{_line(text, m.start())} cites --driver {tok}, which is not in "
                       f"story_harness.py choices and is not marked as to-build/superseded")
        for m in path_re.finditer(text):
            rel = m.group(1)
            p = (DOCS / rel) if rel.startswith("ai-research-notes/") else (REPO / rel)
            if not p.exists():
                a, b = next(((a, b) for a, b in units if a <= m.start() < b), (0, len(text)))
                if SUPERSEDE_RE.search(text[a:b]):
                    continue
                out.append(f"{name}:{_line(text, m.start())} cites `{rel}`, which does not exist")
    return out


def warn_ki_headers() -> list[str]:
    """WARN ONLY — measured at ~4-in-5 false positives; a worklist for a human, never a gate."""
    text = _read(DOCS / "05-KNOWN-ISSUES.md")
    out = []
    headers = list(re.finditer(r"^##+\s+(KI-\d+[a-z]?)\b(.*)$", text, re.M))
    for i, h in enumerate(headers):
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[h.end():body_end]
        head = h.group(2)
        # Suppressed when the header ALREADY carries nuance (a "half FIXED", a scoped REFUTED, a
        # correction) — the warning exists to flag headers a skimmer would misread, and a header
        # that names its own caveat is doing exactly what the rule asks.
        if re.search(r"\bOPEN\b|\bARMED\b|\bBLOCKED\b", head) and \
           not re.search(r"NOT\s+armed|REFUTED|CORRECTED|watch|\bFIXED\b|SUPERSEDED", head, re.I):
            hit = re.search(r"^\s*[-*>]?\s*[✅⛔‼]*\s*\*{0,2}"
                            r"(?:REFUTED|IS SAFE|CANNOT FIRE|(?<!NOT )(?<!not )FIXED\b)",
                            body, re.M)
            if hit:
                out.append(f"05-KNOWN-ISSUES.md:{_line(text, h.start())} {h.group(1)} header says "
                           f"OPEN/ARMED/BLOCKED but its body opens a line with a closed-status "
                           f"word — check the header still carries the caveat")
    return out


def warn_handoff_date() -> list[str]:
    import subprocess
    text = (DOCS / "04-HANDOFF.md").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\*\*Last updated:\*\*\s*(\d{4}-\d\d-\d\d)", text)
    if not m:
        return ["04-HANDOFF.md has no 'Last updated:' line"]
    try:
        git_date = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", "PROJECT KNOWLEDGE/04-HANDOFF.md"],
            cwd=REPO, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:  # noqa: BLE001 - offline git is not a doc defect
        return []
    if git_date and git_date != m.group(1):
        return [f"04-HANDOFF.md 'Last updated: {m.group(1)}' but its newest commit is {git_date} "
                f"— the date line was not refreshed"]
    return []


# ---------------------------------------------------------------------------- self-test
def self_test() -> int:
    """FAULT-TEST the gate itself (CLAUDE.md rule 6): prove it fires, prove it stays quiet."""
    base = {"TEST.md": "## status\n\n* `--driver testx` ACCEPTANCE: PASS on the first drive.\n"}
    fails = 0

    def expect(label, findings, should_fire):
        nonlocal fails
        fired = bool(findings)
        ok = fired == should_fire
        print(f"  {'PASS' if ok else '‼ FAIL'}  {label}: "
              f"{'fired' if fired else 'quiet'} (expected {'fire' if should_fire else 'quiet'})")
        if not ok:
            fails += 1

    # A: the audit's exact bug — unmarked queue item for a passing driver.
    t = base["TEST.md"] + "\n> 1. **NEXT: BUILD `--driver testx`** — not yet written.\n"
    expect("A  unmarked build-vs-pass contradiction", check_queue_vs_headline({"T": t}), True)
    # B: the same text, marked superseded — the exemption must hold.
    t = base["TEST.md"] + "\n> 1. *(superseded)* **NEXT: BUILD `--driver testx`** — not yet written.\n"
    expect("B  superseded marker exempts", check_queue_vs_headline({"T": t}), False)
    # C: the same text inside a code fence — stripped before scanning.
    raw = base["TEST.md"] + "\n```\nNEXT: BUILD --driver testx (not yet written)\n```\n"
    stripped = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), raw)
    expect("C  code fence exempts", check_queue_vs_headline({"T": stripped}), False)
    # D: wrong counts must fire.
    total, fast = real_gate_counts()
    expect("D1 wrong gate count", check_gate_counts({"T": f"the {total + 1}-gate suite\n"}), True)
    expect("D2 right gate count", check_gate_counts({"T": f"the {total}-gate suite\n"}), False)
    measured, _ = real_drift()
    expect("D3 wrong drift", check_drift({"T": f"drift is exactly {measured + 1}\n"}), True)
    expect("D4 right drift", check_drift({"T": f"drift is exactly {measured}\n"}), False)
    expect("D5 stale ladder", check_ladder({"T": "ladder runs 19 of 24 beats\nnow 20 of 24 beats\n"}), True)
    # E: fabricated driver cited as runnable must fire; marked-to-build must not.
    expect("E1 phantom driver", check_artifacts({"T": "run `--driver nosuchthing` now\n"}), True)
    expect("E2 to-build driver exempt",
           check_artifacts({"T": "NEXT: BUILD `--driver nosuchthing` — does not exist yet\n"}), False)

    print(f"\nSELF-TEST {'PASS' if fails == 0 else 'FAIL'} ({fails} deviation(s))")
    return 0 if fails == 0 else 1


# ---------------------------------------------------------------------------- main
def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()

    files = {name: _read(DOCS / name) for name in CURRENT_STATE if (DOCS / name).exists()}
    failures: list[str] = []
    failures += check_gate_counts(files)
    failures += check_drift(files)
    failures += check_queue_vs_headline(files)
    failures += check_ladder(files)
    failures += check_artifacts(files)
    warnings = warn_ki_headers() + warn_handoff_date()

    print("=" * 92)
    print("DOC CONSISTENCY AUDIT — current-state files vs the code and each other")
    print("=" * 92)
    for w in warnings:
        print(f"  WARN  {w}")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print(f"  all consistency checks PASS across {len(files)} current-state files"
              f"{f'  ({len(warnings)} warning(s) above are human worklist, not failures)' if warnings else ''}")
    print("=" * 92)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
