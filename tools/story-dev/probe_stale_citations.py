"""PROBE — does a `symbol` + `file.py:NNN` citation in the docs point at that symbol's REAL line?

‼‼ WHY THIS EXISTS (2026-08-16). A Tier 1 review found that **six of the eight line citations
hand-typed into KI-81's `Guarded:` list were wrong**, and that KI-67's older citations had drifted
the same way. Line numbers are the least stable fact in a repo — every edit ABOVE them invalidates
them — and this project treats citations as load-bearing: a stale one sends the next agent to the
wrong code, which is how a day gets burned. The rule written that day was **"re-derive, never
re-type"**. This is the instrument that makes re-deriving cheap enough to actually do.

WHAT IT CHECKS, and the deliberate narrowness of it:
  It only looks at citations where the doc names a SYMBOL and a FILE:LINE **on the same line of
  prose** — e.g. ``  `talk_to_npc` (`higher_level_actions.py:718`)  ``. For those, it finds the
  symbol's real `def`/`class` line by AST and compares.
  ⚠ **It cannot check a bare `file.py:NNN`** with no symbol beside it: nothing in the document says
  what that line is supposed to CONTAIN, so there is nothing to verify against. Those are the
  majority, and they stay unverifiable by machine — which is itself worth knowing, and is why the
  KI-81 entry now states the SHAPE (*"guard first, latch-keyed"*) as its durable claim.
  ⚠ It reports a citation as STALE only when the symbol EXISTS in that file at a different line.
  A symbol it cannot find is reported separately as UNRESOLVED, never as stale — a doc may name a
  method on a class, a local, or a symbol that has since been renamed, and calling that "stale"
  would be a false positive.

⛔⛔ THIS IS A PROBE, NOT A GATE, AND THAT IS DELIBERATE — the same call `probe_abort_swallowing.py`
makes for the same reason. The docs are years of accumulated citations; a gate that is red on
arrival over pre-existing drift teaches everyone to ignore gates, and an ignored gate is strictly
worse than no gate. ⇒ **measure, record the baseline, fix, THEN promote it.**

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_stale_citations.py
      PYTHONUTF8=1 py -3.12 probe_stale_citations.py --all        # include UNRESOLVED + OK detail
      PYTHONUTF8=1 py -3.12 probe_stale_citations.py --self-test  # prove it fires AND stays quiet
Exit codes: 0 always (it is a PROBE — it measures, it does not fail the build).
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOCS = REPO / "PROJECT KNOWLEDGE"

#: Current-state docs only. The append-only logs (06/07/08) are HISTORY: a citation there was true
#: when written, and "correcting" it would rewrite the record. Reporting them would be pure noise.
SCAN_DOCS = ["01-VISION-AND-DESIGN.md", "02-ARCHITECTURE.md", "03-PUNCH-LIST.md",
             "04-HANDOFF.md", "05-KNOWN-ISSUES.md", "14-AGENT-PLAYBOOK.md"]

#: Where a cited `.py` basename might live. ⛔ The upstream mirror is never scanned — it is a
#: pristine subtree and the docs never cite into it (project directive).
SEARCH_ROOTS = [REPO / "sandbox-pokebot", REPO / "tools" / "story-dev"]

#: `symbol` ... `file.py:123`   — both backticked, same line of prose, symbol FIRST.
CITE_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`[^`\n]{0,120}?`([\w./-]+\.py):(\d{1,5})`")


def _index_files() -> dict[str, list[pathlib.Path]]:
    idx: dict[str, list[pathlib.Path]] = {}
    for root in SEARCH_ROOTS:
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            idx.setdefault(p.name, []).append(p)
    return idx


def symbol_lines(src: str) -> dict[str, list[tuple[int, int]]]:
    """Every `def`/`class` name -> its (first_line, last_line) SPAN.

    ‼ THE SPAN, NOT THE `def` LINE (fixed 2026-08-16, on this probe's second live run). Comparing
    against the `def` line alone flagged a perfectly good citation: a KI table cites the line of a
    specific STATEMENT (`party_in_menu = get_party()`) inside a function whose `def` is 130 lines
    earlier. That is a BODY citation, the most useful kind, and calling it stale is a false
    positive — the failure mode that gets an instrument ignored. ⇒ a citation ANYWHERE inside the
    symbol's span is honest; only one OUTSIDE every span is stale.
    """
    out: dict[str, list[tuple[int, int]]] = {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.setdefault(node.name, []).append((node.lineno, node.end_lineno or node.lineno))
    return out


def _paragraphs(text: str):
    """Yield (start_lineno, joined_text) per blank-line-separated paragraph.

    ‼ WHY NOT LINE-BY-LINE (fixed 2026-08-16, the day this probe was written). Its first live run
    reported 0 stale after a fix round — and a hand check immediately found one it had MISSED,
    because the citation was SOFT-WRAPPED: the symbol ended one line and the `file:line` began the
    next. Docs here wrap at ~100 chars, so wrapped citations are common, not exotic.
    ⛔ Joining the WHOLE file would be wrong the other way: a symbol at the end of one bullet and an
    unrelated `file:line` at the start of the next would match as a pair and manufacture a finding.
    A paragraph is the honest unit — it is one thought, and the regex still caps the gap at 120
    chars. *A probe that reports 0 because it cannot SEE is worse than one that reports honestly.*
    """
    start = 1
    buf: list[str] = []
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip():
            if not buf:
                start = i
            buf.append(line.strip())
        elif buf:
            yield start, " ".join(buf)
            buf = []
    if buf:
        yield start, " ".join(buf)


def check_text(text: str, resolve) -> tuple[list[str], list[str], int]:
    """(stale, unresolved, ok_count). `resolve(basename) -> source str | None`."""
    stale: list[str] = []
    unresolved: list[str] = []
    ok = 0
    for lineno, line in _paragraphs(text):
        for m in CITE_RE.finditer(line):
            sym, base, num = m.group(1), m.group(2).split("/")[-1], int(m.group(3))
            src = resolve(base)
            if src is None:
                unresolved.append(f"line {lineno}: `{base}` not found on disk (cited for `{sym}`)")
                continue
            defs = symbol_lines(src).get(sym)
            if not defs:
                # ⚠ NOT stale — the doc may be naming a method, a local, a module attribute, or a
                # since-renamed symbol. Reporting it as stale would be a false positive, and a
                # probe with false positives gets ignored exactly like a noisy gate.
                unresolved.append(f"line {lineno}: `{sym}` is not a def/class in `{base}` "
                                  f"(cited as :{num}) — unverifiable, not necessarily wrong")
                continue
            if any(a <= num <= b for a, b in defs):
                ok += 1
            else:
                spans = " or ".join(f"{a}-{b}" for a, b in defs)
                stale.append(f"line {lineno}: `{sym}` cited as `{base}:{num}` but that line is "
                             f"OUTSIDE it — its real span is {spans}")
    return stale, unresolved, ok


_GOOD = "the helper `alpha` lives at `t.py:2` today\n"
_BAD = "the helper `alpha` lives at `t.py:99` today\n"
_UNRESOLVED = "the local `zeta` lives at `t.py:2` today\n"
_NO_SYMBOL = "see `t.py:99` for the whole story\n"
_BODY = "the assignment `alpha` makes at `t.py:3` is the one that matters\n"
_SRC = "x = 1\ndef alpha():\n    y = 2\n    return y\n"


def self_test() -> int:
    """‼ FAULT-TEST (CLAUDE.md rule 6): prove it FIRES on a stale citation, and prove it stays
    QUIET on a correct one, on an unverifiable symbol, and on a bare file:line with no symbol —
    the three shapes that, if flagged, would make this probe noise and therefore ignorable."""
    resolve = lambda base: _SRC if base == "t.py" else None  # noqa: E731
    cases = [
        ("correct citation -> quiet", _GOOD, 0, 0),
        ("STALE citation -> FIRES", _BAD, 1, 0),
        ("symbol not a def -> UNRESOLVED, never 'stale'", _UNRESOLVED, 0, 1),
        ("bare file:line with no symbol -> ignored entirely", _NO_SYMBOL, 0, 0),
        # ‼ The blind spot that made this probe report a false 0 on its first run.
        ("SOFT-WRAPPED stale citation -> still FIRES", "the helper `alpha` lives at\n`t.py:99` today\n", 1, 0),
        # ⛔ ...and the opposite error the fix could have introduced: two unrelated paragraphs
        # must NOT be joined into a phantom pair.
        ("symbol and file:line in DIFFERENT paragraphs -> quiet", "`alpha` is the entry point.\n\nSee `t.py:99`.\n", 0, 0),
        # ‼ A BODY citation — a statement INSIDE the function — is the most USEFUL kind there is.
        # Flagging it was this probe's second false positive, caught on its second live run.
        ("citation INSIDE the symbol's body -> quiet, not stale", _BODY, 0, 0),
    ]
    bad = 0
    print("=" * 92)
    print("SELF-TEST — fires on a stale citation, quiet on correct/unverifiable/bare")
    print("=" * 92)
    for label, text, want_stale, want_unres in cases:
        stale, unres, _ = check_text(text, resolve)
        ok = len(stale) == want_stale and len(unres) == want_unres
        bad += 0 if ok else 1
        print(f"  {'PASS' if ok else '‼ FAIL'}  {label}  "
              f"(stale={len(stale)}/{want_stale}, unresolved={len(unres)}/{want_unres})")
    print("=" * 92)
    print(f"SELF-TEST {'PASS' if not bad else 'FAIL'} ({bad} deviation(s))")
    print("=" * 92)
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    show_all = "--all" in sys.argv
    idx = _index_files()
    cache: dict[str, str | None] = {}

    def resolve(base: str) -> str | None:
        if base not in cache:
            hits = idx.get(base, [])
            # ⛔ An ambiguous basename (same name in two trees) is NOT resolved — guessing which
            # one the doc meant is how a "verification" invents its own wrong answer.
            cache[base] = hits[0].read_text(encoding="utf-8", errors="replace") if len(hits) == 1 else None
        return cache[base]

    print("=" * 92)
    print("PROBE — `symbol` + `file.py:NNN` citations in CURRENT-STATE docs, re-derived from source")
    print("=" * 92)
    tot_stale = tot_unres = tot_ok = 0
    for name in SCAN_DOCS:
        p = DOCS / name
        if not p.is_file():
            continue
        stale, unres, ok = check_text(p.read_text(encoding="utf-8", errors="replace"), resolve)
        tot_stale += len(stale)
        tot_unres += len(unres)
        tot_ok += ok
        if stale or (show_all and unres):
            print(f"\n  {name}")
            for s in stale:
                print(f"    ‼ STALE      {s}")
            if show_all:
                for u in unres:
                    print(f"      unverified {u}")
    print("-" * 92)
    print(f"  citations checked : {tot_ok + tot_stale}   (verified OK: {tot_ok})")
    print(f"  ‼ STALE           : {tot_stale}")
    print(f"  unverifiable      : {tot_unres}   (symbol is not a def/class, or file is ambiguous)")
    print("  ‼ Only `symbol` + `file:line` pairs on ONE line of prose are checkable. A BARE")
    print("    `file.py:NNN` says nothing about what that line should contain, so nothing can")
    print("    verify it — which is why the durable claim in a doc should be the SHAPE, not the line.")
    print("  ⛔ NOT a gate: the docs carry years of citations and a gate red on arrival gets ignored.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    sys.exit(main())
