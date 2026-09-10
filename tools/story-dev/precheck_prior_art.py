# -*- coding: utf-8 -*-
"""BEFORE DESIGNING ANYTHING: has this project already ruled on it, tried it, or killed it?

⛔⛔ WHY THIS EXISTS — THE SAME FAILURE TWICE IN ONE DAY (2026-09-09/10). Both times an argument that
KILLED my design was already written down in this repo, and both times an agent found it, not me:
  1. `06-DECISIONS-LOG.md:267-269` — *"any level-denominated threshold is wrong… tuning it just moves
     which map it is wrong on"* — foreclosing a threshold-widening lead I had spent a workflow on.
  2. `07-CHANGELOG.md` F6 — *"'bench' means only 'do not train' — the mon is still FIELDED"* — which
     kills any fix that benches a mon to stop a refusal, because the refusal is the only gate that
     would have noticed, while the mon stays eligible as a faint replacement.

‼ AND I *DID* RUN THE RULE THE SECOND TIME. I grepped `06-DECISIONS-LOG.md` for `BENCH_SPECIES` and
for "bench by role" and got one hit each. **The killing argument was in a DIFFERENT FILE under
DIFFERENT WORDS** ("still FIELDED"). ⇒ the rule was not wrong, my SEARCH was too narrow: I searched
for the SYMBOL I intended to change, not for the MECHANISM I intended to rely on.

⭐ WHAT THIS TOOL DOES. Given the symbols AND the mechanism words of a proposed change, it sweeps
every history file (`05-KNOWN-ISSUES`, `06-DECISIONS-LOG`, `07-CHANGELOG`, `08-MISTAKES`) plus the
punch list, and prints each hit WITH CONTEXT and a loud banner for the phrasings that signal a
verdict — REJECTED / UNSAFE / REFUTED / KILLED / DO NOT / decided / superseded.
⇒ **Run it before proposing a fix, and read every hit.** It costs one command; not running it has
now cost two workflows.

USAGE
    py -3.12 precheck_prior_art.py BENCH_SPECIES bench fielded "faint replacement"
    py -3.12 precheck_prior_art.py TRAIN_CATCHUP_GAP threshold window level-denominated

Always exits 0 — an ADVISORY tool. It cannot know which hit matters; that is the reader's job.
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
DOCS = pathlib.Path(__file__).resolve().parent.parent.parent / "PROJECT KNOWLEDGE"
FILES = ("05-KNOWN-ISSUES.md", "06-DECISIONS-LOG.md", "07-CHANGELOG.md", "08-MISTAKES.md",
         "03-PUNCH-LIST.md")

#: ⛔⛔ `ai-research-notes/` IS SEARCHED TOO, AND IT WAS THE TOOL'S OWN BLIND SPOT (fixed 2026-09-10).
#:
#: MEASURED: I ran this tool on the §Ch24 entry-marker question, got **0 hits across all five files**,
#: reported "no prior art", and commissioned a four-agent decomp round. A refuter then found the
#: identical recommendation ALREADY WRITTEN DOWN in
#:   `ai-research-notes/2026-09-07-ch24-elite-four-BUILD-SPEC.md:70`  and
#:   `ai-research-notes/2026-09-08-ch24-league-RECON.md:39`
#: ⇒ the tool did not disagree with those notes; **it could not see them.**
#:
#: ‼ THE IRONY IS THE LESSON, AND IT IS WHY THIS COMMENT IS LONG. This file's own header records that
#: it exists because a search was TOO NARROW ("the rule was not wrong, my SEARCH was too narrow").
#: It then shipped with a too-narrow search of its own. ⇒ **A TOOL THAT ENFORCES A RULE IS NOT
#: EXEMPT FROM THAT RULE**, and the exemption is invisible precisely because the tool answers
#: confidently either way — 0 hits reads as "nobody has been here", never as "I did not look there".
#:
#: ⭐ Research notes are exactly where a design gets WORKED OUT before it is ruled on, so they are the
#: likeliest place to hold the argument that kills a proposal. They are NOTES, never truth (that rule
#: is unchanged) — but a note you have not read cannot be weighed at all.
NOTES_DIR = "ai-research-notes"
#: phrasings that mean "someone already ruled on this" — a hit carrying one of these is a VERDICT,
#: not a mention, and is what the reader must not skim past.
VERDICT = re.compile(
    r"\b(rejected|unsafe|refuted|killed|superseded|do not|don't|never|decided|ruling|foreclos\w*|"
    r"abandoned|dead end|withdrawn|walked back)\b", re.I)


def main() -> int:
    terms = [t for t in sys.argv[1:] if t.strip()]
    if not terms:
        print(__doc__.split("USAGE")[1].strip())
        return 0
    print("=" * 100)
    print(f"PRIOR ART for: {', '.join(repr(t) for t in terms)}")
    print("=" * 100)

    total = verdicts = 0
    # ⛔ The five current-state/history files FIRST (a ruling outranks a note), then every research
    # note — sorted so the output order is stable and a newer note is not silently preferred.
    targets = [(n, DOCS / n) for n in FILES]
    notes_dir = DOCS / NOTES_DIR
    note_files = sorted(notes_dir.glob("*.md")) if notes_dir.is_dir() else []
    targets += [(f"{NOTES_DIR}/{p.name}", p) for p in note_files]
    if not note_files:
        print(f"\n⚠ {NOTES_DIR}/ HAS NO NOTES (or is missing) — the search is NARROWER than it looks.")

    for name, p in targets:
        if not p.exists():
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        hits = []
        for i, line in enumerate(lines):
            low = line.lower()
            matched = [t for t in terms if t.lower() in low]
            if matched:
                hits.append((i, line, matched))
        if not hits:
            # ⛔ A SILENT MISS IS THE DEFECT THIS FIX EXISTS FOR, so the five ruling files ALWAYS
            # report "no hits" explicitly. The research notes do not: there are dozens, and thirty
            # "no hits" lines would bury the one that matters — the noise would teach the reader to
            # skim, which is how a tool with a blind spot and a tool nobody reads end up equivalent.
            # The scanned-notes COUNT is printed in the footer instead, so coverage stays visible.
            if not name.startswith(NOTES_DIR):
                print(f"\n--- {name}: no hits")
            continue
        print(f"\n--- {name}: {len(hits)} hit(s)")
        for i, line, matched in hits[:40]:
            total += 1
            # a verdict word within a few lines of the hit makes it load-bearing
            window = "\n".join(lines[max(0, i - 4):i + 5])
            flag = ""
            if VERDICT.search(window):
                flag = "  ⛔ VERDICT WORD NEARBY — READ THE SURROUNDING ENTRY IN FULL"
                verdicts += 1
            print(f"  {name}:{i + 1}  [{'+'.join(matched)}]{flag}")
            print(f"      {line.strip()[:150]}")
        if len(hits) > 40:
            print(f"      … {len(hits) - 40} more hit(s) not shown — narrow your terms")

    print("\n" + "=" * 100)
    print(f"  {total} hit(s) shown, {verdicts} sitting near a VERDICT word.")
    # ⛔ COVERAGE IS PART OF THE ANSWER. "0 hits" means nothing unless you know WHAT WAS SEARCHED —
    # that ambiguity is exactly what let this tool report "no prior art" over a recommendation that
    # was already written down in a directory it never opened (2026-09-10).
    print(f"  scanned: {len(FILES)} ruling file(s) + {len(note_files)} research note(s) "
          f"in {NOTES_DIR}/.")
    if note_files:
        print("  ⚠ A RESEARCH NOTE IS A NOTE, NEVER TRUTH — but an argument you have not READ")
        print("     cannot be weighed. A hit there means someone already worked this out.")
    print("  ⛔ SEARCH THE MECHANISM, NOT ONLY THE SYMBOL. The argument that kills a design is")
    print("     usually phrased in terms of what the design RELIES ON, not what it CHANGES —")
    print("     'still FIELDED' killed a bench fix that no `BENCH_SPECIES` grep would ever find.")
    print("  ⭐ A hit near a verdict word is not a hint. Open the entry and read it to its end.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
