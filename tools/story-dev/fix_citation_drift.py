# -*- coding: utf-8 -*-
"""RE-POINT doc citations that a code edit staled — BY SYMBOL LOOKUP, never by arithmetic.

WHY THIS IS A TOOL. `audit_doc_citations.py` (a gate) tells you WHICH citations broke; fixing them
by hand is a recurring tax that this project has already paid badly once. On 2026-09-19 a 37-line
insertion staled 16 citations, they were bulk re-pointed by shifting every START by a constant, and
every RANGE kept its old END — producing NINE INVERTED RANGES that the whole 66-gate suite went
green over. That is what motivated gate #67. On 2026-09-23 the same tax came due THREE more times in
one session, which is the evidence that prose ("read each one") is not enough.

TWO DEFENCES, BOTH STRUCTURAL RATHER THAN CAREFUL:
  1. THE NEW START IS LOOKED UP FROM THE SOURCE (`ast`), NEVER COMPUTED. A single constant offset is
     wrong whenever more than one insertion point moved: on 2026-09-23 one edit shifted three
     regions of `early_game.py` by +94, +105 and +108, so any constant would have been wrong for
     two of them.
  2. A RANGE KEEPS ITS WIDTH. `file.py:100-160` becomes `file.py:<newdef>-<newdef+60>`. An inverted
     range is therefore impossible BY CONSTRUCTION, not merely checked for afterwards.

⛔⛔ WHAT THIS TOOL DELIBERATELY WILL NOT DO, AND WHY YOU STILL HAVE TO READ.
It only touches a citation that is ALREADY BROKEN (outside its symbol's current span), and it always
re-points to the symbol's DEFINITION line. A citation that means something INSIDE the function — a
specific guard, a specific branch — would be silently destroyed by that.
‼ MEASURED CASE: `early_game.py:2139` was cited for `train_team` but meant its **500-round guard**,
and it appears beside the words "KI-28's 19.9M-frame shape" — the guard IS the point of the
sentence. Snapping it to the `def` line would have quietly deleted the reference the prose depends
on. Such citations must be fixed by hand.
⇒ THE WORKFLOW, AND THE ORDER IS LOAD-BEARING (learned the hard way, 2026-09-23):
  1. FIRST repair every known NON-DEF citation BY ITS EXACT OLD VALUE. This tool's whole contract
     is "snap to the def", so anything it is allowed to see must already mean the def.
  2. THEN run this tool.
  3. THEN read the list it prints, and fix by hand any entry whose prose meant a particular LINE
     rather than the symbol.
⛔ DOING 1 AND 2 THE OTHER WAY ROUND CROSSES THEM. Measured: the tool moved a deliberately-placed
GUARD citation (`train_team`'s 500-round line) onto the `def`, and a follow-up repair written as a
NUMERIC RANGE regex then swept that fresh `def` line back onto the guard -- producing a span that
began inside the function it delimited. Both wrong answers were well-formed, and
`audit_doc_citations.py` was GREEN over them, because a citation inside the symbol's span is all it
checks.
⛔⛔ AND NEVER MATCH A CITATION BY A NUMERIC RANGE. `:2273` is an exact string; a pattern spanning
twenty line numbers cannot know which of them it is about, and the one it catches by accident is
the one this tool just wrote. That is the 2026-09-19 bulk-shift antipattern in miniature.

SCOPE: the CURRENT-STATE docs only (`01`-`05`). ⛔ `06`/`07`/`08`/`28` are APPEND-ONLY history and
are never touched — a stale citation there is part of the record, and "fixing" it would falsify the
past to make a gate green.

    PYTHONUTF8=1 py -3.12 fix_citation_drift.py            # apply
    PYTHONUTF8=1 py -3.12 fix_citation_drift.py --dry-run  # show what would change, touch nothing
"""
import ast
import io
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
DRY = "--dry-run" in sys.argv

#: Mirrors `audit_doc_citations.py`'s own pairing regex. ‼ It must: this tool exists to fix exactly
#: what that gate reports, and a tool that fixes a DIFFERENT set than the gate checks would leave
#: the gate red while claiming success.
IDENT = r"[A-Za-z_]\w*"
FILEREF = r"[\w/.\\-]*?([\w-]+\.py):(\d+)"
CITE = re.compile(
    r"`(" + IDENT + r")`[^`\n]{0,48}?`" + FILEREF
    + r"|`" + FILEREF + r"`[^`\n]{0,12}?`(" + IDENT + r")`"
)

SOURCE_ROOTS = [REPO / "sandbox-pokebot" / "modules", REPO / "sandbox-pokebot" / "plugins",
                REPO / "tools" / "story-dev"]
DOCS = ["01-VISION-AND-DESIGN.md", "02-ARCHITECTURE.md", "03-PUNCH-LIST.md",
        "04-HANDOFF.md", "05-KNOWN-ISSUES.md"]

spans: dict = {}
for root in SOURCE_ROOTS:
    if not root.is_dir():
        continue
    for src in root.rglob("*.py"):
        if "__pycache__" in str(src):
            continue
        try:
            tree = ast.parse(src.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - an unparseable source is not this tool's business
            continue
        table = spans.setdefault(src.name, {})
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # ⛔ FIRST definition wins. A name defined in two files (or twice in one) is
                # ambiguous, and guessing which one the prose meant is exactly the kind of silent
                # decision this tool must not make.
                table.setdefault(node.name, (node.lineno, node.end_lineno))

BAR = "=" * 100
print(BAR)
print(f"RE-POINT STALE CITATIONS BY SYMBOL LOOKUP{'   [DRY RUN]' if DRY else ''}")
print(BAR)

fixed = 0
for name in DOCS:
    doc = REPO / "PROJECT KNOWLEDGE" / name
    if not doc.exists():
        continue
    lines = doc.read_text(encoding="utf-8").split("\n")
    changed = False
    for i, line in enumerate(lines):
        for m in CITE.finditer(line):
            ident = m.group(1) or m.group(6)
            fname = m.group(2) or m.group(4)
            start = int(m.group(3) or m.group(5))
            if ident not in spans.get(fname, {}):
                continue
            lo, hi = spans[fname][ident]
            if lo <= start <= hi:
                continue  # still correct — leave it alone
            rng = re.search(re.escape(f"{fname}:{start}") + r"-(\d+)", line)
            if rng:
                width = int(rng.group(1)) - start
                if width < 0:
                    print(f"  ⚠ SKIPPED {name}:{i + 1}  `{fname}:{start}-{rng.group(1)}` "
                          f"is ALREADY INVERTED — fix by hand (gate #67 will refuse it)")
                    continue
                old, new = f"{fname}:{start}-{rng.group(1)}", f"{fname}:{lo}-{lo + width}"
            else:
                old, new = f"{fname}:{start}", f"{fname}:{lo}"
            lines[i] = lines[i].replace(old, new)
            print(f"  {name}:{i + 1}  {ident:<32} {old} -> {new}")
            fixed += 1
            changed = True
    if changed and not DRY:
        doc.write_text("\n".join(lines), encoding="utf-8", newline="\n")

print()
print(f"  {'would re-point' if DRY else 're-pointed'} {fixed} citation(s) by symbol lookup")
if fixed:
    print()
    print("  ‼ NOW READ THE LIST ABOVE. Every entry was snapped to its symbol's `def` line. If any")
    print("    of those citations meant a SPECIFIC LINE INSIDE the function — a guard, a branch, a")
    print("    constant — this tool has just destroyed that meaning and you must restore it by hand.")
    print("    (The known case: a citation for `train_team` that actually meant its 500-round guard.)")
print(BAR)
