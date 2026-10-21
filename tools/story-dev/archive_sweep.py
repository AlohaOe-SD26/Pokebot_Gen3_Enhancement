# -*- coding: utf-8 -*-
"""Sweep the CLOSED `###` blocks of a current-state doc into its append-only archive. A DRY RUN by default.

(spec S2-1, backlog A4, 2026-10-21: `ai-research-notes/2026-10-19-BUILD-SPECS-steps-1-2.md`)

WHY THIS EXISTS. `lint_docs.py` R8 is a RATCHET on the current-state docs' bytes: it ships green at today's sizes
and only tightens as bytes leave. This is what makes them leave. Retiring closed blocks by hand went wrong in this
project twice in one session (truncation, orphaning: `archive_doc_block.py`'s docstring), so this file decides
nothing about HOW a block moves: every move goes through `archive_doc_block.archive_block`, whose invariants A-D
(no loss, no orphan, no false closure, no archival claim over a zero-line move) are verified before either file is
written. What this file adds is WHICH blocks, and a pointer that keeps every slug:

  * SELECTION = R7's OWN PREDICATE (`lint_docs.r7_section_is_closed`, imported, never copied): a `###` section whose
    heading says done, that holds no `- [ ]` / `- [~]` box and is not MIXED / STILL OPEN. ⛔ The sweep is STRICTER
    than R7, never looser: the block that moves (to the next `#`/`##`/`###` heading outside a fence) must be the very
    block `archive_doc_block.find_block` sees, which makes it a prefix of R7's section, and a heading that also says
    NOT FIXED / UNRESOLVED / OPEN / PARTIAL / IN REVIEW / PENDING / NEXT ... is skipped. ⛔ So is a block whose BODY
    keeps it open (round 2): an unchecked/partial box at any indent, or an open word used as a STATUS MARKER (upper
    case, at a bullet's start, a bold span's start or after an emoji) — a heading is not the only claim in a block.
    Round 3: also a narrow set in ANY position and case (UNDRIVEN, UNTESTED, UNVERIFIED, NOT VERIFIED / PROMOTED /
    DONE, FOLLOW-UP, KNOWN GAP), a line-start STILL OPEN, a `####` subheading saying OPEN / Open questions, and an
    open box in a table cell.
    A block that is already a pointer (its heading says ARCHIVED) is skipped. Every skip prints its reason.
    Over-skipping costs bytes; over-selecting moves a LIVE item out of the file a cold reader acts from.
  * POINTER = the heading (cut at 600 characters) + "ARCHIVED VERBATIM to <archive> on <date>", then a "Slugs kept
    for grep" line naming every `#NN-slug` and every `KI-n` the block held that the heading does not. ⛔ CHECKED
    BEFORE WRITING on the source as it would be written: every slug the block held must still be found in it, so
    `grep '#slug'` still lands on the pointer (S-2). The check reads the SIMULATED file, not the pointer builder's
    own output, so a builder that drops a slug cannot vouch for itself.
  * MEGA-LINES (`--split-lines`, opt-in): a prose line over 1,200 characters is split only at the last `. ` / `; `
    / ` - ` before 1,200 characters into continuation lines (a list item's at its content column; a blockquote's
    with its `>` markers repeated), never where the next piece would start a new block (a bullet, a heading, `1. `,
    a quote, a table, a fence), never inside a code span, and ONLY IF every piece fits AND the whitespace-normalised
    join equals the original (S-5). A soft line break renders as a space, so the page reads the same. Headings,
    table rows, fenced lines and 4-space-indented prose (it may be a code block) are never split.
  * `--apply` FIRST REHEARSES THE WHOLE RUN on scratch copies (every move through the real mover, then the split plan
    validated: words unchanged with quote markers aside, quote depth kept). ⛔ Round 3: the COMPLETE would-be result
    (source, archive, both R8 JSON files after the bookkeeping below) is then LINTED in a temp copy of the docs and
    budget folders, every rule including R3's line budget, and a red rule REFUSES the apply, naming it. Any
    refusal happens there, so "nothing written" is true; only then are the real files written.
  * AFTER `--apply`: R8's waivers for the source are re-hashed (shrink and drop only, so no `--why` is needed) and its
    ceiling is RATCHETED down, so the bytes removed cannot quietly grow back — ONLY when `--source` IS the real R8
    file (resolved paths equal); a sweep of a copy prints "R8 not updated (not the real file)".

USAGE
    py -3.12 archive_sweep.py --source "PROJECT KNOWLEDGE/03-PUNCH-LIST.md"                 (dry run: lists, writes nothing)
    py -3.12 archive_sweep.py --source "PROJECT KNOWLEDGE/04-HANDOFF.md" --apply [--split-lines]
    ⛔ NOT A RECIPE TODAY: `--source 04-HANDOFF.md --apply --split-lines` is REFUSED by R3's line budget (measured
    2026-10-21: the split takes 04 from 883 lines to 1,069 against its 900), pending the separate handoff slim-down
    design. 03's sweep + split likewise crosses its 4,400 (4,399 -> 4,525). A plain `--apply` (no split) adds no
    lines; the rehearsal lint (above) refuses either way, with nothing written.
    Default archives: 03 -> `32-PUNCH-LIST-ARCHIVE.md` (created on the first --apply; then add it to 00-README's reading
    order, pair P4), 04 -> `28-HANDOFF-ARCHIVE.md`. Any other source needs --archive.
    `--docs-dir` / `--budget-dir` point R8's bookkeeping (and the rehearsal's lint) at a synthetic tree, and
    `--repo-dir` the lint's R6 scan (selftest_lint_docs.py S-1..S-7).
⚠ AFTER --apply, STILL RUN TIER 0 (`lint_docs.py`, `audit_doc_consistency.py`). One sweep per commit, explicit paths.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import io
import json
import pathlib
import re
import sys
import tempfile

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import archive_doc_block as adb  # noqa: E402  (the MOVE and its invariants A-D: never re-implemented here)
import lint_docs as ld  # noqa: E402  (R7's predicate, the fence rule, R8's rewaive/ratchet: one copy each)

#: Where each source's closed blocks go. 32 is the next free number (R4); 28 already holds old 04 blocks.
DEFAULT_ARCHIVES = {"03-PUNCH-LIST.md": "32-PUNCH-LIST-ARCHIVE.md", "04-HANDOFF.md": "28-HANDOFF-ARCHIVE.md"}
#: A `###` block ends at the next heading of the same or a higher level; its `- [x]` bullets and `####`
#: sub-headings move WITH it (archive_doc_block's default stops at every bullet, for single-item moves).
SWEEP_STOPS = ("# ", "## ", "### ")
#: ⛔ Words that keep a heading OUT of the sweep even when R7 counts it closed. R7's word test is a substring test
#: ("NOT FIXED" contains "FIXED", "UNRESOLVED" contains "RESOLVED", "ABANDONED" contains "DONE"), which is
#: tolerable for a SHARE and not for a MOVE. Matched on the upper-cased heading with word boundaries.
#: Round 2 (2026-10-21) added UNFIXED, NOT YET (any), UNVERIFIED, DEFERRED, OUTSTANDING, PARKED, WIP and AWAITING: each
#: was R7-closed AND selected in the checker's probe ("### ✅ PART 1 DONE; PART 2 UNFIXED" and four more). Still a deny-
#: list, so it errs by WIDENING: a word too many only skips a block (safe); a word too few moves a live one.
OPEN_WORDS = (r"NOT\s+YET|NOT\s+(?:FIXED|DONE|CLOSED|RESOLVED|BUILT|SHIPPED)|UNRESOLVED|UNFIXED|UNDONE|UNVERIFIED"
              r"|REOPEN\w*|PARTLY|PARTIAL\w*|IN\s+PROGRESS|IN\s+REVIEW|STILL\s+OPEN|OPEN|BLOCKED|PENDING|AWAITING"
              r"|DEFERRED|OUTSTANDING|PARKED|WIP|TODO|NEXT|SOME\s+ARE|MIXED|REMAIN\w*")
#: Round 3: the body's narrow set (below) counts in a heading too ("### ✅ FIXED IN SANDBOX — NOT PROMOTED",
#: "(NOT VERIFIED LIVE)", "— UNDRIVEN", "— UNTESTED" were still selected after round 2).
NARROW_OPEN_WORDS = r"UNDRIVEN|UNTESTED|UNVERIFIED|NOT\s+VERIFIED|NOT\s+PROMOTED|NOT\s+DONE|FOLLOW-UPS?|KNOWN\s+GAPS?"
NOT_CLOSED_RE = re.compile(rf"\b(?:{OPEN_WORDS}|{NARROW_OPEN_WORDS})\b")
#: ⛔ THE BODY COUNTS TOO (round 2). A heading saying "✅ FIXED AND RE-DRIVEN" sat over a body opening with
#: "**🔶 MIXED — TWO OF THESE ARE DONE AND TWO ARE GENUINELY OPEN**" and "* ⛔ **STILL OPEN — Doubles are
#: UNEXERCISED.**" (05, 2026-09-06 block); the heading-only test moved it, and both open items left the file a cold
#: reader acts from. A body line SKIPS the block when an open word is used as a STATUS MARKER: in UPPER CASE (the
#: project's convention for status words, so ordinary prose like "open the menu" does not count) and placed at a
#: bullet's start, at a bold span's start, or right after an emoji/arrow mark. Plus any unchecked or partial box,
#: at any indent, under `-`/`*`/`+`/numbered bullets (R7 sees only a top-level `- [ ]`).
MARK = r"[\u203C\u2049\u2190-\u21FF\u2300-\u23FF\u2460-\u27BF\u2900-\u297F\u2B00-\u2BFF\uFE0F\U0001F000-\U0001FAFF]"
BODY_OPEN_RE = re.compile(
    rf"(?:^[ \t]*(?:>[ \t]*)*(?:[-*+]|\d{{1,9}}[.)])[ \t]+(?:\[[ xX~]\][ \t]+)?(?:{MARK}[ \t]*)*(?:\*\*[ \t]*)?"
    rf"(?:{MARK}[ \t]*)*|\*\*[ \t]*(?:{MARK}[ \t]*)*|{MARK}[ \t]*(?:\*\*[ \t]*)?)(?P<word>\b(?:{OPEN_WORDS})\b)")
OPEN_BOX_RE = re.compile(r"^[ \t]*(?:>[ \t]*)*(?:[-*+]|\d{1,9}[.)])[ \t]+\[[ ~]\]")
#: ⛔ ROUND 3: STATUS WORDS IN ANY POSITION, ANY CASE — a narrow set. The marker-position rule above missed the
#: checker's real 05 caveats "Fights 2-5 remain UNDRIVEN." (mid-sentence) and "⚠ **Unverified claim worth
#: probing:**" (sentence case), and both moved out of the file a cold reader acts from. These words have no
#: ordinary-prose meaning that marks a block DONE, so they keep a block anywhere, in any case; a false hit only
#: skips a block (safe). Also kept: a line-start bare "STILL OPEN" (any case), a `####`-`######` subheading saying
#: OPEN (upper case) or "Open question(s)", and an unchecked/partial box inside a TABLE cell.
BODY_OPEN_ANY_RE = re.compile(
    rf"\b(?:{NARROW_OPEN_WORDS})\b"
    r"|^[ \t]*(?:>[ \t]*)*(?:[-*+][ \t]+)?STILL\s+OPEN\b"
    r"|^[ \t]*#{4,6}[ \t].*?(?:(?-i:\bOPEN\b)|\bopen\s+questions?\b)"
    r"|^[ \t]*(?:>[ \t]*)*\|.*\[[ ~]\]", re.I)
#: The slugs a pointer must keep: `#24-foo` / `#28-trainer-improvements` / `#24-trainmap+`, and `KI-66` / `KI-47b`.
SLUG_RE = re.compile(r"(?<![\w#])#\d{2}-[A-Za-z0-9][A-Za-z0-9+_-]*")
KI_RE = re.compile(r"\bKI-\d+[a-z]?\b")
MAX_HEADING_IN_POINTER = 600
SLUG_LINE_CHARS = 1000
SPLIT_LIMIT = ld.MAX_LINE_CHARS
#: A continuation piece must not start a new block: a bullet, a quote, a heading, an ordered item, a fence, a table
#: row, an HTML block or a thematic break / setext underline would each change what the page shows.
BLOCK_START_RE = re.compile(
    r"^(?:[-+*](?:\s|$)|>|#{1,6}(?:\s|$)|\d{1,9}[.)](?:\s|$)|`{3}|~{3}|\||<|[-_*](?:\s*[-_*]){2,}\s*$|[=-]+\s*$)")
LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-+*]|\d{1,9}[.)])\s+")
#: A blockquote's markers (`> `, `> > `, up to 3 leading spaces each, one optional space after each `>`).
QUOTE_RE = re.compile(r"^(?:[ ]{0,3}>[ ]?)+")


def slugs_in(text: str) -> "set[str]":
    return set(SLUG_RE.findall(text)) | set(KI_RE.findall(text))


@dataclasses.dataclass
class Block:
    start: int              # 0-based index of the `###` heading
    end: int                # exclusive
    heading: str
    reason: "str | None"    # None = selected; else why it is skipped
    saving: int = 0         # LF bytes the move removes from the source (block minus pointer)


def _scan(lines: "list[str]") -> "list[str]":
    """The fence-blanked twin of `lines` (lint_docs' rule, so a `###` in an example is not a heading)."""
    return ld._blank_fenced("\n".join(lines)).split("\n")


def body_open_marker(body: "list[str]") -> "tuple[int, str] | None":
    """(0-based index in `body`, why) of the first line that keeps a block OPEN, else None. `body` is FENCE-BLANKED,
    so an open box or a status word inside a fenced example does not count (the mention rule)."""
    for n, line in enumerate(body):
        if OPEN_BOX_RE.match(line):
            return n, f"holds an open box: {line.strip()[:70]!r}"
        m = BODY_OPEN_RE.search(line)
        if m:
            return n, f"carries the open marker {m.group('word')!r}: {line.strip()[:70]!r}"
        m = BODY_OPEN_ANY_RE.search(line)
        if m:
            return n, f"carries the open status {m.group(0).strip()[:40]!r}: {line.strip()[:70]!r}"
    return None


def find_blocks(lines: "list[str]") -> "list[Block]":
    """Every `###` section R7 counts CLOSED, each with the reason it is skipped (None = it moves)."""
    scan = _scan(lines)
    heads = [i for i, line in enumerate(lines) if line.startswith("### ")]
    r7_end = dict(zip(heads, heads[1:] + [len(lines)]))
    out: "list[Block]" = []
    for i in heads:
        heading = lines[i]
        if not ld.r7_section_is_closed(heading, lines[i:r7_end[i]]):
            continue                        # not closed even by R7: never listed, never moved
        end = next((j for j in range(i + 1, len(lines)) if scan[j].startswith(SWEEP_STOPS)), len(lines))
        block = lines[i:end]
        hit = NOT_CLOSED_RE.search(heading.upper())
        reason = None
        if not scan[i].startswith("### "):
            reason = "inside a fenced block (an example, not a heading)"
        elif "ARCHIVED" in heading.upper():
            reason = "already a pointer (its heading says ARCHIVED)"
        elif hit:
            reason = f"its heading also says {hit.group(0)!r}"
        elif not any(line.strip() for line in block[1:]):
            reason = "no body to move (a heading alone)"
        elif (body := body_open_marker(scan[i + 1:end])) is not None:
            n, why = body
            reason = f"its BODY is not closed: line {i + 2 + n} {why}"
        else:
            # ⭐ THE MOVER MUST SEE THE SAME BLOCK. `find_block` reads RAW lines, so a `#`/`##`/`###` line inside a
            # fence ends ITS block early and the fenced rest would be orphaned under the pointer (invariant B
            # accepts a fenced `## ` as a boundary). Equal spans also mean no raw `### ` lies inside the block,
            # so the block is a prefix of R7's own section and R7's "closed" verdict covers every line it moves.
            # The mover refuses a heading that is not unique (its anchor must match exactly one line).
            try:
                if adb.find_block(lines, heading, SWEEP_STOPS) != (i, end):
                    reason = "the mover's block boundary differs (a heading-like line inside a fence)"
            except SystemExit as exc:
                reason = f"the mover refuses the anchor: {str(exc)[:100]}"
        out.append(Block(i, end, heading, reason))
    return out


def make_pointer(heading: str, block: "list[str]", archive_name: str, date: str) -> str:
    """The text left in the source: the heading's start, the archival claim, and every slug the block held."""
    shown = heading
    if len(shown) > MAX_HEADING_IN_POINTER:
        shown = shown[:MAX_HEADING_IN_POINTER].rsplit(" ", 1)[0] + " …"
    first = (f"{shown} — 📦 ARCHIVED VERBATIM to `{archive_name}` on {date} by `archive_sweep.py` "
             f"(nothing deleted; R7 counted it closed).")
    missing = sorted(slugs_in("\n".join(block)) - slugs_in(first))
    out, line = [first], "Slugs kept for grep:"
    for slug in missing:
        piece = f" `{slug}`," if slug.startswith("#") else f" {slug},"
        if len(line) + len(piece) > SLUG_LINE_CHARS:
            out.append(line.rstrip(","))
            line = "Slugs kept for grep (continued):"
        line += piece
    if missing:
        out.append(line.rstrip(",") + ".")
    return "\n".join(out)


def pointer_arg(lines: "list[str]", b: Block, pointer: str) -> str:
    """What is handed to `archive_block` as the pointer: one blank line kept after it when the block ended with
    one, so the next heading is not glued onto the pointer (`archive_block` replaces the WHOLE span, blanks too)."""
    return pointer + ("\n" if b.end < len(lines) and not lines[b.end - 1].strip() else "")


def simulate(lines: "list[str]", b: Block, pointer: str) -> "list[str]":
    """The source exactly as `archive_block` will write it (its `lines[start:end] = [pointer]`, joined by \\n)."""
    return lines[:b.start] + pointer_arg(lines, b, pointer).split("\n") + lines[b.end:]


def slug_check(lines: "list[str]", b: Block, new_lines: "list[str]") -> "list[str]":
    """S-2: every slug the block held is still in the source as it would be written. Returns the LOST ones."""
    return sorted(slugs_in("\n".join(lines[b.start:b.end])) - slugs_in("\n".join(new_lines)))


def split_line(line: str, limit: int = SPLIT_LIMIT) -> "list[str] | None":
    """S-5: `line` as continuation lines of at most `limit` characters, or None when it cannot be split safely.
    A BLOCKQUOTE line (`> ...`, `> > ...`) is split with its quote markers repeated on every piece, so the paragraph
    stays inside the quote: 13 of 04-HANDOFF's 18 mega-lines were quote lines when this was written (2026-10-21).
    ⛔ The checks below are separate from the cutter (`_cut`) on purpose: a check that shares its code with the
    thing it checks is not a check (archive_doc_block's `_BOUNDARY_FOR_CHECK` lesson)."""
    quote = QUOTE_RE.match(line)
    prefix = quote.group(0) if quote else ""
    body = line[len(prefix):]
    stripped = body.lstrip()
    if stripped.startswith(("#", "|", ">", "<", "```", "~~~")):
        return None                             # heading, table row, nested quote, HTML, fence: never split
    item = LIST_ITEM_RE.match(body)
    lead = re.match(r"\s*", body).group(0)
    if not item and len(lead) >= 4:
        return None                             # could be an indented code block
    pieces = _cut(body, " " * len(item.group(0)) if item else lead, limit - len(prefix))
    if pieces is None or len(pieces) < 2 or any(len(prefix + p) > limit for p in pieces):
        return None
    if any(BLOCK_START_RE.match(p.lstrip()) for p in pieces[1:]):
        return None                             # a continuation would start a new block
    if " ".join(" ".join(p.split()) for p in pieces) != " ".join(body.split()):
        return None                             # the join must give back the original, word for word
    return [prefix + p for p in pieces]


def _cut(line: str, indent: str, limit: int) -> "list[str] | None":
    """Greedy: each piece ends at the LAST `. ` / `; ` / ` - ` before `limit` that leaves a safe continuation."""
    pieces: "list[str]" = []
    rest = line
    while len(rest) > limit:
        best = None
        for sep, keep in ((". ", 1), ("; ", 1), (" - ", 2)):
            at = rest.rfind(sep, 0, limit)
            while at > len(indent):
                head, nxt = rest[:at + keep], rest[at + len(sep):]
                ok = (len(head) <= limit and nxt.strip() and not BLOCK_START_RE.match(nxt)
                      and head.count("`") % 2 == 0 and head.rfind("](") <= head.rfind(")"))
                if ok:
                    break
                at = rest.rfind(sep, 0, at)
            else:
                continue
            if best is None or at + keep > best[0]:
                best = (at + keep, at + len(sep))
        if best is None:
            return None
        pieces.append(rest[:best[0]])
        rest = indent + rest[best[1]:]
    pieces.append(rest)
    return pieces


def split_plan(lines: "list[str]") -> "tuple[dict[int, list[str]], list[tuple[int, int]]]":
    """{line index: pieces} for every mega-line R8 polices that splits safely; (line number, chars) for the rest."""
    text = "\n".join(lines)
    plan, refused = {}, []
    for n, line in ld.long_lines(text):
        pieces = split_line(line)
        if pieces is None:
            refused.append((n, len(line)))
        else:
            plan[n - 1] = pieces
    return plan, refused


def _lf_bytes(lines: "list[str]") -> int:
    return sum(len(line.encode("utf-8")) + 1 for line in lines)


def _archive_header(name: str, source_name: str) -> str:
    title = re.sub(r"^\d{2}-", "", name).rsplit(".", 1)[0].replace("-", " ")
    return (f"# {name[:2]} — {title} (APPEND-ONLY)\n\n"
            f"> Closed `###` blocks of `{source_name}`, moved VERBATIM by `archive_sweep.py` (nothing deleted). "
            f"Append-only history: never rewrite, reorder or delete an entry. Each block's pointer in "
            f"`{source_name}` keeps every slug, so `grep '#slug'` still lands there first.\n")


def plan_sweep(source: pathlib.Path, archive_name: str, date: str) -> "tuple[list[str], list[Block]]":
    """Dry-run every candidate through the REAL mover (invariants A-D) against a scratch archive."""
    lines = source.read_text(encoding="utf-8").splitlines()
    blocks = find_blocks(lines)
    with tempfile.TemporaryDirectory() as tmp:
        scratch = pathlib.Path(tmp) / archive_name
        real = source.parent / archive_name
        scratch.write_text(real.read_text(encoding="utf-8") if real.is_file() else
                           _archive_header(archive_name, source.name), encoding="utf-8")
        for b in blocks:
            if b.reason:
                continue
            pointer = make_pointer(b.heading, lines[b.start:b.end], archive_name, date)
            new_lines = simulate(lines, b, pointer)
            lost = slug_check(lines, b, new_lines)
            if lost:
                b.reason = f"the pointer would lose slug(s) {lost[:6]} — refused (S-2)"
                continue
            try:
                adb.archive_block(source, scratch, b.heading, pointer_arg(lines, b, pointer), "dry run",
                                  dry_run=True, stop_prefixes=SWEEP_STOPS)
            except SystemExit as exc:
                b.reason = f"refused by archive_doc_block: {str(exc).splitlines()[0][:120]}"
                continue
            b.saving = _lf_bytes(lines) - _lf_bytes(new_lines)
    return lines, blocks


def apply_sweep(source: pathlib.Path, archive: pathlib.Path, date: str) -> "list[str]":
    """Move every selected block, one at a time, each re-found on the file as it now stands. Returns a line each."""
    done: "list[str]" = []
    moved_headings: "set[str]" = set()
    while True:
        lines = source.read_text(encoding="utf-8").splitlines()
        todo = [b for b in find_blocks(lines) if b.reason is None and b.heading not in moved_headings]
        if not todo:
            return done
        b = todo[0]
        pointer = make_pointer(b.heading, lines[b.start:b.end], archive.name, date)
        new_lines = simulate(lines, b, pointer)
        lost = slug_check(lines, b, new_lines)
        if lost:
            raise SystemExit(f"⛔ REFUSED before writing: the pointer for {b.heading[:80]!r} would lose slug(s) "
                             f"{lost} — `grep` would no longer land on it (S-2). Nothing written for this block.")
        note = (f"Moved by `archive_sweep.py` on {date}: R7 (`lint_docs.py`) counts this `###` block CLOSED — its "
                f"heading says done, it holds no `- [ ]` / `- [~]` box, and it is not MIXED / STILL OPEN.")
        if not archive.is_file():
            # Created only once a move has passed its slug check, so a refused sweep leaves no new file behind.
            archive.write_text(_archive_header(archive.name, source.name), encoding="utf-8", newline="\n")
            done.append(f"CREATED {archive.name} — ‼ add it to 00-README's reading order (pair P4)")
        adb.archive_block(source, archive, b.heading, pointer_arg(lines, b, pointer), note,
                          stop_prefixes=SWEEP_STOPS)
        written = source.read_text(encoding="utf-8").splitlines()
        if written != new_lines:
            raise SystemExit(f"⛔ TRIPWIRE: the source as written differs from the simulated one after moving "
                             f"{b.heading[:80]!r}. The archive holds the block (invariant A); inspect the diff.")
        moved_headings.add(b.heading)
        done.append(f"MOVED {b.end - b.start} line(s): {b.heading[:100]}")


def _words(lines: "list[str]") -> "list[str]":
    """The file's words with each line's blockquote markers removed. ⛔ Round 2: comparing RAW words refused every
    quote-line split, because `split_line` repeats the `>` marker on each piece (that is what keeps the piece in the
    quote) and every repeated `>` is one more 'word'. 13 of 04's 18 mega-lines were quote lines."""
    return " ".join(QUOTE_RE.sub("", line, count=1) for line in lines).split()


def split_text(lines: "list[str]") -> "tuple[str, list[str]]":
    """(the split file's text, a line per split) — VALIDATED, nothing written. Raises SystemExit on a refusal.
    Two checks, both independent of `split_line`'s own: the file's words (quote markers aside) are unchanged, and
    every piece keeps its original line's quote depth (dropping a `>` would move text out of the quote while
    leaving the words intact)."""
    plan, _ = split_plan(lines)
    out = []
    new = list(lines)
    for i in sorted(plan, reverse=True):
        depth = QUOTE_RE.match(lines[i])
        depth = depth.group(0) if depth else ""
        if not all(piece.startswith(depth) and not QUOTE_RE.match(piece[len(depth):]) for piece in plan[i]):
            raise SystemExit(f"⛔ REFUSED: the split of line {i + 1} changes its blockquote depth — nothing written")
        out.append(f"SPLIT line {i + 1}: {len(lines[i]):,} chars -> {len(plan[i])} lines")
        new[i:i + 1] = plan[i]
    if _words(new) != _words(lines):
        raise SystemExit("⛔ REFUSED: the split file's words differ from the original's — nothing written")
    return "\n".join(new) + "\n", list(reversed(out))


def apply_splits(source: pathlib.Path) -> "list[str]":
    """Split `source`'s mega-lines in place; the whole plan is validated before the one write."""
    new_text, out = split_text(source.read_text(encoding="utf-8").splitlines())
    source.write_text(new_text, encoding="utf-8", newline="\n")
    return out


def _copy(src: pathlib.Path, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())


def _slash_keys(budget_dir: pathlib.Path) -> "set[str]":
    """The `/`-keyed R8 files (e.g. `ai_player/README.md`) of the worktree AND the committed ceilings JSON — the
    files `lint_docs.r8_files` resolves against the folder above the docs, which a rehearsal must copy too."""
    keys: "set[str]" = set()
    try:
        keys |= set((ld._read_json(budget_dir / ld.CEILINGS_NAME) or {}).get("files", {}))
        state, text = ld.head_text(budget_dir / ld.CEILINGS_NAME)
        if state == "ok":
            keys |= set(json.loads(text).get("files", {}))
    except (ValueError, OSError):
        pass                    # an unreadable JSON is R8's failure to report, in the rehearsal's lint
    return {k for k in keys if "/" in k}


def rehearse(source: pathlib.Path, archive: pathlib.Path, date: str, split: bool,
             docs_arg: "pathlib.Path | None" = None, budget_arg: "pathlib.Path | None" = None,
             repo: "pathlib.Path | None" = None) -> "tuple[list[str], list[str], str | None, list[str]]":
    """THE WHOLE --apply, run first on scratch COPIES: (sweep report, the source's lines after the sweep, the split
    text or None, split report). ⛔ Round 2: the sweep used to WRITE the source and create the archive, and only
    then did the split refuse — while its message said "nothing written". Validating the whole plan on copies,
    through the REAL mover and the real split checks, means a refusal happens before any real write, so the
    message is true. Raises SystemExit on any refusal.
    ⛔ ROUND 3: THE REHEARSED RESULT MUST PASS THE LINT. `--apply --split-lines` on 04 (the USAGE example below)
    turned 883 lines into 1,069 against R3's 900-line budget: the rehearsal checked only the mover and the split's
    words, so it PASSED, the real files were written, and Tier 0 went red afterwards (undoing it needs a git
    restore, which the destructive-git hook blocks). Now the COMPLETE would-be result (the swept and split source,
    the archive, both R8 JSON files after their rewaive/ratchet bookkeeping) is built in a temp copy of the docs
    folder and the budget folder, and `lint_docs` runs on it with EVERY rule (R3's line budget included; R8 (d)
    still compares against the REAL folder's committed JSON). A red rule there refuses the apply, naming it."""
    docs_dir = (docs_arg or ld.DOCS).resolve()
    budget_dir = (budget_arg or ld.HERE).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp) / "root"
        docs, budget, other = root / docs_dir.name, pathlib.Path(tmp) / "budget", pathlib.Path(tmp) / "other"
        for p in docs_dir.glob("*.md"):
            if p.is_file():
                _copy(p, docs / p.name)
        for name in (ld.CEILINGS_NAME, ld.WAIVERS_NAME):
            if (budget_dir / name).is_file():
                _copy(budget_dir / name, budget / name)
        for key in _slash_keys(budget_dir):
            if (docs_dir.parent / key).is_file():
                _copy(docs_dir.parent / key, root / key)

        def place(path: pathlib.Path, tag: str) -> pathlib.Path:
            # A file in the docs folder is rehearsed AS that file (so R8's bookkeeping and the lint see it); any
            # other (a scratch copy, an archive elsewhere) gets its own temp spot.
            return docs / path.name if path.parent.resolve() == docs_dir else other / tag / path.name

        src, arc = place(source, "src"), place(archive, "arc")
        arc.parent.mkdir(parents=True, exist_ok=True)       # the mover creates the archive, not its folder
        if not src.is_file():
            _copy(source, src)
        if archive.is_file() and not arc.is_file():
            _copy(archive, arc)
        report = apply_sweep(src, arc, date)
        after = src.read_text(encoding="utf-8").splitlines()
        text, split_report = split_text(after) if split else (None, [])
        if text is not None:
            src.write_text(text, encoding="utf-8", newline="\n")
        quiet = io.StringIO()
        with contextlib.redirect_stdout(quiet):
            _r8_bookkeeping(src, docs, budget)
            rc = ld.main(["--docs-dir", str(docs), "--budget-dir", str(budget), "--repo-dir",
                          str((repo or ld.REPO).resolve()), "--head-budget-dir", str(budget_dir)])
        red = list(ld.failures)
    if rc != 0:
        lines = "\n".join(f"  {f}" for f in red) or "  (lint_docs exited non-zero with no rule named)"
        with contextlib.redirect_stdout(io.StringIO()):     # is the tree red ALREADY? (so the message is true)
            base = ld.main(["--docs-dir", str(docs_dir), "--budget-dir", str(budget_dir), "--repo-dir",
                            str((repo or ld.REPO).resolve())])
        before = (f"\n‼ The tree is ALREADY red before this apply ({len(ld.failures)} failure(s)): run lint_docs.py "
                  f"and fix that first." if base != 0 else "")
        raise SystemExit(f"⛔ REFUSED: the would-be result of this --apply FAILS {len(red)} doc rule(s) — "
                         f"`lint_docs.py` on a rehearsed copy of the docs folder and the R8 budget folder "
                         f"(source, archive and both R8 JSON files as they would be written):\n{lines}{before}")
    return report, after, text, split_report


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="the current-state doc to sweep")
    parser.add_argument("--archive", help="the append-only archive (default: 03 -> 32-..., 04 -> 28-...)")
    parser.add_argument("--apply", action="store_true", help="move (default: a dry run that writes nothing)")
    parser.add_argument("--split-lines", action="store_true", help="with --apply: also split mega-lines (S-5)")
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    parser.add_argument("--docs-dir", type=pathlib.Path, help="R8 bookkeeping: the docs folder (default: the real one)")
    parser.add_argument("--budget-dir", type=pathlib.Path, help="R8 bookkeeping: the JSON folder (default: tools/story-dev)")
    parser.add_argument("--repo-dir", type=pathlib.Path,
                        help="the rehearsal's lint: the root whose bot code R6 scans (default: this repository; tests)")
    args = parser.parse_args(argv)
    source = pathlib.Path(args.source).resolve()
    if not source.is_file():
        parser.error(f"no such file: {source}")
    archive_name = args.archive and pathlib.Path(args.archive).name or DEFAULT_ARCHIVES.get(source.name)
    if not archive_name:
        parser.error(f"no default archive for {source.name}: pass --archive")
    archive = pathlib.Path(args.archive).resolve() if args.archive else source.parent / archive_name

    lines, blocks = plan_sweep(source, archive.name, args.date)
    chosen = [b for b in blocks if b.reason is None]
    print(f"SWEEP {source.name} -> {archive.name}  ({'APPLY' if args.apply else 'DRY RUN: nothing is written'})")
    print(f"  {len(lines):,} lines, {_lf_bytes(lines):,} B (LF). R7 counts {len(blocks)} `###` block(s) closed; "
          f"{len(chosen)} would move, {len(blocks) - len(chosen)} skipped.")
    for b in chosen:
        print(f"  MOVE  line {b.start + 1:>5}  {b.end - b.start:>4} lines  -{b.saving:>8,} B  {b.heading[:90]}")
    for b in blocks:
        if b.reason:
            print(f"  skip  line {b.start + 1:>5}  {b.heading[:60]!r}: {b.reason}")
    saved = sum(b.saving for b in chosen)
    print(f"  TOTAL: {saved:,} B would leave {source.name} ({_lf_bytes(lines) - saved:,} B after)")
    plan, refused = split_plan(lines)
    extra = sum(_lf_bytes(p) for p in plan.values()) - sum(_lf_bytes([lines[i]]) for i in plan)
    print(f"  MEGA-LINES over {SPLIT_LIMIT:,} chars: {len(plan) + len(refused)}; {len(plan)} split safely into "
          f"{sum(len(p) for p in plan.values())} lines (+{extra:,} B of indentation/newlines); {len(refused)} cannot "
          f"(no safe `. `/`; `/` - ` cut, or not prose){': lines ' + ', '.join(str(n) for n, _ in refused[:12]) if refused else ''}"
          f"{' ...' if len(refused) > 12 else ''}")
    if not args.apply:
        print("DRY RUN: nothing changed (--apply to move; --apply --split-lines to split too)")
        return 0

    try:
        _, after, split_text_out, _ = rehearse(source, archive, args.date, args.split_lines,
                                               args.docs_dir, args.budget_dir, args.repo_dir)
    except SystemExit as exc:
        raise SystemExit(f"{exc}\n⛔ REFUSED in the rehearsal on scratch copies, BEFORE any real write: nothing "
                         f"written to {source.name}, {archive.name}, {ld.CEILINGS_NAME} or {ld.WAIVERS_NAME}.") from None
    print("  rehearsal on scratch copies PASSED (every move through the real mover, the split plan validated, and "
          "lint_docs GREEN on the complete would-be result)")
    try:
        for line in apply_sweep(source, archive, args.date):
            print(f"  {line}")
        if split_text_out is not None:
            if source.read_text(encoding="utf-8").splitlines() != after:
                raise SystemExit(f"⛔ TRIPWIRE: {source.name} after the real sweep differs from the rehearsal's — the "
                                 f"split is NOT applied. The sweep's moves above ARE written (the archive holds them).")
            source.write_text(split_text_out, encoding="utf-8", newline="\n")
            print(f"  SPLIT the mega-lines (the plan validated in the rehearsal)")
    finally:
        # Runs after a partial write too: rewaive (no --why) only drops/tightens and ratchet only lowers, so the
        # bookkeeping is safe on whatever was written, and skipping it would leave R8 out of step with the file.
        _r8_bookkeeping(source, args.docs_dir, args.budget_dir)
    print("‼ Now run Tier 0: lint_docs.py AND audit_doc_consistency.py. One sweep per commit, explicit paths.")
    return 0


def _r8_bookkeeping(source: pathlib.Path, docs_arg: "pathlib.Path | None", budget_arg: "pathlib.Path | None") -> None:
    """Shrink-only R8 bookkeeping after a write: the moved and split lines' waivers drop or tighten, and the ceiling
    follows the bytes down, so what the sweep removed cannot silently grow back.
    ⛔ ONLY FOR THE REAL R8 FILE (round 2). Matching on the basename, a sweep of a COPY of 05 in a scratch folder
    re-hashed and RATCHETED the real JSON against the real 05 — a write to the project tree from an experiment."""
    docs_dir = (docs_arg or ld.DOCS).resolve()
    budget_dir = (budget_arg or ld.HERE).resolve()
    ceilings = ld._read_json(budget_dir / ld.CEILINGS_NAME) or {}
    name = next((n for n, p in ld.r8_files(docs_dir, ceilings).items() if p.resolve() == source.resolve()), None)
    if name is None or not ceilings:
        print(f"  R8 not updated (not the real file): {source} is not an R8 file under {docs_dir}"
              f"{'' if ceilings else ' (no ceilings JSON)'}")
        return
    if ld.rewaive(docs_dir, budget_dir, name, "") != 0:
        print("  ‼ R8 waivers NOT updated (see the refusal above); lint_docs will report it")
    ld.ratchet(docs_dir, budget_dir, [name])


if __name__ == "__main__":
    sys.exit(main())
