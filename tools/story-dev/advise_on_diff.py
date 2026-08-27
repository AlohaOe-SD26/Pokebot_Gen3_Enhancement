"""ADVISORY — print the prevention rules that match WHAT THE WORKING DIFF CHANGES.

Punch-list `#24-difftriggeredrules`. WHY: four times in ONE session (2026-08-23,
`08-MISTAKES.md`) a correct, written-down prevention rule failed to fire, each time because
prose rules are indexed by the STORY that created them and recall happens by ACTION. This
tool inverts the index: every rule below is keyed to a DIFF SHAPE (an added line of code,
or a touched path), so the rule surfaces at the moment of the edit — the only moment it can
still help.

⛔ ADVISORY, NEVER BLOCKING (the item's own words). Exit code is 0 whether or not rules
match — a blocking version acquires false positives and gets bypassed, which this project
rates worse than nothing. Exit is non-zero ONLY when the TOOL is broken (bad args,
unreadable diff, git failure) or a `--self-test` fails — never because of what the diff
contains.

    PYTHONUTF8=1 py -3.12 advise_on_diff.py                 # advise on `git diff HEAD`
    PYTHONUTF8=1 py -3.12 advise_on_diff.py --diff-file F   # advise on a saved diff
    PYTHONUTF8=1 py -3.12 advise_on_diff.py --self-test     # fault-test every rule BOTH ways

Matching contract (exactly what `--self-test` proves, per rule):
  * a rule FIRES on a diff whose ADDED lines contain its shape as CODE;
  * a `.py`-shaped rule stays SILENT when the same shape appears only in a `#` comment —
    a mention is not an edit, the same distinction this project's AST gates draw;
  * a PATH rule fires on its path and stays silent on every other path;
  * an empty or unrelated diff produces NO output at all — silence is the no-findings
    state, so a clean commit gains zero noise.

Accepted limits, on purpose (each one reviewed, not discovered):
  * a shape inside a docstring or string literal still fires (quote state does not
    survive diff hunk boundaries) — one extra reminder is the cheap direction;
  * an `unless` gate (e.g. R-APRESS's `is_waiting_for_input`) is honored when it sits on
    the SAME added line or within ±2 added lines of the match — a gate further away than
    that still draws the reminder (an adversarial review proved the single-line version
    false-fired on the standard two-line `if gate(): press` idiom, which trains readers
    to ignore the advisory; the window is the fix, and its boundary is documented here);
  * `while not False:`-style always-true spellings and other exotic equivalents are not
    matched — shape heuristics, not a parser.
Renames and binary diffs ARE seen by path rules: git omits `---`/`+++` for both, so
paths are also harvested from `diff --git` and `rename from/to` headers (adversarial
review finding — a pure `git mv` into the pristine mirror was invisible to R-MIRROR).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

# Build patterns that need a literal backslash from chr(92) — the 2026-08-23 rule
# (`\b` in a non-raw string is a BACKSPACE byte and the pattern matches nothing).
# This file must obey the rules it preaches.
_BS = chr(92)


@dataclass(frozen=True)
class Rule:
    rule_id: str
    headline: str
    #: "code"    — pattern runs against comment-stripped ADDED lines of *.py files
    #: "docline" — pattern runs against raw ADDED lines of files matching path_filter
    #: "path"    — pattern runs against each TOUCHED path (adds, edits, deletes alike)
    kind: str
    pattern: re.Pattern[str]
    advice: tuple[str, ...]
    path_filter: re.Pattern[str] | None = None
    #: matched added lines are suppressed when this also matches (e.g. an A-press that is
    #: already gated needs no reminder to gate it)
    unless: re.Pattern[str] | None = None


RULES: tuple[Rule, ...] = (
    Rule(
        rule_id="R-REGEX",
        headline="a regex was added or edited",
        kind="code",
        pattern=re.compile(r"re\.(compile|search|match|fullmatch|findall|finditer|sub)\("),
        advice=(
            "NEVER REVIEW A REGEX BY READING IT — print the COMPILED `.pattern` and run a "
            "positive AND a negative list (08-MISTAKES 2026-08-23: `" + _BS + "b` compiled "
            "to a backspace byte TWICE in one day, and both gates said PASS).",
            "In a NON-raw string `" + _BS + "b` is backspace 0x08 while `" + _BS + "s`/`"
            + _BS + "d`/`" + _BS + "w` survive — use raw strings; when writing a pattern "
            "through a shell, build backslashes with chr(92).",
            "A control character in source is gated (`#24-p2headergate` (C)) — a pattern "
            "carrying one matches NOTHING and wears a green tick.",
        ),
    ),
    Rule(
        rule_id="R-NUMGATE",
        headline="code that matches digits was added (a numeric gate?)",
        kind="code",
        pattern=re.compile(re.escape(_BS + "d")),
        advice=(
            "A NUMERIC GATE MUST ACCEPT THE FORMS HUMANS ACTUALLY WRITE — digits, "
            "spelled-out words (WORD-BOUNDED: `done`/`none` contain `one`) and sameness "
            "words. Gate the CLAIM, not the NUMBER: the check's silence means 'no number "
            "in a form I know', never 'the number is right' (08-MISTAKES 2026-08-23 — the "
            "fourth firing of the meta-failure this tool exists to end).",
        ),
    ),
    Rule(
        rule_id="R-EXCEPT",
        headline="an exception handler was added or edited",
        kind="code",
        pattern=re.compile(r"^except(\*|[ (:]|$)"),
        advice=(
            "Story/recovery paths must NOT swallow aborts — call "
            "`reraise_if_aborting(error)` before handling (modules/story/early_game.py). "
            "The swallow class was paid down 36 -> 23 and is RATCHETED (gate #27, "
            "`probe_abort_swallowing.py`); a new swallowing handler re-opens paid-for debt.",
            "`except X as error:` UNBINDS `error` at handler exit — Python DELETES a "
            "same-named outer variable, so a later read is a NameError on the failure-only "
            "path nobody drives (08-MISTAKES 2026-08-23).",
        ),
    ),
    Rule(
        rule_id="R-LOOP",
        headline="an unconditional loop was added",
        kind="code",
        pattern=re.compile(r"while\s+(True|1)\s*:"),
        advice=(
            "Prime directive: NEVER HANG — bound every loop. A `while True` needs a "
            "frame/attempt bound and a 'did it work?' guard. The unbounded first-wait "
            "shape is exactly what KI-47 nets at 3,001 frames and what turned a missed A "
            "press into a derail cascade (`#26-battleitemwedge`).",
        ),
    ),
    Rule(
        rule_id="R-APRESS",
        headline="an ungated A press was added",
        kind="code",
        pattern=re.compile(r"press_button\(\s*['\"]A['\"]"),
        unless=re.compile(r"is_waiting_for_input"),
        advice=(
            "The museum-greeter shape: ANY loop pressing A across scripted scenes must "
            "gate the press on `is_waiting_for_input()` (08-MISTAKES 2026-08-26 — the rule "
            "existed in prose while TWO ungated sites sat in the same file; one became "
            "`#26-surfteachchain`). When adding such a press, SWEEP for other instances of "
            "the pattern in the same commit.",
        ),
    ),
    Rule(
        rule_id="R-MANUAL",
        headline="a hand-off to Manual mode was added",
        kind="code",
        pattern=re.compile(r"set_manual_mode\s*\("),
        advice=(
            "NEVER SILENTLY DERAIL (CLAUDE.md craft rule): a Manual hand-off is a last "
            "resort. Log WHICH guard fired and why, and prefer a bounded retry/recovery — "
            "`#26-manualderails` measured 44 of 50 runs ending in this call, and the user's "
            "manual flip-back usually just... worked (the budget was exhausted, not the "
            "situation).",
        ),
    ),
    Rule(
        rule_id="R-CAMWINDOW",
        headline="a live-object read was added (get_map_objects / _npc_is_on)",
        kind="code",
        pattern=re.compile(r"(get_map_objects\s*\(|_npc_is_on\s*\()"),
        advice=(
            "`get_map_objects()` is a CAMERA-RANGE WINDOW — an object outside ~7-9 tiles is "
            "absent from it WHETHER OR NOT IT EXISTS. Check presence from an ADJACENT tile, "
            "never from across the map (three paid instances: the §Ch21 'ZERO NPCs loaded' "
            "misread, the (31,18) Expert claim, and leg 2b's Wallace check from (9,3) — "
            "08-MISTAKES 2026-08-27). `MapLocation.objects` is the ROM template (ORIGINAL "
            "positions) — never mix the two.",
        ),
    ),
    Rule(
        rule_id="R-MIRROR",
        headline="a file inside the PRISTINE UPSTREAM MIRROR was touched",
        kind="path",
        pattern=re.compile(r"^40cakes repo/pokebot-gen3/"),
        advice=(
            "⛔ `40cakes repo/pokebot-gen3/` is a PRISTINE mirror of upstream and is NEVER "
            "edited by hand — it changes only via `git subtree pull` from "
            "`upstream-pokebot` (CLAUDE.md two-folder fork layout). Revert this and make "
            "the change in `custom-pokebot/` or `sandbox-pokebot/` instead.",
        ),
    ),
    Rule(
        rule_id="R-KIHEADER",
        headline="a KNOWN-ISSUES heading was added or edited",
        kind="docline",
        path_filter=re.compile(r"05-KNOWN-ISSUES\.md$"),
        pattern=re.compile(r"^#{2,3}\s"),
        advice=(
            "P2: a KI HEADER (title + status words) must agree with the KI's NEWEST dated "
            "body line, and a heading is a claim about EVERY bullet beneath it — mixed "
            "statuses must say MIXED. THE HEADLINE CARRIES THE CAVEAT (CLAUDE.md DOC "
            "CONSISTENCY LAYER, pair P2).",
        ),
    ),
    Rule(
        rule_id="R-HANDOFF",
        headline="04-HANDOFF.md was edited",
        kind="path",
        pattern=re.compile(r"(^|/)04-HANDOFF\.md$"),
        advice=(
            "P1: the YOU-ARE-HERE banner and NEXT ACTIONS item 0 move TOGETHER — 'X is "
            "done' above forbids 'build X' below. P5: the item's own `03-PUNCH-LIST.md` "
            "status must match the claim made here. On finishing an item, GREP THE TREE "
            "FOR ITS SLUG and re-read every hit — a status sentence anywhere is another "
            "half of the pair. Tier 0 (`lint_docs` + `audit_doc_consistency`) before the "
            "commit.",
        ),
    ),
    Rule(
        rule_id="R-PUNCH",
        headline="03-PUNCH-LIST.md was edited",
        kind="path",
        pattern=re.compile(r"(^|/)03-PUNCH-LIST\.md$"),
        advice=(
            "P5: an item's status here and the handoff's claim about it move TOGETHER "
            "(the pair exists because P1-P4 once passed over a punch-list entry commanding "
            "work that had already shipped). Measure the file's line budget LAST; retire "
            "completed items by SUMMARISE + POINT at `07-CHANGELOG.md`, never delete — "
            "code and gates cite these slugs.",
        ),
    ),
)


# --------------------------------------------------------------------------- diff parsing

_QUOTED = re.compile(r'^"(.*)"$')


def _unquote_git_path(raw: str) -> str:
    """git c-quotes paths containing spaces/specials in diff headers; undo the common case."""
    match = _QUOTED.match(raw)
    if match:
        raw = match.group(1).replace(_BS + '"', '"').replace(_BS + _BS, _BS)
    return raw


def _paths_from_diff_git_line(line: str) -> list[str]:
    """Both paths off a `diff --git a/X b/Y` header.

    ‼ This header is the ONLY place a pure rename (100% similarity) or a binary diff
    names its files — git omits `---`/`+++` for both shapes, which made a `git mv` into
    the pristine mirror invisible to R-MIRROR until an adversarial review proved it.
    Quoted sides are unquoted; unquoted sides containing spaces are split by preferring
    a symmetric `a/P b/P` reading, falling back to the LAST ` b/` occurrence.
    """
    rest = line[len("diff --git "):].strip()
    if rest.startswith('"'):
        match = re.match(r'^"((?:[^"\\]|\\.)*)"\s+(.*)$', rest)
        if not match:
            return []
        left, right = _unquote_git_path('"' + match.group(1) + '"'), _unquote_git_path(match.group(2).strip())
    else:
        # symmetric-first: `a/P b/P` with identical P is the overwhelmingly common case
        candidates = [i for i in range(len(rest)) if rest.startswith(" b/", i)]
        left = right = ""
        for i in candidates:
            l, r = rest[:i], rest[i + 1:]
            if l.startswith("a/") and r.startswith("b/") and l[2:] == r[2:]:
                left, right = l, r
                break
        else:
            if candidates:
                i = candidates[-1]
                left, right = rest[:i], rest[i + 1:]
    out = []
    for side in (left, right):
        if side[:2] in ("a/", "b/"):
            out.append(side[2:])
    return out


def parse_diff(text: str) -> tuple[set[str], dict[str, list[str]]]:
    """Return (touched_paths, {path: [added line content, ...]}).

    Paths are collected from `--- a/` / `+++ b/` headers (minus /dev/null), from the
    `diff --git` header (pure renames and binary diffs have NO other path lines), and
    from `rename from/to` lines — so a deletion, a rename or a binary change inside the
    pristine mirror registers for path rules exactly like an edit.
    """
    touched: set[str] = set()
    added: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            touched.update(_paths_from_diff_git_line(line))
        elif line.startswith("rename from ") or line.startswith("rename to "):
            raw = _unquote_git_path(line.split(" ", 2)[2].strip())
            if raw:
                touched.add(raw)
        elif line.startswith("+++ ") or line.startswith("--- "):
            raw = _unquote_git_path(line[4:].strip())
            if raw in ("/dev/null", ""):
                if line.startswith("+++ "):
                    current = None
                continue
            if raw[:2] in ("a/", "b/"):
                raw = raw[2:]
            touched.add(raw)
            if line.startswith("+++ "):
                current = raw
                added.setdefault(raw, [])
        elif line.startswith("+") and not line.startswith("+++") and current is not None:
            added[current].append(line[1:])
    return touched, added


def _strip_comment(line: str) -> str:
    """Drop a trailing `#`-comment, tracking quote state so a '#' inside a string stays.

    A line that IS a comment returns ''. Honest limit (documented in the module
    docstring): multi-line string state cannot be tracked from a diff, so a shape inside
    a docstring still counts as code — the cheap failure direction for an advisory.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return ""
    quote: str | None = None
    out: list[str] = []
    i = 0
    while i < len(stripped):
        ch = stripped[i]
        if quote is not None:
            if ch == _BS:
                out.append(stripped[i : i + 2])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#":
            break
        out.append(ch)
        i += 1
    return "".join(out).strip()


# ------------------------------------------------------------------------------ matching

@dataclass
class Findings:
    #: rule_id -> list of "path: +evidence" strings (path rules use the bare path)
    hits: dict[str, list[str]] = field(default_factory=dict)

    def add(self, rule_id: str, evidence: str) -> None:
        self.hits.setdefault(rule_id, []).append(evidence)


def match_rules(touched: set[str], added: dict[str, list[str]]) -> Findings:
    findings = Findings()
    for rule in RULES:
        if rule.kind == "path":
            for path in sorted(touched):
                if rule.pattern.search(path):
                    findings.add(rule.rule_id, path)
        elif rule.kind == "docline":
            for path, lines in sorted(added.items()):
                if rule.path_filter is None or not rule.path_filter.search(path):
                    continue
                for line in lines:
                    if rule.pattern.search(line):
                        findings.add(rule.rule_id, f"{path}: +{line.strip()}")
        elif rule.kind == "code":
            for path, lines in sorted(added.items()):
                if not path.endswith(".py"):
                    continue
                stripped = [_strip_comment(line) for line in lines]
                for index, code in enumerate(stripped):
                    if not code:
                        continue
                    if not rule.pattern.search(code):
                        continue
                    if rule.unless is not None:
                        # ±2 ADDED lines: the standard two-line `if gate(): action`
                        # idiom must not draw the reminder (adversarial review finding —
                        # a false positive here trains readers to ignore the advisory).
                        # Boundary documented in the module docstring: a gate further
                        # away than 2 added lines still fires.
                        window = stripped[max(0, index - 2): index + 3]
                        if any(rule.unless.search(near) for near in window if near):
                            continue
                    findings.add(rule.rule_id, f"{path}: +{code}")
        else:  # pragma: no cover - a bad rule kind is a bug in THIS file
            raise ValueError(f"unknown rule kind {rule.kind!r} on {rule.rule_id}")
    return findings


_MAX_EVIDENCE = 5
_MAX_EVIDENCE_CHARS = 110


def render(findings: Findings) -> str:
    """The full advisory text, or '' when nothing matched (silence = no findings)."""
    if not findings.hits:
        return ""
    out: list[str] = [
        "=" * 78,
        "ADVISORY — prevention rules matching this diff (advisory only, never blocking)",
        "=" * 78,
    ]
    by_id = {rule.rule_id: rule for rule in RULES}
    for rule_id, evidence in findings.hits.items():
        rule = by_id[rule_id]
        out.append(f"‼ {rule_id} — {rule.headline}")
        for item in evidence[:_MAX_EVIDENCE]:
            shown = item if len(item) <= _MAX_EVIDENCE_CHARS else item[: _MAX_EVIDENCE_CHARS - 3] + "..."
            out.append(f"    where: {shown}")
        if len(evidence) > _MAX_EVIDENCE:
            out.append(f"    ... and {len(evidence) - _MAX_EVIDENCE} more")
        for line in rule.advice:
            out.append(f"    * {line}")
        out.append("")
    out.append("(full rules: PROJECT KNOWLEDGE/08-MISTAKES.md + CLAUDE.md; this tool is")
    out.append(" `#24-difftriggeredrules` — advisory by design, exit 0 either way)")
    return "\n".join(out)


def advise(diff_text: str) -> str:
    """The single pipeline both the CLI and the self-test run — never two code paths."""
    touched, added = parse_diff(diff_text)
    return render(match_rules(touched, added))


# ------------------------------------------------------------------------------ self-test

def _mkdiff(path: str, added_lines: list[str]) -> str:
    """A minimal unified diff adding `added_lines` to `path` (quoted iff git would)."""
    quoted = f'"{{}}"'.format if " " in path else "{}".format
    lines = [
        f"diff --git {quoted('a/' + path)} {quoted('b/' + path)}",
        "index 0000000..1111111 100644",
        f"--- {quoted('a/' + path)}",
        f"+++ {quoted('b/' + path)}",
        "@@ -1,0 +1,{} @@".format(len(added_lines)),
    ]
    lines += ["+" + line for line in added_lines]
    return "\n".join(lines) + "\n"


def _mkdeletion(path: str) -> str:
    quoted = f'"{{}}"'.format if " " in path else "{}".format
    return "\n".join([
        f"diff --git {quoted('a/' + path)} {quoted('b/' + path)}",
        "deleted file mode 100644",
        f"--- {quoted('a/' + path)}",
        "+++ /dev/null",
        "@@ -1,1 +0,0 @@",
        "-gone",
    ]) + "\n"


def self_test() -> int:
    """Fault-test every rule BOTH ways: fires on the shape as code, silent on a comment
    mention / a foreign path. A rule that cannot fail its own test is not a rule — the
    `probe_slot_free_plan` lesson, applied to this tool on day one.
    """
    failures: list[str] = []
    checks_run = [0]  # counted at the call sites so the PASS line can never go stale

    def check(name: str, diff: str, expect: dict[str, bool]) -> None:
        checks_run[0] += 1
        text = advise(diff)
        for rule_id, should_fire in expect.items():
            fired = f"‼ {rule_id} " in text
            if fired != should_fire:
                failures.append(
                    f"{name}: {rule_id} {'did NOT fire' if should_fire else 'FIRED'}"
                    f" (expected the opposite)"
                )

    # T1/T2/T3 — R-REGEX: code fires; a comment mention and a .md mention stay silent.
    check("T1 regex-as-code", _mkdiff("tools/story-dev/x.py", ['pat = re.compile(r"a+")']),
          {"R-REGEX": True})
    check("T2 regex-in-comment", _mkdiff("tools/story-dev/x.py", ["# we use re.compile here"]),
          {"R-REGEX": False})
    check("T3 regex-in-md", _mkdiff("PROJECT KNOWLEDGE/07-CHANGELOG.md", ["added a re.compile("]),
          {"R-REGEX": False})

    # T4/T5 — R-NUMGATE: a digit-matching pattern fires; a comment stays silent.
    check("T4 numgate-as-code",
          _mkdiff("tools/story-dev/x.py", ["m = re.search(r'" + _BS + "d+ gates', s)"]),
          {"R-NUMGATE": True, "R-REGEX": True})
    check("T5 numgate-in-comment",
          _mkdiff("tools/story-dev/x.py", ["# matches " + _BS + "d+ in prose"]),
          {"R-NUMGATE": False})

    # T6/T7 — R-EXCEPT: a handler fires; a comment stays silent.
    check("T6 except-as-code", _mkdiff("m/story/x.py", ["try:", "    f()", "except ValueError:"]),
          {"R-EXCEPT": True})
    check("T7 except-in-comment", _mkdiff("m/story/x.py", ["# except nothing ever"]),
          {"R-EXCEPT": False})

    # T8/T9 — R-LOOP.
    check("T8 loop-as-code", _mkdiff("m/x.py", ["while True:"]), {"R-LOOP": True})
    check("T9 loop-in-comment", _mkdiff("m/x.py", ["# spins while True forever"]),
          {"R-LOOP": False})

    # T10/T11/T11b/T11c/T12 — R-APRESS: an ungated press fires; a SAME-LINE gate, the
    # standard TWO-LINE gate idiom, and a comment stay silent; a gate further than the
    # ±2-line window still fires (the documented boundary, tested so it stays true).
    check("T10 apress-ungated", _mkdiff("m/x.py", ['context.emulator.press_button("A")']),
          {"R-APRESS": True})
    check("T11 apress-gated-inline",
          _mkdiff("m/x.py", ['press_button("A" if is_waiting_for_input() else "B")']),
          {"R-APRESS": False})
    check("T11b apress-gated-twoline",
          _mkdiff("m/x.py", ["if context.emulator.is_waiting_for_input():",
                             '    context.emulator.press_button("A")',
                             '    log("pressed")']),
          {"R-APRESS": False})
    check("T11c apress-gate-out-of-window",
          _mkdiff("m/x.py", ["if is_waiting_for_input():", "    a()", "    b()",
                             "    c()", '    press_button("A")']),
          {"R-APRESS": True})
    check("T12 apress-comment", _mkdiff("m/x.py", ['# never press_button("A") blindly']),
          {"R-APRESS": False})

    # T13/T14 — R-MANUAL.
    check("T13 manual-as-code", _mkdiff("m/x.py", ["context.set_manual_mode()"]),
          {"R-MANUAL": True})
    check("T14 manual-comment", _mkdiff("m/x.py", ["# falls back to set_manual_mode()"]),
          {"R-MANUAL": False})

    # T31/T32 — R-CAMWINDOW: a live-object read as code fires; a comment mention stays silent.
    check("T31 camwindow-as-code",
          _mkdiff("m/story/x.py", ["if not _npc_is_on(MapRSE.CAVE, (9, 13)):"]),
          {"R-CAMWINDOW": True})
    check("T32 camwindow-comment",
          _mkdiff("m/story/x.py", ["# get_map_objects() is camera-limited, remember"]),
          {"R-CAMWINDOW": False})

    # T15/T16/T17 — R-MIRROR: an edit fires, a DELETION fires, the enhancement forks don't.
    check("T15 mirror-edit",
          _mkdiff("40cakes repo/pokebot-gen3/modules/pokemon.py", ["x = 1"]),
          {"R-MIRROR": True})
    check("T16 mirror-deletion", _mkdeletion("40cakes repo/pokebot-gen3/modules/pokemon.py"),
          {"R-MIRROR": True})
    check("T17 fork-edit-clean", _mkdiff("sandbox-pokebot/modules/pokemon.py", ["x = 1"]),
          {"R-MIRROR": False})

    # T18/T19/T20 — R-KIHEADER: a heading in 05 fires; a body bullet and a heading in
    # another doc stay silent.
    check("T18 ki-header", _mkdiff("PROJECT KNOWLEDGE/05-KNOWN-ISSUES.md", ["## KI-99 — new"]),
          {"R-KIHEADER": True})
    check("T19 ki-body-bullet", _mkdiff("PROJECT KNOWLEDGE/05-KNOWN-ISSUES.md", ["* a detail"]),
          {"R-KIHEADER": False})
    check("T20 heading-elsewhere", _mkdiff("PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md", ["## Atlas"]),
          {"R-KIHEADER": False})

    # T21/T22 — the doc-pair path rules.
    check("T21 handoff-touch", _mkdiff("PROJECT KNOWLEDGE/04-HANDOFF.md", ["banner text"]),
          {"R-HANDOFF": True, "R-PUNCH": False})
    check("T22 punchlist-touch", _mkdiff("PROJECT KNOWLEDGE/03-PUNCH-LIST.md", ["- [x] done"]),
          {"R-PUNCH": True, "R-HANDOFF": False})

    # T26/T27/T28 — the shapes git gives NO `---`/`+++` lines for (adversarial review
    # finding): a PURE RENAME into the mirror and a BINARY diff in the mirror must fire
    # R-MIRROR; a rename between fork paths must not.
    rename_diff = "\n".join([
        'diff --git a/custom-pokebot/modules/x.py "b/40cakes repo/pokebot-gen3/modules/x.py"',
        "similarity index 100%",
        "rename from custom-pokebot/modules/x.py",
        'rename to "40cakes repo/pokebot-gen3/modules/x.py"',
    ]) + "\n"
    check("T26 pure-rename-into-mirror", rename_diff, {"R-MIRROR": True})
    binary_diff = "\n".join([
        'diff --git "a/40cakes repo/pokebot-gen3/data/x.bin" "b/40cakes repo/pokebot-gen3/data/x.bin"',
        'Binary files "a/40cakes repo/pokebot-gen3/data/x.bin" and '
        '"b/40cakes repo/pokebot-gen3/data/x.bin" differ',
    ]) + "\n"
    check("T27 binary-in-mirror", binary_diff, {"R-MIRROR": True})
    fork_rename = "\n".join([
        "diff --git a/sandbox-pokebot/modules/a.py b/sandbox-pokebot/modules/b.py",
        "similarity index 100%",
        "rename from sandbox-pokebot/modules/a.py",
        "rename to sandbox-pokebot/modules/b.py",
    ]) + "\n"
    check("T28 fork-rename-clean", fork_rename, {"R-MIRROR": False})

    # T29 — the shape THIS repo's git actually emits for a space-containing path:
    # UNQUOTED with a trailing TAB (measured against real commits by the adversarial
    # review; the quoted form in T15/T27 is the other git configuration).
    tab = "\t"
    real_shape = "\n".join([
        "diff --git a/40cakes repo/pokebot-gen3/modules/pokemon.py "
        "b/40cakes repo/pokebot-gen3/modules/pokemon.py",
        "index 0000000..1111111 100644",
        f"--- a/40cakes repo/pokebot-gen3/modules/pokemon.py{tab}",
        f"+++ b/40cakes repo/pokebot-gen3/modules/pokemon.py{tab}",
        "@@ -1,0 +1,1 @@",
        "+x = 1",
    ]) + "\n"
    check("T29 real-git-space-path-trailing-tab", real_shape, {"R-MIRROR": True})

    # T30 — PEP 654 `except*` groups count as handlers too.
    check("T30 except-star", _mkdiff("m/x.py", ["except* ValueError:"]), {"R-EXCEPT": True})

    # T23/T24 — silence: an empty diff and an unrelated diff produce NO output at all.
    checks_run[0] += 2
    if advise("") != "":
        failures.append("T23: empty diff produced output")
    if advise(_mkdiff("README.txt", ["hello world"])) != "":
        failures.append("T24: unrelated diff produced output")

    # T25 — every rule id above exists in RULES and every RULES id was exercised by a
    # positive test, so a new rule cannot silently ship untested.
    checks_run[0] += 1
    tested_positive = {
        "R-REGEX", "R-NUMGATE", "R-EXCEPT", "R-LOOP", "R-APRESS", "R-MANUAL",
        "R-MIRROR", "R-KIHEADER", "R-HANDOFF", "R-PUNCH", "R-CAMWINDOW",
    }
    actual = {rule.rule_id for rule in RULES}
    if tested_positive != actual:
        failures.append(
            f"T25: rule set and positive-test set differ: only-in-rules="
            f"{sorted(actual - tested_positive)} only-in-tests={sorted(tested_positive - actual)}"
        )

    if failures:
        print(f"SELF-TEST: FAIL ({len(failures)})")
        for failure in failures:
            print(f"  ✗ {failure}")
        return 1
    print(f"SELF-TEST: PASS ({checks_run[0]} checks — every rule fired on its shape and "
          "stayed silent on a comment mention / gated idiom / foreign path; renames, "
          "binary diffs and the real trailing-tab shape register; empty and unrelated "
          "diffs print nothing)")
    return 0


# ----------------------------------------------------------------------------------- CLI

def _working_diff() -> str:
    """`git diff HEAD` — staged and unstaged together: everything a commit could take."""
    # ‼ 10s, deliberately UNDER the hook's outer 20s bound in `.claude/settings.json` —
    # a 60s inner timeout was unreachable dead code there (adversarial review finding),
    # and the tool self-bounding means the hook's kill path should never be the one that
    # fires.
    result = subprocess.run(
        ["git", "diff", "HEAD", "--no-color"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--diff-file", type=Path,
                        help="advise on a saved diff instead of `git diff HEAD`")
    parser.add_argument("--self-test", action="store_true",
                        help="fault-test every rule both ways and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.diff_file is not None:
        diff_text = args.diff_file.read_text(encoding="utf-8", errors="replace")
    else:
        diff_text = _working_diff()

    text = advise(diff_text)
    if text:
        print(text)
    # ⛔ ADVISORY: findings never change the exit code. See the module docstring.
    return 0


if __name__ == "__main__":
    sys.exit(main())
