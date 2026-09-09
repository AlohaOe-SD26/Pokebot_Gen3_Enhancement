"""CITATION DRIFT — does every `identifier` + `file.py:LINE` in the CURRENT-STATE docs still resolve?

WHY THIS EXISTS. Hand-typed `file.py:NNN` references go stale the moment the code moves, and this
project has now been bitten three times:
  * 2026-08-16 — "six of eight hand-copied citations in the KI-81 entry were wrong";
  * 2026-08-17 — a Pass-1 audit found FOUR more, two of them in the exact lines the next session
    was told to act on (`pc_trip.py:453-454`, `higher_level_actions.py:356`, `early_game.py:1587`,
    `early_game.py:6253`);
  * and every one of them survived multiple doc passes, because a wrong line number reads exactly
    like a right one.

⛔ SCOPED NARROWLY ON PURPOSE — A NOISY GATE GETS BYPASSED. This fires ONLY on the unambiguous
case: a doc names a Python IDENTIFIER next to a `file.py:LINE`, and that identifier is DEFINED in
that file at a DIFFERENT line. Everything else is left alone.

‼ WHAT THIS DOES **NOT** COVER, said plainly rather than implied: a citation pointing at a line
INSIDE a function body is invisible here. Two of the four drifted citations found on 2026-08-17
were of exactly that kind. **This is a definition-citation checker, not a citation checker.**
A green run means "no definition-citation has drifted", never "all citations are correct".

Run:      cd tools/story-dev && PYTHONUTF8=1 py -3.12 audit_doc_citations.py
Self-test: ... audit_doc_citations.py --self-test
Exit: 0 clean; 1 if any definition-citation points at the wrong line.
"""

import pathlib
import re
import sys
# ⛔ A default Windows console is cp1252 and this file prints ‼/⛔ — without this the gate
# dies with UnicodeEncodeError AFTER its checks pass, i.e. it FALSELY REDS. Found by a
# Tier 1 reviewer running it bare; invisible to anyone who habitually sets PYTHONUTF8=1.
sys.stdout.reconfigure(encoding="utf-8")


HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOCS = REPO / "PROJECT KNOWLEDGE"

#: ⛔ CURRENT-STATE FILES ONLY. `06`/`07`/`08`/`28`/`31` are append-only history: a citation there
#: was correct when written and MUST be allowed to age, or this gate would demand rewriting the
#: project's own record — which is forbidden.
CURRENT_STATE = ["00-README.md", "01-VISION-AND-DESIGN.md", "02-ARCHITECTURE.md",
                 "03-PUNCH-LIST.md", "04-HANDOFF.md", "05-KNOWN-ISSUES.md",
                 "14-AGENT-PLAYBOOK.md", "24-PLAIN-ENGLISH-STATUS.md"]

SEARCH_ROOTS = [REPO / "sandbox-pokebot", REPO / "tools" / "story-dev"]

#: `ident` then `path/file.py:123`, or the same pair the other way round. Both orders occur here.
IDENT = r"[A-Za-z_]\w*"
FILEREF = r"[\w/.\\-]*?([\w-]+\.py):(\d+)"
#: ⛔ THE TWO GAPS ARE DELIBERATELY ASYMMETRIC, AND THE ASYMMETRY WAS EARNED BY A FALSE POSITIVE.
#: The dominant idiom here is FORWARD — ``  `ident` (`file.py:12`)  `` — so that side can afford a
#: generous 48-char gap. The REVERSE form is rare, and with a wide window it mis-pairs: on
#: `03-PUNCH-LIST.md:2105`, ``(`story_mode.py:1899`) USED TO CO-GATE KI-23's
#: `_boss_plan_is_hopeless` `` made the gate blame `_boss_plan_is_hopeless` for a line that
#: correctly belongs to `grass_is_fodder` (verified: it IS at `:1899`). ⇒ reverse matching is
#: capped at 12 chars, which keeps ``  `f.py:12` in `X`  `` and drops the mis-pairing.
CITE = re.compile(
    r"`(" + IDENT + r")`[^`\n]{0,48}?`" + FILEREF
    + r"|`" + FILEREF + r"`[^`\n]{0,12}?`(" + IDENT + r")`"
)

DEF = re.compile(r"\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)")
TOLERANCE = 2   # a decorator or a wrapped signature legitimately shifts a citation by a line or two

_cache: dict[str, dict[str, int] | None] = {}


def extents(filename: str) -> dict[str, tuple[int, int]] | None:
    """`{name: (first_line, last_line)}` — the BODY SPAN of every def/class.

    ⛔⛔ THIS REPLACED A WRONG RULE, AND THE WRONG RULE WAS MINE. The first draft demanded that a
    citation naming `X` point AT `X`'s `def` line. Run live it produced **9 findings of which most
    were CORRECT CITATIONS** — because this project's normal idiom is to name a function and cite a
    line INSIDE it (`withdraw_from_box` (`pc_trip.py:481`) counts `alive`…, `ally_party_indices`'s
    rationale at `default.py:31-34`). A gate with that false-positive rate teaches everyone to
    bypass it, which is strictly worse than no gate — my own docstring said so, and I built it
    anyway. ⇒ **the sound property is CONTAINMENT: a citation naming X must land inside X's body.**
    """
    defs = definitions(filename)
    if defs is None:
        return None
    hits: list[pathlib.Path] = []
    for root in SEARCH_ROOTS:
        hits.extend(root.rglob(filename))
    if len(hits) != 1:
        return None
    lines = hits[0].read_text(encoding="utf-8", errors="replace").splitlines()
    # A def/class ends where the next def/class at the SAME OR SHALLOWER indent begins.
    starts: list[tuple[int, int, str]] = []
    for n, line in enumerate(lines, 1):
        m = DEF.match(line)
        if m:
            starts.append((n, len(line) - len(line.lstrip()), m.group(1)))
    out: dict[str, tuple[int, int]] = {}
    for i, (n, indent, nm) in enumerate(starts):
        end = len(lines)
        for n2, indent2, _ in starts[i + 1:]:
            if indent2 <= indent:
                end = n2 - 1
                break
        if nm not in out:                    # FIRST definition wins
            out[nm] = (n, end)
    return out


def definitions(filename: str) -> dict[str, int] | None:
    """First definition line of every def/class in `filename`, or None if not uniquely resolvable.

    ‼ AMBIGUITY IS TREATED AS "DO NOT KNOW", NEVER AS "WRONG". `early_game.py` exists in BOTH forks;
    if a name resolves to more than one path we return None and stay silent. A gate that guesses
    which copy a doc meant would produce exactly the false positives that get gates ignored.
    """
    if filename in _cache:
        return _cache[filename]
    hits: list[pathlib.Path] = []
    for root in SEARCH_ROOTS:
        hits.extend(root.rglob(filename))
    if len(hits) != 1:
        _cache[filename] = None
        return None
    out: dict[str, int] = {}
    for n, line in enumerate(hits[0].read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        m = DEF.match(line)
        if m and m.group(1) not in out:      # FIRST definition wins; overloads are not a thing here
            out[m.group(1)] = n
    _cache[filename] = out
    return out


def check(texts: dict[str, str]) -> list[str]:
    findings: list[str] = []
    for name, text in texts.items():
        for m in CITE.finditer(text):
            if m.group(1):
                ident, fname, lineno = m.group(1), m.group(2), m.group(3)
            else:
                ident, fname, lineno = m.group(6), m.group(4), m.group(5)
            spans = extents(fname)
            if not spans or ident not in spans:
                continue          # identifier not in that file, or the file is ambiguous -> silent
            lo, hi = spans[ident]
            cited = int(lineno)
            # ⛔ CONTAINMENT, NOT EQUALITY. A citation naming X may legitimately point ANYWHERE
            # inside X — that is this project's normal idiom ("`withdraw_from_box`
            # (`pc_trip.py:481`) counts `alive`…"). It is wrong only when it lands OUTSIDE X's
            # body, which is exactly what code movement does to it.
            if not (lo - TOLERANCE <= cited <= hi + TOLERANCE):
                line_no = text.count("\n", 0, m.start()) + 1
                findings.append(
                    f"{name}:{line_no} cites `{fname}:{cited}` for `{ident}`, but `{ident}` spans "
                    f"`{fname}:{lo}-{hi}` — the citation lands OUTSIDE it")
    return findings


def self_test() -> int:
    """⛔ BOTH SIGNS. A gate that only proves it can FIRE has not been tested."""
    ok = True

    def expect(label: str, got: list[str], want_fire: bool) -> None:
        nonlocal ok
        fired = bool(got)
        good = fired == want_fire
        ok &= good
        print(f"  {'PASS' if good else '‼ FAIL'}  {label}: "
              f"{'fired' if fired else 'quiet'} (expected {'fire' if want_fire else 'quiet'})")

    real = definitions("audit_doc_citations.py")
    if not real or "check" not in real:
        print("  ‼ FAIL  C0 cannot resolve this file's own definitions — the resolver is broken")
        return 1
    good_line = real["check"]
    expect("C1 a citation naming the RIGHT line -> quiet",
           check({"T": f"the `check` function (`audit_doc_citations.py:{good_line}`) does it\n"}), False)
    expect("C2 a citation naming the WRONG line -> fires",
           check({"T": f"the `check` function (`audit_doc_citations.py:{good_line + 40}`) does it\n"}), True)
    expect("C3 the reversed word order (`file:line` then `ident`) -> fires",
           check({"T": f"see `audit_doc_citations.py:{good_line + 40}`, which is `check`\n"}), True)
    expect("C4 an identifier NOT defined in that file -> quiet (not a definition-citation)",
           check({"T": "`some_local_variable` at `audit_doc_citations.py:12`\n"}), False)
    # ⛔ C5 WAS WRONG ON ITS FIRST DRAFT AND THE GATE WAS RIGHT. It asserted that `pc_trip.py`
    # is AMBIGUOUS because the file exists in both forks — but `SEARCH_ROOTS` deliberately covers
    # `sandbox-pokebot` and `tools/story-dev` only, never `custom-pokebot`, because the docs cite
    # the WORKING tree. So it resolves uniquely and SHOULD fire on a bad line. ‼ Recording this
    # rather than quietly deleting it: a fault test that encodes a wrong premise will happily fail
    # a correct gate, and "the test failed" is not the same as "the gate is broken".
    expect("C5 a real identifier with a nonsense line -> fires (resolution is sandbox-first)",
           check({"T": "`withdraw_from_box` at `pc_trip.py:99999`\n"}), True)
    expect("C5b a file that exists NOWHERE under the search roots -> quiet",
           check({"T": "`whatever` at `no_such_file_anywhere.py:12`\n"}), False)
    expect("C6 within the +/-2 tolerance (a decorator line) -> quiet",
           check({"T": f"`check` at `audit_doc_citations.py:{good_line - 1}`\n"}), False)
    expect("C7 ordinary prose with no citation -> quiet",
           check({"T": "The planner rides currents and the gate is a ratchet.\n"}), False)
    print(f"\nSELF-TEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    texts = {n: (DOCS / n).read_text(encoding="utf-8", errors="replace")
             for n in CURRENT_STATE if (DOCS / n).is_file()}
    findings = check(texts)
    bar = "=" * 92
    print(bar)
    print("DOC CITATION AUDIT — does `identifier` + `file.py:LINE` still resolve?")
    print(bar)
    if findings:
        for f in findings:
            print(f"  FAIL  {f}")
        print(bar)
        print(f"‼ {len(findings)} definition-citation(s) have DRIFTED. Fix the doc, not the code.")
        return 1
    print(f"  all definition-citations resolve across {len(texts)} current-state file(s)")
    print("  ‼ this does NOT cover citations pointing INSIDE a function body — see the docstring")
    print(bar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
