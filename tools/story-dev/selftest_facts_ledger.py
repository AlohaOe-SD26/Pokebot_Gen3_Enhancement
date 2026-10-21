"""GATE: the facts ledger lint (`check_facts_ledger.py`) and the decomp side of `tools/decomp_lookup.py`, spec S3-2
tests L1, L2, F1, F2. Each arm has a FAULT (the guard must fire) and a CONTROL (it must stay quiet). No ROM; ~10 s.

  L1  PIN REFUSAL. FAULT: `trainer TRAINER_ROXANNE_1` against a clone at the WRONG commit exits 2 with the clone
      commands and no answer (the June 2026 clone in ../POKEMON_EMERAL_AI/pokeemerald when present; always also the
      pinned clone checked against a wrong pin file, a folder that is not a clone, and a missing folder).
      CONTROL: the pinned clone answers id 265 with a first party member of level 12 (Geodude).
  L2  CRLF. A copy of a decomp file with CRLF endings returns the SAME hit (line and text) as the LF original: a
      synthetic opponents.h/trainers.h/trainer_parties.h (always), and src/party_menu.c from the pinned clone.
  F1  FAULT: a CONFIRMED row with no source fails; deleting a REFUTED row fails `--against`; editing one fails;
      a REFUTED row with no correction fails; a tool outside tools/ fails; a missing dependent fails.
      CONTROL: appending a row passes; the REAL ledger passes `--against-head`.
  F2  FAULT: a CONFIRMED row whose decomp ref names a symbol absent from the pinned clone fails; a ref at another SHA
      fails. CONTROL: with no clone (a missing --decomp path) the same file prints `SKIPPED <n> decomp refs` and exits
      4 (WARN), never 0.

WITHOUT THE PINNED CLONE on this machine, the arms that need it print SKIPPED and this file exits 4 (WARN): a check
that silently passes where it could not look is vacuous. Make the clone with the commands `decomp_lookup.py` prints.

Run:  py -3.12 tools/story-dev/selftest_facts_ledger.py [--tools-dir DIR] [--decomp DIR]
Exit: 0 every arm passed; 1 any arm failed; 4 no arm failed but some were SKIPPED (no pinned clone).
"""
from __future__ import annotations

import argparse
import json
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
REAL_LEDGER = REPO / "PROJECT KNOWLEDGE" / "facts-ledger.jsonl"
REAL_PIN = REPO / "tools" / "decomp.pin"
DEFAULT_DECOMP = REPO.parent / "_decomp" / "pokeemerald"
JUNE_CLONE = REPO.parent / "POKEMON_EMERAL_AI" / "pokeemerald"   # the known WRONG clone (L1 FAULT), read-only

RESULTS: list[tuple[str, str, str]] = []   # (name, PASS|FAIL|SKIP, detail)


def arm(name: str, ok: bool | None, detail: str = "") -> None:
    state = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
    RESULTS.append((name, state, detail))
    print(f"  {state}  {name}" + (f"  :: {detail}" if detail else ""))


def run(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run([sys.executable] + cmd, capture_output=True, timeout=300)
    return res.returncode, res.stdout.decode("utf-8", errors="replace")


def row(**kw) -> dict:
    base = {"id": "T1", "claim": "a claim", "status": "CONFIRMED",
            "source": {"kind": "code", "ref": "tools/decomp_lookup.py:def decomp_root"},
            "tool": "py -3.12 tools/decomp_lookup.py symbol X", "dependents": ["tools/decomp.pin"],
            "first_seen": "2026-10-21", "last_checked": "2026-10-21", "checked_by": "selftest"}
    base.update(kw)
    return {k: v for k, v in base.items() if v is not None}


def jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    return path


SYN_OPP = "#ifndef X\n#define TRAINER_NONE 0\n#define TRAINER_TEST_1 7\n#endif\n"
SYN_TRAINERS = ("const struct Trainer gTrainers[] = {\n    [TRAINER_TEST_1] =\n    {\n"
                "        .trainerClass = TRAINER_CLASS_LEADER,\n        .doubleBattle = FALSE,\n"
                "        .party = NO_ITEM_DEFAULT_MOVES(sParty_Test1),\n    },\n};\n")
SYN_PARTIES = ("static const struct TrainerMonNoItemDefaultMoves sParty_Test1[] = {\n    {\n    .iv = 0,\n"
               "    .lvl = 9,\n    .species = SPECIES_ZIGZAGOON,\n    }\n};\n\nvoid TestFunction(void)\n{\n}\n")


def write_mini(root: Path, crlf: bool) -> Path:
    for rel, text in (("include/constants/opponents.h", SYN_OPP), ("src/data/trainers.h", SYN_TRAINERS),
                      ("src/data/trainer_parties.h", SYN_PARTIES)):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.replace("\n", "\r\n" if crlf else "\n").encode("utf-8"))
    return root


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tools-dir", type=Path, default=HERE.parent)
    ap.add_argument("--decomp", type=Path, help="the pinned clone (default: decomp_lookup's own resolution)")
    args = ap.parse_args()
    tools = args.tools_dir.resolve()
    sys.path.insert(0, str(tools))
    import decomp_lookup as dl  # noqa: E402
    if args.decomp is None:
        args.decomp = dl.candidate_path(None) if tools == HERE.parent else DEFAULT_DECOMP
    lookup = str(tools / "decomp_lookup.py")
    lint = str(tools / "story-dev" / "check_facts_ledger.py")
    t0 = time.monotonic()
    tmp = Path(tempfile.mkdtemp(prefix="s32-ledger-"))
    pin = dl.read_pin(REAL_PIN)
    try:
        dl.verify_pin(args.decomp, pin)
        clone: Path | None = args.decomp
    except dl.DecompRefused as exc:
        clone = None
        print(f"  (no usable pinned clone at {args.decomp}: {exc}; clone-dependent arms are SKIPPED -> WARN)")
    try:
        # ------------------------------------------------------------------------------------------------ L1
        common = ["--pin-file", str(REAL_PIN)]
        docs = REPO / "PROJECT KNOWLEDGE"
        real_docs = ["--decisions", str(docs / "06-DECISIONS-LOG.md"), "--overlay", str(docs / "rulings-overlay.json"),
                     "--ledger", str(REAL_LEDGER)]
        if JUNE_CLONE.is_dir():
            rc, out = run([lookup, "trainer", "TRAINER_ROXANNE_1", "--decomp", str(JUNE_CLONE)] + common)
            arm("L1 FAULT the June clone is refused: exit 2, clone commands, no answer",
                rc == 2 and "git clone -c core.autocrlf=false" in out and "= 265" not in out, f"rc={rc}")
        else:
            arm("L1 FAULT the June clone is refused", None, f"{JUNE_CLONE} not on this machine")
        notclone = tmp / "not-a-clone"
        write_mini(notclone, crlf=False)
        rc, out = run([lookup, "trainer", "TRAINER_TEST_1", "--decomp", str(notclone)] + common)
        arm("L1 FAULT a folder that is not a clone is refused (exit 2, reason not_a_clone), though the answer is in it",
            rc == 2 and "= 7" not in out and "REFUSED (not_a_clone)" in out, f"rc={rc}")
        rc, out = run([lookup, "trainer", "TRAINER_ROXANNE_1", "--decomp", str(tmp / "absent")] + common)
        arm("L1 FAULT a missing clone is refused (exit 2) with the clone commands",
            rc == 2 and "git clone" in out, f"rc={rc}")
        rc, out = run([lookup, "ask", "stash drop", "--decomp", str(tmp / "absent")] + common + real_docs)
        arm("L1 CONTROL `ask` with NO clone still answers from 06 and says the decomp was NOT SEARCHED",
            rc == 0 and "2026-08-13-9d3b6c" in out and "NOT SEARCHED" in out and "git clone" in out, f"rc={rc}")
        if clone:
            wrong = tmp / "wrong.pin"
            wrong.write_text("83df84e40623b79281f2397faa611cbf044170bd\n", encoding="utf-8")
            rc, out = run([lookup, "trainer", "TRAINER_ROXANNE_1", "--decomp", str(clone), "--pin-file", str(wrong)])
            arm("L1 FAULT the pinned clone against a WRONG pin is refused (exit 2, no answer)",
                rc == 2 and "= 265" not in out, f"rc={rc}")
            rc, out = run([lookup, "ask", "TRAINER_ROXANNE_1", "--decomp", str(clone), "--pin-file", str(wrong)]
                          + real_docs)
            arm("L1 FAULT `ask` against a clone at the wrong commit is refused too (exit 2), not answered from it",
                rc == 2 and "REFUSED" in out and "DECOMP (" not in out, f"rc={rc}")
            rc, out = run([lookup, "trainer", "TRAINER_ROXANNE_1", "--decomp", str(clone)] + common)
            first = next((ln for ln in out.splitlines() if ln.strip().startswith("1. ")), "")
            arm("L1 CONTROL the pinned clone answers TRAINER_ROXANNE_1 = 265, first mon level 12",
                rc == 0 and "TRAINER_ROXANNE_1 = 265" in out and first.strip().startswith("1. L12 SPECIES_GEODUDE"),
                f"rc={rc}; {first.strip()[:60]}")
        else:
            arm("L1 FAULT wrong pin / L1 CONTROL Roxanne = 265, L12", None, "no pinned clone")

        # ------------------------------------------------------------------------------------------------ L2
        lf, crlf = write_mini(tmp / "mini-lf", False), write_mini(tmp / "mini-crlf", True)
        t_lf, t_cr = dl.trainer(lf, "TRAINER_TEST_1"), dl.trainer(crlf, "TRAINER_TEST_1")
        arm("L2 CONTROL the synthetic LF trainer parses (id 7, L9 Zigzagoon)",
            bool(t_lf) and t_lf["id"] == 7 and t_lf["party"][:1] == [{"iv": "0", "lvl": "9", "species": "SPECIES_ZIGZAGOON"}],
            str(t_lf and t_lf["party"]))
        arm("L2 CRLF synthetic: trainer() identical on CRLF", t_lf == t_cr, "")
        s_lf = dl.symbol(lf, "TestFunction", ("src/data/trainer_parties.h",))
        s_cr = dl.symbol(crlf, "TestFunction", ("src/data/trainer_parties.h",))
        arm("L2 CRLF synthetic: symbol() same hit (line, kind, text)", bool(s_lf) and s_lf == s_cr, f"{s_lf} vs {s_cr}")
        g_lf = dl.grep(lf, r"ZIGZAGOON,$", ("src/data/trainer_parties.h",))
        g_cr = dl.grep(crlf, r"ZIGZAGOON,$", ("src/data/trainer_parties.h",))
        arm("L2 CRLF synthetic: grep() with a $ anchor, same hit", bool(g_lf) and g_lf == g_cr, f"{g_lf} vs {g_cr}")
        if clone:
            cp = tmp / "crlf-clone" / "src" / "party_menu.c"
            cp.parent.mkdir(parents=True)
            raw = (clone / "src/party_menu.c").read_bytes()
            cp.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            a = dl.symbol(clone, "CursorCb_FieldMove", ("src/party_menu.c",))
            b = dl.symbol(tmp / "crlf-clone", "CursorCb_FieldMove", ("src/party_menu.c",))
            arm("L2 CRLF real file: a CRLF copy of src/party_menu.c returns the same hit", bool(a) and a == b,
                f"{a[:1]} vs {b[:1]}")
        else:
            arm("L2 CRLF real file", None, "no pinned clone")

        # ------------------------------------------------------------------------------------------------ F1
        def lint_rc(ledger: Path, *extra: str, decomp: Path | None = None) -> tuple[int, str]:
            d = ["--decomp", str(decomp)] if decomp else (["--decomp", str(clone)] if clone else ["--no-decomp"])
            return run([lint, "--ledger", str(ledger), "--repo", str(REPO), "--pin-file", str(REAL_PIN), *d, *extra])

        ok_rc = 0 if clone else 4   # the REAL ledger holds decomp refs: WARN (4) where they cannot be checked
        refuted = row(id="R1", status="REFUTED", correction="what is true instead")
        base = jsonl(tmp / "f1" / "base.jsonl", [row(), refuted])
        rc, out = lint_rc(base)
        arm("F1 CONTROL a well-formed ledger passes (no decomp refs: 0 with or without a clone)", rc == 0,
            f"rc={rc} {out.strip().splitlines()[-1][:90]}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "nosrc.jsonl", [row(source=None), refuted]))
        arm("F1 FAULT a CONFIRMED row with no source fails", rc == 1 and "lacks ['source']" in out, f"rc={rc}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "noref.jsonl", [row(source={"kind": "code", "ref": ""}), refuted]))
        arm("F1 FAULT a CONFIRMED row with an empty source.ref fails", rc == 1 and "no source.ref" in out, f"rc={rc}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "deleted.jsonl", [row()]), "--against", str(base))
        arm("F1 FAULT deleting a REFUTED row fails --against", rc == 1 and "R1" in out and "REMOVED" in out, f"rc={rc}")
        edited = dict(refuted, correction="rewritten history")
        rc, out = lint_rc(jsonl(tmp / "f1" / "edited.jsonl", [row(), edited]), "--against", str(base))
        arm("F1 FAULT editing a REFUTED row fails --against", rc == 1 and "EDITED" in out, f"rc={rc}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "appended.jsonl", [row(), refuted, row(id="T2")]), "--against", str(base))
        arm("F1 CONTROL appending a row passes --against", rc == 0, f"rc={rc}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "nocorr.jsonl", [row(), row(id="R2", status="REFUTED")]))
        arm("F1 FAULT a REFUTED row with no correction fails", rc == 1 and "no correction" in out, f"rc={rc}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "badtool.jsonl", [row(tool="py -3.12 custom-pokebot/pokebot.py")]))
        arm("F1 FAULT a tool outside tools/ fails", rc == 1 and "not under tools/" in out, f"rc={rc}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "nodep.jsonl", [row(dependents=["no/such/file.md"])]))
        arm("F1 FAULT a missing dependent fails", rc == 1 and "no/such/file.md" in out, f"rc={rc}")
        rc, out = lint_rc(jsonl(tmp / "f1" / "dupid.jsonl", [row(), row(claim="another claim")]))
        arm("F1 FAULT two rows with one id fail", rc == 1 and "id 'T1' on lines" in out, f"rc={rc}")
        rc, out = lint_rc(REAL_LEDGER, "--against-head")
        arm("F1 CONTROL the REAL ledger passes --against-head", rc == ok_rc, out.strip().splitlines()[-1][:110])

        # ------------------------------------------------------------------------------------------------ F2
        good = row(id="D1", source={"kind": "decomp", "ref": f"pret/pokeemerald@{pin[:8]}:src/party_menu.c:CursorCb_FieldMove"})
        bad = row(id="D2", source={"kind": "decomp", "ref": f"pret/pokeemerald@{pin[:8]}:src/party_menu.c:CursorCb_NoSuchFn"})
        f2 = jsonl(tmp / "f2" / "absent-symbol.jsonl", [good, bad])
        if clone:
            rc, out = lint_rc(f2)
            arm("F2 FAULT a decomp ref to a symbol absent from the pinned clone fails", rc == 1
                and "CursorCb_NoSuchFn" in out, f"rc={rc}")
            rc, out = lint_rc(jsonl(tmp / "f2" / "good.jsonl", [good]))
            arm("F2 CONTROL the same ref to a real symbol passes", rc == 0, f"rc={rc}")
        else:
            arm("F2 FAULT absent symbol fails / CONTROL real symbol passes", None, "no pinned clone")
        rc, out = lint_rc(jsonl(tmp / "f2" / "othersha.jsonl", [row(id="D3", source={
            "kind": "decomp", "ref": "pret/pokeemerald@83df84e4:src/party_menu.c:CursorCb_FieldMove"})]))
        arm("F2 FAULT a decomp ref at another SHA fails", rc == 1 and "not the pinned" in out, f"rc={rc}")
        rc, out = lint_rc(f2, decomp=tmp / "no-clone-here")
        arm("F2 CONTROL clone path unset: prints 'SKIPPED 2 decomp refs' and exits 4 (WARN), never 0",
            rc == 4 and "SKIPPED 2 decomp refs" in out, f"rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    secs = time.monotonic() - t0
    failed = [n for n, s, _ in RESULTS if s == "FAIL"]
    skipped = [n for n, s, _ in RESULTS if s == "SKIP"]
    if failed:
        print(f"SELFTEST FACTS LEDGER + LOOKUP FAILED: {len(failed)} of {len(RESULTS)} arms ({secs:.1f}s): {failed}")
        return 1
    if skipped:
        print(f"WARN: SELFTEST FACTS LEDGER + LOOKUP: {len(RESULTS) - len(skipped)} arms passed, {len(skipped)} "
              f"SKIPPED (no pinned clone) ({secs:.1f}s). NOT A PASS.")
        return 4
    print(f"SELFTEST FACTS LEDGER + LOOKUP OK: {len(RESULTS)} arms, L1 L2 F1 F2 ({secs:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
