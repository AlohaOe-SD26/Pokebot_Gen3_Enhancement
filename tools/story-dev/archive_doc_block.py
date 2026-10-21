# -*- coding: utf-8 -*-
"""Move a closed block out of a current-state doc into an append-only archive — WITHOUT LOSING IT.

⛔⛔ WHY THIS FILE EXISTS, AND WHY IT ENFORCES **FOUR** INVARIANTS (A and B 2026-09-05; C and D added
2026-09-07/08, each after a failure that A and B both passed over — see their blocks below).
⭐ THE PATTERN WORTH SEEING: A and B protect the MOVE; **C and D protect the CLAIM.** Every invariant
after the first two exists because the tool did the mechanical job correctly and the resulting
document still lied.
On 2026-09-05 the punch list crossed its `lint_docs` R3 line budget and closed blocks were retired
with throwaway inline scripts. That went wrong TWICE IN ONE SESSION, in two different ways, and a
Tier 1 reviewer caught both:

  1. **TRUNCATION.** Three blocks were moved under the words "Full entry ARCHIVED VERBATIM" and two
     arrived truncated, one mid-sentence. Cause: an INDEX-SPACE MISMATCH — block starts were found in
     the MUTATED list while block ENDS were computed against the ORIGINAL. That is this project's
     single most-repeated bug shape (three filed against `handle_fainted_pokemon` alone).
  2. **ORPHANING.** Two new `###` headers were spliced in over an old one and ONLY THE HEADER was
     replaced — leaving ~35 lines of the old body sitting under a "CLOSED ⛔ DO NOT REOPEN" heading,
     still reading "STATUS: OPEN... this is the next build". A cold reader would have redone finished
     work. That is pair P2 (a header and its body move together) broken by an editing script.

⭐ These are OPPOSITE failures — one drops the body, the other keeps it in the wrong place — so ONE
check cannot catch both. Hence:
  **INVARIANT A (no loss):**   every non-blank line removed from the source appears in the archive.
  **INVARIANT B (no orphan):** after the swap, the pointer is followed by a real block boundary, so
                               no remnant of the old body is left behind under it.
Both are verified BEFORE either file is written, so a failure leaves the tree untouched.

‼ **CLAUDE.md rule 6 — "anything enforceable belongs in a GATE, not in prose."** The first fix lived
in a scratchpad script plus a changelog sentence claiming the check now happened. A safety property
proven once, in a file that was thrown away, does not protect the next archiving. So it lives here.

⛔ NOT REGISTERED IN `run_gates.py`, DELIBERATELY: it performs an operation rather than checking the
tree, so it has nothing to assert on a clean run. `--self-test` is its fault-proof — run that to
trust it.

USAGE
    py -3.12 archive_doc_block.py --source "PROJECT KNOWLEDGE/03-PUNCH-LIST.md" \
        --archive "PROJECT KNOWLEDGE/28-HANDOFF-ARCHIVE.md" \
        --starts-with "- [x] HISTORY — `#24-foo`" \
        --pointer "- [x] HISTORY — `#24-foo` — ARCHIVED VERBATIM to `28-...` on YYYY-MM-DD." \
        --note "why this block is closed history and not a live instruction"
    py -3.12 archive_doc_block.py --self-test

⚠ AFTER RUNNING IT, STILL RUN TIER 0 (`lint_docs.py`, `audit_doc_consistency.py`). This tool protects
the MOVE; it cannot know whether the pointer you wrote is honest, and `audit_doc_consistency`
separately enforces that a `##` header edit ships with a body line.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

#: A block runs until the next line that opens a new item or heading at column 0.
#: ⚠⚠ CONSEQUENCE THAT SURPRISED THIS FILE'S OWN AUTHOR (2026-09-05, caught by Tier 1): because
#: `### ` is a stop prefix, a `##` section that CONTAINS a `###` sub-heading is split at that
#: sub-heading — the sub-section stays behind. That is not a bug (invariant B correctly sees a real
#: boundary and invariant A correctly reports no loss), but the POINTER YOU WRITE must then say
#: which part moved. Archiving KI-45 moved its diagnosis and left its `### KI-45 — FIXED` block
#: behind, while the pointer claimed both had moved.
#: ⇒ ⭐ **THE TOOL GUARANTEES NOTHING IS LOST. IT CANNOT GUARANTEE YOUR SENTENCE ABOUT IT IS TRUE.**
#: Check what actually moved before describing it — `--dry-run` prints the line count.
STOP_PREFIXES = ("- [", "### ", "## ", "#### ")

#: ⛔ THE SAME PREFIXES, FROZEN, FOR **INVARIANT B ONLY** — and the duplication is deliberate.
#: ‼ Found by this file's own fault arm: invariant B originally read `STOP_PREFIXES`, the very
#: global the block-finder uses, so injecting a bad boundary broke the finder AND blinded the check
#: that exists to catch it. The arm reported "did not fire" and it was right.
#: ⇒ ⭐ **A CHECK THAT SHARES ITS INPUT WITH THE THING IT CHECKS IS NOT A CHECK** — the same reason
#: this project forbids an agent certifying text it wrote, and forbids a fork counting as
#: independent. Keep these two tuples separate even though they are equal today.
_BOUNDARY_FOR_CHECK = ("- [", "### ", "## ", "#### ")


def find_block(
    lines: "list[str]", starts_with: str, stop_prefixes: "tuple[str, ...] | None" = None
) -> "tuple[int, int]":
    """Return `(start, end)` of the one block whose first line starts with `starts_with`.

    ⛔ BOTH ENDS COME FROM THE SAME LIST — that is the whole point of this function. Refuses an
    anchor that does not match EXACTLY ONE line: silently archiving the wrong block is worse than
    a refusal.

    `stop_prefixes` (spec S2-1, 2026-10-21): `archive_sweep.py` moves a WHOLE `###` section, whose
    `- [x]` bullets are part of it, so it stops only at a heading of the same or a higher level.
    ⚠ Resolved at CALL time, never as a default argument, so the self-test's fault arm B (which
    swaps the global) still reaches the default path.
    """
    stops = STOP_PREFIXES if stop_prefixes is None else stop_prefixes
    hits = [i for i, line in enumerate(lines) if line.startswith(starts_with)]
    if len(hits) != 1:
        raise SystemExit(
            f"⛔ anchor {starts_with!r} matched {len(hits)} lines, expected exactly 1. "
            f"Refusing to guess which block you meant."
        )
    start = hits[0]
    end = start + 1
    while end < len(lines) and not lines[end].startswith(stops):
        end += 1
    return start, end


def render_archive(archive_text: str, source_name: str, note: str, block: str) -> str:
    """Build the new archive text. A seam, so `--self-test` can inject a truncating fault."""
    return (archive_text.rstrip("\n")
            + f"\n\n---\n\n## Archived from `{source_name}`\n\n{note}\n\n{block}\n")


def archive_block(
    source: pathlib.Path,
    archive: pathlib.Path,
    starts_with: str,
    pointer: str,
    note: str,
    *,
    dry_run: bool = False,
    stop_prefixes: "tuple[str, ...] | None" = None,
) -> "tuple[int, int]":
    """Move one block. Returns `(lines_removed, source_line_count_after)`.

    `stop_prefixes`: where the block ends (see `find_block`); invariant B keeps its OWN frozen
    boundary list whatever is passed here, so a caller cannot widen the check with the finder."""
    lines = source.read_text(encoding="utf-8").splitlines()
    start, end = find_block(lines, starts_with, stop_prefixes)
    block = "\n".join(lines[start:end]).rstrip()
    removed = [line for line in lines[start + 1:end] if line.strip()]
    lines[start:end] = [pointer]

    archive_text = render_archive(
        archive.read_text(encoding="utf-8"), source.name, note, block
    )

    # ---- INVARIANT A — NO LOSS ----------------------------------------------------------------
    lost = [line for line in removed if line not in archive_text]
    if lost:
        raise SystemExit(
            "⛔ CONTENT WOULD BE LOST — refusing to write. Not present in the archive:\n  "
            + "\n  ".join(lost[:10])
            + (f"\n  ... and {len(lost) - 10} more" if len(lost) > 10 else "")
        )

    # ---- INVARIANT B — NO ORPHAN ----------------------------------------------------------------
    # ‼ Checked STRUCTURALLY, not by text matching: after the swap the pointer must be followed by a
    # real block boundary. Ordinary prose there means the old body is still sitting under the new
    # pointer — the failure that put "STATUS: OPEN... this is the next build" under a CLOSED header.
    trailer = next((lines[i] for i in range(start + 1, len(lines)) if lines[i].strip()), None)
    if trailer is not None and not trailer.startswith(_BOUNDARY_FOR_CHECK) and trailer.strip() != "---":
        raise SystemExit(
            "⛔ THE BLOCK'S BODY WOULD BE ORPHANED under the new pointer — refusing to write.\n"
            f"  first line after the pointer: {trailer[:110]!r}\n"
            "  Expected a new item/heading. The block boundary is wrong, so only part of the block\n"
            "  was taken and the rest now sits under a pointer that says it was moved."
        )

    # ---- INVARIANT C — NO FALSE CLOSURE ---------------------------------------------------------
    # ⛔ ADDED 2026-09-07, and this file's own docstring PREDICTED the gap: *"it cannot know whether
    # the pointer you wrote is honest."* That day a bulk archiver matched sections on the bare word
    # "FIXED" and moved
    #     "## ‼ ARCHIVED ISSUES WORTH RE-READING — ⛔ MIXED STATUS: SOME ARE FIXED, SOME ARE NOT"
    # under the pointer "⛔ DO NOT REDO — this issue is CLOSED." It is a NAVIGATIONAL INDEX cold
    # starts follow (pair P4), and its heading says the OPPOSITE of closed.
    # ‼ INVARIANTS A AND B BOTH PASSED: nothing was lost, nothing was orphaned — and the document was
    # still wrong. That is exactly why C is a THIRD invariant and not a tightening of the other two.
    # ⭐ CLAUDE.md pair P2: "a heading is a claim about every bullet beneath it; if their statuses
    # differ the heading must say MIXED." So a MIXED heading is legal — what is illegal is covering
    # it with a pointer asserting UNCONDITIONAL closure. An honestly-mixed pointer passes.
    heading = block.lstrip().splitlines()[0] if block.strip() else ""
    heading_up, pointer_up = heading.upper(), pointer.upper()
    NOT_CLOSED = ("MIXED STATUS", "SOME ARE NOT", "SOME ARE FIXED, SOME", "STILL OPEN", "NOT FIXED")
    CLAIMS_CLOSED = ("DO NOT REDO", "DO NOT REOPEN", "IS CLOSED", "CLOSED.", "RESOLVED")
    # ‼ THE CAVEAT MUST BE THE POINTER'S OWN WORDS, NOT AN ECHO OF THE HEADING. A pointer
    # conventionally REPEATS the heading it replaces, so testing the whole pointer for "MIXED" let
    # the heading's own text satisfy the honesty exclusion — and this gate shipped INERT until its
    # fault arm caught it. Strip the heading first; only what the author ADDED counts as a caveat.
    pointer_extra = pointer_up.replace(heading_up, " ")
    hit = [m for m in NOT_CLOSED if m in heading_up]
    if hit and any(c in pointer_extra for c in CLAIMS_CLOSED) and not any(
        m in pointer_extra for m in NOT_CLOSED
    ):
        raise SystemExit(
            "⛔ THE POINTER CLAIMS CLOSURE OVER A HEADING THAT SAYS OTHERWISE — refusing to write.\n"
            f"  heading : {heading[:110]!r}\n"
            f"  says    : {', '.join(hit)}\n"
            f"  pointer : {pointer[:110]!r}\n"
            "  A heading is a claim about everything beneath it (CLAUDE.md pair P2). Either this\n"
            "  block is NOT closed and must not be archived, or the pointer must carry the same\n"
            "  MIXED caveat the heading does. ‼ Note invariants A and B pass here — nothing is lost\n"
            "  and nothing is orphaned. The defect is that the pointer LIES."
        )

    # ---- INVARIANT D — AN ARCHIVAL CLAIM REQUIRES AN ARCHIVAL MOVE ------------------------------
    # ⛔⛔ ADDED 2026-09-08, AND A AND B BOTH PASSED OVER THE FAILURE THAT MOTIVATED IT.
    # Called with `--starts-with "### ✅ \`#24-hm07teach\`"` on `03-PUNCH-LIST.md`, this tool reported
    #     "moved 0 line(s) ... No loss, no orphan — both invariants verified before writing"
    # and left a pointer reading "📦 ARCHIVED VERBATIM ... nothing deleted" with the ENTIRE BODY
    # still sitting directly beneath it. Both other invariants are satisfied by construction when
    # nothing moves: A has no removed lines to lose, and B's trailer is a `- [x]` bullet, which IS a
    # legitimate boundary in this file's item format. ⇒ **the block was the HEADER ALONE.**
    # ‼ The only signal was the words "moved 0 line(s)" in stdout — a number a human has to notice,
    # not a check. That is the day's recurring shape: an instrument that cannot express the failure
    # reports success.
    # ⭐ D is deliberately about the CLAIM, not the technique: a pointer may legitimately replace a
    # block with a summary, but it may not SAY "archived" when nothing was archived.
    ARCHIVAL_CLAIM = ("ARCHIVED", "MOVED TO", "NOTHING DELETED", "VERBATIM")
    if not removed and any(w in pointer.upper() for w in ARCHIVAL_CLAIM):
        raise SystemExit(
            "⛔ THE POINTER CLAIMS AN ARCHIVE BUT **ZERO LINES WOULD MOVE** — refusing to write.\n"
            f"  starts-with : {starts_with[:100]!r}\n"
            f"  pointer     : {pointer[:100]!r}\n"
            "  The matched block is its HEADER ALONE, so the body would stay in the source under a\n"
            "  pointer saying it was moved. ‼ Invariants A and B CANNOT catch this: with nothing\n"
            "  removed A has nothing to lose, and B's trailer is a real boundary.\n"
            "  ⇒ Check `--starts-with`: in a file whose items are `- [x]` bullets, a `###` heading\n"
            "  matches only the heading, because a bullet is itself a block boundary."
        )

    if not dry_run:
        archive.write_text(archive_text + "\n", encoding="utf-8")
        source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(removed), len(lines)


def self_test() -> int:
    """⛔ FAULT-PROOF BOTH INVARIANTS. A guard never seen to fail is not a guard."""
    import tempfile

    failures: "list[str]" = []
    body = ["- [x] `#test` — a closed thing", "  line one", "", "  line two", "  line three"]
    doc = ["# Doc", ""] + body + ["", "- [ ] `#next` — a live thing", "  still open"]
    original = "\n".join(doc) + "\n"

    def fixture(tmp: pathlib.Path, name: str, text: str = original):
        src, arc = tmp / f"{name}-src.md", tmp / f"{name}-arc.md"
        src.write_text(text, encoding="utf-8")
        arc.write_text("# Archive\n", encoding="utf-8")
        return src, arc

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = pathlib.Path(tmp_name)

        # --- 1. happy path: every line survives, the next block is untouched ----------------------
        src, arc = fixture(tmp, "ok")
        removed, _ = archive_block(src, arc, "- [x] `#test`", "- [x] `#test` — ARCHIVED.", "note")
        arc_text = arc.read_text(encoding="utf-8")
        for line in ("  line one", "  line two", "  line three"):
            if line not in arc_text:
                failures.append(f"happy path LOST {line!r}")
        if removed != 3:
            failures.append(f"happy path removed {removed} lines, expected 3")
        src_text = src.read_text(encoding="utf-8")
        if "  still open" not in src_text:
            failures.append("happy path damaged the NEXT block")
        if "  line two" in src_text:
            failures.append("happy path left body text behind in the source")

        # --- 2. FAULT ARM A — TRUNCATION. The archive silently drops the block's tail. ------------
        src, arc = fixture(tmp, "trunc")
        real_render = globals()["render_archive"]
        try:
            globals()["render_archive"] = (
                lambda text, name, note, block: real_render(
                    text, name, note, "\n".join(block.splitlines()[:1])
                )
            )
            try:
                archive_block(src, arc, "- [x] `#test`", "- [x] `#test` — ARCHIVED.", "note")
                failures.append("⛔ FAULT ARM A DID NOT FIRE — truncation was accepted")
            except SystemExit as exc:
                if "CONTENT WOULD BE LOST" not in str(exc):
                    failures.append(f"fault arm A raised the wrong error: {exc}")
        finally:
            globals()["render_archive"] = real_render
        if src.read_text(encoding="utf-8") != original:
            failures.append("⛔ a REFUSED archive (A) still modified the source")

        # --- 3. FAULT ARM B — ORPHANING. Only the header moves; the body stays behind. ------------
        src, arc = fixture(tmp, "orphan")
        real_stop = globals()["STOP_PREFIXES"]
        try:
            globals()["STOP_PREFIXES"] = ("",)   # every line looks like a boundary => block = 1 line
            try:
                archive_block(src, arc, "- [x] `#test`", "- [x] `#test` — ARCHIVED.", "note")
                failures.append("⛔ FAULT ARM B DID NOT FIRE — an orphaned body was accepted")
            except SystemExit as exc:
                if "ORPHANED" not in str(exc):
                    failures.append(f"fault arm B raised the wrong error: {exc}")
        finally:
            globals()["STOP_PREFIXES"] = real_stop
        if src.read_text(encoding="utf-8") != original:
            failures.append("⛔ a REFUSED archive (B) still modified the source")

        # --- 3b. FAULT ARM C — FALSE CLOSURE. The real 2026-09-07 defect, reproduced exactly. -----
        # ‼ Note what makes this arm worth having: invariants A and B BOTH PASS on it. Nothing is
        # lost and nothing is orphaned — the pointer simply lies about the block's status.
        MIXED_HDR = "## ‼ ARCHIVED ISSUES WORTH RE-READING — ⛔ MIXED STATUS: SOME ARE FIXED, SOME ARE NOT"
        mixed_doc = "\n".join(
            ["# Doc", "", MIXED_HDR, "  a pointer to a fixed thing", "  a pointer to an OPEN thing",
             "", "## `KI-99` — next", "  body"]
        ) + "\n"
        src, arc = fixture(tmp, "falseclosure", mixed_doc)
        try:
            archive_block(src, arc, MIXED_HDR,
                          f"{MIXED_HDR}  📦 ARCHIVED VERBATIM.\n⛔ DO NOT REDO — this issue is CLOSED.",
                          "note")
            failures.append("⛔ FAULT ARM C DID NOT FIRE — a CLOSED pointer over a MIXED heading was accepted")
        except SystemExit as exc:
            if "CLAIMS CLOSURE" not in str(exc):
                failures.append(f"fault arm C raised the wrong error: {exc}")
        if src.read_text(encoding="utf-8") != mixed_doc:
            failures.append("⛔ a REFUSED archive (C) still modified the source")

        # --- 3c. C MUST NOT FIRE on an honestly-MIXED pointer -------------------------------------
        # ⭐ CLAUDE.md P2 allows a MIXED heading outright; what it forbids is hiding the caveat. A
        # gate with false positives teaches the reader to bypass it, which is worse than no gate.
        src, arc = fixture(tmp, "honestmixed", mixed_doc)
        try:
            archive_block(src, arc, MIXED_HDR,
                          f"{MIXED_HDR}  📦 ARCHIVED VERBATIM — ⛔ MIXED STATUS, read each entry.",
                          "note")
        except SystemExit as exc:
            failures.append(f"⛔ C FALSE POSITIVE — an honestly-mixed pointer was refused: {exc}")

        # --- 3d. C MUST NOT FIRE on a genuinely closed block, nor on a MERE MENTION in the body ----
        CLOSED_HDR = "## `KI-79` — ✅ FIXED, FAULT-PROVEN AND PROMOTED TO BOTH FORKS"
        closed_doc = "\n".join(
            ["# Doc", "", CLOSED_HDR,
             "  before the fix this was STILL OPEN for three weeks and NOT FIXED anywhere",
             "  now closed", "", "## `KI-99` — next", "  body"]
        ) + "\n"
        src, arc = fixture(tmp, "genuinelyclosed", closed_doc)
        try:
            archive_block(src, arc, CLOSED_HDR,
                          f"{CLOSED_HDR}  📦 ARCHIVED VERBATIM.\n⛔ DO NOT REDO — this issue is CLOSED.",
                          "note")
        except SystemExit as exc:
            failures.append(f"⛔ C FALSE POSITIVE — a genuinely closed block was refused: {exc}")

        # --- 3e. FAULT ARM D — AN ARCHIVAL CLAIM OVER A ZERO-LINE MOVE ---------------------------
        # ‼ REPRODUCES THE REAL 2026-09-08 MISUSE: anchor a `###` heading in a file whose items are
        # `- [x]` bullets, so the "block" is the heading alone, and pair it with an ARCHIVED pointer.
        # ⛔ Invariants A and B BOTH PASS on this input — that is the entire point of arm D.
        bullet_doc = "\n".join(
            ["# Doc", "", "### ✅ `#item` — closed", "- [x] the body that must not be orphaned",
             "  detail line", "", "### ✅ `#next` — other", "- [x] other body"]
        ) + "\n"
        src, arc = fixture(tmp, "zeromove", bullet_doc)
        try:
            archive_block(src, arc, "### ✅ `#item`",
                          "### ✅ `#item` — 📦 ARCHIVED VERBATIM to `28-...` (nothing deleted).",
                          "note")
            failures.append("⛔ FAULT ARM D DID NOT FIRE — an ARCHIVED pointer over a 0-line move "
                            "was accepted (the body would be orphaned in the source)")
        except SystemExit as exc:
            if "ZERO LINES WOULD MOVE" not in str(exc):
                failures.append(f"fault arm D raised the wrong error: {exc}")
        if src.read_text(encoding="utf-8") != bullet_doc:
            failures.append("⛔ a REFUSED archive (D) still modified the source")

        # --- 3f. D MUST NOT FIRE on a SUMMARY pointer that makes no archival claim ----------------
        # ⭐ Replacing a block with a summary is legitimate; D is about the CLAIM, not the technique.
        src, arc = fixture(tmp, "summaryptr", bullet_doc)
        try:
            archive_block(src, arc, "### ✅ `#item`",
                          "### ✅ `#item` — closed; see `07-CHANGELOG.md` for detail.", "note")
        except SystemExit as exc:
            failures.append(f"⛔ D FALSE POSITIVE — a non-archival summary pointer was refused: {exc}")

        # --- 4. an ambiguous anchor is refused, not guessed ---------------------------------------
        src, arc = fixture(tmp, "ambig", "\n".join(doc + doc) + "\n")
        try:
            archive_block(src, arc, "- [x] `#test`", "p", "n")
            failures.append("⛔ ambiguous anchor was NOT refused")
        except SystemExit as exc:
            if "expected exactly 1" not in str(exc):
                failures.append(f"ambiguity check raised the wrong error: {exc}")

    if failures:
        print("SELF-TEST FAILED:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("SELF-TEST PASS — 9 arms:")
    print("  happy path keeps every line and leaves nothing behind;")
    print("  FAULT A (truncated archive)   -> refused by INVARIANT A, source untouched;")
    print("  FAULT B (header-only move)    -> refused by INVARIANT B, source untouched;")
    print("  FAULT C (CLOSED pointer over a MIXED heading) -> refused by INVARIANT C, source")
    print("          untouched. ‼ A and B BOTH PASS on this input — the pointer just lies;")
    print("  C no-fire: an honestly-MIXED pointer is ACCEPTED (the caveat must be the pointer's")
    print("          OWN words — echoing the heading does not count, which once made C inert);")
    print("  C no-fire: a genuinely closed block is ACCEPTED even when its BODY says")
    print("          'STILL OPEN' / 'NOT FIXED' — C reads the HEADING, not mere mentions;")
    print("  FAULT D (ARCHIVED pointer over a ZERO-line move) -> refused by INVARIANT D,")
    print("          source untouched. ‼ A and B BOTH PASS on this input: with nothing removed A")
    print("          has nothing to lose, and B's trailer is a real boundary. This is the REAL")
    print("          2026-09-08 misuse — a `###` anchor in a file whose items are `- [x]` bullets;")
    print("  D no-fire: a SUMMARY pointer making no archival claim is ACCEPTED (D is about the")
    print("          CLAIM, not the technique);")
    print("  ambiguous anchor              -> refused rather than guessed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--self-test", action="store_true", help="fault-prove both invariants")
    parser.add_argument("--source", help="current-state doc to move the block OUT of")
    parser.add_argument("--archive", help="append-only doc to move the block INTO")
    parser.add_argument("--starts-with", help="exact prefix of the block's first line (must match ONE)")
    parser.add_argument("--pointer", help="the one line left behind in the source")
    parser.add_argument("--note", default="", help="why this block is closed history, not a live instruction")
    parser.add_argument("--dry-run", action="store_true", help="verify and report, write nothing")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    missing = [n for n in ("source", "archive", "starts_with", "pointer") if not getattr(args, n)]
    if missing:
        parser.error(f"--self-test not given, so these are required: {', '.join(missing)}")

    removed, after = archive_block(
        pathlib.Path(args.source), pathlib.Path(args.archive),
        args.starts_with, args.pointer, args.note, dry_run=args.dry_run,
    )
    verb = "would move" if args.dry_run else "moved"
    print(f"{verb} {removed} line(s); {args.source} now {after} lines. "
          f"No loss, no orphan — both invariants verified before writing.")
    print("‼ Now run Tier 0: lint_docs.py AND audit_doc_consistency.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
