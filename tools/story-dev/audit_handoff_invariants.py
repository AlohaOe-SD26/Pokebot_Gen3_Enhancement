"""THE HANDOFF'S STRUCTURAL INVARIANTS — the doc failures that PROSE DID NOT PREVENT, as a GATE.

‼ WHY THIS EXISTS. Over 2026-09-01, FOUR independent cold-start audits read `04-HANDOFF.md` and
`00-README.md` and each found a defect the previous round's FIX had created or missed. Tier 0
(`lint_docs.py` + `audit_doc_consistency.py`) was GREEN over every single one, because every one of
them was STRUCTURAL rather than textual. CLAUDE.md's own rule is the answer:

    "Anything enforceable belongs in a GATE, not in prose here. A rule already broken twice is
     evidence that prose failed — write the gate instead."

These four were each broken at least twice in one day:

  H1  MORE THAN ONE `➡➡➡` QUEUE MARKER. The file's own reading rule says the marker IS the live
      next action. Round 1 found the marker retargeted to a new leg with the OLD leg's hazard list
      under it; a later fix then added prose mentions of the arrows, so a bare `grep -c` returned
      11 and the file's "use the LAST one" tie-break landed on prose. ⇒ EXACTLY ONE line may BEGIN
      with the marker.
  H2  THE `HOW TO RUN / TEST` SECTION VANISHING. An archiving script of mine deleted all 333 lines
      after the last queue item — including this section — because its block-boundary loop had no
      terminator and ran to EOF. It was uncommitted and `git checkout --` saved it. Nothing
      mechanical would have caught it. ⇒ the section must exist and be non-trivial.
  H3  A `--driver` NAME IN THE RECIPE THAT THE HARNESS DOES NOT ACCEPT. A run command a cold agent
      copies must actually run. (`story_harness.py` carries the authoritative `choices` list.)
  H4  A FIXTURE NAMED IN A RUN COMMAND THAT DOES NOT EXIST ON DISK. Round 3 flagged that leg 4's
      only anchor was untracked; the general form is worse — a recipe that names a save state
      nobody has is a session wasted before it starts.
  H5  A CLAIMED FAULT-ARM COUNT THAT DISAGREES WITH THE NUMBER OF ARMS LISTED. The file said "THE
      TWO FAULT ARMS ARE NOT OPTIONAL" directly above THREE commands; a reader who trusted the
      count would skip the arm an adversarial review had added BECAUSE IT CAUGHT A REAL BLOCKER.

⛔ WHAT THIS GATE DELIBERATELY DOES **NOT** DO. It does not read meaning. It cannot tell you that a
hazard list belongs to the previous leg, or that a var is the wrong var — those need a cold-start
agent, and Tier 2 stays. This gate exists so the CHEAP, MECHANICAL half never has to be found by an
expensive one again.

Run:        cd tools/story-dev && PYTHONUTF8=1 py -3.12 audit_handoff_invariants.py
Self-test:  PYTHONUTF8=1 py -3.12 audit_handoff_invariants.py --self-test
            ⛔ Every check is fault-tested against a SYNTHETIC broken handoff, and each must fail
            for its OWN reason and not fire on a healthy one. A gate with false positives teaches
            the reader to bypass it, which is strictly worse than no gate.
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
HANDOFF = REPO / "PROJECT KNOWLEDGE" / "04-HANDOFF.md"
HARNESS = HERE / "story_harness.py"
SAVES = HERE / "saves"

#: A queue marker is a line that BEGINS with the arrows (after the blockquote indent). Prose that
#: merely mentions them is not a marker — that distinction is the whole of H1.
MARKER_RE = re.compile(r"^>\s{2,}➡➡➡")
HOWTO_RE = re.compile(r"^#\s*HOW TO RUN", re.MULTILINE)
DRIVER_RE = re.compile(r"--driver\s+([A-Za-z0-9_]+)")
#: ⛔ A FIXTURE IS A POSITIONAL ARGUMENT TO THE HARNESS, NOT ANY `.ss1` TOKEN ANYWHERE.
#: The loose form `\b(\w+\.ss1)\b` produced a FALSE POSITIVE on its first real run: it flagged
#: `current_state.ss1`, which is the emulator's live profile state named in a PROSE WARNING about
#: probes that write — not a fixture anyone is asked to load.
FIXTURE_RE = re.compile(r"story_harness\.py\s+([A-Za-z0-9_]+\.ss1)")
#: "THE THREE FAULT ARMS", "both fault arms", "all THREE fault arms" ...
COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "both": 2}
ARMCOUNT_RE = re.compile(r"\b(one|two|three|four|five|six|both)\b[^.\n]{0,40}?fault arms?", re.I)
ARM_ENV_RE = re.compile(r"POKEBOT_[A-Z0-9_]*FAULT[A-Z0-9_]*")

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def howto_block(text: str) -> str:
    """The HOW TO RUN section's body, or '' when the section is absent.

    ⛔ FENCED CODE BLOCKS ARE TRACKED, AND THAT IS NOT A DETAIL — IT WAS A BUG IN THIS GATE, CAUGHT
    BY ITS OWN SELF-TEST BEFORE IT EVER RAN ON THE REAL FILE. The first version ended the section at
    the next line matching `^#\\s+\\S`. But the HOW TO RUN body is a ```bash fence full of
    `# comment` lines, and every one of them looks exactly like a markdown heading. So the section
    "ended" at its first comment: the body measured 3 lines instead of ~90, H2 fired on a HEALTHY
    file, and H5 silently saw zero fault arms and passed vacuously.
    ‼ A gate that fires on a healthy file is worse than no gate — it teaches the reader to bypass
    it. And a gate that passes VACUOUSLY is worse still, because it looks like coverage.
    """
    m = HOWTO_RE.search(text)
    if not m:
        return ""
    out, fenced = [], False
    for line in text[m.end():].split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        if not fenced and re.match(r"^#\s+\S", line):
            break                      # a REAL heading, outside any fence: the section ends here
        out.append(line)
    return "\n".join(out)


def audit(text: str, *, harness_choices: set[str], fixtures: set[str]) -> None:
    lines = text.split("\n")

    # ---- H1 ------------------------------------------------------------------------------------
    markers = [i + 1 for i, l in enumerate(lines) if MARKER_RE.match(l)]
    check("H1  exactly ONE queue marker line (a line BEGINNING with the arrows)",
          len(markers) == 1, f"found {len(markers)} at lines {markers}")

    # ---- H2 ------------------------------------------------------------------------------------
    block = howto_block(text)
    # ⛔ A LENGTH FLOOR, NOT MERE PRESENCE. The failure mode was the section being DELETED; a
    # heading that survives with an empty body would satisfy "present" and help nobody.
    check("H2  the HOW TO RUN section exists and has a real body",
          bool(block.strip()) and len(block.strip().split("\n")) >= 10,
          f"{len(block.strip().split(chr(10))) if block.strip() else 0} lines")

    # ---- H3 ------------------------------------------------------------------------------------
    drivers = sorted(set(DRIVER_RE.findall(block)))
    unknown = [d for d in drivers if d not in harness_choices]
    check("H3  every --driver named in HOW TO RUN is registered in story_harness.py",
          not unknown, f"unregistered: {unknown}" if unknown else f"{len(drivers)} driver(s) checked")

    # ---- H4 ------------------------------------------------------------------------------------
    named = sorted(set(FIXTURE_RE.findall(block)))
    missing = [f for f in named if f not in fixtures]
    check("H4  every .ss1 fixture named in HOW TO RUN exists in saves/",
          not missing, f"missing: {missing}" if missing else f"{len(named)} fixture(s) checked")

    # ---- H5 ------------------------------------------------------------------------------------
    # ⛔ THE COUNT IS SCOPED TO THE CLAIM'S OWN RECIPE, NOT TO THE WHOLE SECTION. Counting every
    # `POKEBOT_*FAULT*` in HOW TO RUN gave a FALSE POSITIVE on the first real run — 10 arms across
    # §Ch20, §Ch21 and the Route-131 probes, "contradicting" a claim that was only ever about the
    # three §Ch21 approach arms. A claim belongs to the CONTIGUOUS non-blank block it sits in,
    # which is exactly how these recipes are laid out (comment lines interleaved with commands,
    # separated from the next recipe by a blank line).
    block_lines = block.split("\n")
    bad, claims = [], []
    for index, line in enumerate(block_lines):
        m = ARMCOUNT_RE.search(line)
        if not m:
            continue
        # ⛔ THE GROUP ENDS AT A BLANK LINE **OR AT THE NEXT TOP-LEVEL COMMENT HEADER**, and the
        # second half is not optional. These recipes are NOT blank-line separated: on its first
        # real run this check swept forward into the following warning block and counted its
        # `POKEBOT_R131TAIL_FAULT`, reporting "says 3, has 4" against a perfectly correct file.
        # The file's own convention distinguishes them — `# ` + non-space starts a NEW header,
        # `#   ` (indented) continues the current one — so that is what the boundary uses.
        header = re.compile(r"^#\s\S")
        start = index
        while start > 0 and block_lines[start - 1].strip() and not header.match(block_lines[start - 1]):
            start -= 1
        end = index
        while end + 1 < len(block_lines) and block_lines[end + 1].strip() \
                and not header.match(block_lines[end + 1]):
            end += 1
        group = "\n".join(block_lines[start : end + 1])
        present = len(set(ARM_ENV_RE.findall(group)))
        claimed = COUNT_WORDS[m.group(1).lower()]
        claims.append((m.group(0), claimed, present))
        if present and claimed != present:
            bad.append((m.group(0), claimed, present))
    check("H5  any claimed fault-arm count matches the arms in its OWN recipe block",
          not bad,
          f"contradicted: {[(t, f'says {c}', f'has {p}') for t, c, p in bad]}" if bad
          else f"{len(claims)} claim(s) checked, all agree")


def harness_driver_choices() -> set[str]:
    """The authoritative --driver list, read from story_harness.py's own argparse call.

    ⛔ ANCHORED ON `add_argument("--driver"`, NOT ON THE BARE STRING `--driver`. The loose form
    `--driver.*?choices=\\[(.*?)\\]` produced a FALSE POSITIVE on its first real run: it matched an
    earlier mention of `--driver` in a docstring and then took the FIRST `]` it could find, so it
    extracted **2** names out of ~70 and declared 21 perfectly valid drivers "unregistered".
    ‼ That is the shape this gate exists to prevent, committed inside the gate itself — which is
    why the caller REFUSES to run when this returns something implausibly small.
    """
    text = HARNESS.read_text(encoding="utf-8-sig", errors="replace")
    m = re.search(r'add_argument\(\s*"--driver".*?choices\s*=\s*\[(.*?)\]', text, re.S)
    if not m:
        return set()
    return set(re.findall(r'"([A-Za-z0-9_]+)"', m.group(1)))


SYNTHETIC_OK = """# ‼ YOU ARE HERE
>    ➡➡➡ **NEXT ACTION: do the thing.**
> prose that merely mentions ➡➡➡ must NOT count as a marker.

# HOW TO RUN / TEST
```
PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach
# ‼ THE TWO FAULT ARMS ARE NOT OPTIONAL
POKEBOT_CH21_FAULT_BLINDWALL=1 ... --driver ch21approach
POKEBOT_CH21_FAULT_POCKETSTALL=1 ... --driver ch21approach
line5
line6
line7
line8
line9
line10
```
"""


def self_test() -> int:
    """Break each invariant ON PURPOSE; each must fail for its OWN reason, and none on the healthy one."""
    print("SELF-TEST — every check must FAIL on a broken handoff and PASS on a healthy one")
    print("=" * 96)
    choices = {"ch21approach"}
    fixtures = {"post_wallace.ss1"}
    cases = [
        ("HEALTHY (must raise nothing)", SYNTHETIC_OK, []),
        ("H1 two markers", SYNTHETIC_OK.replace(
            "> prose that merely mentions", ">    ➡➡➡ a SECOND marker\n> prose that merely mentions"), ["H1"]),
        # ⛔ H5 must NOT be in this expectation: with the section gone there are no arm CLAIMS to
        # contradict, so H5 passing is correct. Listing it would make the self-test demand a false
        # positive — a self-test can be wrong in the same direction as the gate.
        ("H2 section deleted", SYNTHETIC_OK[: SYNTHETIC_OK.index("# HOW TO RUN")], ["H2"]),
        ("H3 unknown driver", SYNTHETIC_OK.replace("--driver ch21approach\n", "--driver ch21ghost\n", 1), ["H3"]),
        ("H4 missing fixture", SYNTHETIC_OK.replace("post_wallace.ss1", "post_nowhere.ss1", 1), ["H4"]),
        ("H5 count says TWO, three arms listed", SYNTHETIC_OK.replace(
            "POKEBOT_CH21_FAULT_POCKETSTALL=1 ... --driver ch21approach",
            "POKEBOT_CH21_FAULT_POCKETSTALL=1 ... --driver ch21approach\n"
            "POKEBOT_CH21_FAULT_POCKETWALKBACK=1 ... --driver ch21approach"), ["H5"]),
        # ⛔ THE BOUNDARY CASE THAT PRODUCED A FALSE POSITIVE ON THE REAL FILE: a SECOND recipe
        # follows with NO blank line between them. Its arm must NOT be counted against the first
        # recipe's claim. Without this case the boundary logic is untested and the gate would go
        # back to failing a correct handoff.
        ("H5 adjacent recipe must not be swept in", SYNTHETIC_OK.replace(
            "line5",
            "# ⛔ A DIFFERENT RECIPE, no blank line before it\n"
            "POKEBOT_R131TAIL_FAULT=stride ... --driver ch21approach"), []),
    ]
    bad = 0
    for label, text, expect in cases:
        FAILURES.clear()
        print(f"\n--- {label} ---")
        audit(text, harness_choices=choices, fixtures=fixtures)
        fired = sorted({f.split()[0] for f in FAILURES})
        want = sorted(expect)
        ok = fired == want
        print(f"    fired={fired}  expected={want}  {'OK' if ok else '‼ SELF-TEST FAILED'}")
        if not ok:
            bad += 1
    print("\n" + "=" * 96)
    print("SELF-TEST PASS — every check fires for its own reason and none fires on a healthy file."
          if not bad else f"‼ SELF-TEST FAILED on {bad} case(s) — this gate is NOT trustworthy.")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    print("=" * 96)
    print("HANDOFF STRUCTURAL INVARIANTS — the mechanical half of the doc-consistency layer")
    print("=" * 96)
    if not HANDOFF.exists():
        print(f"  FAIL  {HANDOFF} does not exist")
        return 1
    choices = harness_driver_choices()
    # ⛔ A PLAUSIBILITY FLOOR, NOT MERELY "non-empty". The extraction bug that shipped in this
    # gate's first version returned TWO names and H3 then failed 21 valid drivers. A check whose
    # own INPUT is silently truncated does not report "I am broken" — it reports "your file is
    # broken", which is the more expensive lie.
    if len(choices) < 20:
        print(f"  FAIL  read only {len(choices)} --driver choice(s) from story_harness.py "
              f"({sorted(choices)}). That is implausible; the extraction is broken, NOT the "
              f"handoff. Refusing to grade H3 on it.")
        return 1
    fixtures = {p.name for p in SAVES.glob("*.ss1")} if SAVES.is_dir() else set()
    print(f"  ({len(choices)} registered drivers, {len(fixtures)} fixtures on disk)\n")
    audit(HANDOFF.read_text(encoding="utf-8", errors="replace"),
          harness_choices=choices, fixtures=fixtures)
    print()
    if FAILURES:
        print("=" * 96)
        print(f"FAILED — {len(FAILURES)} structural invariant(s) broken:")
        for f in FAILURES:
            print(f"    - {f}")
        print("‼ These are the failures FOUR cold-start audits had to find by hand on 2026-09-01.")
        print("=" * 96)
        return 1
    print("=" * 96)
    print("ALL HANDOFF INVARIANTS HOLD.")
    print("⛔ This is the MECHANICAL half only. It cannot tell you a hazard list belongs to the")
    print("   PREVIOUS leg, or that a grading var is the wrong var — Tier 2 still has to.")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
