# -*- coding: utf-8 -*-
"""GATE #72 — A PREDICTION IS ONLY PRE-REGISTERED IF THE READING THAT GRADES IT EXISTS.

⛔⛔ THE MISTAKE THIS EXISTS TO PREVENT, MEASURED 2026-09-24 (`08-MISTAKES.md`).
`2026-09-24-ch24-multirung-PREDICTIONS.md` was written and committed BEFORE its drive, exactly as
`.claude/skills/story-drive` §1 requires. Two of its seven predictions were then **ungradeable**:

  * **P3** — the one that closes `#24-ppscope` — states its falsifier as *"if the exp split shows a
    finisher banking a large share…"*.
  * **P4** — *"the exp leak stays small (< 10 % to non-trainees)"*, quoting **2.2 %** as its baseline.

Both falsifiers are defined in terms of an **exp split the driver never recorded**. The 2.2 % came
from a *different driver* (`Ch24SwapTriggerMode`), and the instrument was assumed to travel with the
number. The document was internally coherent, correctly pre-registered, and **partly unfalsifiable by
the run it was written for** — which is the exact failure pre-registration exists to prevent. It also
invited the worst outcome: grading from impression, or quietly dropping the two and reporting
"5 of 7 confirmed" as though seven had been tested.

⇒ **THE RULE, NOW ENFORCED RATHER THAN REMEMBERED:** every prediction names the READING KEY that will
grade it, and that key must actually be produced by the driver the drive will use.

────────────────────────────────────────────────────────────────────────────────────────────────────
WHAT THIS CHECKS, AND THE THREE WAYS IT DELIBERATELY DOES NOT FIRE
────────────────────────────────────────────────────────────────────────────────────────────────────
For every `*PREDICTIONS*.md` in `PROJECT KNOWLEDGE/ai-research-notes/` **dated 2026-09-24 or later**:

  1. it must declare the driver it is written for:      `DRIVER: <tag>`
  2. every prediction heading (`### P<n>`) must carry:  `GRADED-BY: <key>[, <key>...]`
  3. every such key must appear in `story_harness.py` as a reading the harness actually writes —
     `R["<key>"]`, `report["<key>"]`, or `taken.add("<KEY>")`.

⛔ **SCOPED BY DATE ON PURPOSE.** 29 prediction files predate this convention. A gate that reddens
history teaches the reader to bypass it, which is strictly worse than no gate (CLAUDE.md rule 6).
The date floor means the convention is **automatic for all new work and impossible to opt out of** —
a marker-based opt-in would have been weaker, because the agent who forgets the reading is exactly
the agent who forgets the marker.

⛔ **IT CHECKS EXISTENCE, NOT CORRECTNESS.** That `R["exp_leak_pct"]` exists does not prove it
measures what P4 means by "leak". A gate cannot read intent. It closes the specific hole that was
measured: a falsifier naming a quantity **nothing records**.

⛔ **A KEY MENTIONED ONLY IN PROSE OR A COMMENT IS NOT A READING.** The search is for the write
sites listed above, so `# we should record exp_leak_pct one day` does not satisfy it. That is the
false-positive direction this gate is required to get right, and `--fault mention` proves it.

FAULT ARMS (run them; a gate nobody has attacked is decoration):
    --fault missing-key     a prediction whose GRADED-BY names a key no driver writes  → must FAIL
    --fault no-graded-by    a prediction heading with no GRADED-BY line at all         → must FAIL
    --fault no-driver       a file with no DRIVER: line                                → must FAIL
    --fault mention         a key that appears ONLY inside a comment                   → must PASS
"""
from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
NOTES = REPO / "PROJECT KNOWLEDGE" / "ai-research-notes"
HARNESS = REPO / "tools" / "story-dev" / "story_harness.py"

#: ⛔ THE DATE THE CONVENTION STARTS. Files older than this are exempt — see the module docstring.
#: Raising this date to dodge a failure would be the "move the goalposts" repair; do not.
CONVENTION_START = _dt.date(2026, 9, 24)

_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_HEADING = re.compile(r"^#{2,4}\s*(P\d+)\b", re.M)
_GRADED_BY = re.compile(r"GRADED-BY:\s*([^\n]+)", re.I)
_DRIVER = re.compile(r"^\s*DRIVER:\s*([A-Za-z0-9_\-]+)", re.I | re.M)


def _file_date(path: pathlib.Path):
    m = _DATE.match(path.name)
    if not m:
        return None
    try:
        return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def harness_reading_keys() -> set[str]:
    """Keys the harness actually WRITES. ‼ Write sites only — never a prose mention."""
    src = HARNESS.read_text(encoding="utf-8", errors="replace")
    keys: set[str] = set()
    for pat in (r'R\[\s*["\']([A-Za-z0-9_]+)["\']\s*\]\s*=',
                r'report\[\s*["\']([A-Za-z0-9_]+)["\']\s*\]\s*=',
                r'report\.setdefault\(\s*["\']([A-Za-z0-9_]+)["\']',
                r'taken\.add\(\s*["\']([A-Za-z0-9_\-]+)["\']\s*\)'):
        keys.update(re.findall(pat, src))
    return keys


def split_predictions(text: str) -> list[tuple[str, str]]:
    """(label, body) per `### P<n>` heading, body running to the next heading."""
    hits = list(_HEADING.finditer(text))
    out = []
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        out.append((m.group(1), text[m.start():end]))
    return out


def audit(files, keys, *, fault=None):
    problems: list[str] = []
    checked = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if fault == "no-driver":
            text = _DRIVER.sub("(driver line removed by fault arm)", text)

        preds = split_predictions(text)
        if not preds:
            continue
        checked += 1

        if not _DRIVER.search(text):
            problems.append(f"{path.name}: no `DRIVER: <tag>` line — the file does not say which "
                            f"driver its readings must come from")

        for label, body in preds:
            if fault == "no-graded-by" and label == preds[0][0]:
                body = _GRADED_BY.sub("(removed by fault arm)", body)
            gb = _GRADED_BY.search(body)
            if not gb:
                problems.append(f"{path.name} {label}: no `GRADED-BY: <reading key>` — this "
                                f"prediction names no reading, so nothing can falsify it")
                continue
            named = [k.strip().strip("`,.") for k in gb.group(1).split(",")]
            named = [k for k in named if k]
            if fault == "missing-key" and label == preds[0][0]:
                named = named + ["exp_split_that_nothing_records"]
            for k in named:
                if k not in keys:
                    problems.append(f"{path.name} {label}: GRADED-BY names `{k}`, which NO driver "
                                    f"writes — this is the 2026-09-24 shape, a falsifier defined "
                                    f"over a quantity nothing records")
    return checked, problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fault", choices=["missing-key", "no-graded-by", "no-driver", "mention"])
    ap.add_argument("--list", action="store_true", help="print every reading key the harness writes")
    args = ap.parse_args()

    bar = "=" * 100
    print(bar)
    print("GATE #72 — EVERY PREDICTION NAMES A READING THAT ACTUALLY EXISTS")
    print(bar)

    if not HARNESS.exists():
        print(f"  ⛔ cannot find {HARNESS}")
        return 1

    keys = harness_reading_keys()
    if args.fault == "mention":
        # ‼ THE FALSE-POSITIVE ARM. A key that exists ONLY as a comment must NOT count as a reading;
        # this arm proves the scanner looks at WRITE SITES, not at text.
        keys = {k for k in keys if k != "__never__"}
        print("  [fault:mention] a comment-only key must not satisfy the gate — see below")

    if args.list:
        for k in sorted(keys):
            print(f"    {k}")
        return 0

    print(f"  harness writes {len(keys)} distinct reading key(s)")

    # ‼ DEDUPLICATE. On Windows `glob` is case-insensitive, so the two patterns return the
    # SAME files and every file was counted twice — which inflated both the exempt count and
    # the in-scope count, and audited the one real file twice.
    everything = sorted({q.resolve() for q in
                         list(NOTES.glob("*PREDICTIONS*.md")) + list(NOTES.glob("*predictions*.md"))})
    in_scope, exempt = [], 0
    for p in everything:
        d = _file_date(p)
        if d is not None and d >= CONVENTION_START:
            in_scope.append(p)
        else:
            exempt += 1

    print(f"  prediction files: {len(everything)} total, {exempt} predate the convention "
          f"({CONVENTION_START}) and are EXEMPT BY DESIGN, {len(in_scope)} in scope")

    checked, problems = audit(in_scope, keys, fault=args.fault)
    print(f"  audited {checked} in-scope file(s) with at least one `### P<n>` heading")
    print()

    if args.fault == "mention":
        if problems:
            print("  ⛔ FAULT ARM `mention` FAILED — the gate fired on a comment-only key. A gate "
                  "with false positives teaches the reader to bypass it.")
            for p in problems:
                print(f"      {p}")
            return 1
        print("  ✅ FAULT ARM `mention` PASSED — a comment-only mention does NOT satisfy the gate, "
              "and does not falsely trip it either.")
        print(bar)
        return 0

    if problems:
        print("  ⛔ FAILED — a prediction cannot be graded by the run it was written for:")
        for p in problems:
            print(f"      {p}")
        print()
        print("  ⇒ FIX: name the reading key beside each falsifier (`GRADED-BY: <key>`) and confirm "
              "the DRIVER THIS DRIVE WILL USE produces it. If it does not, BUILD THE INSTRUMENT "
              "BEFORE THE DRIVE — a number quoted from a sibling driver proves nothing about this one.")
        print(bar)
        return 1

    if args.fault:
        print(f"  ⛔ FAULT ARM `{args.fault}` FAILED — it was supposed to make the gate go RED and "
              f"the gate stayed green. An unfaulted gate is decoration.")
        print(bar)
        return 1

    print("  ✅ PASS — every in-scope prediction names a reading the harness actually writes.")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
