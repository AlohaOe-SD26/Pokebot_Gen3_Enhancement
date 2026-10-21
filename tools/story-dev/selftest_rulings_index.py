"""GATE: the rulings index (`build_rulings_index.py`) and the lookup's ruling side (`tools/decomp_lookup.py ask`),
spec S3-2 tests N0-N6. Each arm has a FAULT (the guard must fire) and a CONTROL (it must stay quiet). No ROM, no
decomp clone (every `ask` here runs with `--no-decomp`); about 5 s.

  N0  the REAL tree: `--check` passes (generated files fresh, overlay resolves, every do-not candidate classified,
      every repeated USER RULING number classified). Red after every 06 append until someone runs the one command it
      prints: that is the design (the index must never silently lag 06).
  N1  ‼ A DETERMINISM CHECK, NOT A RECALL CONTROL: the section count equals the number of `^## ` lines, and the do-not
      candidate count equals an independent re-implementation of the SAME phrase regex. One regex on both sides can
      only show the parser is deterministic; N6 is the control that retrieval works. Also: ids unique, and every line
      a plain line-grep of the spec's three phrases finds is a candidate (so a drop is visible).
  N2  FAULT: a synthetic 06 with `USER RULING 7` on two dates and no overlay fails, naming BOTH sections.
      CONTROL: with `ruling_key` on the later one it passes; with `application_of` it passes.
  N3  FAULT: a synthetic "DO NOT RE-RAISE X" with no overlay fails "unclassified do-not". CONTROL: classified
      `marker` passes and `ask` prints the DO-NOT banner FIRST; classified `mention` passes and `ask` prints NO flag.
  N4  FAULT: an overlay id for a deleted section fails "unresolved"; a `superseded_by` naming nothing fails
      "dangling". CONTROL: the same overlay with live ids passes.
  N5  FAULT (stale): a copy of the real 06 with one appended section fails `--check` and prints the regeneration
      command. CONTROL: after regenerating it passes, and the append created no overlay obligation.
  N6  golden re-asks on the REAL 06 + overlay: six known questions must return their section id in the top 3 (6 of
      6). FAULT: with the overlay EMPTIED, no query that printed the DO-NOT banner first still does (the flag is what
      surfaces it). CONTROL: a never-ruled topic exits 3, "NO PRIOR RULING OR FACT FOUND".

Run:  py -3.12 tools/story-dev/selftest_rulings_index.py [--tools-dir DIR]   (DIR: a copy of tools/, for mutants)
Exit: 0 every arm passed; 1 any arm failed.
"""
from __future__ import annotations

import argparse
import bisect
import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOCS = REPO / "PROJECT KNOWLEDGE"
REAL_06 = DOCS / "06-DECISIONS-LOG.md"
REAL_OVERLAY = DOCS / "rulings-overlay.json"
REAL_JSON = DOCS / "RULINGS.generated.json"
REAL_MD = DOCS / "RULINGS.md"

#: N6: question -> the section id it must return in the top 3 (ids, never line numbers: lines move with every append).
GOLDEN = [
    ("tracked commercial ROM", "2026-08-23-43fd61", "06:3119 the RE-AFFIRMED tracked-ROM ruling"),
    ("stash drop", "2026-08-13-9d3b6c", "06:2007 stash@{0} kept permanently"),
    ("Shoal Cave hunting ground", "2026-08-13-fee98f", "06:1749 Shoal Cave not adopted"),
    ("train the laggard to the boss's level", "2026-09-12-125f6e", "06:5133 the laggard do-not"),
    ("the value question 32x310", "2026-09-12-f83fd9", "06:5173 the POKEBOT_MAINTAIN value do-not"),
    ("B1F", "2026-09-18-7c5632", "06:6225 the B1F do-not-reopen"),
]
NEVER_RULED = "quantum fishing tournaments"
BANNER = "⛔ DO-NOT-REOPEN"

RESULTS: list[tuple[str, bool, str]] = []


def arm(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  :: {detail}" if detail else ""))


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def overlay_file(path: Path, sections: dict) -> Path:
    return write(path, json.dumps({"sections": sections}, ensure_ascii=False, indent=1))


def run_ask(tools: Path, words: str, decisions: Path, overlay: Path, ledger: Path) -> tuple[int, str]:
    res = subprocess.run([sys.executable, str(tools / "decomp_lookup.py"), "ask", words, "--no-decomp",
                          "--decisions", str(decisions), "--overlay", str(overlay), "--ledger", str(ledger)],
                         capture_output=True, timeout=120)
    return res.returncode, res.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tools-dir", type=Path, default=HERE.parent)
    args = ap.parse_args()
    tools = args.tools_dir.resolve()
    sys.path.insert(0, str(tools / "story-dev"))
    sys.path.insert(0, str(tools))
    import build_rulings_index as bri  # noqa: E402
    t0 = time.monotonic()
    tmp = Path(tempfile.mkdtemp(prefix="s32-rulings-"))

    def regen(decisions: Path, ov: Path, oj: Path, om: Path) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            bri.main(["--decisions", str(decisions), "--overlay", str(ov), "--out-json", str(oj), "--out-md", str(om)])

    no_ledger = tmp / "no-ledger.jsonl"
    try:
        # ------------------------------------------------------------------------------------------------ N0
        problems, infos = bri.check(REAL_06, REAL_OVERLAY, REAL_JSON, REAL_MD)
        arm("N0 real tree --check passes", not problems,
            f"{len(problems)} problem(s){': ' + problems[0][:150] if problems else ''}")

        # ------------------------------------------------------------------------------------------------ N1
        text = bri.read_text(REAL_06)
        sections = bri.parse_sections(text)
        n_heads = sum(1 for ln in text.split("\n") if ln.startswith("## "))
        arm("N1 DETERMINISM: sections == count of '^## ' lines", len(sections) == n_heads,
            f"{len(sections)} vs {n_heads}")
        lines = text.split("\n")
        independent = set()
        # `propose` added 2026-10-21 with the generator's DONOT_RE (the independent overlay review found 06:4447, 4448, 5661)
        rx = re.compile(r"do\s+not\s+re-?(?:raise|open|ask|propose)|do-?not-?reopen", re.IGNORECASE)
        offsets = [0]
        for ln in lines:
            offsets.append(offsets[-1] + len(ln) + 1)
        for m in rx.finditer(text):
            i = bisect.bisect_right(offsets, m.start()) - 1
            if not lines[i].startswith("## "):
                independent.add(i + 1)
        cand_lines = {d["line"] for s in sections for d in s["donot"]}
        arm("N1 DETERMINISM: do-not candidates == independent count (same regex)", cand_lines == independent,
            f"{len(cand_lines)} vs {len(independent)}")
        spec_grep = {i + 1 for i, ln in enumerate(lines)
                     if re.search(r"do not re-?raise|do not re-?open|do-?not-?reopen", ln, re.IGNORECASE)
                     and not ln.startswith("## ")}
        arm("N1 every spec-phrase line-grep hit is a candidate", spec_grep <= cand_lines,
            f"line grep {len(spec_grep)}, candidates {len(cand_lines)}, missing {sorted(spec_grep - cand_lines)}")
        ids = [s["id"] for s in sections]
        arm("N1 ids unique", len(ids) == len(set(ids)), f"{len(ids)} ids")

        # ------------------------------------------------------------------------------------------------ N2
        syn = ("# synthetic 06\n\n## 2026-01-01 — USER RULING 7: alpha\nbody a\n\n"
               "## 2026-01-02 — USER RULING 7: beta\nbody b\n")
        d06 = write(tmp / "n2" / "06.md", syn)
        ss = bri.parse_sections(syn)
        a_id, b_id = ss[0]["id"], ss[1]["id"]

        def check_with(decisions: Path, overlay: dict, sub: str):
            ov = overlay_file(tmp / sub / "overlay.json", overlay)
            oj, om = tmp / sub / "R.json", tmp / sub / "R.md"
            regen(decisions, ov, oj, om)
            return bri.check(decisions, ov, oj, om)[0], ov

        p, _ = check_with(d06, {}, "n2f")
        hit = [x for x in p if "repeated USER RULING 7" in x]
        arm("N2 FAULT repeated number with no overlay fails, naming both", bool(hit) and a_id in hit[0] and b_id in hit[0],
            hit[0][:160] if hit else f"no repeat failure: {p[:2]}")
        p, _ = check_with(d06, {b_id: {"ruling_key": "7@2026-01-02"}}, "n2c1")
        arm("N2 CONTROL ruling_key on the later heading passes", not p, "; ".join(p)[:160])
        p, _ = check_with(d06, {b_id: {"application_of": a_id}}, "n2c2")
        arm("N2 CONTROL application_of passes", not p, "; ".join(p)[:160])

        # ------------------------------------------------------------------------------------------------ N3
        syn3 = ("# synthetic 06\n\n## 2026-02-01 — the zebra question\n**DO NOT RE-RAISE X.** zebra crossing ruled.\n"
                "\n## 2026-02-02 — unrelated\nnothing here\n")
        d3 = write(tmp / "n3" / "06.md", syn3)
        s3 = bri.parse_sections(syn3)[0]
        key = s3["donot"][0]["key"] if s3["donot"] else "none"
        p, _ = check_with(d3, {}, "n3f")
        arm("N3 FAULT unclassified do-not fails", any("unclassified do-not" in x for x in p), (p or ["no failure"])[0][:140])
        p, ov = check_with(d3, {s3["id"]: {"candidates": {key: "marker"}, "do_not_reopen": "the zebra question"}}, "n3m")
        rc, out = run_ask(tools, "zebra crossing", d3, ov, no_ledger)
        arm("N3 CONTROL marker passes check", not p, "; ".join(p)[:140])
        arm("N3 CONTROL marker: ask prints the DO-NOT banner FIRST and quotes 06", out.startswith(BANNER)
            and "DO NOT RE-RAISE X" in out, out.splitlines()[0][:100] if out else f"rc={rc}, no output")
        p, ov = check_with(d3, {s3["id"]: {"candidates": {key: "mention"}}}, "n3n")
        rc, out = run_ask(tools, "zebra crossing", d3, ov, no_ledger)
        arm("N3 CONTROL mention passes check", not p, "; ".join(p)[:140])
        arm("N3 CONTROL mention: ask finds the section but prints NO flag", rc == 0 and BANNER not in out
            and s3["id"] in out, f"rc={rc}; first line {out.splitlines()[0][:80] if out else ''}")
        p, _ = check_with(d3, {s3["id"]: {"candidates": {key: "marker"}}}, "n3s1")
        arm("N3b FAULT a marker with no do_not_reopen line fails (schema)",
            any("no do_not_reopen" in x for x in p), (p or ["no failure"])[0][:140])
        p, _ = check_with(d3, {s3["id"]: {"candidates": {key: "mention"}, "superseeded_by": "x"}}, "n3s2")
        arm("N3b FAULT an unknown (misspelled) overlay field fails (schema)",
            any("unknown field" in x for x in p), (p or ["no failure"])[0][:140])

        # ------------------------------------------------------------------------------------------------ N4
        p, _ = check_with(d06, {"2026-01-03-deadbe": {"status": "ACTIVE"}, b_id: {"ruling_key": "7@2026-01-02"}}, "n4f")
        arm("N4 FAULT overlay id of a deleted section fails 'unresolved'", any("unresolved overlay id" in x for x in p),
            (p or ["no failure"])[0][:140])
        p, _ = check_with(d06, {a_id: {"status": "SUPERSEDED", "superseded_by": "2026-01-09-000000"},
                                b_id: {"ruling_key": "7@2026-01-02"}}, "n4g")
        arm("N4 FAULT superseded_by naming nothing fails 'dangling'", any("dangling superseded_by" in x for x in p),
            (p or ["no failure"])[0][:140])
        p, _ = check_with(d06, {a_id: {"status": "SUPERSEDED", "superseded_by": b_id},
                                b_id: {"ruling_key": "7@2026-01-02"}}, "n4c")
        arm("N4 CONTROL the same overlay with live ids passes", not p, "; ".join(p)[:160])
        dup = write(tmp / "n4d" / "06.md", "# x\n\n## 2026-03-01 — same words\na\n\n## 2026-03-01 — same words\nb\n")
        p, _ = check_with(dup, {}, "n4d")
        arm("N4b FAULT two identical headings (one id) fail 'duplicate id'", any("duplicate id" in x for x in p),
            (p or ["no failure"])[0][:140])

        # ------------------------------------------------------------------------------------------------ N5
        d5 = tmp / "n5" / "06.md"
        d5.parent.mkdir(parents=True)
        shutil.copyfile(REAL_06, d5)
        ov5 = tmp / "n5" / "overlay.json"
        shutil.copyfile(REAL_OVERLAY, ov5)
        oj, om = tmp / "n5" / "R.json", tmp / "n5" / "R.md"
        regen(d5, ov5, oj, om)
        p0, _ = bri.check(d5, ov5, oj, om)
        with d5.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n## 2099-01-01 — an ordinary appended decision\nIt rules nothing that needs the overlay.\n")
        p1, _ = bri.check(d5, ov5, oj, om)
        stale = [x for x in p1 if "stale" in x]
        arm("N5 CONTROL before the append the copy passes", not p0, "; ".join(p0)[:140])
        arm("N5 FAULT append without regenerating fails 'stale' with the command",
            bool(stale) and bri.REGEN_CMD in stale[0], (stale or p1 or ["no failure"])[0][:160])
        regen(d5, ov5, oj, om)
        p2, _ = bri.check(d5, ov5, oj, om)
        arm("N5 CONTROL regenerate passes; the append added no overlay obligation", not p2, "; ".join(p2)[:160])

        # ------------------------------------------------------------------------------------------------ N6
        empty = overlay_file(tmp / "n6" / "empty-overlay.json", {})
        control_first, passed = {}, 0
        for q, want, label in GOLDEN:
            rc, out = run_ask(tools, q, REAL_06, REAL_OVERLAY, no_ledger)
            ranked = re.findall(r"^\[(\d+)\] (\S+)", out, re.MULTILINE)
            top3 = [sid for _, sid in ranked[:3]]
            ok = rc == 0 and want in top3
            passed += ok
            control_first[q] = out.startswith(BANNER)
            arm(f"N6 golden {q!r} -> {want} in top 3", ok,
                f"rank {top3.index(want) + 1 if want in top3 else '-'} of {len(ranked)} ({label})")
        arm("N6 golden 6 of 6", passed == len(GOLDEN), f"{passed} of {len(GOLDEN)}")
        flagged = [q for q, first in control_first.items() if first]
        arm("N6 CONTROL some golden answers print the DO-NOT banner first (else the FAULT arm is vacuous)",
            len(flagged) >= 3, f"{len(flagged)} flagged: {flagged}")
        still = []
        for q in flagged:
            rc, out = run_ask(tools, q, REAL_06, empty, no_ledger)
            if out.startswith(BANNER) or BANNER in out:
                still.append(q)
        arm("N6 FAULT overlay emptied: the DO-NOT line is no longer printed first", not still and bool(flagged),
            f"still flagged: {still}" if still else f"{len(flagged)} queries lost their banner")
        rc, out = run_ask(tools, NEVER_RULED, REAL_06, REAL_OVERLAY, no_ledger)
        arm(f"N6 CONTROL never-ruled {NEVER_RULED!r} exits 3 'NO PRIOR RULING OR FACT FOUND'",
            rc == 3 and "NO PRIOR RULING OR FACT FOUND" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [n for n, ok, _ in RESULTS if not ok]
    secs = time.monotonic() - t0
    if failed:
        print(f"SELFTEST RULINGS INDEX FAILED: {len(failed)} of {len(RESULTS)} arms ({secs:.1f}s): {failed}")
        return 1
    print(f"SELFTEST RULINGS INDEX OK: {len(RESULTS)} arms, N0-N6 ({secs:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
