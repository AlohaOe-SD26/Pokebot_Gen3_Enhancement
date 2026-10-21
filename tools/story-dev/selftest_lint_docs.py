"""Self-test for spec S2-1 (backlog N3 + A4 + P9): `lint_docs.py` R8 (the byte RATCHET), `archive_sweep.py`,
`split_readme.py`, the `stop_prefixes` seam of `archive_doc_block.py`, and the three P9 consumers. Offline, ~20 s.

WHY THIS EXISTS. Each of these is a GUARD: R8 refuses doc growth that nobody recorded, the sweep refuses to move a
live item or lose a slug, the split refuses to lose a line, and the consumers keep a moved citation findable (or
evidence is DELETED as uncited). A guard never seen to fail is not a guard (CLAUDE.md rule 6), so every check below
has a FAULT arm (the guarded thing broken -> it must fire) and a CONTROL (the ordinary case, and a mere MENTION —
a fenced example, a table row — must not fire). Everything runs on SYNTHETIC trees in temp folders, each its own
throw-away git repository (R8 (d) compares against `git show HEAD:`); the real docs are only READ (the NOTE at the end).

  RX  every new regex: its compiled .pattern printed, a POSITIVE and a NEGATIVE list.
  R8-0 CONTROL the seeded synthetic tree is clean, with a waived mega-line, a 1,300-char FENCED line and a waived
       TABLE row (round 2: rows are no longer exempt).
  R8-1 FAULT a 1,300-char line appended to 04 -> exit 1 naming file:line. CONTROL the same text fenced -> exit 0;
       FAULT as a new table row -> exit 1. FAULT an unclosed fence -> still caught (fail toward catching). FAULT a
       mega-line opening with an inline ```code``` span -> caught, and the fence state does not flip.
  R8-2 FAULT 1 KB over the ceiling -> fail; AT the ceiling -> pass. A CRLF checkout measures the LF size.
  R8-3 FAULT a waived line grows by 1 char (both ends kept) -> fail; an in-place shrink -> pass; grown at its END
       -> fail naming --rewaive. FAULT a 2nd long line sharing a waived line's first 60 chars -> fail. FAULT by hand
       against HEAD with no history: chars bumped, `count` bumped, `tails` edited -> (d) fails. FAULT (the checker's
       inherit.py) an unrelated line starting like a waived one is not covered; --rewaive records + prints it.
  R8-4 FAULT a ceiling raised against HEAD with no `raised` record -> fail; CONTROL [CRITIC] the same raise WITH
       one (`--raise`) -> pass, PRINTED. FAULT a committed raised record removed; a headroom raise; a NEW waiver.
       R8-4b FAULT a `/`-keyed ceiling removed (file kept) -> fail; CONTROL removed with its file -> pass.
       R8-4c `--raise ai_player/README.md` adds the key on the record; CONTROL a missing / escaping path -> refused.
  R8-5 `--ratchet` lowers to max(target, size + headroom), never raises; run twice, the 2nd is a byte no-op.
  R8-6 FAULT a stale waiver -> fail; `--rewaive` drops it -> pass.
  R8-7 THE DOC EDITOR'S WORKFLOW: a sentence appended inside a waived mega-line -> R8 fails; `--rewaive` without
       --why REFUSES and writes nothing; with --why it records the growth, and the lint PRINTS it. The line's START
       edited -> `--rewaive` RE-KEYS it (twice before a commit: lineage). A NEW long line, or a file over its
       ceiling -> `--rewaive` REFUSES.
  R8-8 `--seed` is refused once the JSON is committed.  R8-9 a missing JSON fails; no git -> (d) SKIPPED, LOUDLY.
  S-1 the dry run leaves the tree byte-identical.  S-2 a closed block moves and every slug it held is still found
      in the source by grep, ON the pointer; FAULT a pointer builder that drops a slug -> refused before writing
      (dry run and apply), nothing written; FAULT a write that differs from the simulation -> the tripwire.
  S-3 an ✅ section still holding `- [ ]`, and a MIXED heading, are NEVER selected (CONTROL: the open box closed ->
      selected); R7-closed but "NOT FIXED" / heading-only / fenced-heading blocks are skipped with their reason.
      Round 2: a BODY that keeps the block open (the checker's 05 MIXED / `* ⛔ STILL OPEN` shape, an indented, `*`
      or numbered open box, UNFIXED after an emoji) -> never selected, with its reason; CONTROL the clean body, the
      marker inside a fence, lower-case prose -> selected.
  S-4 after --apply, `lint_docs.py` and `audit_doc_consistency.py` pass on the synthetic tree; the ceiling followed
      the bytes down; a second sweep moves nothing.  S-5 split lines: every piece <= 1,200, the join equals the
      original, never a cut that starts a block or splits a code span; FAULT arms on the join and block checks.
      Round 2: a quote line and a quote-list line split on --apply in the same run as a move; FAULT a lost word, and
      a piece that drops its `>`, are refused BEFORE any write (source sha1 unchanged, no archive created).
  S-6 FAULT sweeping a copy outside the docs folder leaves R8's JSON byte-identical ("R8 not updated").
  S-7 (round 3) the rehearsal LINTS the complete would-be result: FAULT the round-2 checker's shape (04 at its 900-line
      budget, `--apply --split-lines` crosses it) and a sweep + split crossing 03's 4,400 -> refused naming R3, the
      source, the archive and both JSON files byte-identical; CONTROL the split landing exactly AT 900, and a plain
      sweep, apply. FAULT an unrecorded headroom raise -> R8 (d) still runs on the rehearsed copy. Also round 3:
      S-3 arms for the checker's shapes.py (UNDRIVEN mid-sentence, 'Unverified claim', a table-cell box, ...), and
      R8-1's table-row refusal says a row cannot be split.
  AD  archive_doc_block: its own --self-test passes; `stop_prefixes` moves a whole `###` section (CONTROL: the
      default still stops at the first bullet).
  P9-1 evidence cited ONLY from `readme/step-x.md` -> `prune_evidence.py` dry run KEEPs it; FAULT CITING without the
       glob -> INDEX AND DELETE (the data-loss path).  P9-2 `check_lessons` resolves a quote living in a moved
       section; FAULT without the folder -> fails.  P9-3 `disk_budget.citing_text()` includes it; FAULT without.
  P9-4 split_readme: sections before == after (ordered, no loss); FAULT arms for loss, reorder, a stale KEEP, an
       unclosed fence, a second split, a colliding planner, an existing folder, a corrupted write.

Run: cd tools/story-dev && py -3.12 selftest_lint_docs.py [--tools-dir <copy of tools/story-dev>] [--gates-dir <copy
     of ai_player/gates>]   (the two flags point the test at scratch copies: that is how call-deleting mutants run)
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TOOLS = HERE
GATES = REPO / "ai_player" / "gates"
if "--tools-dir" in sys.argv:
    TOOLS = Path(sys.argv[sys.argv.index("--tools-dir") + 1]).resolve()
if "--gates-dir" in sys.argv:
    GATES = Path(sys.argv[sys.argv.index("--gates-dir") + 1]).resolve()
sys.path.insert(0, str(TOOLS))

import archive_doc_block as adb  # noqa: E402
import archive_sweep as sw  # noqa: E402
import lint_docs as ld  # noqa: E402
import split_readme as sr  # noqa: E402

RESULTS: "list[tuple[str, bool, str]]" = []
NOTES: "list[str]" = []
REGISTRY = REPO / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ENV = dict(os.environ, PYTHONUTF8="1")


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def quiet(fn, *args, **kw):
    """(result or the SystemExit raised, everything printed)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            result = fn(*args, **kw)
        except SystemExit as exc:
            result = exc
    return result, buf.getvalue()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          cwd=repo, capture_output=True, text=True, check=True).stdout


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------------------------------------- synthetic tree
SENT = "Sentence {} records one more measured detail of the work and the reason it was done."


def prose(prefix: str, n: int) -> str:
    return prefix + " ".join(SENT.format(i) for i in range(n))


STATE_LINE = prose("**STATE NOTE:** the synthetic handoff's one long paragraph. ", 20)
CLOSED_MEGA = prose("  Closed-block detail, waived when R8 shipped. ", 18)
FENCED_LONG = "x " * 650
TABLE_LONG = "| key | " + "cell " * 260 + "|"
OPEN_ITEMS = "\n".join(f"- [ ] `#90-open{i}` — an open item that is still live\n  its detail" for i in range(30))
CLOSED_DONE = ("### ✅ `#90-closedone` — DONE 2026-10-01\n- [x] the closed work; the bug KI-901 is fixed here\n"
               "  detail line one\n" + CLOSED_MEGA + "\n")
STILL_OPEN = "### ✅ `#90-stillopen` — DONE 2026-10-02\n- [ ] the one box still open\n"
FENCED_EXAMPLE = "```text\n### ✅ `#90-example` — DONE (an example in a fence)\n- [x] example body\n```\n"
PUNCH = ("# Punch List — synthetic\n\n## Now\n\n" + OPEN_ITEMS + "\n\n" + FENCED_EXAMPLE + "\n" + CLOSED_DONE + "\n"
         + STILL_OPEN + "\n"
         "### ‼ `#90-mixed` — MIXED: ✅ the first half DONE\n- [x] the done half\n\n"
         "### ✅ `#90-notfixed` — NOT FIXED in the fork, DONE in sandbox\n- [x] the sandbox half\n\n"
         "### ✅ `#90-bare` — DONE 2026-10-03\n"
         "### ✅ `#90-fenced` — DONE 2026-10-04\n- [x] its example:\n```text\n## an example heading inside a fence\n"
         "```\n  after the fence\n\n"
         "### ⭐ `#90-live` — an open item\n- [ ] live\n")


def handoff(extra: str = "") -> str:
    return ("# Handoff — synthetic\n\n## YOU ARE HERE\n\n" + STATE_LINE + "\n\n```text\n" + FENCED_LONG + "\n```\n\n"
            "| key | value |\n|---|---|\n" + TABLE_LONG + "\n" + extra)


class Tree:
    """A throw-away git repo: `PROJECT KNOWLEDGE/` (00-05, 28, 29) + `tools/story-dev/` (R8's JSON), committed."""

    def __init__(self, base: Path, punch: str = PUNCH, seed: bool = True):
        self.root = base
        self.docs = base / "PROJECT KNOWLEDGE"
        self.budget = base / "tools" / "story-dev"
        self.docs.mkdir(parents=True)
        self.budget.mkdir(parents=True)
        self.write("00-README.md", "# Reading order\n\n1. `04-HANDOFF.md` — the handoff\n2. `03-PUNCH-LIST.md`\n")
        self.write("01-VISION-AND-DESIGN.md", "# Vision\n\nA synthetic tree for selftest_lint_docs.py.\n")
        self.write("02-ARCHITECTURE.md", "# Architecture\n\nNothing to see.\n")
        self.write("03-PUNCH-LIST.md", punch)
        self.write("04-HANDOFF.md", handoff())
        self.write("05-KNOWN-ISSUES.md", "# Known issues — synthetic\n\n## Open\n\n- none open today\n")
        self.write("28-HANDOFF-ARCHIVE.md", "# 28 — handoff archive (synthetic)\n")
        shutil.copyfile(REGISTRY, self.docs / REGISTRY.name)
        _git(base, "init", "-q")
        if seed:
            rc, out = quiet(ld.seed, self.docs, self.budget)
            assert rc == 0, out
        self.commit("synthetic tree")

    def write(self, name: str, text: str) -> None:
        (self.docs / name).write_text(text, encoding="utf-8", newline="\n")

    def read(self, name: str) -> str:
        return (self.docs / name).read_text(encoding="utf-8")

    def cj(self) -> dict:
        return json.loads((self.budget / ld.CEILINGS_NAME).read_text(encoding="utf-8"))

    def wj(self) -> dict:
        return json.loads((self.budget / ld.WAIVERS_NAME).read_text(encoding="utf-8"))

    def save(self, which: str, data: dict) -> None:
        (self.budget / which).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def commit(self, msg: str) -> None:
        files = [p.relative_to(self.root).as_posix() for p in self.root.rglob("*")
                 if p.is_file() and ".git" not in p.relative_to(self.root).parts]
        _git(self.root, "add", "--", *files)
        _git(self.root, "commit", "-q", "-m", msg)

    def digest(self) -> str:
        h = hashlib.sha256()
        for p in sorted(self.root.rglob("*")):
            if p.is_file() and ".git" not in p.relative_to(self.root).parts:
                h.update(p.relative_to(self.root).as_posix().encode() + b"\0" + p.read_bytes())
        return h.hexdigest()

    def r8(self):
        return ld.check_r8(self.docs, self.budget)

    def cli(self, *args: str) -> "tuple[int, str]":
        done = subprocess.run([sys.executable, str(TOOLS / "lint_docs.py"), "--docs-dir", str(self.docs),
                               "--budget-dir", str(self.budget), "--repo-dir", str(REPO), *args],
                              cwd=TOOLS, capture_output=True, text=True, encoding="utf-8", env=ENV)
        return done.returncode, done.stdout + done.stderr


def fresh(punch: str = PUNCH) -> "tuple[tempfile.TemporaryDirectory, Tree]":
    tmp = tempfile.TemporaryDirectory()
    return tmp, Tree(Path(tmp.name), punch)


def has(fails: "list[str]", *words: str) -> bool:
    return any(all(w in f for w in words) for f in fails)


# ------------------------------------------------------------------------------------------------------------ RX
def t_regexes() -> None:
    cases = [
        ("SLUG_RE", sw.SLUG_RE, ["`#24-foo`", "see #28-trainer-improvements.", "#24-trainmap+"],
         ["##24-foo", "C#24-x", "#2-foo", "issue #245"]),
        ("KI_RE", sw.KI_RE, ["KI-66", "KI-47b", "(KI-901)"], ["SKI-66", "KI-", "KIx-5"]),
        ("NOT_CLOSED_RE", sw.NOT_CLOSED_RE,
         ["NOT FIXED", "UNRESOLVED", "STILL OPEN", "OPEN", "REOPENED", "IN REVIEW", "PARTIAL", "NEXT", "NOT YET DONE",
          "MIXED", "SOME ARE FIXED", "PENDING",
          # round 2: the checker's five headings that R7 counted closed AND the sweep selected, plus the new words
          "### ✅ PART 1 DONE; PART 2 UNFIXED", "### FIXED IN SANDBOX — NOT YET PROMOTED", "### ✅ FIXED (UNVERIFIED LIVE)",
          "### ✅ DONE (DEFERRED)", "### ✅ FIXED, TWO ITEMS OUTSTANDING", "PARKED", "WIP", "IN PROGRESS", "BLOCKED",
          "AWAITING THE USER", "TODO",
          # round 3: the four headings the round-2 checker still saw selected
          "### ✅ FIXED IN SANDBOX — NOT PROMOTED", "### ✅ FIXED (NOT VERIFIED LIVE)", "### ✅ FIXED — UNDRIVEN",
          "### ✅ FIXED — UNTESTED"],
         ["✅ DONE 2026-10-01", "FIXED AND PROMOTED", "OPENED 2026-09-05", "CLOSED.", "RESOLVED", "DONE AND CLOSED",
          "FIXED (VERIFIED LIVE)", "UNPARKED AND DONE", "WIPED THE SAVE, DONE", "TODOS DONE"]),
        ("BODY_OPEN_RE", sw.BODY_OPEN_RE,
         ["**🔶 MIXED — TWO OF THESE ARE DONE AND TWO ARE GENUINELY OPEN.**",
          "* ⛔ **STILL OPEN — Doubles are UNEXERCISED.**", "⛔ **STILL OPEN:** the owner filter is UNFIXED",
          "- OPEN: the second half", "  1. PENDING the review", "> - ⚠ NOT FIXED in custom", "⇒ NEXT: build it",
          "the fix landed, ⏳ AWAITING the user's ruling", "- [x] **UNVERIFIED** live"],
         ["open the menu and press A", "- the menu is OPEN when the bag is shown", "**FIXED** and promoted",
          "- ✅ FIXED — no longer open", "Status — OPEN (an em dash is punctuation, not a mark)", "**Opened** 2026-09-05",
          "the word OPEN in plain prose"]),
        ("BODY_OPEN_ANY_RE", sw.BODY_OPEN_ANY_RE,
         ["Fights 2-5 remain UNDRIVEN.", "⚠ **Unverified claim worth probing:**", "- UNTESTED: the doubles path",
          "- ⛔ NOT VERIFIED live", "- ⛔ **NOT PROMOTED** to custom yet", "- part 2 is NOT DONE.",
          "- ⛔ FOLLOW-UP: retest", "a follow-up is filed", "- ⚠ **KNOWN GAP:** doubles", "STILL OPEN: the filter",
          "Still open: the filter", "> - still open: x", "#### STILL OPEN — doubles", "#### Open questions",
          "##### Open question", "| item | [ ] |", "| a | - [~] partial |", "> | x | [ ] |"],
         ["open the menu", "DRIVEN AND VERIFIED", "it was done and promoted", "the gap is closed",
          "#### Opened 2026-09-05", "#### how to open the bag", "| a | [x] |", "a [ ] outside a table",
          "the bag stays still; open it", "KNOWN GAPLESS", "UNDRIVENX"]),
        ("OPEN_BOX_RE", sw.OPEN_BOX_RE, ["- [ ] x", "  * [ ] x", "    - [~] x", "1. [ ] x", "> - [ ] x", "+ [ ] x"],
         ["- [x] x", "text [ ] x", "-[ ] x", "`- [ ] x` quoted in prose"]),
        ("BLOCK_START_RE", sw.BLOCK_START_RE,
         ["- item", "* item", "+ item", "> quote", "# h", "### h", "1. item", "12) x", "```", "~~~", "| a |", "<div>",
          "---", "***", "___", "- - -", "===", "--", "-"],
         ["Sentence two.", "-1 is negative", "**bold** text", "#hashtag", "1.5 is a number", "(a paren)", "`code`"]),
        ("POINTER_RE", sr.POINTER_RE, ["> moved: The battles (build step 4) -> readme/04-the-battles-build-step-4.md"],
         ["> moved: x -> readme/4-x.md", "> moved x -> readme/01-x.md", "moved: x -> readme/01-x.md",
          "> moved: x -> readme/01-X.md"]),
        ("LIST_ITEM_RE", sw.LIST_ITEM_RE, ["- [ ] x", "  * x", "1. x", "10) x"], ["-x", "text - x", "1.x"]),
        ("QUOTE_RE", sw.QUOTE_RE, ["> x", "> > x", "   > x", ">x"], ["x > y", "    > x", "→ x", "- > x"]),
    ]
    for name, rx, pos, neg in cases:
        print(f"  RX {name}.pattern = {rx.pattern!r}")
        miss = [s for s in pos if not rx.search(s.upper() if name == "NOT_CLOSED_RE" else s)]
        hit = [s for s in neg if rx.search(s.upper() if name == "NOT_CLOSED_RE" else s)]
        check(f"RX {name}: every positive matches", not miss, f"missed {miss}")
        check(f"RX {name}: no negative matches", not hit, f"matched {hit}")


# ------------------------------------------------------------------------------------------------------------- R8
def t_r8_0_1() -> None:
    tmp, t = fresh()
    with tmp:
        fails, notes, rows = t.r8()
        check("R8-0 CONTROL the seeded tree is clean (waived mega-line, fenced + table long lines)", not fails, str(fails))
        longs = ld.long_lines(t.read("04-HANDOFF.md"))
        check("R8-0 the fenced long line is NOT counted; the prose line AND the table row are (round 2: rows are "
              "waived like prose, no longer exempt)",
              [x for _, x in longs] == [STATE_LINE, TABLE_LONG], str([(n, len(x)) for n, x in longs]))
        rc, out = t.cli()
        check("R8-0 CONTROL the CLI exits 0 on the clean synthetic tree", rc == 0, out[-600:])
        text = "y" * 1300
        n = handoff().count("\n") + 1
        t.write("04-HANDOFF.md", handoff(text + "\n"))
        rc, out = t.cli()
        check("R8-1 FAULT a 1,300-char line appended -> exit 1, naming file and line",
              rc == 1 and f"04-HANDOFF.md:{n}: 1,300 characters" in out, out[-500:])
        t.write("04-HANDOFF.md", handoff("```text\n" + text + "\n```\n"))
        rc, out = t.cli()
        check("R8-1 CONTROL the same text inside a fence -> exit 0 (an example)", rc == 0, out[-400:])
        row = "| row | " + text + " |"
        t.write("04-HANDOFF.md", handoff(row + "\n"))
        rc, out = t.cli()
        check("R8-1 FAULT the same text as a NEW table row -> exit 1 (round 2: a row is no longer exempt)",
              rc == 1 and f"04-HANDOFF.md:{n}: {len(row):,} characters" in out, out[-400:])
        # Round 3: a line break ENDS a table row, so "split it" was wrong advice for one. CONTROL: prose keeps it.
        row_msg = next((x for x in out.splitlines() if f"04-HANDOFF.md:{n}:" in x), "")
        check("R8-1 the refusal for a long TABLE ROW says it cannot be split (shorten to 1,200 or move the detail "
              "into a linked section), never 'Split it'",
              "table row cannot be split" in row_msg and "shorten it to 1,200" in row_msg
              and "linked section" in row_msg and "Split it" not in row_msg, row_msg[-300:])
        t.write("04-HANDOFF.md", handoff(text + "\n"))
        fails, _, _ = t.r8()
        check("R8-1 CONTROL the refusal for a long PROSE line still says 'Split it' (no table-row advice)",
              has(fails, f"04-HANDOFF.md:{n}:", "Split it") and not has(fails, "table row cannot"), str(fails)[:300])
        t.write("04-HANDOFF.md", handoff("```text\n" + text + "\n"))
        fails, _, _ = t.r8()
        check("R8-1 FAULT an UNCLOSED fence does not hide a long line (fail toward catching)",
              has(fails, "04-HANDOFF.md:", "NOT waived"), str(fails)[:300])
        # A line OPENING with an inline ```code``` span is not a fence: read as one, it flipped the fence state and
        # hid itself and every line up to the next real fence (the checker's latent _blank_fenced desync).
        inline = "```x``` is inline code, " + "z" * 1300
        t.write("04-HANDOFF.md", handoff(inline + "\n" + text + "\n"))
        fails, _, _ = t.r8()
        check("R8-1 FAULT a mega-line that STARTS with an inline ```code``` span is caught, and so is the next one "
              "(the fence state did not flip)", has(fails, f"04-HANDOFF.md:{n}:", "NOT waived")
              and has(fails, f"04-HANDOFF.md:{n + 1}:", "NOT waived"), str(fails)[:400])
        check("R8-1 _blank_fenced: a real fence is still blanked (CONTROL) and the inline-span line is left alone (FAULT)",
              ld._blank_fenced("a\n```text\nhidden\n```\n```x``` shown\n").split("\n") == ["a", "", "", "", "```x``` shown", ""],
              repr(ld._blank_fenced("a\n```text\nhidden\n```\n```x``` shown\n")))

    # R7 is unchanged but now a shared FUNCTION (the sweep calls it), so it gets its own FAULT arm here.
    closed = "# Punch\n\n## Now\n\n- [ ] one open item\n\n### ✅ `#91-a` — DONE\n- [x] a\n  b\n  c\n  d\n  e\n  f\n"
    tmp = tempfile.TemporaryDirectory()
    with tmp:
        t = Tree(Path(tmp.name), closed)
        rc, out = t.cli()
        check("R7 FAULT a punch list that is mostly CLOSED content fires R7 (the shared predicate is wired)",
              rc == 1 and "R7  03-PUNCH-LIST.md" in out, out[-400:])


def t_r8_2_3() -> None:
    tmp, t = fresh()
    with tmp:
        size = ld.doc_bytes(t.docs / "04-HANDOFF.md")
        c = t.cj()
        c["files"]["04-HANDOFF.md"]["ceiling"] = size - 1024
        t.save(ld.CEILINGS_NAME, c)
        fails, _, _ = t.r8()
        check("R8-2 FAULT 1 KB over the ceiling -> fail", has(fails, "04-HANDOFF.md", "over its ceiling"), str(fails))
        c["files"]["04-HANDOFF.md"]["ceiling"] = size
        t.save(ld.CEILINGS_NAME, c)
        fails, _, _ = t.r8()
        check("R8-2 CONTROL exactly AT the ceiling -> pass", not fails, str(fails))
        (t.docs / "04-HANDOFF.md").write_bytes(handoff().replace("\n", "\r\n").encode("utf-8"))
        fails, _, _ = t.r8()
        check("R8-2 a CRLF checkout measures the LF size (no machine-dependent fail)",
              ld.doc_bytes(t.docs / "04-HANDOFF.md") == size and not fails, str(fails))
        t.write("04-HANDOFF.md", handoff())
        c["files"]["04-HANDOFF.md"]["ceiling"] = size + 8192
        t.save(ld.CEILINGS_NAME, c)

        mid = len(STATE_LINE) // 2
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, STATE_LINE[:mid] + "z" + STATE_LINE[mid:]))
        fails, _, _ = t.r8()
        check("R8-3 FAULT a waived line grows by ONE character (in its middle: both ends kept) -> fail",
              has(fails, "WAIVED line GREW"), str(fails))
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, STATE_LINE.replace(SENT.format(5) + " ", "", 1)))
        fails, _, _ = t.r8()
        check("R8-3 CONTROL a waived line shrinks IN PLACE, keeping both ends -> pass with no bookkeeping",
              not fails, str(fails))
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, STATE_LINE + "z"))
        fails, _, _ = t.r8()
        check("R8-3 FAULT ... grown at its END (a new last 60) -> fail, telling the editor to run --rewaive",
              has(fails, "last 60 characters differ", "--rewaive"), str(fails))
        t.write("04-HANDOFF.md", handoff(STATE_LINE[:-5] + "\n"))
        fails, _, _ = t.r8()
        check("R8-3 FAULT a NEW long line sharing a waived line's first 60 chars -> fail",
              has(fails, "share the first 60"), str(fails))
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, STATE_LINE + " More."))
        w = t.wj()
        for entry in w["waivers"]:
            if entry["sha1"] == ld.waiver_key(STATE_LINE):
                entry["chars"] += 6
        t.save(ld.WAIVERS_NAME, w)
        fails, _, _ = t.r8()
        check("R8-3 FAULT a waiver's chars bumped by hand, no history record -> (d) fails",
              has(fails, "GREW", "against HEAD", "history"), str(fails))
        t.write("04-HANDOFF.md", handoff())
        w = json.loads(_git(t.root, "show", f"HEAD:tools/story-dev/{ld.WAIVERS_NAME}"))
        for entry in w["waivers"]:
            if entry["sha1"] == ld.waiver_key(STATE_LINE):
                entry["count"] = entry.get("count", 1) + 1
        t.save(ld.WAIVERS_NAME, w)
        fails, _, _ = t.r8()
        check("R8-3 FAULT a waiver's `count` raised by hand against HEAD (no record can make it legal) -> (d) fails",
              has(fails, "count never rises"), str(fails))
        for entry in w["waivers"]:
            if entry["sha1"] == ld.waiver_key(STATE_LINE):
                entry["count"] = 1
                entry["tails"] = [ld.waiver_tail("a different paragraph's end, written in by hand for the test")]
        t.save(ld.WAIVERS_NAME, w)
        fails, _, _ = t.r8()
        check("R8-3 FAULT a waiver's `tails` edited by hand against HEAD with no history record -> (d) fails",
              has(fails, "different `tails`", "no new `history`"), str(fails))

    # THE CHECKER'S inherit.py SHAPE: a waived line is cut to 300 characters and an UNRELATED 1,500-character line
    # starting with the same 60 is added elsewhere. Keyed on its start alone, the old waiver silently covered it.
    tmp, t = fresh()
    with tmp:
        new = (STATE_LINE[:60] + " UNRELATED NEW CONTENT: " + "a brand-new paragraph nobody waived. " * 50)[:1500]
        t.write("04-HANDOFF.md", handoff(new + "\n").replace(STATE_LINE, STATE_LINE[:300]))
        fails, _, _ = t.r8()
        check("R8-3 FAULT (inherit.py) an unrelated new line that starts like a waived one is NOT covered: it fails "
              "and tells the editor to run --rewaive", has(fails, "STARTS like a waived line", "--rewaive"), str(fails))
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "")
        fails, notes, _ = t.r8()
        check("R8-3 ... --rewaive RECORDS the new end and PRINTS it for review; the lint then passes, printing it too",
              rc == 0 and "RE-TAILED" in out and not fails and any("RE-TAILED" in x for x in notes)
              and any(r.get("to_tails") == [ld.waiver_tail(new)] for x in t.wj()["waivers"] for r in x["history"]),
              out + str(fails) + str(notes))


def t_r8_4() -> None:
    tmp, t = fresh()
    with tmp:
        c = t.cj()
        before = c["files"]["04-HANDOFF.md"]["ceiling"]
        c["files"]["04-HANDOFF.md"]["ceiling"] = before + 5000
        t.save(ld.CEILINGS_NAME, c)
        fails, _, _ = t.r8()
        check("R8-4 FAULT a ceiling raised against HEAD with no `raised` record -> fail",
              has(fails, "ceiling ROSE", "no new `raised` record"), str(fails))
        c["files"]["04-HANDOFF.md"]["ceiling"] = before
        t.save(ld.CEILINGS_NAME, c)
        rc, out = quiet(ld.raise_ceiling, t.docs, t.budget, "04-HANDOFF.md", before + 5000, "the queue grew on purpose")
        fails, notes, _ = t.r8()
        check("R8-4 CONTROL the same raise WITH a `raised` record (--raise) -> pass", rc == 0 and not fails, str(fails))
        check("R8-4 CONTROL ... and the raise is PRINTED for review",
              any("RAISE — NEW IN THIS DIFF" in n and "the queue grew on purpose" in n for n in notes), str(notes))
        rc, out = quiet(ld.raise_ceiling, t.docs, t.budget, "04-HANDOFF.md", before, "lowering is not a raise")
        check("R8-4 --raise refuses a value that is not a raise", rc == 2, out)
        t.commit("the raise")
        c = t.cj()
        c["files"]["04-HANDOFF.md"]["raised"] = []
        t.save(ld.CEILINGS_NAME, c)
        fails, _, _ = t.r8()
        check("R8-4 FAULT a committed `raised` record removed -> fail (append-only)",
              has(fails, "`raised` record was removed"), str(fails))
        c = json.loads(_git(t.root, "show", f"HEAD:tools/story-dev/{ld.CEILINGS_NAME}"))
        c["files"]["03-PUNCH-LIST.md"]["headroom"] = 50000
        t.save(ld.CEILINGS_NAME, c)
        fails, _, _ = t.r8()
        check("R8-4 FAULT a headroom raise (a looser ratchet) with no record -> fail", has(fails, "headroom ROSE"),
              str(fails))
        c["files"]["03-PUNCH-LIST.md"]["headroom"] = 8192
        t.save(ld.CEILINGS_NAME, c)
        new_line = prose("A brand-new mega paragraph. ", 16)
        t.write("04-HANDOFF.md", handoff(new_line + "\n"))
        w = t.wj()
        w["waivers"].append({"file": "04-HANDOFF.md", "sha1": ld.waiver_key(new_line), "chars": len(new_line),
                             "head": new_line[:60], "history": []})
        t.save(ld.WAIVERS_NAME, w)
        fails, _, _ = t.r8()
        check("R8-4 FAULT a NEW waiver (no committed waiver it replaces) -> fail", has(fails, "a NEW waiver"),
              str(fails))

    tmp, t = fresh()
    with tmp:
        k1 = ld.waiver_key(STATE_LINE)
        a = STATE_LINE.replace("**STATE NOTE:**", "**STATE MEMO:**", 1)
        b = prose("**STATE MORE:** a second long paragraph. ", 15)
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, a + "\n" + b))
        w = t.wj()
        w["waivers"] = [x for x in w["waivers"] if x["sha1"] != k1] + [
            {"file": "04-HANDOFF.md", "sha1": ld.waiver_key(line), "chars": len(line), "head": line[:60],
             "history": [{"date": "2026-10-21", "from_sha1": k1, "from_chars": len(STATE_LINE),
                          "to_chars": len(line), "why": "split in two"}]} for line in (a, b)]
        t.save(ld.WAIVERS_NAME, w)
        fails, _, _ = t.r8()
        check("R8-4 FAULT one committed long line became TWO waived ones (both claim its waiver) -> fail",
              has(fails, "two waivers both descend"), str(fails))
        t.write("04-HANDOFF.md", handoff())
        w = json.loads(_git(t.root, "show", f"HEAD:tools/story-dev/{ld.WAIVERS_NAME}"))
        w["waivers"].append({"file": "07-CHANGELOG.md", "sha1": "0" * 40, "chars": 5000, "head": "x", "history": []})
        t.save(ld.WAIVERS_NAME, w)
        fails, _, _ = t.r8()
        check("R8-4 FAULT a waiver for a file R8 does not check -> fail", has(fails, "holds waivers for `07-"),
              str(fails))
        w["waivers"].pop()
        t.save(ld.WAIVERS_NAME, w)
        c = t.cj()
        del c["files"]["01-VISION-AND-DESIGN.md"]
        t.save(ld.CEILINGS_NAME, c)
        fails, _, _ = t.r8()
        check("R8-4 FAULT a ceiling REMOVED from the JSON -> fail, both as a missing ceiling and against HEAD",
              has(fails, "01-VISION", "has no byte ceiling") and has(fails, "01-VISION", "was REMOVED"), str(fails))
        c = t.cj()
        c["files"]["01-VISION-AND-DESIGN.md"] = json.loads(_git(
            t.root, "show", f"HEAD:tools/story-dev/{ld.CEILINGS_NAME}"))["files"]["01-VISION-AND-DESIGN.md"]
        c["files"]["ai_player/README.md"] = {"ceiling": 4000, "headroom": 8192, "target": None, "raised": []}
        t.save(ld.CEILINGS_NAME, c)
        fails, notes, _ = t.r8()
        check("R8-4 a `/`-keyed extra file (the README's current part) with a ceiling but no file -> fail",
              has(fails, "ai_player/README.md", "does not exist"), str(fails))
        (t.root / "ai_player").mkdir()
        (t.root / "ai_player" / "README.md").write_text("# README\n\n" + "w" * 1300 + "\n", encoding="utf-8")
        fails, notes, _ = t.r8()
        check("R8-4 CONTROL ... once it exists R8 checks it like any doc (its long line is named), and the new "
              "ceiling is printed", fails == [f for f in fails if "ai_player/README.md:3" in f] and fails
              and any("NEW CEILING" in n for n in notes), str(fails) + str(notes))
        # R8-4b: the `/`-keyed file set must come from HEAD's keys too. From the worktree JSON alone, deleting the
        # README's entry removed the file from R8 entirely (no failure at all) and it could grow without limit.
        (t.root / "ai_player" / "README.md").write_text("# README\n\nshort\n", encoding="utf-8")
        t.commit("the README's current part is in R8")
        fails, _, _ = t.r8()
        check("R8-4b CONTROL the committed `/`-keyed ceiling is clean", not fails, str(fails))
        (t.root / "ai_player" / "README.md").write_text("# README\n\n" + "grown. " * 2000 + "\n", encoding="utf-8")
        c = t.cj()
        del c["files"]["ai_player/README.md"]
        t.save(ld.CEILINGS_NAME, c)
        fails, _, _ = t.r8()
        check("R8-4b FAULT a `/`-keyed ceiling REMOVED from the JSON (the README then grown) -> fail as a removed "
              "ceiling and as a missing one", has(fails, "ai_player/README.md", "was REMOVED")
              and has(fails, "ai_player/README.md", "has no byte ceiling"), str(fails))
        (t.root / "ai_player" / "README.md").unlink()
        fails, _, _ = t.r8()
        check("R8-4b CONTROL the key removed TOGETHER with its file (a retirement) -> pass, nothing resurrected",
              not fails, str(fails))

    # R8-4c: `--raise` takes a repo-relative key for a file R8 does not check yet (split_readme's documented step).
    tmp, t = fresh()
    with tmp:
        (t.root / "ai_player").mkdir()
        (t.root / "ai_player" / "README.md").write_text("# README\n\nthe current part\n", encoding="utf-8")
        rc, out = quiet(ld.raise_ceiling, t.docs, t.budget, "ai_player/README.md", 5000, "the P9 split's current part")
        fails, notes, _ = t.r8()
        entry = t.cj()["files"].get("ai_player/README.md", {})
        check("R8-4c --raise ai_player/README.md adds the ceiling WITH a `raised` record, and the lint prints it",
              rc == 0 and entry.get("ceiling") == 5000 and entry.get("raised", [{}])[0].get("from") == 0
              and not fails and any("NEW CEILING" in n for n in notes)
              and any("RAISE — NEW IN THIS DIFF" in n and "P9 split" in n for n in notes), out + str(fails) + str(notes))
        with tempfile.TemporaryDirectory() as sibling:
            (Path(sibling) / "outside.md").write_text("# not in this repository\n", encoding="utf-8")
            bad = [quiet(ld.raise_ceiling, t.docs, t.budget, arg, 5000, "x")[0]
                   for arg in ("ai_player/missing.md", f"../{Path(sibling).name}/outside.md",
                               str(Path(sibling) / "outside.md"))]
        check("R8-4c FAULT --raise refuses a missing file, and an EXISTING file outside the repository (relative "
              "`../` and absolute)", bad == [2, 2, 2], str(bad))


def t_r8_5() -> None:
    tmp, t = fresh()
    with tmp:
        t.write("03-PUNCH-LIST.md", PUNCH.replace(OPEN_ITEMS, OPEN_ITEMS[:200]))
        size = ld.doc_bytes(t.docs / "03-PUNCH-LIST.md")
        rc, out = quiet(ld.ratchet, t.docs, t.budget, [])
        c = t.cj()
        check("R8-5 --ratchet lowers the ceiling to size + headroom",
              rc == 0 and c["files"]["03-PUNCH-LIST.md"]["ceiling"] == size + 8192, out)
        h1 = hashlib.sha256((t.budget / ld.CEILINGS_NAME).read_bytes()).hexdigest()
        rc, out = quiet(ld.ratchet, t.docs, t.budget, [])
        h2 = hashlib.sha256((t.budget / ld.CEILINGS_NAME).read_bytes()).hexdigest()
        check("R8-5 a second --ratchet is a no-op (byte-identical JSON)", h1 == h2 and "no change" in out, out)
        t.write("03-PUNCH-LIST.md", PUNCH + "\n" + "- [ ] grown\n" * 1500)
        rc, out = quiet(ld.ratchet, t.docs, t.budget, [])
        fails, _, _ = t.r8()
        check("R8-5 FAULT a file grown past its ceiling: --ratchet NEVER raises (R8 then fails)",
              t.cj()["files"]["03-PUNCH-LIST.md"]["ceiling"] == size + 8192
              and has(fails, "03-PUNCH-LIST.md", "over its ceiling"), out)
        t.write("03-PUNCH-LIST.md", PUNCH.replace(OPEN_ITEMS, OPEN_ITEMS[:200]))
        c = t.cj()
        c["files"]["04-HANDOFF.md"]["ceiling"] = 100000
        c["files"]["04-HANDOFF.md"]["target"] = 30000
        t.save(ld.CEILINGS_NAME, c)
        rc, out = quiet(ld.ratchet, t.docs, t.budget, ["04-HANDOFF.md"])
        check("R8-5 the ratchet floors at the TARGET when it is above size + headroom",
              t.cj()["files"]["04-HANDOFF.md"]["ceiling"] == 30000, out)
        rc, out = quiet(ld.ratchet, t.docs, t.budget, ["nope.md"])
        check("R8-5 --ratchet refuses a file that is not an R8 file", rc == 2, out)


def t_r8_6_7() -> None:
    tmp, t = fresh()
    with tmp:
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, STATE_LINE[:1000]))
        fails, _, _ = t.r8()
        check("R8-6 FAULT a waiver whose line is gone -> STALE fails", has(fails, "STALE waiver"), str(fails))
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "")
        fails, _, _ = t.r8()
        check("R8-6 --rewaive drops it (a shrink, no --why) -> pass", rc == 0 and "DROPPED" in out and not fails,
              out + str(fails))

    tmp, t = fresh()
    with tmp:
        grown = STATE_LINE + " One more sentence, appended by the orchestrator."
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, grown))
        fails, _, _ = t.r8()
        check("R8-7a an appended sentence inside a waived mega-line -> R8 fails (a new end: run --rewaive)",
              has(fails, "last 60 characters differ", "--rewaive"), str(fails))
        h = hashlib.sha256((t.budget / ld.WAIVERS_NAME).read_bytes()).hexdigest()
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "")
        check("R8-7a FAULT --rewaive WITHOUT --why refuses and writes nothing",
              rc == 1 and "REFUSED" in out
              and hashlib.sha256((t.budget / ld.WAIVERS_NAME).read_bytes()).hexdigest() == h, out)
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "the O5 status sentence")
        fails, notes, _ = t.r8()
        delta = len(grown) - len(STATE_LINE)
        check("R8-7a --rewaive --why records the growth AND the new end, printing both with the size in characters",
              rc == 0 and "GREW" in out and f"(+{delta})" in out and "RE-TAILED" in out, out)
        check("R8-7a CONTROL the lint passes and PRINTS the growth with its why (Tier 1 sees it)",
              not fails and any("WAIVED LINE GREW" in n and "the O5 status sentence" in n for n in notes),
              str(fails) + str(notes))
        recorded = t.wj()
        bumped = json.loads(json.dumps(recorded))
        for x in bumped["waivers"]:
            if x["sha1"] == ld.waiver_key(STATE_LINE):      # only the recorded line (the table row has no record)
                x["chars"] += 5
        t.save(ld.WAIVERS_NAME, bumped)
        fails, _, _ = t.r8()
        check("R8-7a FAULT a recorded growth does not cover MORE growth: chars bumped 5 past the record -> (d) fails",
              has(fails, "GREW", "against HEAD", "history"), str(fails))
        t.save(ld.WAIVERS_NAME, recorded)
        t.commit("growth recorded")
        saved = t.wj()
        edited = json.loads(json.dumps(saved))
        for x in edited["waivers"]:
            x["history"] = []
        t.save(ld.WAIVERS_NAME, edited)
        fails, _, _ = t.r8()
        check("R8-7a FAULT a committed `history` record deleted from the JSON -> fail (append-only)",
              has(fails, "`history` record", "removed"), str(fails))
        t.save(ld.WAIVERS_NAME, saved)
        start = STATE_LINE.replace("**STATE NOTE:**", "**STATE MEMO:**", 1)
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, start))
        fails, _, _ = t.r8()
        check("R8-7b the line's START edited -> R8 fails (unwaived + stale)",
              has(fails, "NOT waived") and has(fails, "STALE"), str(fails))
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "")
        fails, notes, _ = t.r8()
        check("R8-7b --rewaive RE-KEYS it (paired against HEAD's version), the lint passes and prints the re-key",
              rc == 0 and "RE-KEYED" in out and not fails and any("RE-KEYED" in n for n in notes), out + str(fails))
        again = start.replace("**STATE MEMO:**", "**STATE INFO:**", 1)
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, again))
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "")
        fails, _, _ = t.r8()
        check("R8-7b a SECOND start edit before the commit re-keys through the lineage, and (d) accepts it",
              rc == 0 and "RE-KEYED" in out and not fails, out + str(fails))
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, again) + prose("Another new paragraph. ", 15) + "\n")
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "trying to waive a new line")
        check("R8-7c FAULT a NEW long line -> --rewaive REFUSES (split it instead)", rc == 1 and "a NEW line" in out,
              out)
        t.write("04-HANDOFF.md", handoff().replace(STATE_LINE, again + " grow"))
        c = t.cj()
        c["files"]["04-HANDOFF.md"]["ceiling"] = ld.doc_bytes(t.docs / "04-HANDOFF.md") - 1
        t.save(ld.CEILINGS_NAME, c)
        rc, out = quiet(ld.rewaive, t.docs, t.budget, "04-HANDOFF.md", "fits?")
        check("R8-7d FAULT --rewaive refuses when the FILE is over its ceiling", rc == 1 and "over its ceiling" in out,
              out)


def t_r8_8_9() -> None:
    tmp, t = fresh()
    with tmp:
        rc, out = quiet(ld.seed, t.docs, t.budget)
        check("R8-8 FAULT --seed is REFUSED once the JSON is committed (it would reset the ratchet)",
              rc == 1 and "REFUSED" in out, out)
        (t.budget / ld.WAIVERS_NAME).unlink()
        fails, _, _ = t.r8()
        check("R8-9 FAULT a missing JSON fails (a ratchet's state may not vanish silently)",
              has(fails, "cannot run", ld.WAIVERS_NAME), str(fails))
    with tempfile.TemporaryDirectory() as plain:
        tree_tmp, t = fresh()
        with tree_tmp:
            outside = Path(plain)
            for name in (ld.CEILINGS_NAME, ld.WAIVERS_NAME):
                shutil.copyfile(t.budget / name, outside / name)
            fails, notes, _ = ld.check_r8(t.docs, outside)
            check("R8-9 no git for the JSON -> (d) is SKIPPED LOUDLY (a WARN), never printed as a pass",
                  not fails and any("SKIPPED" in n and "did NOT run" in n for n in notes), str(notes))
            check("R8-9 CONTROL a committed JSON prints no skip and no NOT-CHECKED line",
                  not any("SKIPPED" in n or "NOT CHECKED" in n for n in t.r8()[1]), str(t.r8()[1]))


# ---------------------------------------------------------------------------------------------------------- sweep
def run_sweep(t: Tree, *extra: str, source: str = "03-PUNCH-LIST.md"):
    # --repo-dir: the rehearsal's lint scans bot code for R6; a --tools-dir COPY's own parents hold none.
    return quiet(sw.main, ["--source", str(t.docs / source), "--docs-dir", str(t.docs),
                           "--budget-dir", str(t.budget), "--repo-dir", str(REPO), "--date", "2026-10-21", *extra])


def t_sweep() -> None:
    tmp, t = fresh()
    with tmp:
        lines = t.read("03-PUNCH-LIST.md").splitlines()
        blocks = {b.heading.split("`")[1]: b for b in sw.find_blocks(lines)}
        chosen = [k for k, b in blocks.items() if b.reason is None]
        check("S-3 only the genuinely closed block is selected", chosen == ["#90-closedone"], str(chosen))
        check("S-3 FAULT an ✅ section still holding `- [ ]` is never selected (not even listed: R7 says open)",
              "#90-stillopen" not in blocks, str(list(blocks)))
        check("S-3 FAULT a MIXED heading is never selected (not even listed)", "#90-mixed" not in blocks,
              str(list(blocks)))
        check("S-3 a `###` line inside a fence is an example, never a block (R7 counts it; the sweep skips it)",
              "inside a fenced block" in (blocks.get("#90-example") and blocks["#90-example"].reason or ""),
              str(blocks.get("#90-example")))
        check("S-3 R7 counts '#90-notfixed' closed; the sweep skips it for 'NOT FIXED'",
              "#90-notfixed" in blocks and "NOT FIXED" in (blocks["#90-notfixed"].reason or ""),
              str(blocks.get("#90-notfixed")))
        check("S-3 a heading-only closed block is skipped: no body",
              "no body" in (blocks.get("#90-bare") and blocks["#90-bare"].reason or ""), str(blocks.get("#90-bare")))
        check("S-3 FAULT a block whose fenced `## ` line would end the MOVER's block early is skipped (no orphan)",
              "boundary differs" in (blocks.get("#90-fenced") and blocks["#90-fenced"].reason or ""),
              str(blocks.get("#90-fenced")))
        opened = sw.find_blocks(PUNCH.replace(STILL_OPEN, STILL_OPEN.replace("- [ ]", "- [x]")).splitlines())
        check("S-3 CONTROL the same text with the open box closed IS selected",
              any("#90-stillopen" in b.heading and b.reason is None for b in opened), "")
        mixed = sw.find_blocks(PUNCH.replace("### ‼ `#90-mixed` — MIXED: ✅ the first half DONE\n- [x] the done half",
                                             "### ✅ `#90-mixed` — MIXED: DONE\n- [x] the done half").splitlines())
        check("S-3 a MIXED heading with no open box is still never selected",
              not any("#90-mixed" in b.heading and b.reason is None for b in mixed), "")
        dup = sw.find_blocks((PUNCH + "\n" + CLOSED_DONE).splitlines())
        check("S-3 a duplicated heading is refused by the mover's anchor rule, never guessed",
              all(b.reason and "matched 2 lines" in b.reason for b in dup if "#90-closedone" in b.heading), "")

        # ROUND 2: THE BODY COUNTS. The checker's 05 shape: an ✅-headed block whose body says MIXED / STILL OPEN moved,
        # and two live items left the current-state file. Each shape below sits under an otherwise closed block.
        def verdict(extra: str) -> "sw.Block | None":
            text = ("# Punch\n\n## Now\n\n" + OPEN_ITEMS + "\n\n### ⛔⛔ `#92-review` — 2026-09-06, SAME NIGHT — A REVIEWER "
                    "FOUND A DEFECT. ✅ FIXED AND RE-DRIVEN CLEAN\n- [x] the fix, re-driven\n  its detail\n" + extra
                    + "\n### ⭐ `#92-next` — an open item\n- [ ] live\n")
            return next((b for b in sw.find_blocks(text.splitlines()) if "#92-review" in b.heading), None)
        control = verdict("")
        check("S-3 CONTROL the closed block with no open line in its body IS selected",
              control is not None and control.reason is None, str(control))
        for label, extra in (
                ("a body-level MIXED line (the checker's 05 shape)",
                 "**🔶 MIXED — TWO OF THESE ARE DONE AND TWO ARE GENUINELY OPEN. Each bullet carries its own marker,**\n"),
                ("a `* ⛔ **STILL OPEN**` bullet (the 05 shape)",
                 "* ⛔ **STILL OPEN — Doubles are UNEXERCISED.** The mapping is asserted, not driven\n"),
                ("a `⛔ **STILL OPEN:**` line", "⛔ **STILL OPEN:** the owner filter itself is UNFIXED and remains\n"),
                ("an INDENTED open box", "  - [ ] a nested sub-item, still open\n"),
                ("a `*` open box", "* [ ] a star-bullet box\n"),
                ("a numbered open box", "1. [ ] a numbered box\n"),
                ("an UNFIXED marker after an emoji", "⚠ UNFIXED in the fork: the same check\n")):
            got = verdict(extra)
            check(f"S-3 FAULT {label} in the BODY -> never selected, and the skip says why",
                  got is None or (got.reason is not None and "BODY" in got.reason), str(got))
        for label, extra in (("the same MIXED line inside a FENCED example (a mention)",
                              "```text\n**🔶 MIXED — an example of a marker**\n* [ ] an example box\n```\n"),
                             ("ordinary lower-case prose ('open the menu')", "open the menu, then the bag stays open\n")):
            got = verdict(extra)
            check(f"S-3 CONTROL {label} does NOT keep the block open", got is not None and got.reason is None, str(got))
        # ROUND 3: the round-2 checker's shapes.py GAP shapes (status words outside a marker position, or in sentence
        # case), plus the two real 05 caveats that moved ("Fights 2-5 remain UNDRIVEN.", "Unverified claim").
        for label, extra in (
                ("a line-start bare 'STILL OPEN:'", "STILL OPEN: the owner filter is unfixed.\n"),
                ("a sentence-case line-start 'Still open:'", "Still open: the owner filter.\n"),
                ("a '#### STILL OPEN' subheading", "\n#### STILL OPEN — doubles\nNot exercised.\n"),
                ("a '#### Open questions' subheading", "\n#### Open questions\n- why X?\n"),
                ("'UNDRIVEN' after an emoji", "- ⚠ Fights 2-5 remain UNDRIVEN.\n"),
                ("'UNDRIVEN' mid-sentence (the real 05 KI-93 caveat)", "  Fights 2-5 remain UNDRIVEN.\n"),
                ("'Unverified claim' in sentence case (the real 05 caveat)",
                 "⚠ **Unverified claim worth probing:** the doubles path\n"),
                ("an 'UNTESTED:' bullet", "- UNTESTED: the doubles path.\n"),
                ("'NOT VERIFIED'", "- ⛔ NOT VERIFIED live.\n"),
                ("'NOT PROMOTED'", "- ⛔ **NOT PROMOTED** to custom yet.\n"),
                ("an open box inside a TABLE cell", "| item | [ ] |\n"),
                ("'FOLLOW-UP'", "- ⛔ FOLLOW-UP: retest on doubles.\n"),
                ("'KNOWN GAP'", "- ⚠ **KNOWN GAP:** doubles.\n"),
                ("'NOT DONE' in plain prose", "- part 2 is NOT DONE.\n")):
            got = verdict(extra)
            check(f"S-3 FAULT (round 3) {label} in the BODY -> never selected, and the skip says why",
                  got is None or (got.reason is not None and "BODY" in got.reason), str(got))
        for label, extra in (("a closed `- [X]` box", "- [X] done\n"), ("a `- [-]` dropped box", "- [-] dropped\n"),
                             ("lower-case 'open the menu'", "Fixed: open the menu first.\n"),
                             ("a closed box in a table cell", "| item | [x] |\n"),
                             ("a '#### Opened' subheading (not OPEN)", "\n#### Opened 2026-09-05\ndetail\n")):
            got = verdict(extra)
            check(f"S-3 CONTROL (round 3) {label} does NOT keep the block open", got is not None and got.reason is None,
                  str(got))

        before = t.digest()
        rc, out = run_sweep(t)
        check("S-1 the dry run leaves the tree byte-identical", rc == 0 and t.digest() == before and
              "MOVE  line" in out and "#90-closedone" in out, out[-600:])

        real_make = sw.make_pointer
        try:
            sw.make_pointer = lambda h, b, a, d: real_make(h, b, a, d).split("\n")[0]
            _, plan = sw.plan_sweep(t.docs / "03-PUNCH-LIST.md", "32-PUNCH-LIST-ARCHIVE.md", "2026-10-21")
            dry = [b for b in plan if "#90-closedone" in b.heading]
            check("S-2 FAULT a pointer that drops a slug: the DRY RUN reports the block refused",
                  dry and "lose slug" in (dry[0].reason or ""), str(dry))
            rc, out = quiet(sw.apply_sweep, t.docs / "03-PUNCH-LIST.md", t.docs / "32-PUNCH-LIST-ARCHIVE.md",
                            "2026-10-21")
            check("S-2 FAULT ... and --apply REFUSES before writing, nothing written (no archive created)",
                  isinstance(rc, SystemExit) and "lose slug" in str(rc) and "KI-901" in str(rc)
                  and t.digest() == before, str(rc)[:300])
        finally:
            sw.make_pointer = real_make

        real_move = sw.adb.archive_block
        try:
            def tampered(source, archive, starts, pointer, note, **kw):
                return real_move(source, archive, starts, pointer.replace("nothing deleted", "nothing deleted!"),
                                 note, **kw)
            sw.adb.archive_block = tampered
            rc, out = quiet(sw.apply_sweep, t.docs / "03-PUNCH-LIST.md", t.docs / "32-PUNCH-LIST-ARCHIVE.md",
                            "2026-10-21")
            check("S-2 FAULT a write that differs from the simulated source -> the TRIPWIRE fires",
                  isinstance(rc, SystemExit) and "TRIPWIRE" in str(rc), str(rc)[:200])
        finally:
            sw.adb.archive_block = real_move

    tmp, t = fresh()
    with tmp:
        ceiling_before = t.cj()["files"]["03-PUNCH-LIST.md"]["ceiling"]
        rc, out = run_sweep(t, "--apply")
        src, arc = t.read("03-PUNCH-LIST.md"), t.read("32-PUNCH-LIST-ARCHIVE.md")
        pointer = [line for line in src.splitlines() if "#90-closedone" in line]
        check("S-2 --apply moves the closed block VERBATIM to the new archive",
              rc == 0 and "the closed work; the bug KI-901 is fixed here" in arc and CLOSED_MEGA in arc
              and "detail line one" not in src, out[-500:])
        check("S-2 every slug the block held is still found in the source by grep, ON the pointer",
              pointer and "ARCHIVED VERBATIM" in pointer[0] and re.search(r"\bKI-901\b", src)
              and sw.slugs_in(CLOSED_DONE) <= sw.slugs_in(src), str(pointer))
        src_lines = src.splitlines()
        at = src_lines.index(pointer[0])
        check("S-2 the pointer keeps the blank line the block ended with (the next heading is not glued on)",
              src_lines[at + 1].startswith("Slugs kept for grep") and src_lines[at + 2] == ""
              and src_lines[at + 3].startswith("### ✅ `#90-stillopen`"), str(src_lines[at:at + 4]))
        rc_l, out_l = t.cli()
        # The REAL audit (this checkout's, never a copy), pointed at the synthetic docs; it has no docs-dir flag.
        audit = subprocess.run([sys.executable, "-c",
                                "import os, sys, pathlib; sys.argv = ['audit_doc_consistency.py']; "
                                "import audit_doc_consistency as a; a.DOCS = pathlib.Path(os.environ['SYNTH_DOCS']); "
                                "sys.exit(a.main())"],
                               cwd=HERE, capture_output=True, text=True, encoding="utf-8",
                               env=dict(ENV, SYNTH_DOCS=str(t.docs)))
        check("S-4 lint_docs.py passes on the synthetic tree after --apply", rc_l == 0, out_l[-800:])
        check("S-4 audit_doc_consistency.py passes on the synthetic tree after --apply", audit.returncode == 0,
              (audit.stdout + audit.stderr)[-800:])
        after = t.cj()["files"]["03-PUNCH-LIST.md"]["ceiling"]
        check("S-4 the ceiling FOLLOWED the bytes down (the sweep ratchets) and the moved line's waiver is gone",
              after < ceiling_before and after == ld.doc_bytes(t.docs / "03-PUNCH-LIST.md") + 8192
              and not any(w["sha1"] == ld.waiver_key(CLOSED_MEGA) for w in t.wj()["waivers"]),
              f"{ceiling_before} -> {after}")
        digest = t.digest()
        rc, out = run_sweep(t, "--apply")
        check("S-4 a second sweep moves nothing (the pointer is never re-archived)",
              rc == 0 and t.digest() == digest and "MOVED" not in out, out[-400:])

    # ROUND 2: R8's bookkeeping runs ONLY for the real R8 file. Matched by basename, sweeping a COPY of 03 in a scratch
    # folder ratcheted the real JSON against the real 03 — a write to the project tree from an experiment.
    tmp, t = fresh()
    with tmp, tempfile.TemporaryDirectory() as other:
        copy = Path(other) / "03-PUNCH-LIST.md"
        copy.write_text(t.read("03-PUNCH-LIST.md"), encoding="utf-8", newline="\n")
        # One open item dropped: enough bytes for a ratchet to lower, while R7's closed share stays under its 25%
        # (round 3: the rehearsal now lints the docs folder, and a red tree refuses every apply).
        t.write("03-PUNCH-LIST.md", t.read("03-PUNCH-LIST.md").replace(OPEN_ITEMS, OPEN_ITEMS.split("\n", 2)[2]))
        before = {n: (t.budget / n).read_bytes() for n in (ld.CEILINGS_NAME, ld.WAIVERS_NAME)}
        rc, out = quiet(sw.main, ["--source", str(copy), "--archive", str(Path(other) / "32-PUNCH-LIST-ARCHIVE.md"),
                                  "--apply", "--docs-dir", str(t.docs), "--budget-dir", str(t.budget),
                                  "--repo-dir", str(REPO), "--date", "2026-10-21"])
        after = {n: (t.budget / n).read_bytes() for n in (ld.CEILINGS_NAME, ld.WAIVERS_NAME)}
        check("S-6 FAULT sweeping a COPY outside the docs folder leaves R8's JSON byte-identical (the real 03, "
              "shrunk so a ratchet WOULD lower it, is not consulted)",
              rc == 0 and "MOVED" in out and before == after and "R8 not updated (not the real file)" in out,
              out[-400:])


def t_split() -> None:
    item = "- [ ] `#90-x` — " + " ".join(SENT.format(i) for i in range(40))
    pieces = sw.split_line(item)
    check("S-5 a mega list item splits: every piece <= 1,200 and the whitespace-normalised join equals it",
          pieces and all(len(p) <= 1200 for p in pieces)
          and " ".join(" ".join(p.split()) for p in pieces) == " ".join(item.split()), str(pieces and len(pieces)))
    check("S-5 continuation lines sit at the item's content column and start no new block",
          pieces and all(p.startswith("  ") and not p.startswith("   ") and not sw.BLOCK_START_RE.match(p.lstrip())
                         for p in pieces[1:]), "")
    check("S-5 CONTROL a heading, a table row, an unbroken run and 4-space-indented prose (an indented code block) "
          "are never split",
          all(sw.split_line(x) is None for x in ("### " + item, "| " + item + " |", "x" * 1300,
                                                 "    " + item[2:])), "")
    for prefix in ("> ", "> > "):
        quoted = prefix + "   " + " ".join(SENT.format(i) for i in range(40))
        pieces = sw.split_line(quoted)
        check(f"S-5 a blockquote mega-line ({prefix.strip()!r}) splits with its markers on EVERY piece, each <= 1,200, "
              f"the join unchanged",
              pieces is not None and all(p.startswith(prefix + "   ") and len(p) <= 1200 for p in pieces)
              and " ".join(" ".join(p[len(prefix):].split()) for p in pieces) == " ".join(quoted[len(prefix):].split()),
              str(pieces and [p[:12] for p in pieces]))
    # The `. ` of "end." ends at body column 1,199: it fits 1,200 WITHOUT the 2-char quote marker and not with it.
    body = ("word " * 100 + "early. ").ljust(1195, "z") + "end. " + "tail " * 100
    pieces = sw.split_line("> " + body)
    check("S-5 the quote marker counts toward the 1,200 (the cut falls back to an earlier one)",
          pieces is not None and all(len(p) <= 1200 for p in pieces) and pieces[0].endswith("early."),
          str(pieces and [len(p) for p in pieces]))
    pieces = sw.split_line(CLOSED_MEGA)
    check("S-5 CONTROL 2-space continuation prose splits, its pieces keep the 2-space indent",
          pieces is not None and all(p.startswith("  ") for p in pieces), "")
    # The LAST `. ` before 1,200 would start a quote; the only safe cut is the earlier "early. ".
    quote = "word " * 120 + "early. " + "word " * 110 + "end. > quoted words " + "z" * 100 + " later text" * 20
    pieces = sw.split_line(quote)
    check("S-5 FAULT the last cut would start a block (a quote): an earlier safe cut is taken instead",
          pieces is not None and not any(sw.BLOCK_START_RE.match(p.lstrip()) for p in pieces[1:]),
          str(pieces and [p[:16] for p in pieces]))
    bullet = "word " * 200 + "end. - not a bullet " + "z " * 300
    pieces = sw.split_line(bullet)
    check("S-5 CONTROL a dash after a full stop: cut AFTER the dash, never before it (no bullet created)",
          pieces is not None and pieces[0].endswith("end. -") and pieces[1].startswith("not a bullet"),
          str(pieces and [p[-12:] for p in pieces]))
    # The LAST `. ` before 1,200 sits inside a code span; the only safe cut is the earlier "early. ".
    code = ("a " * 300 + "early. " + "a " * 20 + "`code " + "q" * 400 + " inner. still code " + "q" * 300
            + "` after " + "b " * 100)
    pieces = sw.split_line(code)
    check("S-5 FAULT a cut inside a code span is never taken",
          pieces is not None and all(p.count("`") % 2 == 0 for p in pieces),
          str(pieces and [p.count("`") for p in pieces]))
    real_cut = sw._cut
    try:
        sw._cut = lambda line, indent, limit: [(p if i != 1 else p.replace("Sentence", "", 1))
                                               for i, p in enumerate(real_cut(line, indent, limit))]
        check("S-5 FAULT a cutter that drops a word -> refused by the join check", sw.split_line(item) is None, "")
        cut_at = item.index(" ", 10)        # at a SPACE, so the words survive and only the length check can fire
        sw._cut = lambda line, indent, limit: [line[:cut_at], indent + line[cut_at + 1:]]
        check("S-5 FAULT a cutter that leaves a piece over 1,200 (words intact) -> refused by the length check",
              sw.split_line(item) is None, "")
        at = bullet.index("end. - not") + 4
        sw._cut = lambda line, indent, limit: [line[:at], indent + line[at + 1:]]
        check("S-5 FAULT a cutter whose next piece starts a bullet (words intact) -> refused by the block check",
              sw.split_line(bullet) is None, "")
    finally:
        sw._cut = real_cut

    tmp, t = fresh()
    with tmp:
        h = t.digest()
        real_plan = sw.split_plan
        try:
            sw.split_plan = lambda lines: ({i: [p.replace("reason", "", 1) for p in ps]
                                            for i, ps in real_plan(lines)[0].items()}, [])
            rc, _ = quiet(sw.apply_splits, t.docs / "04-HANDOFF.md")
            check("S-5 FAULT a file-level split that loses a word -> refused, file untouched",
                  isinstance(rc, SystemExit) and "differ" in str(rc) and t.digest() == h, str(rc))
        finally:
            sw.split_plan = real_plan
        words = " ".join(t.read("04-HANDOFF.md").split())
        rc, out = run_sweep(t, "--apply", "--split-lines", source="04-HANDOFF.md")
        rc_l, out_l = t.cli()
        check("S-5 --apply --split-lines: no long prose line left (the table row stays: never split, it is waived), "
              "the words unchanged, the lint passes",
              rc == 0 and [x for _, x in ld.long_lines(t.read("04-HANDOFF.md"))] == [TABLE_LONG]
              and " ".join(t.read("04-HANDOFF.md").split()) == words and rc_l == 0, out[-300:] + out_l[-500:])

    # ROUND 2: BLOCKQUOTE mega-lines (13 of 04's 18) were refused at apply time by a whole-file word check that
    # counted every repeated `>` as a word — after the sweep had ALREADY written, under a "nothing written" message.
    quote_line = "> " + " ".join(SENT.format(i) for i in range(30))
    quote_list = "> - " + " ".join(SENT.format(i) for i in range(30, 60))
    punch = PUNCH.replace("## Now\n\n", "## Now\n\n" + quote_line + "\n\n" + quote_list + "\n\n", 1)
    tmp, t = fresh(punch)
    with tmp:
        src, arc = t.docs / "03-PUNCH-LIST.md", t.docs / "32-PUNCH-LIST-ARCHIVE.md"
        sha = hashlib.sha1(src.read_bytes()).hexdigest()
        real_plan = sw.split_plan
        try:
            sw.split_plan = lambda lines: ({i: [p.replace("reason", "", 1) for p in ps]
                                            for i, ps in real_plan(lines)[0].items()}, [])
            rc, out = run_sweep(t, "--apply", "--split-lines")
        finally:
            sw.split_plan = real_plan
        check("S-5 FAULT a split that would lose a word, with a closed block ALSO selected -> refused BEFORE any write: "
              "the source's sha1 unchanged and no archive created (the message is true)",
              isinstance(rc, SystemExit) and "nothing written" in str(rc) and "differ" in str(rc)
              and hashlib.sha1(src.read_bytes()).hexdigest() == sha and not arc.exists(), str(rc)[:300])
        real_split = sw.split_line
        try:
            # Words intact, but a continuation piece loses its `>`: the text would leave the quote.
            sw.split_line = lambda line, limit=sw.SPLIT_LIMIT: (
                None if (p := real_split(line, limit)) is None else [p[0]] + [x.lstrip("> ") for x in p[1:]])
            rc, out = run_sweep(t, "--apply", "--split-lines")
        finally:
            sw.split_line = real_split
        check("S-5 FAULT a split piece that drops its quote marker (words intact) -> refused before any write",
              isinstance(rc, SystemExit) and "blockquote depth" in str(rc)
              and hashlib.sha1(src.read_bytes()).hexdigest() == sha and not arc.exists(), str(rc)[:300])
        rc, out = run_sweep(t, "--apply", "--split-lines")
        text = t.read("03-PUNCH-LIST.md")
        rc_l, out_l = t.cli()
        quoted = [x for x in text.splitlines() if x.startswith("> ")]
        check("S-5 a QUOTE mega-line and a QUOTE-LIST mega-line split on --apply (with a block moved in the same run): "
              "every piece keeps its `> `, none is long, the words (quote markers aside) unchanged, the lint passes",
              rc == 0 and "MOVED" in out and len(quoted) > 2 and not ld.long_lines("\n".join(quoted))
              and sw._words(quoted) == sw._words([quote_line, quote_list]) and rc_l == 0,
              out[-400:] + out_l[-600:])


def _seeded(punch: str = PUNCH, handoff_text: "str | None" = None) -> "tuple[tempfile.TemporaryDirectory, Tree]":
    """A Tree whose 03/04 are given BEFORE R8 is seeded, so their mega-lines are waived and the ceilings fit."""
    tmp = tempfile.TemporaryDirectory()
    t = Tree(Path(tmp.name), punch, seed=False)
    if handoff_text is not None:
        t.write("04-HANDOFF.md", handoff_text)
    rc, out = quiet(ld.seed, t.docs, t.budget)
    assert rc == 0, out
    t.commit("seeded")
    return tmp, t


def _shas(t: Tree, *names: str) -> "dict[str, str | None]":
    paths = [t.docs / n for n in names] + [t.budget / ld.CEILINGS_NAME, t.budget / ld.WAIVERS_NAME]
    return {p.name: hashlib.sha1(p.read_bytes()).hexdigest() if p.is_file() else None for p in paths}


def t_rehearsal_lint() -> None:
    """S-7 (round 3): `--apply` never writes a result that turns a doc rule red. The rehearsal lints the COMPLETE
    would-be result (source, archive, both R8 JSON files) in a temp copy; a red rule refuses, nothing written."""
    added = sum(len(p) - 1 for p in sw.split_plan(handoff().splitlines())[0].values())
    base = len(handoff("\n").splitlines())
    check("S-7 precondition: the synthetic 04's split ADDS lines (else the R3 arm is vacuous)", added >= 1, str(added))

    # FAULT — the round-2 checker's shape: 04 at its 900-line budget, `--apply --split-lines` would cross it (R3).
    tmp, t = _seeded(handoff_text=handoff("\n" + "pad\n" * (900 - base)))
    with tmp:
        rc0, out0 = t.cli()
        n04 = len(t.read("04-HANDOFF.md").splitlines())
        check("S-7 precondition: the FAULT tree is GREEN before the apply, 04 exactly AT its 900-line budget",
              rc0 == 0 and n04 == 900, f"{n04} lines; {out0[-300:]}")
        before, digest = _shas(t, "04-HANDOFF.md", "28-HANDOFF-ARCHIVE.md"), t.digest()
        rc, out = run_sweep(t, "--apply", "--split-lines", source="04-HANDOFF.md")
        msg = str(rc)
        check("S-7 FAULT `--apply --split-lines` that would push 04 over R3's 900-line budget is REFUSED, the "
              "message names R3 and says nothing was written",
              isinstance(rc, SystemExit) and "R3  04-HANDOFF.md" in msg and "900-line budget" in msg
              and "nothing written" in msg and "ALREADY red" not in msg, msg[:500])
        check("S-7 FAULT ... and the source, the archive and BOTH R8 JSON files are byte-identical (sha1), the whole "
              "tree too", _shas(t, "04-HANDOFF.md", "28-HANDOFF-ARCHIVE.md") == before and t.digest() == digest,
              str(_shas(t, "04-HANDOFF.md", "28-HANDOFF-ARCHIVE.md")))

    # CONTROL — the same shape one split's worth of lines shorter: the result lands exactly AT 900 and applies.
    tmp, t = _seeded(handoff_text=handoff("\n" + "pad\n" * (900 - base - added)))
    with tmp:
        rc, out = run_sweep(t, "--apply", "--split-lines", source="04-HANDOFF.md")
        rc_l, out_l = t.cli()
        check("S-7 CONTROL the same split whose result keeps the lint green (04 ends exactly AT 900 lines) APPLIES, "
              "and the real lint passes afterwards",
              rc == 0 and "lint_docs GREEN" in out and len(t.read("04-HANDOFF.md").splitlines()) == 900
              and rc_l == 0, out[-300:] + out_l[-300:])

    # FAULT — a sweep AND a split on 03 at its 4,400-line budget: the move saves lines, the split adds more.
    mega = prose("> ", 100)
    punch = PUNCH.replace("## Now\n\n", "## Now\n\n" + mega + "\n\n", 1)
    pad = 4400 - len(punch.replace("## Now\n\n", "## Now\n\n\n", 1).splitlines())
    punch = punch.replace("## Now\n\n", "## Now\n\n" + "pad\n" * pad + "\n", 1)
    tmp, t = _seeded(punch)
    with tmp:
        rc0, _ = t.cli()
        lines = t.read("03-PUNCH-LIST.md").splitlines()
        chosen = [b for b in sw.find_blocks(lines) if b.reason is None]
        check("S-7 precondition: the 03 FAULT tree is green AT 4,400 lines with a closed block selected",
              rc0 == 0 and len(lines) == 4400 and len(chosen) == 1, f"{len(lines)} lines, {len(chosen)} chosen")
        before, digest = _shas(t, "03-PUNCH-LIST.md", "32-PUNCH-LIST-ARCHIVE.md"), t.digest()
        rc, out = run_sweep(t, "--apply", "--split-lines")
        msg = str(rc)
        check("S-7 FAULT a sweep + split on 03 that would cross R3's 4,400 is REFUSED naming R3; the source, BOTH "
              "JSON files are byte-identical and NO archive was created",
              isinstance(rc, SystemExit) and "R3  03-PUNCH-LIST.md" in msg and "nothing written" in msg
              and _shas(t, "03-PUNCH-LIST.md", "32-PUNCH-LIST-ARCHIVE.md") == before
              and before["32-PUNCH-LIST-ARCHIVE.md"] is None and t.digest() == digest, msg[:400])
        rc, out = run_sweep(t, "--apply")
        rc_l, _ = t.cli()
        check("S-7 CONTROL on the same tree a plain sweep (no split: it REMOVES lines) still applies, lint green",
              rc == 0 and "MOVED" in out and (t.docs / "32-PUNCH-LIST-ARCHIVE.md").is_file() and rc_l == 0,
              out[-300:])

    # FAULT — R8 (d) still runs in the rehearsal: the rehearsed JSON lives outside git, so it is compared with the
    # REAL folder's committed copy. A headroom raised with no record (the ratchet never touches headroom) is red.
    tmp, t = fresh()
    with tmp:
        data = t.cj()
        data["files"]["03-PUNCH-LIST.md"]["headroom"] += 1
        t.save(ld.CEILINGS_NAME, data)
        digest = t.digest()
        rc, out = run_sweep(t, "--apply")
        msg = str(rc)
        check("S-7 FAULT R8 (d) runs on the rehearsed copy (against the real folder's HEAD): an unrecorded headroom "
              "raise refuses the sweep, says the tree was ALREADY red, nothing written",
              isinstance(rc, SystemExit) and "headroom ROSE" in msg and "ALREADY red" in msg
              and t.digest() == digest, msg[:400])


def t_archive_doc_block() -> None:
    done = subprocess.run([sys.executable, str(TOOLS / "archive_doc_block.py"), "--self-test"], cwd=TOOLS,
                          capture_output=True, text=True, encoding="utf-8", env=ENV)
    check("AD archive_doc_block --self-test still passes (9 arms)", done.returncode == 0, done.stdout[-300:])
    lines = PUNCH.splitlines()
    start = lines.index("### ✅ `#90-closedone` — DONE 2026-10-01")
    check("AD CONTROL the default stops at the first bullet (single-item moves unchanged)",
          adb.find_block(lines, "### ✅ `#90-closedone`") == (start, start + 1), "")
    end = adb.find_block(lines, "### ✅ `#90-closedone`", sw.SWEEP_STOPS)[1]
    check("AD stop_prefixes moves the whole `###` section, bullets and all", lines[end].startswith("### ✅ `#90-still"),
          lines[end][:40])


# ------------------------------------------------------------------------------------------------------------- P9
def prune_arm(fault: bool) -> "tuple[str, bool]":
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gates = root / "ai_player" / "gates"
        gates.mkdir(parents=True)
        (root / "ai_player" / "__init__.py").write_text("", encoding="utf-8")
        (gates / "__init__.py").write_text("", encoding="utf-8")
        src = (GATES / "prune_evidence.py").read_text(encoding="utf-8")
        glob = '"ai_player/readme/**/*.md", '
        built = src.count(glob) == 1
        if fault:
            src = src.replace(glob, "")
        (gates / "prune_evidence.py").write_text(src, encoding="utf-8")
        shutil.copyfile(GATES / "provenance.py" if (GATES / "provenance.py").is_file()
                        else REPO / "ai_player" / "gates" / "provenance.py", gates / "provenance.py")
        ev = root / "ai_player" / "evidence" / "archive" / "0123456789abcdef"
        ev.mkdir(parents=True)
        (ev / "2026-01-01-SYNTH-ONLYREADME.txt").write_text("SYNTHETIC EVIDENCE A\n", encoding="utf-8")
        (ev / "2026-01-01-SYNTH-UNCITED.txt").write_text("SYNTHETIC EVIDENCE B\n", encoding="utf-8")
        (root / "ai_player" / "readme").mkdir()
        (root / "ai_player" / "readme" / "01-step-x.md").write_text(
            "## Step x\n\nIts proof: `2026-01-01-SYNTH-ONLYREADME.txt`.\n", encoding="utf-8")
        (root / "ai_player" / "README.md").write_text("# README\n\n> moved: Step x -> readme/01-step-x.md\n",
                                                      encoding="utf-8")
        _git(root, "init", "-q")
        files = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
        _git(root, "add", "--", *files)
        _git(root, "commit", "-q", "-m", "synthetic")
        done = subprocess.run([sys.executable, str(gates / "prune_evidence.py")], cwd=root, capture_output=True,
                              text=True, encoding="utf-8", env=ENV)
        return done.stdout + done.stderr, built


def t_p9() -> None:
    out, built = prune_arm(False)
    keep = next((line for line in out.splitlines() if line.startswith("KEEP (cited)")), "")
    delete = next((line for line in out.splitlines() if line.startswith("INDEX AND DELETE")), "")
    check("P9-1 evidence cited ONLY from readme/step-x.md is KEPT (cited) by the prune dry run",
          "SYNTH-ONLYREADME" in keep and ": 1 files" in delete, out[-500:])
    check("P9-1 the FAULT arm can be built (CITING holds the readme glob exactly once)", built, "")
    out, _ = prune_arm(True)
    keep = next((line for line in out.splitlines() if line.startswith("KEEP (cited)")), "")
    delete = next((line for line in out.splitlines() if line.startswith("INDEX AND DELETE")), "")
    check("P9-1 FAULT CITING without the glob -> the file is listed INDEX AND DELETE (the data-loss path)",
          "SYNTH-ONLYREADME" not in keep and ": 2 files" in delete, out[-500:])

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "ai_player" / "readme").mkdir(parents=True)
        (root / "ai_player" / "README.md").write_text("# README\n\n> moved: x -> readme/01-x.md\n", encoding="utf-8")
        marker = "a phrase that lives only in a moved section"
        (root / "ai_player" / "readme" / "01-x.md").write_text(f"## x\n\nThe {marker}, verbatim.\n", encoding="utf-8")
        lesson = (f'### TS-1. a synthetic lesson\n- **Origin:** 2026-10-21, README "{marker}"\n'
                  "- **Status:** PROSE ONLY\n- **Needs:** a gate\n- **Retires:** never\n")
        cl = load(GATES / "check_lessons.py", "check_lessons_under_test")
        problems, _ = cl.check(lesson, documents={"README": cl.readme_documents(root)}, required=())
        check("P9-2 check_lessons finds a quote that lives in a moved section", not problems, str(problems))
        problems, _ = cl.check(lesson.replace(marker, "a phrase in no document"),
                               documents={"README": cl.readme_documents(root)}, required=())
        check("P9-2 CONTROL a quote in NO document still fails (the check can fail)",
              any("does not contain" in p for p in problems), str(problems))
        check("P9-2 the real DOCUMENTS['README'] starts with ai_player/README.md",
              isinstance(cl.DOCUMENTS["README"], tuple) and cl.DOCUMENTS["README"][0].name == "README.md", "")
        src = (GATES / "check_lessons.py").read_text(encoding="utf-8")
        glob = ', *sorted((root / "ai_player" / "readme").glob("**/*.md"))'
        mutant = root / "check_lessons_fault.py"
        mutant.write_text(src.replace(glob, ""), encoding="utf-8")
        fl = load(mutant, "check_lessons_fault")
        problems, _ = fl.check(lesson, documents={"README": fl.readme_documents(root)}, required=())
        check("P9-2 FAULT DOCUMENTS without the readme folder -> the quote is NOT found",
              src.count(glob) == 1 and any("does not contain" in p for p in problems), str(problems))

        db = load(GATES / "disk_budget.py", "disk_budget_under_test")
        db.REPO = root
        check("P9-3 disk_budget.citing_text() includes the moved sections' text", marker in db.citing_text(), "")
        src = (GATES / "disk_budget.py").read_text(encoding="utf-8")
        glob = '"ai_player/readme/**/*.md", '
        mutant = root / "disk_budget_fault.py"
        mutant.write_text(src.replace(glob, ""), encoding="utf-8")
        fd = load(mutant, "disk_budget_fault")
        fd.REPO = root
        check("P9-3 FAULT citing_text without the glob -> the moved text is missing",
              src.count(glob) == 1 and marker not in fd.citing_text(), "")


README_TEXT = ("# synthetic README\n\nIntro paragraph.\n\n"
               "## Run it\n\nrun it like this\n```text\n## not a heading (fenced)\n```\n\n"
               "## The battles (build step 4)\n\nbattle detail\nmore\n\n\n"
               "## Known limits of step 1\n\n- a caveat\n\n"
               "## The eyes (build step 1)\n\neyes detail\n")
KEEP = ("Run it", "Known limits of step 1")


def t_split_readme() -> None:
    new_text, moved = sr.plan_split(README_TEXT, KEEP)
    files = {name: content for name, _, content in moved}
    check("P9-4 the plan moves the two non-KEEP sections, in order, to NN-<slug>.md",
          [m[0] for m in moved] == ["01-the-battles-build-step-4.md", "02-the-eyes-build-step-1.md"], str(moved))
    check("P9-4 sections before == after: substituting the files gives back the README EXACTLY",
          sr.reconstruct(new_text, files) == README_TEXT, "")
    check("P9-4 a fenced `## ` stays where it was (an example, not a section) and the KEEP sections stay",
          "## not a heading (fenced)" in new_text and "## Known limits of step 1" in new_text
          and "battle detail" not in new_text, new_text)
    lost = dict(files)
    lost["01-the-battles-build-step-4.md"] = lost["01-the-battles-build-step-4.md"].replace("more\n", "")
    rc, _ = quiet(sr.check, README_TEXT, new_text, lost)
    check("P9-4 FAULT a moved file missing a line -> invariant A refuses (LOST)",
          isinstance(rc, SystemExit) and "LOST" in str(rc), str(rc))
    swapped = {"01-the-battles-build-step-4.md": files["02-the-eyes-build-step-1.md"],
               "02-the-eyes-build-step-1.md": files["01-the-battles-build-step-4.md"]}
    rc, _ = quiet(sr.check, README_TEXT, new_text, swapped)
    check("P9-4 FAULT two sections swapped (no line lost) -> the reconstruction refuses",
          isinstance(rc, SystemExit) and "DOES NOT RECONSTRUCT" in str(rc), str(rc))
    for name, text, keep, word in (
            ("a stale KEEP heading", README_TEXT, KEEP + ("Gone section",), "KEEP names"),
            ("an unclosed fence", README_TEXT + "```\n## after\n", KEEP, "never closes"),
            ("a second split", new_text, KEEP, "already holds")):
        rc, _ = quiet(sr.plan_split, text, keep)
        check(f"P9-4 FAULT {name} -> refused", isinstance(rc, SystemExit) and word in str(rc), str(rc))
    real_slug = sr.slug
    try:
        sr.slug = lambda heading: "Bad_Name"      # a pointer the reconstruction cannot read back
        rc, _ = quiet(sr.plan_split, README_TEXT, KEEP)
        check("P9-4 FAULT a planner writing an unreadable pointer -> plan_split's OWN check refuses before writing",
              isinstance(rc, SystemExit) and "RECONSTRUCT" in str(rc), str(rc))
    finally:
        sr.slug = real_slug

    with tempfile.TemporaryDirectory() as tmp:
        readme = Path(tmp) / "ai_player" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text(README_TEXT, encoding="utf-8", newline="\n")
        real_keep = sr.KEEP
        try:
            sr.KEEP = KEEP
            rc, out = quiet(sr.main, ["--readme", str(readme)])
            check("P9-4 the dry run writes nothing", rc == 0 and not (readme.parent / "readme").exists()
                  and readme.read_text(encoding="utf-8") == README_TEXT, out)
            (readme.parent / "readme").mkdir()
            (readme.parent / "readme" / "old.md").write_text("x", encoding="utf-8")
            rc, _ = quiet(sr.main, ["--readme", str(readme), "--apply"])
            check("P9-4 FAULT an existing readme/ folder with files -> refused, README untouched",
                  isinstance(rc, SystemExit) and "already holds files" in str(rc)
                  and readme.read_text(encoding="utf-8") == README_TEXT, str(rc))
            shutil.rmtree(readme.parent / "readme")
            real_write = pathlib.Path.write_text

            def short_write(self, data, *a, **kw):
                if self.parent.name == "readme":
                    data = data.replace("more\n", "")
                return real_write(self, data, *a, **kw)
            pathlib.Path.write_text = short_write
            try:
                rc, _ = quiet(sr.main, ["--readme", str(readme), "--apply"])
            finally:
                pathlib.Path.write_text = real_write
            check("P9-4 FAULT a corrupted write -> the post-write check refuses (LOST)",
                  isinstance(rc, SystemExit) and "LOST" in str(rc), str(rc))
            shutil.rmtree(readme.parent / "readme")
            readme.write_text(README_TEXT, encoding="utf-8", newline="\n")
            rc, out = quiet(sr.main, ["--readme", str(readme), "--apply"])
            on_disk = {p.name: p.read_text(encoding="utf-8") for p in (readme.parent / "readme").glob("*.md")}
            check("P9-4 --apply writes the files and the README, and they reconstruct the original from DISK",
                  rc == 0 and sr.reconstruct(readme.read_text(encoding="utf-8"), on_disk) == README_TEXT, out)
        finally:
            sr.KEEP = real_keep

    real = REPO / "ai_player" / "README.md"
    text = real.read_text(encoding="utf-8")
    if not any(sr.POINTER_RE.match(x) for x in text.split("\n")):
        try:
            new, moved = sr.plan_split(text)
            NOTES.append(f"NOTE (not graded) the REAL ai_player/README.md: {len(text.encode()):,} B; the current part "
                         f"would be {len(new.encode()):,} B, {len(moved)} sections moving (read only)")
        except SystemExit as exc:
            NOTES.append(f"NOTE (not graded) the REAL README's split plan refuses: {exc}")
    else:
        NOTES.append("NOTE (not graded) the REAL README is already split")


def main() -> int:
    print("=" * 100)
    print(f"SELFTEST spec S2-1 — lint_docs R8, archive_sweep, split_readme, P9 consumers (tools {TOOLS}; gates {GATES})")
    print("=" * 100)
    check("the code under test is the --tools-dir copy", Path(ld.__file__).resolve().parent == TOOLS
          and Path(sw.__file__).resolve().parent == TOOLS, str(ld.__file__))
    for test in (t_regexes, t_r8_0_1, t_r8_2_3, t_r8_4, t_r8_5, t_r8_6_7, t_r8_8_9, t_sweep, t_split,
                 t_rehearsal_lint, t_archive_doc_block, t_p9, t_split_readme):
        try:
            test()
        except Exception as exc:  # noqa: BLE001 — a crash is a FAIL with its reason, never a silent stop
            check(f"{test.__name__} ran to the end", False, f"{type(exc).__name__}: {exc}")
    failed = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"\n         {detail[:600]}" if not ok and detail else ""))
    for note in NOTES:
        print(f"  {note}")
    print("=" * 100)
    print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks PASS" + (f"; {len(failed)} FAIL" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
