# -*- coding: utf-8 -*-
"""ONE-OFF: split `ai_player/README.md` into its CURRENT part and one history file per moved section. A DRY RUN by default.

(spec S2-1, backlog P9, 2026-10-21: `ai-research-notes/2026-10-19-BUILD-SPECS-steps-1-2.md`)

WHY. The README is ~514 KB, and most of it is the record of finished build steps (each step's proofs, verifier rounds
and fixes). Every agent that opens it to find how to RUN the AI player pays for all of it. The spec keeps the
current part (~90 KB target) and moves the rest VERBATIM, in order, to `ai_player/readme/NN-<slug>.md`, leaving one
line in its place:
    > moved: <heading> -> readme/NN-<slug>.md
so the README still says what moved and where, and `grep` over `ai_player/` still finds every word.

WHAT STAYS (`KEEP`, written from the REAL README's `##` headings on 2026-10-21 — the spec left the list to the builder,
UNVERIFIED): everything before the first `##` (the title and the "where it is now" text), and the sections a user
or agent needs to run and trust the program today: Run it, Layout, The purity contract, Fault and control switches,
and EVERY "Known limits of ..." section. ⛔ The known limits stay on purpose although they cost ~32 KB over the 90 KB
target: a limit is a CAVEAT, and moving caveats out of the page people read is the trim CLAUDE.md rule 2 forbids
("the headline carries the caveat"). Narrowing KEEP is a decision for the user/orchestrator, made on the printed sizes.

GUARANTEES, checked BEFORE anything is written (nothing is written on a refusal):
  * INVARIANT A (archive_doc_block's): every non-blank line of the README is in the new README or a moved file.
  * P9-4, stronger: substituting each `> moved:` line by its file gives back the original README EXACTLY (order and
    blank lines included), and after `--apply` the same check is re-run on what was written.
  * Refuses a KEEP heading the README does not have (a stale allowlist must not silently move a renamed section), a
    fence that never closes (its `##` lines could not be told from examples), a `readme/` folder that already holds
    files, and an original line that already looks like a `> moved:` pointer.

THE CONSUMERS (the same commit): `ai_player/gates/prune_evidence.py` CITING, `disk_budget.citing_text` and
`check_lessons.DOCUMENTS["README"]` read `ai_player/readme/**/*.md` too, so a citation or a quoted lesson origin that
moved is still found (selftest_lint_docs.py P9-1..P9-4). After `--apply`, give R8 the README's current part:
`lint_docs.py --raise ai_player/README.md --to <bytes> --why "the README's current part after the P9 split"`.

USAGE
    py -3.12 tools/story-dev/split_readme.py                 (dry run: the plan and the sizes)
    py -3.12 tools/story-dev/split_readme.py --apply         (writes ai_player/readme/*.md, then the README)
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import lint_docs as ld  # noqa: E402  (the fence rule, one copy)

README = REPO / "ai_player" / "README.md"
#: The `##` headings that STAY (exact text after "## "), measured from the real README on 2026-10-21.
KEEP = (
    "Run it",
    "Layout",
    "The purity contract",
    "Fault and control switches",
    "Known limits of step 3",
    "Known limits of step 2",
    "Known limits of step 1.1",
    "Known limits of step 1",
    "Known limits of step 0.1",
)
POINTER_RE = re.compile(r"^> moved: (?P<heading>.+) -> readme/(?P<name>\d{2}-[a-z0-9-]+\.md)$")


def slug(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")[:60].rstrip("-") or "section"


def plan_split(text: str, keep: "tuple[str, ...] | None" = None) -> "tuple[str, list[tuple[str, str, str]]]":
    """(the new README text, [(file name, heading, content)]). Raises SystemExit on any refusal.
    `keep` defaults to KEEP read at CALL time (a default argument would freeze it at import)."""
    keep = KEEP if keep is None else keep
    lines = text.split("\n")
    scan = ld._blank_fenced(text).split("\n")
    has_fence = any(line.lstrip().startswith(("```", "~~~")) for line in lines)
    if has_fence and scan == lines:
        raise SystemExit("⛔ REFUSED: a fence never closes, so a `## ` line cannot be told from an example")
    if any(POINTER_RE.match(line) for line in lines):
        raise SystemExit("⛔ REFUSED: the README already holds a `> moved:` line — split once, or the reconstruction "
                         "check could not tell a pointer from text")
    heads = [i for i, line in enumerate(scan) if line.startswith("## ")]
    names = [lines[i][3:].strip() for i in heads]
    stale = [k for k in keep if k not in names]
    if stale:
        raise SystemExit(f"⛔ REFUSED: KEEP names heading(s) the README does not have: {stale}. A renamed section "
                         f"would be MOVED silently; update KEEP from the real headings first.")
    out = lines[:heads[0]] if heads else lines[:]
    moved: "list[tuple[str, str, str]]" = []
    for at, start in enumerate(heads):
        end = heads[at + 1] if at + 1 < len(heads) else len(lines)
        section = lines[start:end]
        if names[at] in keep:
            out += section
            continue
        cut = len(section)
        while cut > 1 and not section[cut - 1].strip():
            cut -= 1
        name = f"{len(moved) + 1:02d}-{slug(names[at])}.md"
        moved.append((name, names[at], "\n".join(section[:cut]) + "\n"))
        out += [f"> moved: {names[at]} -> readme/{name}"] + section[cut:]
    new_text = "\n".join(out)
    check(text, new_text, {name: content for name, _, content in moved})
    return new_text, moved


def reconstruct(new_text: str, files: "dict[str, str]") -> str:
    """P9-4: every `> moved:` line replaced by its file's content (without the file's final newline)."""
    out = []
    for line in new_text.split("\n"):
        m = POINTER_RE.match(line)
        out.append(files[m["name"]][:-1] if m else line)
    return "\n".join(out)


def check(original: str, new_text: str, files: "dict[str, str]") -> None:
    """INVARIANT A and the exact reconstruction (P9-4). Raises SystemExit; called before any write."""
    have = collections.Counter(line for line in new_text.split("\n") if line.strip() and not POINTER_RE.match(line))
    for content in files.values():
        have.update(line for line in content.split("\n") if line.strip())
    need = collections.Counter(line for line in original.split("\n") if line.strip())
    lost = need - have
    if lost:
        raise SystemExit(f"⛔ CONTENT WOULD BE LOST (invariant A) — refusing to write: {list(lost)[:5]}")
    if reconstruct(new_text, files) != original:
        raise SystemExit("⛔ THE SPLIT DOES NOT RECONSTRUCT THE ORIGINAL (P9-4: order or blank lines changed) — "
                         "refusing to write")


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--readme", type=pathlib.Path, default=README)
    parser.add_argument("--apply", action="store_true", help="write (default: a dry run that writes nothing)")
    args = parser.parse_args(argv)
    readme = args.readme.resolve()
    text = readme.read_text(encoding="utf-8")
    new_text, moved = plan_split(text)
    folder = readme.parent / "readme"
    size = lambda s: len(s.encode("utf-8"))  # noqa: E731
    print(f"SPLIT {readme.name} ({'APPLY' if args.apply else 'DRY RUN: nothing is written'})")
    print(f"  before {size(text):,} B; the current part after {size(new_text):,} B (target ~90 KB, spec S2-1); "
          f"{len(moved)} section(s) move, {sum(size(c) for _, _, c in moved):,} B")
    kept = [line[3:].strip() for line in new_text.split("\n") if line.startswith("## ")]
    print(f"  KEEP ({len(kept)}): {kept}")
    for name, heading, content in moved:
        print(f"  MOVE {size(content):>8,} B  readme/{name}  <- ## {heading}")
    print("  invariant A (no non-blank line lost) and the exact reconstruction: VERIFIED before writing")
    if not args.apply:
        print("DRY RUN: nothing changed (--apply to write)")
        return 0
    if folder.exists() and any(folder.iterdir()):
        raise SystemExit(f"⛔ REFUSED: {folder} already holds files — this is a one-off; nothing written")
    folder.mkdir(exist_ok=True)
    for name, _, content in moved:
        (folder / name).write_text(content, encoding="utf-8", newline="\n")
    readme.write_text(new_text, encoding="utf-8", newline="\n")
    written = {name: (folder / name).read_text(encoding="utf-8") for name, _, _ in moved}
    check(text, readme.read_text(encoding="utf-8"), written)
    print(f"APPLIED: {len(moved)} file(s) in {folder}; README re-checked against the original after writing.")
    print(f"‼ R8: `lint_docs.py --raise ai_player/README.md --to <bytes> --why ...` gives its current part a ceiling.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
