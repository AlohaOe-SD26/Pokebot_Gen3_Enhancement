# -*- coding: utf-8 -*-
"""Move a closed block out of a current-state doc into an append-only archive — WITHOUT LOSING IT.

⛔⛔ WHY THIS FILE EXISTS, AND WHY IT ENFORCES **TWO** INVARIANTS.
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
STOP_PREFIXES = ("- [", "### ", "## ", "#### ")

#: ⛔ THE SAME PREFIXES, FROZEN, FOR **INVARIANT B ONLY** — and the duplication is deliberate.
#: ‼ Found by this file's own fault arm: invariant B originally read `STOP_PREFIXES`, the very
#: global the block-finder uses, so injecting a bad boundary broke the finder AND blinded the check
#: that exists to catch it. The arm reported "did not fire" and it was right.
#: ⇒ ⭐ **A CHECK THAT SHARES ITS INPUT WITH THE THING IT CHECKS IS NOT A CHECK** — the same reason
#: this project forbids an agent certifying text it wrote, and forbids a fork counting as
#: independent. Keep these two tuples separate even though they are equal today.
_BOUNDARY_FOR_CHECK = ("- [", "### ", "## ", "#### ")


def find_block(lines: "list[str]", starts_with: str) -> "tuple[int, int]":
    """Return `(start, end)` of the one block whose first line starts with `starts_with`.

    ⛔ BOTH ENDS COME FROM THE SAME LIST — that is the whole point of this function. Refuses an
    anchor that does not match EXACTLY ONE line: silently archiving the wrong block is worse than
    a refusal.
    """
    hits = [i for i, line in enumerate(lines) if line.startswith(starts_with)]
    if len(hits) != 1:
        raise SystemExit(
            f"⛔ anchor {starts_with!r} matched {len(hits)} lines, expected exactly 1. "
            f"Refusing to guess which block you meant."
        )
    start = hits[0]
    end = start + 1
    while end < len(lines) and not lines[end].startswith(STOP_PREFIXES):
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
) -> "tuple[int, int]":
    """Move one block. Returns `(lines_removed, source_line_count_after)`."""
    lines = source.read_text(encoding="utf-8").splitlines()
    start, end = find_block(lines, starts_with)
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
    print("SELF-TEST PASS — 4 arms:")
    print("  happy path keeps every line and leaves nothing behind;")
    print("  FAULT A (truncated archive) -> refused by INVARIANT A, source untouched;")
    print("  FAULT B (header-only move)  -> refused by INVARIANT B, source untouched;")
    print("  ambiguous anchor            -> refused rather than guessed.")
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
