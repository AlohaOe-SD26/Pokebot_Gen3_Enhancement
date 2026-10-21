"""Enforce the PROJECT KNOWLEDGE documentation rules MECHANICALLY. No emulator — seconds.

‼‼ WHY THIS EXISTS — the central finding of the 2026-08-11 review
(`PROJECT KNOWLEDGE/26-REVIEW-AND-HARDENING-PLAN-2026-08-11.md`):

    Of 164 logged mistakes in 26 days, **at least 12 are self-admitted REPEATS**, and several were
    committed while the author knew the rule — *"having already written the rule against it"*,
    *"an hour after writing a rule against exactly that"*, *"the second time"*, *"THIRD removal-
    shaped feature in a week"*.

**An advisory rule in a document has a measurably poor prevention rate.** What actually held were
the rules converted into code that REFUSES — 87 `repro_*.py`, 51 hard-failing scripts, and
`gemini_relay.py`, whose own comment records that a doc rule failed where code succeeded.

This linter converts `CLAUDE.md`'s documentation rules into that shape. It **exits 1**.

‼ DESIGN RULE: PRECISION OVER COVERAGE. A linter with false positives gets ignored, and an ignored
linter is an advisory rule with extra steps. Every check here is exact and mechanically decidable;
fuzzy things (is this claim supported? is this rate meaningful?) are deliberately left to humans and
reported as INFO, never as failures.

RULES ENFORCED (failures):
  R1  a CURRENT-STATE file (01-05) must contain no `# HISTORY` block
  R2  a CURRENT-STATE file must contain at most ONE "START HERE" / "YOU ARE HERE" banner
  R3  a CURRENT-STATE file must stay under its line budget
  R4  no two PROJECT KNOWLEDGE docs may share a leading NN- number
  R5  every file named in 00-README's reading order must exist
  R6  every `POKEBOT_*` flag in bot code appears in 29-DISABLED-FEATURES-REGISTRY.md
  R7  a current-state file's CLOSED/ARCHIVED share stays under its budget (R3's intent, measured
      directly rather than by line count — see CLOSED_FRACTION_BUDGET)
  R8  (spec S2-1, 2026-10-21) BYTES, built as a RATCHET, on 00-README + 01-05: (a) each file is at
      most its ceiling in `doc_size_ceilings.json`; (b) no line over 1,200 characters outside fences
      (table rows INCLUDED) unless waived in `long_line_waivers.json` by the hash of its first 60
      characters AND its last 60 (`tails`), and a waived line may only SHRINK; (c) a waiver whose
      line is gone is STALE (a failure); (d) the ceilings and waivers may only shrink against
      `git show HEAD:` — a raise needs a `raised` record and a waiver's growth or new tail a
      `history` record, each printed so Tier 1 sees it in the diff. See the R8 block below.

REPORTED AS INFO (never fails the run):
  I1  count of completed `- [x]` items sitting in the punch list
  I2  count of `- [~]` partial items that do not say what remains

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 lint_docs.py
      PYTHONUTF8=1 py -3.12 lint_docs.py --list   # show every offending line, for fixing
  R8's maintenance modes (each prints every change; the JSON diff is what a reviewer reads):
      py -3.12 lint_docs.py --ratchet [FILE ...]          lower ceilings to max(target, size + headroom)
                                                          and tighten live waivers; NEVER raises
      py -3.12 lint_docs.py --rewaive FILE [--why TEXT]   after editing a waived mega-line: re-hash it,
                                                          record its growth (needs --why), drop stale ones
      py -3.12 lint_docs.py --raise FILE --to BYTES --why TEXT   a recorded ceiling raise (FILE may be a
                                                          repo-relative path such as ai_player/README.md:
                                                          that ADDS the file to R8 with a first ceiling)
      py -3.12 lint_docs.py --seed                        first commit only: ceilings + waivers of today
  Tests run it on a synthetic tree with `--docs-dir DIR --budget-dir DIR` (selftest_lint_docs.py).
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import json
import pathlib
import re
import subprocess
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")

from collections import defaultdict

# This linter prints U+203C/U+26D4 markers on its FAILURE path. On a bare Windows console (cp1252)
# an unconfigured stdout raises UnicodeEncodeError there -- so the linter crashes with a codec
# traceback INSTEAD OF SHOWING THE VIOLATION IT FOUND (observed 2026-09-01: a real R3 over-budget
# finding was nearly missed this way). run_gates.py sets PYTHONUTF8=1 and never saw it; a direct
# `python lint_docs.py` did. Force UTF-8 on our own streams so a finding is always legible.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
DOCS = REPO / "PROJECT KNOWLEDGE"

# ‼ From CLAUDE.md: "01, 02, 03, 04, 05 are CURRENT-STATE files: edit them in place so they always
# describe present reality. Remove stale content." 06/07/08 are APPEND-ONLY history and are exempt.
CURRENT_STATE = ("01-", "02-", "03-", "04-", "05-")

# Budgets are generous — the point is to catch an ARCHIVE forming inside a current-state file, not
# to police prose. 04-HANDOFF was 3,239 lines with only its first 163 current when this was written.
#: ⛔ 03 WENT 3600 -> 4200 ON 2026-09-08, ON A MEASUREMENT, NOT A PREFERENCE. R3's message says "an
#: archive is forming inside a current-state file"; for 03 that was measurably false — 78.5% of it is
#: OPEN sections (46 of them) and only **6.8%** is closed-or-archived. The budget had become a proxy
#: for staleness that was instead measuring BACKLOG, and satisfying it meant deleting detail from
#: open items. ⭐ The intent is now enforced DIRECTLY by R7 below, so this ceiling is a backstop
#: rather than the guard. ‼ If you are tempted to raise it again, run R7 first: if the closed
#: fraction has grown, the file really IS becoming an archive and trimming is the right answer.
#: ⛔ 05 WENT 3000 -> 4000 ON 2026-09-16, ON A MEASUREMENT AND A USER RULING, NOT A PREFERENCE —
#: and it followed the instruction the 03 block above leaves for exactly this moment ("run R7 first").
#: R7 WAS RUN. 05 measured **49.3% closed** against the 41.1% recorded here, i.e. the closed share HAD
#: grown ⇒ by that instruction the file really was becoming an archive and TRIMMING was the right
#: answer. So trimming came FIRST: five fixed-driven-AND-PROMOTED issues (KI-93/94/95/96/97) were
#: retired to `31-KNOWN-ISSUES-ARCHIVE.md` with `archive_doc_block.py`, taking 05 from 3000 -> 2675.
#: ‼ WHY THE RETENTION CONDITION HAD EXPIRED: the 2026-07-29 user ruling retains fixed issues *until
#: they are PROMOTED*. `promote.py --check` now measures drift 0, so those five were promoted and the
#: condition no longer held. The file had grown because nothing re-checked that trigger after the
#: promotions happened — not because anyone was careless.
#: ⭐ THE RAISE IS FOR THE **OPEN BACKLOG**, which is the same thing 03's raise was for: after
#: trimming, 05 is 2675 lines and 55.1% of it is OPEN work. A ceiling that forces the next agent to
#: delete detail from LIVE issues is the failure 03 already paid for.
#: ⛔ AND THE CEILING IS NOW A BACKSTOP, NOT THE GUARD — R7 below applies to 05 as of 2026-09-16, so
#: the INTENT (is an archive forming?) is measured directly. Same architecture as 03.
#: ⛔ 03 WENT 4200 -> 4400 ON 2026-09-16, BY THE SAME PROCEDURE AND WITH THE SAME ANSWER.
#: R7 was run FIRST, as the 2026-09-08 block above instructs. 03 measures **4.1% closed** — DOWN
#: from the 6.8% recorded there, against a 25% budget — with **189 open items**. The closed
#: share SHRANK, so the file is not becoming an archive; R3 is again measuring BACKLOG, which is
#: exactly the condition under which raising is right and trimming would mean deleting detail
#: from live items. ‼ Contrast 05 on the same day: ITS closed share had GROWN (41.1% -> 49.3%),
#: so it was TRIMMED first and only then raised. Same rule, opposite actions, because the
#: measurement differed — which is the whole point of measuring instead of preferring.
LINE_BUDGET = {"01-": 700, "02-": 700, "03-": 4400, "04-": 900, "05-": 4000}

#: R7 — the share of a current-state file that may be CLOSED or ARCHIVED content.
#: ⛔ DELIBERATELY NOT APPLIED TO EVERY FILE. 03 measures 6.8% today, so 25% is ~4x headroom and
#: still fires long before the file rots.
#: ⭐ 05 JOINED ON 2026-09-16, AND ITS BUDGET IS DELIBERATELY LOOSE BECAUSE A USER RULING MAKES IT SO.
#: This block previously said 05 must NOT have an R7 budget, because it "measures 41.1% closed and
#: that is CORRECT: the 2026-07-29 user ruling retains fixed issues until they are PROMOTED. Adding
#: it here would red the suite for a user-approved state — a gate that cries wolf is worse than
#: none." ‼ THAT REASONING STILL STANDS AND IS WHY THE NUMBER IS 0.55 RATHER THAN 0.25. What changed
#: is that leaving 05 ungated let the share drift 41.1% -> 49.3% with nothing to notice. After
#: retiring five promoted issues it measures **44.9%**, so 0.55 is ~10 points of headroom over a
#: user-approved state and still fires long before the file is majority-archive.
#: ⛔ DO NOT TIGHTEN THIS TO 0.25 TO "MATCH 03". 05 is not 03: the ruling deliberately retains closed
#: issues here, so a 03-shaped budget would be red on arrival — the exact cry-wolf this block was
#: originally written to prevent.
#: ‼ FAULT-TESTED 2026-09-16: with the budget temporarily set to 0.40 (below the measured 44.9%) R7
#: FIRES on 05; at 0.55 it passes. A gate that cannot be shown to fire is not a gate.
CLOSED_FRACTION_BUDGET = {"03-": 0.25, "05-": 0.55}

def _blank_fenced(text: str) -> str:
    """Return `text` with the CONTENTS of ``` fenced blocks blanked, line count preserved.

    ‼ `#24-p4residuals` (b). R1 bans a `# HISTORY` heading in a current-state file and R2 allows at
    most one START-HERE banner — but both matched inside FENCED CODE BLOCKS, where such text is an
    EXAMPLE, not a heading. A doc that shows "what not to do" in a fence would trip its own rule, and
    the natural way to make the gate green again is to delete the example — losing the explanation
    to satisfy a false positive. Latent when found (no doc currently does it), which is the cheapest
    possible moment to fix it.
    ⚠ LINE COUNT IS PRESERVED on purpose: R3 counts lines and the `--show` reporter prints line
    numbers, so blanking must not shift anything. Only the CONTENT is removed, never the newlines."""
    out, fenced, marker = [], False, None
    for line in text.split(chr(10)):
        stripped = line.lstrip()
        hit = next((f for f in ("```", "~~~") if stripped.startswith(f)), None)
        if hit == "```" and "`" in stripped.lstrip("`"):
            # ‼ An INLINE code span that opens a line (```x``` and prose) is not a fence: CommonMark forbids a
            # backtick in a backtick fence's info string. Read as a fence it flipped the state, so the line
            # itself and everything up to the next real fence went unscanned (R8 missed a mega-line, 2026-10-21).
            hit = None
        if hit and (marker is None or hit == marker):
            marker = None if fenced else hit      # a fence closes only with its OWN marker
            fenced = not fenced
            out.append("")           # the fence marker itself is never a heading
            continue
        out.append("" if fenced else line)
    # ‼ FAIL TOWARD CATCHING. An UNCLOSED fence would otherwise blank everything after it, so a
    # single stray ``` would silently switch R1/R2 off for the rest of the file — a blind spot
    # introduced by the very fix meant to remove a false positive. Measured before shipping: a
    # real `## HISTORY` after an unclosed fence went from FOUND to MISSED. If the fence never
    # closes, the document is malformed and we scan it UNBLANKED: a gate may cry wolf, but it may
    # never go quiet.
    if fenced:
        return text
    return chr(10).join(out)


def r7_section_is_closed(heading: str, section: "list[str]") -> bool:
    """R7's verdict on ONE `###` section: CLOSED or ARCHIVED content.

    ⭐ A FUNCTION SINCE 2026-10-21 (spec S2-1) SO `archive_sweep.py` CALLS THE SAME PREDICATE R7
    MEASURES WITH: the sweep may only ever move what R7 already counts as closed, and a second copy
    of these word lists would drift from this one. The logic is unchanged, byte for byte."""
    head = heading.upper()
    still_open = any(l.startswith(("- [ ]", "- [~]")) for l in section)
    hedged = any(w in head for w in ("MIXED", "STILL OPEN", "SOME ARE NOT"))
    done = any(w in head for w in ("✅", "FIXED", "CLOSED", "RESOLVED", "DONE"))
    return "ARCHIVED VERBATIM" in heading or (not still_open and done and not hedged)


# ==================================================================================================
# R8 — BYTE CEILINGS AND THE LONG-LINE RULE, BUILT AS A RATCHET (spec S2-1, backlog N3, 2026-10-21)
# ==================================================================================================
# WHY A RATCHET AND NOT A BUDGET: `04-HANDOFF.md` was ~390 KB and `03-PUNCH-LIST.md` ~690 KB when this
# was written, against a ~60 KB goal for the handoff. A hard budget would be red on arrival, and a red
# gate gets bypassed. So R8 ships GREEN at today's sizes and only ever TIGHTENS: `--ratchet` lowers a
# ceiling as the archive sweep removes bytes, and nothing lowers it back up silently.
# ⛔ [CRITIC, spec S2-1] THE RATCHET LOWERS TO `max(target, size + headroom)`, NEVER TO THE EXACT SIZE.
# At exactly-current every next doc edit fails, and the cheapest way to pass is to TRIM A CAVEAT
# (CLAUDE.md rule 2, "the headline carries the caveat"). A gate must never reward that. A ceiling may
# RISE only with a `raised` record (date, bytes, why), and every raise new against HEAD is PRINTED, so
# the Tier 1 reviewer sees it in the diff instead of trusting that nobody loosened the gate.
# WHY LINES TOO: grep, Read and Edit all work per line, and one 59,685-character line in 04 makes
# every grep hit that touches it cost ~15k tokens. Mega-lines that exist today are WAIVED by the hash
# of their first 60 characters; a waived line may only shrink, and new ones are refused. A legitimate
# edit that grows one is recorded with `--rewaive FILE --why ...` (a `history` record, printed by (d)).
# ⛔ A WAIVER ALSO PINS THE LINE'S LAST 60 CHARACTERS (`tails`, round 2). Keyed on its start alone, a
# waiver silently covered an UNRELATED new line that merely began the same way (a status line's usual
# shape): the checker cut a waived 03 line to 300 characters, appended a 1,500-character paragraph with
# the same first 60, and the lint passed. A line whose start matches and whose end does not is NOT
# covered; `--rewaive` records the new tail (printed by (d)), so the change is reviewed, never silent.
# An in-place shrink that keeps both ends still passes with no bookkeeping.
MAX_LINE_CHARS = 1200
WAIVER_KEY_CHARS = 60
WAIVER_TAIL_CHARS = 60
DEFAULT_HEADROOM = 8 * 1024
CEILINGS_NAME = "doc_size_ceilings.json"
WAIVERS_NAME = "long_line_waivers.json"
#: `--seed` only (the first commit): the spec's targets. The handoff's is ~60 KB; 03/05 get theirs
#: after the first sweep MEASURES what is closed (spec S2-1), so they start with none.
SEED_TARGETS = {"04-HANDOFF.md": 60 * 1024}
R8_FIXED = ("00-README.md",)


def r8_files(docs: pathlib.Path, ceilings: dict, head_ceilings: "dict | None" = None) -> "dict[str, pathlib.Path]":
    """name -> path of every R8 file: `00-README.md` + the current-state files 01-05 in `docs`, plus
    any ceiling key holding a `/` (e.g. `ai_player/README.md` once it is split), resolved against
    the folder ABOVE the docs folder — the repository root on the real tree.
    ⛔ `head_ceilings` (the COMMITTED JSON): its `/` keys count too, while their file exists. Taken from
    the worktree JSON alone, deleting `ai_player/README.md`'s entry removed the file from R8 entirely —
    no missing-ceiling, no REMOVED failure, and the README could grow without limit (round-2 finding).
    A file deleted together with its key is a legitimate retirement, so it is not resurrected."""
    out = {p.name: p for p in sorted(docs.glob("*.md")) if p.name in R8_FIXED or p.name[:3] in CURRENT_STATE}
    for key in ceilings.get("files", {}):
        if "/" in key:
            out[key] = docs.parent / key
    for key in (head_ceilings or {}).get("files", {}):
        if "/" in key and key not in out and (docs.parent / key).is_file():
            out[key] = docs.parent / key
    return out


def doc_bytes(path: pathlib.Path) -> int:
    """The file's size with CRLF folded to LF — the size of the blob git commits.
    ‼ This PC checks out with CRLF (core.autocrlf) and another machine may not; 03 has ~4,400 lines,
    so a raw size would differ by ~4.4 KB between machines, over half of the 8 KB headroom."""
    return len(path.read_bytes().replace(b"\r\n", b"\n"))


def waiver_key(line: str) -> str:
    """sha1 of the line's first 60 characters (spec S2-1): survives edits to the line's END, which is
    where a sentence is usually appended, and changes when its start is edited (`--rewaive` re-keys)."""
    return hashlib.sha1(line[:WAIVER_KEY_CHARS].encode("utf-8")).hexdigest()


def waiver_tail(line: str) -> str:
    """The line's last 60 characters, stored as text (`tails`) so the JSON diff shows what changed."""
    return line[-WAIVER_TAIL_CHARS:]


def tails_of(lines: "list[str]") -> "list[str]":
    return sorted(waiver_tail(line) for line in lines)


def long_lines(text: str) -> "list[tuple[int, str]]":
    """(1-based line number, line) of every line over MAX_LINE_CHARS that R8 polices.
    ‼ THE MENTION RULE: a line inside a fence is an EXAMPLE, exempt, so a doc never has to delete an
    example to pass. The fence logic is `_blank_fenced`'s, including its fail-toward-catching on an
    unclosed fence.
    ⛔ TABLE ROWS ARE NOT EXEMPT (round 2, 2026-10-21; the spec said they were). 04's state table held
    rows of 24,531 / 15,426 / 14,097 characters: exactly the grep-cost lines R8 exists for, and the
    exemption let them grow with no record. A long row is now WAIVED like a prose line (by hash,
    shrink-only); `archive_sweep.py` still never SPLITS one (a row is one record by construction)."""
    raw = text.split("\n")
    seen = _blank_fenced(text).split("\n")
    return [(n, line) for n, (line, scan) in enumerate(zip(raw, seen), 1)
            if len(line) > MAX_LINE_CHARS and scan.strip()]


def _long_line_advice(line: str) -> str:
    """How to fix an unwaived long line. ⛔ Round 3: a TABLE ROW (it starts with `|`) cannot be split, since a line
    break ends the row, so the split advice was wrong for exactly the 04 state-table rows R8 was widened to cover."""
    if line.lstrip().startswith("|"):
        return (f"A table row cannot be split (a line break ends the row): shorten it to {MAX_LINE_CHARS:,} "
                f"characters or move the detail into a linked section.")
    return "Split it: a line break inside a paragraph or list item renders the same (indent it under a bullet)."


def _read_json(path: pathlib.Path) -> "dict | None":
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: pathlib.Path, data: dict) -> None:
    # LF on every machine, so the diff a reviewer reads is the same everywhere.
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def head_text(path: pathlib.Path) -> "tuple[str, str | None]":
    """(state, text) of `path` as committed at HEAD: state `ok`, `absent` (not committed yet: the
    file's first commit) or `unavailable: <why>`.
    ‼ `absent` and `unavailable` are KEPT APART on purpose: the first is a fact (nothing to compare,
    the shrink-only rule has no baseline yet), the second means the check did not run, and a skipped
    check must never print like a passed one (audit_doc_consistency's 2026-08-17 lesson)."""
    def git(*args: str, raw: bool = False) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], capture_output=True, text=not raw, timeout=30)
    try:
        top = git("-C", str(path.parent), "rev-parse", "--show-toplevel")
        if top.returncode != 0:
            return "unavailable: not inside a git work tree", None
        root = pathlib.Path(top.stdout.strip()).resolve()
        rel = path.resolve().relative_to(root).as_posix()
        if git("-C", str(root), "rev-parse", "--verify", "-q", "HEAD").returncode != 0:
            return "absent", None
        listed = git("-C", str(root), "ls-tree", "--name-only", "HEAD", "--", rel)
        if listed.returncode != 0:
            return f"unavailable: git ls-tree exited {listed.returncode}", None
        if not listed.stdout.strip():
            return "absent", None
        shown = git("-C", str(root), "show", f"HEAD:{rel}", raw=True)
        if shown.returncode != 0:
            return f"unavailable: git show exited {shown.returncode}", None
        return "ok", shown.stdout.decode("utf-8").replace("\r\n", "\n")
    except (OSError, subprocess.SubprocessError, ValueError, UnicodeDecodeError) as exc:
        return f"unavailable: {type(exc).__name__}: {str(exc)[:80]}", None


def _r8_name(arg: str, files: "dict[str, pathlib.Path]") -> "str | None":
    """Accept a bare name (`04-HANDOFF.md`), a repo key (`ai_player/README.md`) or any path to it."""
    if arg in files:
        return arg
    if pathlib.Path(arg).name in files and "/" not in pathlib.Path(arg).name:
        return pathlib.Path(arg).name
    target = pathlib.Path(arg).resolve()
    return next((name for name, path in files.items() if path.resolve() == target), None)


def _head_states(cpath: pathlib.Path, wpath: pathlib.Path) -> "dict[str, tuple[str, str | None]]":
    return {path.name: head_text(path) for path in (cpath, wpath)}


def _head_ceilings(states: dict) -> "dict | None":
    state, text = states.get(CEILINGS_NAME, ("absent", None))
    return json.loads(text) if state == "ok" else None


def _against_head(states: dict, ceilings: dict, waivers: dict,
                  files: "dict[str, pathlib.Path]") -> "tuple[list[str], list[str]]":
    """R8 (d): the ceilings and waivers may only SHRINK against their committed copies (`states`: the
    `head_text` of each JSON). Returns (failures, notes). Every raise, waiver growth and new waiver
    tail NEW in this diff is a note."""
    fails: list[str] = []
    notes: list[str] = []
    for name, (state, _) in states.items():
        if state == "absent":
            notes.append(f"R8(d) NOT CHECKED for `{name}`: it is not in HEAD yet (its first "
                         f"commit), so there is no committed baseline to shrink against.")
        elif state != "ok":
            notes.append(f"⛔ WARN R8(d) SKIPPED for `{name}` — {state}. The shrink-only rule "
                         f"did NOT run; a clean result below does not cover it.")

    state, text = states[CEILINGS_NAME]
    if state == "ok":
        head_files = json.loads(text).get("files", {})
        now_files = ceilings.get("files", {})
        for name in sorted(set(head_files) - set(now_files)):
            if name in files and files[name].is_file():
                fails.append(f"R8  `{name}`'s ceiling was REMOVED from {CEILINGS_NAME} (HEAD had "
                             f"{head_files[name].get('ceiling'):,} B) — a removed ceiling is an "
                             f"unrecorded infinite raise")
        for name, entry in sorted(now_files.items()):
            base = head_files.get(name)
            if base is None:
                # A NEW ceiling polices a file nobody policed: a tightening, so it needs no record (only printed).
                notes.append(f"R8 NEW CEILING (not in HEAD): `{name}` {entry.get('ceiling', 0):,} B")
            head_raised = (base or {}).get("raised", [])
            new_raised = [r for r in entry.get("raised", []) if r not in head_raised]
            for r in head_raised:
                if r not in entry.get("raised", []):
                    fails.append(f"R8  `{name}`: a committed `raised` record was removed or edited "
                                 f"({r.get('date')}, -> {r.get('to')}) — the raise history is append-only")
            for r in new_raised:
                notes.append(f"R8 RAISE — NEW IN THIS DIFF, REVIEW IT: `{name}` {r.get('field', 'ceiling')} "
                             f"{r.get('from')} -> {r.get('to')} ({r.get('date')}): {r.get('why')}")
            if base is None:
                continue
            for field in ("ceiling", "headroom", "target"):
                was, now = base.get(field) or 0, entry.get(field) or 0
                if now <= was:
                    continue
                ok = any(r.get("field", "ceiling") == field and r.get("to") == now
                         and str(r.get("why", "")).strip() and r.get("date") for r in new_raised)
                if not ok:
                    fails.append(f"R8  `{name}`: its {field} ROSE {was:,} -> {now:,} against HEAD with no "
                                 f"new `raised` record saying why. A ceiling only shrinks; to raise one on "
                                 f"purpose run `lint_docs.py --raise {name} --to {now} --why \"...\"`.")

    state, text = states[WAIVERS_NAME]
    if state == "ok":
        head_list = json.loads(text).get("waivers", [])
        head_w = {(w["file"], w["sha1"]): w for w in head_list}
        now_w = {(w["file"], w["sha1"]): w for w in waivers.get("waivers", [])}
        claimed: dict = {}
        for key, w in sorted(now_w.items()):
            file = w["file"]
            if key in head_w:
                base_key = key
            else:
                # A re-key (its first 60 characters were edited) names the HEAD waiver it replaces
                # in `history`; that waiver must be gone from the worktree, or it is a NEW waiver.
                lineage = [r.get("from_sha1") for r in w.get("history", []) if r.get("from_sha1")]
                base_key = next(((file, s) for s in reversed(lineage)
                                 if (file, s) in head_w and (file, s) not in now_w), None)
                if base_key is None:
                    fails.append(f"R8  `{file}`: a NEW waiver for a line starting {w.get('head', '')[:50]!r} "
                                 f"— HEAD has no waiver it replaces. Waivers only shrink: split the line "
                                 f"under {MAX_LINE_CHARS:,} characters instead.")
                    continue
                notes.append(f"R8 WAIVER RE-KEYED (its first {WAIVER_KEY_CHARS} characters were edited): "
                             f"`{file}` {head_w[base_key].get('head', '')[:40]!r} -> {w.get('head', '')[:40]!r}")
            if base_key in claimed:
                fails.append(f"R8  `{file}`: two waivers both descend from ONE committed waiver "
                             f"({head_w[base_key].get('head', '')[:40]!r}) — one long line became two")
            claimed[base_key] = key
            base = head_w[base_key]
            head_hist = base.get("history", [])
            if any(r not in w.get("history", []) for r in head_hist):
                fails.append(f"R8  `{file}`: a committed `history` record of the waiver "
                             f"{w.get('head', '')[:40]!r} was removed or edited — it is append-only")
            new_hist = [r for r in w.get("history", []) if r not in head_hist]
            # ⛔ `count` (how many long lines one waiver covers) may NEVER rise: a rise is a new long line
            # riding an old waiver, which `--rewaive` itself refuses — so no record can make it legal.
            if w.get("count", 1) > base.get("count", 1):
                fails.append(f"R8  `{file}`: the waiver {w.get('head', '')[:50]!r} now covers "
                             f"{w.get('count', 1)} lines against HEAD's {base.get('count', 1)} — a waiver's "
                             f"count never rises (a new long line is split, never waived)")
            if w["chars"] > base["chars"]:
                grown = [r for r in new_hist if (r.get("to_chars") or 0) > (r.get("from_chars") or 0)
                         and str(r.get("why", "")).strip() and r.get("date")]
                if not grown or max(r["to_chars"] for r in grown) < w["chars"]:
                    fails.append(f"R8  `{file}`: the waived line {w.get('head', '')[:50]!r} GREW "
                                 f"{base['chars']:,} -> {w['chars']:,} characters against HEAD with no "
                                 f"new `history` record saying why — record it with `lint_docs.py "
                                 f"--rewaive {file} --why \"...\"`")
                else:
                    for r in grown:
                        was = r.get("from_chars") or 0
                        notes.append(f"R8 WAIVED LINE GREW — NEW IN THIS DIFF, REVIEW IT: `{file}` "
                                     f"{w.get('head', '')[:40]!r} {was:,} -> {r['to_chars']:,} chars "
                                     f"(+{r['to_chars'] - was:,}) ({r.get('date')}): {r.get('why')}")
            if base.get("tails") is not None and sorted(w.get("tails") or []) != sorted(base["tails"]):
                # A new END on a waived line: it may be the same paragraph edited at its end, or an unrelated
                # line that starts the same way. Only `--rewaive` (which records it) makes it legal, and the
                # record is printed so Tier 1 decides which it is.
                if not any(r.get("to_tails") == w.get("tails") for r in new_hist):
                    fails.append(f"R8  `{file}`: the waiver {w.get('head', '')[:50]!r} has a different `tails` "
                                 f"than HEAD with no new `history` record — run `lint_docs.py --rewaive {file}`")
                else:
                    notes.append(f"R8 WAIVER RE-TAILED (its line's last {WAIVER_TAIL_CHARS} characters changed) — "
                                 f"NEW IN THIS DIFF, REVIEW IT: `{file}` {w.get('head', '')[:40]!r}: "
                                 f"{sorted(base['tails'])} -> {w.get('tails')}")
    return fails, notes


def _covered(w: dict, lines: "list[tuple[int, str]]") -> "tuple[list[tuple[int, str]], list[tuple[int, str]]]":
    """(covered, not covered) of the long lines sharing `w`'s first 60 characters: covered = its end matches too."""
    tails = w.get("tails")
    hit = [(n, line) for n, line in lines if tails is not None and waiver_tail(line) in tails]
    return hit, [x for x in lines if x not in hit]


def check_r8(docs: pathlib.Path, budget_dir: pathlib.Path,
             head_dir: "pathlib.Path | None" = None) -> "tuple[list[str], list[str], list[str]]":
    """R8 (a)-(d) over the tree. Returns (failures, notes, table rows); nothing is written.
    `head_dir` (default `budget_dir`): the folder whose COMMITTED JSON files (d) compares against. Round 3:
    `archive_sweep.py` lints a REHEARSED copy of the budget folder in a temp dir, outside git, where (d) would
    otherwise be SKIPPED; it points this at the real folder so (d) still runs on the would-be result."""
    cpath, wpath = budget_dir / CEILINGS_NAME, budget_dir / WAIVERS_NAME
    hdir = head_dir or budget_dir
    try:
        ceilings, waivers = _read_json(cpath), _read_json(wpath)
    except (ValueError, OSError) as exc:
        return [f"R8  cannot parse the budget files under {budget_dir}: {type(exc).__name__}: {exc}"], [], []
    missing = [p.name for p, d in ((cpath, ceilings), (wpath, waivers)) if d is None]
    if missing:
        # ‼ A ratchet whose state file vanished must not read as "no ceilings, all fine".
        return [f"R8  cannot run: {', '.join(missing)} missing under {budget_dir} — R8 is a ratchet "
                f"and its state lives there"], [], []
    fails: list[str] = []
    notes: list[str] = []
    rows: list[str] = []
    states = _head_states(hdir / CEILINGS_NAME, hdir / WAIVERS_NAME)
    try:
        head_ceilings = _head_ceilings(states)
    except ValueError as exc:
        return [f"R8  cannot parse HEAD's {CEILINGS_NAME}: {exc}"], [], []
    files = r8_files(docs, ceilings, head_ceilings)
    cfiles = ceilings.get("files", {})
    by_file: "dict[str, dict[str, dict]]" = defaultdict(dict)
    for w in waivers.get("waivers", []):
        by_file[w["file"]][w["sha1"]] = w
    for name in sorted(set(by_file) - set(files)):
        fails.append(f"R8  {WAIVERS_NAME} holds waivers for `{name}`, which is not an R8 file — remove them")
    for name, path in files.items():
        if not path.is_file():
            fails.append(f"R8  `{name}` has a ceiling in {CEILINGS_NAME} but does not exist")
            continue
        size = doc_bytes(path)
        entry = cfiles.get(name)
        ceiling = target = None
        if entry is None:
            fails.append(f"R8  `{name}` has no byte ceiling in {CEILINGS_NAME} — every R8 file needs "
                         f"one (`lint_docs.py --raise {name} --to <bytes> --why ...` adds it on the record)")
        else:
            ceiling, target = entry["ceiling"], entry.get("target")
            if size > ceiling:
                fails.append(f"R8  `{name}`: {size:,} bytes is {size - ceiling:,} over its ceiling "
                             f"{ceiling:,}. Archive closed blocks (`archive_sweep.py --source ...`), or, if "
                             f"the growth is right, record it: `lint_docs.py --raise {name} --to <bytes> "
                             f"--why \"...\"`. ⛔ Do NOT trim a caveat to fit.")
            if target and size > target:
                notes.append(f"R8 `{name}` is over its TARGET by {size - target:,} B ({size:,} vs "
                             f"{target:,}) — non-fatal until the ceiling reaches it")
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = long_lines(text)
        by_key: "dict[str, list[tuple[int, str]]]" = defaultdict(list)
        for n, line in hits:
            by_key[waiver_key(line)].append((n, line))
        mine = by_file.get(name, {})
        for key, lines in by_key.items():
            w = mine.get(key)
            if w is None:
                for n, line in lines:
                    fails.append(f"R8  {name}:{n}: {len(line):,} characters — over {MAX_LINE_CHARS:,} "
                                 f"outside a fence and NOT waived. " + _long_line_advice(line))
                continue
            covered, foreign = _covered(w, lines)
            for n, line in foreign:
                fails.append(f"R8  {name}:{n}: {len(line):,} characters (the waived line had {w['chars']:,}) — it "
                             f"STARTS like a waived line but its last {WAIVER_TAIL_CHARS} characters differ, so the "
                             f"waiver does not cover it (it pins "
                             f"both ends). If this IS the waived line edited at its end, run `lint_docs.py "
                             f"--rewaive {name}` (it records and prints the new end; add --why \"...\" if it "
                             f"grew); if it is a NEW paragraph, split it under {MAX_LINE_CHARS:,} characters.")
            if len(lines) > w.get("count", 1):
                fails.append(f"R8  {name}:{lines[-1][0]}: {len(lines)} long lines share the first "
                             f"{WAIVER_KEY_CHARS} characters of ONE waived line — a new long line is "
                             f"not covered by an old waiver; split it")
            for n, line in covered:
                if len(line) > w["chars"]:
                    fails.append(f"R8  {name}:{n}: a WAIVED line GREW {w['chars']:,} -> {len(line):,} "
                                 f"characters (waivers only shrink). Put the new text on its own line, "
                                 f"or record the growth: `lint_docs.py --rewaive {name} --why \"...\"`")
        for key, w in mine.items():
            if key not in by_key:
                fails.append(f"R8  {name}: STALE waiver for a line starting {w.get('head', '')[:50]!r} "
                             f"— no line over {MAX_LINE_CHARS:,} characters starts that way any more "
                             f"(edited at its start, shortened or moved). `lint_docs.py --rewaive {name}` "
                             f"re-keys or drops it.")
        flag = " <-" if (ceiling is None or size > ceiling) else ""
        rows.append(f"  {name:<30}{size:>10,}{(ceiling or 0):>11,}{(target or 0):>11,}"
                    f"{len(hits):>7}{sum(len(_covered(mine[k], v)[0]) for k, v in by_key.items() if k in mine):>8}"
                    f"{flag}")
    head_fails, head_notes = _against_head(states, ceilings, waivers, files)
    return fails + head_fails, notes + head_notes, rows


def _load_budget(budget_dir: pathlib.Path) -> "tuple[pathlib.Path, pathlib.Path, dict, dict]":
    cpath, wpath = budget_dir / CEILINGS_NAME, budget_dir / WAIVERS_NAME
    ceilings, waivers = _read_json(cpath), _read_json(wpath)
    if ceilings is None or waivers is None:
        raise SystemExit(f"R8: {CEILINGS_NAME} / {WAIVERS_NAME} missing under {budget_dir} "
                         f"(`--seed` creates them on a first commit)")
    return cpath, wpath, ceilings, waivers


def _sorted_waivers(waivers: "list[dict]", files: "dict[str, pathlib.Path]") -> "list[dict]":
    """File order, then line order — so the JSON diff of one edit touches one entry."""
    where: dict = {}
    for name, path in files.items():
        if path.is_file():
            for n, line in long_lines(path.read_text(encoding="utf-8", errors="replace")):
                where.setdefault((name, waiver_key(line)), n)
    return sorted(waivers, key=lambda w: (w["file"], where.get((w["file"], w["sha1"]), 10 ** 9), w["sha1"]))


def ratchet(docs: pathlib.Path, budget_dir: pathlib.Path, only: "list[str]") -> int:
    """`--ratchet`: lower each ceiling to max(target, size + headroom) and tighten every LIVE waiver to
    its line's length. ⛔ NEVER RAISES — a file over its ceiling stays over it (R8 fails until it is
    swept or raised on the record). Stale waivers are left for `--rewaive`, which can re-key them."""
    cpath, wpath, ceilings, waivers = _load_budget(budget_dir)
    files = r8_files(docs, ceilings)
    names = list(files)
    if only:
        names = []
        for arg in only:
            name = _r8_name(arg, files)
            if name is None:
                print(f"--ratchet: `{arg}` is not an R8 file ({', '.join(files)})")
                return 2
            names.append(name)
    changes: list[str] = []
    for name in names:
        entry, path = ceilings.get("files", {}).get(name), files[name]
        if entry is None or not path.is_file():
            print(f"  {name}: no ceiling or no file — skipped (R8 reports it)")
            continue
        size = doc_bytes(path)
        headroom = entry.get("headroom", DEFAULT_HEADROOM)
        floor = max(entry.get("target") or 0, size + headroom)
        if floor < entry["ceiling"]:
            changes.append(f"  {name}: ceiling {entry['ceiling']:,} -> {floor:,} B (size {size:,} + headroom "
                           f"{headroom:,}{'; floored at its target' if floor == entry.get('target') else ''})")
            entry["ceiling"] = floor
        else:
            print(f"  {name}: ceiling {entry['ceiling']:,} B kept (size {size:,}, headroom {headroom:,}; "
                  f"the ratchet never raises)")
        by_key: "dict[str, list[tuple[int, str]]]" = defaultdict(list)
        for n, line in long_lines(path.read_text(encoding="utf-8", errors="replace")):
            by_key[waiver_key(line)].append((n, line))
        for w in waivers.get("waivers", []):
            if w["file"] != name or w["sha1"] not in by_key:
                continue
            covered, _ = _covered(w, by_key[w["sha1"]])      # only a line it really covers can tighten it
            longest = max((len(line) for _, line in covered), default=None)
            if longest is not None and longest < w["chars"]:
                changes.append(f"  {name}: waiver {w.get('head', '')[:40]!r} {w['chars']:,} -> {longest:,} chars")
                w["chars"] = longest
    if not changes:
        print("RATCHET: no change (every ceiling is already at max(target, size + headroom) or below)")
        return 0
    waivers["waivers"] = _sorted_waivers(waivers.get("waivers", []), files)
    _write_json(cpath, ceilings)
    _write_json(wpath, waivers)
    print("RATCHET: lowered (shrink only):")
    for line in changes:
        print(line)
    return 0


def rewaive(docs: pathlib.Path, budget_dir: pathlib.Path, arg: str, why: str) -> int:
    """`--rewaive FILE`: bring FILE's waivers up to date after a legitimate edit, or refuse.

    * a waived line that SHRANK is tightened; one that GREW is recorded in its `history` (date,
      from, to, why) and REFUSED without `--why`;
    * a waived line whose LAST 60 characters changed is RE-TAILED: the new end is recorded in
      `history` (`from_tails` / `to_tails`) and printed, so a reviewer decides whether it is the same
      paragraph edited at its end or an unrelated line that starts the same way (needs `--why` only
      if it also grew);
    * a waived line whose first 60 characters were edited is RE-KEYED: paired with the line it
      replaced by diffing the file against its committed version (`git show HEAD:`), lineage kept;
    * a waiver whose line is gone or now within the limit is dropped (a shrink);
    * a NEW long line (one that replaces no waived line) is REFUSED: split it;
    * REFUSED outright if the FILE is over its ceiling — a mega-line's growth is bytes too.
    Nothing is written on a refusal. Every change is printed with its growth in characters."""
    cpath, wpath, ceilings, waivers = _load_budget(budget_dir)
    files = r8_files(docs, ceilings)
    name = _r8_name(arg, files)
    if name is None or not files[name].is_file():
        print(f"--rewaive: `{arg}` is not an existing R8 file ({', '.join(files)})")
        return 2
    path = files[name]
    why = (why or "").strip()
    today = datetime.date.today().isoformat()
    text = path.read_text(encoding="utf-8", errors="replace")
    by_key: "dict[str, list[tuple[int, str]]]" = defaultdict(list)
    for n, line in long_lines(text):
        by_key[waiver_key(line)].append((n, line))
    others = [w for w in waivers.get("waivers", []) if w["file"] != name]
    mine = {w["sha1"]: w for w in waivers.get("waivers", []) if w["file"] == name}
    kept: "dict[str, dict]" = {}
    changes: list[str] = []
    refusals: list[str] = []

    for key, hits in by_key.items():
        if key not in mine:
            continue
        w = json.loads(json.dumps(mine[key]))        # a deep copy: nothing changes on a refusal
        n, longest = max(((n, len(line)) for n, line in hits), key=lambda t: t[1])
        if len(hits) > w.get("count", 1):
            refusals.append(f"{name}:{hits[-1][0]}: {len(hits)} long lines now share the first "
                            f"{WAIVER_KEY_CHARS} characters of one waived line — split the new one")
        old_tails, new_tails = sorted(w.get("tails") or []), tails_of([line for _, line in hits])
        grew, retailed = longest > w["chars"], new_tails != old_tails
        if grew and not why:
            refusals.append(f"{name}:{n}: the waived line grew {w['chars']:,} -> {longest:,} characters "
                            f"(+{longest - w['chars']:,}); say why with --why \"...\" (it is recorded and "
                            f"printed for review), or put the new text on its own line")
        elif grew or retailed:
            record = {"date": today, "from_chars": w["chars"], "to_chars": longest,
                      "why": why or "its end was edited (no growth): the new last 60 characters are recorded"}
            if retailed:
                record["from_tails"], record["to_tails"] = old_tails, new_tails
            w.setdefault("history", []).append(record)
            if grew:
                changes.append(f"  GREW     {name}:{n}  {w['chars']:,} -> {longest:,} chars "
                               f"(+{longest - w['chars']:,})  {hits[0][1][:50]!r}")
            if retailed:
                changes.append(f"  RE-TAILED {name}:{n}  its end {old_tails} -> {new_tails} — REVIEW: the same "
                               f"paragraph edited at its end, or a new line that starts like it?")
        elif longest < w["chars"]:
            changes.append(f"  SHRANK   {name}:{n}  {w['chars']:,} -> {longest:,} chars "
                           f"({longest - w['chars']:,})  {hits[0][1][:50]!r}")
        w["chars"], w["head"], w["tails"] = longest, hits[0][1][:WAIVER_KEY_CHARS], new_tails
        kept[key] = w

    stale = {k: w for k, w in mine.items() if k not in by_key}
    unwaived = [(n, line) for key, hits in by_key.items() if key not in mine for n, line in hits]
    if unwaived:
        state, old_text = head_text(path)
        pairs: "list[tuple[dict, int, str]]" = []
        if old_text is not None and stale:
            # A stale waiver claims an old line by its own key or any key in its lineage (an edit
            # re-keyed and re-edited before the commit).
            ancestry = {k: {k} | {r.get("from_sha1") for r in w.get("history", []) if r.get("from_sha1")}
                        for k, w in stale.items()}
            old, new = old_text.split("\n"), text.split("\n")
            waiting = {n: line for n, line in unwaived}
            free = dict(stale)
            matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != "replace":
                    continue
                olds = [k for i in range(i1, i2) for k, keys in ancestry.items()
                        if k in free and waiver_key(old[i]) in keys and len(old[i]) > MAX_LINE_CHARS]
                news = [j + 1 for j in range(j1, j2) if j + 1 in waiting]
                if olds and len(olds) == len(news):
                    for k, n in zip(olds, news):
                        pairs.append((free.pop(k), n, waiting.pop(n)))
            unwaived = sorted(waiting.items())
            stale = free
        for w_old, n, line in pairs:
            grew = len(line) > w_old["chars"]
            if grew and not why:
                refusals.append(f"{name}:{n}: an edited waived line (its start changed) grew "
                                f"{w_old['chars']:,} -> {len(line):,} characters; say why with --why \"...\"")
                continue
            w = json.loads(json.dumps(w_old))
            w.pop("count", None)
            w["history"] = w.get("history", []) + [{
                "date": today, "from_sha1": w_old["sha1"], "from_chars": w_old["chars"],
                "to_chars": len(line), "from_tails": sorted(w_old.get("tails") or []),
                "to_tails": tails_of([line]),
                "why": why or "re-keyed: its first 60 characters were edited (no growth)"}]
            w["sha1"], w["chars"], w["head"] = waiver_key(line), len(line), line[:WAIVER_KEY_CHARS]
            w["tails"] = tails_of([line])
            kept[w["sha1"]] = w
            changes.append(f"  RE-KEYED {name}:{n}  {w_old['chars']:,} -> {len(line):,} chars "
                           f"({len(line) - w_old['chars']:+,})  {w_old.get('head', '')[:30]!r} -> {line[:30]!r}")
        for n, line in unwaived:
            refusals.append(f"{name}:{n}: a NEW line of {len(line):,} characters — it replaces no waived line"
                            f"{'' if state == 'ok' else f' (no committed version to pair against: {state})'}. "
                            + (_long_line_advice(line).rstrip(".") if line.lstrip().startswith("|") else
                               f"Split it under {MAX_LINE_CHARS:,} characters (a continuation line renders the "
                               f"same)") + "; waivers are only for the lines that existed when R8 shipped.")
    for key, w in stale.items():
        changes.append(f"  DROPPED  {name}  stale waiver {w.get('head', '')[:50]!r} (its line is gone or "
                       f"now within {MAX_LINE_CHARS:,} characters)")

    entry = ceilings.get("files", {}).get(name)
    size = doc_bytes(path)
    if entry is None or size > entry["ceiling"]:
        refusals.append(f"{name} is {size:,} bytes, over its ceiling "
                        f"{'(none)' if entry is None else format(entry['ceiling'], ',')} — a waiver cannot "
                        f"cover a file that is over budget. Sweep it, or `--raise` on the record first.")
    if refusals:
        print(f"REWAIVE REFUSED for {name} — nothing written:")
        for line in refusals:
            print(f"  {line}")
        return 1
    if not changes:
        print(f"REWAIVE {name}: no change (every waiver matches its line)")
        return 0
    waivers["waivers"] = _sorted_waivers(others + list(kept.values()), files)
    _write_json(wpath, waivers)
    print(f"REWAIVE {name} — written to {WAIVERS_NAME} (its diff is what Tier 1 reviews):")
    for line in changes:
        print(line)
    return 0


def _new_r8_key(docs: pathlib.Path, arg: str) -> "str | None":
    """`--raise` only: a repo-relative path such as `ai_player/README.md` that names an EXISTING `.md` file
    under the repository root becomes a new `/` key (how the README's current part joins R8 after its split).
    A path that leaves the root, an absolute path or a missing file is not accepted."""
    rel = pathlib.PurePosixPath(arg.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or len(rel.parts) < 2 or rel.suffix != ".md":
        return None
    root = docs.parent.resolve()
    target = (root / rel).resolve()
    if not target.is_file() or root not in target.parents:
        return None
    return rel.as_posix()


def raise_ceiling(docs: pathlib.Path, budget_dir: pathlib.Path, arg: str, to: "int | None", why: str) -> int:
    """`--raise FILE --to BYTES --why TEXT`: the ONE recorded way up. Appends a `raised` record (date,
    from, to, why) that R8 (d) requires and prints for review. Also adds a missing ceiling, including a
    repo-relative one (`ai_player/README.md`) for a file R8 does not check yet."""
    cpath, _, ceilings, _ = _load_budget(budget_dir)
    files = r8_files(docs, ceilings)
    name = _r8_name(arg, files) or _new_r8_key(docs, arg)
    why = (why or "").strip()
    if name is None or to is None or not why:
        print("--raise needs an R8 FILE (or an existing repo-relative .md path such as ai_player/README.md), "
              "--to BYTES and a non-empty --why (it is printed for review)")
        return 2
    entry = ceilings.setdefault("files", {}).setdefault(
        name, {"ceiling": 0, "headroom": DEFAULT_HEADROOM, "target": None, "raised": []})
    if to <= entry["ceiling"]:
        print(f"--raise: {to:,} is not above {name}'s ceiling {entry['ceiling']:,} — lowering is `--ratchet`")
        return 2
    entry.setdefault("raised", []).append({"date": datetime.date.today().isoformat(), "field": "ceiling",
                                           "from": entry["ceiling"], "to": to, "why": why})
    print(f"RAISED {name}: ceiling {entry['ceiling']:,} -> {to:,} B — recorded, and printed by every lint "
          f"until it is committed: {why}")
    entry["ceiling"] = to
    _write_json(cpath, ceilings)
    return 0


def seed(docs: pathlib.Path, budget_dir: pathlib.Path) -> int:
    """`--seed`: R8's starting state — every ceiling at size + headroom, a waiver for every long line
    that exists today. ⛔ REFUSED once either file is committed: re-seeding would reset the ratchet
    and silently re-admit every growth since, which is exactly what (d) exists to stop."""
    cpath, wpath = budget_dir / CEILINGS_NAME, budget_dir / WAIVERS_NAME
    for path in (cpath, wpath):
        state, _ = head_text(path)
        if state != "absent":
            print(f"--seed REFUSED: `{path.name}` is {'committed' if state == 'ok' else state} — use "
                  f"--ratchet / --rewaive / --raise, which keep the record")
            return 1
    old = _read_json(cpath) or {}
    files = r8_files(docs, old)
    entries = {}
    waivers = []
    for name, path in files.items():
        if not path.is_file():
            continue
        was = old.get("files", {}).get(name, {})
        headroom = was.get("headroom", DEFAULT_HEADROOM)
        entries[name] = {"ceiling": doc_bytes(path) + headroom, "headroom": headroom,
                         "target": was.get("target", SEED_TARGETS.get(name)), "raised": []}
        counts: dict = {}
        for _, line in long_lines(path.read_text(encoding="utf-8", errors="replace")):
            key = waiver_key(line)
            counts.setdefault(key, []).append(line)
        for key, lines in counts.items():
            w = {"file": name, "sha1": key, "chars": max(len(l) for l in lines), "head": lines[0][:WAIVER_KEY_CHARS],
                 "tails": tails_of(lines), "history": []}
            if len(lines) > 1:
                w["count"] = len(lines)
            waivers.append(w)
    _write_json(cpath, {"_why": "R8 (lint_docs.py, spec S2-1): byte ceilings of the current-state docs, "
                               "measured with CRLF folded to LF. A ratchet: --ratchet lowers, never raises; "
                               "a raise needs a `raised` record (--raise), printed for review.",
                        "files": entries})
    _write_json(wpath, {"_why": "R8 (lint_docs.py, spec S2-1): the lines over 1,200 characters (table rows "
                                "included, fenced lines exempt) that existed when R8 shipped, keyed by sha1 of "
                                "their first 60 characters AND pinned by their last 60 (`tails`). Only shrink; "
                                "growth and a new end are recorded in `history` by --rewaive, printed for review.",
                        "waivers": _sorted_waivers(waivers, files)})
    print(f"SEEDED {CEILINGS_NAME} ({len(entries)} files) and {WAIVERS_NAME} ({len(waivers)} waivers)")
    return 0


BANNER_RE = re.compile(r"^#{1,3}\s.*\b(START HERE|YOU ARE HERE)\b", re.I | re.M)
HISTORY_RE = re.compile(r"^#{1,2}\s+(?:‼\s*)?HISTORY\b", re.I | re.M)

failures: list[str] = []
infos: list[str] = []


def fail(rule: str, msg: str) -> None:
    failures.append(f"{rule}  {msg}")


def lint(docs_dir: pathlib.Path, budget_dir: pathlib.Path, show: bool, repo: pathlib.Path = REPO,
         head_dir: "pathlib.Path | None" = None) -> int:
    """Every rule, R1-R8. ‼ A function since 2026-10-21 (spec S2-1) so `archive_sweep.py` can import
    this module's helpers without running the lint; the rules' code is unchanged."""
    failures.clear()
    infos.clear()
    docs = sorted(p for p in docs_dir.glob("*.md"))
    if not docs:
        raise SystemExit(f"lint cannot run: no docs found under {docs_dir}")

    print("=" * 92)
    print("DOCUMENTATION LINT — CLAUDE.md's rules, enforced instead of advised")
    print("=" * 92)

    # ---------- R4: number collisions ----------
    by_number: dict[str, list[str]] = defaultdict(list)
    for p in docs:
        m = re.match(r"^(\d{2})-", p.name)
        if m:
            by_number[m.group(1)].append(p.name)
    for num, names in sorted(by_number.items()):
        if len(names) > 1:
            fail("R4", f"doc number {num}- is used by {len(names)} files: {', '.join(names)}")

    # ---------- R1/R2/R3: current-state hygiene ----------
    print("\nCURRENT-STATE FILES (01-05) — must describe PRESENT reality")
    print(f"  {'file':<44}{'lines':>7}{'budget':>8}  {'HISTORY':>8}{'banners':>9}")
    for p in docs:
        prefix = p.name[:3]
        if prefix not in CURRENT_STATE:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        # ‼ `len(splitlines())`, NOT `count("\n") + 1` — fixed 2026-08-23 (`#24-p4residuals` (c)).
        # Every file here ends with a trailing newline (git enforces it), and `count("\n") + 1` counts a
        # phantom final line for exactly those files: it reported 834 where `wc -l` said 833. That made
        # R3's effective budget ONE STRICTER than the number it prints, and made every line-count claim
        # in the docs disagree with the obvious way a reader checks it. Measured before/after on the
        # five current-state files: each drops by exactly 1, and no file changes pass/fail state.
        lines = len(text.splitlines())
        budget = LINE_BUDGET.get(prefix, 1500)
        # ‼ R1/R2 scan the FENCE-BLANKED text; R3 counts the REAL one (see `_blank_fenced`).
        scannable = _blank_fenced(text)
        hist = HISTORY_RE.findall(scannable)
        banners = BANNER_RE.findall(scannable)
        flag = ""
        if hist:
            fail("R1", f"{p.name}: {len(hist)} `# HISTORY` block(s) inside a CURRENT-STATE file")
            flag = " <-"
        if len(banners) > 1:
            fail("R2", f"{p.name}: {len(banners)} START-HERE/YOU-ARE-HERE banners (max 1) — a reader "
                       f"cannot tell which is current")
            flag = " <-"
        if lines > budget:
            fail("R3", f"{p.name}: {lines} lines exceeds its {budget}-line budget — an archive is "
                       f"forming inside a current-state file")
            flag = " <-"
        print(f"  {p.name:<44}{lines:>7}{budget:>8}  {len(hist):>8}{len(banners):>9}{flag}")

        # ---------- R7: the CLOSED/ARCHIVED share of a current-state file ----------
        # ⭐ THIS IS R3'S REAL INTENT, MEASURED DIRECTLY. R3 counts LINES and says "an archive is
        # forming"; that inference only holds if the growth is stale content. On 2026-09-08 03 hit its
        # ceiling while 78.5% of it was OPEN work and just 6.8% closed — so R3 was firing on a genuine
        # backlog and every "fix" deleted detail from live items. R7 asks the question R3 was proxying.
        frac_budget = next((v for k, v in CLOSED_FRACTION_BUDGET.items() if p.name.startswith(k)), None)
        if frac_budget is not None:
            body = p.read_text(encoding="utf-8", errors="replace").splitlines()
            heads = [i for i, l in enumerate(body) if l.startswith("### ")]
            closed = 0
            for a, b in zip(heads, heads[1:] + [len(body)]):
                if r7_section_is_closed(body[a], body[a:b]):
                    closed += b - a
            share = closed / len(body) if body else 0.0
            if share > frac_budget:
                fail("R7", f"{p.name}: {share:.1%} of the file is CLOSED or ARCHIVED content "
                           f"({closed} of {len(body)} lines), over its {frac_budget:.0%} budget — THIS "
                           f"is 'an archive forming in a current-state file', and here trimming IS the "
                           f"right answer. Retire closed items with `archive_doc_block.py`.")
        if show and (hist or len(banners) > 1):
            for m in HISTORY_RE.finditer(scannable):
                print(f"      HISTORY @ line {scannable[:m.start()].count(chr(10)) + 1}: {m.group(0)[:70]}")
            for m in BANNER_RE.finditer(scannable):
                print(f"      BANNER  @ line {scannable[:m.start()].count(chr(10)) + 1}: {m.group(0)[:70]}")

    # ---------- R8: byte ceilings + the long-line rule, a RATCHET (see the R8 block above) ----------
    r8_fails, r8_notes, r8_rows = check_r8(docs_dir, budget_dir, head_dir)
    print(f"\nR8 — BYTES (CRLF folded to LF) AND LINES OVER {MAX_LINE_CHARS:,} CHARACTERS: a RATCHET, "
          f"shrink-only against HEAD")
    print(f"  {'file':<30}{'bytes':>10}{'ceiling':>11}{'target':>11}{'long':>7}{'waived':>8}")
    for row in r8_rows:
        print(row)
    for note in r8_notes:
        print(f"  {note}")
    for f in r8_fails:
        failures.append(f)

    # ---------- R5: the reading order must point at real files ----------
    readme = docs_dir / "00-README.md"
    if readme.is_file():
        named = set(re.findall(r"`(\d{2}-[A-Za-z0-9._-]+\.md)`", readme.read_text(encoding="utf-8")))
        existing = {p.name for p in docs}
        for name in sorted(named - existing):
            fail("R5", f"00-README's reading order names `{name}`, which does not exist")

    # ---------- R6: every POKEBOT_* flag in bot code must be in the registry ----------
    # ‼‼ FAMILY C — the family with the worst measured cost in this project's history. A flag pinned at
    # 0 is usually a RESULT ("this was measured harmful"), not a leftover, and those results were
    # living in code comments where nobody looks before PROPOSING a feature. On 2026-08-11 that cost a
    # recommendation: "roster hygiene before bosses" was proposed as new work when it had already been
    # built, measured harmful and pinned off (KI-54). Only a manual pre-build check caught it.
    section_r6 = docs_dir / "29-DISABLED-FEATURES-REGISTRY.md"
    # ‼ WIDENED 2026-08-14 — THE OLD SCAN HAD A PROVEN HOLE, found by a cold-start audit, and it is
    # rule 6's exact shape: a gate that was never fault-tested against how flags are ACTUALLY written.
    # The old regex matched only `environ.get("POKEBOT_…")` literals, so it was blind to:
    #   * `os.getenv("POKEBOT_ENCOUNTER_BENCHMARK")`          (stats.py — different accessor)
    #   * `_TURBO_ENV = "POKEBOT_STORY_DEBUG_TURBO"`          (story_mode.py — name held in a constant,
    #     the accessor never sees the literal; intro.py's POKEBOT_RNG_DECORRELATION_FRAMES likewise)
    #   * `pokebot.py` / `tools/story-dev` flags               (outside the scan roots entirely)
    # FIVE live flags were undocumented while the gate printed "11 flag(s) in code, 11 documented" and
    # exited 0. The scan now matches ANY quoted POKEBOT_* string literal — accessor-agnostic, constant-
    # agnostic — and adds pokebot.py + tools/story-dev to the roots. Comments/docstrings mentioning a
    # flag also match; that is deliberate overreach in the SAFE direction: the registry documents the
    # flag either way, and a phantom mention would surface as an undocumented "flag" worth deleting.
    flag_re = re.compile(r'["\'](POKEBOT_[A-Z0-9_]+)["\']')
    found: set[str] = set()
    # ‼ BOTH FORKS — widened 2026-08-22, deep sanity check PASS 4 (INFRASTRUCTURE).
    # R6 scanned ONLY `sandbox-pokebot`, so `custom-pokebot` — THE FORK THAT SHIPS — was invisible:
    # 234 .py files, none of them ever read by the registry guard. A kill-switch living only in the
    # promoted fork would have been documented nowhere and R6 would still have passed.
    # ⚠ MEASURED BEFORE WIDENING, so this is provably non-breaking: custom's flag set is a SUBSET of
    # sandbox's (17 ⊆ 21), i.e. the widened scan finds no new undocumented flag today. It is a guard
    # against tomorrow, not a repair of today — which is exactly when a scope gap is cheapest to close.
    bot_roots = [repo / "sandbox-pokebot" / "modules", repo / "sandbox-pokebot" / "plugins",
                 repo / "custom-pokebot" / "modules", repo / "custom-pokebot" / "plugins",
                 repo / "tools" / "story-dev"]
    _single_files = [repo / "sandbox-pokebot" / "pokebot.py", repo / "custom-pokebot" / "pokebot.py"]
    for _f in _single_files:
        if _f.is_file():
            found |= set(flag_re.findall(_f.read_text(encoding="utf-8", errors="replace")))
    for root in bot_roots:
        if not root.is_dir():
            continue
        for py in root.rglob("*.py"):
            # ‼ `evidence/` IS NOT BOT CODE — excluded 2026-08-22 (deep sanity check PASS 4).
            # Committed evidence includes fault-injection drivers that deliberately contain SYNTHETIC
            # flag names (`POKEBOT_TOTALLY_UNDOCUMENTED_FLAG` and friends) to prove R6 can fire. R6
            # scanned them and demanded registry rows for flags no bot will ever read — a gate firing
            # on its own test fixtures, which is the false-positive shape this project rates as worse
            # than no gate. Caught by running the suite BEFORE committing the evidence, not after.
            if "evidence" in py.parts or "__pycache__" in py.parts:
                continue
            try:
                found |= set(flag_re.findall(py.read_text(encoding="utf-8", errors="replace")))
            except Exception as error:  # noqa: BLE001 — an unreadable file is reported, never skipped
                fail("R6", f"could not read {py.name} while scanning for flags: {type(error).__name__}")

    print("\nFEATURE FLAGS (POKEBOT_*) — every one must be in 29-DISABLED-FEATURES-REGISTRY.md")
    if not section_r6.is_file():
        fail("R6", "29-DISABLED-FEATURES-REGISTRY.md is missing")
    elif not found:
        # ‼ A scan that finds nothing must not silently pass — that is the silent-zero family.
        fail("R6", "found ZERO POKEBOT_* flags in the bot code — the scan is probably broken, "
                   "since the project is known to use them")
    else:
        registry = section_r6.read_text(encoding="utf-8", errors="replace")
        missing = sorted(f for f in found if f not in registry)
        print(f"  {len(found)} flag(s) in code, {len(found) - len(missing)} documented")
        for f in missing:
            fail("R6", f"`{f}` is used in bot code but is NOT in the registry — a flag pinned off is "
                       f"usually a MEASUREMENT, and it must be findable before someone re-proposes it")

        # ‼ THE REVERSE DIRECTION — added 2026-08-22, deep sanity check PASS 4.
        # R6 only ever asked "is every flag in the code documented?". The opposite rot was unguarded:
        # a registry row whose flag NO CODE READS ANY MORE. That row keeps warning future agents off
        # work that has already been deleted, which is the same cost as a stale prevention rule — and
        # `/reconcile`'s own charter says a rule whose hazard is gone must be retired, because leaving
        # it active wastes the context of everyone who reads it.
        # ⚠ MEASURED FIRST: zero orphans today (21 in code, 21 in the registry, both directions), so
        # this ships green and is a guard against future rot, not a repair.
        documented = set(re.findall(r"`(POKEBOT_[A-Z0-9_]+)`", registry))
        orphaned = sorted(f for f in documented if f not in found)
        for f in orphaned:
            fail("R6", f"`{f}` has a registry row but NO code in either fork reads it — the feature is "
                       f"gone and the row now misleads. Retire the row (or restore the reader).")

    # ---------- INFO ----------
    punch = docs_dir / "03-PUNCH-LIST.md"
    if punch.is_file():
        t = punch.read_text(encoding="utf-8", errors="replace")
        done = len(re.findall(r"^- \[x\]", t, re.M))
        partial = re.findall(r"^- \[~\] (.+)$", t, re.M)
        vague = [x for x in partial if not re.search(r"remain|outstanding|todo|left to|still", x, re.I)]
        infos.append(f"I1  {done} completed `[x]` items are sitting in the punch list (a CURRENT-STATE "
                     f"file). Consider moving closed ones to 07-CHANGELOG.")
        infos.append(f"I2  {len(vague)} of {len(partial)} `[~]` partial items do not say what REMAINS "
                     f"on their headline (the marker is load-bearing — see 03's own note).")

    print("\nINFO (never fails the run)")
    for i in infos:
        print(f"  {i}")

    print("\n" + "=" * 92)
    if failures:
        print(f"FAILED — {len(failures)} rule violation(s):")
        for f in failures:
            print(f"  {f}")
        print("\n‼ These are CLAUDE.md's own rules. Re-run with --list to see the offending lines.")
        print("  Move stale content to an append-only file; do not delete hard-won detail.")
        return 1
    print("ALL DOCUMENTATION RULES PASS.")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="show every offending line")
    # ‼ Flags, not an environment variable: a quoted POKEBOT_-prefixed name in tools/story-dev would
    # be read by R6 as a bot flag owed a registry row, and a test-only override is not a bot feature.
    ap.add_argument("--docs-dir", type=pathlib.Path, help="lint this docs folder instead (tests)")
    ap.add_argument("--budget-dir", type=pathlib.Path, help=f"folder of {CEILINGS_NAME} / {WAIVERS_NAME}")
    # R6 scans the bot code under this root. Tests pass the REAL repository when they run a COPY of this file
    # (call-deleting mutants live in a scratch folder, where `parents[2]` holds no bot code and R6 would fail).
    ap.add_argument("--repo-dir", type=pathlib.Path, help="root whose bot code R6 scans (tests)")
    ap.add_argument("--head-budget-dir", type=pathlib.Path,
                    help="R8 (d): compare against HEAD's JSON files in THIS folder (default: --budget-dir); "
                         "archive_sweep's rehearsal lints a temp copy outside git")
    ap.add_argument("--ratchet", nargs="*", metavar="FILE", help="lower ceilings (all, or these files)")
    ap.add_argument("--rewaive", metavar="FILE", help="re-hash FILE's waived lines after an edit")
    ap.add_argument("--raise", dest="raise_file", metavar="FILE", help="raise FILE's ceiling, on the record")
    ap.add_argument("--to", type=int, help="--raise: the new ceiling in bytes")
    ap.add_argument("--why", default="", help="--rewaive / --raise: the reason, recorded and printed")
    ap.add_argument("--seed", action="store_true", help="create the R8 files (first commit only)")
    args = ap.parse_args(argv)
    docs_dir = (args.docs_dir or DOCS).resolve()
    budget_dir = (args.budget_dir or HERE).resolve()
    if args.seed:
        return seed(docs_dir, budget_dir)
    if args.ratchet is not None:
        return ratchet(docs_dir, budget_dir, args.ratchet)
    if args.rewaive:
        return rewaive(docs_dir, budget_dir, args.rewaive, args.why)
    if args.raise_file:
        return raise_ceiling(docs_dir, budget_dir, args.raise_file, args.to, args.why)
    return lint(docs_dir, budget_dir, show=args.list, repo=(args.repo_dir or REPO).resolve(),
                head_dir=args.head_budget_dir and args.head_budget_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
