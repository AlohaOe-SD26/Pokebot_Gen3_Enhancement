# -*- coding: utf-8 -*-
"""⛔ GATE: A RANGE CITATION MUST NOT BE INVERTED. (plus an advisory straddle census)

THE GAP THIS CLOSES, AND HOW IT WAS FOUND. `audit_doc_citations.py` pairs an identifier with a
`file.py:LINE` and checks that LINE falls inside the identifier's span. ⛔ **Its `FILEREF` captures
a single `(\\d+)`** — so for a RANGE citation (`file.py:100-220`) it reads the START and is
structurally blind to the END.

‼ THAT BLINDNESS WAS NOT THEORETICAL. On 2026-09-19 a 37-line insertion into `early_game.py` staled
16 citations. They were bulk re-pointed by shifting the START — and every RANGE citation kept its
OLD end, producing inverted ranges such as `early_game.py:4614-4605` and `early_game.py:2106-2103`.
The full 66-gate suite went green over all of them, and the commit message claimed the gate had
"caught every one". It had not; it could not. A Tier 1 reviewer found them by reading.
⇒ **this gate exists so that reading is not required for the mechanical half.**

WHAT FAILS THE BUILD — one check, and it is a defect BY CONSTRUCTION:
  **INVERTED**: `start > end`. Nothing legitimate looks like this, so there is nothing to judge and
  nothing to misjudge. Zero false positives is the whole design.

⚠ WHAT IS ADVISORY ONLY, AND WHY. A range whose START sits inside some definition while its END
falls outside every definition containing that start is *suspicious* — it is the shape a
half-applied re-point leaves. But it is ALSO the shape of a legitimately imprecise citation that
names a passage spanning a boundary, and this tree contains many such from before the gate existed.
⛔ Failing on them would make this a noisy gate, and this project's rule is explicit that a gate
with false positives teaches the reader to bypass it — strictly worse than no gate. ⇒ they are
COUNTED and listed, never fatal.

⚠ AND WHAT NEITHER HALF CAN SEE: a well-formed range, wholly inside the right function, whose END
no longer marks the passage the prose MEANT. That is semantic; `08-MISTAKES.md` 2026-09-19 carries
the human rule for it ("read each one; if it is not the def, cite the thing it means").

‼ AND A TRAP THIS GATE WALKED INTO ON ITS FIRST REGISTRATION: **it scans the documents that
describe it.** The flag-registry row explaining its fault arm quoted a synthetic inverted citation
literally, and the gate duly reported its own documentation as a defect. That is a fair catch, not
a bug — but it means any prose ABOUT a malformed citation must spell the numbers out rather than
write a parseable range. The same applies to `08-MISTAKES.md`, which is why the append-only files
are exempt outright.

FAULT ARM: `POKEBOT_CITERANGE_FAULT=1` injects a synthetic inverted citation; the gate must FAIL.
"""
import ast
import os
import pathlib as _pl
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

REPO = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
DOCS = REPO / "PROJECT KNOWLEDGE"

#: APPEND-ONLY HISTORY IS EXEMPT, AND THE REASON IS NOT CONVENIENCE.
#: `06`/`07`/`08` and the handoff archive RECORD what was written, including what was written
#: wrongly. `08-MISTAKES.md` literally quotes `story_mode.py:2002-1442` as the example of a
#: malformed range -- that quote is the evidence, and "fixing" it would falsify the record to make
#: a gate green. ⇒ a gate over documentation MUST exempt the files whose job is to preserve the
#: past, or it turns a green build into an argument for rewriting history.
#: What remains in scope is exactly where a citation is a LIVE claim a reader would act on:
#: the current-state files (01-05) and the research notes.
EXEMPT_PREFIXES = ("06-", "07-", "08-", "28-")
SEARCH_ROOTS = [REPO / "sandbox-pokebot", REPO / "tools" / "story-dev"]

#: `file.py:START-END`. Looser than the sibling gate's pairing regex on purpose: the fatal check
#: needs no identifier, because it is about the range itself.
RANGE = re.compile(r"([\w-]+\.py):(\d+)-(\d+)")

print("=" * 100)
print("GATE: range citations must not be inverted   (+ advisory straddle census)")
print("=" * 100)

_SPAN_CACHE: dict = {}


def _spans(path: _pl.Path):
    """[(start, end)] for every def/class, from `ast` — a class's span INCLUDES its methods.

    ‼ NOT a regex over `def` lines. That version reported a CLASS as straddling its own methods
    (`story_mode.py:1038-1096`, SwapTrainBattleStrategy, because a nested `def` sits at 1060) —
    a false positive on the first run, which is precisely why the straddle check is advisory.
    """
    key = str(path)
    if key in _SPAN_CACHE:
        return _SPAN_CACHE[key]
    out = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                end = getattr(node, "end_lineno", None)
                if end:
                    out.append((node.lineno, end))
    except Exception:  # noqa: BLE001 - an unparseable source is not this gate's business
        out = []
    _SPAN_CACHE[key] = out
    return out


_index: dict = {}
for root in SEARCH_ROOTS:
    for p in root.rglob("*.py"):
        _index.setdefault(p.name, []).append(p)

inverted = []
straddles = []
scanned = 0
for doc in sorted(DOCS.rglob("*.md")):
    if doc.name.startswith(EXEMPT_PREFIXES):
        continue
    scanned += 1
    for ln, line in enumerate(doc.read_text(encoding="utf-8").split("\n"), 1):
        for fname, a, b in RANGE.findall(line):
            start, end = int(a), int(b)
            if start > end:
                inverted.append((doc, ln, f"`{fname}:{start}-{end}`  (start > end)"))
                continue
            for src in _index.get(fname, []):
                containing = [x for x in _spans(src) if x[0] <= start <= x[1]]
                if containing and not any(x[0] <= end <= x[1] for x in containing):
                    widest = max(containing, key=lambda x: x[1] - x[0])
                    straddles.append((doc, ln, f"`{fname}:{start}-{end}` "
                                               f"(widest def containing start: {widest[0]}-{widest[1]})"))
                break

if os.environ.get("POKEBOT_CITERANGE_FAULT", "").strip() in ("1", "true", "yes"):
    inverted.append((DOCS / "<synthetic>.md", 1,
                     "`early_game.py:900-100`  [FAULT ARM — injected, not real]"))
    print("  ⚠ FAULT ARM ACTIVE: synthetic inverted citation injected")

print(f"  scanned {scanned} document(s) against {len(_index)} source filename(s)")
print()

if straddles:
    print(f"  ℹ ADVISORY — {len(straddles)} range(s) whose end leaves every definition containing")
    print("    their start. Suspicious, not fatal: an imprecise citation looks the same as a")
    print("    half-applied re-point. Triage when touching the surrounding prose.")
    for doc, ln, what in straddles[:8]:
        print(f"      · {doc.name}:{ln}  {what}")
    if len(straddles) > 8:
        print(f"      · … and {len(straddles) - 8} more")
    print()

if inverted:
    print("⛔ FAIL — INVERTED range citation(s); these are defects by construction:")
    for doc, ln, what in inverted:
        try:
            rel = doc.relative_to(REPO)
        except ValueError:
            rel = doc
        print(f"  • {rel}:{ln}  {what}")
    print()
    print("  ‼ THE USUAL CAUSE: a bulk re-point after lines were inserted into a source file, which")
    print("    shifted each citation's START and left its END behind. Recompute the END too — or")
    print("    better, re-point to the exact passage the prose names.")
    print("=" * 100)
    raise SystemExit(1)

print(f"  ✅ PASS — no inverted range citations ({len(straddles)} advisory straddle(s) listed above).")
print("=" * 100)
