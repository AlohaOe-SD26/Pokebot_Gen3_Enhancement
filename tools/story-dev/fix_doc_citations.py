# -*- coding: utf-8 -*-
"""Repair the citation drift that `audit_doc_citations.py` reports — mechanically, from its own output.

‼‼ WHY THIS EXISTS. Citation drift fired **five times in two days** (2026-09-13 ×4, 2026-09-14 ×1),
every time for the same reason: an edit to `story_mode.py` shifts line numbers, and documented
`file.py:LINE` citations that named a function's `def` line now land somewhere else. The fix was
always identical and always hand-typed — which is toil, and hand-typing a line number is how a
WRONG number gets introduced while "fixing" a stale one.

⛔ THIS TOOL IS A REPAIRER, NOT A GATE. `audit_doc_citations.py` stays the authority and stays in
`run_gates.py`; this only applies the corrections that gate has ALREADY computed. It cannot invent a
target: every new line number comes from the gate's own "spans `file.py:A-B`" clause.

⛔ SAFETY PROPERTIES, all enforced below rather than promised:
  * It edits ONLY the exact `doc:line` the gate names, and ONLY the exact `path:oldline` token.
  * It asserts the token is present EXACTLY ONCE on that line before touching it. A line carrying
    the same citation twice is left alone and REPORTED — ambiguity is not resolved silently.
  * It never changes a file's LINE COUNT (the R3 budgets are at their limit) and preserves the
    file's own line endings (this tree mixes LF and CRLF, which has bitten a repair script before).
  * It re-runs the audit afterwards and FAILS if anything still drifts, so a partial repair can
    never be mistaken for a clean one.
  * `--dry-run` prints the plan and writes nothing.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 fix_doc_citations.py [--dry-run]
"""
import io
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DOCS = HERE.parents[1] / "PROJECT KNOWLEDGE"
AUDIT = HERE / "audit_doc_citations.py"

# "  FAIL  03-PUNCH-LIST.md:1757 cites `story_mode.py:1785` for `_should_catch`, but
#  `_should_catch` spans `story_mode.py:1819-1918` — the citation lands OUTSIDE it"
FAIL = re.compile(
    r"FAIL\s+(?P<doc>[\w.\-]+\.md):(?P<line>\d+)\s+cites\s+`(?P<path>[^`]+):(?P<old>\d+)`"
    r".*?spans\s+`(?P=path):(?P<start>\d+)-(?P<end>\d+)`"
)


def run_audit() -> "tuple[int, str]":
    proc = subprocess.run([sys.executable, str(AUDIT)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(HERE))
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def repoint(line: str, path: str, old: str, start: str) -> "tuple[str, int]":
    """Re-point ONE `path:old` or `path:old-END` citation on `line` to `start`, shifting a RANGE's END by the
    same offset. Returns `(new_line, matches)`; the line is changed only when there is exactly one match.
    ⛔ 2026-09-26: this tool used to replace the bare `path:old` token, so `victory_road.py:2014-2026` became
    `2017-2026` — the exact defect `08-MISTAKES.md` names ("A RE-POINT SHIFTS BOTH ENDS BY THE SAME OFFSET"),
    committed by the repairer itself. `probe_citation_ranges.py` only catches an INVERTED range, not a stale end."""
    pat = re.compile(re.escape(f"{path}:{old}") + r"(?:-(\d+))?(?!\d)")
    matches = pat.findall(line)
    if len(matches) != 1:
        return line, len(matches)
    delta = int(start) - int(old)

    def _sub(m):
        end = m.group(1)
        return f"{path}:{start}" + (f"-{int(end) + delta}" if end else "")
    return pat.sub(_sub, line, count=1), 1


def _selftest() -> int:
    cases = [
        ("see `victory_road.py:2014-2026` here", "victory_road.py", "2014", "2017", "see `victory_road.py:2017-2029` here"),
        ("see `story_mode.py:2081`,", "story_mode.py", "2081", "2093", "see `story_mode.py:2093`,"),
        ("`a.py:12` and `a.py:120`", "a.py", "12", "15", "`a.py:15` and `a.py:120`"),
    ]
    bad = 0
    for line, path, old, start, want in cases:
        got, n = repoint(line, path, old, start)
        ok = got == want and n == 1
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {line!r} -> {got!r}")
    got, n = repoint("`a.py:12` twice `a.py:12`", "a.py", "12", "15")
    ok = n == 2 and got == "`a.py:12` twice `a.py:12`"
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} two identical citations are left alone (n={n})")
    print("SELFTEST PASS" if not bad else f"SELFTEST FAIL ({bad})")
    return 1 if bad else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    dry = "--dry-run" in sys.argv
    code, out = run_audit()
    if code == 0:
        print("audit_doc_citations.py already exits 0 — nothing to repair.")
        return 0

    fixes = [m.groupdict() for m in FAIL.finditer(out)]
    if not fixes:
        print("‼ The audit FAILED but no repairable 'cites/spans' lines were parsed.")
        print("⛔ Do NOT assume there is nothing to do — read its output and fix by hand:")
        print(out[-1500:])
        return 1

    print(f"{len(fixes)} drifted citation(s) reported by the gate:")
    by_doc: dict = {}
    for f in fixes:
        by_doc.setdefault(f["doc"], []).append(f)

    changed = 0
    for doc, items in sorted(by_doc.items()):
        path = DOCS / doc
        raw = io.open(path, "rb").read()
        eol = "\r\n" if raw.count(b"\r\n") > raw.count(b"\n") - raw.count(b"\r\n") else "\n"
        lines = raw.decode("utf-8").split(eol)
        before = len(lines)
        touched = False
        for f in items:
            i = int(f["line"]) - 1
            old_tok = f"{f['path']}:{f['old']}"
            new_tok = f"{f['path']}:{f['start']}"
            if not (0 <= i < len(lines)):
                print(f"  SKIP  {doc}:{f['line']} — line out of range")
                continue
            new_line, n = repoint(lines[i], f["path"], f["old"], f["start"])
            if n != 1:
                # ⛔ Ambiguity is REPORTED, never guessed at. Two identical citations on one line
                # cannot be told apart, and picking one would be a coin flip recorded as a repair.
                print(f"  SKIP  {doc}:{f['line']} — {old_tok!r} appears {n}× (need exactly 1)")
                continue
            lines[i] = new_line
            print(f"  FIX   {doc}:{f['line']}  {old_tok} -> {new_tok}  "
                  f"({f['path'].rsplit('/', 1)[-1]} def line, span {f['start']}-{f['end']})")
            touched = True
            changed += 1
        if touched and not dry:
            assert len(lines) == before, f"{doc}: line count changed {before} -> {len(lines)}"
            io.open(path, "wb").write(eol.join(lines).encode("utf-8"))

    if dry:
        print(f"\n--dry-run: {changed} change(s) planned, nothing written.")
        return 0
    if not changed:
        print("\n‼ Nothing was changed — every reported drift was ambiguous. Fix by hand.")
        return 1

    code2, out2 = run_audit()
    print()
    if code2 == 0:
        print(f"✅ REPAIRED {changed} citation(s); audit_doc_citations.py now exits 0.")
        return 0
    # ⛔ A partial repair must never read as a clean one.
    print(f"⛔ {changed} citation(s) rewritten but the audit STILL FAILS — repair is INCOMPLETE:")
    print("\n".join(l for l in out2.splitlines() if "FAIL" in l)[-1500:])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
